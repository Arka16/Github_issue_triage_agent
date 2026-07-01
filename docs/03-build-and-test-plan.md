# GitHub Issue Triage Agent — Build & Test Plan

## Prerequisites (30 min)

Before writing any code:

1. Create a test GitHub repo (public or private) — this is your sandbox
2. Generate a GitHub Personal Access Token with `repo` scope
3. Get an Anthropic API key from console.anthropic.com
4. Install ngrok (brew install ngrok or download from ngrok.com)
5. Create a Python virtual environment and install dependencies:
   `pip install fastapi uvicorn httpx anthropic python-dotenv`

## Day 1: Core Pipeline (4–5 hours)

### Block 1: Webhook receiver (1 hour)

Build `config.py` and `main.py`.

- Load env vars with python-dotenv
- Create a FastAPI app with a POST `/webhook` endpoint
- Parse the incoming JSON, extract action, issue title, issue number, repo name
- Skip webhook signature validation for now (add in Day 2)
- Log the parsed data and return 200
- Test: start the server with `uvicorn main:app --reload`, open ngrok (`ngrok http 8000`), configure the GitHub repo webhook (Settings → Webhooks → Payload URL = ngrok URL + `/webhook`, Content type = application/json, select "Issues" events). Open a test issue and confirm the server logs it.

### Block 2: GitHub service (1 hour)

Build `github_service.py`.

- Implement `get_issue()`, `get_open_issues()`, `get_labels()` using httpx
- Implement `apply_labels()` and `post_comment()`
- Test each function in isolation: run a quick script that fetches your test repo's issues and prints them. Then test `apply_labels` by adding a label to a test issue and checking GitHub.

### Block 3: Agent logic (1.5 hours)

Build `agent.py`.

- Define the `TriageResult` dataclass
- Write the prompt template (system + user message with the new issue, existing issues, and available labels)
- Call the Claude API via the Anthropic Python SDK
- Parse the JSON response into a `TriageResult`
- Handle malformed responses gracefully (Claude occasionally returns extra text around JSON — strip it)
- Test in isolation: hardcode a sample issue and existing issues list, call the agent, print the result. Tweak the prompt until classifications feel right.

### Block 4: Wire it together (1 hour)

Connect all three components in `main.py`.

- When a webhook arrives: call `get_issue()`, `get_open_issues()`, and `get_labels()` concurrently using asyncio.gather
- Pass the results to the agent
- Take the agent's output and call `apply_labels()` + `post_comment()`
- Wrap in a background task so the webhook returns 200 immediately
- End-to-end test: open a new issue on the test repo. Watch the server logs. Confirm labels appear and the triage comment is posted within a few seconds.

## Day 2: Harden & Polish (3–4 hours)

### Block 5: Error handling and edge cases (1.5 hours)

- Add webhook signature validation using `hmac` and the `X-Hub-Signature-256` header
- Handle issues with empty bodies (some people only write a title)
- Handle rate limiting from both GitHub API and Claude API (add retries with exponential backoff)
- Handle the case where Claude returns labels not in the repo's set (filter them out)
- Add a timeout to the Claude API call (10 second max)
- Test: open issues with edge cases — empty body, very long body (paste a full stack trace), title only in a non-English language, an issue that's clearly not a duplicate of anything

### Block 6: Prompt tuning (1 hour)

Open 5–10 varied test issues and review the triage quality:

- Does it correctly distinguish bugs from feature requests from questions?
- Is duplicate detection too aggressive or too conservative?
- Are the labels reasonable?
- Is the summary comment useful and concise?

Iterate on the prompt based on what you see. Common fixes: adding "if unsure, label as 'needs-triage' rather than guessing", asking for confidence scores, giving examples of good triage in the prompt.

### Block 7: Documentation and cleanup (1 hour)

- Write a README with setup instructions (clone, env vars, ngrok, webhook config)
- Create `.env.example` with placeholder values
- Add type hints throughout
- Clean up logging (info for normal flow, error for failures)
- Record a short screen recording or GIF of the bot in action for the README

## Testing Strategy

### Unit tests — `test_agent.py`

Test the agent logic in isolation, no API calls needed:

- Mock the Claude API response and verify `TriageResult` parsing
- Test with malformed JSON responses (verify graceful fallback)
- Test label filtering (agent returns a label not in the repo → it gets stripped)
- Test with empty issue body
- Test with no existing issues (nothing to compare against)

### Integration tests — manual

Use your test repo to validate the full pipeline:

- Open an issue that's clearly a bug → verify it gets labeled `bug`
- Open an issue that's clearly a feature request → verify `feature` label
- Open an issue that duplicates an existing one → verify it links to the original
- Open an issue with no clear category → verify it gets a safe fallback label
- Open two issues rapidly → verify both get triaged without race conditions

### Load/reliability (stretch)

- Open 10 issues in quick succession and verify all get triaged
- Kill the server mid-triage and restart — verify no duplicate comments (idempotency)

## Deployment (Post-Weekend Stretch)

When you're ready to move off ngrok:

- Deploy to Railway, Render, or Fly.io (all have free tiers and support FastAPI)
- Replace ngrok URL with the deployed URL in GitHub webhook settings
- Add environment variables in the hosting platform's dashboard
- Optionally: package as a GitHub App instead of a personal token for multi-repo support

## What to Build Next (V2 Ideas)

After the MVP is working and deployed, pick one:

- Assignee suggestions via git blame (who last touched the relevant files?)
- Configurable triage rules per repo (via a `.triage.yml` config file in the repo)
- Slack/Discord notifications when high-priority issues are triaged
- A simple dashboard showing triage accuracy over time
- GitHub App packaging so other people can install it with one click
