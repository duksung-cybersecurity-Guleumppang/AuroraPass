#!/usr/bin/env python3
"""
CAPTCHA 오디오 합성 PoC
DB에서 한글/영어 오디오를 불러와 합성하는 최소 파이프라인
"""
import io
import hashlib
import math
import numpy as np
import soundfile as sf
import librosa
import random

# ===================== 파라미터 =====================
SR = 16000
GAIN = 2.5
PITCH_SHIFT_STEPS = -1.3
SILENCE_DURATION = 2.0
FOREIGN_GAIN = 1.1
KOREAN_GAIN = 1.0
APPLY_PITCH_SHIFT = True
TRIM_SILENCE = True
TRIM_TOP_DB = 30
# 길이 맞춤 방식: 이전 loop(반복) → pad(무음 패딩)으로 변경해 문장 반복을 방지
FIT_METHOD = "pad"
SEED = None
PIPELINE_VERSION = "v1"

def params_snapshot():
    """현재 파라미터 스냅샷을 반환합니다."""
    return {
        "sr": SR,
        "gain": GAIN,
        "pitch_shift_steps": PITCH_SHIFT_STEPS,
        "silence_duration": SILENCE_DURATION,
        "foreign_gain": FOREIGN_GAIN,
        "korean_gain": KOREAN_GAIN,
        "apply_pitch_shift": APPLY_PITCH_SHIFT,
        "trim_silence": TRIM_SILENCE,
        "trim_top_db": TRIM_TOP_DB,
        "fit_method": FIT_METHOD,
        "seed": SEED,
    }

# ===================== 유틸 함수 =====================
def trim_silence_fn(y, top_db=30):
    """무음 구간을 제거합니다."""
    trimmed, _ = librosa.effects.trim(y, top_db=top_db)
    return trimmed

def fit_to_length(y, target_len, method="loop"):
    """오디오를 목표 길이에 맞춥니다."""
    n = len(y)
    if n == target_len:
        return y
    if n > target_len:
        return y[:target_len]
    if n == 0:
        return np.zeros(target_len, dtype=np.float32)
    if method == "loop":
        rep = int(math.ceil(target_len / n))
        y = np.tile(y, rep)
        return y[:target_len]
    elif method == "pad":
        pad = target_len - n
        return np.concatenate([y, np.zeros(pad, dtype=y.dtype)])
    else:
        return y[:target_len]

def prepend_silence(y, sr, sec=0.0):
    """앞에 무음을 추가합니다."""
    if sec <= 0:
        return y
    return np.concatenate([np.zeros(int(sr * sec), dtype=y.dtype), y])

def safe_mix(a, b, master_gain=1.0):
    """두 오디오를 안전하게 믹스합니다."""
    mixed = a + b
    mixed = mixed * master_gain
    peak = np.max(np.abs(mixed)) if mixed.size else 0.0
    if peak > 1.0:
        mixed = mixed / peak
    return np.clip(mixed, -1.0, 1.0)

def sha256_bytes(b: bytes) -> str:
    """바이트 데이터의 SHA256 해시를 계산합니다."""
    return hashlib.sha256(b).hexdigest()

def load_audio_from_bytes(audio_bytes: bytes, sr: int = SR) -> np.ndarray:
    """바이트 데이터에서 오디오를 로드합니다."""
    audio_buffer = io.BytesIO(audio_bytes)
    y, _ = librosa.load(audio_buffer, sr=sr)
    return y

def save_audio_to_bytes(y: np.ndarray, sr: int = SR) -> bytes:
    """오디오를 WAV 바이트로 저장합니다."""
    buffer = io.BytesIO()
    sf.write(buffer, y, sr, format='WAV')
    return buffer.getvalue()

