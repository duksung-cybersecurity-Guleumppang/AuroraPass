import os
from typing import Dict, Optional

from dotenv import load_dotenv
from models.user_models import UserRegisterRequest, UserLoginRequest
from services.captcha_service import captcha_service
from repositories.user_repository import user_repository

class UserService:
    """
    사용자 관련 비즈니스 로직을 처리하는 서비스
    """

    def register_user(self, request: UserRegisterRequest) -> Optional[Dict]:
        """
        신규 사용자를 등록합니다.

        Args:
            request (UserRegisterRequest): 사용자 가입 요청 데이터

        Returns:
            Optional[Dict]: 등록 성공 시 생성된 사용자 정보, 실패 시 None
        """
        # 1. CAPTCHA 검증
        if not captcha_service.verify_captcha(request.captcha_id, request.user_input):
            raise ValueError("CAPTCHA 인증에 실패했습니다.")

        # 2. 새 사용자 생성 (중복 확인은 repository에서 처리)
        try:
            new_user = user_repository.create_user(
                username=request.username,
                email=request.email,
                password=request.password
            )
            
            print(f"User Registered: {new_user.username} ({new_user.id})")  # 디버깅용 로그
            
            return {
                "user_id": str(new_user.id),
                "username": new_user.username,
                "email": new_user.email
            }
        except ValueError as e:
            # Repository에서 발생한 중복 에러를 그대로 전파
            raise e

    def login_user(self, request: UserLoginRequest) -> bool:
        """
        환경변수(LOGIN_USERNAME, LOGIN_PASSWORD)와 비교하여 로그인 검증을 수행합니다.
        실제 서비스에서는 해시 검증 및 DB를 사용해야 합니다.
        """
        # 컨테이너/프로세스 환경에서 .env를 로드(존재 시)
        load_dotenv(override=False)

        expected_username = os.getenv("LOGIN_USERNAME", "")
        expected_password = os.getenv("LOGIN_PASSWORD", "")

        is_valid = (
            request.username == expected_username and request.password == expected_password
        )

        return is_valid

# 서비스 인스턴스 생성
user_service = UserService()
