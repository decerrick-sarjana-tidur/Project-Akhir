"""Firebase Authentication and Firestore REST API for MyVault."""
from __future__ import annotations

import json
import os
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        here = Path(__file__).resolve().parent
        for directory in (here, here.parent):
            env_file = directory / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                break
    except ImportError:
        pass


_load_env()

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
FIREBASE_OAUTH_REDIRECT_URL = os.environ.get(
    "FIREBASE_OAUTH_REDIRECT_URL", "http://localhost:8550/oauth_callback"
)

_id_token = None
_user_id = None
_API = "https://identitytoolkit.googleapis.com/v1"
_FIRESTORE = "https://firestore.googleapis.com/v1"


def is_configured() -> bool:
    return bool(FIREBASE_API_KEY and FIREBASE_PROJECT_ID)


def google_is_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def _json_request(url: str, payload=None, token=None, method="POST") -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read()
    except HTTPError as exc:
        body = exc.read()
        try:
            details = json.loads(body).get("error", {}).get("message", str(exc))
        except (ValueError, AttributeError):
            details = str(exc)
        raise RuntimeError(details) from exc
    except URLError as exc:
        raise RuntimeError(f"Tidak dapat terhubung ke Firebase: {exc.reason}") from exc
    return json.loads(body) if body else {}


def _auth_url(endpoint: str) -> str:
    if not is_configured():
        raise RuntimeError("Isi FIREBASE_API_KEY dan FIREBASE_PROJECT_ID di file .env.")
    return f"{_API}/{endpoint}?{urlencode({'key': FIREBASE_API_KEY})}"


def _auth_result(data: dict) -> dict:
    global _id_token, _user_id
    _id_token = data.get("idToken")
    _user_id = data.get("localId") or data.get("user_id")
    session = None
    user = None
    if _id_token and data.get("refreshToken") and _user_id:
        session = SimpleNamespace(
            access_token=_id_token,
            refresh_token=data["refreshToken"],
        )
        user = SimpleNamespace(id=_user_id, email=data.get("email", ""))
        user.display_name = data.get("displayName", "")
    return {"user": user, "session": session, "error": None}


def sign_up(email: str, password: str, display_name: str = "") -> dict:
    try:
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
        if display_name.strip():
            payload["displayName"] = display_name.strip()
        data = _json_request(_auth_url("accounts:signUp"), payload)
        return _auth_result(data)
    except Exception as exc:
        return {"user": None, "session": None, "error": str(exc)}


def sign_in(email: str, password: str) -> dict:
    try:
        data = _json_request(_auth_url("accounts:signInWithPassword"), {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        })
        return _auth_result(data)
    except Exception as exc:
        return {"user": None, "session": None, "error": str(exc)}


def sign_in_with_google(google_access_token: str) -> dict:
    try:
        post_body = urlencode({
            "access_token": google_access_token,
            "providerId": "google.com",
        })
        data = _json_request(_auth_url("accounts:signInWithIdp"), {
            "postBody": post_body,
            "requestUri": FIREBASE_OAUTH_REDIRECT_URL,
            "returnIdpCredential": True,
            "returnSecureToken": True,
        })
        return _auth_result(data)
    except Exception as exc:
        return {"user": None, "session": None, "error": str(exc)}


def sign_in_with_google_id_token(google_id_token: str) -> dict:
    try:
        post_body = urlencode({
            "id_token": google_id_token,
            "providerId": "google.com",
        })
        data = _json_request(_auth_url("accounts:signInWithIdp"), {
            "postBody": post_body,
            "requestUri": "http://localhost",
            "returnIdpCredential": True,
            "returnSecureToken": True,
        })
        return _auth_result(data)
    except Exception as exc:
        return {"user": None, "session": None, "error": str(exc)}


def sign_out() -> None:
    global _id_token, _user_id
    _id_token = None
    _user_id = None


