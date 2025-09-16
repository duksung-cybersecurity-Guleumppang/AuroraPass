#!/usr/bin/env python3
"""
DB 디버깅 스크립트
데이터베이스 내부 상태를 상세히 확인하고 디버깅할 수 있는 도구
"""
import sys
import json
from datetime import datetime, timedelta
from db.session import get_db_session
from sqlalchemy import text

def print_separator(title: str = "", char: str = "-", width: int = 80):
    """구분선 출력"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(f"{char * padding}{title_line}{char * padding}")
    else:
        print(char * width)

def debug_table_schema():
    """테이블 스키마 정보 출력"""
    print_separator("TABLE SCHEMA DEBUG", "=")
    
    try:
        with get_db_session() as session:
            # 모든 테이블 목록
            tables = session.execute(text("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)).fetchall()
            
            print(f" 총 {len(tables)}개 테이블:")
            for table in tables:
                print(f"   - {table.table_name} ({table.table_type})")
            
            # 각 테이블의 컬럼 정보
            for table in tables:
                table_name = table.table_name
                print_separator(f"TABLE: {table_name.upper()}")
                
                columns = session.execute(text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = :table_name
                    ORDER BY ordinal_position
                """), {"table_name": table_name}).fetchall()
                
                print(f"컬럼 정보 ({len(columns)}개):")
                for col in columns:
                    nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                    default = f" DEFAULT {col.column_default}" if col.column_default else ""
                    max_len = f"({col.character_maximum_length})" if col.character_maximum_length else ""
                    print(f"   {col.column_name:<20} {col.data_type}{max_len:<15} {nullable}{default}")
                
                # 인덱스 정보
                indexes = session.execute(text("""
                    SELECT 
                        i.indexname,
                        i.indexdef
                    FROM pg_indexes i
                    WHERE i.schemaname = 'public' AND i.tablename = :table_name
                    ORDER BY i.indexname
                """), {"table_name": table_name}).fetchall()
                
                if indexes:
                    print(f"\n인덱스 ({len(indexes)}개):")
                    for idx in indexes:
                        print(f"   {idx.indexname}")
                        print(f"   └─ {idx.indexdef}")
                
                print()
                
    except Exception as e:
        print(f" 스키마 정보 조회 실패: {e}")

