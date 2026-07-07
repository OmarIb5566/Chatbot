import argparse
import getpass
import sys

from app import auth


def cmd_add_user(args: argparse.Namespace) -> None:
    if auth.user_exists(args.username):
        print(f"User '{args.username}' already exists.", file=sys.stderr)
        sys.exit(1)
    password = getpass.getpass("Password: ")
    if not password:
        print("Password cannot be empty.", file=sys.stderr)
        sys.exit(1)
    if password != getpass.getpass("Confirm password: "):
        print("Passwords do not match.", file=sys.stderr)
        sys.exit(1)
    auth.create_user(args.username, password)
    print(f"Created user '{args.username}'.")


def cmd_list_users(args: argparse.Namespace) -> None:
    users = auth.list_users()
    if not users:
        print("No users yet.")
        return
    for username in users:
        print(username)


def cmd_remove_user(args: argparse.Namespace) -> None:
    if auth.delete_user(args.username):
        print(f"Removed user '{args.username}'.")
    else:
        print(f"No such user '{args.username}'.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    auth.init_db()
    parser = argparse.ArgumentParser(prog="app.manage", description="Manage chatbot user accounts")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add-user", help="Create a new user account")
    p_add.add_argument("username")
    p_add.set_defaults(func=cmd_add_user)

    p_list = sub.add_parser("list-users", help="List all user accounts")
    p_list.set_defaults(func=cmd_list_users)

    p_remove = sub.add_parser("remove-user", help="Delete a user account")
    p_remove.add_argument("username")
    p_remove.set_defaults(func=cmd_remove_user)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
