-- Demo user (for API testing)
INSERT INTO users (id, username, email, password_hash) VALUES
('12345678-1234-1234-1234-123456789012', 'demo_user', 'demo@example.com', 'demo_hash')
ON CONFLICT (id) DO NOTHING;

-- Demo courses matching the JSON data
INSERT INTO courses (id, title, capacity, enrolled_count)
VALUES
  ('CS5501', '졸린데안졸린척하는법', 2, 0),
  ('CS101', '컴퓨터개론', 2, 0),
  ('CS201', '자료구조', 1, 0),
  ('CS301', '운영체제', 1, 0),
  ('CS5401', '사이버보안개론', 3, 0)
ON CONFLICT (id) DO NOTHING;


