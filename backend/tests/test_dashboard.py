"""Tests for Phase 3: Dashboard APIs and Date Range Filtering."""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.app_usage import AppUsage
from app.models.browser_activity import BrowserActivity
from app.models.user import User
from app.models.youtube_activity import YouTubeActivity


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def test_user_and_headers(client):
    test_email = f"dash_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "DashboardPassword123!"

    signup_res = client.post("/auth/signup", json={"email": test_email, "password": test_password})
    assert signup_res.status_code == 201
    user_id = signup_res.json()["id"]

    login_res = client.post("/auth/login", json={"email": test_email, "password": test_password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Populate test data
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        # App usage: Chrome today (2 hours = 7200s), VS Code 2 days ago (3 hours = 10800s), Slack 15 days ago (1 hour = 3600s)
        app1 = AppUsage(
            user_id=user_id,
            app_name="Chrome",
            window_title="Google Search",
            start_time=now - timedelta(hours=2),
            end_time=now,
            duration_seconds=7200,
        )
        app2 = AppUsage(
            user_id=user_id,
            app_name="VS Code",
            window_title="main.py - project",
            start_time=now - timedelta(days=2, hours=3),
            end_time=now - timedelta(days=2),
            duration_seconds=10800,
        )
        app3 = AppUsage(
            user_id=user_id,
            app_name="Slack",
            window_title="#general",
            start_time=now - timedelta(days=15, hours=1),
            end_time=now - timedelta(days=15),
            duration_seconds=3600,
        )

        # Browser activity: google.com, youtube.com, github.com
        b1 = BrowserActivity(
            user_id=user_id,
            browser="Chrome",
            url="https://www.google.com/search?q=fastapi",
            title="Google Search",
            timestamp=now - timedelta(hours=1),
        )
        b2 = BrowserActivity(
            user_id=user_id,
            browser="Chrome",
            url="https://youtube.com/watch?v=1",
            title="YouTube",
            timestamp=now - timedelta(days=1),
        )
        b3 = BrowserActivity(
            user_id=user_id,
            browser="Chrome",
            url="https://github.com/fastapi/fastapi",
            title="GitHub",
            timestamp=now - timedelta(days=3),
        )

        # YouTube activity
        y1 = YouTubeActivity(
            user_id=user_id,
            video_id="py101",
            video_title="Python Tutorial",
            url="https://youtube.com/watch?v=py101",
            watched_time_seconds=1800,
            timestamp=now - timedelta(hours=3),
        )
        y2 = YouTubeActivity(
            user_id=user_id,
            video_id="react202",
            video_title="React Tutorial",
            url="https://youtube.com/watch?v=react202",
            watched_time_seconds=2400,
            timestamp=now - timedelta(days=1),
        )
        y3 = YouTubeActivity(
            user_id=user_id,
            video_id="fastapi303",
            video_title="FastAPI Tutorial",
            url="https://youtube.com/watch?v=fastapi303",
            watched_time_seconds=1200,
            timestamp=now - timedelta(days=2),
        )

        db.add_all([app1, app2, app3, b1, b2, b3, y1, y2, y3])
        db.commit()

    yield {"headers": headers, "user_id": user_id}

    # Teardown
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user:
            db.delete(user)
            db.commit()


def test_unauthorized_dashboard_access(client):
    """Ensure all dashboard endpoints reject unauthenticated requests with 401."""
    assert client.get("/dashboard/summary").status_code == 401
    assert client.get("/dashboard/apps").status_code == 401
    assert client.get("/dashboard/browser").status_code == 401
    assert client.get("/dashboard/youtube").status_code == 401


def test_dashboard_summary(client, test_user_and_headers):
    """Test /dashboard/summary aggregate metrics."""
    headers = test_user_and_headers["headers"]
    res = client.get("/dashboard/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["today_seconds"] == 7200
    assert "2 hrs" in data["today_formatted"]
    assert data["week_seconds"] == 18000  # 7200 + 10800
    assert "5 hrs" in data["week_formatted"]
    assert data["month_seconds"] == 21600  # 7200 + 10800 + 3600
    assert "6 hrs" in data["month_formatted"]

    assert data["total_app_sessions"] == 3
    assert data["total_browser_visits"] == 3
    assert data["total_videos_watched"] == 3


def test_dashboard_apps_with_range_filters(client, test_user_and_headers):
    """Test /dashboard/apps with 7d and 30d range filtering."""
    headers = test_user_and_headers["headers"]

    # 1. 7d range: should include VS Code (3h) and Chrome (2h), excluding Slack (15d ago)
    res_7d = client.get("/dashboard/apps?range=7d", headers=headers)
    assert res_7d.status_code == 200
    data_7d = res_7d.json()
    assert data_7d["range"] == "7d"
    assert data_7d["total_duration_seconds"] == 18000
    assert len(data_7d["items"]) == 2
    assert data_7d["items"][0]["app_name"] == "VS Code"
    assert data_7d["items"][0]["duration_seconds"] == 10800
    assert data_7d["items"][1]["app_name"] == "Chrome"
    assert data_7d["items"][1]["duration_seconds"] == 7200

    # 2. 30d range: should include Slack as well
    res_30d = client.get("/dashboard/apps?range=30d", headers=headers)
    assert res_30d.status_code == 200
    data_30d = res_30d.json()
    assert data_30d["total_duration_seconds"] == 21600
    assert len(data_30d["items"]) == 3
    app_names = [item["app_name"] for item in data_30d["items"]]
    assert app_names == ["VS Code", "Chrome", "Slack"]

    # 3. Invalid range should return 400
    res_invalid = client.get("/dashboard/apps?range=999x", headers=headers)
    assert res_invalid.status_code == 400


def test_dashboard_browser(client, test_user_and_headers):
    """Test /dashboard/browser domain extraction and grouping."""
    headers = test_user_and_headers["headers"]
    res = client.get("/dashboard/browser?range=7d", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_visits"] == 3
    domains = [item["domain"] for item in data["items"]]
    assert "google.com" in domains
    assert "youtube.com" in domains
    assert "github.com" in domains


def test_dashboard_youtube(client, test_user_and_headers):
    """Test /dashboard/youtube ranking by watched time."""
    headers = test_user_and_headers["headers"]
    res = client.get("/dashboard/youtube?range=7d", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert len(data["items"]) == 3
    # Ordered descending by watched_seconds: React Tutorial (2400s) -> Python (1800s) -> FastAPI (1200s)
    titles = [item["video_title"] for item in data["items"]]
    assert titles == ["React Tutorial", "Python Tutorial", "FastAPI Tutorial"]
    assert data["items"][0]["watched_seconds"] == 2400
    assert data["items"][1]["watched_seconds"] == 1800
    assert data["items"][2]["watched_seconds"] == 1200


def test_user_isolation(client):
    """Ensure a different user only sees their own dashboard statistics."""
    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={"email": other_email, "password": "Password123!"})
    login_res = client.post("/auth/login", json={"email": other_email, "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    summary_res = client.get("/dashboard/summary", headers=headers)
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert data["today_seconds"] == 0
    assert data["week_seconds"] == 0
    assert data["total_app_sessions"] == 0

    apps_res = client.get("/dashboard/apps", headers=headers)
    assert apps_res.status_code == 200
    assert apps_res.json()["items"] == []
