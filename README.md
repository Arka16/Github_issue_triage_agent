# GitHub Issue Triage Agent — MVP Overview

## Problem

Open-source maintainers spend 30–60 minutes daily on mechanical triage work: reading new issues, deciding if they're bugs or feature requests, checking for duplicates, and applying labels. This is repetitive judgment work that an LLM agent can handle well.

## Solution

An agent that automatically triages new GitHub issues the moment they're opened. It reads the issue, classifies it, checks for duplicates against existing issues, and posts a summary comment with labels applied — all within seconds.

## MVP Scope

When a new issue is opened on a connected repo, the agent:

1. Reads the issue title and body
2. Fetches all existing open issues for context
3. Classifies the issue with labels from the repo's existing label set (e.g., bug, feature, question, priority, area)
4. Searches for duplicate or related issues and links them
5. Posts a single triage comment summarizing its findings and applies the chosen labels

## What's explicitly out of scope for V1

- Assignee suggestions (requires git blame integration)
- Smart reply drafting beyond the triage summary
- Dashboard or custom UI (GitHub's interface is the UI)
- Multi-repo support (hardcoded to one repo)
- Custom label creation (only uses labels already on the repo)

## Key Design Principles

- **Human-in-the-loop**: The agent labels and comments but never closes, assigns, or takes destructive actions. A maintainer reviews everything.
- **Safe by default**: Only applies labels that already exist on the repo. The triage comment is clearly marked as bot-generated.
- **Atomic actions**: If the Claude API call fails, nothing gets posted. No partial triage.

## Tech Stack

- Python 3.11+
- FastAPI (webhook receiver)
- Anthropic Python SDK (Claude API)
- PyGithub or httpx (GitHub REST API)
- ngrok (local development tunnel)

## Success Criteria

The MVP is done when you can open a fake issue on a test repo and watch the bot apply correct labels and post a useful triage comment within 10 seconds.
