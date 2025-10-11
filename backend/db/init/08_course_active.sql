-- Add is_active flag to courses and index it
ALTER TABLE courses ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS ix_courses_is_active ON courses (is_active);


