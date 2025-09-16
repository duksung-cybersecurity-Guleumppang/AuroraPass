#!/usr/bin/env python3
"""
CAPTCHA 오디오 합성 PoC 테스트
"""
import unittest
import numpy as np
from captcha_synth import (
    synthesize_captcha_audio, 
    create_test_audio, 
    load_audio_from_bytes,
    save_audio_to_bytes,
    trim_silence_fn,
    fit_to_length,
    safe_mix,
    sha256_bytes
)

class TestCaptchaSynth(unittest.TestCase):
    """CAPTCHA 합성 로직 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.ko_test_audio = create_test_audio(440, 1.0)  # 1초 440Hz
        self.en_test_audio = create_test_audio(880, 0.8)  # 0.8초 880Hz
    
    def test_create_test_audio(self):
        """테스트 오디오 생성 검증"""
        audio_bytes = create_test_audio(440, 1.0)
        self.assertIsInstance(audio_bytes, bytes)
        self.assertGreater(len(audio_bytes), 0)
        
        # 오디오 로드해서 검증
        y = load_audio_from_bytes(audio_bytes)
        self.assertEqual(len(y), 16000)  # 1초 * 16kHz = 16000 샘플
    
    def test_load_audio_from_bytes(self):
        """바이트에서 오디오 로드 테스트"""
        y = load_audio_from_bytes(self.ko_test_audio)
        self.assertIsInstance(y, np.ndarray)
        self.assertEqual(y.dtype, np.float32)
        self.assertGreater(len(y), 0)
    
    def test_save_audio_to_bytes(self):
        """오디오를 바이트로 저장 테스트"""
        y = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)).astype(np.float32)
        audio_bytes = save_audio_to_bytes(y)
        self.assertIsInstance(audio_bytes, bytes)
        self.assertGreater(len(audio_bytes), 0)
    
    def test_trim_silence_fn(self):
        """무음 제거 함수 테스트"""
        # 앞뒤로 무음이 있는 오디오 생성
        silence = np.zeros(1000, dtype=np.float32)
        signal = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 8000)).astype(np.float32)
        y_with_silence = np.concatenate([silence, signal, silence])
        
        # 무음 제거
        y_trimmed = trim_silence_fn(y_with_silence, top_db=30)
        
        # 결과 검증
        self.assertLess(len(y_trimmed), len(y_with_silence))
        self.assertGreater(len(y_trimmed), 0)
    
    def test_fit_to_length(self):
        """길이 맞추기 함수 테스트"""
        y = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 8000)).astype(np.float32)
        
        # 늘리기 (loop 방식)
        y_extended = fit_to_length(y, 16000, "loop")
        self.assertEqual(len(y_extended), 16000)
        
        # 자르기
        y_truncated = fit_to_length(y, 4000, "loop")
        self.assertEqual(len(y_truncated), 4000)
        
        # 패딩 방식
        y_padded = fit_to_length(y, 10000, "pad")
        self.assertEqual(len(y_padded), 10000)
    
    def test_safe_mix(self):
        """안전한 믹싱 함수 테스트"""
        a = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000)).astype(np.float32)
        b = np.sin(2 * np.pi * 880 * np.linspace(0, 1, 16000)).astype(np.float32)
        
        mixed = safe_mix(a, b, 1.0)
        
        # 결과 검증
        self.assertEqual(len(mixed), len(a))
        self.assertLessEqual(np.max(np.abs(mixed)), 1.0)  # 클리핑 확인
        self.assertGreaterEqual(np.min(mixed), -1.0)
    
    def test_sha256_bytes(self):
        """SHA256 해시 함수 테스트"""
        test_data = b"test data"
        hash_result = sha256_bytes(test_data)
        
        self.assertIsInstance(hash_result, str)
        self.assertEqual(len(hash_result), 64)  # SHA256은 64자리 hex
        
        # 같은 데이터는 같은 해시
        hash_result2 = sha256_bytes(test_data)
        self.assertEqual(hash_result, hash_result2)
        
        # 다른 데이터는 다른 해시
        hash_result3 = sha256_bytes(b"different data")
        self.assertNotEqual(hash_result, hash_result3)
    
    def test_synthesize_captcha_audio(self):
        """전체 합성 파이프라인 테스트"""
        result_bytes, metadata = synthesize_captcha_audio(
            self.ko_test_audio, 
            self.en_test_audio
        )
        
        # 결과 검증
        self.assertIsInstance(result_bytes, bytes)
        self.assertGreater(len(result_bytes), 0)
        
        # 메타데이터 검증
        self.assertIsInstance(metadata, dict)
        self.assertIn('sample_rate', metadata)
        self.assertIn('duration_ms', metadata)
        self.assertIn('n_samples', metadata)
        self.assertIn('audio_hash', metadata)
        self.assertIn('params', metadata)
        self.assertIn('pipeline_version', metadata)
        
        # 값 검증
        self.assertEqual(metadata['sample_rate'], 16000)
        self.assertGreater(metadata['duration_ms'], 0)
        self.assertGreater(metadata['n_samples'], 0)
        self.assertEqual(len(metadata['audio_hash']), 64)
        self.assertEqual(metadata['pipeline_version'], 'v1')
        
        # 오디오 로드해서 검증
        result_audio = load_audio_from_bytes(result_bytes)
        self.assertEqual(len(result_audio), metadata['n_samples'])
    
    def test_synthesis_reproducibility(self):
        """합성 결과 재현성 테스트"""
        result1_bytes, metadata1 = synthesize_captcha_audio(
            self.ko_test_audio, 
            self.en_test_audio
        )
        
        result2_bytes, metadata2 = synthesize_captcha_audio(
            self.ko_test_audio, 
            self.en_test_audio
        )
        
        # 같은 입력은 같은 결과를 생성해야 함
        self.assertEqual(metadata1['audio_hash'], metadata2['audio_hash'])
        self.assertEqual(len(result1_bytes), len(result2_bytes))
    
    def test_different_inputs_different_outputs(self):
        """다른 입력에 대해 다른 출력 생성 테스트"""
        ko_audio2 = create_test_audio(330, 1.2)  # 다른 주파수, 다른 길이
        
        result1_bytes, metadata1 = synthesize_captcha_audio(
            self.ko_test_audio, 
            self.en_test_audio
        )
        
        result2_bytes, metadata2 = synthesize_captcha_audio(
            ko_audio2, 
            self.en_test_audio
        )
        
        # 다른 입력은 다른 해시를 생성해야 함
        self.assertNotEqual(metadata1['audio_hash'], metadata2['audio_hash'])

def run_tests():
    """테스트 실행"""
    print(" CAPTCHA 합성 PoC 테스트 시작...")
    
    # 테스트 실행
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n 모든 테스트 완료!")

if __name__ == "__main__":
    run_tests()
