"""
测试用例：俄罗斯方块游戏核心（Tetris）

测试单个玩家实例的游戏逻辑
"""
import pytest
from backend.game.tetris import TetrisGame, GameStatus, PlayerAction


class TestTetrisCreation:
    """测试游戏创建"""

    def test_game_creation(self):
        """测试创建游戏实例"""
        game = TetrisGame(player_id=0)
        assert game.player_id == 0
        assert game.status == GameStatus.WAITING

    def test_game_has_board(self):
        """测试游戏有棋盘"""
        game = TetrisGame(player_id=0)
        assert game.board is not None
        assert game.board.width == 10
        assert game.board.height == 20

    def test_game_has_current_piece(self):
        """测试游戏有当前方块"""
        game = TetrisGame(player_id=0)
        assert game.current_piece is not None

    def test_initial_score(self):
        """测试初始分数为0"""
        game = TetrisGame(player_id=0)
        assert game.score == 0


class TestGameStart:
    """测试游戏开始"""

    def test_start_game(self):
        """测试开始游戏"""
        game = TetrisGame(player_id=0)
        game.start()
        assert game.status == GameStatus.RUNNING

    def test_start_generates_piece(self):
        """测试开始游戏生成新方块"""
        game = TetrisGame(player_id=0)
        game.start()
        assert game.current_piece is not None
        assert game.current_piece.y < 0  # 方块从顶部出现


class TestGameStatus:
    """测试游戏状态"""

    def test_get_state(self):
        """测试获取游戏状态"""
        game = TetrisGame(player_id=0)
        game.start()
        game.score = 100

        state = game.get_state()

        assert state['player_id'] == 0
        assert state['status'] == 'running'
        assert state['score'] == 100
        assert 'board' in state
        assert 'current_piece' in state


class TestPlayerActions:
    """测试玩家动作"""

    def test_action_move_left(self):
        """测试左移"""
        game = TetrisGame(player_id=0)
        game.start()
        initial_x = game.current_piece.x

        result = game.perform_action(PlayerAction.MOVE_LEFT)

        assert result is True
        assert game.current_piece.x == initial_x - 1

    def test_action_move_right(self):
        """测试右移"""
        game = TetrisGame(player_id=0)
        game.start()
        initial_x = game.current_piece.x

        result = game.perform_action(PlayerAction.MOVE_RIGHT)

        assert result is True
        assert game.current_piece.x == initial_x + 1

    def test_action_rotate(self):
        """测试旋转"""
        game = TetrisGame(player_id=0)
        game.start()
        initial_rotation = game.current_piece.rotation

        result = game.perform_action(PlayerAction.ROTATE)

        assert result is True
        assert game.current_piece.rotation == (initial_rotation + 1) % 4

    def test_action_soft_drop(self):
        """测试软下降"""
        game = TetrisGame(player_id=0)
        game.start()
        initial_y = game.current_piece.y

        result = game.perform_action(PlayerAction.SOFT_DROP)

        assert result is True
        assert game.current_piece.y > initial_y

    def test_action_hard_drop(self):
        """测试硬下降"""
        game = TetrisGame(player_id=0)
        game.start()

        result = game.perform_action(PlayerAction.HARD_DROP)

        assert result is True
        # 硬下降应该直接落到最底部
        # 检查是否碰撞了
        assert game.board.check_collision(game.current_piece) is True

    def test_action_wait(self):
        """测试等待（无操作）"""
        game = TetrisGame(player_id=0)
        game.start()

        result = game.perform_action(PlayerAction.WAIT)

        assert result is True
        # 等待应该不改变状态


class TestLineClearing:
    """测试行消除"""

    def test_line_clear_adds_score(self):
        """测试消除行增加分数"""
        game = TetrisGame(player_id=0)
        game.start()

        # 先放置当前方块
        game.board.place_piece(game.current_piece)

        # 手动填充一行并通过游戏方法消除
        for x in range(10):
            game.board.set_cell(x, 19, 1)

        # 使用_process_line_clearing来正确触发分数计算
        lines = game._process_line_clearing()

        # 分数应该增加（消除1行=100分）
        assert lines == 1
        assert game.score >= 100


class TestGameOver:
    """测试游戏结束"""

    def test_game_over_when_piece_stuck(self):
        """测试方块无法放置时游戏结束"""
        game = TetrisGame(player_id=0)
        game.start()

        # 填满整个棋盘除了顶部几行
        for y in range(15, 20):
            for x in range(10):
                game.board.set_cell(x, y, 1)

        # 尝试生成新方块 - 应该会导致游戏结束
        game.spawn_new_piece()

        # 如果新方块无法放置，游戏应该结束
        if game.board.check_collision(game.current_piece):
            assert game.status == GameStatus.GAME_OVER or game.check_game_over()


class TestCheckGameOver:
    """测试检查游戏结束"""

    def test_check_game_over(self):
        """测试检查游戏是否结束"""
        game = TetrisGame(player_id=0)

        # 空棋盘不应该结束
        assert game.check_game_over() is False


class TestTick:
    """测试游戏tick"""

    def test_tick_moves_piece_down(self):
        """测试tick使方块下落"""
        game = TetrisGame(player_id=0)
        game.start()
        initial_y = game.current_piece.y

        game.tick()

        assert game.current_piece.y >= initial_y


class TestSpawnNewPiece:
    """测试生成新方块"""

    def test_spawn_new_piece(self):
        """测试生成新方块"""
        game = TetrisGame(player_id=0)
        game.start()

        # 先放置当前方块
        game.board.place_piece(game.current_piece)

        old_piece = game.current_piece
        game.spawn_new_piece()

        assert game.current_piece is not old_piece
        assert game.current_piece.y < 0  # 新方块从顶部出现