#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import List


BANNED_SUBSTRINGS: List[str] = [
    "전공세미나",
    "심화세미나",
    "학문포럼",
    "오픈워크숍",
    "융합특강",
    "응용프로젝트",
    "인턴십 세미나",
    "리딩스",
    "학습공동체",
]


def clean_curated(input_path: Path, output_path: Path, inplace: bool = False) -> int:
    with input_path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    def is_banned(title: str) -> bool:
        title = title or ""
        return any(bad in title for bad in BANNED_SUBSTRINGS)

    # 1) 금지 패턴 제거
    filtered = [c for c in data if not is_banned(c.get('title', ''))]
    # 2) 과목명 유일화: 같은 제목(대소문자 무시)은 첫 항목만 유지
    seen = set()
    unique = []
    for c in filtered:
        title = (c.get('title') or '').strip()
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        unique.append(c)

    target = input_path if inplace else output_path
    if not inplace and not output_path:
        raise ValueError("output_path must be provided when not using --inplace")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding='utf-8')
    return len(data) - len(unique)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=str, help='Path to courses_curated.json')
    p.add_argument('--output', type=str, default='', help='Optional output path (default: overwrite input)')
    p.add_argument('--inplace', action='store_true', help='Overwrite input file in place')
    args = p.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    removed = clean_curated(input_path, output_path, inplace=args.inplace)
    print(f"Removed {removed} banned-title courses from {output_path}")


if __name__ == '__main__':
    main()


