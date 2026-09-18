"""Verification script for Phase 3 Dashboard APIs and Date Range Filtering."""

from datetime import datetime, timedelta, timezone
import sys
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.app_usage import AppUsage
from app.models.browser_activity import BrowserActivity
from app.models.user import User
from app.models.youtube_activity import YouTubeActivity


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== Phase 3 Verification: Dashboard APIs & Date Range Filtering ===")

    client = TestClient(app)

    # 1. Test unauthorized access
    print("[1/5] Testing unauthorized access on /dashboard/*...")
    for endpoint in ["/dashboard/summary", "/dashboard/apps", "/dashboard/browser", "/dashboard/youtube"]:
        resp = client.get(endpoint)
        assert resp.status_code == 401, f"{endpoint} did not return 401: {resp.status_code}"
    print("All dashboard endpoints correctly reject unauthorized requests ✓")

    # 2. Setup test user and data
    print("[2/5] Creating test user and seeding time-stamped activity data...")
    test_email = f"phase3_{int(datetime.now(timezone.utc).timestamp())}@example.com"
    test_password = "DashboardPass123!"

    signup = client.post("/auth/signup", json={"email": test_email, "password": test_password})
    assert signup.status_code == 201
    user_id = signup.json()["id"]

    login = client.post("/auth/login", json={"email": test_email, "password": test_password})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        # Chrome: 2 hours today
        # VS Code: 3 hours 2 days ago
        # Slack: 1 hour 15 days ago
        db.add_all([
            AppUsage(
                user_id=user_id,
                app_name="Chrome",
                window_title="Google Search",
                start_time=now - timedelta(hours=2),
                end_time=now,
                duration_seconds=7200,
            ),
            AppUsage(
                user_id=user_id,
                app_name="VS Code",
                window_title="FastAPI Project",
                start_time=now - timedelta(days=2, hours=3),
                end_time=now - timedelta(days=2),
                duration_seconds=10800,
            ),
            AppUsage(
                user_id=user_id,
                app_name="Slack",
                window_title="#general",
                start_time=now - timedelta(days=15, hours=1),
                end_time=now - timedelta(days=15),
                duration_seconds=3600,
            ),
            BrowserActivity(
                user_id=user_id,
                browser="Chrome",
                url="https://google.com/search?q=fastapi",
                title="Google",
                timestamp=now - timedelta(hours=1),
            ),
            BrowserActivity(
                user_id=user_id,
                browser="Chrome",
                url="https://youtube.com/watch?v=abc",
                title="YouTube",
                timestamp=now - timedelta(days=1),
            ),
            BrowserActivity(
                user_id=user_id,
                browser="Chrome",
                url="https://github.com/fastapi/fastapi",
                title="GitHub",
                timestamp=now - timedelta(days=3),
            ),
            YouTubeActivity(
                user_id=user_id,
                video_id="py101",
                video_title="Python Tutorial",
                url="https://youtube.com/watch?v=py101",
                watched_time_seconds=1800,
                timestamp=now - timedelta(hours=2),
            ),
            YouTubeActivity(
                user_id=user_id,
                video_id="react202",
                video_title="React Tutorial",
                url="https://youtube.com/watch?v=react202",
                watched_time_seconds=2400,
                timestamp=now - timedelta(days=1),
            ),
            YouTubeActivity(
                user_id=user_id,
                video_id="fastapi303",
                video_title="FastAPI Tutorial",
                url="https://youtube.com/watch?v=fastapi303",
                watched_time_seconds=1200,
                timestamp=now - timedelta(days=2),
            ),
        ])
        db.commit()
    print("Seed data inserted successfully.")

    # 3. Test /dashboard/summary
    print("[3/5] Testing GET /dashboard/summary...")
    res_summary = client.get("/dashboard/summary", headers=headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()
    print(f"  Today: {summary['today_formatted']} ({summary['today_seconds']}s)")
    print(f"  Week:  {summary['week_formatted']} ({summary['week_seconds']}s)")
    print(f"  Month: {summary['month_formatted']} ({summary['month_seconds']}s)")
    assert summary["today_seconds"] == 7200
    assert summary["week_seconds"] == 18000
    assert summary["month_seconds"] == 21600
    assert summary["total_app_sessions"] == 3
    assert summary["total_browser_visits"] == 3
    assert summary["total_videos_watched"] == 3
    print("Summary metrics verified ✓")

    # 4. Test /dashboard/apps with range filters
    print("[4/5] Testing GET /dashboard/apps with range filters...")
    res_apps_7d = client.get("/dashboard/apps?range=7d", headers=headers)
    assert res_apps_7d.status_code == 200
    apps_7d = res_apps_7d.json()
    print(f"  7d Apps Total: {apps_7d['total_duration_formatted']}")
    for item in apps_7d["items"]:
        print(f"    - {item['app_name']}: {item['duration_formatted']} ({item['percentage']}%)")
    assert len(apps_7d["items"]) == 2  # VS Code, Chrome (Slack excluded)
    assert apps_7d["items"][0]["app_name"] == "VS Code"

    res_apps_30d = client.get("/dashboard/apps?range=30d", headers=headers)
    assert res_apps_30d.status_code == 200
    apps_30d = res_apps_30d.json()
    print(f"  30d Apps Total: {apps_30d['total_duration_formatted']}")
    for item in apps_30d["items"]:
        print(f"    - {item['app_name']}: {item['duration_formatted']} ({item['percentage']}%)")
    assert len(apps_30d["items"]) == 3  # VS Code, Chrome, Slack included
    print("Apps range filtering verified ✓")

    # 5. Test /dashboard/browser & /dashboard/youtube
    print("[5/5] Testing GET /dashboard/browser and /dashboard/youtube...")
    res_browser = client.get("/dashboard/browser?range=7d", headers=headers)
    assert res_browser.status_code == 200
    browser = res_browser.json()
    print(f"  Browser Visits Total: {browser['total_visits']}")
    for b in browser["items"]:
        print(f"    - {b['domain']}: {b['visit_count']} visits")
    domains = [b["domain"] for b in browser["items"]]
    assert "google.com" in domains and "youtube.com" in domains and "github.com" in domains

    res_yt = client.get("/dashboard/youtube?range=7d", headers=headers)
    assert res_yt.status_code == 200
    yt = res_yt.json()
    print(f"  YouTube Watched Total: {yt['total_watched_formatted']}")
    for y in yt["items"]:
        print(f"    - {y['video_title']}: {y['watched_formatted']}")
    assert yt["items"][0]["video_title"] == "React Tutorial"
    assert yt["items"][1]["video_title"] == "Python Tutorial"
    assert yt["items"][2]["video_title"] == "FastAPI Tutorial"
    print("Browser and YouTube activity verified ✓")

    # Cleanup
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user:
            db.delete(user)
            db.commit()
    print("Cleaned up test data.")

    print("\nALL PHASE 3 TESTS PASSED SUCCESSFULLY! ✓")


if __name__ == "__main__":
    main()
