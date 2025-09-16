-- CAPTCHA availability schema migration
-- Adds used flag, expiration, and availability index for atomic consumption

-- Add availability columns to captcha_files
ALTER TABLE captcha_files
  ADD COLUMN IF NOT EXISTS used boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS expires_at timestamptz;

-- Create availability index for efficient atomic selection
CREATE INDEX IF NOT EXISTS ix_captcha_files_available
  ON captcha_files (used, created_at DESC)
  WHERE used = false;

-- Backfill existing data to used=false
UPDATE captcha_files 
SET used = false 
WHERE used IS NULL;
