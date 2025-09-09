#!/usr/bin/env python3
"""
CAPTCHA 오디오 합성 스크립트
DB에서 한글/영어 오디오를 랜덤 선택하여 합성하고 captcha_files에 저장
"""
import sys
import uuid
from pathlib import Path
from db.session import get_db_session
from sqlalchemy import text

# PoC 모듈 임포트를 위한 경로 추가
poc_path = Path(__file__).parent.parent.parent / "poc" / "captcha_synth"
sys.path.insert(0, str(poc_path))

try:
    from captcha_synth import synthesize_captcha_audio, params_snapshot, PIPELINE_VERSION
except ImportError as e:
    print(f"PoC 모듈을 임포트할 수 없습니다: {e}")
    print(f"경로를 확인하세요: {poc_path}")
    exit(1)

def get_random_audio_source(language: str) -> tuple:
    """지정된 언어의 랜덤 오디오 소스를 가져옵니다."""
    with get_db_session() as session:
        result = session.execute(text("""
            SELECT id, original_filename, audio_data
            FROM audio_sources 
            WHERE language = :language
            ORDER BY RANDOM() 
            LIMIT 1
        """), {"language": language}).fetchone()
        
        if result:
            return result.id, result.original_filename, result.audio_data
        return None, None, None

def get_answer_for_ko_source(ko_filename: str) -> tuple:
    """한글 소스 파일명으로 정답을 조회합니다."""
    ko_key = Path(ko_filename).stem
    
    with get_db_session() as session:
        result = session.execute(text("""
            SELECT question, answer
            FROM ko_source_answers 
            WHERE ko_key = :ko_key
        """), {"ko_key": ko_key}).fetchone()
        
        if result:
            return result.question, result.answer
        return None, None

def save_synthesized_captcha(
    audio_data: bytes, 
    answer: str, 
    metadata: dict, 
    ko_source_id: int, 
    en_source_id: int
) -> str:
    """합성된 CAPTCHA를 DB에 저장합니다."""
    captcha_id = str(uuid.uuid4())
    filename = f"synthesized_{captcha_id[:8]}.wav"
    
    with get_db_session() as session:
        session.execute(text("""
            INSERT INTO captcha_files (
                id, filename, answer, audio_data, content_type,
                sample_rate, duration_ms, n_samples, params, 
                pipeline_version, audio_hash, ko_source_id, en_source_id
            ) VALUES (
                :id, :filename, :answer, :audio_data, :content_type,
                :sample_rate, :duration_ms, :n_samples, :params,
                :pipeline_version, :audio_hash, :ko_source_id, :en_source_id
            )
        """), {
            'id': captcha_id,
            'filename': filename,
            'answer': answer,
            'audio_data': audio_data,
            'content_type': 'audio/wav',
            'sample_rate': metadata['sample_rate'],
            'duration_ms': metadata['duration_ms'],
            'n_samples': metadata['n_samples'],
            'params': metadata['params'],
            'pipeline_version': metadata['pipeline_version'],
            'audio_hash': metadata['audio_hash'],
            'ko_source_id': ko_source_id,
            'en_source_id': en_source_id
        })
        
        session.commit()
    
    return captcha_id

def synthesize_single_captcha() -> bool:
    """단일 CAPTCHA를 합성하여 DB에 저장합니다."""
    print(" CAPTCHA 합성을 시작합니다...")
    
    # 1. 한글 오디오 랜덤 선택
    print(" 한글 오디오 소스 선택 중...")
    ko_id, ko_filename, ko_audio_data = get_random_audio_source("ko")
    if not ko_id:
        print(" 한글 오디오 소스를 찾을 수 없습니다.")
        return False
    
    print(f" 한글 소스: {ko_filename} (ID: {ko_id})")
    
    # 2. 정답 조회
    print("정답 조회 중...")
    question, answer = get_answer_for_ko_source(ko_filename)
    if not answer:
        print(f" {ko_filename}에 대한 정답을 찾을 수 없습니다.")
        return False
    
    print(f"정답: {answer}")
    if question:
        print(f"   질문: {question}")
    
    # 3. 영어 오디오 랜덤 선택
    print(" 영어 오디오 소스 선택 중...")
    en_id, en_filename, en_audio_data = get_random_audio_source("en")
    if not en_id:
        print(" 영어 오디오 소스를 찾을 수 없습니다.")
        return False
    
    print(f" 영어 소스: {en_filename} (ID: {en_id})")
    
    # 4. 오디오 합성
    print(" 오디오 합성 중...")
    try:
        synthesized_audio, metadata = synthesize_captcha_audio(ko_audio_data, en_audio_data)
        print(f" 합성 완료:")
        print(f"   - 크기: {len(synthesized_audio):,} bytes")
        print(f"   - 지속시간: {metadata['duration_ms']}ms")
        print(f"   - 샘플 수: {metadata['n_samples']:,}")
        print(f"   - 해시: {metadata['audio_hash'][:16]}...")
    except Exception as e:
        print(f" 오디오 합성 실패: {e}")
        return False
    
    # 5. DB에 저장
    print(" DB에 저장 중...")
    try:
        captcha_id = save_synthesized_captcha(
            synthesized_audio, answer, metadata, ko_id, en_id
        )
        print(f" 저장 완료: CAPTCHA ID = {captcha_id}")
        return True
    except Exception as e:
        print(f" DB 저장 실패: {e}")
        return False

