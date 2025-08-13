import os
import json
import uuid
import random
from typing import Dict, Tuple

# 실제 운영 환경에서는 Redis나 DB를 사용해야 합니다.
# 여기서는 간단한 인메모리 딕셔너리를 사용하여 CAPTCHA의 정답을 관리합니다.
captcha_storage: Dict[str, str] = {}

def _load_available_captchas() -> Dict[str, str]:
    """
    backend/static/audio/captcha_answers.json 을 로드하여
    {"sample1.wav": "apple", ...} 형태를
    {"/static/audio/sample1.wav": "apple", ...} 로 변환합니다.
    """
    answers_path = os.path.join(os.path.dirname(__file__), "..", "static", "audio", "captcha_answers.json")
    answers_path = os.path.abspath(answers_path)
    with open(answers_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    mapping: Dict[str, str] = {}
    for filename, answer in data.items():
        mapping[f"/static/audio/{filename}"] = answer
    return mapping

available_captchas: Dict[str, str] = _load_available_captchas()

class CaptchaService:
    """
    CAPTCHA 생성 및 검증을 처리하는 서비스
    """

    def create_captcha(self) -> Tuple[str, str]:
        """
        새로운 CAPTCHA를 생성하고 ID와 오디오 경로를 반환합니다.

        Returns:
            Tuple[str, str]: (captcha_id, audio_path)
        """
        captcha_id = str(uuid.uuid4())
        
        # 사용 가능한 CAPTCHA 중에서 무작위로 하나를 선택합니다.
        audio_path, answer = random.choice(list(available_captchas.items()))
        
        # 생성된 CAPTCHA ID와 정답을 저장소에 기록합니다.
        captcha_storage[captcha_id] = answer
        
        print(f"CAPTCHA Created: ID={captcha_id}, Answer={answer}") # 디버깅용 로그
        
        return captcha_id, audio_path

    def verify_captcha(self, captcha_id: str, user_input: str) -> bool:
        """
        사용자가 제출한 CAPTCHA 정답을 검증합니다.
        검증 시도 후에는 저장된 CAPTCHA 정보를 삭제하여 재사용을 방지합니다.

        Args:
            captcha_id (str): 검증할 CAPTCHA의 고유 ID
            user_input (str): 사용자가 입력한 정답

        Returns:
            bool: 정답이 일치하면 True, 그렇지 않으면 False
        """
        correct_answer = captcha_storage.get(captcha_id)
        
        # 검증 시도 후에는 항상 저장소에서 삭제
        if captcha_id in captcha_storage:
            del captcha_storage[captcha_id]
            
        if not correct_answer:
            print(f"CAPTCHA Verification Failed: ID={captcha_id} not found.") # 디버깅용 로그
            return False
            
        is_correct = (user_input.lower() == correct_answer.lower())
        
        print(f"CAPTCHA Verification: ID={captcha_id}, Input='{user_input}', Correct='{correct_answer}', Result={is_correct}") # 디버깅용 로그
        
        return is_correct

# 서비스 인스턴스 생성
captcha_service = CaptchaService()
