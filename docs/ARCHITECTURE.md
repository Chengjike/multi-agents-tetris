# 三AI对战俄罗斯方块 - 技术架构文档

## 项目概述

这是一个网页游戏，三个 AI Agent 各自控制一个俄罗斯方块实例进行对战。核心规则：当任意玩家一次消除 4 行时，立即在其他两个玩家的板子最底部随机增加一行障碍（留一个缺口）。最终根据存活时间或得分判定胜负。

## 技术架构

### 后端
- **FastAPI** - HTTP API 服务
- **Python asyncio** - 异步处理
- **SSE (Server-Sent Events)** - 实时状态推送

### 前端
- **HTML + JavaScript** - 页面渲染
- **Canvas** - 游戏绘制
- **EventSource API** - 接收实时状态

## 项目结构

```
.
├── backend/
│   ├── main.py              # FastAPI 应用入口
│   ├── http_client.py      # HTTP 客户端
│   ├── game/
│   │   ├── game_manager.py    # 游戏管理器
│   │   ├── tetris.py          # 俄罗斯方块核心逻辑
│   │   ├── board.py           # 棋盘实现
│   │   ├── piece.py          # 方块定义
│   │   ├── punishment.py     # 惩罚机制
│   │   └── game_experience.py # 游戏经验知识库
│   ├── agents/
│   │   └── rule_agent.py     # 基于规则的AI
│   └── protocol/
│       └── messages.py      # 消息协议
├── frontend/
│   ├── index.html          # 主页面
│   ├── js/
│   │   ├── main.js         # 主程序
│   │   ├── http-client.js  # HTTP客户端
│   │   └── game-renderer.js # 游戏渲染器
│   └── css/
│       └── style.css       # 样式
├── tests/                   # 测试用例
├── docker-compose.yml       # Docker 配置
└── nginx.conf              # Nginx 配置
```

## 核心模块

### 1. 游戏引擎 (backend/game/)

#### TetrisGame
- 俄罗斯方块核心逻辑
- 方块生成、下落、移动、旋转
- 行消除检测与计分

#### Board
- 20x10 棋盘实现
- 高度计算、碰撞检测
- 行消除（clear_lines）

#### Piece
- 7种标准方块类型（I, J, L, O, S, T, Z）
- 4种旋转状态

#### GameManager
- 游戏主循环
- 多玩家管理
- 惩罚机制协调

### 2. AI Agent (backend/agents/)

#### RuleAgent
基于启发式评估函数的AI：

**评估指标：**
- 高度（WEIGHT_HEIGHT = -0.5）
- 空洞数（WEIGHT_HOLES = -3.0）
- 不平整度（WEIGHT_BUMPINESS = -0.3）
- 消除行数（WEIGHT_LINES = 1000）
- 完成行奖励（WEIGHT_COMPLETE_LINE = 500）
- 井惩罚（WEIGHT_WELL = -50）
- 列填充率（WEIGHT_COLUMN_FILL = 20）

**决策流程：**
1. 计算最佳落点位置
2. 优先旋转到最佳角度
3. 移动到最佳位置
4. 软降（慢速下落）

### 3. 惩罚机制 (backend/game/punishment.py)

- 累积消除行数
- 每累积4行触发惩罚
- 在其他玩家棋盘底部添加障碍行（留缺口）

### 4. 游戏经验知识库 (backend/game/game_experience.py)

记录已发现的问题和解决方案，供后续参考。

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/game/start` | POST | 开始游戏 |
| `/api/game/stop` | POST | 停止游戏 |
| `/api/game/restart` | POST | 重新开始 |
| `/api/game/state` | GET | 获取游戏状态 |
| `/api/game/status` | GET | 获取简化状态 |
| `/api/game/sse` | GET | SSE 实时推送 |
| `/api/experience` | GET | 获取游戏经验 |

## 前端渲染

### GameRenderer
- 棋盘绘制
- 方块渲染（带3D效果）
- 消除行闪烁动画
- 下一个方块预览

### 动画效果
- 方块下落动画
- 消除行闪烁（4次）
- 3D 单元格效果

## 部署

### 本地开发
```bash
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8080
```

### Docker 部署
```bash
docker-compose up -d
```

## 游戏规则

1. **基本规则**：标准俄罗斯方块玩法
2. **惩罚机制**：任意玩家一次消除4行时，其他玩家底部增加障碍行
3. **结束条件**：任何一列高度达到20（方块到顶）
4. **胜负判定**：存活到最后（高度未到顶）或得分最高

## 已知问题与修复

1. ~~高度计算错误~~ - 已修复（从顶部计算改为从底部计算）
2. ~~AI不旋转~~ - 已修复（简化决策逻辑）
3. ~~游戏结束检测~~ - 已修复（任何一列到顶就结束）
4. ~~消除动画时序~~ - 已修复（消除前记录待消除行）

## 许可证

MIT