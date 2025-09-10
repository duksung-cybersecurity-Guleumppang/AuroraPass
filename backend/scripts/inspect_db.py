#!/usr/bin/env python3
"""
DB 상태 점검 스크립트
운영자가 재고와 적재 현황을 확인할 수 있는 점검 도구
"""
from db.session import get_db_session
from sqlalchemy import text
from datetime import datetime

def print_section_header(title: str):
    """섹션 헤더 출력"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def inspect_captcha_files():
    """CAPTCHA 파일 현황 점검"""
    print_section_header("CAPTCHA FILES 현황")
    
    try:
        with get_db_session() as session:
            # 전체 및 가용 건수
            stats = session.execute(text("""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(*) FILTER (WHERE used = false AND (expires_at IS NULL OR expires_at > now())) as available_count,
                    COUNT(*) FILTER (WHERE used = true) as used_count,
                    COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at <= now()) as expired_count
                FROM captcha_files
            """)).fetchone()
            
            print(f" 전체 통계:")
            print(f"   - 총 CAPTCHA 수: {stats.total_count:,}")
            print(f"   - 사용 가능: {stats.available_count:,}")
            print(f"   - 사용됨: {stats.used_count:,}")
            print(f"   - 만료됨: {stats.expired_count:,}")
            
            if stats.available_count > 0:
                availability_pct = (stats.available_count / stats.total_count) * 100
                print(f"   - 가용률: {availability_pct:.1f}%")
            
            # 최근 10개 합성 현황
            recent = session.execute(text("""
                SELECT id, filename, created_at, used, 
                       CASE WHEN expires_at IS NOT NULL AND expires_at <= now() THEN true ELSE false END as expired
                FROM captcha_files 
                ORDER BY created_at DESC 
                LIMIT 10
            """)).fetchall()
            
            print(f"\n 최근 10개 CAPTCHA:")
            if recent:
                for i, row in enumerate(recent, 1):
                    status = "사용됨" if row.used else ("만료" if row.expired else "가용")
                    created = row.created_at.strftime("%m-%d %H:%M:%S") if row.created_at else "N/A"
                    print(f"   {i:2d}. {row.id[:8]}... | {row.filename[:30]:<30} | {created} | {status}")
            else:
                print("   (데이터 없음)")
                
    except Exception as e:
        print(f" CAPTCHA 파일 점검 실패: {e}")

def inspect_audio_sources():
    """오디오 소스 현황 점검"""
    print_section_header("AUDIO SOURCES 현황")
    
    try:
        with get_db_session() as session:
            # 언어별 통계
            lang_stats = session.execute(text("""
                SELECT 
                    language,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_duration_ms,
                    SUM(LENGTH(audio_data)) as total_bytes
                FROM audio_sources 
                GROUP BY language
                ORDER BY language
            """)).fetchall()
            
            print(f" 언어별 통계:")
            total_files = 0
            total_bytes = 0
            
            for row in lang_stats:
                total_files += row.count
                total_bytes += row.total_bytes or 0
                avg_duration = f"{row.avg_duration_ms/1000:.1f}s" if row.avg_duration_ms else "N/A"
                size_mb = (row.total_bytes or 0) / (1024*1024)
                
                print(f"   - {row.language.upper()}: {row.count:,}개 파일, 평균 {avg_duration}, {size_mb:.1f}MB")
            
            print(f"   - 총합: {total_files:,}개 파일, {total_bytes/(1024*1024):.1f}MB")
            
            # 최근 사용량 (합성에 사용된 횟수)
            usage_stats = session.execute(text("""
                SELECT 
                    s.language,
                    s.original_filename,
                    COUNT(c.id) as usage_count,
                    MAX(c.created_at) as last_used
                FROM audio_sources s
                LEFT JOIN captcha_files c ON 
                    (s.language = 'ko' AND c.ko_source_id = s.id) OR
                    (s.language = 'en' AND c.en_source_id = s.id)
                WHERE c.created_at >= now() - interval '30 days'
                GROUP BY s.id, s.language, s.original_filename
                ORDER BY usage_count DESC, s.language
                LIMIT 10
            """)).fetchall()
            
            print(f"\n 최근 30일 사용량 TOP 10:")
            if usage_stats:
                for i, row in enumerate(usage_stats, 1):
                    last_used = row.last_used.strftime("%m-%d %H:%M") if row.last_used else "사용안됨"
                    print(f"   {i:2d}. {row.language.upper()} | {row.original_filename:<20} | 사용 {row.usage_count:3d}회 | {last_used}")
            else:
                print("   (최근 사용 데이터 없음)")
                
    except Exception as e:
        print(f" 오디오 소스 점검 실패: {e}")

def inspect_ko_source_answers():
    """한글 정답 사전 현황 점검"""
    print_section_header("KO SOURCE ANSWERS 현황")
    
    try:
        with get_db_session() as session:
            # 전체 통계
            stats = session.execute(text("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(ko_source_id) as linked_count,
                    AVG(LENGTH(answer)) as avg_answer_length
                FROM ko_source_answers
            """)).fetchone()
            
            print(f" 정답 사전 통계:")
            print(f"   - 총 정답 수: {stats.total_rows:,}")
            print(f"   - 소스 연결: {stats.linked_count:,}")
            print(f"   - 평균 정답 길이: {stats.avg_answer_length:.1f}자")
            
            if stats.linked_count and stats.total_rows:
                link_pct = (stats.linked_count / stats.total_rows) * 100
                print(f"   - 연결률: {link_pct:.1f}%")
            
            # 샘플 데이터
            samples = session.execute(text("""
                SELECT ko_key, question, answer, 
                       CASE WHEN ko_source_id IS NOT NULL THEN 'Y' ELSE 'N' END as linked
                FROM ko_source_answers 
                ORDER BY ko_key 
                LIMIT 10
            """)).fetchall()
            
            print(f"\n 샘플 정답 (처음 10개):")
            if samples:
                for i, row in enumerate(samples, 1):
                    question_short = (row.question[:30] + '...') if len(row.question) > 30 else row.question
                    print(f"   {i:2d}. {row.ko_key:<8} | {question_short:<33} | {row.answer:<10} | 연결:{row.linked}")
            else:
                print("   (데이터 없음)")
                
    except Exception as e:
        print(f" 정답 사전 점검 실패: {e}")

