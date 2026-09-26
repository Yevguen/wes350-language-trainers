# hash_generator.py
import sys
import getpass
from password import get_password_hash  # (argon2/bcrypt via password.py)


def main() -> None:
    # 1st arg = password (optional). If absent, ask securely.
    if len(sys.argv) > 1:
        plain = sys.argv[1]
    else:
        plain = getpass.getpass("Enter password to hash (input hidden): ")

    if not plain:
        print("Empty password; aborted.")
        sys.exit(1)

    print(get_password_hash(plain))


if __name__ == "__main__":
    main()
