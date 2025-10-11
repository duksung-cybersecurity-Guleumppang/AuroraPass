#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Set

from sqlalchemy import text

from db.session import get_db_session


def sync_to_curated(curated_path: Path) -> int:
    with curated_path.open('r', encoding='utf-8') as f:
        curated = json.load(f)

    curated_ids: Set[str] = {c["courseId"] for c in curated}

    removed = 0
    with get_db_session() as session:
        # 비활성화: curated에 없는 코스는 비활성 처리, curated에 있는 코스는 활성화
        session.execute(
            text("UPDATE courses SET is_active = false WHERE id NOT IN :ids"),
            {"ids": tuple(curated_ids) if curated_ids else ("__none__",)},
        )
        res = session.execute(
            text("UPDATE courses SET is_active = true WHERE id IN :ids"),
            {"ids": tuple(curated_ids) if curated_ids else ("__none__",)},
        )
        removed = res.rowcount or 0

    return removed


def main():
    default_path = Path(__file__).parent.parent / "static" / "demo" / "courses_curated.json"
    removed = sync_to_curated(default_path)
    print(f"Removed {removed} non-curated courses. Synced to {default_path}.")


if __name__ == "__main__":
    main()