def debug_captcha_files():
    """CAPTCHA 파일 상세 디버깅"""
    print_separator("CAPTCHA FILES DEBUG", "=")
    
    try:
        with get_db_session() as session:
            # 전체 통계
            stats = session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE used = false) as unused,
                    COUNT(*) FILTER (WHERE used = true) as used,
                    COUNT(*) FILTER (WHERE expires_at IS NOT NULL) as has_expiry,
                    COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at <= now()) as expired,
                    COUNT(*) FILTER (WHERE ko_source_id IS NOT NULL) as has_ko_source,
                    COUNT(*) FILTER (WHERE en_source_id IS NOT NULL) as has_en_source,
                    COUNT(*) FILTER (WHERE pipeline_version IS NOT NULL) as synthesized,
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest,
                    AVG(duration_ms) as avg_duration,
                    SUM(LENGTH(audio_data)) as total_bytes
                FROM captcha_files
            """)).fetchone()
            
            print(f" 전체 통계:")
            print(f"   총 개수: {stats.total:,}")
            print(f"   미사용: {stats.unused:,} | 사용됨: {stats.used:,}")
            print(f"   만료설정: {stats.has_expiry:,} | 만료됨: {stats.expired:,}")
            print(f"   한글소스: {stats.has_ko_source:,} | 영어소스: {stats.has_en_source:,}")
            print(f"   합성생성: {stats.synthesized:,}")
            print(f"   생성기간: {stats.oldest} ~ {stats.newest}")
            print(f"   평균길이: {stats.avg_duration/1000:.1f}초" if stats.avg_duration else "N/A")
            print(f"   총 용량: {stats.total_bytes/(1024*1024):.1f}MB" if stats.total_bytes else "N/A")
            
            # 파이프라인 버전별 통계
            pipeline_stats = session.execute(text("""
                SELECT 
                    COALESCE(pipeline_version, 'legacy') as version,
                    COUNT(*) as count,
                    COUNT(*) FILTER (WHERE used = false) as available
                FROM captcha_files
                GROUP BY pipeline_version
                ORDER BY version
            """)).fetchall()
            
            print(f"\n 파이프라인별 통계:")
            for ps in pipeline_stats:
                print(f"   {ps.version}: {ps.count:,}개 (가용: {ps.available:,})")
            
            # 최근 생성된 항목들 (상세)
            recent_items = session.execute(text("""
                SELECT 
                    id, filename, answer, used,
                    expires_at, created_at, pipeline_version,
                    duration_ms, LENGTH(audio_data) as size_bytes,
                    audio_hash
                FROM captcha_files
                ORDER BY created_at DESC
                LIMIT 10
            """)).fetchall()
            
            print(f"\n 최근 10개 항목 (상세):")
            for i, item in enumerate(recent_items, 1):
                status = "사용됨" if item.used else "가용"
                expired = ""
                if item.expires_at:
                    if item.expires_at <= datetime.now():
                        expired = " [만료]"
                    else:
                        expired = f" [만료예정: {item.expires_at.strftime('%m-%d %H:%M')}]"
                
                created = item.created_at.strftime("%m-%d %H:%M:%S") if item.created_at else "N/A"
                duration = f"{item.duration_ms/1000:.1f}s" if item.duration_ms else "N/A"
                size_kb = item.size_bytes / 1024 if item.size_bytes else 0
                hash_short = item.audio_hash[:8] if item.audio_hash else "N/A"
                version = item.pipeline_version or "legacy"
                
                print(f"   {i:2d}. {item.id[:8]}... | {status}{expired}")
                print(f"       파일: {item.filename}")
                print(f"       정답: {item.answer} | 길이: {duration} | 크기: {size_kb:.1f}KB")
                print(f"       생성: {created} | 버전: {version} | 해시: {hash_short}...")
                print()
                
    except Exception as e:
        print(f" CAPTCHA 파일 디버깅 실패: {e}")

def debug_audio_sources():
    """오디오 소스 상세 디버깅"""
    print_separator("AUDIO SOURCES DEBUG", "=")
    
    try:
        with get_db_session() as session:
            # 전체 통계
            stats = session.execute(text("""
                SELECT 
                    language,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_duration,
                    MIN(duration_ms) as min_duration,
                    MAX(duration_ms) as max_duration,
                    AVG(sample_rate) as avg_sample_rate,
                    SUM(LENGTH(audio_data)) as total_bytes,
                    COUNT(DISTINCT audio_hash) as unique_hashes
                FROM audio_sources
                GROUP BY language
                ORDER BY language
            """)).fetchall()
            
            print(f" 언어별 상세 통계:")
            for stat in stats:
                print(f"   {stat.language.upper()}:")
                print(f"     파일 수: {stat.count:,}")
                print(f"     길이: 평균 {stat.avg_duration/1000:.1f}s, 범위 {stat.min_duration/1000:.1f}~{stat.max_duration/1000:.1f}s")
                print(f"     샘플레이트: 평균 {stat.avg_sample_rate:.0f}Hz")
                print(f"     총 용량: {stat.total_bytes/(1024*1024):.1f}MB")
                print(f"     고유 해시: {stat.unique_hashes:,}")
            
            # 사용 빈도 분석 (최근 30일)
            usage_analysis = session.execute(text("""
                SELECT 
                    s.language,
                    s.id,
                    s.original_filename,
                    s.duration_ms,
                    COUNT(c.id) as usage_count,
                    MAX(c.created_at) as last_used,
                    s.audio_hash
                FROM audio_sources s
                LEFT JOIN captcha_files c ON 
                    (s.language = 'ko' AND c.ko_source_id = s.id) OR
                    (s.language = 'en' AND c.en_source_id = s.id)
                WHERE c.created_at >= now() - interval '30 days' OR c.created_at IS NULL
                GROUP BY s.id, s.language, s.original_filename, s.duration_ms, s.audio_hash
                ORDER BY s.language, usage_count DESC, s.original_filename
            """)).fetchall()
            
            print(f"\n 사용 빈도 분석 (최근 30일):")
            current_lang = None
            for usage in usage_analysis:
                if usage.language != current_lang:
                    current_lang = usage.language
                    print(f"   {current_lang.upper()}:")
                
                last_used = usage.last_used.strftime("%m-%d %H:%M") if usage.last_used else "미사용"
                duration = f"{usage.duration_ms/1000:.1f}s" if usage.duration_ms else "N/A"
                hash_short = usage.audio_hash[:8] if usage.audio_hash else "N/A"
                
                print(f"     {usage.original_filename:<15} | 사용 {usage.usage_count:3d}회 | 최근: {last_used} | {duration} | {hash_short}")
            
            # 중복 해시 검사
            duplicate_hashes = session.execute(text("""
                SELECT audio_hash, COUNT(*) as count, array_agg(original_filename) as filenames
                FROM audio_sources
                GROUP BY audio_hash
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_hashes:
                print(f"\n   중복 해시 발견:")
                for dup in duplicate_hashes:
                    print(f"     해시 {dup.audio_hash[:8]}...: {dup.count}개 파일 - {dup.filenames}")
            else:
                print(f"\n  해시 중복 없음")
                
    except Exception as e:
        print(f" 오디오 소스 디버깅 실패: {e}")

