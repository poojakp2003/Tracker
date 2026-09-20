"""Temporary connectivity test: FastAPI -> SQLAlchemy -> PostgreSQL."""

import sys

from sqlalchemy import text

from app.core.database import SessionLocal
from app.main import app


def main() -> None:
    """Validate database connection and print current database name."""
    sys.stdout.reconfigure(encoding="utf-8")
    assert app.title == "Tracker API"

    with SessionLocal() as db:
        value = db.execute(text("SELECT 1")).scalar()
        database = db.execute(text("SELECT current_database()")).scalar()

    if value != 1:
        raise SystemExit(f"Unexpected SELECT 1 result: {value}")

    print("PostgreSQL connection ✓")
    print(f"database={database}")


if __name__ == "__main__":
    main()
