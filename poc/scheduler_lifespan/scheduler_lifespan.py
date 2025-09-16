#!/usr/bin/env python3
"""
PoC: scheduler_lifespan
비-데몬 스레드, stop_event, 슬립 분할, stop()→join(timeout) 검증
"""
import threading
import time
from typing import Optional


class SchedulerLifespanPoC:
    """스케줄러 라이프사이클 PoC"""
    
    def __init__(self, work_interval: float = 1.0, sleep_chunk: float = 0.1):
        self.work_interval = work_interval  # 작업 주기
        self.sleep_chunk = sleep_chunk      # 슬립 분할 단위
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
        # 메트릭
        self.cycle_count = 0
        self.last_work_time: Optional[float] = None
        
    def _work_unit(self):
        """단위 작업 (실제 스케줄러의 한 사이클)"""
        self.cycle_count += 1
        self.last_work_time = time.time()
        print(f"[{time.time():.1f}] Work cycle #{self.cycle_count}")
        
        # 작업 시뮬레이션 (짧은 시간)
        time.sleep(0.05)
        
        # 중단 체크 (작업 도중에도)
        if self._stop_event.is_set():
            print(f"[{time.time():.1f}] Work interrupted by stop signal")
            return False
        
        return True
    
    def _sleep_with_interrupt_check(self, duration: float) -> bool:
        """슬립을 청크 단위로 분할하여 중단 신호에 빠르게 반응"""
        elapsed = 0.0
        while elapsed < duration:
            if self._stop_event.is_set():
                print(f"[{time.time():.1f}] Sleep interrupted after {elapsed:.2f}s")
                return False
            
            chunk = min(self.sleep_chunk, duration - elapsed)
            time.sleep(chunk)
            elapsed += chunk
        
        return True
    
    def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        print(f"[{time.time():.1f}] Scheduler started (daemon={self._thread.daemon})")
        
        while not self._stop_event.is_set():
            # 단위 작업 수행
            if not self._work_unit():
                break
            
            # 다음 주기까지 대기 (중단 신호에 빠르게 반응)
            if not self._sleep_with_interrupt_check(self.work_interval):
                break
        
        print(f"[{time.time():.1f}] Scheduler loop ended")
    
    def start(self) -> bool:
        """스케줄러 시작"""
        if self._running:
            print("Scheduler already running")
            return False
        
        self._stop_event.clear()
        self._running = True
        
        # 비-데몬 스레드로 생성
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            name="SchedulerPoC",
            daemon=False  # 중요: 비-데몬
        )
        self._thread.start()
        
        print(f"[{time.time():.1f}] Scheduler thread started")
        return True
    
    def stop(self) -> None:
        """스케줄러 정지 신호 전송 (비블로킹)"""
        if not self._running:
            return
        
        print(f"[{time.time():.1f}] Sending stop signal")
        self._stop_event.set()
    
    def join(self, timeout: Optional[float] = None) -> bool:
        """스레드 종료 대기 (유한 시간)"""
        if not self._thread or not self._running:
            return True
        
        print(f"[{time.time():.1f}] Waiting for scheduler to stop (timeout={timeout})")
        self._thread.join(timeout)
        
        is_alive = self._thread.is_alive()
        if not is_alive:
            self._running = False
            print(f"[{time.time():.1f}] Scheduler stopped successfully")
        else:
            print(f"[{time.time():.1f}] Scheduler still running after timeout")
        
        return not is_alive
    
    def is_running(self) -> bool:
        """실행 상태 확인"""
        return self._running and self._thread and self._thread.is_alive()
    
    def get_status(self) -> dict:
        """상태 정보 반환"""
        return {
            "running": self.is_running(),
            "cycle_count": self.cycle_count,
            "last_work_time": self.last_work_time,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "stop_event_set": self._stop_event.is_set()
        }


if __name__ == "__main__":
    # 간단한 테스트
    scheduler = SchedulerLifespanPoC(work_interval=0.5, sleep_chunk=0.1)
    
    print("=== Starting scheduler ===")
    scheduler.start()
    
    # 몇 초 실행
    time.sleep(2.0)
    
    print("\n=== Stopping scheduler ===")
    scheduler.stop()
    
    # 유한 시간 대기
    success = scheduler.join(timeout=3.0)
    
    print(f"\n=== Final status ===")
    print(f"Stop success: {success}")
    print(f"Status: {scheduler.get_status()}")
