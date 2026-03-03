"""
测试用例：规则Agent（基于简单规则的AI）

用于测试的简单AI，选择最优落点
"""
import pytest
from backend.game.tetris import TetrisGame, PlayerAction
from backend.game.piece import Piece, PieceType
from backend.game.board import Board
from backend.agents.rule_agent import RuleAgent


class TestRuleAgentCreation:
    """测试Agent创建"""

    def test_agent_creation(self):
        """测试创建Agent"""
        agent = RuleAgent(player_id=0)
        assert agent.player_id == 0


class TestRuleAgentDecision:
    """测试Agent决策"""

    def test_agent_returns_valid_action(self):
        """测试Agent返回有效动作"""
        game = TetrisGame(player_id=0)
        game.start()

        agent = RuleAgent(player_id=0)
        action = agent.decide(game)

        assert action in list(PlayerAction)

    def test_agent_considers_all_moves(self):
        """测试Agent考虑所有可能的移动"""
        # 创建一个空棋盘
        board = Board()
        game = TetrisGame(player_id=0)
        game.start()

        agent = RuleAgent(player_id=0)

        # Agent应该选择一个动作
        action = agent.decide(game)
        assert action is not None


class TestRuleAgentScoring:
    """测试Agent评分逻辑"""

    def test_agent_prefers_lower_position(self):
        """测试Agent偏好更低的位置"""
        agent = RuleAgent(player_id=0)

        # 测试评分函数
        from backend.game.piece import Piece

        # 高位置
        piece_high = Piece(PieceType.T, x=3, y=5)
        board1 = Board()
        # 填充底部让方块无法完全落下
        for x in range(10):
            board1.set_cell(x, 19, 1)
        board1.place_piece(piece_high)

        # 低位置
        piece_low = Piece(PieceType.T, x=3, y=15)
        board2 = Board()
        board2.place_piece(piece_low)

        # 评估位置
        score_high = agent._evaluate_board(board1)
        score_low = agent._evaluate_board(board2)

        # 低位置应该更好（分数更低，因为高度更低）
        assert score_low <= score_high

    def test_agent_prefers_fewer_holes(self):
        """测试Agent能正确评估空洞"""
        agent = RuleAgent(player_id=0)

        board1 = Board()
        # 创建一些空洞
        board1.set_cell(5, 18, 1)
        board1.set_cell(5, 19, 0)  # 空洞
        board1.set_cell(6, 19, 1)

        board2 = Board()
        # 填充的棋盘
        for x in range(10):
            board2.set_cell(x, 19, 1)

        score1 = agent._evaluate_board(board1)
        score2 = agent._evaluate_board(board2)

        # 两个棋盘都应该有有效的分数
        assert score1 < 0  # 负分表示不理想
        assert score2 < 0
        # board2因为全满，高度更低
        assert score2 > score1  # 填充的棋盘分数更高（负数越大越好）


class TestRuleAgentSimulation:
    """测试Agent模拟"""

    def test_agent_can_simulate_action(self):
        """测试Agent可以模拟动作"""
        agent = RuleAgent(player_id=0)
        game = TetrisGame(player_id=0)
        game.start()

        # 测试模拟
        from backend.game.tetris import TetrisGame as TG
        result = TG.simulate_action(
            game.board,
            game.current_piece,
            PlayerAction.MOVE_LEFT
        )

        assert result is not None
        assert len(result) == 3  # (new_board, score_change, lines_cleared)