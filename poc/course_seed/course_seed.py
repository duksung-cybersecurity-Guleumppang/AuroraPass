from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class SeedCourse:
    courseId: str
    title: str
    professor: str
    schedule: str
    capacity: int
    enrolled: int = 0
    year: int = 2025
    semester: int = 1
    level: str = "학사"
    category: str = "전선"
    department: str = "사이버보안전공"


_DEPARTMENTS = [
    "컴퓨터공학과",
    "소프트웨어학과",
    "사이버보안전공",
    "데이터사이언스학과",
    "전자공학과",
    "수학과",
    "경영학과",
    "경제학과",
]


_PROFESSORS = [
    "김교수",
    "이교수",
    "박교수",
    "정교수",
    "최교수",
    "조교수",
    "윤교수",
    "강교수",
]


_WEEKDAYS = ["월", "화", "수", "목", "금"]


_TOPICS = [
    "프로그래밍",
    "자료구조",
    "알고리즘",
    "운영체제",
    "데이터베이스",
    "네트워크",
    "컴퓨터구조",
    "인공지능",
    "머신러닝",
    "보안",
    "클라우드",
    "블록체인",
    "웹개발",
    "모바일개발",
    "분산시스템",
]


# 학과별 어울리는 주제 목록 매핑
_DEPARTMENT_TOPICS = {
    "컴퓨터공학과": [
        "운영체제", "자료구조", "알고리즘", "컴퓨터구조", "네트워크", "데이터베이스",
    ],
    "소프트웨어학과": [
        "웹개발", "모바일개발", "클라우드", "분산시스템", "소프트웨어공학",
    ],
    "사이버보안전공": [
        "보안", "애플리케이션보안", "웹보안", "모바일보안", "클라우드보안",
        "암호학", "시스템보안", "디지털포렌식", "취약점진단", "모의해킹",
        "침해사고대응", "위협인텔리전스", "리버스엔지니어링", "악성코드분석",
        "DevSecOps", "제로트러스트", "IAM", "SIEM", "EDR",
        "IoT보안", "OT/ICS보안", "프라이버시공학", "블록체인보안",
        "보안거버넌스", "컴플라이언스", "위험관리", "보안아키텍처",
    ],
    "데이터사이언스학과": [
        "머신러닝", "인공지능", "통계학", "데이터마이닝", "딥러닝",
    ],
    "전자공학과": [
        "회로이론", "전자기학", "신호처리", "통신공학", "마이크로프로세서",
    ],
    "수학과": [
        "선형대수", "해석학", "확률론", "수치해석", "이산수학",
    ],
    "경영학과": [
        "마케팅", "재무관리", "회계학", "조직행동", "운영관리",
    ],
    "경제학과": [
        "미시경제", "거시경제", "계량경제", "국제경제", "산업조직",
    ],
}


def _make_schedule(idx: int) -> str:
    day = random.choice(_WEEKDAYS)
    start = 9 + (idx % 6)  # 09~14시 시작
    return f"{day} {start:02d}:00-{start + 1:02d}:30"


def generate_courses(n: int = 100, prefix: str = "CS") -> List[SeedCourse]:
    random.seed(42)
    courses: List[SeedCourse] = []
    years = [2024, 2025]
    semesters = [1, 2]
    levels = ["학사", "석사"]
    categories = ["전필", "전선", "교양"]

    for i in range(1, n + 1):
        code_num = 5500 + i
        dept = _DEPARTMENTS[(i - 1) % len(_DEPARTMENTS)]
        dept_topics = _DEPARTMENT_TOPICS.get(dept, _TOPICS)
        topic = dept_topics[(i * 3) % len(dept_topics)]
        # 화면 표시는 과목명만 사용, 전공은 별도 필드에 저장
        title = f"{topic}"
        professor = _PROFESSORS[(i * 7) % len(_PROFESSORS)]
        schedule = _make_schedule(i)
        capacity = [50, 60, 70, 80, 90, 100][(i * 5) % 6]
        year = years[(i // len(_DEPARTMENTS)) % len(years)]
        semester = semesters[(i // (len(_DEPARTMENTS) // 2 + 1)) % len(semesters)]
        level = levels[(i // 4) % len(levels)]
        category = categories[(i // 3) % len(categories)]
        # 과목 workload 생성
        theory_hours = 3 if level == "학사" else 2
        practice_hours = 1 if category != "교양" else 0
        courses.append(
            SeedCourse(
                courseId=f"{prefix}{code_num}",
                title=title,
                professor=professor,
                schedule=schedule,
                capacity=capacity,
                enrolled=0,
                year=year,
                semester=semester,
                level=level,
                category=category,
                department=dept,
            )
        )
    return courses


def to_json_list(courses: List[SeedCourse]) -> List[Dict]:
    return [
        {
            "courseId": c.courseId,
            "title": c.title,
            "professor": c.professor,
            "schedule": c.schedule,
            "capacity": c.capacity,
            "enrolled": c.enrolled,
            "year": c.year,
            "semester": c.semester,
            "level": c.level,
            "category": c.category,
            "department": c.department,
            "theoryHours": 3 if c.level == "학사" else 2,
            "practiceHours": 1 if c.category != "교양" else 0,
        }
        for c in courses
    ]


if __name__ == "__main__":
    import json
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    data = to_json_list(generate_courses(n))
    print(json.dumps(data, ensure_ascii=False, indent=2))