import os
from pathlib import Path

from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig, DaytonaError


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "data" / ".env"

# Default repo + target path used for LLM 911 sandboxes
DEFAULT_DAYTONA_REPOSITORY = "https://github.com/arun3676/LLM-911"
DEFAULT_DAYTONA_REPO_PATH = "workspace/LLM-911"


def create_daytona_sandbox(
    api_key: str | None = None,
    repository: str | None = None,
    repo_path: str | None = None,
):
    """Provision a Daytona sandbox using the SDK and return the sandbox object.

    The Daytona API key is read from ``DAYTONA_API_KEY`` (either OS env or
    ``data/.env``). The sandbox is created from the GitHub repository for this
    project by default, but can be overridden via the ``repository`` argument or
    the ``DAYTONA_REPOSITORY`` environment variable.
    """

    # Load environment variables from data/.env if present
    load_dotenv(dotenv_path=ENV_PATH, override=False)

    resolved_api_key = api_key or os.getenv("DAYTONA_API_KEY")
    if not resolved_api_key:
        raise RuntimeError(
            "DAYTONA_API_KEY is not set. Add it to data/.env or your environment."
        )

    # Prefer explicit argument, then env var, then project default
    resolved_repo = (
        repository
        or os.getenv("DAYTONA_REPOSITORY")
        or DEFAULT_DAYTONA_REPOSITORY
    )
    resolved_repo_path = (
        repo_path
        or os.getenv("DAYTONA_REPOSITORY_PATH")
        or DEFAULT_DAYTONA_REPO_PATH
    )

    config = DaytonaConfig(api_key=resolved_api_key)
    daytona = Daytona(config)

    sandbox = daytona.create()

    try:
        sandbox.git.clone(url=resolved_repo, path=resolved_repo_path)
    except DaytonaError as exc:
        # Allow already-cloned repos (e.g., reruns) to proceed, but raise for other issues
        if "already exists" not in str(exc).lower():
            raise RuntimeError(
                f"Failed to clone {resolved_repo} into sandbox: {exc}"
            ) from exc

    return sandbox


def main() -> None:
    """CLI entry point that provisions a sandbox and prints its identifier."""
    sandbox = create_daytona_sandbox()
    print(f"Sandbox created: {sandbox.id}")
    print("View your sandboxes in the dashboard:")
    print("https://app.daytona.io/dashboard/sandboxes")


if __name__ == "__main__":
    main()
