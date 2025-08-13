FROM oven/bun:1 AS base
WORKDIR /app

# 의존성 파일만 먼저 복사하여 캐시 활용
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile || bun install

# 소스 복사
COPY . .

# 개발 서버
EXPOSE 3000
CMD ["bun", "run", "dev"]