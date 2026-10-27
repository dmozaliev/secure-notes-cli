import getpass
import os
import sys

import auth
from notes import Note, NotesVault


def clear_screen() -> None:
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def prompt_password(prompt: str = "Password: ") -> str:
    """Reads password with '*' masking on Windows terminals (or getpass elsewhere)."""
    if not sys.stdin.isatty():
        return input(prompt)

    if os.name == "nt":
        import msvcrt

        sys.stdout.write(prompt)
        sys.stdout.flush()
        chars: list[str] = []
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                print()
                return "".join(chars)
            if ch == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
            if ch == "\x08":  # Backspace
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch in ("\x00", "\xe0"):  # Arrow / function keys prefix
                msvcrt.getwch()
            else:
                chars.append(ch)
                sys.stdout.write("*")
                sys.stdout.flush()

    return getpass.getpass(prompt)


def print_header(title: str) -> None:
    print("=" * 56)
    print(title.center(56))
    print("=" * 56)


def print_notes_summary(notes_list: list[Note]) -> None:
    if not notes_list:
        print("\nNo notes found.")
        return

    print(f"\n{'ID':<5} | {'Created At':<17} | {'Title'}")
    print("-" * 56)
    for note in notes_list:
        print(f"{note.id:<5} | {note.created_at:<17} | {note.title}")


def login_screen() -> str | None:
    while True:
        clear_screen()
        print_header("SECURE NOTES VAULT - LOGIN")
        print("1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("\nSelect an option (1-3): ").strip()

        if choice == "1":
            username = input("Username: ").strip()
            password = prompt_password("Password: ")
            if auth.login_user(username, password):
                return username
            input("\nInvalid username or password. Press Enter to try again...")

        elif choice == "2":
            username = input("New Username (min 3 chars): ").strip()
            password = prompt_password("New Password (min 6 chars): ")
            ok, message = auth.register_user(username, password)
            input(f"\n{message} Press Enter to continue...")

        elif choice == "3":
            return None


def vault_app(user: str) -> None:
    vault = NotesVault()

    while True:
        clear_screen()
        print_header(f"SECURE VAULT - Logged in as: {user}")
        print("1. Create new note")
        print("2. List all my notes")
        print("3. Read note by ID")
        print("4. Search my notes")
        print("5. Delete note by ID")
        print("6. Logout")

        choice = input("\nChoose (1-6): ").strip()

        if choice == "6":
            break

        if choice == "1":
            title = input("Note title: ")
            content = input("Note content: ")
            try:
                note_id = vault.create_note(user, title, content)
                print(f"\nSaved note #{note_id}.")
            except ValueError as err:
                print(f"\nError: {err}")
            input("\nPress Enter to continue...")

        elif choice == "2":
            print_notes_summary(vault.list_notes(user))
            input("\nPress Enter to continue...")

        elif choice == "3":
            try:
                note_id = int(input("Enter Note ID: "))
                note = vault.get_note(user, note_id)
                if note:
                    print(f"\n[{note.id}] {note.title} ({note.created_at})")
                    print("-" * 56)
                    print(note.content)
                else:
                    print("\nNote not found.")
            except ValueError:
                print("\nError: Please enter a numeric ID.")
            input("\nPress Enter to continue...")

        elif choice == "4":
            keyword = input("Search keyword: ")
            print_notes_summary(vault.search_notes(user, keyword))
            input("\nPress Enter to continue...")

        elif choice == "5":
            try:
                note_id = int(input("Enter Note ID to delete: "))
                if vault.delete_note(user, note_id):
                    print(f"\nNote #{note_id} deleted.")
                else:
                    print("\nNote not found.")
            except ValueError:
                print("\nError: Please enter a numeric ID.")
            input("\nPress Enter to continue...")


def main() -> None:
    while True:
        try:
            current_user = login_screen()
            if current_user is None:
                print("\nGood bye!")
                break
            vault_app(current_user)
        except (KeyboardInterrupt, EOFError):
            print("\nGood bye!")
            break


if __name__ == "__main__":
    main()
