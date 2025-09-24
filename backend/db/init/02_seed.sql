-- Demo user (for API testing)
INSERT INTO users (id, username, email, password_hash) VALUES
('12345678-1234-1234-1234-123456789012', 'demo_user', 'demo@example.com', 'demo_hash')
ON CONFLICT (id) DO NOTHING;

-- Demo courses matching the JSON data
INSERT INTO courses (id, title, capacity, enrolled_count)
VALUES
  ('CS5501', '디지털포렌식', 60, 0),
  ('CS5502', '악성코드분석', 70, 0),
  ('CS5503', '네트워크보안', 80, 0),
  ('CS5504', '암호학개론', 100, 0),
  ('CS5505', '보안프로그래밍', 60, 0),
  ('CS5506', '취약점분석과대응', 70, 0),
  ('CS5507', '클라우드보안', 80, 0),
  ('CS5508', '침해사고대응', 60, 0),
  ('CS5509', '블록체인보안', 90, 0),
  ('CS5510', '보안정책과윤리', 100, 0)
ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, capacity = EXCLUDED.capacity;


