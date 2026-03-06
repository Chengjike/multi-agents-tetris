"""
测试用例：惩罚机制

核心规则：当任意玩家一次消除4行时，立即在其他两个玩家的板子最底部随机增加一行障碍（留一个缺口）
"""
from backend.game.punishment import PunishmentManager


class TestPunishmentTrigger:
    """测试惩罚触发"""

    def test_single_4_line_clear_triggers_punishment(self):
        """测试一次消除4行触发惩罚"""
        pm = PunishmentManager(num_players=3)

        # 玩家0一次消除4行
        result = pm.record_lines_cleared(player_id=0, lines=4)

        # 应该触发惩罚
        assert result['should_punish'] is True
        assert 0 not in result['punished_players']  # 自己不受惩罚

    def test_less_than_4_lines_no_punishment(self):
        """测试消除少于4行不触发惩罚"""
        # 每个测试使用独立的manager避免累积影响
        pm = PunishmentManager(num_players=3)
        result = pm.record_lines_cleared(player_id=0, lines=1)
        assert result['should_punish'] is False

        pm2 = PunishmentManager(num_players=3)
        result = pm2.record_lines_cleared(player_id=0, lines=2)
        assert result['should_punish'] is False

        pm3 = PunishmentManager(num_players=3)
        result = pm3.record_lines_cleared(player_id=0, lines=3)
        assert result['should_punish'] is False


class TestPunishmentAccumulation:
    """测试惩罚累积"""

    def test_accumulate_4_lines(self):
        """测试累积4行触发惩罚"""
        pm = PunishmentManager(num_players=3)

        # 累积消除4行
        result1 = pm.record_lines_cleared(player_id=0, lines=2)
        assert result1['should_punish'] is False

        result2 = pm.record_lines_cleared(player_id=0, lines=2)
        assert result2['should_punish'] is True

    def test_reset_after_punishment(self):
        """测试惩罚后重置累积"""
        pm = PunishmentManager(num_players=3)

        # 累积4行触发惩罚
        pm.record_lines_cleared(player_id=0, lines=4)

        # 再次消除2行不应该触发（重置后从头累积）
        result = pm.record_lines_cleared(player_id=0, lines=2)
        assert result['should_punish'] is False


class TestPunishmentExecution:
    """测试惩罚执行"""

    def test_punish_adds_bottom_row(self):
        """测试惩罚添加底部障碍行"""
        from backend.game.board import Board

        board = Board()
        initial_row = [board.get_cell(x, 19) for x in range(10)]

        # 添加惩罚行
        board.add_bottom_row()

        # 应该有变化（有填充也有空缺）
        new_row = [board.get_cell(x, 19) for x in range(10)]
        assert new_row != initial_row

    def test_punish_creates_gap(self):
        """测试惩罚行有缺口"""
        from backend.game.board import Board

        board = Board()

        # 添加多行惩罚
        for _ in range(10):
            board.add_bottom_row()

        # 检查是否有空位
        has_empty = any(board.get_cell(x, 19) == 0 for x in range(10))
        assert has_empty


class TestMultiPlayerPunishment:
    """测试多人惩罚"""

    def test_3_players_punishment(self):
        """测试3人游戏的惩罚"""
        pm = PunishmentManager(num_players=3)

        # 玩家0触发惩罚
        result = pm.record_lines_cleared(player_id=0, lines=4)

        assert result['should_punish'] is True
        # 玩家1和2应该受到惩罚
        assert 1 in result['punished_players']
        assert 2 in result['punished_players']
        assert 0 not in result['punished_players']

    def test_different_player_triggers(self):
        """测试不同玩家触发惩罚"""
        pm = PunishmentManager(num_players=3)

        # 玩家1消除4行
        result = pm.record_lines_cleared(player_id=1, lines=4)

        assert result['should_punish'] is True
        assert 0 in result['punished_players']
        assert 2 in result['punished_players']
        assert 1 not in result['punished_players']


class TestPunishmentState:
    """测试惩罚状态"""

    def test_get_pending_punishments(self):
        """测试获取待执行的惩罚"""
        pm = PunishmentManager(num_players=3)

        # 玩家0累积2行
        pm.record_lines_cleared(player_id=0, lines=2)

        pending = pm.get_pending_punishments()
        assert len(pending) == 0

    def test_clear_pending_punishments(self):
        """测试清除待执行惩罚"""
        pm = PunishmentManager(num_players=3)

        # 玩家0触发惩罚
        pm.record_lines_cleared(player_id=0, lines=4)

        # 清除惩罚
        pm.clear_pending_punishments(0)

        # 玩家0应该没有待执行惩罚
        pending = pm.get_pending_punishments()
        for p in pending:
            assert 0 not in p['punished_players']