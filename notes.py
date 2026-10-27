import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from auth import DEFAULT_DB_PATH, init_db


@dataclass
class Note:
    """Represents a private user note stored in SQLite."""

    id: int
    owner: str
    title: str
    content: str
    created_at: str


class NotesVault:
    """Manages private notes scoped strictly to the authenticated user."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def create_note(self, owner: str, title: str, content: str) -> int:
        """Creates a new note for the given user and returns its note ID."""
        clean_title = title.strip()
        clean_content = content.strip()
        if not clean_title or not clean_content:
            raise ValueError("Title and content cannot be empty.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO notes (owner, title, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (owner.strip(), clean_title, clean_content, timestamp),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_notes(self, owner: str) -> list[Note]:
        """Returns all notes belonging to the specified user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, owner, title, content, created_at
                FROM notes
                WHERE owner = ? COLLATE NOCASE
                ORDER BY id DESC
                """,
                (owner.strip(),),
            )
            return [Note(*row) for row in cursor.fetchall()]

    def get_note(self, owner: str, note_id: int) -> Note | None:
        """Fetches a single note by ID only if it belongs to the user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, owner, title, content, created_at
                FROM notes
                WHERE id = ? AND owner = ? COLLATE NOCASE
                """,
                (note_id, owner.strip()),
            )
            row = cursor.fetchone()
            return Note(*row) if row else None

    def search_notes(self, owner: str, keyword: str) -> list[Note]:
        """Searches a user's own notes by title or content."""
        pattern = f"%{keyword.strip()}%"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, owner, title, content, created_at
                FROM notes
                WHERE owner = ? COLLATE NOCASE
                  AND (title LIKE ? OR content LIKE ?)
                ORDER BY id DESC
                """,
                (owner.strip(), pattern, pattern),
            )
            return [Note(*row) for row in cursor.fetchall()]

    def delete_note(self, owner: str, note_id: int) -> bool:
        """Deletes a note by ID if owned by the user. Returns True if deleted."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM notes WHERE id = ? AND owner = ? COLLATE NOCASE",
                (note_id, owner.strip()),
            )
            conn.commit()
            return cursor.rowcount > 0
