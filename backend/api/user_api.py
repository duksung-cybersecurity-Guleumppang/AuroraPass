from fastapi import APIRouter, HTTPException, status
from models.user_models import UserRegisterRequest, UserRegisterResponse
from services.user_service import user_service

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 가입 (회원가입)",
    description="CAPTCHA 인증을 포함한 신규 사용자 가입을 처리합니다.",
)
async def register_user(request: UserRegisterRequest):
    """
    신규 사용자를 등록합니다.
    - CAPTCHA 인증
    - 사용자 정보 중복 확인
    - 사용자 생성
    """
    try:
        new_user = user_service.register_user(request)
        if not new_user:
            # 이 경우는 현재 로직 상 발생하지 않지만, 안전을 위해 추가
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 등록에 실패했습니다.",
            )
        
        return UserRegisterResponse(
            userId=new_user["user_id"],
            username=new_user["username"],
            message="회원가입이 성공적으로 완료되었습니다.",
        )
    except ValueError as e:
        # 서비스에서 발생한 오류(CAPTCHA 실패, 중복 등)를 400 에러로 처리
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # 기타 예상치 못한 서버 오류
        print(f"Error registering user: {e}") # 로깅
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )
