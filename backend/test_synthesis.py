import io
import numpy as np
import soundfile as sf
import librosa

def create_test_audio(freq, duration, sr=16000):
    t = np.linspace(0, duration, int(sr * duration), False)
    y = np.sin(2 * np.pi * freq * t).astype(np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, y, sr, format='WAV')
    return buffer.getvalue()

# 테스트 실행
ko_bytes = create_test_audio(440, 1.0)
en_bytes = create_test_audio(880, 0.8)

print(f'한글 테스트 오디오: {len(ko_bytes)} bytes')
print(f'영어 테스트 오디오: {len(en_bytes)} bytes')

# librosa로 로드 테스트
ko_audio = librosa.load(io.BytesIO(ko_bytes), sr=16000)[0]
en_audio = librosa.load(io.BytesIO(en_bytes), sr=16000)[0]

print(f'한글 오디오 샘플: {len(ko_audio)}')
print(f'영어 오디오 샘플: {len(en_audio)}')
print('기본 합성 라이브러리 테스트 성공!')
