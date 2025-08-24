#!/bin/bash
# AWS 배포 스크립트
# 사용법: ./scripts/deploy.sh

set -e

echo "Aurora Pass AWS 배포 시작..."

# 환경변수 파일 확인
if [ ! -f "deploy.env" ]; then
    echo " deploy.env 파일이 없습니다."
    echo "   deploy.env.example을 복사하여 deploy.env를 만들고 값을 채워주세요."
    echo "   cp deploy.env.example deploy.env"
    exit 1
fi

# 환경변수 로드
echo " 환경변수 로드 중..."
set -a
source deploy.env
set +a

# 필수 환경변수 확인
required_vars=("AWS_REGION" "ACCOUNT_ID" "IMAGE_TAG" "DATABASE_URL" "REDIS_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo " 필수 환경변수 $var이 설정되지 않았습니다."
        exit 1
    fi
done

# ECR 레지스트리 URL 구성
export ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "🔧 배포 설정:"
echo "   리전: $AWS_REGION"
echo "   ECR: $ECR_REGISTRY"
echo "   태그: $IMAGE_TAG"

# ECR 로그인
echo "🔐 ECR 로그인 중..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# 이미지 빌드 및 푸시
echo "🏗️  이미지 빌드 및 푸시 중..."

# Backend
echo "   Backend 빌드 중..."
docker buildx build \
  -t $ECR_REGISTRY/aurora-backend:$IMAGE_TAG \
  -f backend/Dockerfile \
  --platform linux/amd64 \
  --push .

# Frontend  
echo "   Frontend 빌드 중..."
docker buildx build \
  -t $ECR_REGISTRY/aurora-frontend:$IMAGE_TAG \
  -f frontend/Dockerfile \
  --platform linux/amd64 \
  --push frontend

echo " 이미지 빌드/푸시 완료!"
echo " 다음 단계:"
echo "   1. ECS 태스크 정의에서 이미지를 다음으로 업데이트:"
echo "      - Backend: $ECR_REGISTRY/aurora-backend:$IMAGE_TAG"
echo "      - Frontend: $ECR_REGISTRY/aurora-frontend:$IMAGE_TAG"
echo "   2. ECS 서비스 업데이트"
echo "   3. ALB 헬스체크 확인"
echo ""
echo " 배포 확인:"
echo "   curl http://<alb-dns>/readyz"
