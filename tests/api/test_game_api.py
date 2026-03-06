"""
测试用例：游戏 REST API

测试 HTTP API 端点
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


class TestGameAPI:
    """测试游戏 API"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_start_game(self, client):
        """测试开始游戏 API"""
        response = await client.post("/api/game/start")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "game_state"
        assert data["game_status"] == "running"

    @pytest.mark.asyncio
    async def test_stop_game(self, client):
        """测试停止游戏 API"""
        # 先开始游戏
        await client.post("/api/game/start")

        # 停止游戏
        response = await client.post("/api/game/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["game_status"] in ["paused", "stopped"]

    @pytest.mark.asyncio
    async def test_get_game_state(self, client):
        """测试获取游戏状态 API"""
        response = await client.get("/api/game/state")
        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        assert "game_status" in data

    @pytest.mark.asyncio
    async def test_get_game_status(self, client):
        """测试获取游戏状态简化版 API"""
        response = await client.get("/api/game/status")
        assert response.status_code == 200
        data = response.json()
        assert "game_status" in data
        assert "tick" in data


class TestGameAPIIntegration:
    """测试游戏 API 集成"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_game_lifecycle(self, client):
        """测试游戏完整生命周期"""
        # 初始状态
        response = await client.get("/api/game/state")
        assert response.status_code == 200

        # 开始游戏
        response = await client.post("/api/game/start")
        assert response.status_code == 200

        # 获取运行中状态
        response = await client.get("/api/game/state")
        data = response.json()
        assert data["game_status"] == "running"

        # 停止游戏
        response = await client.post("/api/game/stop")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_multiple_players_state(self, client):
        """测试多玩家状态"""
        response = await client.get("/api/game/state")
        data = response.json()
        assert len(data["players"]) == 3
        for i, player in enumerate(data["players"]):
            assert player["player_id"] == i


class TestGameAPIResponseFormat:
    """测试 API 响应格式"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_game_state_has_required_fields(self, client):
        """测试游戏状态包含必需字段"""
        response = await client.get("/api/game/state")
        data = response.json()

        # 检查必需字段
        assert "type" in data
        assert "players" in data
        assert "game_status" in data
        assert "tick" in data

    @pytest.mark.asyncio
    async def test_player_state_has_required_fields(self, client):
        """测试玩家状态包含必需字段"""
        response = await client.get("/api/game/state")
        data = response.json()

        for player in data["players"]:
            assert "player_id" in player
            assert "board" in player
            assert "score" in player
            assert "status" in player

    @pytest.mark.asyncio
    async def test_status_endpoint_minimal_response(self, client):
        """测试状态端点返回最小响应"""
        response = await client.get("/api/game/status")
        data = response.json()

        # 验证只有两个字段
        assert set(data.keys()) == {"game_status", "tick"}


class TestGameAPIErrorHandling:
    """测试 API 错误处理"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, client):
        """测试无效端点"""
        response = await client.get("/api/game/invalid")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_twice(self, client):
        """测试连续开始两次游戏"""
        # 第一次开始
        response = await client.post("/api/game/start")
        assert response.status_code == 200

        # 第二次开始（应该仍然运行）
        response = await client.post("/api/game/start")
        assert response.status_code == 200
        data = response.json()
        assert data["game_status"] == "running"

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, client):
        """测试游戏未运行时停止"""
        # 确保游戏未运行
        response = await client.post("/api/game/stop")
        assert response.status_code == 200