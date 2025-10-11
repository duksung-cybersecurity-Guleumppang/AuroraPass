from poc.course_seed.course_seed import generate_courses, to_json_list


def test_generate_courses_count():
    courses = generate_courses(100)
    assert len(courses) == 100


def test_generate_courses_schema():
    courses = generate_courses(3, prefix="CS")
    data = to_json_list(courses)
    assert all(set(["courseId", "title", "professor", "schedule", "capacity", "enrolled"]).issubset(d.keys()) for d in data)
    assert data[0]["courseId"].startswith("CS")
    assert isinstance(data[0]["capacity"], int)

