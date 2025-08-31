#!/usr/bin/env python3
"""
CAPTCHA 오디오 파일들을 DB에 로드하는 스크립트
"""
import os
import json
from pathlib import Path
from db.session import get_db_session
from sqlalchemy import text

def load_captcha_files():
    """CAPTCHA 파일들을 DB에 로드"""
    script_dir = Path(__file__).parent
    audio_dir = script_dir.parent / "static" / "audio"
    answers_file = audio_dir / "captcha_answers.json"
    
    # 정답 파일 읽기
    with open(answers_file, 'r', encoding='utf-8') as f:
        answers = json.load(f)
    
    with get_db_session() as session:
        # 기존 데이터 삭제
        session.execute(text("DELETE FROM captcha_files"))
        
        for filename, answer in answers.items():
            file_path = audio_dir / filename
            if not file_path.exists():
                print(f"파일 없음: {file_path}")
                continue
            
            # 파일 읽기
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # DB 삽입
            session.execute(text("""
                INSERT INTO captcha_files (id, filename, answer, audio_data, content_type)
                VALUES (:id, :filename, :answer, :audio_data, :content_type)
            """), {
                'id': filename.replace('.wav', ''),
                'filename': filename,
                'answer': answer,
                'audio_data': audio_data,
                'content_type': 'audio/wav'
            })
            
            print(f"로드 완료: {filename} -> {answer}")
        
        print(f"총 {len(answers)}개 CAPTCHA 파일 DB 로드 완료")

if __name__ == "__main__":
    load_captcha_files()
