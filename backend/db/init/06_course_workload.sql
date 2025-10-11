-- Add theory/practice hours to courses
ALTER TABLE courses ADD COLUMN IF NOT EXISTS theory_hours INTEGER NOT NULL DEFAULT 3;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS practice_hours INTEGER NOT NULL DEFAULT 1;

-- Optional: simple check constraints (non-negative)
ALTER TABLE courses DROP CONSTRAINT IF EXISTS check_theory_hours_nonnegative;
ALTER TABLE courses ADD CONSTRAINT check_theory_hours_nonnegative CHECK (theory_hours >= 0);
ALTER TABLE courses DROP CONSTRAINT IF EXISTS check_practice_hours_nonnegative;
ALTER TABLE courses ADD CONSTRAINT check_practice_hours_nonnegative CHECK (practice_hours >= 0);


