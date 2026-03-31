"""Async Sentry API client using httpx."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from mcp_server.config import SentryConfig


@dataclass
class PaginatedResponse:
    data: list[dict]
    next_cursor: str | None
    has_more: bool


class SentryAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Sentry API error: {status_code} - {message}")


class SentryAuthError(SentryAPIError):
    def __init__(self):
        super().__init__(401, "Authentication failed. Check your SENTRY_AUTH_TOKEN.")


class SentryRateLimitError(SentryAPIError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(429, f"Sentry rate limit reached. Retry after {retry_after}s.")


def _validate_issue_id(issue_id: str) -> str:
    """Validate that issue_id is numeric to prevent path traversal."""
    if not re.match(r"^\d+$", issue_id):
        raise ValueError(f"Invalid issue_id (must be numeric): {issue_id}")
    return issue_id


def _validate_slug(slug: str) -> str:
    """Validate that a project/org slug matches Sentry's slug format."""
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", slug):
        raise ValueError(f"Invalid slug: {slug}")
    return slug


class SentryClient:
    def __init__(self, config: SentryConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.auth_token}"},
            timeout=30.0,
        )

    async def close(self):
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.ConnectError as e:
            raise SentryAPIError(0, f"Cannot connect to Sentry: {e}") from e
        except httpx.TimeoutException as e:
            raise SentryAPIError(0, f"Sentry request timed out: {e}") from e

        if response.status_code == 401:
            raise SentryAuthError()
        if response.status_code == 429:
            try:
                retry_after = int(response.headers.get("Retry-After", "60"))
            except (ValueError, TypeError):
                retry_after = 60
            raise SentryRateLimitError(retry_after)
        if response.status_code >= 400:
            raise SentryAPIError(response.status_code, response.text)

        return response

    @staticmethod
    def _parse_link_header(link_header: str) -> tuple[str | None, bool]:
        """Parse cursor and has_more from Sentry's Link header."""
        next_cursor = None
        has_more = False

        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part:
                results_match = re.search(r'results="(\w+)"', part)
                if results_match and results_match.group(1) == "true":
                    has_more = True
                    cursor_match = re.search(r"cursor=([^&>]+)", part)
                    if cursor_match:
                        next_cursor = cursor_match.group(1)

        return next_cursor, has_more

    async def list_issues(
        self,
        project_slug: str | None = None,
        query: str = "is:unresolved",
        sort_by: str = "date",
        environment: str | None = None,
        date_range: str = "14d",
        cursor: str | None = None,
    ) -> PaginatedResponse:
        slug = _validate_slug(project_slug or self.config.project)
        org = _validate_slug(self.config.org)
        path = f"/projects/{org}/{slug}/issues/"

        params: dict = {
            "query": query,
            "sortBy": sort_by,
            "statsPeriod": date_range,
        }
        if environment:
            params["environment"] = environment
        if cursor:
            params["cursor"] = cursor

        response = await self._request("GET", path, params=params)
        data = response.json()

        link = response.headers.get("Link", "")
        next_cursor, has_more = self._parse_link_header(link)

        return PaginatedResponse(data=data, next_cursor=next_cursor, has_more=has_more)

    async def get_issue_detail(self, issue_id: str) -> dict:
        _validate_issue_id(issue_id)
        org = _validate_slug(self.config.org)
        path = f"/organizations/{org}/issues/{issue_id}/"
        response = await self._request("GET", path)
        return response.json()

    async def get_latest_event(self, issue_id: str) -> dict:
        _validate_issue_id(issue_id)
        org = _validate_slug(self.config.org)
        path = f"/organizations/{org}/issues/{issue_id}/events/latest/"
        response = await self._request("GET", path)
        return response.json()

    async def validate_auth(self) -> bool:
        """Check if the auth token is valid by hitting a lightweight endpoint."""
        try:
            org = _validate_slug(self.config.org)
            await self._request("GET", f"/organizations/{org}/")
            return True
        except SentryAuthError:
            return False
        except SentryAPIError:
            return False
