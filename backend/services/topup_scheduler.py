#!/usr/bin/env python3
"""
CAPTCHA Top-up 스케줄러
주기적으로 가용 재고를 확인하고 목표치까지 합성하여 보충
"""
import os
import sys
import time
import threading
from pathlib import Path
from db.session import get_db_session
from sqlalchemy import text
from utils.logging import get_logger

logger = get_logger("topup_scheduler")

# 환경 변수 설정
INVENTORY_TARGET = int(os.getenv("INVENTORY_TARGET", "1000"))
TOP_UP_INTERVAL_SEC = int(os.getenv("TOP_UP_INTERVAL_SEC", "60"))
MAX_PER_TICK = int(os.getenv("MAX_PER_TICK", "200"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))

class TopUpScheduler:
    """CAPTCHA 재고 보충 스케줄러"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        
        # 합성 모듈 임포트
        try:
            poc_path = Path(__file__).parent.parent.parent / "poc" / "captcha_synth"
            sys.path.insert(0, str(poc_path))
            
            scripts_path = Path(__file__).parent.parent / "scripts"
            sys.path.insert(0, str(scripts_path))
            
            from synthesize_captcha import synthesize_single_captcha
            self.synthesize_single_captcha = synthesize_single_captcha
            logger.info("Top-up scheduler initialized", 
                       target=INVENTORY_TARGET, 
                       interval=TOP_UP_INTERVAL_SEC,
                       max_per_tick=MAX_PER_TICK)
        except ImportError as e:
            logger.error("Failed to import synthesis modules", error=str(e))
            self.synthesize_single_captcha = None
    
    def get_available_inventory(self) -> int:
        """현재 가용 재고 수량 조회"""
        try:
            with get_db_session() as session:
                result = session.execute(text("""
                    SELECT COUNT(*) 
                    FROM captcha_files
                    WHERE used = false AND (expires_at IS NULL OR expires_at > now())
                """)).scalar()
                return result or 0
        except Exception as e:
            logger.error("Failed to get available inventory", error=str(e))
            return 0
    
    def calculate_needed(self) -> int:
        """필요한 보충 수량 계산"""
        available = self.get_available_inventory()
        needed = max(0, INVENTORY_TARGET - available)
        return min(needed, MAX_PER_TICK)  # 한 틱당 최대치 제한
    
    def run_synthesis_batch(self, count: int) -> int:
        """배치 단위로 합성 실행"""
        if not self.synthesize_single_captcha:
            logger.warning("Synthesis function not available")
            return 0
        
        success_count = 0
        batches = (count + BATCH_SIZE - 1) // BATCH_SIZE  # 올림 나눗셈
        
        for batch_num in range(batches):
            batch_start = batch_num * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, count)
            batch_size = batch_end - batch_start
            
            logger.info("Starting synthesis batch", 
                       batch=f"{batch_num+1}/{batches}", 
                       size=batch_size)
            
            batch_success = 0
            for i in range(batch_size):
                try:
                    if self.synthesize_single_captcha():
                        batch_success += 1
                        success_count += 1
                except Exception as e:
                    logger.error("Single synthesis failed", 
                               batch=batch_num+1, 
                               item=i+1, 
                               error=str(e))
            
            logger.info("Batch completed", 
                       batch=f"{batch_num+1}/{batches}", 
                       success=f"{batch_success}/{batch_size}")
            
            # 배치 간 짧은 휴식
            if batch_num < batches - 1:
                time.sleep(1)
        
        return success_count
    
    def run_topup_cycle(self):
        """단일 Top-up 사이클 실행"""
        try:
            available = self.get_available_inventory()
            needed = self.calculate_needed()
            
            if needed <= 0:
                logger.debug("Inventory sufficient", 
                           available=available, 
                           target=INVENTORY_TARGET)
                return
            
            logger.info("Starting top-up cycle", 
                       available=available, 
                       target=INVENTORY_TARGET, 
                       needed=needed)
            
            start_time = time.time()
            success_count = self.run_synthesis_batch(needed)
            duration = time.time() - start_time
            
            new_available = self.get_available_inventory()
            
            logger.info("Top-up cycle completed", 
                       requested=needed,
                       success=success_count,
                       duration_sec=f"{duration:.1f}",
                       before=available,
                       after=new_available)
            
        except Exception as e:
            logger.error("Top-up cycle failed", error=str(e))
    
    def scheduler_loop(self):
        """스케줄러 메인 루프"""
        logger.info("Top-up scheduler started")
        
        # 첫 실행 지연 (5-10초)
        initial_delay = 7  # 고정값으로 단순화
        logger.info("Initial delay before first top-up", delay_sec=initial_delay)
        time.sleep(initial_delay)
        
        while self.running:
            try:
                self.run_topup_cycle()
            except Exception as e:
                logger.error("Scheduler loop error", error=str(e))
            
            # 다음 사이클까지 대기
            time.sleep(TOP_UP_INTERVAL_SEC)
        
        logger.info("Top-up scheduler stopped")
    
    def start(self):
        """백그라운드 스케줄러 시작"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.thread.start()
        logger.info("Top-up scheduler thread started")
    
    def stop(self):
        """스케줄러 정지"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Top-up scheduler stopped")

# 전역 인스턴스
topup_scheduler = TopUpScheduler()

def start_topup_scheduler():
    """Top-up 스케줄러 시작 (외부 호출용)"""
    topup_scheduler.start()

def stop_topup_scheduler():
    """Top-up 스케줄러 정지 (외부 호출용)"""
    topup_scheduler.stop()

if __name__ == "__main__":
    # 직접 실행 시 테스트
    print(f"Top-up Scheduler Test")
    print(f"Target: {INVENTORY_TARGET}, Interval: {TOP_UP_INTERVAL_SEC}s")
    
    available = topup_scheduler.get_available_inventory()
    needed = topup_scheduler.calculate_needed()
    
    print(f"Available: {available}, Needed: {needed}")
    
    if needed > 0:
        print(f"Running single top-up cycle...")
        topup_scheduler.run_topup_cycle()
