#!/usr/bin/env python3
"""Entry point for the GitHub Issue Triage Agent."""

import logging
from src.main import app, settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on port {settings.webhook_port}")
    logger.info(f"Configured repo: {settings.repo_full_name}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.webhook_port,
        log_level="info"
    )
