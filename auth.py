"""Simple authentication for the online version.

Passwords are stored as PBKDF2-SHA256 hashes (salt$hash) in the database.
Two roles are used: "gerant" (full access) and "reception" (no team admin).
Use manage_users.py to create/update accounts.
"""

import hashlib
import hmac
import os

_ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS).hex()
    return f"{salt}${h}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
    except (ValueError, AttributeError):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS).hex()
    return hmac.compare_digest(candidate, h)


def authenticate(users: dict, username: str, password: str) -> dict | None:
    """Return {'username', 'role'} if credentials match, else None."""
    rec = users.get(username)
    if not rec:
        return None
    if verify_password(password, rec.get("hash", "")):
        return {"username": username, "role": rec.get("role", "reception")}
    return None
