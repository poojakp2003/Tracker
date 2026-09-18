"""Temporary connectivity test: FastAPI -> SQLAlchemy -> PostgreSQL."""

import sys

from sqlalchemy import text

from app.core.database import get_db
from app.main import app


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    assert app.title == "Tracker API"

    db = next(get_db())
    try:
        value = db.execute(text("SELECT 1")).scalar()
        database = db.execute(text("SELECT current_database()")).scalar()
    finally:
        db.close()

    if value != 1:
        raise SystemExit(f"Unexpected SELECT 1 result: {value}")

    print("PostgreSQL connection ✓")
    print(f"database={database}")


if __name__ == "__main__":
    main()
