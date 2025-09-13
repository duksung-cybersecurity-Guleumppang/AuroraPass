#!/usr/bin/env python3
"""
부팅 초기화 단일 진입점 (멱등)
컨테이너 부팅 시 마이그레이션 → 초기 시드 → 정답/오디오 UPSERT → API 기동
"""
import os
import sys
import json
import hashlib
import threading
import time
from pathlib import Path
from db.session import get_db_session
from sqlalchemy import text

# 스크립트들 임포트를 위한 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

def run_migrations():
    """전체 DB 마이그레이션 실행"""
    print(" DB 마이그레이션 실행 중...")
    
    try:
        from run_migration import run_all_migrations
        success = run_all_migrations()
        if success:
            print(" 마이그레이션 완료")
            return True
        else:
            print(" 마이그레이션 실패")
            return False
    except Exception as e:
        print(f" 마이그레이션 오류: {e}")
        return False

def seed_initial_captcha():
    """초기 시드: static/audio 10개 WAV + answers JSON 전량 적재"""
    print(" 초기 CAPTCHA 시드 확인 중...")
    
    try:
        audio_dir = Path(__file__).parent.parent / "static" / "audio"
        answers_file = audio_dir / "captcha_answers.json"
        
        if not answers_file.exists():
            print(f"  정답 파일 없음: {answers_file}")
            return True  # 선택사항이므로 성공으로 처리
        
        with open(answers_file, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        
        with get_db_session() as session:
            # 기존 데이터 확인
            count = session.execute(text("SELECT COUNT(*) FROM captcha_files")).scalar()
            if count > 0:
                print(f" 기존 CAPTCHA 데이터 존재 ({count}개), 시드 스킵")
                return True
            
            # 시드 데이터 적재
            loaded = 0
            for filename, answer in answers.items():
                file_path = audio_dir / filename
                if not file_path.exists():
                    print(f"  파일 없음: {file_path}")
                    continue
                
                audio_data = file_path.read_bytes()
                audio_hash = hashlib.sha256(audio_data).hexdigest()
                
                session.execute(text("""
                    INSERT INTO captcha_files (id, filename, answer, audio_data, content_type, audio_hash, used)
                    VALUES (:id, :filename, :answer, :audio_data, :content_type, :audio_hash, false)
                    ON CONFLICT (filename) DO NOTHING
                """), {
                    'id': filename.replace('.wav', ''),
                    'filename': filename,
                    'answer': answer,
                    'audio_data': audio_data,
                    'content_type': 'audio/wav',
                    'audio_hash': audio_hash
                })
                loaded += 1
            
            session.commit()
            print(f" 초기 CAPTCHA 시드 완료: {loaded}개")
            return True
            
    except Exception as e:
        print(f" 초기 시드 실패: {e}")
        return False

def upsert_answers():
    """정답 사전 UPSERT: backend/static/real_answer.json → ko_source_answers"""
    print(" 정답 사전 UPSERT 중...")
    
    try:
        from load_answers_to_db import load_answers_to_db
        success = load_answers_to_db()
        if success:
            print(" 정답 사전 UPSERT 완료")
            return True
        else:
            print(" 정답 사전 UPSERT 실패")
            return False
    except Exception as e:
        print(f" 정답 사전 UPSERT 오류: {e}")
        return False

def upsert_audio_sources():
    """원본 오디오 UPSERT: tts_men_ko/, foreign_women_eng/ → audio_sources"""
    print(" 원본 오디오 UPSERT 중...")
    
    try:
        from load_audio_to_db import load_all_audio_sources
        total_loaded = load_all_audio_sources()
        if total_loaded >= 0:  # 0개도 성공으로 처리 (파일 없을 수 있음)
            print(f" 원본 오디오 UPSERT 완료: {total_loaded}개")
            return True
        else:
            print(" 원본 오디오 UPSERT 실패")
            return False
    except Exception as e:
        print(f" 원본 오디오 UPSERT 오류: {e}")
        return False

def prefetch_synthesis():
    """백그라운드 사전 합성 3개 (실패해도 부팅에 영향 없음)"""
    print(" 백그라운드 사전 합성 시작...")
    
    def background_synthesis():
        try:
            # PoC 모듈 임포트
            # __file__ = /app/backend/scripts/bootstrap.py
            # repo root = parents[2] → /app
            poc_path = Path(__file__).parents[2] / "poc" / "captcha_synth"
            sys.path.insert(0, str(poc_path))
            
            from synthesize_captcha import synthesize_multiple_captchas
            success_count = synthesize_multiple_captchas(3)
            print(f" 백그라운드 사전 합성 완료: {success_count}/3개")
        except Exception as e:
            print(f"  백그라운드 사전 합성 실패 (무시됨): {e}")
    
    # 백그라운드 스레드로 실행
    thread = threading.Thread(target=background_synthesis, daemon=True)
    thread.start()

def start_topup_scheduler():
    """Top-up 스케줄러 시작 (백그라운드)"""
    print(" Top-up 스케줄러 시작...")
    
    try:
        from services.topup_scheduler import start_topup_scheduler as start_scheduler
        start_scheduler()
        print(" Top-up 스케줄러 시작됨")
    except Exception as e:
        print(f"  Top-up 스케줄러 시작 실패 (무시됨): {e}")

def bootstrap_sequence():
    """부팅 초기화 시퀀스 실행"""
    print(" 부팅 초기화 시퀀스 시작...")
    
    steps = [
        ("DB 마이그레이션", run_migrations),
        ("초기 시드", seed_initial_captcha),
        ("정답 사전 UPSERT", upsert_answers),
        ("원본 오디오 UPSERT", upsert_audio_sources),
    ]
    
    for step_name, step_func in steps:
        print(f"\n {step_name} 실행 중...")
        if not step_func():
            print(f" {step_name} 실패로 부팅 중단")
            sys.exit(1)
    
    print("\n 모든 초기화 단계 완료!")
    
    # 백그라운드 사전 합성 시작 (실패해도 부팅 계속)
    prefetch_synthesis()
    
    # Top-up 스케줄러 시작 (실패해도 부팅 계속)
    start_topup_scheduler()
    
    print(" 부팅 초기화 완료, API 서버 기동 준비")
    return True

if __name__ == "__main__":
    bootstrap_sequence()
