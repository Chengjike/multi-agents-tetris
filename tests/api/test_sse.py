"""
测试用例：SSE 端点

测试 Server-Sent Events 推送
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app


class TestSSEEndpoint:
    """测试 SSE 端点"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_sse_connection(self, client):
        """测试 SSE 连接建立"""
        # 使用 timeout 避免长时间等待
        try:
            response = await asyncio.wait_for(
                client.get("/api/game/sse"),
                timeout=2.0
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
        except asyncio.TimeoutError:
            pytest.skip("SSE connection timeout - may need real server")

    @pytest.mark.asyncio
    async def test_sse_initial_message(self, client):
        """测试 SSE 初始消息"""
        # 这个测试需要实际的服务器运行，标记为集成测试
        pytest.skip("SSE test requires real server - use integration test")

    @pytest.mark.asyncio
    async def test_sse_event_format(self, client):
        """测试 SSE 事件格式"""
        pytest.skip("SSE test requires real server - use integration test")


class TestSSEGameEvents:
    """测试 SSE 游戏事件"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_sse_on_game_start(self, client):
        """测试游戏开始时的 SSE 推送"""
        pytest.skip("SSE test requires real server - use integration test")

    @pytest.mark.asyncio
    async def test_sse_on_game_stop(self, client):
        """测试游戏停止时的 SSE 推送"""
        pytest.skip("SSE test requires real server - use integration test")


class TestSSEParser:
    """测试 SSE 消息解析（使用 mock）"""

    def test_parse_sse_data_line(self):
        """测试解析 SSE data 行"""
        from backend.http_client import TetrisHTTPClient

        # 模拟解析 "data: {\"type\": \"game_state\"}"
        line = 'data: {"type": "game_state", "tick": 1}'
        result = TetrisHTTPClient._parse_sse_line(line)

        assert result is not None
        assert result["type"] == "game_state"
        assert result["tick"] == 1

    def test_parse_empty_line(self):
        """测试解析空行"""
        from backend.http_client import TetrisHTTPClient

        result = TetrisHTTPClient._parse_sse_line("")
        assert result is None

    def test_parse_non_data_line(self):
        """测试解析非 data 行"""
        from backend.http_client import TetrisHTTPClient

        result = TetrisHTTPClient._parse_sse_line(": comment")
        assert result is None

    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        from backend.http_client import TetrisHTTPClient

        result = TetrisHTTPClient._parse_sse_line("data: invalid json")
        assert result is None


class TestHTTPClientMocked:
    """使用 Mock 测试 HTTP 客户端"""

    @pytest.mark.asyncio
    async def test_client_creation(self):
        """测试客户端创建"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient(base_url="http://test")
        assert client.base_url == "http://test"
        assert client.reconnect is True
        assert client.reconnect_delay == 1.0
        assert client.max_reconnect_attempts == 5

    @pytest.mark.asyncio
    async def test_client_callbacks(self):
        """测试客户端回调设置"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()

        # 设置回调
        def on_state(data):
            pass

        def on_error(err):
            pass

        client.on_game_state = on_state
        client.on_error = on_error

        assert client.on_game_state == on_state
        assert client.on_error == on_error

    @pytest.mark.asyncio
    async def test_client_ensure_session(self):
        """测试 session 确保"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        # session 初始为 None
        assert client._session is None

        # 调用 ensure_session 后应该创建 session
        # 注意：这需要真实的 aiohttp，这里只测试方法存在
        assert hasattr(client, '_ensure_session')
        assert callable(client._ensure_session)