def debug_ko_source_answers():
    """한글 정답 사전 상세 디버깅"""
    print_separator("KO SOURCE ANSWERS DEBUG", "=")
    
    try:
        with get_db_session() as session:
            # 전체 통계
            stats = session.execute(text("""
                SELECT 
                    COUNT(*) as total_answers,
                    COUNT(ko_source_id) as linked_answers,
                    COUNT(DISTINCT answer) as unique_answers,
                    AVG(LENGTH(answer)) as avg_answer_length,
                    MIN(LENGTH(answer)) as min_answer_length,
                    MAX(LENGTH(answer)) as max_answer_length,
                    AVG(LENGTH(question)) as avg_question_length
                FROM ko_source_answers
            """)).fetchone()
            
            print(f" 정답 사전 통계:")
            print(f"   총 정답: {stats.total_answers:,}")
            print(f"   소스 연결: {stats.linked_answers:,} ({stats.linked_answers/stats.total_answers*100:.1f}%)")
            print(f"   고유 정답: {stats.unique_answers:,}")
            print(f"   정답 길이: 평균 {stats.avg_answer_length:.1f}자, 범위 {stats.min_answer_length}~{stats.max_answer_length}자")
            print(f"   질문 길이: 평균 {stats.avg_question_length:.1f}자")
            
            # 정답 길이별 분포
            length_dist = session.execute(text("""
                SELECT 
                    LENGTH(answer) as answer_length,
                    COUNT(*) as count
                FROM ko_source_answers
                GROUP BY LENGTH(answer)
                ORDER BY answer_length
            """)).fetchall()
            
            print(f"\n 정답 길이 분포:")
            for dist in length_dist:
                print(f"   {dist.answer_length}자: {dist.count:,}개")
            
            # 연결되지 않은 정답들
            unlinked = session.execute(text("""
                SELECT ko_key, question, answer
                FROM ko_source_answers
                WHERE ko_source_id IS NULL
                ORDER BY ko_key
                LIMIT 10
            """)).fetchall()
            
            if unlinked:
                print(f"\n 연결되지 않은 정답 (처음 10개):")
                for ul in unlinked:
                    question_short = (ul.question[:40] + '...') if len(ul.question) > 40 else ul.question
                    print(f"   {ul.ko_key}: {question_short} -> {ul.answer}")
            else:
                print(f"\n ✓ 모든 정답이 소스에 연결됨")
            
            # 중복 정답 검사
            duplicate_answers = session.execute(text("""
                SELECT answer, COUNT(*) as count, array_agg(ko_key) as keys
                FROM ko_source_answers
                GROUP BY answer
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 5
            """)).fetchall()
            
            if duplicate_answers:
                print(f"\n 중복 정답 (TOP 5):")
                for dup in duplicate_answers:
                    print(f"   '{dup.answer}': {dup.count}개 키 - {dup.keys[:3]}{'...' if len(dup.keys) > 3 else ''}")
            else:
                print(f"\n ✓ 정답 중복 없음")
                
    except Exception as e:
        print(f" 정답 사전 디버깅 실패: {e}")

