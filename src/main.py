import logging
from fastapi import FastAPI, Request
from .config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration
settings = Settings.load()

# Initialize FastAPI app
app = FastAPI(
    title="GitHub Issue Triage Agent",
    description="Automatically triage GitHub issues with Claude AI",
    version="0.1.0"
)


@app.get("/")
async def root():
    """Root endpoint - returns basic app info."""
    return {
        "name": "GitHub Issue Triage Agent",
        "status": "running",
        "repo": settings.repo_full_name,
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request):
    """Receive GitHub webhook events for new issues."""
    try:
        payload = await request.json()

        # Extract relevant fields
        action = payload.get("action")
        issue_number = payload.get("issue", {}).get("number")
        repo_full_name = payload.get("repository", {}).get("full_name")

        logger.info(
            f"Webhook received: action={action}, repo={repo_full_name}, issue=#{issue_number}"
        )

        # Filter for the target repo only
        if repo_full_name != settings.repo_full_name:
            logger.info(f"Ignoring webhook for different repo: {repo_full_name}")
            return {"status": "ignored", "reason": "different_repo"}

        # Filter for issue opened events only
        if action != "opened":
            logger.info(f"Ignoring webhook for action: {action}")
            return {"status": "ignored", "reason": "not_opened"}

        logger.info(f"Issue #{issue_number} opened - queued for triage")

        # Return 200 immediately (background task will be added in Block 4)
        return {"status": "webhook received", "issue": issue_number}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
