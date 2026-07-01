import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.github.com"


class GitHubService:
    """Wrapper for GitHub REST API operations."""

    def __init__(self, token: str, repo_full_name: str, fetch_limit: int = 50):
        """Initialize GitHub service.

        Args:
            token: GitHub Personal Access Token
            repo_full_name: Repository name in format 'owner/repo'
            fetch_limit: Number of issues to fetch (default 50)
        """
        self.token = token
        self.repo_full_name = repo_full_name
        self.fetch_limit = fetch_limit
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get_issue(self, issue_number: int) -> Optional[dict]:
        """Fetch a specific issue by number.

        Args:
            issue_number: GitHub issue number

        Returns:
            Issue dict with keys: title, body, number, user.login, created_at, labels
            Returns None if issue not found
        """
        url = f"{BASE_URL}/repos/{self.repo_full_name}/issues/{issue_number}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 404:
                    logger.warning(f"Issue #{issue_number} not found (404)")
                    return None
                response.raise_for_status()

                data = response.json()
                return {
                    "title": data.get("title", ""),
                    "body": data.get("body", ""),
                    "number": data.get("number"),
                    "author": data.get("user", {}).get("login"),
                    "created_at": data.get("created_at"),
                    "labels": [label["name"] for label in data.get("labels", [])],
                }
        except httpx.HTTPError as e:
            logger.error(f"Error fetching issue #{issue_number}: {e}")
            return None

    async def get_open_issues(self, exclude_number: Optional[int] = None) -> list[dict]:
        """Fetch recent open issues from the repo.

        Args:
            exclude_number: Issue number to exclude from results (optional)

        Returns:
            List of issue dicts with keys: title, number, body, labels
            Body is truncated to 200 characters
        """
        url = f"{BASE_URL}/repos/{self.repo_full_name}/issues"
        params = {
            "state": "open",
            "per_page": self.fetch_limit,
            "sort": "created",
            "direction": "desc",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                issues = []
                for data in response.json():
                    # Skip the excluded issue
                    if exclude_number and data.get("number") == exclude_number:
                        continue

                    body = data.get("body", "") or ""
                    truncated_body = body[:200] + "..." if len(body) > 200 else body

                    issues.append(
                        {
                            "title": data.get("title", ""),
                            "number": data.get("number"),
                            "body": truncated_body,
                            "labels": [
                                label["name"] for label in data.get("labels", [])
                            ],
                        }
                    )

                logger.info(f"Fetched {len(issues)} open issues from {self.repo_full_name}")
                return issues
        except httpx.HTTPError as e:
            logger.error(f"Error fetching open issues: {e}")
            return []

    async def get_labels(self) -> list[str]:
        """Fetch all labels defined on the repo.

        Returns:
            List of label names
        """
        url = f"{BASE_URL}/repos/{self.repo_full_name}/labels"
        params = {"per_page": 100}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                labels = [label["name"] for label in response.json()]
                logger.info(f"Fetched {len(labels)} labels from {self.repo_full_name}")
                return labels
        except httpx.HTTPError as e:
            logger.error(f"Error fetching labels: {e}")
            return []

    async def apply_labels(self, issue_number: int, labels: list[str]) -> bool:
        """Add labels to an issue.

        Args:
            issue_number: GitHub issue number
            labels: List of label names to add

        Returns:
            True if successful, False otherwise
        """
        if not labels:
            logger.info(f"No labels to apply to issue #{issue_number}")
            return True

        url = f"{BASE_URL}/repos/{self.repo_full_name}/issues/{issue_number}/labels"
        payload = {"labels": labels}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url, headers=self.headers, json=payload
                )
                response.raise_for_status()

                logger.info(f"Applied {len(labels)} labels to issue #{issue_number}: {labels}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Error applying labels to issue #{issue_number}: {e}")
            return False

    async def post_comment(self, issue_number: int, body: str) -> bool:
        """Post a comment on an issue.

        Args:
            issue_number: GitHub issue number
            body: Comment body (markdown)

        Returns:
            True if successful, False otherwise
        """
        url = f"{BASE_URL}/repos/{self.repo_full_name}/issues/{issue_number}/comments"
        payload = {"body": body}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url, headers=self.headers, json=payload
                )
                response.raise_for_status()

                logger.info(
                    f"Posted comment to issue #{issue_number} "
                    f"({len(body)} chars)"
                )
                return True
        except httpx.HTTPError as e:
            logger.error(f"Error posting comment to issue #{issue_number}: {e}")
            return False
