"""
规则Agent（基于简单规则的AI）

使用评估函数选择最优落点
"""
from typing import Optional
from backend.game.tetris import TetrisGame, PlayerAction
from backend.game.piece import Piece


class RuleAgent:
    """基于规则的俄罗斯方块AI"""

    # 评估权重
    WEIGHT_HEIGHT = -1.0      # 高度越低越好
    WEIGHT_HOLES = -5.0       # 空洞越少越好
    WEIGHT_BUMPINESS = -0.5   # 不平整度越低越好
    WEIGHT_LINES = 10.0       # 消除行越多越好

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

        # 考虑所有可能的动作
        best_action = PlayerAction.WAIT
        best_score = float('-inf')

        # 尝试所有动作
        for action in list(PlayerAction):
            if action == PlayerAction.WAIT:
                continue

            # 模拟动作结果
            new_board, score_change, lines_cleared = TetrisGame.simulate_action(
                game.board,
                game.current_piece,
                action
            )

            # 评估结果
            eval_score = self._evaluate_board_with_result(
                new_board,
                score_change,
                lines_cleared
            )

            if eval_score > best_score:
                best_score = eval_score
                best_action = action

        return best_action

    def _evaluate_board(self, board) -> float:
        """
        评估棋盘状态

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

        score = (
            self.WEIGHT_HEIGHT * total_height +
            self.WEIGHT_HOLES * holes +
            self.WEIGHT_BUMPINESS * bumpiness +
            self.WEIGHT_HEIGHT * max_height * 0.5
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