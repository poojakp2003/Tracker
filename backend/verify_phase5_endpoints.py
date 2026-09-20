"""Verification script for Phase 5 Dashboard APIs:
- GET /dashboard/timeline (Line Chart data)
- GET /dashboard/browser-history (Browser Activity table data)
"""

from datetime import datetime, timedelta, timezone
import sys

from app.core.database import SessionLocal
from app.models.app_usage import AppUsage
from app.models.browser_activity import BrowserActivity
from app.models.user import User
from app.routers.dashboard import get_dashboard_browser_history, get_dashboard_timeline


def run_verification() -> None:
    """Execute end-to-end verification of Phase 5 timeline and browser history endpoints."""
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 65)
    print("Phase 5 Backend Verification: Timeline and Browser History Endpoints")
    print("=" * 65)

    now = datetime.now(timezone.utc)
    ts = int(now.timestamp())
    test_email = f"phase5_test_{ts}@example.com"

    with SessionLocal() as db:
        # 1. Create temporary test user
        user = User(
            email=test_email,
            password_hash="hashed_test_password",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id


        try:
            # 2. Seed AppUsage for Timeline (e.g. today 4h, yesterday 6h, 2 days ago 3h)
            db.add_all([
                AppUsage(
                    user_id=user_id,
                    app_name="Chrome",
                    window_title="Google Search",
                    start_time=now - timedelta(hours=4),
                    end_time=now,
                    duration_seconds=14400,  # 4 hours
                ),
                AppUsage(
                    user_id=user_id,
                    app_name="VS Code",
                    window_title="Main.jsx",
                    start_time=now - timedelta(days=1, hours=6),
                    end_time=now - timedelta(days=1),
                    duration_seconds=21600,  # 6 hours
                ),
                AppUsage(
                    user_id=user_id,
                    app_name="Slack",
                    window_title="#general",
                    start_time=now - timedelta(days=2, hours=3),
                    end_time=now - timedelta(days=2),
                    duration_seconds=10800,  # 3 hours
                ),
            ])

            # 3. Seed BrowserActivity
            db.add_all([
                BrowserActivity(
                    user_id=user_id,
                    browser="Chrome",
                    url="https://google.com/search?q=fastapi",
                    title="Google Search - FastAPI",
                    timestamp=now - timedelta(minutes=40),
                ),
                BrowserActivity(
                    user_id=user_id,
                    browser="Chrome",
                    url="https://youtube.com/watch?v=tutorial123",
                    title="Python Tutorial",
                    timestamp=now - timedelta(minutes=30),
                ),
                BrowserActivity(
                    user_id=user_id,
                    browser="Chrome",
                    url="https://github.com/project",
                    title="GitHub Project",
                    timestamp=now - timedelta(minutes=10),
                ),
            ])
            db.commit()

            # 4. Test GET /dashboard/timeline
            print("\n[1] Testing get_dashboard_timeline(time_range='7d')...")
            timeline_res = get_dashboard_timeline(time_range="7d", current_user=user, db=db)
            print(f"    - Total Hours: {timeline_res.total_hours} hrs")
            print(f"    - Formatted: {timeline_res.total_duration_formatted}")
            print(f"    - Items count: {len(timeline_res.items)}")

            assert len(timeline_res.items) == 7, f"Expected 7 daily items, got {len(timeline_res.items)}"
            assert timeline_res.total_hours == 13.0, f"Expected 13.0 hrs, got {timeline_res.total_hours}"
            print("    ✓ Timeline API returns correct 7-day trend series")

            # 5. Test GET /dashboard/browser-history
            print("\n[2] Testing get_dashboard_browser_history(range='7d', limit=10)...")
            history_res = get_dashboard_browser_history(range="7d", limit=10, current_user=user, db=db)
            print(f"    - Total Count: {history_res.total_count}")
            for h in history_res.items:
                print(f"      • {h.domain:15} | {h.time_formatted:5} | {h.url}")

            assert history_res.total_count == 3, f"Expected 3 history items, got {history_res.total_count}"
            domains = [h.domain for h in history_res.items]
            assert "github.com" in domains
            assert "youtube.com" in domains
            assert "google.com" in domains
            print("    ✓ Browser History API returns chronological URL items with time_formatted")

            print("\n" + "=" * 65)
            print("ALL PHASE 5 BACKEND TESTS PASSED SUCCESSFULLY! ✓")
            print("=" * 65)

        finally:
            # Cleanup test user
            db.delete(user)
            db.commit()


if __name__ == "__main__":
    run_verification()