def synthesize_multiple_captchas(count: int) -> int:
    """여러 개의 CAPTCHA를 합성합니다."""
    print(f" {count}개의 CAPTCHA 합성을 시작합니다...\n")
    
    success_count = 0
    
    for i in range(1, count + 1):
        print(f" {i}/{count} 번째 CAPTCHA 합성:")
        
        if synthesize_single_captcha():
            success_count += 1
            print(f" {i}번째 합성 성공!\n")
        else:
            print(f" {i}번째 합성 실패!\n")
    
    print(f" 합성 완료: {success_count}/{count}개 성공")
    return success_count

def verify_synthesized_captchas():
    """합성된 CAPTCHA들을 검증합니다."""
    try:
        with get_db_session() as session:
            # 통계 조회
            result = session.execute(text("""
                SELECT 
                    COUNT(*) as total_count,
                    AVG(duration_ms) as avg_duration_ms,
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest,
                    COUNT(DISTINCT ko_source_id) as unique_ko_sources,
                    COUNT(DISTINCT en_source_id) as unique_en_sources
                FROM captcha_files 
                WHERE pipeline_version = :version
            """), {"version": PIPELINE_VERSION}).fetchone()
            
            if result and result.total_count > 0:
                print(f"\n  합성된 CAPTCHA 통계 (파이프라인 {PIPELINE_VERSION}):")
                print(f"   - 총 개수: {result.total_count}")
                print(f"   - 평균 지속시간: {result.avg_duration_ms/1000:.1f}초")
                print(f"   - 고유 한글 소스: {result.unique_ko_sources}")
                print(f"   - 고유 영어 소스: {result.unique_en_sources}")
                print(f"   - 생성 기간: {result.oldest} ~ {result.newest}")
                
                # 최근 샘플
                samples = session.execute(text("""
                    SELECT id, filename, answer, duration_ms, created_at
                    FROM captcha_files 
                    WHERE pipeline_version = :version
                    ORDER BY created_at DESC 
                    LIMIT 3
                """), {"version": PIPELINE_VERSION}).fetchall()
                
                print(f"\n 최근 생성된 CAPTCHA:")
                for sample in samples:
                    duration = f"{sample.duration_ms/1000:.1f}s"
                    print(f"   - {sample.id[:8]}...: {sample.answer} ({duration})")
                
                return True
            else:
                print(" 합성된 CAPTCHA가 없습니다.")
                return False
                
    except Exception as e:
        print(f" CAPTCHA 검증 실패: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CAPTCHA 오디오 합성 스크립트")
    parser.add_argument("--count", "-c", type=int, default=1, help="생성할 CAPTCHA 개수 (기본: 1)")
    parser.add_argument("--verify", "-v", action="store_true", help="합성된 CAPTCHA 검증")
    
    args = parser.parse_args()
    
    if args.verify:
        verify_synthesized_captchas()
    else:
        if args.count == 1:
            success = synthesize_single_captcha()
            if success:
                verify_synthesized_captchas()
            else:
                exit(1)
        else:
            success_count = synthesize_multiple_captchas(args.count)
            if success_count > 0:
                verify_synthesized_captchas()
            if success_count < args.count:
                exit(1)
