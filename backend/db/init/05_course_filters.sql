-- Extend courses table with filterable fields
ALTER TABLE courses
    ADD COLUMN IF NOT EXISTS year int NOT NULL DEFAULT 2025,
    ADD COLUMN IF NOT EXISTS semester smallint NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS level varchar(20),
    ADD COLUMN IF NOT EXISTS category varchar(30),
    ADD COLUMN IF NOT EXISTS department varchar(100);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS ix_courses_year ON courses(year);
CREATE INDEX IF NOT EXISTS ix_courses_semester ON courses(semester);
CREATE INDEX IF NOT EXISTS ix_courses_level ON courses(level);
CREATE INDEX IF NOT EXISTS ix_courses_category ON courses(category);
CREATE INDEX IF NOT EXISTS ix_courses_department ON courses(department);
CREATE INDEX IF NOT EXISTS ix_courses_title_lower ON courses((lower(title)));

