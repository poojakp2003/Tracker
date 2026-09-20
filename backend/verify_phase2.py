"""Verification script for Phase 2 Core Data Model & Tracking APIs."""

from datetime import datetime, timezone
import sys
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from alembic import command
from alembic.config import Config
from app.core.database import SessionLocal, engine
from app.main import app
from app.models.user import User


def main() -> None:
    """Execute end-to-end verification of Phase 2 tables, tracking, and permissions."""
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Phase 2 Verification ===")

    # 1. Run Alembic migration to head
    print("[1/6] Running Alembic migration to head...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migration applied successfully.")

    # 2. Verify tables exist in DB
    print("[2/6] Inspecting DB tables...")
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {"users", "permissions", "app_usage", "browser_activity", "youtube_activity"}
    missing = required_tables - existing_tables
    if missing:
        raise RuntimeError(f"Missing tables in database: {missing}")
    print(f"All required tables exist: {required_tables}")

    # 3. Test client & unauthorized protection
    client = TestClient(app)
    print("[3/6] Testing unauthorized protection on tracking endpoints...")
    resp = client.post("/track/app-usage", json={
        "app_name": "Chrome",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
    })
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.post("/track/browser-activity", json={
        "browser": "Chrome",
        "url": "https://google.com",
    })
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
    print("Unauthorized calls correctly returned 401.")

    # 4. Create / Login test user
    print("[4/6] Authenticating test user...")
    test_email = f"phase2_test_{int(datetime.now(timezone.utc).timestamp())}@example.com"
    test_password = "SecurePassword123!"

    signup_res = client.post("/auth/signup", json={"email": test_email, "password": test_password})
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"
    user_id = signup_res.json()["id"]

    login_res = client.post("/auth/login", json={"email": test_email, "password": test_password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"User created (id={user_id}) and token acquired.")

    # 5. Test Tracking endpoints
    print("[5/6] Testing tracking data submission...")
    # 5a. app-usage
    start_t = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    end_t = datetime(2026, 9, 18, 10, 30, 0, tzinfo=timezone.utc)
    app_res = client.post(
        "/track/app-usage",
        headers=headers,
        json={
            "app_name": "Chrome",
            "window_title": "Google Search - Tab 1",
            "start_time": start_t.isoformat(),
            "end_time": end_t.isoformat(),
        },
    )
    assert app_res.status_code == 201, f"App usage failed: {app_res.text}"
    app_data = app_res.json()
    assert app_data["app_name"] == "Chrome"
    assert app_data["duration_seconds"] == 1800, f"Expected 1800s, got {app_data['duration_seconds']}"
    print("POST /track/app-usage ✓ (duration auto-calculated: 1800s)")

    # 5b. browser-activity
    browser_res = client.post(
        "/track/browser-activity",
        headers=headers,
        json={
            "browser": "Chrome",
            "url": "https://google.com",
            "title": "Google",
            "timestamp": datetime(2026, 9, 18, 10, 20, 0, tzinfo=timezone.utc).isoformat(),
        },
    )
    assert browser_res.status_code == 201, f"Browser activity failed: {browser_res.text}"
    browser_data = browser_res.json()
    assert browser_data["url"] == "https://google.com"
    assert browser_data["browser"] == "Chrome"
    print("POST /track/browser-activity ✓")

    # 6. Test permissions and permission-gated tracking
    print("[6/6] Testing permissions toggling & gating...")
    # By default, youtube_tracking is False
    yt_blocked = client.post(
        "/track/youtube-activity",
        headers=headers,
        json={
            "video_id": "test_video_123",
            "video_title": "FastAPI Tutorial",
            "url": "https://youtube.com/watch?v=test_video_123",
            "watched_time_seconds": 120,
        },
    )
    assert yt_blocked.status_code == 403, f"Expected 403 for default disabled YouTube tracking, got {yt_blocked.status_code}"
    print("POST /track/youtube-activity blocked with 403 as expected.")

    # Enable youtube tracking via PUT /track/permissions
    perm_update = client.put(
        "/track/permissions",
        headers=headers,
        json={"youtube_tracking": True},
    )
    assert perm_update.status_code == 200
    assert perm_update.json()["youtube_tracking"] is True
    print("PUT /track/permissions enabled youtube_tracking ✓")

    # Now retry youtube-activity
    yt_allowed = client.post(
        "/track/youtube-activity",
        headers=headers,
        json={
            "video_id": "test_video_123",
            "video_title": "FastAPI Tutorial",
            "url": "https://youtube.com/watch?v=test_video_123",
            "watched_time_seconds": 120,
        },
    )
    assert yt_allowed.status_code == 201, f"Expected 201, got {yt_allowed.status_code}: {yt_allowed.text}"
    print("POST /track/youtube-activity allowed with 201 after enabling permission ✓")

    # Disable app_tracking and verify 403
    perm_disable_app = client.put(
        "/track/permissions",
        headers=headers,
        json={"app_tracking": False},
    )
    assert perm_disable_app.status_code == 200
    app_blocked = client.post(
        "/track/app-usage",
        headers=headers,
        json={
            "app_name": "VS Code",
            "start_time": start_t.isoformat(),
            "end_time": end_t.isoformat(),
        },
    )
    assert app_blocked.status_code == 403, f"Expected 403, got {app_blocked.status_code}"
    print("POST /track/app-usage blocked with 403 after disabling permission ✓")

    # Cleanup test user
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user:
            db.delete(user)
            db.commit()
    print("Cleaned up test user successfully.")

    print("\nALL PHASE 2 TESTS PASSED SUCCESSFULLY! ✓")


if __name__ == "__main__":
    main()