def debug_redis_state():
    """Redis 상태 디버깅"""
    print_separator("REDIS DEBUG", "=")
    
    try:
        from db.redis_client import redis_client
        
        # Redis 연결 테스트
        if redis_client.ping():
            print(f" ✓ Redis 연결 성공")
        else:
            print(f" ✗ Redis 연결 실패")
            return
        
        # 모든 키 조회
        all_keys = redis_client.keys('*')
        print(f" 총 키 개수: {len(all_keys)}")
        
        # 키 패턴별 분류
        key_patterns = {
            'captcha:': [],
            'rl:': [],
            'unlock:': [],
            'other': []
        }
        
        for key in all_keys:
            categorized = False
            for pattern in ['captcha:', 'rl:', 'unlock:']:
                if key.startswith(pattern):
                    key_patterns[pattern].append(key)
                    categorized = True
                    break
            if not categorized:
                key_patterns['other'].append(key)
        
        print(f"\n 키 패턴별 분포:")
        for pattern, keys in key_patterns.items():
            if keys:
                print(f"   {pattern:<10} {len(keys):,}개")
                
                # 각 패턴의 샘플 키들 보기
                if pattern == 'captcha:':
                    print(f"     CAPTCHA 키들 (TTL 포함):")
                    for key in keys[:5]:  # 처음 5개만
                        ttl = redis_client.ttl(key)
                        value = redis_client.get(key)
                        print(f"       {key} = '{value}' (TTL: {ttl}초)")
                        
                elif pattern == 'rl:':
                    print(f"     Rate Limit 키들:")
                    for key in keys[:5]:
                        value = redis_client.get(key)
                        ttl = redis_client.ttl(key)
                        print(f"       {key} = {value} (TTL: {ttl}초)")
                        
                elif pattern == 'unlock:':
                    print(f"     Unlock 키들:")
                    for key in keys[:5]:
                        value = redis_client.get(key)
                        ttl = redis_client.ttl(key)
                        print(f"       {key} = {value} (TTL: {ttl}초)")
        
        # Redis 메모리 사용량
        info = redis_client.info('memory')
        used_memory = info.get('used_memory', 0)
        used_memory_human = info.get('used_memory_human', 'N/A')
        
        print(f"\n 메모리 사용량: {used_memory_human} ({used_memory:,} bytes)")
        
    except Exception as e:
        print(f" Redis 디버깅 실패: {e}")

