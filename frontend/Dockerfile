FROM oven/bun:1 AS base
WORKDIR /app

COPY package.json bun.lock* bun.lockb* ./
RUN sh -lc 'if [ -f bun.lockb ]; then bun install --frozen-lockfile --no-progress; else bun install --no-progress; fi'

# 소스 복사
COPY . .

# 개발 서버 (포트는 환경변수 FRONT_PORT 또는 PORT 사용, 기본 3000)
ARG FRONT_PORT
ENV FRONT_PORT=${FRONT_PORT}
ENV PORT=${FRONT_PORT:-${PORT}}
EXPOSE ${FRONT_PORT:-3000}
CMD ["sh", "-lc", "bun run dev"]