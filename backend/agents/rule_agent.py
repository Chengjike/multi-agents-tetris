"""
规则Agent（基于简单规则的AI）

使用评估函数选择最优落点
"""
from typing import Optional
from backend.game.tetris import TetrisGame, PlayerAction
from backend.game.piece import Piece


class RuleAgent:
    """基于规则的俄罗斯方块AI"""

    # 评估权重 - 优化目标：1.尽量多消除 2.尽快消除 3.给对手添麻烦
    WEIGHT_HEIGHT = -0.5      # 高度越低越好（降低权重）
    WEIGHT_HOLES = -3.0       # 空洞越少越好
    WEIGHT_BUMPINESS = -0.3   # 不平整度越低越好（降低权重）
    WEIGHT_LINES = 100.0      # 消除行越多越好（大幅提高权重）
    WEIGHT_COMPLETE_LINE = 50.0  # 完成一行（即将满的行）的奖励

    def __init__(self, player_id: int):
        self.player_id = player_id

    def decide(self, game: TetrisGame) -> PlayerAction:
        """
        决定最佳动作

        Args:
            game: 当前游戏实例

        Returns:
            最佳动作
        """
        if game.current_piece is None:
            return PlayerAction.WAIT

        # 始终获取最佳落点位置
        best_x, best_rotation, _ = self.get_best_position_and_rotation(game)

        # 如果当前位置/旋转不是最佳的，尝试调整
        if game.current_piece.rotation != best_rotation:
            # 尝试旋转
            test_rotated = game.current_piece.clone()
            test_rotated.rotate()
            if not game.board.check_collision(test_rotated):
                return PlayerAction.ROTATE

        if game.current_piece.x < best_x:
            # 尝试右移
            test_moved = game.current_piece.clone()
            test_moved.x += 1
            if not game.board.check_collision(test_moved):
                return PlayerAction.MOVE_RIGHT

        if game.current_piece.x > best_x:
            # 尝试左移
            test_moved = game.current_piece.clone()
            test_moved.x -= 1
            if not game.board.check_collision(test_moved):
                return PlayerAction.MOVE_LEFT

        # 如果位置和旋转都已优化，直接硬降
        return PlayerAction.HARD_DROP

    def _evaluate_board(self, board) -> float:
        """
        评估棋盘状态

        优化目标：
        1. 尽量多消除行（最高优先级）
        2. 尽快消除行（优先选择能快速消除的落点）
        3. 给对手添麻烦（通过惩罚系统实现）

        Args:
            board: 棋盘

        Returns:
            评估分数（越高越好）
        """
        height_map = board.get_height_map()
        holes = board.get_holes()
        bumpiness = board.get_bumpiness()

        # 计算总分
        total_height = sum(height_map)
        max_height = max(height_map)

        # 复制棋盘来测试消除行（不修改原始棋盘）
        test_board = board.copy()
        lines_cleared = test_board.clear_lines()

        # 计算即将完成行数（只差1-2个格子的行）
        near_complete_lines = 0
        for y, row in enumerate(board._grid):
            filled = sum(1 for cell in row if cell != 0)
            if 8 <= filled <= 9:  # 差1-2个格子就满了
                near_complete_lines += 1

        score = (
            self.WEIGHT_HEIGHT * total_height +
            self.WEIGHT_HOLES * holes +
            self.WEIGHT_BUMPINESS * bumpiness +
            self.WEIGHT_HEIGHT * max_height * 0.5 +
            self.WEIGHT_LINES * lines_cleared +
            self.WEIGHT_COMPLETE_LINE * near_complete_lines
        )

        return score

    def _evaluate_board_with_result(
        self,
        board,
        score_change: int,
        lines_cleared: bool
    ) -> float:
        """
        评估模拟后的结果

        Args:
            board: 模拟后的棋盘
            score_change: 分数变化
            lines_cleared: 是否消除行

        Returns:
            评估分数
        """
        base_score = self._evaluate_board(board)

        # 添加行消除奖励
        if lines_cleared:
            base_score += self.WEIGHT_LINES * 2

        # 添加分数奖励
        base_score += score_change * 0.1

        return base_score

    def get_best_position_and_rotation(
        self,
        game: TetrisGame
    ) -> tuple:
        """
        获取最佳位置和旋转

        Args:
            game: 当前游戏实例

        Returns:
            (最佳x位置, 最佳旋转, 最佳动作)
        """
        if game.current_piece is None:
            return (3, 0, PlayerAction.WAIT)

        best_x = game.current_piece.x
        best_rotation = game.current_piece.rotation
        best_action = PlayerAction.WAIT
        best_score = float('-inf')

        # 尝试当前方块的所有旋转状态
        for rotation in range(4):
            test_piece = game.current_piece.clone()
            test_piece.rotation = rotation

            if game.board.check_collision(test_piece):
                continue

            # 尝试所有x位置
            for x in range(-2, game.board.width + 2):
                test_piece.x = x

                if game.board.check_collision(test_piece):
                    continue

                # 找到落底位置
                bottom_piece = game.get_piece_at_bottom(test_piece)

                # 临时放置方块
                game.board.place_piece(bottom_piece)

                # 评估
                score = self._evaluate_board(game.board)

                # 移除临时方块
                for cx, cy in bottom_piece.get_cells():
                    if 0 <= cy < game.board.height:
                        game.board.set_cell(cx, cy, 0)

                if score > best_score:
                    best_score = score
                    best_x = x
                    best_rotation = rotation

        # 确定最佳动作
        if best_rotation != game.current_piece.rotation:
            best_action = PlayerAction.ROTATE
        elif best_x < game.current_piece.x:
            best_action = PlayerAction.MOVE_LEFT
        elif best_x > game.current_piece.x:
            best_action = PlayerAction.MOVE_RIGHT
        else:
            best_action = PlayerAction.HARD_DROP

        return (best_x, best_rotation, best_action)