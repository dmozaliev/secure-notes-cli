from pathlib import Path

from auth import hash_password, login_user, register_user
from notes import NotesVault


def test_password_salting_is_unique() -> None:
    hash1, salt1 = hash_password("SecretPass123")
    hash2, salt2 = hash_password("SecretPass123")
    assert salt1 != salt2
    assert hash1 != hash2


def test_register_and_login(tmp_path: Path) -> None:
    db = tmp_path / "test_vault.db"
    ok, _ = register_user("daniil", "StrongPass99", db)
    assert ok is True

    # Duplicate registration should fail cleanly
    ok_dup, msg = register_user("Daniil", "AnotherPass12", db)
    assert ok_dup is False
    assert "exists" in msg

    assert login_user("daniil", "StrongPass99", db) is True
    assert login_user("daniil", "WrongPassword", db) is False
    assert login_user("unknown", "StrongPass99", db) is False


def test_notes_user_isolation(tmp_path: Path) -> None:
    db = tmp_path / "test_vault.db"
    register_user("alice", "AlicePass1", db)
    register_user("bob", "BobPass1", db)

    vault = NotesVault(db)
    alice_note_id = vault.create_note("alice", "Bewerbung Hilti", "Send CV in October")
    vault.create_note("bob", "Shopping List", "Milk and bread")

    # Alice sees only her note
    alice_notes = vault.list_notes("alice")
    assert len(alice_notes) == 1
    assert alice_notes[0].title == "Bewerbung Hilti"

    # Bob cannot read or delete Alice's note
    assert vault.get_note("bob", alice_note_id) is None
    assert vault.delete_note("bob", alice_note_id) is False

    # Alice can delete her own note
    assert vault.delete_note("alice", alice_note_id) is True
    assert vault.list_notes("alice") == []
