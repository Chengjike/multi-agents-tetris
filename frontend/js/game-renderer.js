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
    }

    render(canvas, gameState) {
        const ctx = canvas.getContext('2d');
        const board = gameState.board;
        const currentPiece = gameState.current_piece;

        // 清空画布
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 绘制棋盘
        if (board) {
            for (let y = 0; y < board.length; y++) {
                for (let x = 0; x < board[y].length; x++) {
                    if (board[y][x]) {
                        this._drawCell(ctx, x, y, '#444');
                    }
                }
            }
        }

        // 绘制当前方块
        if (currentPiece && currentPiece.type) {
            const pieceType = currentPiece.type;
            const color = this.colors[pieceType] || '#fff';
            const x = currentPiece.x;
            const y = currentPiece.y;
            const rotation = currentPiece.rotation || 0;

            const cells = this._getPieceCells(pieceType, rotation);
            cells.forEach(([dx, dy]) => {
                this._drawCell(ctx, x + dx, y + dy, color);
            });
        }

        // 绘制网格线
        this._drawGrid(ctx, canvas.width, canvas.height);
    }

    _drawCell(ctx, x, y, color) {
        const px = x * this.cellSize;
        const py = y * this.cellSize;

        ctx.fillStyle = color;
        ctx.fillRect(px, py, this.cellSize - 1, this.cellSize - 1);

        // 添加高光效果
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.fillRect(px, py, this.cellSize - 1, 2);
        ctx.fillRect(px, py, 2, this.cellSize - 1);
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