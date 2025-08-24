# poc/db_conn/db_conn.py
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Please export it or add to .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def ping() -> bool:
    with engine.connect() as conn:
        return conn.execute(text("select 1")).scalar() == 1