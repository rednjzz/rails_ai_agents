"""Sentry MCP server — exposes Sentry data as tools for Claude Code."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from mcp.server.fastmcp import Context, FastMCP

from mcp_server.config import SentryConfig
from mcp_server.path_mapper import format_mapping_summary, map_frames_to_local
from mcp_server.redactor import redact_event
from mcp_server.sentry_client import SentryAPIError, SentryClient
from mcp_server.state import MonitorState

mcp = FastMCP("sentry-monitor")

# Lazily initialized client — created on first tool call
_client: SentryClient | None = None
_config: SentryConfig | None = None


def _get_config() -> SentryConfig:
    global _config
    if _config is None:
        _config = SentryConfig.from_env()
    return _config


def _get_client() -> SentryClient:
    global _client
    if _client is None:
        _client = SentryClient(_get_config())
    return _client


def _extract_frames(event_data: dict) -> list[dict]:
    """Extract stack trace frames from a Sentry event."""
    frames = []
    for entry in event_data.get("entries", []):
        if entry.get("type") == "exception":
            for exc in entry.get("data", {}).get("values", []):
                frames.extend(exc.get("stacktrace", {}).get("frames", []))
    return frames


def _build_issue_summary(issue: dict) -> dict:
    """Transform a Sentry issue into a standardized summary."""
    return {
        "issue_id": issue["id"],
        "short_id": issue.get("shortId", ""),
        "title": issue.get("title", ""),
        "culprit": issue.get("culprit", ""),
        "level": issue.get("level", ""),
        "count": int(issue.get("count", 0)),
        "user_count": issue.get("userCount", 0),
        "first_seen": issue.get("firstSeen", ""),
        "last_seen": issue.get("lastSeen", ""),
        "project_name": issue.get("project", {}).get("name", ""),
        "permalink": issue.get("permalink", ""),
    }


@mcp.tool()
async def list_issues(
    ctx: Context,
    project_slug: str = "",
    query: str = "is:unresolved",
    sort_by: str = "date",
    environment: str = "",
    date_range: str = "14d",
    page_size: int = 25,
    cursor: str = "",
) -> str:
    """List unresolved Sentry issues with filtering and pagination.

    Args:
        project_slug: Sentry project slug. Uses default if empty.
        query: Sentry search query (e.g., "is:unresolved level:error").
        sort_by: Sort order: "date", "freq", "new", or "priority".
        environment: Filter by environment (e.g., "production").
        date_range: Stats period: "24h", "7d", "14d", "30d".
        page_size: Number of issues per page (max 100).
        cursor: Pagination cursor from a previous response.
    """
    client = _get_client()
    await ctx.info(f"Fetching issues (query={query}, sort={sort_by})")

    try:
        result = await client.list_issues(
            project_slug=project_slug or None,
            query=query,
            sort_by=sort_by,
            environment=environment or None,
            date_range=date_range,
            cursor=cursor or None,
        )
    except (SentryAPIError, ValueError) as e:
        return json.dumps({"error": str(e)})

    issues = [_build_issue_summary(issue) for issue in result.data[:page_size]]

    return json.dumps(
        {
            "issues": issues,
            "next_cursor": result.next_cursor,
            "has_more": result.has_more,
        }
    )


@mcp.tool()
async def get_issue_detail(
    ctx: Context,
    issue_id: str,
    include_pii: bool = False,
) -> str:
    """Get detailed information about a specific Sentry issue including stack trace.

    Args:
        issue_id: Sentry issue ID (numeric string).
        include_pii: If True, include user context, request headers/body, and local variables.
    """
    client = _get_client()
    await ctx.info(f"Fetching issue detail for {issue_id}")

    try:
        issue = await client.get_issue_detail(issue_id)
        event = await client.get_latest_event(issue_id)
    except (SentryAPIError, ValueError) as e:
        return json.dumps({"error": str(e)})

    # Redact PII from event data
    event = redact_event(event, include_pii=include_pii)

    # Extract and map stack frames
    frames = _extract_frames(event)
    frame_data = []
    for frame in frames:
        frame_data.append(
            {
                "filename": frame.get("filename", ""),
                "function": frame.get("function", ""),
                "line_no": frame.get("lineNo"),
                "context_lines": [line[1] for line in frame.get("context", [])],
            }
        )

    # Extract exception info
    exception_type = ""
    exception_value = ""
    for entry in event.get("entries", []):
        if entry.get("type") == "exception":
            values = entry.get("data", {}).get("values", [])
            if values:
                exception_type = values[0].get("type", "")
                exception_value = values[0].get("value", "")

    tags = {}
    for tag in event.get("tags", []):
        tags[tag["key"]] = tag["value"]

    result = {
        "issue_id": issue["id"],
        "short_id": issue.get("shortId", ""),
        "title": issue.get("title", ""),
        "culprit": issue.get("culprit", ""),
        "level": issue.get("level", ""),
        "count": int(issue.get("count", 0)),
        "first_seen": issue.get("firstSeen", ""),
        "last_seen": issue.get("lastSeen", ""),
        "project_name": issue.get("project", {}).get("name", ""),
        "permalink": issue.get("permalink", ""),
        "exception_type": exception_type,
        "exception_value": exception_value,
        "stacktrace": frame_data,
        "tags": tags,
        "environment": tags.get("environment", ""),
        "user_context": event.get("user"),
        "request_context": None,
        "pii_redacted": event.get("pii_redacted", True),
    }

    if event.get("pii_note"):
        result["pii_note"] = event["pii_note"]

    # Include request context if PII is included
    if include_pii:
        for entry in event.get("entries", []):
            if entry.get("type") == "request":
                result["request_context"] = entry.get("data")

    return json.dumps(result)


@mcp.tool()
async def map_stacktrace(
    ctx: Context,
    issue_id: str,
    repo_root: str = "",
) -> str:
    """Map a Sentry stack trace to local repository files.

    Args:
        issue_id: Sentry issue ID to map.
        repo_root: Root path of the local repository. Uses current directory if empty.
    """
    client = _get_client()
    root = repo_root or os.getcwd()
    await ctx.info(f"Mapping stacktrace for issue {issue_id} against {root}")

    try:
        event = await client.get_latest_event(issue_id)
    except (SentryAPIError, ValueError) as e:
        return json.dumps({"error": str(e)})

    frames = _extract_frames(event)

    try:
        mappings = map_frames_to_local(frames, root)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    result = {
        "issue_id": issue_id,
        "mappings": [
            {
                "sentry_path": m.sentry_path,
                "local_path": m.local_path,
                "confidence": m.confidence,
                "line_no": m.line_no,
                "exists": m.exists,
            }
            for m in mappings
        ],
        "summary": format_mapping_summary(mappings),
    }

    return json.dumps(result)


@mcp.tool()
async def get_server_status(ctx: Context) -> str:
    """Check MCP server health and Sentry connection status."""
    try:
        config = _get_config()
    except ValueError as e:
        return json.dumps({"status": "misconfigured", "error": str(e)})

    client = _get_client()
    auth_valid = await client.validate_auth()

    state_file = os.path.join(".claude", "sentry-monitor-state.json")
    state_exists = os.path.isfile(state_file)
    seen_count = 0
    if state_exists:
        try:
            with open(state_file) as f:
                state = json.load(f)
            seen_count = len(state.get("seen_issues", {}))
        except (json.JSONDecodeError, OSError):
            pass

    return json.dumps(
        {
            "status": "connected" if auth_valid else "auth_failed",
            "sentry_org": config.org,
            "configured_projects": [config.project],
            "auth_valid": auth_valid,
            "state_file_exists": state_exists,
            "seen_issues_count": seen_count,
        }
    )


DEFAULT_STATE_DIR = os.path.abspath(".claude")
DEFAULT_STATE_FILE = os.path.join(DEFAULT_STATE_DIR, "sentry-monitor-state.json")


def _safe_state_path(state_file: str) -> str:
    """Validate that state_file is within the .claude/ directory to prevent path traversal."""
    resolved = os.path.abspath(state_file)
    if not resolved.startswith(DEFAULT_STATE_DIR + os.sep) and resolved != DEFAULT_STATE_DIR:
        raise ValueError(
            f"state_file must be within {DEFAULT_STATE_DIR}, got: {resolved}"
        )
    return resolved


@mcp.tool()
async def check_new_errors(
    ctx: Context,
    project_slug: str = "",
    environment: str = "",
    state_file: str = "",
) -> str:
    """Check for new Sentry errors since last poll. Updates the state file.

    Args:
        project_slug: Sentry project slug. Uses default if empty.
        environment: Filter by environment (e.g., "production").
        state_file: Path to persistent state file. Must be within .claude/ directory. Uses default if empty.
    """
    client = _get_client()
    try:
        sf = _safe_state_path(state_file or DEFAULT_STATE_FILE)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    # Load state
    state = MonitorState.load(sf)
    was_corrupted = state.was_corrupted and os.path.isfile(sf)

    last_poll = state.last_poll
    current_poll = datetime.now(timezone.utc).isoformat()

    await ctx.info(f"Checking for new errors (last poll: {last_poll or 'never'})")

    try:
        result = await client.list_issues(
            project_slug=project_slug or None,
            query="is:unresolved",
            sort_by="date",
            environment=environment or None,
        )
    except (SentryAPIError, ValueError) as e:
        return json.dumps({"error": str(e)})

    # Filter to new/updated issues
    new_issues = []
    for issue in result.data:
        issue_id = issue["id"]
        last_seen = issue.get("lastSeen", "")
        if state.is_new(issue_id, last_seen):
            new_issues.append(_build_issue_summary(issue))
            state.mark_seen(issue_id, last_seen)

    # Prune old entries and save
    state.last_poll = current_poll
    state.prune()
    state.save(sf)

    response = {
        "new_issues": new_issues,
        "total_new": len(new_issues),
        "last_poll": last_poll,
        "current_poll": current_poll,
    }

    if was_corrupted:
        response["warning"] = (
            "State file was corrupted and has been reset. All current issues will appear as new."
        )

    return json.dumps(response)


if __name__ == "__main__":
    mcp.run()
