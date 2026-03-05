/**
 * 游戏渲染器
 */
class GameRenderer {
    constructor() {
        this.cellSize = 20; // 每个格子的大小
        this.colors = {
            'I': '#00ffff',
            'J': '#0000ff',
            'L': '#ffa500',
            'O': '#ffff00',
            'S': '#00ff00',
            'T': '#800080',
            'Z': '#ff0000',
            'filled': '#444',
        };
        // 闪烁效果相关
        this.flashLines = []; // 要闪烁消除的行
        this.flashCount = {}; // 每行的闪烁计数
        
        // 动画相关 - 为每个玩家保存状态
        this.playerStates = {}; // { playerId: { lastPiece, lastBoard, animatingPiece } }
        this.animationFrameId = null;
    }

    // 获取或创建玩家状态
    _getPlayerState(playerId) {
        if (!this.playerStates[playerId]) {
            this.playerStates[playerId] = {
                lastPiece: null,
                lastBoard: null,
                animatingPiece: null, // 当前动画中的方块
                animationProgress: 1, // 动画进度 0-1
            };
        }
        return this.playerStates[playerId];
    }

    render(canvas, gameState) {
        const ctx = canvas.getContext('2d');
        const playerId = gameState.player_id;
        const board = gameState.board;
        const currentPiece = gameState.current_piece;
        
        // 获取玩家状态
        const state = this._getPlayerState(playerId);
        
        // 检测方块变化并启动动画
        let drawPiece = currentPiece;
        if (currentPiece && currentPiece.type) {
            if (state.lastPiece && state.lastPiece.type === currentPiece.type) {
                // 方块类型相同，检测位置变化
                const dx = currentPiece.x - state.lastPiece.x;
                const dy = currentPiece.y - state.lastPiece.y;
                
                // 如果有移动，启动动画
                if ((Math.abs(dx) > 0 || Math.abs(dy) > 0) && state.animationProgress >= 1) {
                    // 开始新动画：从上次位置移动到当前位置
                    state.animatingPiece = {
                        ...state.lastPiece,
                        targetX: currentPiece.x,
                        targetY: currentPiece.y,
                        startX: state.lastPiece.x,
                        startY: state.lastPiece.y,
                    };
                    state.animationProgress = 0;
                }
                
                // 如果有进行中的动画，使用插值
                if (state.animatingPiece && state.animationProgress < 1) {
                    // 缓动函数
                    const t = this._easeOutQuad(state.animationProgress);
                    drawPiece = {
                        ...currentPiece,
                        x: state.animatingPiece.startX + (state.animatingPiece.targetX - state.animatingPiece.startX) * t,
                        y: state.animatingPiece.startY + (state.animatingPiece.targetY - state.animatingPiece.startY) * t,
                    };
                }
            }
            
            // 更新上次状态
            state.lastPiece = { ...currentPiece };
        }

        // 清空画布
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 绘制棋盘（处理闪烁效果）
        if (board) {
            for (let y = 0; y < board.length; y++) {
                // 检查这行是否需要闪烁
                if (this.flashLines.includes(y)) {
                    // 闪烁效果：交替显示白色和原色
                    const flashOn = Math.floor(this.flashCount[y] / 5) % 2 === 0;
                    for (let x = 0; x < board[y].length; x++) {
                        if (board[y][x]) {
                            this._drawCell(ctx, x, y, flashOn ? '#ffffff' : '#444', true);
                        }
                    }
                } else {
                    for (let x = 0; x < board[y].length; x++) {
                        if (board[y][x]) {
                            this._drawCell(ctx, x, y, '#444', false);
                        }
                    }
                }
            }
        }

        // 绘制当前方块（带3D效果）
        if (drawPiece && drawPiece.type) {
            const pieceType = drawPiece.type;
            const color = this.colors[pieceType] || '#fff';
            const x = Math.round(drawPiece.x); // 取整用于绘制
            const y = Math.round(drawPiece.y);
            const rotation = drawPiece.rotation || 0;

            const cells = this._getPieceCells(pieceType, rotation);
            cells.forEach(([dx, dy]) => {
                this._drawCell3D(ctx, x + dx, y + dy, color);
            });
        }

        // 绘制网格线
        this._drawGrid(ctx, canvas.width, canvas.height);
        
        // 更新动画进度
        if (state.animationProgress < 1) {
            state.animationProgress += 0.2; // 动画速度
            if (state.animationProgress >= 1) {
                state.animationProgress = 1;
                state.animatingPiece = null;
            }
        }
    }
    
