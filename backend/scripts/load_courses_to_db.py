#!/usr/bin/env python3
import json
from pathlib import Path
import sys
from sqlalchemy import text

from db.session import get_db_session


def upsert_courses(data_path: Path) -> int:
    with open(data_path, "r", encoding="utf-8") as f:
        courses = json.load(f)

    count = 0
    with get_db_session() as session:
        for c in courses:
            course_id = c["courseId"]
            title = c["title"]
            capacity = int(c.get("capacity", 0))

            session.execute(
                text(
                    """
                    INSERT INTO courses (id, title, capacity, enrolled_count, year, semester, level, category, department, theory_hours, practice_hours)
                    VALUES (:id, :title, :capacity, :enrolled, :year, :semester, :level, :category, :department, :theory_hours, :practice_hours)
                    ON CONFLICT (id) DO UPDATE SET
                      title = EXCLUDED.title,
                      capacity = EXCLUDED.capacity,
                      year = COALESCE(EXCLUDED.year, courses.year),
                      semester = COALESCE(EXCLUDED.semester, courses.semester),
                      level = COALESCE(EXCLUDED.level, courses.level),
                      category = COALESCE(EXCLUDED.category, courses.category),
                      theory_hours = COALESCE(EXCLUDED.theory_hours, courses.theory_hours),
                      practice_hours = COALESCE(EXCLUDED.practice_hours, courses.practice_hours),
                      department = COALESCE(EXCLUDED.department, courses.department),
                      updated_at = now()
                    """
                ),
                {
                    "id": course_id,
                    "title": title,
                    "capacity": capacity,
                    "enrolled": int(c.get("enrolled", 0)),
                    "year": int(c.get("year", 2025)),
                    "semester": int(c.get("semester", 1)),
                    "level": c.get("level"),
                    "category": c.get("category"),
                    "department": c.get("department"),
                    "theory_hours": int(c.get("theoryHours") or c.get("theory_hours") or 3),
                    "practice_hours": int(c.get("practiceHours") or c.get("practice_hours") or 1),
                },
            )
            count += 1
    return count


def main():
    default_path = Path(__file__).parent.parent / "static" / "demo" / "courses.json"
    path = Path(sys.argv[1]) if len(sys.argv) >= 2 else default_path

    n = upsert_courses(path)
    print(f"Upserted {n} courses from {path}")


if __name__ == "__main__":
    main()


