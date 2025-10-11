#!/usr/bin/env python3
import sys
import json
from pathlib import Path

from poc.course_seed.course_seed import generate_courses, to_json_list


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_courses.py <count> [output_path]", file=sys.stderr)
        sys.exit(1)

    try:
        n = int(sys.argv[1])
    except ValueError:
        print("count must be an integer", file=sys.stderr)
        sys.exit(1)

    output_path = None
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])

    data = to_json_list(generate_courses(n))

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {n} courses to {output_path}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