def synthesize_captcha_audio(ko_audio_bytes: bytes, en_audio_bytes: bytes, stop_checker=None) -> tuple[bytes, dict]:
    """
    한글과 영어 오디오를 합성하여 CAPTCHA 오디오를 생성합니다.
    
    Args:
        ko_audio_bytes: 한글 오디오 바이트 데이터
        en_audio_bytes: 영어 오디오 바이트 데이터
    
    Returns:
        tuple: (합성된 오디오 바이트, 메타데이터 딕셔너리)
    """
    # 인터럽트 체크 헬퍼
    def _should_stop() -> bool:
        try:
            return bool(stop_checker and stop_checker())
        except Exception:
            return False

    # 랜덤화 시드 설정 (요청 시 고정 가능)
    if SEED is not None:
        random.seed(SEED)
        np.random.seed(SEED)

    # 호출별 소폭 랜덤화 파라미터 생성 (해시 충돌 감소 목적)
    pitch_steps_runtime = float(PITCH_SHIFT_STEPS + np.random.uniform(-0.3, 0.3))
    silence_runtime = float(max(0.0, SILENCE_DURATION + np.random.uniform(-0.2, 0.2)))
    gain_runtime = float(GAIN * (1.0 + np.random.uniform(-0.1, 0.1)))
    foreign_gain_runtime = float(FOREIGN_GAIN * (1.0 + np.random.uniform(-0.1, 0.1)))
    korean_gain_runtime = float(KOREAN_GAIN * (1.0 + np.random.uniform(-0.1, 0.1)))

    if _should_stop():
        raise RuntimeError("Synthesis interrupted (pre-load)")

    # 오디오 로드
    ko_audio = load_audio_from_bytes(ko_audio_bytes, SR)
    en_audio = load_audio_from_bytes(en_audio_bytes, SR)
    
    # 1. 무음 제거 (옵션)
    if TRIM_SILENCE:
        if _should_stop():
            raise RuntimeError("Synthesis interrupted (trim)")
        ko_audio = trim_silence_fn(ko_audio, TRIM_TOP_DB)
        en_audio = trim_silence_fn(en_audio, TRIM_TOP_DB)
    
    # 2. 길이 맞추기 - 더 긴 쪽에 맞춤
    if _should_stop():
        raise RuntimeError("Synthesis interrupted (fit)")
    max_len = max(len(ko_audio), len(en_audio))
    ko_audio = fit_to_length(ko_audio, max_len, FIT_METHOD)
    en_audio = fit_to_length(en_audio, max_len, FIT_METHOD)
    
    # 3. 피치 변경 (옵션)
    if APPLY_PITCH_SHIFT:
        if _should_stop():
            raise RuntimeError("Synthesis interrupted (pitch)")
        try:
            en_audio = librosa.effects.pitch_shift(en_audio, sr=SR, n_steps=pitch_steps_runtime)
        except Exception as e:
            print(f"  피치 변경 실패: {e}")
    
    # 4. 게인 적용
    if _should_stop():
        raise RuntimeError("Synthesis interrupted (gain)")
    ko_audio = ko_audio * korean_gain_runtime
    en_audio = en_audio * foreign_gain_runtime
    
    # 5. 믹싱
    if _should_stop():
        raise RuntimeError("Synthesis interrupted (mix)")
    mixed_audio = safe_mix(ko_audio, en_audio, gain_runtime)
    
    # 6. 앞에 무음 추가
    if _should_stop():
        raise RuntimeError("Synthesis interrupted (silence)")
    final_audio = prepend_silence(mixed_audio, SR, silence_runtime)
    
    # 7. 바이트로 변환
    if _should_stop():
        raise RuntimeError("Synthesis interrupted (export)")
    result_bytes = save_audio_to_bytes(final_audio, SR)
    
    # 8. 메타데이터 생성
    # 파라미터 스냅샷 + 런타임 변동치 기록
    params = params_snapshot()
    params.update({
        "runtime_pitch_shift_steps": pitch_steps_runtime,
        "runtime_silence_duration": silence_runtime,
        "runtime_gain": gain_runtime,
        "runtime_foreign_gain": foreign_gain_runtime,
        "runtime_korean_gain": korean_gain_runtime,
    })

    metadata = {
        'sample_rate': SR,
        'duration_ms': int(len(final_audio) / SR * 1000),
        'n_samples': len(final_audio),
        'audio_hash': sha256_bytes(result_bytes),
        'params': params,
        'pipeline_version': PIPELINE_VERSION
    }
    
    return result_bytes, metadata

# 테스트용 함수들
def create_test_audio(frequency: float, duration: float, sr: int = SR) -> bytes:
    """테스트용 사인파 오디오를 생성합니다."""
    t = np.linspace(0, duration, int(sr * duration), False)
    y = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    return save_audio_to_bytes(y, sr)

def test_synthesis():
    """합성 로직을 테스트합니다."""
    print(" CAPTCHA 오디오 합성 테스트 시작...")
    
    # 테스트 오디오 생성 (440Hz, 880Hz 사인파)
    ko_test_bytes = create_test_audio(440, 1.0)  # 1초간 440Hz
    en_test_bytes = create_test_audio(880, 0.8)  # 0.8초간 880Hz
    
    print(f" 테스트 오디오 생성 완료:")
    print(f"   - 한글 테스트: {len(ko_test_bytes):,} bytes")
    print(f"   - 영어 테스트: {len(en_test_bytes):,} bytes")
    
    # 합성 실행
    try:
        result_bytes, metadata = synthesize_captcha_audio(ko_test_bytes, en_test_bytes)
        
        print(f" 합성 성공!")
        print(f"   - 결과 크기: {len(result_bytes):,} bytes")
        print(f"   - 샘플레이트: {metadata['sample_rate']}Hz")
        print(f"   - 지속시간: {metadata['duration_ms']}ms")
        print(f"   - 샘플 수: {metadata['n_samples']:,}")
        print(f"   - 오디오 해시: {metadata['audio_hash'][:16]}...")
        print(f"   - 파이프라인: {metadata['pipeline_version']}")
        
        return True, result_bytes, metadata
        
    except Exception as e:
        print(f" 합성 실패: {e}")
        return False, None, None

if __name__ == "__main__":
    success, result_bytes, metadata = test_synthesis()
    if success:
        print("\n PoC 테스트 성공!")
    else:
        print("\n PoC 테스트 실패!")
        exit(1)
