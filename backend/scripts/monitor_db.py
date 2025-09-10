#!/usr/bin/env python3
"""
DB 실시간 모니터링 스크립트
데이터베이스 상태를 실시간으로 모니터링하고 변화를 추적
"""
import time
import os
from datetime import datetime
from db.session import get_db_session
from sqlalchemy import text

def clear_screen():
    """화면 지우기"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_current_stats():
    """현재 상태 통계 조회"""
    try:
        with get_db_session() as session:
            # CAPTCHA 파일 통계
            captcha_stats = session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE used = false AND (expires_at IS NULL OR expires_at > now())) as available,
                    COUNT(*) FILTER (WHERE used = true) as used,
                    COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at <= now()) as expired,
                    COUNT(*) FILTER (WHERE created_at >= now() - interval '1 hour') as created_last_hour,
                    COUNT(*) FILTER (WHERE used = true AND created_at >= now() - interval '1 hour') as used_last_hour
                FROM captcha_files
            """)).fetchone()
            
            # 오디오 소스 통계
            audio_stats = session.execute(text("""
                SELECT 
                    COUNT(*) FILTER (WHERE language = 'ko') as ko_count,
                    COUNT(*) FILTER (WHERE language = 'en') as en_count
                FROM audio_sources
            """)).fetchall()
            
            ko_count = audio_stats[0][0] if audio_stats else 0
            en_count = audio_stats[0][1] if audio_stats else 0
            
            # 정답 사전 통계
            answers_count = session.execute(text("""
                SELECT COUNT(*) FROM ko_source_answers
            """)).scalar()
            
            # Redis 통계
            try:
                from db.redis_client import redis_client
                redis_keys = len(redis_client.keys('*'))
                captcha_keys = len(redis_client.keys('captcha:*'))
                redis_connected = True
            except:
                redis_keys = 0
                captcha_keys = 0
                redis_connected = False
            
            return {
                'captcha': captcha_stats,
                'ko_sources': ko_count,
                'en_sources': en_count,
                'answers': answers_count,
                'redis_keys': redis_keys,
                'captcha_keys': captcha_keys,
                'redis_connected': redis_connected,
                'timestamp': datetime.now()
            }
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now()}

def display_stats(stats, previous_stats=None):
    """통계 화면 출력"""
    clear_screen()
    
    print(" AuroraPass DB 실시간 모니터링")
    print("=" * 60)
    print(f"업데이트 시간: {stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    if 'error' in stats:
        print(f"\n 오류: {stats['error']}")
        return
    
    captcha = stats['captcha']
    
    print(f"\n CAPTCHA 파일 상태:")
    print(f"   총 개수: {captcha.total:,}")
    print(f"   사용가능: {captcha.available:,}")
    print(f"   사용됨: {captcha.used:,}")
    print(f"   만료됨: {captcha.expired:,}")
    
    # 가용률 계산 및 경고
    if captcha.total > 0:
        availability_pct = (captcha.available / captcha.total) * 100
        if availability_pct < 10:
            status_icon = "🔴"
            status_text = "심각한 재고 부족!"
        elif availability_pct < 30:
            status_icon = "🟡"
            status_text = "재고 부족 주의"
        else:
            status_icon = "🟢"
            status_text = "재고 양호"
        
        print(f"   가용률: {availability_pct:.1f}% {status_icon} {status_text}")
    
    print(f"\n 최근 1시간 활동:")
    print(f"   생성됨: {captcha.created_last_hour:,}개")
    print(f"   사용됨: {captcha.used_last_hour:,}개")
    
    # 변화량 표시 (이전 통계가 있을 때)
    if previous_stats and 'captcha' in previous_stats:
        prev_captcha = previous_stats['captcha']
        
        total_change = captcha.total - prev_captcha.total
        available_change = captcha.available - prev_captcha.available
        used_change = captcha.used - prev_captcha.used
        
        print(f"\n 변화량 (이전 대비):")
        print(f"   총 개수: {total_change:+,}")
        print(f"   사용가능: {available_change:+,}")
        print(f"   사용됨: {used_change:+,}")
    
    print(f"\n🎵 오디오 소스:")
    print(f"   한글: {stats['ko_sources']:,}개")
    print(f"   영어: {stats['en_sources']:,}개")
    
    print(f"\n 정답 사전: {stats['answers']:,}개")
    
    print(f"\n Redis 상태:")
    if stats['redis_connected']:
        print(f"   연결:  정상")
        print(f"   전체 키: {stats['redis_keys']:,}개")
        print(f"   CAPTCHA 키: {stats['captcha_keys']:,}개")
    else:
        print(f"   연결:  실패")
    
    # 환경 설정 표시
    target = int(os.getenv("INVENTORY_TARGET", "1000"))
    interval = int(os.getenv("TOP_UP_INTERVAL_SEC", "60"))
    
    print(f"\n 설정:")
    print(f"   목표 재고: {target:,}개")
    print(f"   보충 주기: {interval}초")
    
    print(f"\n 명령어: Ctrl+C로 종료, Enter로 즉시 새로고침")
    print("-" * 60)

def monitor_loop(refresh_interval=10):
    """모니터링 루프 실행"""
    previous_stats = None
    
    try:
        while True:
            current_stats = get_current_stats()
            display_stats(current_stats, previous_stats)
            previous_stats = current_stats
            
            # 새로고침 대기 (Enter 키로 즉시 새로고침 가능)
            import select
            import sys
            
            print(f"다음 새로고침까지 {refresh_interval}초... (Enter: 즉시 새로고침)")
            
            for i in range(refresh_interval):
                # 논블로킹 입력 체크 (Unix/Linux/macOS만)
                if hasattr(select, 'select'):
                    ready, _, _ = select.select([sys.stdin], [], [], 1)
                    if ready:
                        sys.stdin.readline()  # Enter 키 소비
                        break
                else:
                    # Windows에서는 단순 대기
                    time.sleep(1)
                
                if i < refresh_interval - 1:
                    # 진행률 표시 업데이트
                    remaining = refresh_interval - i - 1
                    print(f"\r다음 새로고침까지 {remaining}초...    ", end='', flush=True)
            
            print()  # 줄바꿈
            
    except KeyboardInterrupt:
        print(f"\n\n모니터링을 종료합니다.")
    except Exception as e:
        print(f"\n\n모니터링 오류: {e}")

def main():
    """메인 실행"""
    import sys
    
    refresh_interval = 10  # 기본 10초
    
    if len(sys.argv) > 1:
        try:
            refresh_interval = int(sys.argv[1])
            if refresh_interval < 1:
                refresh_interval = 1
        except ValueError:
            print(f"잘못된 새로고침 간격: {sys.argv[1]}")
            print(f"사용법: python monitor_db.py [새로고침_간격_초]")
            return
    
    print(f"DB 실시간 모니터링을 시작합니다... (새로고침: {refresh_interval}초)")
    time.sleep(1)
    
    monitor_loop(refresh_interval)

if __name__ == "__main__":
    main()
