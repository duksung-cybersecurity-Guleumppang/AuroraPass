#!/usr/bin/env python3
"""
SQL 직접 실행 스크립트
디버깅을 위해 SQL 쿼리를 직접 실행하고 결과를 확인할 수 있는 도구
"""
import sys
import json
from datetime import datetime
from db.session import get_db_session
from sqlalchemy import text

def execute_sql(query, params=None):
    """SQL 쿼리 실행"""
    try:
        with get_db_session() as session:
            if params:
                result = session.execute(text(query), params)
            else:
                result = session.execute(text(query))
            
            # SELECT 쿼리인 경우 결과 반환
            if query.strip().upper().startswith('SELECT'):
                rows = result.fetchall()
                columns = result.keys() if hasattr(result, 'keys') else []
                return {'success': True, 'rows': rows, 'columns': columns, 'rowcount': len(rows)}
            else:
                # INSERT/UPDATE/DELETE 등의 경우
                session.commit()
                return {'success': True, 'rowcount': result.rowcount, 'message': f"{result.rowcount}개 행 영향받음"}
                
    except Exception as e:
        return {'success': False, 'error': str(e)}

def format_result(result):
    """결과 포맷팅"""
    if not result['success']:
        print(f" 오류: {result['error']}")
        return
    
    if 'rows' in result:
        # SELECT 결과
        rows = result['rows']
        columns = result['columns']
        
        if not rows:
            print(" 결과 없음")
            return
        
        print(f" {len(rows)}개 행 조회됨:")
        print()
        
        # 컬럼 헤더
        if columns:
            header = " | ".join(f"{col:<15}" for col in columns)
            print(header)
            print("-" * len(header))
        
        # 데이터 행들
        for i, row in enumerate(rows, 1):
            if hasattr(row, '_asdict'):
                # NamedTuple인 경우
                values = [str(getattr(row, col, ''))[:15] for col in columns]
            else:
                # 일반 튜플인 경우
                values = [str(val)[:15] if val is not None else 'NULL' for val in row]
            
            row_str = " | ".join(f"{val:<15}" for val in values)
            print(f"{row_str}")
            
            # 너무 많은 행은 일부만 표시
            if i >= 50:
                print(f"... (총 {len(rows)}개 행, 처음 50개만 표시)")
                break
    else:
        # INSERT/UPDATE/DELETE 결과
        print(f" {result['message']}")

def interactive_mode():
    """대화형 모드"""
    print(" AuroraPass SQL 실행기 (대화형 모드)")
    print("도움말: help, 종료: exit/quit")
    print("-" * 50)
    
    while True:
        try:
            query = input("\nSQL> ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['exit', 'quit', 'q']:
                print("종료합니다.")
                break
                
            if query.lower() == 'help':
                show_help()
                continue
            
            if query.lower().startswith('preset:'):
                # 미리 정의된 쿼리 실행
                preset_name = query[7:].strip()
                preset_query = get_preset_query(preset_name)
                if preset_query:
                    print(f"실행: {preset_query}")
                    result = execute_sql(preset_query)
                    format_result(result)
                else:
                    print(f"알 수 없는 프리셋: {preset_name}")
                continue
            
            # SQL 실행
            print(f"실행 중...")
            start_time = datetime.now()
            result = execute_sql(query)
            end_time = datetime.now()
            
            format_result(result)
            
            duration = (end_time - start_time).total_seconds()
            print(f"\n실행 시간: {duration:.3f}초")
            
        except KeyboardInterrupt:
            print("\n\n종료합니다.")
            break
        except EOFError:
            print("\n\n종료합니다.")
            break

def show_help():
    """도움말 표시"""
    print("""
  사용법:
  - SQL 쿼리를 직접 입력하세요
  - preset:이름 - 미리 정의된 쿼리 실행
  - help - 이 도움말 표시
  - exit/quit - 종료

  프리셋 쿼리:
  preset:captcha_stats    - CAPTCHA 파일 통계
  preset:audio_stats      - 오디오 소스 통계
  preset:recent_captcha   - 최근 CAPTCHA 10개
  preset:available        - 사용 가능한 CAPTCHA
  preset:used_today       - 오늘 사용된 CAPTCHA
  preset:ko_usage         - 한글 소스 사용 현황
  preset:tables           - 모든 테이블 목록
  preset:indexes          - 인덱스 정보

   주의사항:
  - SELECT 쿼리만 사용하는 것을 권장합니다
  - 데이터 변경 시 신중히 하세요
  - 트랜잭션은 자동 커밋됩니다
""")

def get_preset_query(name):
    """미리 정의된 쿼리 반환"""
    presets = {
        'captcha_stats': """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE used = false) as available,
                COUNT(*) FILTER (WHERE used = true) as used,
                COUNT(*) FILTER (WHERE pipeline_version IS NOT NULL) as synthesized
            FROM captcha_files
        """,
        
        'audio_stats': """
            SELECT 
                language,
                COUNT(*) as count,
                AVG(duration_ms) as avg_duration_ms,
                SUM(LENGTH(audio_data)) as total_bytes
            FROM audio_sources
            GROUP BY language
            ORDER BY language
        """,
        
        'recent_captcha': """
            SELECT id, filename, answer, used, created_at, pipeline_version
            FROM captcha_files
            ORDER BY created_at DESC
            LIMIT 10
        """,
        
        'available': """
            SELECT id, filename, answer, created_at
            FROM captcha_files
            WHERE used = false AND (expires_at IS NULL OR expires_at > now())
            ORDER BY created_at DESC
            LIMIT 20
        """,
        
        'used_today': """
            SELECT id, filename, answer, created_at
            FROM captcha_files
            WHERE used = true AND created_at >= CURRENT_DATE
            ORDER BY created_at DESC
            LIMIT 20
        """,
        
        'ko_usage': """
            SELECT 
                s.original_filename,
                COUNT(c.id) as usage_count,
                MAX(c.created_at) as last_used
            FROM audio_sources s
            LEFT JOIN captcha_files c ON c.ko_source_id = s.id
            WHERE s.language = 'ko'
            GROUP BY s.id, s.original_filename
            ORDER BY usage_count DESC, s.original_filename
            LIMIT 20
        """,
        
        'tables': """
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """,
        
        'indexes': """
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """
    }
    
    return presets.get(name)

def main():
    """메인 실행"""
    if len(sys.argv) > 1:
        # 명령행에서 SQL 직접 실행
        query = ' '.join(sys.argv[1:])
        
        print(f"실행: {query}")
        result = execute_sql(query)
        format_result(result)
    else:
        # 대화형 모드
        interactive_mode()

if __name__ == "__main__":
    main()
