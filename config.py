import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    """Application configuration loaded from environment variables."""

    anthropic_api_key: str
    github_token: str
    github_webhook_secret: str
    repo_full_name: str
    issue_fetch_limit: int = 50
    claude_model: str = "claude-3-5-sonnet-20241022"
    webhook_port: int = 8000
    triage_enabled: bool = True

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables.

        Raises:
            ValueError: If any required environment variable is missing.
        """
        load_dotenv()

        required_fields = {
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "GITHUB_TOKEN": "github_token",
            "GITHUB_WEBHOOK_SECRET": "github_webhook_secret",
            "REPO_FULL_NAME": "repo_full_name",
        }

        # Check required fields
        missing = []
        for env_key, field_name in required_fields.items():
            if not os.getenv(env_key):
                missing.append(env_key)

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Load optional fields with defaults
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            github_token=os.getenv("GITHUB_TOKEN"),
            github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
            repo_full_name=os.getenv("REPO_FULL_NAME"),
            issue_fetch_limit=int(os.getenv("ISSUE_FETCH_LIMIT", "50")),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8000")),
            triage_enabled=os.getenv("TRIAGE_ENABLED", "true").lower() == "true",
        )
