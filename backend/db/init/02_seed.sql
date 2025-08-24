-- Demo courses matching the JSON data
INSERT INTO courses (id, title, capacity, enrolled_count)
VALUES
  ('CS5501', '졸린데안졸린척하는법', 2, 0),
  ('CS101', '컴퓨터개론', 2, 0),
  ('CS201', '자료구조', 1, 0),
  ('CS301', '운영체제', 1, 0),
  ('CS5401', '사이버보안개론', 3, 0)
ON CONFLICT (id) DO NOTHING;


