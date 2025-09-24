#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 실행 스크립트
"""
import os
import sys
from pathlib import Path
from db.session import get_db_session
from sqlalchemy import text


def run_migration(sql_file_path: str):
    """지정된 SQL 파일을 실행합니다."""
    if not Path(sql_file_path).exists():
        print(f" 마이그레이션 파일을 찾을 수 없습니다: {sql_file_path}")
        return False
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with get_db_session() as session:
            # SQL 파일을 세미콜론으로 분리하여 실행
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                print(f" 실행 중 ({i}/{len(statements)}): {statement[:50]}...")
                session.execute(text(statement))
            
            session.commit()
            print(f" 마이그레이션 완료: {sql_file_path}")
            return True
            
    except Exception as e:
        print(f" 마이그레이션 실패: {e}")
        return False


def run_all_migrations():
    """모든 마이그레이션을 순서대로 실행합니다."""
    script_dir = Path(__file__).parent
    init_dir = script_dir.parent / "db" / "init"
    
    # 마이그레이션 파일들을 순서대로 정렬 (모든 *.sql 대상)
    migration_files = sorted(init_dir.glob("*.sql"), key=lambda f: f.name)
    
    if not migration_files:
        print(" 마이그레이션 파일을 찾을 수 없습니다.")
        return False
    
    print(f" {len(migration_files)}개의 마이그레이션을 실행합니다...")
    
    success_count = 0
    for migration_file in migration_files:
        print(f"\n 실행 중: {migration_file.name}")
        if run_migration(str(migration_file)):
            success_count += 1
        else:
            print(f" 마이그레이션 실패로 중단: {migration_file.name}")
            break
    
    if success_count == len(migration_files):
        print(f"\n 모든 마이그레이션이 성공적으로 완료되었습니다! ({success_count}/{len(migration_files)})")
        return True
    else:
        print(f"\n 마이그레이션이 부분적으로 실패했습니다. ({success_count}/{len(migration_files)})")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 특정 마이그레이션 파일 실행
        migration_file = sys.argv[1]
        run_migration(migration_file)
    else:
        # 모든 마이그레이션 실행
        run_all_migrations()
