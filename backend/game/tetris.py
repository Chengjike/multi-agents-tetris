"""
俄罗斯方块游戏核心（Tetris Game）

单个玩家实例的游戏逻辑
"""
from enum import Enum
from typing import Dict, Any, Optional, List

from backend.game.board import Board
from backend.game.piece import Piece


class GameStatus(Enum):
    """游戏状态枚举"""
    WAITING = "waiting"
    RUNNING = "running"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class PlayerAction(Enum):
    """玩家动作枚举"""
    MOVE_LEFT = "left"
    MOVE_RIGHT = "right"
    ROTATE = "rotate"
    SOFT_DROP = "soft_drop"  # 软下降（加速下落）
    HARD_DROP = "hard_drop"  # 硬下降（直接落到底）
    WAIT = "wait"  # 无操作


# 分数配置（消除行数 * 100）
SCORES = {
    1: 100,   # 消除1行
    2: 300,   # 消除2行
    3: 600,   # 消除3行
    4: 1000,  # 消除4行
}


class TetrisGame:
    """俄罗斯方块游戏类"""

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.board = Board()
        self.current_piece: Optional[Piece] = None
        self.next_piece: Optional[Piece] = None
        self.status = GameStatus.WAITING
        self.score = 0
        self.lines_cleared_total = 0
        self.prev_lines_cleared_total = 0  # 上次tick的累计消除行数
        self.last_cleared_rows: List[int] = []  # 最近消除的行号

        # 生成第一个方块
        self._generate_next_piece()

    def _generate_next_piece(self) -> None:
        """生成下一个方块"""
        if self.next_piece:
            self.current_piece = self.next_piece
        else:
            self.current_piece = Piece.random(x=3, y=-2)

        self.next_piece = Piece.random(x=3, y=-2)

    def start(self) -> None:
        """开始游戏"""
        if self.status == GameStatus.WAITING:
            self.status = GameStatus.RUNNING
            self._generate_next_piece()

    def spawn_new_piece(self) -> bool:
        """
        生成新方块

        Returns:
            True 表示成功，False 表示游戏结束
        """
        # 将当前方块放置到棋盘
        if self.current_piece:
            self.board.place_piece(self.current_piece)

        # 检查棋盘是否已满（游戏结束条件）- 超过90%就算满
        filled_cells = sum(sum(row) for row in self.board._grid)
        if filled_cells >= self.board.height * self.board.width * 0.9:
            print(f"Player {self.player_id}: game over - board is full ({filled_cells} cells)")
            self.status = GameStatus.GAME_OVER
            return False

        # 生成新方块
        self._generate_next_piece()

        # 检查新方块是否可以直接放置（游戏结束条件）
        if self.board.check_collision(self.current_piece):
            print(f"Player {self.player_id}: game over - new piece collides at start, piece={self.current_piece}")
            self.status = GameStatus.GAME_OVER
            return False

        return True

    def check_game_over(self) -> bool:
        """检查游戏是否结束 - 任何一列到达顶部就结束"""
        # 检查最高列是否到达顶部（高度=20表示满）
        height_map = self.board.get_height_map()
        if max(height_map) >= self.board.height:
            return True
        return False

    def perform_action(self, action: PlayerAction) -> bool:
        """
        执行玩家动作

        Args:
            action: 玩家动作

        Returns:
            True 表示动作成功执行
        """
        if self.status != GameStatus.RUNNING:
            return False

        if self.current_piece is None:
            return False

        piece = self.current_piece.clone()

        if action == PlayerAction.MOVE_LEFT:
            piece.x -= 1
            if not self.board.check_collision(piece):
                self.current_piece.x = piece.x
                return True

        elif action == PlayerAction.MOVE_RIGHT:
            piece.x += 1
            if not self.board.check_collision(piece):
                self.current_piece.x = piece.x
                return True

        elif action == PlayerAction.ROTATE:
            piece.rotate()
            if not self.board.check_collision(piece):
                self.current_piece.rotation = piece.rotation
                return True

        elif action == PlayerAction.SOFT_DROP:
            piece.y += 1
            if not self.board.check_collision(piece):
                self.current_piece.y = piece.y
                return True

        elif action == PlayerAction.HARD_DROP:
            # 硬下降：一直往下直到碰撞或超出棋盘
            while not self.board.check_collision(self.current_piece):
                self.current_piece.y += 1
                # 防止无限循环
                if self.current_piece.y > self.board.height + 10:
                    break

            # 回退一格
            self.current_piece.y -= 1

            # 确保方块在有效范围内
            if self.current_piece.y < 0:
                self.current_piece.y = 0

            # 放置方块并生成新的
            self.spawn_new_piece()
            # 处理消除
            self._process_line_clearing()
            return True

        elif action == PlayerAction.WAIT:
            return True

        return False

    def tick(self) -> None:
        """游戏主循环的一个tick"""
        if self.status != GameStatus.RUNNING:
            return

        if self.current_piece is None:
            return

        # 自动下落一格
        piece = self.current_piece.clone()
        piece.y += 1

        if not self.board.check_collision(piece):
            self.current_piece.y = piece.y
        else:
            # 碰撞了，标记方块已落地，等待 AI 执行 HARD_DROP
            # 不自动生成新方块，让 AI 决定动作
            pass

    def _process_line_clearing(self) -> int:
        """处理行消除

        Returns:
            消除的行号列表
        """
        cleared_rows = self.board.clear_lines()
        lines_count = len(cleared_rows)
        if lines_count > 0:
            self.lines_cleared_total += lines_count
            self.last_cleared_rows = cleared_rows  # 记录最近消除的行
            # 根据消除行数计算分数
            self.score += SCORES.get(lines_count, lines_count * 100)
        else:
            self.last_cleared_rows = []

        return cleared_rows

    def get_state(self) -> Dict[str, Any]:
        """获取游戏状态"""
        return {
            'player_id': self.player_id,
            'status': self.status.value,
            'score': self.score,
            'board': self.board.get_board_data(),
            'current_piece': {
                'type': self.current_piece.type.value if self.current_piece else None,
                'x': self.current_piece.x if self.current_piece else None,
                'y': self.current_piece.y if self.current_piece else None,
                'rotation': self.current_piece.rotation if self.current_piece else None,
                'color': self.current_piece.color if self.current_piece else None,
            } if self.current_piece else None,
            'next_piece': {
                'type': self.next_piece.type.value if self.next_piece else None,
            } if self.next_piece else None,
            'lines_cleared': self.lines_cleared_total,
            'last_cleared_rows': self.last_cleared_rows,  # 最近消除的行
        }

    def get_piece_at_bottom(self, piece: Piece) -> Piece:
        """
        获取方块下落到底部时的位置

        Args:
            piece: 要检查的方块

        Returns:
            落在底部后的方块副本
        """
        result = piece.clone()
        while not self.board.check_collision(result):
            result.y += 1
        result.y -= 1
        return result

    def evaluate_position(self, piece: Piece) -> Dict[str, int]:
        """
        评估给定方块位置的质量

        Args:
            piece: 要评估的方块

        Returns:
            评估指标字典
        """
        # 将方块放置到棋盘上（临时）
        temp_piece = piece.clone()
        temp_piece.y = 0  # 从顶部开始

        # 找到落底位置
        bottom_piece = self.get_piece_at_bottom(temp_piece)
        self.board.place_piece(bottom_piece)

        # 计算指标
        height_map = self.board.get_height_map()
        holes = self.board.get_holes()
        bumpiness = self.board.get_bumpiness()

        # 移除临时放置的方块
        for x, y in bottom_piece.get_cells():
            if 0 <= y < self.board.height:
                self.board.set_cell(x, y, 0)

        return {
            'max_height': max(height_map) if height_map else 0,
            'total_height': sum(height_map),
            'holes': holes,
            'bumpiness': bumpiness,
        }

    @classmethod
    def simulate_action(cls, board: Board, piece: Piece, action: PlayerAction) -> tuple:
        """
        模拟执行动作后的结果

        Args:
            board: 棋盘
            piece: 当前方块
            action: 要执行的动作

        Returns:
            (新棋盘, 得分变化, 是否消除行)
        """
        new_board = board.copy()
        test_piece = piece.clone()

        # 应用动作
        if action == PlayerAction.MOVE_LEFT:
            test_piece.x -= 1
        elif action == PlayerAction.MOVE_RIGHT:
            test_piece.x += 1
        elif action == PlayerAction.ROTATE:
            test_piece.rotate()
        elif action == PlayerAction.SOFT_DROP:
            test_piece.y += 1
        elif action == PlayerAction.HARD_DROP:
            # 硬降：一直往下直到碰撞或超出底部
            while not new_board.check_collision(test_piece):
                test_piece.y += 1
                # 防止无限循环（当方块在屏幕上方时）
                if test_piece.y > new_board.height + 10:
                    break
            test_piece.y -= 1

        # 检查碰撞
        if new_board.check_collision(test_piece):
            return board, 0, False

        # 放置方块
        new_board.place_piece(test_piece)

        # 消除行
        lines_cleared = new_board.clear_lines()
        score_change = SCORES.get(lines_cleared, 0)

        return new_board, score_change, lines_cleared > 0