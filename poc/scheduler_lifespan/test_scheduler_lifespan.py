#!/usr/bin/env python3
"""
PoC: scheduler_lifespan 테스트
비-데몬 스레드, stop_event, 슬립 분할, stop()→join(timeout) 동작 검증
"""
import time
import threading
from scheduler_lifespan import SchedulerLifespanPoC


def test_basic_start_stop():
    """기본 시작/정지 테스트"""
    print("=== Test: Basic start/stop ===")
    
    scheduler = SchedulerLifespanPoC(work_interval=0.2, sleep_chunk=0.05)
    
    # 시작
    assert scheduler.start() == True
    assert scheduler.is_running() == True
    
    # 몇 사이클 실행
    time.sleep(0.6)
    
    # 정지
    scheduler.stop()
    success = scheduler.join(timeout=2.0)
    
    assert success == True
    assert scheduler.is_running() == False
    
    status = scheduler.get_status()
    print(f"Cycles completed: {status['cycle_count']}")
    assert status['cycle_count'] >= 2  # 최소 2사이클은 실행되어야 함
    
    print("✓ Basic start/stop test passed\n")


def test_fast_interrupt():
    """빠른 중단 테스트 (슬립 분할 효과 검증)"""
    print("=== Test: Fast interrupt ===")
    
    scheduler = SchedulerLifespanPoC(work_interval=5.0, sleep_chunk=0.1)  # 긴 주기, 짧은 청크
    
    start_time = time.time()
    
    # 시작
    scheduler.start()
    
    # 짧은 시간 후 정지 (work_interval보다 훨씬 짧음)
    time.sleep(0.3)
    scheduler.stop()
    
    success = scheduler.join(timeout=1.0)
    elapsed = time.time() - start_time
    
    assert success == True
    assert elapsed < 1.0  # 1초 내에 종료되어야 함 (5초 주기임에도)
    
    print(f"Interrupted in {elapsed:.2f}s (expected < 1.0s)")
    print("✓ Fast interrupt test passed\n")


def test_timeout_scenario():
    """타임아웃 시나리오 테스트"""
    print("=== Test: Timeout scenario ===")
    
    class SlowScheduler(SchedulerLifespanPoC):
        """의도적으로 느린 스케줄러"""
        
        def _work_unit(self):
            """긴 작업 시뮬레이션"""
            print(f"[{time.time():.1f}] Starting slow work...")
            time.sleep(2.0)  # 2초 작업
            print(f"[{time.time():.1f}] Slow work completed")
            return super()._work_unit()
    
    scheduler = SlowScheduler(work_interval=0.1, sleep_chunk=0.1)
    
    # 시작
    scheduler.start()
    time.sleep(0.1)  # 작업이 시작되도록 잠시 대기
    
    # 정지 신호 전송
    scheduler.stop()
    
    # 짧은 타임아웃으로 join (실패해야 함)
    success = scheduler.join(timeout=0.5)
    
    assert success == False  # 타임아웃으로 실패해야 함
    assert scheduler._thread.is_alive() == True  # 스레드는 여전히 살아있어야 함
    
    # 충분한 시간으로 다시 대기
    success = scheduler.join(timeout=3.0)
    assert success == True
    
    print("✓ Timeout scenario test passed\n")


def test_non_daemon_thread():
    """비-데몬 스레드 검증"""
    print("=== Test: Non-daemon thread ===")
    
    scheduler = SchedulerLifespanPoC(work_interval=0.1, sleep_chunk=0.05)
    
    scheduler.start()
    
    # 스레드가 비-데몬인지 확인
    assert scheduler._thread.daemon == False
    
    # 메인 스레드 외에 활성 비-데몬 스레드가 있는지 확인
    active_threads = [t for t in threading.enumerate() if t.is_alive() and not t.daemon]
    non_main_threads = [t for t in active_threads if t != threading.main_thread()]
    
    assert len(non_main_threads) >= 1  # 스케줄러 스레드가 포함되어야 함
    
    scheduler.stop()
    scheduler.join(timeout=2.0)
    
    print("✓ Non-daemon thread test passed\n")


def test_multiple_start_calls():
    """중복 시작 호출 테스트"""
    print("=== Test: Multiple start calls ===")
    
    scheduler = SchedulerLifespanPoC(work_interval=0.2, sleep_chunk=0.05)
    
    # 첫 번째 시작
    result1 = scheduler.start()
    assert result1 == True
    
    # 두 번째 시작 (실패해야 함)
    result2 = scheduler.start()
    assert result2 == False
    
    scheduler.stop()
    scheduler.join(timeout=2.0)
    
    print("✓ Multiple start calls test passed\n")


def run_all_tests():
    """모든 테스트 실행"""
    print("Starting scheduler lifespan PoC tests...\n")
    
    try:
        test_basic_start_stop()
        test_fast_interrupt()
        test_timeout_scenario()
        test_non_daemon_thread()
        test_multiple_start_calls()
        
        print(" All tests passed!")
        return True
        
    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
