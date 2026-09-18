"""Test script for Dashboard Apps API with fake data:
- Chrome:  2 hours
- VS Code: 3 hours
- Slack:   1 hour

Calls: GET /dashboard/apps?range=7d
"""

from datetime import datetime, timedelta, timezone
import json
import sys
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.app_usage import AppUsage
from app.models.user import User


def run_test():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 60)
    print("Testing GET /dashboard/apps?range=7d with Fake Data")
    print("=" * 60)

    client = TestClient(app)

    # 1. Create temporary test user
    timestamp_id = int(datetime.now(timezone.utc).timestamp())
    email = f"test_apps_{timestamp_id}@example.com"
    password = "TestPassword123!"

    signup_res = client.post("/auth/signup", json={"email": email, "password": password})
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.text}"
    user_id = signup_res.json()["id"]

    login_res = client.post("/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)

    # 2. Insert fake database data:
    #    Chrome  -> 2 hours (7200 seconds)
    #    VS Code -> 3 hours (10800 seconds)
    #    Slack   -> 1 hour  (3600 seconds)
    print("\n[1] Seeding database with fake usage records:")
    print("    - Chrome:  2 hours (7200 seconds)")
    print("    - VS Code: 3 hours (10800 seconds)")
    print("    - Slack:   1 hour  (3600 seconds)")

    with SessionLocal() as db:
        record_chrome = AppUsage(
            user_id=user_id,
            app_name="Chrome",
            window_title="Google Chrome - Work Tab",
            start_time=now - timedelta(hours=2),
            end_time=now,
            duration_seconds=7200,
        )
        record_vscode = AppUsage(
            user_id=user_id,
            app_name="VS Code",
            window_title="Visual Studio Code - tracker-backend",
            start_time=now - timedelta(days=1, hours=3),
            end_time=now - timedelta(days=1),
            duration_seconds=10800,
        )
        record_slack = AppUsage(
            user_id=user_id,
            app_name="Slack",
            window_title="Slack - #engineering",
            start_time=now - timedelta(days=2, hours=1),
            end_time=now - timedelta(days=2),
            duration_seconds=3600,
        )
        db.add_all([record_chrome, record_vscode, record_slack])
        db.commit()

    # 3. Call GET /dashboard/apps?range=7d
    print("\n[2] Calling GET /dashboard/apps?range=7d...")
    response = client.get("/dashboard/apps?range=7d", headers=headers)
    print(f"Status Code: {response.status_code}")

    assert response.status_code == 200, f"API call failed: {response.text}"
    data = response.json()

    print("\n[3] Raw API Response JSON:")
    print(json.dumps(data, indent=2))

    # 4. Verify assertions
    print("\n[4] Validating response correctness...")
    assert data["range"] == "7d", f"Expected range '7d', got {data['range']}"
    assert data["total_duration_seconds"] == 21600, f"Expected 21600s (6h), got {data['total_duration_seconds']}"
    assert "6 hrs" in data["total_duration_formatted"]
    assert len(data["items"]) == 3, f"Expected 3 app items, got {len(data['items'])}"

    items_by_name = {item["app_name"]: item for item in data["items"]}

    # VS Code -> 3 hours
    assert "VS Code" in items_by_name
    assert items_by_name["VS Code"]["duration_seconds"] == 10800
    assert "3 hrs" in items_by_name["VS Code"]["duration_formatted"]
    assert items_by_name["VS Code"]["percentage"] == 50.0
    print("    ✓ VS Code  → 3 hours (10,800s, 50.0%) verified")

    # Chrome -> 2 hours
    assert "Chrome" in items_by_name
    assert items_by_name["Chrome"]["duration_seconds"] == 7200
    assert "2 hrs" in items_by_name["Chrome"]["duration_formatted"]
    assert items_by_name["Chrome"]["percentage"] == 33.3
    print("    ✓ Chrome   → 2 hours (7,200s, 33.3%) verified")

    # Slack -> 1 hour
    assert "Slack" in items_by_name
    assert items_by_name["Slack"]["duration_seconds"] == 3600
    assert "1 hr" in items_by_name["Slack"]["duration_formatted"]
    assert items_by_name["Slack"]["percentage"] == 16.7
    print("    ✓ Slack    → 1 hour  (3,600s, 16.7%) verified")

    # Order check: ordered by duration descending (VS Code -> Chrome -> Slack)
    assert [item["app_name"] for item in data["items"]] == ["VS Code", "Chrome", "Slack"]
    print("    ✓ Ordering: Ranked descending by duration (VS Code -> Chrome -> Slack)")

    # 5. Cleanup test data
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user:
            db.delete(user)
            db.commit()
    print("\n[5] Cleaned up temporary test user and records.")

    print("\n" + "=" * 60)
    print("TEST PASSED! The Dashboard Apps API works correctly.")
    print("=" * 60)


if __name__ == "__main__":
    run_test()
