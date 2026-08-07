"""
auth.py
Simple login/signup system. Passwords are hashed (never stored as plain text)
using Python's built-in hashlib with a per-user salt. This is fine for a
student project, but note it is not a full production-grade auth system
(no rate limiting, no password reset flow, etc.).
"""

import hashlib
import os
import binascii


def _hash_password(password, salt=None):
    """Returns (salt_hex, hash_hex) for the given password."""
    if salt is None:
        salt = os.urandom(16)
    elif isinstance(salt, str):
        salt = binascii.unhexlify(salt)

    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(salt).decode(), binascii.hexlify(pwd_hash).decode()


def create_user(data, username, password):
    """
    Adds a new user to data['users']. Returns (success: bool, message: str).
    """
    username = username.strip()
    if not username or not password:
        return False, "Username and password cannot be empty."

    if username in data["users"]:
        return False, "This username already exists."

    salt_hex, hash_hex = _hash_password(password)
    data["users"][username] = {
        "salt": salt_hex,
        "password_hash": hash_hex,
        "completed_lessons": [],
        "quiz_scores": {},
        "xp": 0,
        "streak": 0,
        "last_activity_date": None,
    }
    return True, "Account created successfully."


def verify_login(data, username, password):
    """Returns (success: bool, message: str)."""
    username = username.strip()
    user = data["users"].get(username)
    if not user:
        return False, "No account found with this username."

    _, hash_hex = _hash_password(password, salt=user["salt"])
    if hash_hex == user["password_hash"]:
        return True, "Login successful."
    return False, "Incorrect password."