def inspect_system_health():
    """시스템 건강성 점검"""
    print_section_header("시스템 건강성 점검")
    
    try:
        with get_db_session() as session:
            # 재고 부족 경고
            available = session.execute(text("""
                SELECT COUNT(*) 
                FROM captcha_files
                WHERE used = false AND (expires_at IS NULL OR expires_at > now())
            """)).scalar()
            
            import os
            target = int(os.getenv("INVENTORY_TARGET", "1000"))
            
            print(f" 재고 상태:")
            print(f"   - 현재 가용: {available:,}")
            print(f"   - 목표 재고: {target:,}")
            
            if available < target * 0.1:  # 10% 미만
                print(f"     심각한 재고 부족! (목표의 {available/target*100:.1f}%)")
            elif available < target * 0.3:  # 30% 미만
                print(f"     재고 부족 주의 (목표의 {available/target*100:.1f}%)")
            else:
                print(f"    재고 양호 (목표의 {available/target*100:.1f}%)")
            
            # 합성 실패율 점검 (최근 24시간)
            synthesis_stats = session.execute(text("""
                SELECT 
                    COUNT(*) as recent_synthesis,
                    COUNT(*) FILTER (WHERE pipeline_version IS NOT NULL) as successful_synthesis
                FROM captcha_files 
                WHERE created_at >= now() - interval '24 hours'
                  AND (ko_source_id IS NOT NULL OR en_source_id IS NOT NULL)
            """)).fetchone()
            
            print(f"\n🔧 합성 상태 (최근 24시간):")
            if synthesis_stats.recent_synthesis > 0:
                success_rate = (synthesis_stats.successful_synthesis / synthesis_stats.recent_synthesis) * 100
                print(f"   - 합성 시도: {synthesis_stats.recent_synthesis:,}")
                print(f"   - 성공률: {success_rate:.1f}%")
                
                if success_rate < 80:
                    print(f"     합성 성공률 낮음!")
                else:
                    print(f"    합성 성공률 양호")
            else:
                print(f"   - 최근 합성 활동 없음")
                
    except Exception as e:
        print(f" 시스템 건강성 점검 실패: {e}")

def main():
    """메인 점검 실행"""
    print(f" AuroraPass DB 상태 점검")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 각 섹션별 점검 실행
    inspect_captcha_files()
    inspect_audio_sources()
    inspect_ko_source_answers()
    inspect_system_health()
    
    print(f"\n{'='*60}")
    print(f" 점검 완료")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
