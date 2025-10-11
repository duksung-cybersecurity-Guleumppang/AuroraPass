#!/usr/bin/env python3
import json
import random
import sys
from pathlib import Path
from typing import Dict, List

from sqlalchemy import select

from db.models import Course
from db.session import get_db_session


DEPT_TITLE_TEMPLATES: Dict[str, List[str]] = {
    "컴퓨터공학과": [
        "고급 {topic} 설계와 구현", "현대 {topic} 이론과 응용", "{topic} 심화 프로젝트",
    ],
    "소프트웨어학과": [
        "대규모 {topic} 사례연구", "{topic} 아키텍처와 패턴", "{topic} 실무 워크숍",
    ],
    "사이버보안전공": [
        "현대 {topic}과 보안 프로토콜", "{topic} 위협 모델링과 대응", "{topic} 심층 분석",
    ],
    "데이터사이언스학과": [
        "딥러닝 기반 {topic}", "{topic}과 통계적 추론", "{topic} 실전 프로젝트",
    ],
    "전자공학과": [
        "{topic} 이론과 실험", "실전 {topic} 설계", "{topic} 시스템 구현",
    ],
    "수학과": [
        "{topic} 심화", "{topic}과 응용", "{topic} 이론",
    ],
    "경영학과": [
        "{topic}과 데이터 분석", "{topic} 전략과 사례", "실무 {topic}",
    ],
    "경제학과": [
        "{topic} 동학과 정책 분석", "{topic} 심화", "{topic} 모델링",
    ],
}

DEPT_TOPICS: Dict[str, List[str]] = {
    "컴퓨터공학과": ["운영체제", "자료구조", "알고리즘", "컴퓨터구조", "네트워크", "데이터베이스"],
    "소프트웨어학과": ["웹개발", "모바일개발", "클라우드", "분산시스템", "소프트웨어공학"],
    "사이버보안전공": [
        "애플리케이션보안", "웹보안", "모바일보안", "클라우드보안",
        "암호학", "시스템보안", "네트워크보안", "디지털포렌식",
        "취약점진단", "모의해킹", "침해사고대응", "위협인텔리전스",
        "리버스엔지니어링", "악성코드분석", "DevSecOps", "제로트러스트",
        "IAM", "SIEM", "EDR", "IoT보안", "OT/ICS보안",
        "프라이버시공학", "블록체인보안", "보안거버넌스", "컴플라이언스", "위험관리",
    ],
    "데이터사이언스학과": ["머신러닝", "딥러닝", "통계학", "데이터마이닝"],
    "전자공학과": ["신호처리", "회로이론", "통신공학", "마이크로프로세서"],
    "수학과": ["선형대수", "해석학", "확률론", "수치해석", "이산수학"],
    "경영학과": ["마케팅", "재무관리", "회계학", "조직행동", "운영관리"],
    "경제학과": ["미시경제", "거시경제", "계량경제", "국제경제", "산업조직"],
}


def build_title(department: str, seed_index: int) -> str:
    topics = DEPT_TOPICS.get(department, ["전공특강"])
    templates = DEPT_TITLE_TEMPLATES.get(department, ["{topic}"])
    topic = topics[seed_index % len(topics)]
    template = templates[(seed_index * 7) % len(templates)]
    return template.format(topic=topic)


def generate_curated_from_db(limit: int = 1000) -> List[dict]:
    curated: List[dict] = []
    with get_db_session() as session:
        rows = session.execute(
            select(Course.id, Course.department, Course.year, Course.semester, Course.level, Course.category, Course.capacity)
            .order_by(Course.id)
            .limit(limit)
        ).all()

        random.seed(123)
        for idx, (cid, dept, year, semester, level, category, capacity) in enumerate(rows):
            if not dept:
                dept = "교양"
            title = build_title(dept, idx)
            professor = random.choice(["김교수", "이교수", "박교수", "정교수", "최교수", "조교수", "윤교수", "강교수"])  # noqa
            weekday = random.choice(["월", "화", "수", "목", "금"])  # noqa
            start = 9 + (idx % 6)
            schedule = f"{weekday} {start:02d}:00-{start + 2:02d}:00"

            curated.append({
                "courseId": cid,
                "title": title,
                "professor": professor,
                "schedule": schedule,
                "capacity": int(capacity or 60),
                "enrolled": 0,
                "department": dept,
                "year": int(year or 2025),
                "semester": int(semester or 1),
                "level": level or "학사",
                "category": category or "전선",
            })
    return curated


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) >= 2 else Path(__file__).parent.parent / "static" / "demo" / "courses_curated.json"
    data = generate_curated_from_db()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote curated {len(data)} courses to {out_path}")


if __name__ == "__main__":
    main()


