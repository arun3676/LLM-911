import os
from pathlib import Path

from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "data" / ".env"


def create_daytona_sandbox(api_key: str | None = None):
    """Provision a Daytona sandbox using the SDK and return the sandbox object."""
    load_dotenv(dotenv_path=ENV_PATH, override=False)

    resolved_api_key = api_key or os.getenv("DAYTONA_API_KEY")
    if not resolved_api_key:
        raise RuntimeError(
            "DAYTONA_API_KEY is not set. Add it to data/.env or your environment."
        )

    config = DaytonaConfig(api_key=resolved_api_key)
    daytona = Daytona(config)
    return daytona.create()


def main() -> None:
    """CLI entry point that provisions a sandbox and prints its identifier."""
    sandbox = create_daytona_sandbox()
    print(f"Sandbox created: {sandbox.id}")
    print("View your sandboxes in the dashboard:")
    print("https://app.daytona.io/dashboard/sandboxes")


if __name__ == "__main__":
    main()
