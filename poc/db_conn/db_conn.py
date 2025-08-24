import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://appuser:apppass@localhost:5432/aurora",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def ping() -> bool:
    with engine.connect() as conn:
        return conn.execute(text("select 1")).scalar() == 1


