"""
리더락 모듈: PostgreSQL Advisory Lock을 사용한 단일 인스턴스 보장
"""
import os
import time
import threading
import random
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    psycopg2 = None

from utils.logging import get_logger

logger = get_logger("db.leader_lock")


class LeaderLock:
    """PostgreSQL Advisory Lock을 사용한 리더 선출"""
    
    def __init__(self, 
                 database_url: str,
                 lock_id: int = 12345,
                 reconnect_interval: float = 1.0,
                 max_backoff: float = 8.0):
        if not psycopg2:
            raise RuntimeError("psycopg2 is required for leader lock functionality")
        
        self.database_url = database_url
        self.lock_id = lock_id
        self.reconnect_interval = reconnect_interval
        self.max_backoff = max_backoff
        
        self._conn: Optional[psycopg2.extensions.connection] = None
        self._lock_acquired = False
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()  # 내부 상태 보호
        
        # 메트릭
        self.acquire_attempts = 0
        self.reconnect_count = 0
        self.last_acquire_time: Optional[float] = None
        self.last_error: Optional[str] = None
        self.last_monitor_cycle: Optional[float] = None
        # readiness에서 블로킹을 피하기 위한 비동기 최신 상태 캐시
        self._last_connection_alive: bool = False
        
        logger.info("Leader lock initialized", lock_id=lock_id)
    
    def _create_connection(self) -> psycopg2.extensions.connection:
        """전용 지속 커넥션 생성 (풀 미사용)"""
        conn = psycopg2.connect(self.database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # 연결 성공 시 최신 상태 갱신
        self._last_connection_alive = True
        return conn
    
    def _is_connection_alive(self) -> bool:
        """커넥션 상태 확인"""
        if not self._conn:
            return False
        
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def _try_acquire_lock(self) -> bool:
        """Advisory Lock 획득 시도"""
        if not self._conn:
            return False
        
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT pg_try_advisory_lock(%s)", (self.lock_id,))
                result = cur.fetchone()[0]
                
                if result:
                    with self._lock:
                        self._lock_acquired = True
                        self.last_acquire_time = time.time()
                        self._last_connection_alive = True
                    
                    logger.info("Leader lock acquired", lock_id=self.lock_id)
                
                return result
        except Exception as e:
            self.last_error = str(e)
            logger.error("Lock acquire failed", lock_id=self.lock_id, error=str(e))
            return False
    
    def _release_lock(self) -> bool:
        """Advisory Lock 해제"""
        if not self._conn or not self._lock_acquired:
            return True
        
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", (self.lock_id,))
                result = cur.fetchone()[0]
                
                if result:
                    with self._lock:
                        self._lock_acquired = False
                    
                    logger.info("Leader lock released", lock_id=self.lock_id)
                
                return result
        except Exception as e:
            self.last_error = str(e)
            logger.error("Lock release failed", lock_id=self.lock_id, error=str(e))
            return False
    
    def _reconnect_with_backoff(self) -> bool:
        """지수 백오프로 재연결"""
        backoff = self.reconnect_interval
        
        while not self._stop_event.is_set():
            try:
                if self._conn:
                    self._conn.close()
                
                self._conn = self._create_connection()
                self.reconnect_count += 1
                self._last_connection_alive = True
                logger.info("Database reconnected", 
                          attempt=self.reconnect_count,
                          lock_id=self.lock_id)
                return True
                
            except Exception as e:
                self.last_error = str(e)
                logger.warning("Reconnect failed, retrying", 
                             error=str(e),
                             backoff_sec=backoff,
                             lock_id=self.lock_id)
                
                # 지수 백오프 + 지터
                jitter = random.uniform(0.8, 1.2)
                sleep_time = min(backoff * jitter, self.max_backoff)
                
                if self._stop_event.wait(sleep_time):
                    break  # 중단 신호
                
                backoff = min(backoff * 2, self.max_backoff)
        
        return False
    
    def _monitor_connection(self):
        """커넥션 모니터링 스레드"""
        logger.info("Connection monitor started", lock_id=self.lock_id)
        
        while not self._stop_event.is_set():
            try:
                self.last_monitor_cycle = time.time()
                
                # 커넥션 상태 확인
                alive_now = self._is_connection_alive()
                self._last_connection_alive = alive_now
                if not alive_now:
                    logger.warning("Connection lost", lock_id=self.lock_id)
                    
                    with self._lock:
                        if self._lock_acquired:
                            self._lock_acquired = False
                            logger.warning("Lock status reset due to connection loss", 
                                         lock_id=self.lock_id)
                    
                    # 재연결 시도
                    if self._reconnect_with_backoff():
                        # 재연결 성공 시 락 재획득 시도
                        if self._try_acquire_lock():
                            self._last_connection_alive = True
                            logger.info("Lock re-acquired after reconnection", 
                                      lock_id=self.lock_id)
                
            except Exception as e:
                logger.error("Monitor cycle failed", 
                           lock_id=self.lock_id, 
                           error=str(e))
            
            # 짧은 간격으로 체크 (중단 신호에 빠르게 반응)
            if self._stop_event.wait(0.5):
                break
        
        logger.info("Connection monitor stopped", lock_id=self.lock_id)
    
    def acquire(self) -> bool:
        """락 획득 (초기 연결 포함)"""
        with self._lock:
            if self._lock_acquired:
                return True
        
        self.acquire_attempts += 1
        
        # 초기 연결
        if not self._conn:
            try:
                self._conn = self._create_connection()
                logger.info("Initial database connection established", 
                          lock_id=self.lock_id)
            except Exception as e:
                self.last_error = str(e)
                logger.error("Initial connection failed", 
                           lock_id=self.lock_id, 
                           error=str(e))
                return False
        
        # 락 획득 시도
        if self._try_acquire_lock():
            # 모니터링 스레드 시작
            if not self._monitor_thread or not self._monitor_thread.is_alive():
                self._stop_event.clear()
                self._monitor_thread = threading.Thread(
                    target=self._monitor_connection,
                    name=f"LeaderLockMonitor-{self.lock_id}",
                    daemon=False
                )
                self._monitor_thread.start()
            
            return True
        
        return False
    
    def release(self) -> bool:
        """락 해제 및 정리"""
        success = True
        
        # 모니터링 스레드 중단
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.info("Stopping connection monitor", lock_id=self.lock_id)
            self._stop_event.set()
            self._monitor_thread.join(timeout=2.0)
            
            if self._monitor_thread.is_alive():
                logger.warning("Monitor thread did not stop in time", 
                             lock_id=self.lock_id)
                success = False
        
        # 락 해제
        if not self._release_lock():
            success = False
        
        # 커넥션 정리
        if self._conn:
            try:
                self._conn.close()
                self._conn = None
                logger.info("Database connection closed", lock_id=self.lock_id)
            except Exception as e:
                self.last_error = str(e)
                logger.error("Connection close failed", 
                           lock_id=self.lock_id, 
                           error=str(e))
                success = False
        
        return success
    
    def is_leader(self) -> bool:
        """리더 상태 확인"""
        with self._lock:
            return self._lock_acquired and self._is_connection_alive()
    
    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        with self._lock:
            # readiness 경로에서 DB 동기 질의로 블로킹되지 않도록 내부 캐시만 사용
            is_leader_cached = self._lock_acquired and self._last_connection_alive
            return {
                "is_leader": is_leader_cached,
                "lock_acquired": self._lock_acquired,
                "connection_alive": self._last_connection_alive,
                "acquire_attempts": self.acquire_attempts,
                "reconnect_count": self.reconnect_count,
                "last_acquire_time": self.last_acquire_time,
                "last_monitor_cycle": self.last_monitor_cycle,
                "last_error": self.last_error,
                "monitor_thread_alive": self._monitor_thread.is_alive() if self._monitor_thread else False,
                "lock_id": self.lock_id
            }


# 전역 인스턴스 (싱글톤)
_global_leader_lock: Optional[LeaderLock] = None


def get_leader_lock(database_url: Optional[str] = None, lock_id: int = 54321) -> LeaderLock:
    """전역 리더락 인스턴스 반환 (싱글톤)"""
    global _global_leader_lock
    
    if _global_leader_lock is None:
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise RuntimeError("DATABASE_URL is required for leader lock")
        
        # SQLAlchemy URL을 psycopg2 형식으로 변환
        if database_url.startswith("postgresql+psycopg2://"):
            database_url = database_url.replace("postgresql+psycopg2://", "postgresql://")
        
        _global_leader_lock = LeaderLock(database_url, lock_id)
    
    return _global_leader_lock


@contextmanager
def leader_lock_context(database_url: Optional[str] = None, lock_id: int = 54321):
    """컨텍스트 매니저로 리더락 관리"""
    lock = get_leader_lock(database_url, lock_id)
    
    try:
        success = lock.acquire()
        yield lock, success
    finally:
        if success:
            lock.release()


# 편의 함수들
def acquire_leader_lock(database_url: Optional[str] = None, lock_id: int = 54321) -> bool:
    """리더락 획득"""
    return get_leader_lock(database_url, lock_id).acquire()


def release_leader_lock() -> bool:
    """리더락 해제"""
    global _global_leader_lock
    if _global_leader_lock:
        return _global_leader_lock.release()
    return True


def is_leader() -> bool:
    """현재 리더 상태 확인"""
    global _global_leader_lock
    if _global_leader_lock:
        return _global_leader_lock.is_leader()
    return False


def get_leader_status() -> Dict[str, Any]:
    """리더락 상태 정보 반환"""
    global _global_leader_lock
    if _global_leader_lock:
        return _global_leader_lock.get_status()
    return {
        "is_leader": False,
        "lock_acquired": False,
        "connection_alive": False,
        "acquire_attempts": 0,
        "reconnect_count": 0,
        "last_acquire_time": None,
        "last_monitor_cycle": None,
        "last_error": "Leader lock not initialized",
        "monitor_thread_alive": False,
        "lock_id": None
    }
