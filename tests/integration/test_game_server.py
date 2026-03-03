"""
测试用例：游戏服务器

测试游戏主循环和管理器
"""
import pytest
import asyncio
from backend.game.tetris import TetrisGame, GameStatus
from backend.game.punishment import PunishmentManager
from backend.agents.rule_agent import RuleAgent
from backend.game.game_manager import GameManager


class TestGameManagerCreation:
    """测试游戏管理器创建"""

    def test_manager_creation(self):
        """测试创建游戏管理器"""
        manager = GameManager()
        assert manager.num_players == 3
        assert len(manager.games) == 3


class TestGameManagerControl:
    """测试游戏控制"""

    def test_start_game(self):
        """测试开始游戏"""
        manager = GameManager()
        manager.start_game()

        for game in manager.games:
            assert game.status == GameStatus.RUNNING

    def test_get_game_states(self):
        """测试获取游戏状态"""
        manager = GameManager()
        manager.start_game()

        states = manager.get_game_states()
        assert len(states) == 3
        assert all('player_id' in s for s in states)


class TestGameLoop:
    """测试游戏主循环"""

    def test_single_tick(self):
        """测试单次tick"""
        manager = GameManager()
        manager.start_game()

        initial_piece_y = manager.games[0].current_piece.y

        # 执行一次tick
        manager.tick()

        # 方块应该下落
        assert manager.games[0].current_piece.y >= initial_piece_y


class TestPunishment:
    """测试惩罚"""

    def test_punishment_trigger(self):
        """测试惩罚触发"""
        manager = GameManager()

        # 模拟玩家0消除4行
        result = manager.punishment_manager.record_lines_cleared(0, 4)
        assert result['should_punish'] is True

    def test_apply_punishment(self):
        """测试应用惩罚"""
        manager = GameManager()
        manager.start_game()

        # 记录惩罚
        manager.punishment_manager.record_lines_cleared(0, 4)

        # 应用惩罚
        manager.apply_punishments()

        # 检查是否有惩罚应用到其他玩家


class TestGameEnd:
    """测试游戏结束"""

    def test_check_all_game_over(self):
        """检查所有游戏是否结束"""
        manager = GameManager()
        manager.start_game()

        # 游戏刚开始不应该结束
        assert manager.check_all_game_over() is False