-- Audio synthesis schema migration
-- This migration adds tables and columns for audio synthesis feature

-- Audio sources table (stores raw audio files as bytea)
CREATE TABLE IF NOT EXISTS audio_sources (
  id                 bigserial PRIMARY KEY,
  language           varchar(8)   NOT NULL,                  -- 'ko' | 'en'
  original_filename  varchar(255) NOT NULL,                  -- 예: '1.wav'
  content_type       varchar(50)  NOT NULL DEFAULT 'audio/wav',
  audio_data         bytea        NOT NULL,                  -- ★ 원본 바이너리
  sample_rate        int          NOT NULL,
  duration_ms        int,
  n_samples          int,
  audio_hash         char(64)     NOT NULL,                  -- 원본 바이트 SHA256
  created_at         timestamptz  NOT NULL DEFAULT now(),
  CONSTRAINT ux_audio_sources_hash UNIQUE (audio_hash)
);

CREATE INDEX IF NOT EXISTS ix_audio_sources_lang ON audio_sources (language);
CREATE INDEX IF NOT EXISTS ix_audio_sources_created ON audio_sources (created_at DESC);

-- Korean source to answer mapping table
CREATE TABLE IF NOT EXISTS ko_source_answers (
  ko_key       varchar(255) PRIMARY KEY,   -- 확장자 제거 파일명 (예: '1', '2')
  question     text         NOT NULL,
  answer       varchar(100) NOT NULL,
  ko_source_id bigint UNIQUE,
  CONSTRAINT fk_ko_source
    FOREIGN KEY (ko_source_id) REFERENCES audio_sources(id)
    ON DELETE SET NULL
);

-- Extend existing captcha_files table for synthesis results
ALTER TABLE captcha_files
  ADD COLUMN IF NOT EXISTS sample_rate       int     NOT NULL DEFAULT 16000,
  ADD COLUMN IF NOT EXISTS duration_ms       int,
  ADD COLUMN IF NOT EXISTS n_samples         int,
  ADD COLUMN IF NOT EXISTS params            jsonb   NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS pipeline_version  varchar(20) DEFAULT 'v1',
  ADD COLUMN IF NOT EXISTS audio_hash        char(64),
  ADD COLUMN IF NOT EXISTS ko_source_id      bigint REFERENCES audio_sources(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS en_source_id      bigint REFERENCES audio_sources(id) ON DELETE SET NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_captcha_files_audio_hash ON captcha_files (audio_hash);
CREATE INDEX        IF NOT EXISTS ix_captcha_files_created_at ON captcha_files (created_at DESC);
CREATE INDEX        IF NOT EXISTS ix_captcha_files_params_gin ON captcha_files USING GIN (params);
