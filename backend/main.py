"""
WebSocket 服务器

运行游戏主循环和WebSocket服务
"""
import asyncio
import json
import logging
from typing import Set, Optional
import aiohttp
from aiohttp import web

from backend.game.game_manager import GameManager
from backend.protocol.messages import parse_message, create_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TetrisServer:
    """俄罗斯方块WebSocket服务器"""

    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 8765,
        tick_interval: float = 0.1,
    ):
        self.host = host
        self.port = port
        self.tick_interval = tick_interval

        self.app = web.Application()
        self.game_manager = GameManager(tick_interval=tick_interval)

        # WebSocket 客户端集合
        self.websockets: Set[web.WebSocketResponse] = set()

        # 设置路由
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/', self.index_handler)

        # 启动游戏循环
        self._game_task: Optional[asyncio.Task] = None

    async def index_handler(self, request: web.Request) -> web.Response:
        """主页处理器"""
        return web.Response(
            text='<h1>Multi-Agents Tetris Server</h1><p>Connect to /ws for WebSocket</p>',
            content_type='text/html',
        )

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """WebSocket处理器"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websockets.add(ws)
        logger.info(f'Client connected. Total: {len(self.websockets)}')

        try:
            # 发送欢迎消息
            await ws.send_json({
                'type': 'welcome',
                'message': 'Connected to Multi-Agents Tetris Server',
            })

            # 广播当前游戏状态
            if self.game_manager.game_status.value == 'running':
                await self.broadcast_state()

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_message(ws, msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    break
        except Exception as e:
            logger.error(f'WebSocket handler error: {e}')
        finally:
            self.websockets.discard(ws)
            logger.info(f'Client disconnected. Total: {len(self.websockets)}')

        return ws

    async def handle_message(self, ws: web.WebSocketResponse, data: str) -> None:
        """处理客户端消息"""
        try:
            msg = parse_message(data)
            if msg is None:
                await ws.send_json(create_error('Invalid message format'))
                return

            if msg.type == 'start':
                # 开始游戏
                if not self.game_manager.running:
                    self.game_manager.start_game()
                    logger.info('Game started')
                    await self.broadcast_state()

            elif msg.type == 'action':
                # 玩家动作（目前由AI控制，客户端无法直接控制）
                await ws.send_json(create_error('Actions are controlled by AI'))

            elif msg.type == 'status':
                # 请求当前状态
                await ws.send_json(self.game_manager.get_broadcast_state())

            else:
                await ws.send_json(create_error(f'Unknown message type: {msg.type}'))

        except Exception as e:
            logger.error(f'Error handling message: {e}')
            await ws.send_json(create_error(str(e)))

    async def broadcast_state(self) -> None:
        """广播游戏状态给所有客户端"""
        if not self.websockets:
            return

        state = self.game_manager.get_broadcast_state()
        message = json.dumps(state)

        # 如果游戏结束，添加结束消息
        if self.game_manager.game_status.value == 'game_over':
            game_over = {
                'type': 'game_over',
                'winner': self.game_manager.get_winner(),
                'final_scores': self.game_manager.get_final_scores(),
            }
            message = json.dumps(game_over)

        # 广播给所有客户端
        for ws in list(self.websockets):
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.error(f'Error broadcasting to client: {e}')
                self.websockets.discard(ws)

    async def game_loop(self) -> None:
        """游戏主循环"""
        while True:
            if self.game_manager.running:
                self.game_manager.tick()

                # 每10个tick广播一次状态
                if self.game_manager.tick_count % 10 == 0:
                    await self.broadcast_state()

                # 检查游戏结束
                if self.game_manager.check_all_game_over():
                    await self.broadcast_state()
                    logger.info('Game over')
                    break

            await asyncio.sleep(self.tick_interval)

    async def start(self) -> None:
        """启动服务器"""
        # 启动游戏循环
        self._game_task = asyncio.create_task(self.game_loop())

        # 启动WebSocket服务器
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info(f'Server started on ws://{self.host}:{self.port}')

    async def run_forever(self) -> None:
        """运行服务器（阻塞）"""
        await self.start()

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info('Server stopped')
        finally:
            if self._game_task:
                self._game_task.cancel()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Agents Tetris Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    parser.add_argument('--port', type=int, default=8765, help='Port to bind')
    parser.add_argument('--tick-interval', type=float, default=0.1, help='Tick interval in seconds')

    args = parser.parse_args()

    server = TetrisServer(
        host=args.host,
        port=args.port,
        tick_interval=args.tick_interval,
    )

    asyncio.run(server.run_forever())


if __name__ == '__main__':
    main()