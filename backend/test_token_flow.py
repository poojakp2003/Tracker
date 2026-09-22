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
password = getpass.getpass("Password: ")

status, tokens = call("POST", "/auth/login", {"email": email, "password": password})
print("1. login                       ->", status, "(expect 200)")
if status != 200:
    raise SystemExit("Login failed - check email/password and that the server is running.")
access, refresh = tokens["access_token"], tokens["refresh_token"]

status, new = call("POST", "/auth/refresh", {"refresh_token": refresh})
print("2. refresh with refresh token  ->", status, "(expect 200)")

status, _ = call("POST", "/auth/refresh", {"refresh_token": access})
print("3. refresh with access token   ->", status, "(expect 401)")

status, body = call("GET", "/auth/me", token=refresh)
print("4. /auth/me with refresh token ->", status, "(expect 401)")

status, body = call("GET", "/auth/me", token=access)
print("5. /auth/me with access token  ->", status, "(expect 200)", body.get("email", ""))

status, body = call("GET", "/auth/me", token=new["access_token"])
print("6. /auth/me with new access    ->", status, "(expect 200)")