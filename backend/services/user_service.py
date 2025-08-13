import os
import uuid
from typing import Dict, Optional

from dotenv import load_dotenv
from models.user_models import UserRegisterRequest, UserLoginRequest
from services.captcha_service import captcha_service

# 실제 운영 환경에서는 PostgreSQL, MySQL 같은 관계형 데이터베이스를 사용해야 합니다.
# 여기서는 간단한 인메모리 딕셔너리를 사용하여 사용자 정보를 관리합니다.
# key: username, value: user_data
user_db: Dict[str, Dict] = {}

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

        # 2. 사용자 정보 중복 확인
        if request.username in user_db:
            raise ValueError("이미 사용 중인 아이디입니다.")
        
        for user in user_db.values():
            if user["email"] == request.email:
                raise ValueError("이미 사용 중인 이메일입니다.")

        # 3. 새 사용자 생성 및 저장
        # 실제로는 비밀번호를 해싱하여 저장해야 합니다. (예: passlib 라이브러리 사용)
        new_user_id = str(uuid.uuid4())
        new_user = {
            "user_id": new_user_id,
            "username": request.username,
            "email": request.email,
            "password_hash": f"hashed_{request.password}", # 실제 해싱 로직으로 대체 필요
        }
        
        user_db[request.username] = new_user
        
        print(f"User Registered: {new_user}") # 디버깅용 로그
        
        return new_user

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