    // 缓动函数
    _easeOutQuad(t) {
        return t * (2 - t);
    }

    // 3D 效果的单元格绘制
    _drawCell3D(ctx, x, y, color) {
        console.log('_drawCell3D called with x:', x, 'y:', y, 'color:', color, 'cellSize:', this.cellSize);
        const px = x * this.cellSize;
        const py = y * this.cellSize;
        const size = this.cellSize - 1;

        console.log('Drawing at px:', px, 'py:', py, 'size:', size);

        // 主体颜色
        ctx.fillStyle = color;
        ctx.fillRect(px, py, size, size);
        
        // 顶部高光（左上角）
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.beginPath();
        ctx.moveTo(px, py + size);
        ctx.lineTo(px, py);
        ctx.lineTo(px + size, py);
        ctx.lineTo(px + size - 3, py + 3);
        ctx.lineTo(px + 3, py + 3);
        ctx.lineTo(px, py + size);
        ctx.fill();
        
        // 右侧阴影（右下角）
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.beginPath();
        ctx.moveTo(px + size, py);
        ctx.lineTo(px + size, py + size);
        ctx.lineTo(px, py + size);
        ctx.lineTo(px + 3, py + size - 3);
        ctx.lineTo(px + 3, py + 3);
        ctx.lineTo(px + size - 3, py + 3);
        ctx.fill();
        
        // 底部暗面
        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.fillRect(px + 3, py + size - 3, size - 3, 3);
    }

    _drawCell(ctx, x, y, color, isFlashing = false) {
        const px = x * this.cellSize;
        const py = y * this.cellSize;

        ctx.fillStyle = color;
        ctx.fillRect(px, py, this.cellSize - 1, this.cellSize - 1);

        if (!isFlashing) {
            // 添加高光效果
            ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.fillRect(px, py, this.cellSize - 1, 2);
            ctx.fillRect(px, py, 2, this.cellSize - 1);
            
            // 添加简单的3D阴影
            ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
            ctx.fillRect(px + this.cellSize - 3, py + 2, 2, this.cellSize - 3);
            ctx.fillRect(px + 2, py + this.cellSize - 3, this.cellSize - 3, 2);
        }
    }

    // 设置闪烁行（消除前闪烁）
    setFlashLines(lines) {
        this.flashLines = lines;
        this.flashCount = {};
        lines.forEach(line => {
            this.flashCount[line] = 0;
        });
    }

    // 更新闪烁计数
    updateFlash() {
        this.flashLines.forEach(line => {
            this.flashCount[line]++;
        });
    }

    // 清除闪烁
    clearFlash() {
        this.flashLines = [];
        this.flashCount = {};
    }

    _drawGrid(ctx, width, height) {
        ctx.strokeStyle = '#222';
        ctx.lineWidth = 0.5;

        // 垂直线
        for (let x = 0; x <= width; x += this.cellSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }

        // 水平线
        for (let y = 0; y <= height; y += this.cellSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
    }

    _getPieceCells(type, rotation) {
        // 定义方块形状（相对于中心点）
        const shapes = {
            'I': [[0, 0], [-1, 0], [1, 0], [2, 0]],
            'J': [[-1, 0], [0, 0], [1, 0], [1, 1]],
            'L': [[-1, 0], [0, 0], [1, 0], [-1, 1]],
            'O': [[0, 0], [1, 0], [0, 1], [1, 1]],
            'S': [[0, 0], [1, 0], [-1, 1], [0, 1]],
            'T': [[-1, 0], [0, 0], [1, 0], [0, 1]],
            'Z': [[-1, 0], [0, 0], [0, 1], [1, 1]],
        };

        // 根据旋转返回对应的形状
        // 这里简化处理，返回原始形状
        return shapes[type] || [];
    }

    updateScore(element, score) {
        if (element) {
            element.textContent = score;
        }
    }

    updateStatus(element, status) {
        if (element) {
            element.textContent = status;
            element.className = 'status-text';
            if (status === 'alive') {
                element.classList.add('alive');
            } else if (status === 'dead') {
                element.classList.add('dead');
            }
        }
    }
}

// 导出
window.GameRenderer = GameRenderer;