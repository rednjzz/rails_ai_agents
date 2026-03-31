"""Integration tests for MCP tools."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import httpx
import pytest
import respx

from tests.conftest import (
    LINK_HEADER_NO_NEXT,
    LINK_HEADER_WITH_NEXT,
    MOCK_ISSUE_DETAIL,
    MOCK_ISSUE_LIST,
    MOCK_LATEST_EVENT,
)

# Reset global state before importing server module
os.environ.setdefault("SENTRY_AUTH_TOKEN", "test-token")
os.environ.setdefault("SENTRY_ORG", "test-org")
os.environ.setdefault("SENTRY_PROJECT", "test-project")


@pytest.fixture(autouse=True)
def reset_server_globals():
    """Reset lazily-initialized globals between tests."""
    import mcp_server.server as srv

    srv._client = None
    srv._config = None
    yield
    srv._client = None
    srv._config = None


@pytest.fixture
def mock_ctx():
    """Create a mock MCP Context."""

    class MockContext:
        async def info(self, msg):
            pass

        async def error(self, msg):
            pass

        async def debug(self, msg):
            pass

    return MockContext()


class TestListIssuesTool:
    async def test_returns_issues(self, mock_ctx):
        from mcp_server.server import list_issues

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/projects/test-org/test-project/issues/").mock(
                return_value=httpx.Response(
                    200, json=MOCK_ISSUE_LIST, headers={"Link": LINK_HEADER_NO_NEXT}
                )
            )

            result = json.loads(await list_issues(mock_ctx))

        assert len(result["issues"]) == 2
        assert result["issues"][0]["issue_id"] == "12345"
        assert result["issues"][0]["title"] == "TypeError: Cannot read property 'x' of undefined"
        assert result["has_more"] is False

    async def test_pagination(self, mock_ctx):
        from mcp_server.server import list_issues

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/projects/test-org/test-project/issues/").mock(
                return_value=httpx.Response(
                    200, json=MOCK_ISSUE_LIST, headers={"Link": LINK_HEADER_WITH_NEXT}
                )
            )

            result = json.loads(await list_issues(mock_ctx))

        assert result["has_more"] is True
        assert result["next_cursor"] == "def456"

    async def test_error_handling(self, mock_ctx):
        from mcp_server.server import list_issues

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/projects/test-org/test-project/issues/").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )

            result = json.loads(await list_issues(mock_ctx))

        assert "error" in result
        assert "Authentication failed" in result["error"]


class TestGetIssueDetailTool:
    async def test_returns_redacted_detail(self, mock_ctx):
        from mcp_server.server import get_issue_detail

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/organizations/test-org/issues/12345/").mock(
                return_value=httpx.Response(200, json=MOCK_ISSUE_DETAIL)
            )
            mock.get("/organizations/test-org/issues/12345/events/latest/").mock(
                return_value=httpx.Response(200, json=MOCK_LATEST_EVENT)
            )

            result = json.loads(await get_issue_detail(mock_ctx, issue_id="12345"))

        assert result["issue_id"] == "12345"
        assert result["pii_redacted"] is True
        assert result["user_context"] is None
        assert result["request_context"] is None
        assert "pii_note" in result

    async def test_returns_full_detail_with_pii(self, mock_ctx):
        from mcp_server.server import get_issue_detail

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/organizations/test-org/issues/12345/").mock(
                return_value=httpx.Response(200, json=MOCK_ISSUE_DETAIL)
            )
            mock.get("/organizations/test-org/issues/12345/events/latest/").mock(
                return_value=httpx.Response(200, json=MOCK_LATEST_EVENT)
            )

            result = json.loads(
                await get_issue_detail(mock_ctx, issue_id="12345", include_pii=True)
            )

        assert result["pii_redacted"] is False
        assert result["user_context"] is not None
        assert result["user_context"]["email"] == "john@example.com"
        assert result["request_context"] is not None

    async def test_error_handling(self, mock_ctx):
        from mcp_server.server import get_issue_detail

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/organizations/test-org/issues/99999/").mock(
                return_value=httpx.Response(404, text="Not found")
            )

            result = json.loads(await get_issue_detail(mock_ctx, issue_id="99999"))

        assert "error" in result


class TestMapStacktraceTool:
    async def test_maps_frames(self, mock_ctx, tmp_path):
        from mcp_server.server import map_stacktrace

        # Create a local file matching the stack trace
        services_dir = tmp_path / "services"
        services_dir.mkdir()
        (services_dir / "payment_service.rb").write_text("# test")

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/organizations/test-org/issues/12345/events/latest/").mock(
                return_value=httpx.Response(200, json=MOCK_LATEST_EVENT)
            )

            result = json.loads(
                await map_stacktrace(mock_ctx, issue_id="12345", repo_root=str(tmp_path))
            )

        assert result["issue_id"] == "12345"
        assert len(result["mappings"]) == 2
        # At least one should be mapped (partial at minimum via filename)
        mapped = [m for m in result["mappings"] if m["exists"]]
        assert len(mapped) >= 1
        assert "frames mapped" in result["summary"]


class TestGetServerStatusTool:
    async def test_returns_status(self, mock_ctx):
        from mcp_server.server import get_server_status

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/organizations/test-org/").mock(
                return_value=httpx.Response(200, json={"slug": "test-org"})
            )

            result = json.loads(await get_server_status(mock_ctx))

        assert result["status"] == "connected"
        assert result["sentry_org"] == "test-org"
        assert result["auth_valid"] is True

    async def test_auth_failed(self, mock_ctx):
        from mcp_server.server import get_server_status

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/organizations/test-org/").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )

            result = json.loads(await get_server_status(mock_ctx))

        assert result["status"] == "auth_failed"
        assert result["auth_valid"] is False

    async def test_missing_config(self, mock_ctx):
        from mcp_server.server import get_server_status

        with patch.dict(os.environ, {}, clear=True), patch(
            "mcp_server.config.load_dotenv"
        ):
            import mcp_server.server as srv

            srv._config = None
            srv._client = None
            result = json.loads(await get_server_status(mock_ctx))

        assert result["status"] == "misconfigured"
        assert "error" in result


class TestCheckNewErrorsTool:
    @pytest.fixture(autouse=True)
    def _patch_state_dir(self, tmp_path):
        """Point DEFAULT_STATE_DIR to tmp_path/.claude so state_file validation passes."""
        import mcp_server.server as srv

        safe_dir = str(tmp_path / ".claude")
        os.makedirs(safe_dir, exist_ok=True)
        with patch.object(srv, "DEFAULT_STATE_DIR", safe_dir):
            yield safe_dir

    async def test_returns_new_issues(self, mock_ctx, tmp_path):
        from mcp_server.server import check_new_errors

        state_file = str(tmp_path / ".claude" / "state.json")

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/projects/test-org/test-project/issues/").mock(
                return_value=httpx.Response(
                    200, json=MOCK_ISSUE_LIST, headers={"Link": LINK_HEADER_NO_NEXT}
                )
            )

            result = json.loads(await check_new_errors(mock_ctx, state_file=state_file))

        assert result["total_new"] == 2
        assert len(result["new_issues"]) == 2
        assert result["last_poll"] is None  # First poll

    async def test_skips_already_seen(self, mock_ctx, tmp_path):
        from mcp_server.server import check_new_errors

        state_file = str(tmp_path / ".claude" / "state.json")

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/projects/test-org/test-project/issues/").mock(
                return_value=httpx.Response(
                    200, json=MOCK_ISSUE_LIST, headers={"Link": LINK_HEADER_NO_NEXT}
                )
            )

            # First call — all new
            result1 = json.loads(await check_new_errors(mock_ctx, state_file=state_file))
            assert result1["total_new"] == 2

            # Second call — same data, nothing new
            result2 = json.loads(await check_new_errors(mock_ctx, state_file=state_file))
            assert result2["total_new"] == 0

    async def test_updates_state_file(self, mock_ctx, tmp_path):
        from mcp_server.server import check_new_errors

        state_file = str(tmp_path / ".claude" / "state.json")

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/projects/test-org/test-project/issues/").mock(
                return_value=httpx.Response(
                    200, json=MOCK_ISSUE_LIST, headers={"Link": LINK_HEADER_NO_NEXT}
                )
            )

            await check_new_errors(mock_ctx, state_file=state_file)

        assert os.path.isfile(state_file)
        with open(state_file) as f:
            state = json.load(f)
        assert "12345" in state["seen_issues"]
        assert "12346" in state["seen_issues"]

    async def test_corrupted_state_recovery(self, mock_ctx, tmp_path):
        from mcp_server.server import check_new_errors

        state_file = str(tmp_path / ".claude" / "state.json")
        with open(state_file, "w") as f:
            f.write("{corrupt!!!")

        with respx.mock(base_url="https://sentry.io/api/0") as mock:
            mock.get("/projects/test-org/test-project/issues/").mock(
                return_value=httpx.Response(
                    200, json=MOCK_ISSUE_LIST, headers={"Link": LINK_HEADER_NO_NEXT}
                )
            )

            result = json.loads(await check_new_errors(mock_ctx, state_file=state_file))

        assert result["total_new"] == 2
        assert "warning" in result

    async def test_rejects_path_traversal(self, mock_ctx, tmp_path):
        from mcp_server.server import check_new_errors

        state_file = str(tmp_path / "outside" / "state.json")
        result = json.loads(await check_new_errors(mock_ctx, state_file=state_file))

        assert "error" in result
        assert "must be within" in result["error"]
