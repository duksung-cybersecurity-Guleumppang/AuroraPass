import uuid
from typing import Tuple
from db.redis_client import store_captcha, verify_captcha_redis
from db.captcha_repository import captcha_repository

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
        
        # DB에서 가용한 CAPTCHA 원자적 소비
        captcha_data = captcha_repository.get_random_captcha()
        if not captcha_data:
            raise RuntimeError("사용 가능한 CAPTCHA 파일이 DB에 없습니다.")
        
        file_id, filename, answer, audio_data, content_type = captcha_data
        audio_path = f"/api/captcha/audio/{file_id}"
        
        # 생성된 CAPTCHA ID와 정답을 Redis에 TTL 5분으로 저장합니다.
        from db.redis_client import redis_client
        redis_client.setex(f"captcha:{captcha_id}", 300, answer)
        
        print(f"CAPTCHA Created: ID={captcha_id}, File={filename}, Answer={answer}") # 디버깅용 로그
        
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
        is_correct = verify_captcha_redis(captcha_id, user_input)
        
        print(f"CAPTCHA Verification: ID={captcha_id}, Input='{user_input}', Result={is_correct}") # 디버깅용 로그
        
        return is_correct

# 서비스 인스턴스 생성
captcha_service = CaptchaService()
