"""
HTTP + SSE 客户端

替代 WebSocket 的 HTTP API 客户端
"""
import json
import asyncio
from typing import Optional, Callable, Dict
import aiohttp


class TetrisHTTPClient:
    """俄罗斯方块 HTTP 客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_reconnect_attempts: int = 5,
    ):
        self.base_url = base_url
        self.reconnect = reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        # 回调函数
        self.on_game_state: Callable[[Dict], None] = lambda state: None
        self.on_game_over: Callable[[Dict], None] = lambda data: None
        self.on_error: Callable[[str], None] = lambda error: None
        self.on_connect: Callable[[], None] = lambda: None
        self.on_disconnect: Callable[[], None] = lambda: None

        # 内部状态
        self._session: Optional[aiohttp.ClientSession] = None
        self._sse_task: Optional[asyncio.Task] = None
        self._connected = False
        self._reconnect_count = 0

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """确保 session 存在"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def start_game(self) -> Dict:
        """开始游戏"""
        session = await self._ensure_session()
        async with session.post(f"{self.base_url}/api/game/start") as response:
            response.raise_for_status()
            return await response.json()

    async def stop_game(self) -> Dict:
        """停止游戏"""
        session = await self._ensure_session()
        async with session.post(f"{self.base_url}/api/game/stop") as response:
            response.raise_for_status()
            return await response.json()

    async def get_state(self) -> Dict:
        """获取游戏状态"""
        session = await self._ensure_session()
        async with session.get(f"{self.base_url}/api/game/state") as response:
            response.raise_for_status()
            return await response.json()

    async def get_status(self) -> Dict:
        """获取简化游戏状态"""
        session = await self._ensure_session()
        async with session.get(f"{self.base_url}/api/game/status") as response:
            response.raise_for_status()
            return await response.json()

    async def connect_sse(self) -> None:
        """连接 SSE 端点"""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        self._connected = True
        self.on_connect()

        # 启动 SSE 监听任务
        self._sse_task = asyncio.create_task(self._listen_sse())

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False

        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass

        if self._session:
            await self._session.close()
            self._session = None

        self.on_disconnect()

    async def _listen_sse(self) -> None:
        """监听 SSE 消息"""
        while self._connected:
            try:
                async with self._session.get(
                    f"{self.base_url}/api/game/sse"
                ) as response:
                    response.raise_for_status()

                    async for line in response.content:
                        line = line.decode('utf-8').strip()

                        if not line:
                            continue

                        data = self._parse_sse_line(line)
                        if data:
                            self._handle_message(data)

            except asyncio.CancelledError:
                break
            except aiohttp.ClientError as e:
                self.on_error(f"SSE connection error: {e}")
                if self.reconnect and self._reconnect_count < self.max_reconnect_attempts:
                    self._reconnect_count += 1
                    await asyncio.sleep(self.reconnect_delay)
                    continue
                break
            except Exception as e:
                self.on_error(f"Unexpected error: {e}")
                break

        self._connected = False

    def _handle_message(self, data: Dict) -> None:
        """处理接收到的消息"""
        msg_type = data.get("type")

        if msg_type == "game_state":
            self.on_game_state(data)
        elif msg_type == "game_over":
            self.on_game_over(data)
        elif msg_type == "error":
            self.on_error(data.get("error", "Unknown error"))
        elif msg_type == "ping":
            # 心跳消息，忽略
            pass

    @staticmethod
    def _parse_sse_line(line: str) -> Optional[Dict]:
        """解析 SSE 行"""
        # SSE 格式: "data: {json}"
        if not line.startswith("data: "):
            return None

        data_str = line[6:]  # 移除 "data: " 前缀

        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            return None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()

    # ========== 便捷方法（兼容 WebSocket API）==========

    async def start(self):
        """开始游戏（兼容 WebSocket API）"""
        return await self.start_game()

    async def stop(self):
        """停止游戏（兼容 WebSocket API）"""
        return await self.stop_game()

    def connect(self):
        """连接 SSE（兼容 WebSocket API）"""
        self.connect_sse()


# 导出
__all__ = ["TetrisHTTPClient"]