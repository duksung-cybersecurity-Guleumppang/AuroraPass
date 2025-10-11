-- Ensure unique course titles (case-insensitive) by creating an index on lower(title)
CREATE UNIQUE INDEX IF NOT EXISTS ux_courses_title_lower ON courses (lower(title));