def debug_recent_activity():
    """최근 활동 디버깅"""
    print_separator("RECENT ACTIVITY DEBUG", "=")
    
    try:
        with get_db_session() as session:
            # 최근 24시간 CAPTCHA 생성 활동
            recent_captcha = session.execute(text("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as count,
                    COUNT(*) FILTER (WHERE pipeline_version IS NOT NULL) as synthesized_count
                FROM captcha_files
                WHERE created_at >= now() - interval '24 hours'
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour DESC
            """)).fetchall()
            
            print(f" 최근 24시간 CAPTCHA 생성 (시간별):")
            if recent_captcha:
                for activity in recent_captcha:
                    hour_str = activity.hour.strftime("%m-%d %H:00")
                    synth_pct = (activity.synthesized_count / activity.count * 100) if activity.count > 0 else 0
                    print(f"   {hour_str}: {activity.count:3d}개 (합성: {activity.synthesized_count:3d}, {synth_pct:.0f}%)")
            else:
                print(f"   (최근 24시간 활동 없음)")
            
            # 오늘 사용된 CAPTCHA 수
            today_used = session.execute(text("""
                SELECT COUNT(*) 
                FROM captcha_files
                WHERE used = true AND created_at >= CURRENT_DATE
            """)).scalar()
            
            print(f"\n 오늘 사용된 CAPTCHA: {today_used:,}개")
            
            # 가장 자주 사용되는 정답들 (최근 7일)
            popular_answers = session.execute(text("""
                SELECT answer, COUNT(*) as usage_count
                FROM captcha_files
                WHERE used = true AND created_at >= now() - interval '7 days'
                GROUP BY answer
                ORDER BY usage_count DESC
                LIMIT 10
            """)).fetchall()
            
            print(f"\n 인기 정답 TOP 10 (최근 7일):")
            for i, answer in enumerate(popular_answers, 1):
                print(f"   {i:2d}. '{answer.answer}': {answer.usage_count}회")
                
    except Exception as e:
        print(f" 최근 활동 디버깅 실패: {e}")

def debug_data_integrity():
    """데이터 무결성 검사"""
    print_separator("DATA INTEGRITY CHECK", "=")
    
    try:
        with get_db_session() as session:
            issues = []
            
            # 1. 고아 참조 검사
            orphan_ko = session.execute(text("""
                SELECT COUNT(*)
                FROM captcha_files c
                WHERE c.ko_source_id IS NOT NULL 
                  AND NOT EXISTS (SELECT 1 FROM audio_sources a WHERE a.id = c.ko_source_id)
            """)).scalar()
            
            orphan_en = session.execute(text("""
                SELECT COUNT(*)
                FROM captcha_files c
                WHERE c.en_source_id IS NOT NULL 
                  AND NOT EXISTS (SELECT 1 FROM audio_sources a WHERE a.id = c.en_source_id)
            """)).scalar()
            
            if orphan_ko > 0:
                issues.append(f"고아 한글 참조: {orphan_ko}개")
            if orphan_en > 0:
                issues.append(f"고아 영어 참조: {orphan_en}개")
            
            # 2. 중복 해시 검사
            dup_captcha_hash = session.execute(text("""
                SELECT COUNT(*)
                FROM (
                    SELECT audio_hash
                    FROM captcha_files
                    WHERE audio_hash IS NOT NULL
                    GROUP BY audio_hash
                    HAVING COUNT(*) > 1
                ) t
            """)).scalar()
            
            if dup_captcha_hash > 0:
                issues.append(f"중복 CAPTCHA 해시: {dup_captcha_hash}개")
            
            # 3. 빈 데이터 검사
            empty_audio = session.execute(text("""
                SELECT COUNT(*)
                FROM captcha_files
                WHERE audio_data IS NULL OR LENGTH(audio_data) = 0
            """)).scalar()
            
            if empty_audio > 0:
                issues.append(f"빈 오디오 데이터: {empty_audio}개")
            
            # 4. 일관성 검사
            inconsistent_used = session.execute(text("""
                SELECT COUNT(*)
                FROM captcha_files
                WHERE used = true AND expires_at IS NOT NULL AND expires_at > now()
            """)).scalar()
            
            if inconsistent_used > 0:
                issues.append(f"사용됐지만 미만료: {inconsistent_used}개")
            
            # 결과 출력
            if issues:
                print(f"   발견된 문제들:")
                for issue in issues:
                    print(f"   - {issue}")
            else:
                print(f"  데이터 무결성 검사 통과")
                
            # 추가 통계
            print(f"\n 추가 검사 결과:")
            
            # 만료된 항목 수
            expired_count = session.execute(text("""
                SELECT COUNT(*)
                FROM captcha_files
                WHERE expires_at IS NOT NULL AND expires_at <= now()
            """)).scalar()
            print(f"   만료된 항목: {expired_count:,}개")
            
            # 사용되지 않은 오래된 항목
            old_unused = session.execute(text("""
                SELECT COUNT(*)
                FROM captcha_files
                WHERE used = false AND created_at < now() - interval '7 days'
            """)).scalar()
            print(f"   7일 이상 미사용: {old_unused:,}개")
                
    except Exception as e:
        print(f" 데이터 무결성 검사 실패: {e}")

def main():
    """메인 디버깅 실행"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "schema":
            debug_table_schema()
        elif command == "captcha":
            debug_captcha_files()
        elif command == "audio":
            debug_audio_sources()
        elif command == "answers":
            debug_ko_source_answers()
        elif command == "redis":
            debug_redis_state()
        elif command == "activity":
            debug_recent_activity()
        elif command == "integrity":
            debug_data_integrity()
        else:
            print(f"사용법: python debug_db.py [command]")
            print(f"명령어:")
            print(f"  schema    - 테이블 스키마 정보")
            print(f"  captcha   - CAPTCHA 파일 상세")
            print(f"  audio     - 오디오 소스 상세")
            print(f"  answers   - 정답 사전 상세")
            print(f"  redis     - Redis 상태")
            print(f"  activity  - 최근 활동")
            print(f"  integrity - 데이터 무결성")
            print(f"  (명령어 없음 = 전체 실행)")
            return
    else:
        # 전체 디버깅 실행
        print(f" AuroraPass DB 디버깅 도구")
        print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        debug_captcha_files()
        print()
        debug_audio_sources()
        print()
        debug_ko_source_answers()
        print()
        debug_redis_state()
        print()
        debug_recent_activity()
        print()
        debug_data_integrity()
        
        print_separator("디버깅 완료", "=")

if __name__ == "__main__":
    main()
