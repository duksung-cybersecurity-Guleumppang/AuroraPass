#!/usr/bin/env python3
"""
정답 사전을 JSON에서 DB로 로드하는 스크립트
입력: static/real_answer.json
출력: ko_source_answers 테이블에 UPSERT
"""
import json
from pathlib import Path
from db.session import get_db_session
from sqlalchemy import text

def load_answers_to_db():
    """정답 사전 JSON 파일을 DB에 로드합니다."""
    script_dir = Path(__file__).parent
    answers_file = script_dir.parent / "static" / "real_answer.json"
    
    if not answers_file.exists():
        print(f" 정답 파일을 찾을 수 없습니다: {answers_file}")
        return False
    
    try:
        # JSON 파일 읽기
        with open(answers_file, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)
        
        if not isinstance(answers_data, list):
            print(" JSON 파일 형식이 올바르지 않습니다. 배열 형태여야 합니다.")
            return False
        
        print(f" {len(answers_data)}개의 정답 항목을 로드합니다...")
        
        with get_db_session() as session:
            success_count = 0
            
            for i, item in enumerate(answers_data, 1):
                try:
                    # 필수 필드 검증
                    filename = item.get('filename')
                    question = item.get('question')
                    answer = item.get('answer')
                    
                    if not all([filename, question, answer]):
                        print(f"  항목 {i}: 필수 필드가 누락되었습니다 - {item}")
                        continue
                    
                    # ko_key 생성 (확장자 제거)
                    ko_key = Path(filename).stem
                    
                    # UPSERT 실행
                    session.execute(text("""
                        INSERT INTO ko_source_answers (ko_key, question, answer)
                        VALUES (:ko_key, :question, :answer)
                        ON CONFLICT (ko_key) 
                        DO UPDATE SET 
                            question = EXCLUDED.question,
                            answer = EXCLUDED.answer
                    """), {
                        'ko_key': ko_key,
                        'question': question,
                        'answer': answer
                    })
                    
                    print(f" {i:3d}/{len(answers_data)}: {ko_key} -> {answer}")
                    success_count += 1
                    
                except Exception as e:
                    print(f" 항목 {i} 처리 실패: {e}")
            
            session.commit()
            print(f"\n 정답 사전 로드 완료! ({success_count}/{len(answers_data)})")
            return success_count > 0
            
    except Exception as e:
        print(f" 정답 사전 로드 실패: {e}")
        return False

def verify_loaded_answers():
    """로드된 정답 사전을 검증합니다."""
    try:
        with get_db_session() as session:
            result = session.execute(text("""
                SELECT COUNT(*) as total_count,
                       COUNT(DISTINCT ko_key) as unique_keys,
                       MIN(LENGTH(answer)) as min_answer_len,
                       MAX(LENGTH(answer)) as max_answer_len
                FROM ko_source_answers
            """)).fetchone()
            
            if result and result.total_count > 0:
                print(f"\n 정답 사전 통계:")
                print(f"   - 총 항목 수: {result.total_count}")
                print(f"   - 고유 키 수: {result.unique_keys}")
                print(f"   - 정답 길이: {result.min_answer_len}~{result.max_answer_len}자")
                
                # 샘플 데이터 출력
                samples = session.execute(text("""
                    SELECT ko_key, question, answer 
                    FROM ko_source_answers 
                    ORDER BY ko_key 
                    LIMIT 3
                """)).fetchall()
                
                print(f"\n 샘플 데이터:")
                for sample in samples:
                    print(f"   - {sample.ko_key}: {sample.question} -> {sample.answer}")
                
                return True
            else:
                print(" 로드된 정답 사전이 없습니다.")
                return False
                
    except Exception as e:
        print(f" 정답 사전 검증 실패: {e}")
        return False

if __name__ == "__main__":
    print(" 정답 사전 로드를 시작합니다...")
    
    if load_answers_to_db():
        verify_loaded_answers()
    else:
        print(" 정답 사전 로드에 실패했습니다.")
        exit(1)
