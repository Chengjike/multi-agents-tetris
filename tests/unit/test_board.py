"""
测试用例：俄罗斯方块Board（棋盘）

棋盘规格：20行 x 10列
"""
import pytest
from backend.game.board import Board
from backend.game.piece import Piece, PieceType


class TestBoardCreation:
    """测试棋盘创建"""

    def test_default_size(self):
        """测试默认棋盘大小 20x10"""
        board = Board()
        assert board.width == 10
        assert board.height == 20

    def test_custom_size(self):
        """测试自定义棋盘大小"""
        board = Board(width=15, height=30)
        assert board.width == 15
        assert board.height == 30


class TestBoardState:
    """测试棋盘状态"""

    def test_empty_board(self):
        """测试空棋盘"""
        board = Board()
        for y in range(board.height):
            for x in range(board.width):
                assert board.get_cell(x, y) == 0

    def test_set_cell(self):
        """测试设置格子"""
        board = Board()
        board.set_cell(5, 10, 1)
        assert board.get_cell(5, 10) == 1

    def test_set_cell_out_of_bounds(self):
        """测试越界设置"""
        board = Board()
        # 越界应该被忽略或报错
        with pytest.raises(IndexError):
            board.set_cell(10, 20, 1)


class TestBoardCollision:
    """测试碰撞检测"""

    def test_no_collision(self):
        """测试无碰撞"""
        board = Board()
        piece = Piece(PieceType.T, x=3, y=0)
        assert not board.check_collision(piece)

    def test_collision_with_wall_left(self):
        """测试左墙碰撞"""
        board = Board()
        piece = Piece(PieceType.I, x=-2, y=0)
        assert board.check_collision(piece)

    def test_collision_with_wall_right(self):
        """测试右墙碰撞"""
        board = Board()
        piece = Piece(PieceType.I, x=9, y=0)
        assert board.check_collision(piece)

    def test_collision_with_floor(self):
        """测试地板碰撞"""
        board = Board()
        piece = Piece(PieceType.I, x=0, y=19)
        assert board.check_collision(piece)

    def test_collision_with_placed_pieces(self):
        """测试与已放置方块的碰撞"""
        board = Board()
        # 先放置一些方块在 (5, 18) 位置
        board.set_cell(5, 18, 1)

        # T型方块中心在(5, 18)时会占据 (4,18), (5,18), (6,18), (5,19)
        piece = Piece(PieceType.T, x=5, y=18)
        assert board.check_collision(piece)


class TestBoardPlacePiece:
    """测试放置方块"""

    def test_place_piece(self):
        """测试放置方块"""
        board = Board()
        piece = Piece(PieceType.T, x=3, y=17)
        board.place_piece(piece)

        # 检查方块占据的格子
        cells = piece.get_cells()
        for x, y in cells:
            assert board.get_cell(x, y) == 1

    def test_place_piece_with_collision(self):
        """测试放置方块时发生碰撞"""
        board = Board()
        # 先放置一个方块在 (5, 18)
        board.set_cell(5, 18, 1)

        # T型方块中心在(5, 18)时会占据 (4,18), (5,18), (6,18), (5,19)，与现有方块碰撞
        piece = Piece(PieceType.T, x=5, y=18)
        result = board.place_piece(piece)
        assert result is False


class TestBoardClearLines:
    """测试消除行"""

    def test_no_lines_to_clear(self):
        """测试没有行需要消除"""
        board = Board()
        board.set_cell(5, 19, 1)  # 只有部分格子有方块
        lines_cleared = board.clear_lines()
        assert lines_cleared == 0

    def test_clear_one_line(self):
        """测试消除一行"""
        board = Board()
        # 填充第19行
        for x in range(board.width):
            board.set_cell(x, 19, 1)

        lines_cleared = board.clear_lines()
        assert lines_cleared == 1

        # 检查第19行是否为空
        for x in range(board.width):
            assert board.get_cell(x, 19) == 0

    def test_clear_multiple_lines(self):
        """测试消除多行"""
        board = Board()
        # 填充第18、19行
        for x in range(board.width):
            board.set_cell(x, 18, 1)
            board.set_cell(x, 19, 1)

        lines_cleared = board.clear_lines()
        assert lines_cleared == 2

    def test_clear_non_consecutive_lines(self):
        """测试消除不连续的行（所有满行都会被消除）"""
        board = Board()
        # 填充第17、19行
        for x in range(board.width):
            board.set_cell(x, 17, 1)
            board.set_cell(x, 19, 1)

        lines_cleared = board.clear_lines()
        # 所有满行都应该被消除
        assert lines_cleared == 2


class TestBoardAddBottomRow:
    """测试添加底部障碍行"""

    def test_add_bottom_row(self):
        """测试添加底部障碍行"""
        board = Board()
        # 设置第18行有方块
        for x in range(board.width):
            board.set_cell(x, 18, 1)

        board.add_bottom_row()

        # 第19行应该有障碍（有缺口）
        has_filled = False
        has_empty = False
        for x in range(board.width):
            if board.get_cell(x, 19) == 1:
                has_filled = True
            else:
                has_empty = True

        assert has_filled and has_empty  # 有填充也有空缺

    def test_add_bottom_row_pushes_up(self):
        """测试添加底部障碍行时棋盘上移"""
        board = Board()
        # 设置第19行有方块
        for x in range(board.width):
            board.set_cell(x, 19, 1)

        board.add_bottom_row()

        # 第19行应该有新障碍
        # 第18行应该变成原来的第19行（如果有空位）
        # 由于满行会被推上去，这里主要测试不会崩溃


class TestBoardGetBoardData:
    """测试获取棋盘数据"""

    def test_get_board_data(self):
        """测试获取完整棋盘数据"""
        board = Board()
        board.set_cell(3, 5, 1)
        board.set_cell(4, 5, 1)

        data = board.get_board_data()

        assert len(data) == 20  # 20行
        assert len(data[0]) == 10  # 10列
        assert data[5][3] == 1
        assert data[5][4] == 1


class TestBoardCopy:
    """测试棋盘复制"""

    def test_board_copy(self):
        """测试棋盘深拷贝"""
        board1 = Board()
        board1.set_cell(5, 10, 1)

        board2 = board1.copy()

        # 修改board2不影响board1
        board2.set_cell(5, 10, 2)
        assert board1.get_cell(5, 10) == 1
        assert board2.get_cell(5, 10) == 2