"""
测试用例：俄罗斯方块Piece定义

方块类型：I, J, L, O, S, T, Z（共7种）
每种方块有4种旋转状态（0, 90, 180, 270度）
"""
import pytest
from backend.game.piece import Piece, PieceType


class TestPieceType:
    """测试PieceType枚举"""

    def test_all_piece_types_exist(self):
        """7种标准方块类型都应该存在"""
        expected_types = {'I', 'J', 'L', 'O', 'S', 'T', 'Z'}
        actual_types = {pt.value for pt in PieceType}
        assert actual_types == expected_types


class TestPiece:
    """测试Piece类"""

    def test_piece_creation(self):
        """测试创建方块"""
        piece = Piece(PieceType.T, x=3, y=0, rotation=0)
        assert piece.type == PieceType.T
        assert piece.x == 3
        assert piece.y == 0
        assert piece.rotation == 0

    def test_piece_shape_i(self):
        """测试I型方块的4种旋转状态"""
        # I型方块：水平放置
        piece = Piece(PieceType.I, x=0, y=0, rotation=0)
        shape = piece.get_shape()
        assert len(shape) == 4  # I型4格

    def test_piece_shape_o(self):
        """测试O型方块（旋转不变）"""
        piece = Piece(PieceType.O, x=0, y=0, rotation=0)
        shape_0 = piece.get_shape()

        piece.rotation = 1
        shape_1 = piece.get_shape()

        piece.rotation = 2
        shape_2 = piece.get_shape()

        piece.rotation = 3
        shape_3 = piece.get_shape()

        # O型方块旋转后形状相同
        assert shape_0 == shape_1 == shape_2 == shape_3

    def test_piece_rotation(self):
        """测试方块旋转"""
        piece = Piece(PieceType.T, x=0, y=0, rotation=0)
        assert piece.rotation == 0

        piece.rotate()
        assert piece.rotation == 1

        piece.rotate()
        assert piece.rotation == 2

        piece.rotate()
        assert piece.rotation == 3

        piece.rotate()  # 回到0
        assert piece.rotation == 0

    def test_piece_clone(self):
        """测试方块克隆"""
        original = Piece(PieceType.T, x=3, y=5, rotation=2)
        cloned = original.clone()

        assert cloned.type == original.type
        assert cloned.x == original.x
        assert cloned.y == original.y
        assert cloned.rotation == original.rotation

        # 修改克隆不应影响原对象
        cloned.x = 10
        assert original.x == 3


class TestPieceShapes:
    """测试各种方块的具体形状"""

    def test_t_piece_shape(self):
        """T型方块形状测试"""
        piece = Piece(PieceType.T, x=0, y=0, rotation=0)
        shape = piece.get_shape()
        
        # T型：上3下1，呈T形
        # 验证形状包含正确的格子数
        assert len(shape) == 4

    def test_l_piece_shape(self):
        """L型方块形状测试"""
        piece = Piece(PieceType.L, x=0, y=0, rotation=0)
        shape = piece.get_shape()
        assert len(shape) == 4

    def test_j_piece_shape(self):
        """J型方块形状测试"""
        piece = Piece(PieceType.J, x=0, y=0, rotation=0)
        shape = piece.get_shape()
        assert len(shape) == 4

    def test_s_piece_shape(self):
        """S型方块形状测试"""
        piece = Piece(PieceType.S, x=0, y=0, rotation=0)
        shape = piece.get_shape()
        assert len(shape) == 4

    def test_z_piece_shape(self):
        """Z型方块形状测试"""
        piece = Piece(PieceType.Z, x=0, y=0, rotation=0)
        shape = piece.get_shape()
        assert len(shape) == 4


class TestPieceColors:
    """测试方块颜色"""

    def test_piece_has_color(self):
        """每个方块应该有颜色"""
        for pt in PieceType:
            piece = Piece(pt)
            assert piece.color is not None
            # 颜色应该是有效的RGB元组
            assert len(piece.color) == 3
            assert all(0 <= c <= 255 for c in piece.color)


class TestRandomPiece:
    """测试随机方块生成"""

    def test_random_piece_returns_valid_type(self):
        """随机生成的方块应该是有效的类型"""
        piece = Piece.random()
        assert isinstance(piece.type, PieceType)

    def test_random_piece_has_default_position(self):
        """随机方块应该有默认位置"""
        piece = Piece.random()
        assert piece.x >= 0
        assert piece.y >= 0
        assert piece.rotation == 0