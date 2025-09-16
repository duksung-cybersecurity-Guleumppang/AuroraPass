#!/usr/bin/env python3
"""
오디오 파일들을 DB에 로드하는 스크립트
입력: static/tts_men_ko/, static/foreign_women_eng/
출력: audio_sources 테이블에 bytea로 저장
"""
import hashlib
from pathlib import Path
from db.session import get_db_session
from sqlalchemy import text

try:
    import librosa
    import numpy as np
except ImportError as e:
    print(f" 필수 라이브러리가 설치되지 않았습니다: {e}")
    print("다음 명령으로 설치하세요: uv add librosa numpy soundfile")
    exit(1)

def calculate_audio_hash(audio_data: bytes) -> str:
    """오디오 데이터의 SHA256 해시를 계산합니다."""
    return hashlib.sha256(audio_data).hexdigest()

def analyze_audio_file(audio_data: bytes, sample_rate: int = 16000) -> dict:
    """오디오 파일을 분석하여 메타데이터를 추출합니다."""
    try:
        # BytesIO를 사용해 메모리에서 오디오 로드
        import io
        audio_buffer = io.BytesIO(audio_data)
        
        # librosa로 오디오 로드
        y, sr = librosa.load(audio_buffer, sr=sample_rate)
        
        duration_ms = int(len(y) / sr * 1000)
        n_samples = len(y)
        
        return {
            'sample_rate': sr,
            'duration_ms': duration_ms,
            'n_samples': n_samples
        }
    except Exception as e:
        print(f" 오디오 분석 실패: {e}")
        return {
            'sample_rate': sample_rate,
            'duration_ms': None,
            'n_samples': None
        }

def load_audio_files_from_directory(directory_path: Path, language: str):
    """지정된 디렉터리의 오디오 파일들을 DB에 로드합니다."""
    if not directory_path.exists():
        print(f" 디렉터리를 찾을 수 없습니다: {directory_path}")
        return 0
    
    # WAV 파일들 찾기
    audio_files = list(directory_path.glob("*.wav"))
    if not audio_files:
        print(f"  {directory_path}에서 WAV 파일을 찾을 수 없습니다.")
        return 0
    
    print(f" {language} 오디오 파일 {len(audio_files)}개를 로드합니다...")
    
    success_count = 0
    with get_db_session() as session:
        for i, audio_file in enumerate(audio_files, 1):
            try:
                # 파일을 바이너리로 읽기
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()
                
                # 해시 계산
                audio_hash = calculate_audio_hash(audio_data)
                
                # 오디오 분석
                metadata = analyze_audio_file(audio_data)
                
                # DB에 UPSERT
                session.execute(text("""
                    INSERT INTO audio_sources (
                        language, original_filename, content_type, audio_data,
                        sample_rate, duration_ms, n_samples, audio_hash
                    ) VALUES (
                        :language, :original_filename, :content_type, :audio_data,
                        :sample_rate, :duration_ms, :n_samples, :audio_hash
                    )
                    ON CONFLICT (audio_hash) 
                    DO UPDATE SET 
                        language = EXCLUDED.language,
                        original_filename = EXCLUDED.original_filename,
                        content_type = EXCLUDED.content_type,
                        sample_rate = EXCLUDED.sample_rate,
                        duration_ms = EXCLUDED.duration_ms,
                        n_samples = EXCLUDED.n_samples
                """), {
                    'language': language,
                    'original_filename': audio_file.name,
                    'content_type': 'audio/wav',
                    'audio_data': audio_data,
                    'sample_rate': metadata['sample_rate'],
                    'duration_ms': metadata['duration_ms'],
                    'n_samples': metadata['n_samples'],
                    'audio_hash': audio_hash
                })
                
                print(f" {i:3d}/{len(audio_files)}: {audio_file.name} ({len(audio_data):,} bytes)")
                success_count += 1
                
            except Exception as e:
                print(f" {audio_file.name} 처리 실패: {e}")
        
        session.commit()
    
    return success_count

def load_all_audio_sources():
    """모든 오디오 소스를 DB에 로드합니다."""
    script_dir = Path(__file__).parent
    static_dir = script_dir.parent / "static"
    
    # 로드할 디렉터리와 언어 매핑
    audio_directories = [
        (static_dir / "tts_men_ko", "ko"),
        (static_dir / "foreign_women_eng", "en")
    ]
    
    total_success = 0
    
    for directory, language in audio_directories:
        print(f"\n {language.upper()} 오디오 로드 시작: {directory}")
        success_count = load_audio_files_from_directory(directory, language)
        total_success += success_count
        print(f" {language.upper()} 오디오 로드 완료: {success_count}개")
    
    return total_success

def verify_loaded_audio():
    """로드된 오디오 소스를 검증합니다."""
    try:
        with get_db_session() as session:
            # 전체 통계
            result = session.execute(text("""
                SELECT 
                    language,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_duration_ms,
                    SUM(LENGTH(audio_data)) as total_bytes
                FROM audio_sources 
                GROUP BY language
                ORDER BY language
            """)).fetchall()
            
            if result:
                print(f"\n 오디오 소스 통계:")
                total_files = 0
                total_bytes = 0
                
                for row in result:
                    total_files += row.count
                    total_bytes += row.total_bytes or 0
                    avg_duration = f"{row.avg_duration_ms/1000:.1f}s" if row.avg_duration_ms else "N/A"
                    size_mb = (row.total_bytes or 0) / (1024*1024)
                    
                    print(f"   - {row.language.upper()}: {row.count}개 파일, 평균 {avg_duration}, {size_mb:.1f}MB")
                
                print(f"   - 총합: {total_files}개 파일, {total_bytes/(1024*1024):.1f}MB")
                
                # 샘플 데이터
                samples = session.execute(text("""
                    SELECT language, original_filename, duration_ms, LENGTH(audio_data) as size_bytes
                    FROM audio_sources 
                    ORDER BY language, original_filename 
                    LIMIT 5
                """)).fetchall()
                
                print(f"\n 샘플 데이터:")
                for sample in samples:
                    duration = f"{sample.duration_ms/1000:.1f}s" if sample.duration_ms else "N/A"
                    size_kb = sample.size_bytes / 1024
                    print(f"   - {sample.language}: {sample.original_filename} ({duration}, {size_kb:.1f}KB)")
                
                return True
            else:
                print(" 로드된 오디오 소스가 없습니다.")
                return False
                
    except Exception as e:
        print(f" 오디오 소스 검증 실패: {e}")
        return False

if __name__ == "__main__":
    print(" 오디오 소스 로드를 시작합니다...")
    
    total_loaded = load_all_audio_sources()
    
    if total_loaded > 0:
        print(f"\n 총 {total_loaded}개의 오디오 파일이 로드되었습니다!")
        verify_loaded_audio()
    else:
        print(" 오디오 파일 로드에 실패했습니다.")
        exit(1)
