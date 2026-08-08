"""
auth.py
Login/signup system supporting login by username OR email, plus a
"Remember Me" session that expires after 30 days.

Passwords are hashed (never stored as plain text) using Python's built-in
hashlib with a per-user salt. This is fine for a student project, but note
it is not a full production-grade auth system (no rate limiting, no
password reset flow, etc.).
"""

import hashlib
import os
import binascii
import json
from datetime import datetime, timedelta

SESSION_DURATION_DAYS = 30


def _hash_password(password, salt=None):
    """Returns (salt_hex, hash_hex) for the given password."""
    if salt is None:
        salt = os.urandom(16)
    elif isinstance(salt, str):
        salt = binascii.unhexlify(salt)

    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(salt).decode(), binascii.hexlify(pwd_hash).decode()


def _find_username_by_email(data, email):
    """Looks up a username by matching stored email (case-insensitive)."""
    email = email.strip().lower()
    for uname, udata in data["users"].items():
        if udata.get("email", "").lower() == email:
            return uname
    return None


def create_user(data, username, password, email=""):
    """
    Adds a new user to data['users']. Email is optional but, if given,
    must be unique too (so it can be used to log in later).
    Returns (success: bool, message: str).
    """
    username = username.strip()
    email = email.strip()

    if not username or not password:
        return False, "Username and password cannot be empty."

    if username in data["users"]:
        return False, "This username already exists."

    if email and _find_username_by_email(data, email):
        return False, "An account with this email already exists."

    salt_hex, hash_hex = _hash_password(password)
    data["users"][username] = {
        "salt": salt_hex,
        "password_hash": hash_hex,
        "email": email,
        "completed_lessons": [],
        "quiz_scores": {},
        "xp": 0,
        "streak": 0,
        "last_activity_date": None,
    }
    return True, "Account created successfully."


def verify_login(data, identifier, password):
    """
    Logs in with either a username or an email address in `identifier`.
    Returns (success: bool, message: str, username: str or None).
    """
    identifier = identifier.strip()

    username = identifier if identifier in data["users"] else _find_username_by_email(data, identifier)
    if not username:
        return False, "No account found with this username or email.", None

    user = data["users"][username]
    _, hash_hex = _hash_password(password, salt=user["salt"])
    if hash_hex == user["password_hash"]:
        return True, "Login successful.", username
    return False, "Incorrect password.", None


# ---------------------------------------------------------------------------
# "Remember Me" session support — stores only the logged-in username (never
# the password) plus a timestamp, so the app can auto-login next time it's
# opened, but only within SESSION_DURATION_DAYS (30 days) of the last login.
# ---------------------------------------------------------------------------

SESSION_FILE = os.path.join(os.path.dirname(__file__), "session.json")


def save_session(username):
    """Remembers the logged-in user with today's timestamp."""
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "logged_in_user": username,
            "saved_at": datetime.now().isoformat(),
        }, f)


def load_session():
    """
    Returns the remembered username if a session exists AND is less than
    30 days old. Otherwise returns None (and clears an expired session).
    """
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            session = json.load(f)

        saved_at = datetime.fromisoformat(session["saved_at"])
        if datetime.now() - saved_at > timedelta(days=SESSION_DURATION_DAYS):
            clear_session()
            return None

        return session.get("logged_in_user")
    except (json.JSONDecodeError, OSError, KeyError, ValueError):
        return None


def clear_session():
    """Forgets the remembered user (called on logout)."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)