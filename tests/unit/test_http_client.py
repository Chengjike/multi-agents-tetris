"""
测试用例：HTTP 客户端

测试前端 HTTP/SSE 客户端
"""
import pytest


class TestHTTPClientInterface:
    """测试 HTTP 客户端接口"""

    def test_client_has_start_method(self):
        """测试客户端有 startGame 方法"""
        from backend.http_client import TetrisHTTPClient
        assert hasattr(TetrisHTTPClient, 'start_game')

    def test_client_has_stop_method(self):
        """测试客户端有 stopGame 方法"""
        from backend.http_client import TetrisHTTPClient
        assert hasattr(TetrisHTTPClient, 'stop_game')

    def test_client_has_get_state_method(self):
        """测试客户端有 getState 方法"""
        from backend.http_client import TetrisHTTPClient
        assert hasattr(TetrisHTTPClient, 'get_state')

    def test_client_has_connect_sse_method(self):
        """测试客户端有 connectSSE 方法"""
        from backend.http_client import TetrisHTTPClient
        assert hasattr(TetrisHTTPClient, 'connect_sse')

    def test_client_has_disconnect_method(self):
        """测试客户端有 disconnect 方法"""
        from backend.http_client import TetrisHTTPClient
        assert hasattr(TetrisHTTPClient, 'disconnect')

    def test_client_has_get_status_method(self):
        """测试客户端有 getStatus 方法"""
        from backend.http_client import TetrisHTTPClient
        assert hasattr(TetrisHTTPClient, 'get_status')


class TestHTTPClientCallbacks:
    """测试 HTTP 客户端回调"""

    def test_client_has_on_game_state_callback(self):
        """测试客户端有 onGameState 回调"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()
        assert hasattr(client, 'on_game_state')
        assert callable(client.on_game_state)

    def test_client_has_on_game_over_callback(self):
        """测试客户端有 onGameOver 回调"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()
        assert hasattr(client, 'on_game_over')
        assert callable(client.on_game_over)

    def test_client_has_on_error_callback(self):
        """测试客户端有 onError 回调"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()
        assert hasattr(client, 'on_error')
        assert callable(client.on_error)

    def test_client_has_on_connect_callback(self):
        """测试客户端有 onConnect 回调"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()
        assert hasattr(client, 'on_connect')
        assert callable(client.on_connect)

    def test_client_has_on_disconnect_callback(self):
        """测试客户端有 onDisconnect 回调"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()
        assert hasattr(client, 'on_disconnect')
        assert callable(client.on_disconnect)


class TestHTTPClientIntegration:
    """测试 HTTP 客户端集成"""

    @pytest.mark.asyncio
    async def test_start_game_sends_post_request(self):
        """测试 startGame 发送 POST 请求"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient(base_url="http://test")

        # 直接测试方法存在且可调用
        assert hasattr(client, 'start_game')
        assert callable(client.start_game)

        # 由于需要真实服务器，标记为集成测试
        pytest.skip("Integration test - requires running server")

    @pytest.mark.asyncio
    async def test_get_state_sends_get_request(self):
        """测试 getState 发送 GET 请求"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient(base_url="http://test")

        # 直接测试方法存在且可调用
        assert hasattr(client, 'get_state')
        assert callable(client.get_state)

        # 由于需要真实服务器，标记为集成测试
        pytest.skip("Integration test - requires running server")


class TestSSEParser:
    """测试 SSE 消息解析"""

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

    def test_parse_event_line(self):
        """测试解析 event 行"""
        from backend.http_client import TetrisHTTPClient

        # event 行不应该被解析为数据
        result = TetrisHTTPClient._parse_sse_line("event: game_state")
        assert result is None


class TestHTTPClientReconnection:
    """测试 HTTP 客户端重连机制"""

    def test_client_has_reconnect_attribute(self):
        """测试客户端有重连属性"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()
        assert hasattr(client, 'reconnect')
        assert hasattr(client, 'reconnect_delay')

    def test_client_has_max_reconnect_attempts(self):
        """测试客户端有最大重连次数"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()
        assert hasattr(client, 'max_reconnect_attempts')

    def test_client_default_values(self):
        """测试客户端默认值"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient()

        assert client.reconnect is True
        assert client.reconnect_delay == 1.0
        assert client.max_reconnect_attempts == 5
        assert client._reconnect_count == 0

    def test_client_custom_values(self):
        """测试客户端自定义值"""
        from backend.http_client import TetrisHTTPClient
        client = TetrisHTTPClient(
            base_url="http://custom:8080",
            reconnect=False,
            reconnect_delay=2.0,
            max_reconnect_attempts=10
        )

        assert client.base_url == "http://custom:8080"
        assert client.reconnect is False
        assert client.reconnect_delay == 2.0
        assert client.max_reconnect_attempts == 10


class TestHTTPClientMessageHandling:
    """测试 HTTP 客户端消息处理"""

    def test_handle_game_state_message(self):
        """测试处理游戏状态消息"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        callback_data = []

        def on_state(data):
            callback_data.append(data)

        client.on_game_state = on_state

        # 模拟消息
        data = {"type": "game_state", "tick": 100, "players": []}
        client._handle_message(data)

        assert len(callback_data) == 1
        assert callback_data[0] == data

    def test_handle_game_over_message(self):
        """测试处理游戏结束消息"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        callback_data = []

        def on_over(data):
            callback_data.append(data)

        client.on_game_over = on_over

        # 模拟消息
        data = {"type": "game_over", "winner": 0, "final_scores": [100, 50, 0]}
        client._handle_message(data)

        assert len(callback_data) == 1
        assert callback_data[0]["winner"] == 0

    def test_handle_error_message(self):
        """测试处理错误消息"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        callback_data = []

        def on_err(msg):
            callback_data.append(msg)

        client.on_error = on_err

        # 模拟消息
        data = {"type": "error", "error": "Something went wrong"}
        client._handle_message(data)

        assert len(callback_data) == 1
        assert "Something went wrong" in callback_data[0]

    def test_handle_ping_message(self):
        """测试处理心跳消息"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()

        # 设置回调确保不被调用
        client.on_game_state = lambda d: pytest.fail("Should not be called for ping")
        client.on_game_over = lambda d: pytest.fail("Should not be called for ping")

        # ping 消息应该被忽略
        data = {"type": "ping", "tick": 100}
        client._handle_message(data)  # 不应该抛出异常


class TestHTTPClientConvenienceMethods:
    """测试 HTTP 客户端便捷方法"""

    def test_start_method_alias(self):
        """测试 start 方法别名"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        assert hasattr(client, 'start')
        assert callable(client.start)

    def test_stop_method_alias(self):
        """测试 stop 方法别名"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        assert hasattr(client, 'stop')
        assert callable(client.stop)

    def test_connect_method_alias(self):
        """测试 connect 方法别名"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        assert hasattr(client, 'connect')
        assert callable(client.connect)

    def test_disconnect_method_alias(self):
        """测试 disconnect 方法别名"""
        from backend.http_client import TetrisHTTPClient

        client = TetrisHTTPClient()
        assert hasattr(client, 'disconnect')
        assert callable(client.disconnect)