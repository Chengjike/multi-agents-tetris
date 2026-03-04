"""
WebSocket + HTTP API 服务器

运行游戏主循环和WebSocket服务
支持 HTTP REST API 和 SSE
"""
import asyncio
import json
import logging
import ssl
from typing import Set, Optional
from contextlib import asynccontextmanager
import aiohttp
from aiohttp import web

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from backend.game.game_manager import GameManager
from backend.protocol.messages import parse_message, create_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局游戏管理器
_game_manager: Optional[GameManager] = None
_sse_queue: Optional[asyncio.Queue] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _game_manager, _sse_queue

    # 初始化游戏管理器和SSE队列
    _game_manager = GameManager(tick_interval=0.1)
    _sse_queue = asyncio.Queue()

    # 启动游戏循环
    asyncio.create_task(game_loop_with_sse())

    yield

    # 清理
    if _game_manager:
        _game_manager.stop_game()


async def game_loop_with_sse():
    """游戏循环（带SSE推送）"""
    global _game_manager, _sse_queue

    while True:
        if _game_manager and _game_manager.running:
            _game_manager.tick()

            # 每10个tick推送一次状态
            if _game_manager.tick_count % 10 == 0:
                state = _game_manager.get_broadcast_state()
                await _sse_queue.put(state)

                # 检查游戏结束
                if _game_manager.check_all_game_over():
                    game_over = {
                        'type': 'game_over',
                        'winner': _game_manager.get_winner(),
                        'final_scores': _game_manager.get_final_scores(),
                    }
                    await _sse_queue.put(game_over)
                    logger.info('Game over')

        await asyncio.sleep(0.1)


# FastAPI 应用
app = FastAPI(title="Multi-Agents Tetris API", lifespan=lifespan)


# ========== REST API 端点 ==========

def get_game_manager() -> GameManager:
    """获取游戏管理器（如果不存在则创建）"""
    global _game_manager
    if _game_manager is None:
        _game_manager = GameManager(tick_interval=0.1)
    return _game_manager


@app.post("/api/game/start")
async def start_game():
    """开始游戏"""
    global _game_manager
    gm = get_game_manager()
    if not gm.running:
        gm.start_game()
        logger.info('Game started via REST API')
    return gm.get_broadcast_state()


@app.post("/api/game/stop")
async def stop_game():
    """停止游戏"""
    global _game_manager
    gm = get_game_manager()
    if gm.running:
        gm.stop_game()
        logger.info('Game stopped via REST API')
    return gm.get_broadcast_state()


@app.get("/api/game/state")
async def get_game_state():
    """获取完整游戏状态"""
    gm = get_game_manager()
    return gm.get_broadcast_state()


@app.get("/api/game/status")
async def get_game_status():
    """获取简化游戏状态"""
    gm = get_game_manager()
    state = gm.get_broadcast_state()
    return {
        "game_status": state["game_status"],
        "tick": state["tick"],
    }


# ========== SSE 端点 ==========

@app.get("/api/game/sse")
async def game_sse(request: Request):
    """SSE 端点 - 推送游戏状态"""
    global _sse_queue

    gm = get_game_manager()
    if _sse_queue is None:
        _sse_queue = asyncio.Queue()

    async def event_generator():
        # 发送初始状态
        initial_state = gm.get_broadcast_state()
        yield {
            "event": "game_state",
            "data": json.dumps(initial_state)
        }

        while True:
            # 检查客户端断开
            if await request.is_disconnected():
                break

            try:
                # 等待新状态（超时1秒）
                state = await asyncio.wait_for(_sse_queue.get(), timeout=1.0)
                yield {
                    "event": "game_state",
                    "data": json.dumps(state)
                }
            except asyncio.TimeoutError:
                # 发送心跳
                yield {
                    "event": "ping",
                    "data": json.dumps({"tick": gm.tick_count})
                }
            except Exception as e:
                logger.error(f"SSE error: {e}")
                break

    return EventSourceResponse(event_generator())


# ========== 原有 WebSocket 服务器代码 ==========


class TetrisServer:
    """俄罗斯方块WebSocket服务器"""

    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 8080,
        tick_interval: float = 0.1,
        ssl_cert: str = None,
        ssl_key: str = None,
        wss_port: int = None,
    ):
        self.host = host
        self.port = port
        self.tick_interval = tick_interval
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.wss_port = wss_port or 443  # 默认 443

        self.app = web.Application()
        self.game_manager = GameManager(tick_interval=tick_interval)

        # WebSocket 客户端集合
        self.websockets: Set[web.WebSocketResponse] = set()

        # 设置路由
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/{path:.*}', self.static_handler)

        # 启动游戏循环
        self._game_task: Optional[asyncio.Task] = None

    async def index_handler(self, request: web.Request) -> web.Response:
        """主页处理器 - 服务前端静态文件"""
        import os
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        index_path = os.path.join(frontend_path, 'index.html')
        
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return web.Response(text=content, content_type='text/html')
        
        return web.Response(
            text='<h1>Multi-Agents Tetris Server</h1><p>Connect to /ws for WebSocket</p>',
            content_type='text/html',
        )

    async def static_handler(self, request: web.Request) -> web.Response:
        """静态文件处理器"""
        import os
        import mimetypes
        
        # 获取请求路径并防止路径遍历
        path = request.match_info.get('path', '')
        if '..' in path or path.startswith('/'):
            return web.Response(status=404)
        
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        file_path = os.path.join(frontend_path, path)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            with open(file_path, 'rb') as f:
                content = f.read()
            return web.Response(body=content, content_type=content_type)
        
        return web.Response(status=404)

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

            elif msg.type == 'stop':
                # 停止游戏
                if self.game_manager.running:
                    self.game_manager.stop_game()
                    logger.info('Game stopped')
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

        # 启动WebSocket服务器 (同时支持 WS 和 WSS)
        runner = web.AppRunner(self.app)
        await runner.setup()

        # WS (未加密) - 用于 HTTP 前端
        site_ws = web.TCPSite(runner, self.host, self.port)
        await site_ws.start()
        logger.info(f'Server started on ws://{self.host}:{self.port}')

        # WSS (加密) - 用于 HTTPS 前端或代理环境
        if self.ssl_cert and self.ssl_key:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)
            site_wss = web.TCPSite(runner, self.host, self.wss_port, ssl_context=ssl_context)
            await site_wss.start()
            logger.info(f'Server started on wss://{self.host}:{self.wss_port}')

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
    import os

    parser = argparse.ArgumentParser(description='Multi-Agents Tetris Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind (WS)')
    parser.add_argument('--tick-interval', type=float, default=0.1, help='Tick interval in seconds')
    parser.add_argument('--ssl-cert', default=os.getenv('SSL_CERT'), help='SSL certificate file')
    parser.add_argument('--ssl-key', default=os.getenv('SSL_KEY'), help='SSL key file')
    parser.add_argument('--wss-port', type=int, default=8766, help='Port for WSS (encrypted)')

    args = parser.parse_args()

    server = TetrisServer(
        host=args.host,
        port=args.port,
        tick_interval=args.tick_interval,
        ssl_cert=args.ssl_cert,
        ssl_key=args.ssl_key,
        wss_port=args.wss_port,
    )

    asyncio.run(server.run_forever())


if __name__ == '__main__':
    main()