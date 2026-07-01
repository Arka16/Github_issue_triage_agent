# GitHub Issue Triage Agent — Architecture & Design

## System Flow

```
GitHub (issue.opened webhook)
        │
        ▼
┌──────────────────────────┐
│   FastAPI Server         │
│   POST /webhook          │
│   Validates payload,     │
│   extracts repo + issue  │
└──────────┬───────────────┘
           │
     ┌─────┼──────────┐
     ▼     ▼          ▼
  Parse   Fetch      Get
  issue   open       repo
  body    issues     labels
     │     │          │
     └─────┼──────────┘
           ▼
┌──────────────────────────┐
│   Claude API             │
│   Classify, detect       │
│   duplicates, generate   │
│   triage summary         │
└──────────┬───────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
  Apply        Post triage
  labels       comment
```

## Components

### 1. Webhook Receiver — `main.py`

Responsibility: Accept GitHub webhook payloads and dispatch to the triage pipeline.

- Single POST endpoint at `/webhook`
- Validates the `X-Hub-Signature-256` header using a webhook secret
- Filters for `issues` events with action `opened` (ignores edits, closes, etc.)
- Extracts `repo_full_name` and `issue_number`, passes them to the agent
- Returns 200 immediately; triage runs in a background task so GitHub doesn't time out

Key details:

- Use FastAPI's `BackgroundTasks` to run triage asynchronously
- Log every incoming event for debugging
- Return 200 even if triage fails (GitHub retries on non-2xx, which causes duplicate comments)

### 2. GitHub Service — `github_service.py`

Responsibility: All communication with the GitHub REST API. Nothing else talks to GitHub directly.

Functions:

- `get_issue(repo, issue_number) -> dict` — Returns title, body, author, and creation time of the new issue
- `get_open_issues(repo, limit=50) -> list[dict]` — Returns the 50 most recent open issues (title, number, labels, body snippet) for duplicate comparison
- `get_labels(repo) -> list[str]` — Returns all labels defined on the repo
- `apply_labels(repo, issue_number, labels) -> None` — Adds labels to the issue
- `post_comment(repo, issue_number, body) -> None` — Posts the triage summary as a comment

Auth: GitHub Personal Access Token with `repo` scope, passed via `GITHUB_TOKEN` env var. Use httpx for HTTP calls (async-native, pairs well with FastAPI).

### 3. Agent — `agent.py`

Responsibility: The decision-making core. Takes raw data, calls Claude, returns structured triage results.

Input: The new issue, list of existing issues, list of available labels.

Output: A `TriageResult` dataclass containing:

```python
@dataclass
class TriageResult:
    labels: list[str]           # From repo's existing label set
    related_issues: list[int]   # Issue numbers that look similar
    duplicate_of: int | None    # If it's a clear duplicate
    summary: str                # Markdown comment to post
```

Prompt design: The Claude API call receives a system prompt defining its role as a triage bot, then a user message containing:

- The new issue (title + full body)
- The existing issues (title + number + labels + body snippet, truncated to ~200 chars each)
- The available labels with descriptions if they exist

Claude is instructed to respond in JSON matching the TriageResult shape. The prompt explicitly tells it to only use labels from the provided list and to be conservative with duplicate detection (flag as "related" unless it's clearly the same bug).

### 4. Config — `config.py`

Loads from environment variables:

- `GITHUB_TOKEN` — Personal access token
- `ANTHROPIC_API_KEY` — Claude API key
- `GITHUB_WEBHOOK_SECRET` — For payload validation
- `REPO_NAME` — e.g., `octocat/my-project`
- `ISSUE_FETCH_LIMIT` — How many existing issues to fetch (default 50)

## Data Flow Detail

### What the Claude prompt looks like

```
System: You are a GitHub issue triage bot. You classify issues
and detect duplicates. Respond ONLY in JSON.

User:
## New issue #142: "Button component crashes when onClick is undefined"

Body: "When I render <Button /> without passing an onClick prop,
the app crashes with TypeError: Cannot read property 'apply'
of undefined. Stack trace: ..."

## Existing open issues (50 most recent):
- #89: "App crashes on optional handler props" [bug, component:button]
  "Several components crash when optional event handlers..."
- #102: "Add dark mode support" [feature, ui]
  "It would be great to have..."
- #131: "Dropdown doesn't close on outside click" [bug, component:dropdown]
  "When clicking outside..."
...

## Available labels:
bug, feature, question, duplicate, component:button, component:dropdown,
component:modal, priority:high, priority:medium, priority:low, good-first-issue

## Instructions:
- labels: pick from the available labels list ONLY
- related_issues: list issue numbers that seem related
- duplicate_of: set ONLY if this is clearly the same bug as an existing issue
- summary: write a brief triage comment in markdown
```

### What Claude returns

```json
{
  "labels": ["bug", "component:button", "priority:medium"],
  "related_issues": [89],
  "duplicate_of": 89,
  "summary": "This appears to be a duplicate of #89, which tracks crashes on optional handler props. The root cause is likely the same missing null check on event handlers.\n\nLabels applied: `bug`, `component:button`, `priority:medium`"
}
```

### What gets posted to GitHub

The agent applies the three labels and posts the summary as a comment, prefixed with a bot indicator:

```markdown
🤖 **Automated Triage**

This appears to be a duplicate of #89, which tracks crashes on
optional handler props. The root cause is likely the same missing
null check on event handlers.

Labels applied: `bug`, `component:button`, `priority:medium`
```

## Project Structure

```
github-issue-triage-agent/
├── main.py              # FastAPI app + webhook endpoint
├── agent.py             # Triage logic + Claude API call
├── github_service.py    # GitHub REST API wrapper
├── config.py            # Environment variable loading
├── requirements.txt     # fastapi, uvicorn, httpx, anthropic
├── .env.example         # Template for required env vars
├── test_agent.py        # Unit tests for agent logic
└── README.md            # Setup and usage instructions
```

## Security Considerations

- Webhook signature validation prevents spoofed payloads
- The GitHub token should have minimal scope (just `repo` on the target repo)
- The Anthropic API key is never logged or exposed
- The bot never takes destructive actions (no closing, deleting, or force-pushing)
