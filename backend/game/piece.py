"""
俄罗斯方块Piece定义

方块类型：I, J, L, O, S, T, Z（共7种）
每种方块有4种旋转状态（0, 90, 180, 270度）
"""
import random
from enum import Enum
from typing import List, Tuple


class PieceType(Enum):
    """方块类型枚举"""
    I = 'I'
    J = 'J'
    L = 'L'
    O = 'O'
    S = 'S'
    T = 'T'
    Z = 'Z'


# 方块形状定义（相对于中心点的坐标）
# 每种类型有4个旋转状态，每个状态是一组坐标
PIECE_SHAPES = {
    PieceType.I: [
        [(0, 0), (-1, 0), (1, 0), (2, 0)],   # 0度：水平
        [(0, -1), (0, 0), (0, 1), (0, 2)],   # 90度：垂直
        [(0, 0), (-1, 0), (1, 0), (2, 0)],   # 180度：水平
        [(0, -1), (0, 0), (0, 1), (0, 2)],   # 270度：垂直
    ],
    PieceType.J: [
        [(-1, 0), (0, 0), (1, 0), (1, 1)],   # 0度
        [(0, -1), (0, 0), (0, 1), (1, -1)],   # 90度
        [(-1, -1), (-1, 0), (0, 0), (1, 0)],  # 180度
        [(-1, 1), (0, -1), (0, 0), (0, 1)],   # 270度
    ],
    PieceType.L: [
        [(-1, 0), (0, 0), (1, 0), (-1, 1)],  # 0度
        [(-1, -1), (0, -1), (0, 0), (0, 1)], # 90度
        [(1, -1), (-1, 0), (0, 0), (1, 0)],   # 180度
        [(0, -1), (0, 0), (0, 1), (1, 1)],   # 270度
    ],
    PieceType.O: [
        [(0, 0), (1, 0), (0, 1), (1, 1)],    # 所有旋转状态相同
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
    ],
    PieceType.S: [
        [(0, 0), (1, 0), (-1, 1), (0, 1)],   # 0度
        [(0, -1), (0, 0), (1, 0), (1, 1)],   # 90度
        [(0, 0), (1, 0), (-1, 1), (0, 1)],   # 180度
        [(0, -1), (0, 0), (1, 0), (1, 1)],   # 270度
    ],
    PieceType.T: [
        [(-1, 0), (0, 0), (1, 0), (0, 1)],   # 0度
        [(0, -1), (0, 0), (1, 0), (0, 1)],   # 90度
        [(-1, 0), (0, 0), (1, 0), (0, -1)],  # 180度
        [(0, -1), (-1, 0), (0, 0), (0, 1)],  # 270度
    ],
    PieceType.Z: [
        [(-1, 0), (0, 0), (0, 1), (1, 1)],   # 0度
        [(1, -1), (0, 0), (1, 0), (0, 1)],   # 90度
        [(-1, 0), (0, 0), (0, 1), (1, 1)],   # 180度
        [(1, -1), (0, 0), (1, 0), (0, 1)],   # 270度
    ],
}

# 方块颜色（RGB）
PIECE_COLORS = {
    PieceType.I: (0, 255, 255),    # 青色
    PieceType.J: (0, 0, 255),      # 蓝色
    PieceType.L: (255, 165, 0),    # 橙色
    PieceType.O: (255, 255, 0),    # 黄色
    PieceType.S: (0, 255, 0),      # 绿色
    PieceType.T: (128, 0, 128),    # 紫色
    PieceType.Z: (255, 0, 0),      # 红色
}


class Piece:
    """俄罗斯方块Piece类"""

    def __init__(
        self,
        piece_type: PieceType,
        x: int = 0,
        y: int = 0,
        rotation: int = 0
    ):
        self.type = piece_type
        self.x = x
        self.y = y
        self.rotation = rotation % 4

    @property
    def color(self) -> Tuple[int, int, int]:
        """获取方块颜色"""
        return PIECE_COLORS[self.type]

    def get_shape(self) -> List[Tuple[int, int]]:
        """
        获取当前旋转状态下的方块形状坐标

        Returns:
            相对于(x, y)的坐标列表
        """
        shapes = PIECE_SHAPES[self.type]
        return list(shapes[self.rotation])

    def get_cells(self) -> List[Tuple[int, int]]:
        """
        获取方块在棋盘上的绝对坐标

        Returns:
            绝对坐标列表 [(x, y), ...]
        """
        shape = self.get_shape()
        return [(self.x + dx, self.y + dy) for dx, dy in shape]

    def rotate(self) -> None:
        """顺时针旋转90度"""
        self.rotation = (self.rotation + 1) % 4

    def clone(self) -> 'Piece':
        """克隆当前方块"""
        return Piece(self.type, self.x, self.y, self.rotation)

    @classmethod
    def random(cls, x: int = 0, y: int = 0) -> 'Piece':
        """随机生成一个方块"""
        piece_type = random.choice(list(PieceType))
        return cls(piece_type, x=x, y=y, rotation=0)