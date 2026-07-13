"""
Password Hasher
bcrypt-based password hashing and verification.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Malformed hash or invalid input — treat as non-match rather than crash
        return False
