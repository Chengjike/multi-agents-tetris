# 三AI对战俄罗斯方块

## 项目概述

网页游戏，三个 AI Agent 各自控制一个俄罗斯方块实例进行对战。核心规则：当任意玩家一次消除 4 行时，立即在其他两个玩家的板子最底部随机增加一行障碍（留一个缺口）。最终根据存活时间或得分判定胜负。

## 技术架构

### 后端
- **FastAPI** - HTTP API 服务
- **Python asyncio** - 异步处理
- **SSE (Server-Sent Events)** - 实时状态推送

### 前端
- **HTML + JavaScript** - 页面渲染
- **Canvas** - 游戏绘制
- **EventSource API** - 接收实时状态

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/game/start` | POST | 开始游戏 |
| `/api/game/stop` | POST | 停止游戏 |
| `/api/game/state` | GET | 获取游戏状态 |
| `/api/game/status` | GET | 获取简化状态 |
| `/api/game/sse` | GET | SSE 实时推送 |

## 快速开始

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端服务
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload

# 访问前端
# 浏览器打开 http://localhost:8080
```

### Docker 部署

```bash
# 构建并运行
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 测试

```bash
# 运行所有测试
pytest

# 运行带覆盖率
pytest --cov=backend
```

## 部署说明

- **后端端口**: 8080（与现有服务 3000 端口完全分离）
- **不影响现有服务**: 端口隔离验证通过

## 项目结构

```
.
├── backend/
│   ├── main.py          # FastAPI 应用
│   ├── http_client.py   # HTTP 客户端
│   ├── game/            # 游戏逻辑
│   ├── agents/          # AI Agent
│   └── protocol/        # 消息协议
├── frontend/
│   ├── index.html       # 主页面
│   ├── js/              # JavaScript
│   └── css/             # 样式
├── tests/               # 测试用例
├── docker-compose.yml   # Docker 配置
└── nginx.conf           # Nginx 配置
```

## License

MIT