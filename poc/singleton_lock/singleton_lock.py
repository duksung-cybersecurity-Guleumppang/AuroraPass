#!/usr/bin/env python3
"""
PoC: singleton_lock
pg_try_advisory_lock 기반 단일 인스턴스 보장, 끊김 시 재연결/재획득 검증
"""
import os
import time
import threading
import random
from typing import Optional, Tuple
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("psycopg2 not available. Install with: pip install psycopg2-binary")
    raise


class SingletonLockPoC:
    """PostgreSQL Advisory Lock을 사용한 단일 인스턴스 보장 PoC"""
    
    def __init__(self, 
                 database_url: str,
                 lock_id: int = 12345,
                 reconnect_interval: float = 1.0,
                 max_backoff: float = 8.0):
        self.database_url = database_url
        self.lock_id = lock_id
        self.reconnect_interval = reconnect_interval
        self.max_backoff = max_backoff
        
        self._conn: Optional[psycopg2.extensions.connection] = None
        self._lock_acquired = False
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
        # 메트릭
        self.acquire_attempts = 0
        self.reconnect_count = 0
        self.last_acquire_time: Optional[float] = None
        self.last_error: Optional[str] = None
    
    def _create_connection(self) -> psycopg2.extensions.connection:
        """전용 지속 커넥션 생성 (풀 미사용)"""
        conn = psycopg2.connect(self.database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
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
                    self._lock_acquired = True
                    self.last_acquire_time = time.time()
                    print(f"[{time.time():.1f}] Lock acquired (id={self.lock_id})")
                
                return result
        except Exception as e:
            self.last_error = str(e)
            print(f"[{time.time():.1f}] Lock acquire failed: {e}")
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
                    self._lock_acquired = False
                    print(f"[{time.time():.1f}] Lock released (id={self.lock_id})")
                
                return result
        except Exception as e:
            self.last_error = str(e)
            print(f"[{time.time():.1f}] Lock release failed: {e}")
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
                print(f"[{time.time():.1f}] Reconnected (attempt #{self.reconnect_count})")
                return True
                
            except Exception as e:
                self.last_error = str(e)
                print(f"[{time.time():.1f}] Reconnect failed: {e}, retrying in {backoff:.1f}s")
                
                # 지수 백오프 + 지터
                jitter = random.uniform(0.8, 1.2)
                sleep_time = min(backoff * jitter, self.max_backoff)
                
                if self._stop_event.wait(sleep_time):
                    break  # 중단 신호
                
                backoff = min(backoff * 2, self.max_backoff)
        
        return False
    
    def _monitor_connection(self):
        """커넥션 모니터링 스레드"""
        print(f"[{time.time():.1f}] Connection monitor started")
        
        while not self._stop_event.is_set():
            # 커넥션 상태 확인
            if not self._is_connection_alive():
                if self._lock_acquired:
                    self._lock_acquired = False
                    print(f"[{time.time():.1f}] Connection lost, lock status reset")
                
                # 재연결 시도
                if self._reconnect_with_backoff():
                    # 재연결 성공 시 락 재획득 시도
                    self._try_acquire_lock()
            
            # 짧은 간격으로 체크 (중단 신호에 빠르게 반응)
            if self._stop_event.wait(0.5):
                break
        
        print(f"[{time.time():.1f}] Connection monitor stopped")
    
    def acquire(self) -> bool:
        """락 획득 (초기 연결 포함)"""
        if self._lock_acquired:
            return True
        
        self.acquire_attempts += 1
        
        # 초기 연결
        if not self._conn:
            try:
                self._conn = self._create_connection()
                print(f"[{time.time():.1f}] Initial connection established")
            except Exception as e:
                self.last_error = str(e)
                print(f"[{time.time():.1f}] Initial connection failed: {e}")
                return False
        
        # 락 획득 시도
        if self._try_acquire_lock():
            # 모니터링 스레드 시작
            if not self._monitor_thread or not self._monitor_thread.is_alive():
                self._stop_event.clear()
                self._monitor_thread = threading.Thread(
                    target=self._monitor_connection,
                    name="ConnectionMonitor",
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
            self._stop_event.set()
            self._monitor_thread.join(timeout=2.0)
            
            if self._monitor_thread.is_alive():
                print(f"[{time.time():.1f}] Monitor thread did not stop in time")
                success = False
        
        # 락 해제
        if not self._release_lock():
            success = False
        
        # 커넥션 정리
        if self._conn:
            try:
                self._conn.close()
                self._conn = None
                print(f"[{time.time():.1f}] Connection closed")
            except Exception as e:
                self.last_error = str(e)
                print(f"[{time.time():.1f}] Connection close failed: {e}")
                success = False
        
        return success
    
    def is_leader(self) -> bool:
        """리더 상태 확인"""
        return self._lock_acquired and self._is_connection_alive()
    
    def get_status(self) -> dict:
        """상태 정보 반환"""
        return {
            "is_leader": self.is_leader(),
            "lock_acquired": self._lock_acquired,
            "connection_alive": self._is_connection_alive(),
            "acquire_attempts": self.acquire_attempts,
            "reconnect_count": self.reconnect_count,
            "last_acquire_time": self.last_acquire_time,
            "last_error": self.last_error,
            "monitor_thread_alive": self._monitor_thread.is_alive() if self._monitor_thread else False
        }


@contextmanager
def singleton_lock_context(database_url: str, lock_id: int = 12345):
    """컨텍스트 매니저로 락 관리"""
    lock = SingletonLockPoC(database_url, lock_id)
    
    try:
        success = lock.acquire()
        yield lock, success
    finally:
        lock.release()


if __name__ == "__main__":
    # 간단한 테스트
    database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/testdb")
    
    print("=== Testing singleton lock ===")
    
    with singleton_lock_context(database_url, lock_id=99999) as (lock, acquired):
        if acquired:
            print("Lock acquired successfully!")
            
            # 몇 초간 유지
            for i in range(5):
                print(f"Working as leader... {i+1}/5")
                print(f"Status: {lock.get_status()}")
                time.sleep(1)
        else:
            print("Failed to acquire lock (another instance may be running)")
    
    print("Lock released, exiting")
