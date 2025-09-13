#!/usr/bin/env python3
"""
CAPTCHA Top-up 스케줄러 (개편)
주기적으로 가용 재고를 확인하고 목표치까지 합성하여 보충
- 비-데몬 스레드, stop_event, 슬립 분할, 소배치, 메트릭
"""
import os
import sys
import time
import threading
import random
from pathlib import Path
from typing import Optional, Dict, Any
from db.session import get_db_session_with_timeout
from sqlalchemy import text
from utils.logging import get_logger

logger = get_logger("topup_scheduler")

# 환경 변수 설정
INVENTORY_TARGET = int(os.getenv("INVENTORY_TARGET", "1000"))
TOP_UP_INTERVAL_SEC = int(os.getenv("TOP_UP_INTERVAL_SEC", "60"))
MAX_PER_TICK = int(os.getenv("MAX_PER_TICK", "200"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
TOPUP_JOIN_TIMEOUT_SEC = int(os.getenv("TOPUP_JOIN_TIMEOUT_SEC", "25"))


class TopUpScheduler:
    """CAPTCHA 재고 보충 스케줄러 (개편)"""
    
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._lock = threading.Lock()  # 내부 상태 보호
        
        # 메트릭
        self.cycle_count = 0
        self.last_cycle_at: Optional[float] = None
        self.last_duration_ms: Optional[float] = None
        self.last_success = False
        self.error_count = 0
        self.total_synthesized = 0
        
        # 합성 모듈 임포트
        self.synthesize_single_captcha = None
        try:
            # PoC 및 스크립트 경로 등록
            # __file__ = /app/services/topup_scheduler.py
            # repo root = parent.parent → /app
            poc_path = Path(__file__).parent.parent / "poc" / "captcha_synth"
            sys.path.insert(0, str(poc_path))
            
            scripts_path = Path(__file__).parent.parent / "scripts"
            sys.path.insert(0, str(scripts_path))
            
            from synthesize_captcha import synthesize_single_captcha
            self.synthesize_single_captcha = synthesize_single_captcha
            
            logger.info("Top-up scheduler initialized",
                        target=INVENTORY_TARGET,
                        interval=TOP_UP_INTERVAL_SEC,
                        max_per_tick=MAX_PER_TICK,
                        batch_size=BATCH_SIZE,
                        join_timeout=TOPUP_JOIN_TIMEOUT_SEC)
        except ImportError as e:
            logger.error("Failed to import synthesis modules", error=str(e))
    
    def _sleep_with_interrupt_check(self, duration: float, chunk_size: float = 0.5) -> bool:
        """슬립을 청크 단위로 분할하여 중단 신호에 빠르게 반응"""
        elapsed = 0.0
        while elapsed < duration:
            if self._stop_event.is_set():
                return False
            
            chunk = min(chunk_size, duration - elapsed)
            time.sleep(chunk)
            elapsed += chunk
        
        return True
    
    def _get_available_inventory(self) -> int:
        """현재 가용 재고 수량 조회 (소배치)"""
        try:
            with get_db_session_with_timeout(timeout_ms=1000) as session:
                result = session.execute(text("""
                    SELECT COUNT(*) 
                    FROM captcha_files
                    WHERE used = false AND (expires_at IS NULL OR expires_at > now())
                """)).scalar()
                return result or 0
        except Exception as e:
            logger.error("Failed to get available inventory", error=str(e))
            return 0
    
    def _calculate_needed(self) -> int:
        """필요한 보충 수량 계산"""
        available = self._get_available_inventory()
        # 매 사이클마다 최신 환경변수 재적용
        target = int(os.getenv("INVENTORY_TARGET", str(INVENTORY_TARGET)))
        per_tick = int(os.getenv("MAX_PER_TICK", str(MAX_PER_TICK)))
        needed = max(0, target - available)
        needed = min(needed, per_tick)
        
        if not self._stop_event.is_set():  # 종료 중이 아닐 때만 로그
            logger.info("Top-up needed calculation", 
                       available=available, 
                       target=target, 
                       needed=needed)
        
        return needed
    
    def _synthesize_single_with_timeout(self) -> bool:
        """단일 합성 (타임아웃과 중단 체크 포함)"""
        if not self.synthesize_single_captcha:
            return False
        
        try:
            # 중단 체크
            if self._stop_event.is_set():
                return False
            
            # stop_event 연동용 콜백
            def _stop_checker() -> bool:
                return self._stop_event.is_set()

            # 합성 타임아웃 (환경 변수, 기본 10초)
            timeout_sec = float(os.getenv("SYNTHESIS_TIMEOUT_SEC", "10"))

            # 워커 스레드에서 합성 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.synthesize_single_captcha, _stop_checker)
                try:
                    success = future.result(timeout=timeout_sec)
                except concurrent.futures.TimeoutError:
                    logger.warning("Synthesis timed out", timeout_sec=timeout_sec)
                    # 타임아웃 시 이후 아이템 진행 (현재 작업은 포기)
                    return False
            
            if success:
                self.total_synthesized += 1
            
            return success
        except Exception as e:
            logger.error("Single synthesis failed", error=str(e))
            return False
    
    def _run_synthesis_batch(self, count: int) -> int:
        """배치 단위로 합성 실행 (소배치)"""
        if count <= 0:
            return 0
        
        success_count = 0
        batch_size = int(os.getenv("BATCH_SIZE", str(BATCH_SIZE)))
        batches = (count + batch_size - 1) // batch_size
        
        for batch_num in range(batches):
            if self._stop_event.is_set():
                break
            
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, count)
            current_batch_size = batch_end - batch_start
            
            if not self._stop_event.is_set():  # 종료 중이 아닐 때만 로그
                logger.info("Starting synthesis batch", 
                           batch=f"{batch_num+1}/{batches}", 
                           size=current_batch_size)
            
            batch_success = 0
            for i in range(current_batch_size):
                if self._stop_event.is_set():
                    break
                
                if self._synthesize_single_with_timeout():
                    batch_success += 1
                    success_count += 1
                
                # 배치 내 아이템 간 짧은 휴식 (중단 체크 포함)
                if i < current_batch_size - 1:
                    if not self._sleep_with_interrupt_check(0.1):
                        break
            
            if not self._stop_event.is_set():  # 종료 중이 아닐 때만 로그
                logger.info("Batch completed", 
                           batch=f"{batch_num+1}/{batches}", 
                           success=f"{batch_success}/{current_batch_size}")
            
            # 배치 간 휴식
            if batch_num < batches - 1:
                if not self._sleep_with_interrupt_check(1.0):
                    break
        
        return success_count
    
    def _run_topup_cycle(self):
        """단일 Top-up 사이클 실행"""
        cycle_start = time.time()
        
        try:
            with self._lock:
                self.cycle_count += 1
                self.last_cycle_at = cycle_start
            
            available = self._get_available_inventory()
            needed = self._calculate_needed()
            
            if needed <= 0:
                with self._lock:
                    self.last_success = True
                return
            
            if not self._stop_event.is_set():  # 종료 중이 아닐 때만 로그
                logger.info("Starting top-up cycle", 
                           cycle=self.cycle_count,
                           available=available, 
                           target=int(os.getenv("INVENTORY_TARGET", str(INVENTORY_TARGET))), 
                           needed=needed)
            
            success_count = self._run_synthesis_batch(needed)
            new_available = self._get_available_inventory()
            
            with self._lock:
                self.last_success = success_count > 0
                duration_ms = (time.time() - cycle_start) * 1000
                self.last_duration_ms = duration_ms
            
            if not self._stop_event.is_set():  # 종료 중이 아닐 때만 로그
                logger.info("Top-up cycle completed", 
                           cycle=self.cycle_count,
                           requested=needed,
                           success=success_count,
                           duration_ms=f"{duration_ms:.1f}",
                           before=available,
                           after=new_available)
            
        except Exception as e:
            with self._lock:
                self.error_count += 1
                self.last_success = False
            
            logger.error("Top-up cycle failed", 
                       cycle=self.cycle_count,
                       error=str(e))
    
    def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        logger.info("Top-up scheduler started", 
                   daemon=self._thread.daemon if self._thread else False)
        
        # 첫 실행 지연 (5-10초)
        initial_delay = random.uniform(5.0, 10.0)
        if not self._stop_event.is_set():
            logger.info("Initial delay before first top-up", delay_sec=f"{initial_delay:.1f}")
            if not self._sleep_with_interrupt_check(initial_delay):
                logger.info("Scheduler stopped during initial delay")
                return
        
        while not self._stop_event.is_set():
            try:
                self._run_topup_cycle()
            except Exception as e:
                with self._lock:
                    self.error_count += 1
                logger.error("Scheduler loop error", error=str(e))
            
            # 다음 사이클까지 대기 (런타임에 최신 주기 반영)
            interval = int(os.getenv("TOP_UP_INTERVAL_SEC", str(TOP_UP_INTERVAL_SEC)))
            if not self._sleep_with_interrupt_check(interval):
                break
        
        logger.info("Top-up scheduler stopped")
    
    def start(self) -> bool:
        """스케줄러 시작"""
        with self._lock:
            if self._running:
                logger.warning("Scheduler already running")
                return False
            
            self._running = True
        
        self._stop_event.clear()
        
        # 비-데몬 스레드로 생성
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            name="TopUpScheduler",
            daemon=False  # 중요: 비-데몬
        )
        self._thread.start()
        
        logger.info("Top-up scheduler thread started")
        return True
    
    def stop(self) -> None:
        """스케줄러 정지 신호 전송 (비블로킹)"""
        with self._lock:
            if not self._running:
                return
        
        logger.info("Sending stop signal to scheduler")
        self._stop_event.set()
    
    def join(self, timeout: Optional[float] = None) -> bool:
        """스레드 종료 대기 (유한 시간)"""
        with self._lock:
            if not self._thread or not self._running:
                return True
        
        effective_timeout = timeout or TOPUP_JOIN_TIMEOUT_SEC
        logger.info("Waiting for scheduler to stop", timeout_sec=effective_timeout)
        
        self._thread.join(effective_timeout)
        
        is_alive = self._thread.is_alive()
        with self._lock:
            if not is_alive:
                self._running = False
                logger.info("Scheduler stopped successfully")
            else:
                logger.warning("Scheduler still running after timeout")
        
        return not is_alive
    
    def is_running(self) -> bool:
        """실행 상태 확인"""
        with self._lock:
            return self._running and self._thread and self._thread.is_alive()
    
    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환 (메트릭 포함)"""
        with self._lock:
            return {
                "running": self.is_running(),
                "cycle_count": self.cycle_count,
                "last_cycle_at": self.last_cycle_at,
                "last_duration_ms": self.last_duration_ms,
                "last_success": self.last_success,
                "error_count": self.error_count,
                "total_synthesized": self.total_synthesized,
                "thread_alive": self._thread.is_alive() if self._thread else False,
                "stop_event_set": self._stop_event.is_set()
            }


# 전역 인스턴스 (싱글톤)
_global_scheduler: Optional[TopUpScheduler] = None


def get_topup_scheduler() -> TopUpScheduler:
    """전역 스케줄러 인스턴스 반환 (싱글톤)"""
    global _global_scheduler
    
    if _global_scheduler is None:
        _global_scheduler = TopUpScheduler()
    
    return _global_scheduler


def start_topup_scheduler() -> bool:
    """Top-up 스케줄러 시작 (외부 호출용)"""
    return get_topup_scheduler().start()


def stop_topup_scheduler() -> None:
    """Top-up 스케줄러 정지 (외부 호출용)"""
    get_topup_scheduler().stop()


def join_topup_scheduler(timeout: Optional[float] = None) -> bool:
    """Top-up 스케줄러 종료 대기 (외부 호출용)"""
    return get_topup_scheduler().join(timeout)


def get_topup_status() -> Dict[str, Any]:
    """Top-up 스케줄러 상태 반환 (외부 호출용)"""
    global _global_scheduler
    if _global_scheduler:
        return _global_scheduler.get_status()
    return {
        "running": False,
        "cycle_count": 0,
        "last_cycle_at": None,
        "last_duration_ms": None,
        "last_success": False,
        "error_count": 0,
        "total_synthesized": 0,
        "thread_alive": False,
        "stop_event_set": False
    }


if __name__ == "__main__":
    # 직접 실행 시 테스트
    print(f"Top-up Scheduler Test (Refactored)")
    print(f"Target: {INVENTORY_TARGET}, Interval: {TOP_UP_INTERVAL_SEC}s")
    
    scheduler = get_topup_scheduler()
    
    available = scheduler._get_available_inventory()
    needed = scheduler._calculate_needed()
    
    print(f"Available: {available}, Needed: {needed}")
    
    if needed > 0:
        print(f"Running single top-up cycle...")
        scheduler._run_topup_cycle()
        print(f"Status: {scheduler.get_status()}")