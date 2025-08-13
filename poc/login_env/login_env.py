import os
from typing import Optional

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # optional in PoC


def verify_credentials(input_username: str, input_password: str, env_file_path: Optional[str] = None) -> bool:
    """
    Verify credentials by comparing against environment variables.
    If env_file_path is provided and python-dotenv is available, load .env from that path.
    Expected variables: LOGIN_USERNAME, LOGIN_PASSWORD
    """
    if env_file_path and load_dotenv is not None:
        load_dotenv(env_file_path)

    expected_username = os.getenv("LOGIN_USERNAME", "")
    expected_password = os.getenv("LOGIN_PASSWORD", "")

    return input_username == expected_username and input_password == expected_password


if __name__ == "__main__":
    # Simple manual check (set env first):
    # export LOGIN_USERNAME=demo_user; export LOGIN_PASSWORD=demo_pass
    print(verify_credentials("demo_user", "demo_pass"))


