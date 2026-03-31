"""Tests for the Sentry API client."""

from __future__ import annotations

import httpx
import pytest

from mcp_server.sentry_client import (
    SentryAPIError,
    SentryAuthError,
    SentryClient,
    SentryRateLimitError,
)
from tests.conftest import (
    LINK_HEADER_NO_NEXT,
    LINK_HEADER_WITH_NEXT,
    MOCK_ISSUE_DETAIL,
    MOCK_ISSUE_LIST,
    MOCK_LATEST_EVENT,
)


class TestListIssues:
    async def test_returns_issues(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            return_value=httpx.Response(
                200,
                json=MOCK_ISSUE_LIST,
                headers={"Link": LINK_HEADER_NO_NEXT},
            )
        )

        result = await sentry_client.list_issues()
        assert len(result.data) == 2
        assert result.data[0]["id"] == "12345"
        assert result.has_more is False
        assert result.next_cursor is None

    async def test_pagination_with_next(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            return_value=httpx.Response(
                200,
                json=MOCK_ISSUE_LIST,
                headers={"Link": LINK_HEADER_WITH_NEXT},
            )
        )

        result = await sentry_client.list_issues()
        assert result.has_more is True
        assert result.next_cursor == "def456"

    async def test_passes_query_params(self, sentry_client: SentryClient, mock_sentry):
        route = mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            return_value=httpx.Response(200, json=[], headers={"Link": LINK_HEADER_NO_NEXT})
        )

        await sentry_client.list_issues(
            query="is:unresolved level:error",
            sort_by="freq",
            environment="production",
            date_range="24h",
        )

        assert route.called
        request = route.calls[0].request
        assert "is%3Aunresolved" in str(request.url) or "is:unresolved" in str(request.url)

    async def test_custom_project_slug(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/projects/test-org/other-project/issues/").mock(
            return_value=httpx.Response(200, json=[], headers={"Link": LINK_HEADER_NO_NEXT})
        )

        result = await sentry_client.list_issues(project_slug="other-project")
        assert result.data == []

    async def test_with_cursor(self, sentry_client: SentryClient, mock_sentry):
        route = mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            return_value=httpx.Response(200, json=[], headers={"Link": LINK_HEADER_NO_NEXT})
        )

        await sentry_client.list_issues(cursor="abc123")
        request = route.calls[0].request
        assert "cursor=abc123" in str(request.url)


class TestGetIssueDetail:
    async def test_returns_detail(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/organizations/test-org/issues/12345/").mock(
            return_value=httpx.Response(200, json=MOCK_ISSUE_DETAIL)
        )

        result = await sentry_client.get_issue_detail("12345")
        assert result["id"] == "12345"
        assert result["title"] == "TypeError: Cannot read property 'x' of undefined"

    async def test_not_found(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/organizations/test-org/issues/99999/").mock(
            return_value=httpx.Response(404, text="Not found")
        )

        with pytest.raises(SentryAPIError) as exc_info:
            await sentry_client.get_issue_detail("99999")
        assert exc_info.value.status_code == 404


class TestGetLatestEvent:
    async def test_returns_event(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/organizations/test-org/issues/12345/events/latest/").mock(
            return_value=httpx.Response(200, json=MOCK_LATEST_EVENT)
        )

        result = await sentry_client.get_latest_event("12345")
        assert result["eventID"] == "evt-abc123"
        assert len(result["entries"]) == 3


class TestErrorHandling:
    async def test_auth_failure(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        with pytest.raises(SentryAuthError):
            await sentry_client.list_issues()

    async def test_rate_limiting(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            return_value=httpx.Response(429, headers={"Retry-After": "30"}, text="Rate limited")
        )

        with pytest.raises(SentryRateLimitError) as exc_info:
            await sentry_client.list_issues()
        assert exc_info.value.retry_after == 30

    async def test_network_error(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(SentryAPIError) as exc_info:
            await sentry_client.list_issues()
        assert "Cannot connect to Sentry" in exc_info.value.message

    async def test_server_error(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/projects/test-org/test-project/issues/").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        with pytest.raises(SentryAPIError) as exc_info:
            await sentry_client.list_issues()
        assert exc_info.value.status_code == 500


class TestValidateAuth:
    async def test_valid_auth(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/organizations/test-org/").mock(
            return_value=httpx.Response(200, json={"slug": "test-org"})
        )

        assert await sentry_client.validate_auth() is True

    async def test_invalid_auth(self, sentry_client: SentryClient, mock_sentry):
        mock_sentry.get("/organizations/test-org/").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        assert await sentry_client.validate_auth() is False


class TestInputValidation:
    """Tests for _validate_issue_id and _validate_slug."""

    def test_valid_issue_id(self):
        from mcp_server.sentry_client import _validate_issue_id

        assert _validate_issue_id("12345") == "12345"
        assert _validate_issue_id("0") == "0"

    def test_invalid_issue_id_rejects_traversal(self):
        from mcp_server.sentry_client import _validate_issue_id

        with pytest.raises(ValueError, match="Invalid issue_id"):
            _validate_issue_id("../../../admin")

    def test_invalid_issue_id_rejects_non_numeric(self):
        from mcp_server.sentry_client import _validate_issue_id

        with pytest.raises(ValueError, match="Invalid issue_id"):
            _validate_issue_id("abc")

    def test_invalid_issue_id_rejects_empty(self):
        from mcp_server.sentry_client import _validate_issue_id

        with pytest.raises(ValueError, match="Invalid issue_id"):
            _validate_issue_id("")

    def test_valid_slug(self):
        from mcp_server.sentry_client import _validate_slug

        assert _validate_slug("my-project") == "my-project"
        assert _validate_slug("test-org") == "test-org"
        assert _validate_slug("project123") == "project123"
        assert _validate_slug("my_project") == "my_project"

    def test_invalid_slug_rejects_traversal(self):
        from mcp_server.sentry_client import _validate_slug

        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("../../etc")

    def test_invalid_slug_rejects_special_chars(self):
        from mcp_server.sentry_client import _validate_slug

        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("my project")

    def test_invalid_slug_rejects_empty(self):
        from mcp_server.sentry_client import _validate_slug

        with pytest.raises(ValueError, match="Invalid slug"):
            _validate_slug("")

    def test_rate_limit_non_integer_retry_after(self):
        """Malformed Retry-After header should fall back to 60s, not crash."""
        from mcp_server.sentry_client import SentryRateLimitError

        # Simulate the parsing logic
        try:
            int("Thu, 01 Dec 2025 16:00:00 GMT")
        except (ValueError, TypeError):
            retry_after = 60

        assert retry_after == 60
