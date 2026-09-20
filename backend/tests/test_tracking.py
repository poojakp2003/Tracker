from collections.abc import Generator
from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.user import User


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient instance for API tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def auth_headers(client: TestClient) -> Generator[dict[str, str], None, None]:
    """Create a temporary test user and yield Authorization headers."""
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"

    # Signup
    signup_res = client.post("/auth/signup", json={"email": test_email, "password": test_password})
    assert signup_res.status_code == 201
    user_id = signup_res.json()["id"]

    # Login
    login_res = client.post("/auth/login", json={"email": test_email, "password": test_password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    yield {"Authorization": f"Bearer {token}"}

    # Teardown
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user:
            db.delete(user)
            db.commit()


def test_unauthorized_tracking_rejected(client: TestClient) -> None:
    """Ensure unauthorized requests cannot post tracking data."""
    res_app = client.post("/track/app-usage", json={
        "app_name": "Chrome",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
    })
    assert res_app.status_code == 401

    res_browser = client.post("/track/browser-activity", json={
        "browser": "Chrome",
        "url": "https://google.com",
    })
    assert res_browser.status_code == 401


def test_track_app_usage(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test POST /track/app-usage with automatic duration computation."""
    start_time = datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 9, 18, 10, 30, 0, tzinfo=timezone.utc)

    payload = {
        "app_name": "Google Chrome",
        "window_title": "GitHub - Repository",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    response = client.post("/track/app-usage", headers=auth_headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["app_name"] == "Google Chrome"
    assert data["window_title"] == "GitHub - Repository"
    assert data["duration_seconds"] == 1800  # 30 mins


def test_track_browser_activity(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test POST /track/browser-activity from Chrome extension."""
    payload = {
        "browser": "Chrome",
        "url": "https://github.com",
        "title": "GitHub",
        "timestamp": datetime(2026, 9, 18, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
    }
    response = client.post("/track/browser-activity", headers=auth_headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["browser"] == "Chrome"
    assert data["url"] == "https://github.com"
    assert data["title"] == "GitHub"


def test_permissions_flow_and_gating(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test default permissions, toggling, and enforcement on tracking."""
    # 1. Fetch default permissions
    res_perm = client.get("/track/permissions", headers=auth_headers)
    assert res_perm.status_code == 200
    perms = res_perm.json()
    assert perms["app_tracking"] is True
    assert perms["browser_tracking"] is True
    assert perms["youtube_tracking"] is False

    # 2. YouTube tracking disabled by default -> 403
    res_yt_blocked = client.post("/track/youtube-activity", headers=auth_headers, json={
        "video_id": "dQw4w9WgXcQ",
        "video_title": "Music Video",
        "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "watched_time_seconds": 60,
    })
    assert res_yt_blocked.status_code == 403

    # 3. Enable YouTube tracking
    res_update = client.put("/track/permissions", headers=auth_headers, json={"youtube_tracking": True})
    assert res_update.status_code == 200
    assert res_update.json()["youtube_tracking"] is True

    # 4. Now YouTube tracking succeeds -> 201
    res_yt_success = client.post("/track/youtube-activity", headers=auth_headers, json={
        "video_id": "dQw4w9WgXcQ",
        "video_title": "Music Video",
        "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "watched_time_seconds": 60,
    })
    assert res_yt_success.status_code == 201
    assert res_yt_success.json()["video_id"] == "dQw4w9WgXcQ"
    assert res_yt_success.json()["watched_time_seconds"] == 60

    # 5. Disable app tracking -> 403 on app-usage
    client.put("/track/permissions", headers=auth_headers, json={"app_tracking": False})
    now = datetime.now(timezone.utc).isoformat()
    res_app_blocked = client.post("/track/app-usage", headers=auth_headers, json={
        "app_name": "VS Code",
        "start_time": now,
        "end_time": now,
    })
    assert res_app_blocked.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
