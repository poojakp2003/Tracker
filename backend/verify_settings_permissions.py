"""Verification script for Tracking Settings and /permissions endpoints.

Flow tested:
1. React GET /permissions -> FastAPI -> Database (PostgreSQL)
2. React PUT /permissions -> FastAPI -> PostgreSQL
3. Backend gating: verify 403 Forbidden when tracking is disabled in user settings.
"""

from datetime import datetime, timezone
import uuid
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.user import User


def main() -> None:
    """Verify permissions GET and PUT API flows and backend gating."""
    print("==================================================")
    print("VERIFYING TRACKING SETTINGS & PERMISSIONS FLOW")
    print("==================================================")

    client = TestClient(app)

    # 1. Setup temporary test user
    test_email = f"settings_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"

    print(f"\n[Step 1] Creating test user: {test_email}...")
    signup_res = client.post("/auth/signup", json={"email": test_email, "password": test_password})
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"
    user_id = signup_res.json()["id"]

    login_res = client.post("/auth/login", json={"email": test_email, "password": test_password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ User authenticated with JWT")

    try:
        # 2. React -> GET /permissions -> FastAPI -> PostgreSQL
        print("\n[Step 2] Testing GET /permissions (Initial Settings Page Load)...")
        get_res = client.get("/permissions", headers=headers)
        assert get_res.status_code == 200, f"GET /permissions failed: {get_res.text}"
        initial_perms = get_res.json()
        print(f"  Current Permissions: {initial_perms}")
        assert initial_perms["app_tracking"] is True, "Expected app_tracking to default to True"
        assert initial_perms["browser_tracking"] is True, "Expected browser_tracking to default to True"
        assert initial_perms["youtube_tracking"] is False, "Expected youtube_tracking to default to False"
        print("✓ Default permissions retrieved from database: App [ON], Browser [ON], YouTube [OFF]")

        # 3. React -> PUT /permissions (User switches Browser Tracking OFF)
        print("\n[Step 3] Testing PUT /permissions (User switches Browser Tracking OFF)...")
        put_browser_res = client.put("/permissions", headers=headers, json={"browser_tracking": False})
        assert put_browser_res.status_code == 200, f"PUT /permissions failed: {put_browser_res.text}"
        updated_perms = put_browser_res.json()
        print(f"  Updated Permissions: {updated_perms}")
        assert updated_perms["browser_tracking"] is False, "Expected browser_tracking to be False"
        print("✓ Browser Tracking set to [ OFF ] in PostgreSQL")

        # 4. Verify backend knows browser tracking is disabled
        print("\n[Step 4] Verifying Backend Rejects Browser Tracking (403 Forbidden)...")
        browser_payload = {
            "browser": "Google Chrome",
            "url": "https://news.ycombinator.com",
            "title": "Hacker News",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        track_attempt = client.post("/track/browser-activity", headers=headers, json=browser_payload)
        assert track_attempt.status_code == 403, f"Expected 403, got {track_attempt.status_code}: {track_attempt.text}"
        print("✓ Backend successfully blocked browser activity tracking with HTTP 403 Forbidden")

        # 5. User switches YouTube Tracking ON
        print("\n[Step 5] Testing PUT /permissions (User switches YouTube Tracking ON)...")
        put_yt_res = client.put("/permissions", headers=headers, json={"youtube_tracking": True})
        assert put_yt_res.status_code == 200
        assert put_yt_res.json()["youtube_tracking"] is True
        print("✓ YouTube Tracking set to [ ON ] in PostgreSQL")

        # 6. Verify YouTube tracking is now permitted
        yt_payload = {
            "video_id": "dQw4w9WgXcQ",
            "video_title": "Rick Astley - Never Gonna Give You Up",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "watched_time_seconds": 120,
        }
        yt_track_attempt = client.post("/track/youtube-activity", headers=headers, json=yt_payload)
        assert yt_track_attempt.status_code == 201, f"Expected 201, got {yt_track_attempt.status_code}: {yt_track_attempt.text}"
        print("✓ YouTube activity tracking accepted with HTTP 201 Created")

        # 7. Also verify backward-compatible /track/permissions endpoint
        track_perm_res = client.get("/track/permissions", headers=headers)
        assert track_perm_res.status_code == 200
        assert track_perm_res.json()["browser_tracking"] is False
        assert track_perm_res.json()["youtube_tracking"] is True
        print("✓ Backward-compatibility endpoint GET /track/permissions verified")

        print("\n==================================================")
        print("ALL PERMISSIONS & SETTINGS TESTS PASSED SUCCESSFULLY!")
        print("==================================================")

    finally:
        # Teardown
        with SessionLocal() as db:
            user = db.get(User, user_id)
            if user:
                db.delete(user)
                db.commit()
        print("✓ Test user cleanup completed")


if __name__ == "__main__":
    main()
