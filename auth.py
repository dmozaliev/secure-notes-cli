import hashlib
import hmac
import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "vault.db"
PBKDF2_ITERATIONS = 100_000


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Initializes the SQLite database with 'users' and 'notes' tables."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                password_hash BLOB NOT NULL,
                salt BLOB NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (owner) REFERENCES users(username) ON DELETE CASCADE
            );
            """
        )
        conn.commit()


def hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a 16-byte random salt."""
    if salt is None:
        salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return pw_hash, salt


def register_user(
    username: str, password: str, db_path: str | Path = DEFAULT_DB_PATH
) -> tuple[bool, str]:
    """Registers a new user after validating username and password length."""
    cleaned_user = username.strip()
    if len(cleaned_user) < 3:
        return False, "Username must be at least 3 characters long."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    init_db(db_path)
    pw_hash, salt = hash_password(password)

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (cleaned_user, pw_hash, salt),
            )
            conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."


def login_user(
    username: str, password: str, db_path: str | Path = DEFAULT_DB_PATH
) -> bool:
    """Verifies user credentials using constant-time hash comparison."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT password_hash, salt FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        )
        result = cursor.fetchone()

    if not result:
        return False

    stored_hash, salt = result
    pw_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(pw_hash, stored_hash)
