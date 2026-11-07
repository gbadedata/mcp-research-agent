# Roadmap

The research-digest tools already fetch pages and feeds, deduplicate what they find, store it
in SQLite and serve it through a dashboard. The next stage turns the same foundation into a
job-discovery pipeline: pull roles from job APIs and alert emails, score them against my
criteria, and queue the good ones for review. Applications are always submitted by hand.

Each milestone is small enough to build and test in one or two sessions, and every one ends
with the test suite green in CI.

## Ground rules

- **No secrets in the repo.** API keys are read from environment variables only. `.env`
  files and key files are git-ignored, and the code never logs a key.
- **No other people's personal data.** Job records keep job details only (title, company,
  location, pay, contract type, link, source, dates). Recruiter names, emails and phone
  numbers are dropped at ingestion, and email addresses and phone numbers are stripped from
  description text before anything is stored.
- **Offline tests.** Every external call (job APIs, the mail server, the model) is tested
  against recorded or sanitised fixtures, so CI needs no keys and no network.

## Milestone 0 - Maintenance

1. **Migrate to MCP Python SDK 2.x.** `FastMCP` became `MCPServer` in 2.x. Port
   `mcp_server.py`, remove the `<2` pin in `requirements.txt`, and keep the server tests
   passing across the CI Python versions.
2. **Clear the feedparser deprecation.** `fetch_feed` triggers feedparser's
   `updated`/`published` fallback warning. Read the fields explicitly, and run the suite
   with warnings treated as errors.
3. **Lint and type checks in CI.** Add Ruff and mypy, and fix what they report.
4. **Packaging.** Move to `pyproject.toml` with a `research-agent` console script, keeping
   `requirements.txt` for simple installs.

## Milestone 1 - Job sources

5. **Job data model.** A `JobPosting` schema with an explicit allow-list of fields, so
   contact details cannot be stored by accident.
6. **Store migration.** A schema-version table and a simple migration runner. Add a `jobs`
   table alongside the existing `items` table without breaking current data.
7. **Adzuna source.** Search by keywords and location, with pagination, retries with
   backoff and rate limiting. Tested against recorded responses.
8. **Reed source.** The same for the Reed API, which uses basic auth with the key.
9. **Credential handling.** One place that reads keys from the environment and gives a
   clear error when one is missing.
10. **Alert-email ingestion.** Read unprocessed job-alert emails from a dedicated inbox over
    IMAP and mark them processed. Tested against a fake mail server.
11. **Alert parsers.** Parsers for each board's alert format (e.g. Jobserve, CWJobs), plus a
    generic fallback. Tested on sanitised email fixtures.
12. **Personal-data filter.** Strip email addresses and phone numbers from descriptions and
    drop contact fields. Tests prove nothing slips through.
13. **Cross-source deduplication.** Match the same role posted on several boards by
    canonical URL, then by a fuzzy match on title, company and location.

## Milestone 2 - Scoring and review

14. **Criteria config.** A TOML file with target titles, required and nice-to-have skills,
    locations or remote, minimum pay or day rate, IR35 status and exclusions.
15. **Rule-based fit scorer.** A score with a per-criterion breakdown, so every score can be
    explained.
16. **Optional model-assisted scoring.** A thin hook through the existing LLM wrapper,
    tested with the MockLLM, and off by default.
17. **Application states.** discovered -> shortlisted -> applied -> interviewing ->
    offer / rejected / withdrawn. Invalid transitions are rejected and every change is
    logged.
18. **Review queue in the dashboard.** Jobs listed by score, with actions to shortlist,
    dismiss or mark as applied. The dashboard is read-only today, so this adds basic auth
    and CSRF protection for its forms.
19. **Job detail page.** The score breakdown, status history and source links.

## Milestone 3 - Running it day to day

20. **CLI commands.** `jobs fetch`, `jobs score`, `jobs review` and `jobs status`.
21. **Scheduled runs.** Idempotent runs with a run log, plus an example cron job and
    systemd timer.
22. **MCP tools for jobs.** Expose job search, listing and status updates over the MCP
    server, so an MCP client can query the pipeline.
23. **Daily digest.** A digest of new high-scoring roles, reusing the digest module.
24. **Logging and run summaries.** Structured logs and a short summary of each run.
25. **Docs.** Update the README and architecture diagram for the job pipeline, including
    the data-handling rules above.
