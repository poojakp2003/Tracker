import getpass
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


email = input("Email: ")
old = getpass.getpass("Current password: ")
new = getpass.getpass("New password (min 8 characters): ")
confirm = getpass.getpass("Repeat new password: ")

if new != confirm:
    raise SystemExit("New passwords do not match.")

status, tokens = call("POST", "/auth/login", {"email": email, "password": old})
if status != 200:
    raise SystemExit(f"Login failed ({status}). Check the email and current password.")

status, body = call(
    "POST",
    "/auth/change-password",
    {"current_password": old, "new_password": new},
    token=tokens["access_token"],
)
print(status, body.get("message") or body.get("detail") or body)