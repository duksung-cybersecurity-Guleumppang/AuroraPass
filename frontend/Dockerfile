FROM oven/bun:1 AS base
WORKDIR /app

# 의존성 파일만 먼저 복사하여 캐시 활용
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile || bun install

# 소스 복사
COPY . .

# 개발 서버 (포트는 환경변수 FRONT_PORT 또는 PORT 사용, 기본 3000)
ARG FRONT_PORT
ENV FRONT_PORT=${FRONT_PORT}
ENV PORT=${FRONT_PORT:-${PORT}}
EXPOSE ${FRONT_PORT:-3000}
CMD ["sh", "-lc", "bun run dev"]