def restore_session(access_token: str, refresh_token: str) -> dict:
    try:
        if not is_configured():
            raise RuntimeError("Isi konfigurasi Firebase di file .env.")
        url = f"https://securetoken.googleapis.com/v1/token?{urlencode({'key': FIREBASE_API_KEY})}"
        request = Request(
            url,
            data=urlencode({
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            tokens = json.loads(response.read())
        user_data = _json_request(_auth_url("accounts:lookup"), {
            "idToken": tokens["id_token"],
        })["users"][0]
        normalized = {
            "idToken": tokens["id_token"],
            "refreshToken": tokens["refresh_token"],
            "localId": tokens["user_id"],
            "email": user_data.get("email", ""),
            "displayName": user_data.get("displayName", ""),
        }
        return _auth_result(normalized)
    except Exception as exc:
        return {"user": None, "session": None, "error": str(exc)}


def _document_path(user_id: str, vault_id: str) -> str:
    return f"projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/flet_users/{user_id}/vaults/{vault_id}"


def _encode_value(value):
    if value is None:
        return {"nullValue": "NULL_VALUE"}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, list):
        return {"arrayValue": {"values": [_encode_value(item) for item in value]}}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {key: _encode_value(item) for key, item in value.items()}}}
    raise TypeError(f"Tipe data Firestore tidak didukung: {type(value).__name__}")


def _decode_value(value):
    if "stringValue" in value:
        return value["stringValue"]
    if "integerValue" in value:
        return int(value["integerValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "booleanValue" in value:
        return value["booleanValue"]
    if "nullValue" in value:
        return None
    if "arrayValue" in value:
        return [_decode_value(item) for item in value["arrayValue"].get("values", [])]
    if "mapValue" in value:
        return {
            key: _decode_value(item)
            for key, item in value["mapValue"].get("fields", {}).items()
        }
    return None


def _firestore_request(path: str, payload=None, method="GET", query=()):
    if not _id_token:
        raise RuntimeError("Sesi Firebase tidak aktif. Silakan login kembali.")
    url = f"{_FIRESTORE}/{path}"
    if query:
        url = f"{url}?{urlencode(query)}"
    return _json_request(url, payload, token=_id_token, method=method)


def load_vaults(user_id: str) -> list:
    path = f"projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/flet_users/{user_id}/vaults"
    response = _firestore_request(path)
    result = []
    for document in response.get("documents", []):
        values = {
            key: _decode_value(value)
            for key, value in document.get("fields", {}).items()
        }
        vault_id = document["name"].rsplit("/", 1)[-1]
        result.append({
            "id": vault_id,
            "name": values.get("name", ""),
            "category": values.get("category", "Lainnya"),
            "target": float(values.get("target", 0)),
            "current": float(values.get("current", 0)),
            "deadline": str(values.get("deadline", "")),
            "priority": bool(values.get("priority", False)),
            "itemLink": values.get("itemLink", ""),
            "history": values.get("history", []),
        })
    return result


def _patch_document(user_id: str, vault_id: str, fields: dict) -> None:
    path = _document_path(user_id, vault_id)
    query = [("updateMask.fieldPaths", field) for field in fields]
    _firestore_request(
        path,
        {"fields": {key: _encode_value(value) for key, value in fields.items()}},
        method="PATCH",
        query=query,
    )


def upsert_vault(vault: dict, user_id: str) -> None:
    fields = {
        "name": vault["name"],
        "category": vault["category"],
        "target": vault["target"],
        "current": vault["current"],
        "deadline": vault["deadline"],
        "priority": vault["priority"],
        "itemLink": vault.get("itemLink", ""),
        "history": vault.get("history", []),
    }
    _patch_document(user_id, str(vault["id"]), fields)


def update_vault_current(vault_id: str, new_current: float) -> None:
    if _user_id:
        _patch_document(_user_id, vault_id, {"current": new_current})


def update_vault_priority(vault_id: str, priority: bool) -> None:
    if _user_id:
        _patch_document(_user_id, vault_id, {"priority": priority})


def add_transaction(vault_id: str, user_id: str, tx: dict) -> None:
    path = _document_path(user_id, vault_id)
    value = _encode_value({
        "id": tx["id"],
        "type": tx["type"],
        "amount": tx["amount"],
        "date": tx["date"],
    })
    commit_path = f"projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents:commit"
    _firestore_request(commit_path, {
        "writes": [{
            "transform": {
                "document": path,
                "fieldTransforms": [{
                    "fieldPath": "history",
                    "appendMissingElements": {"values": [value]},
                }],
            },
        }],
    }, method="POST")


def delete_vault(vault_id: str) -> None:
    if _user_id:
        _firestore_request(_document_path(_user_id, vault_id), method="DELETE")
