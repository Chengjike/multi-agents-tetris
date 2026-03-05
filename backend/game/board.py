"""
俄罗斯方块Board（棋盘）实现

棋盘规格：20行 x 10列
"""
import copy
import random
from typing import List, Optional

from backend.game.piece import Piece


class Board:
    """俄罗斯方块棋盘类"""

    def __init__(self, width: int = 10, height: int = 20):
        self.width = width
        self.height = height
        self._grid: List[List[int]] = [
            [0 for _ in range(width)] for _ in range(height)
        ]

    def get_cell(self, x: int, y: int) -> int:
        """
        获取指定位置的格子值

        Args:
            x: 横坐标 (0 到 width-1)
            y: 纵坐标 (0 到 height-1)

        Returns:
            0 表示空，1 表示有方块
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._grid[y][x]
        raise IndexError(f"Position ({x}, {y}) out of bounds")

    def set_cell(self, x: int, y: int, value: int) -> None:
        """
        设置指定位置的格子值

        Args:
            x: 横坐标
            y: 纵坐标
            value: 0 表示空，1 表示有方块
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"Position ({x}, {y}) out of bounds")
        self._grid[y][x] = value

    def check_collision(self, piece: Piece) -> bool:
        """
        检查方块是否与墙壁或已放置的方块碰撞

        Args:
            piece: 要检查的方块

        Returns:
            True 表示发生碰撞，False 表示无碰撞
        """
        for x, y in piece.get_cells():
            # 检查边界
            if x < 0 or x >= self.width or y >= self.height:
                return True

            # y < 0 允许（方块还在屏幕上方）
            if y >= 0 and self._grid[y][x] != 0:
                return True

        return False

    def place_piece(self, piece: Piece) -> bool:
        """
        将方块放置到棋盘上

        Args:
            piece: 要放置的方块

        Returns:
            True 表示放置成功，False 表示发生碰撞
        """
        if self.check_collision(piece):
            return False

        for x, y in piece.get_cells():
            if 0 <= y < self.height:
                self._grid[y][x] = 1

        return True

    def clear_lines(self) -> List[int]:
        """
        消除已满的行（所有满行都会被消除，不只是连续的）

        Returns:
            消除的行号列表
        """
        # 找出所有满的行
        full_rows = []
        for y, row in enumerate(self._grid):
            if all(cell != 0 for cell in row):
                full_rows.append(y)

        if not full_rows:
            return []

        # 创建新棋盘，只保留未满的行
        new_grid = [row for row in self._grid if not all(cell != 0 for cell in row)]

        # 在顶部添加空行
        for _ in range(len(full_rows)):
            new_grid.insert(0, [0 for _ in range(self.width)])

        self._grid = new_grid
        return full_rows

    def add_bottom_row(self) -> None:
        """
        在棋盘底部添加一行障碍（随机缺口）

        缺口位置随机生成
        """
        # 首先将所有行上移一行
        self._grid.pop(0)  # 移除顶部行
        new_row = [1 for _ in range(self.width)]

        # 随机选择一个位置为空（缺口）
        gap_position = random.randint(0, self.width - 1)
        new_row[gap_position] = 0

        self._grid.append(new_row)

    def get_board_data(self) -> List[List[int]]:
        """
        获取棋盘数据的副本

        Returns:
            20x10 的二维数组
        """
        return [row[:] for row in self._grid]

    def copy(self) -> 'Board':
        """
        创建棋盘的深拷贝

        Returns:
            新的Board对象
        """
        new_board = Board(self.width, self.height)
        new_board._grid = copy.deepcopy(self._grid)
        return new_board

    def get_height_map(self) -> List[int]:
        """
        获取每列的最高方块高度（从底部计算）

        Returns:
            长度为 width 的列表，值为每列的最高点距离底部的高度
            0表示该列为空，height表示该列已满到顶部
        """
        height_map = [0 for _ in range(self.width)]

        for x in range(self.width):
            # 从顶部向下找第一个填充的格子（最高的方块）
            for y in range(self.height):
                if self._grid[y][x] != 0:
                    # 高度 = 底部行索引 - 当前行索引 + 1
                    height_map[x] = self.height - y
                    break

        return height_map

    def get_holes(self) -> int:
        """
        计算棋盘上的空洞数量

        Returns:
            空洞数量
        """
        holes = 0
        height_map = self.get_height_map()

        for x in range(self.width):
            above_top = True
            for y in range(height_map[x]):
                if above_top and self._grid[y][x] == 0:
                    # 记录第一个空格，之后的空格如果下面有方块则为空洞
                    above_top = False
                elif not above_top and self._grid[y][x] == 0:
                    holes += 1

        return holes

    def get_bumpiness(self) -> int:
        """
        计算棋盘的不平整度（相邻列高度差的绝对值之和）

        Returns:
            不平整度
        """
        height_map = self.get_height_map()
        bumpiness = 0

        for i in range(len(height_map) - 1):
            bumpiness += abs(height_map[i] - height_map[i + 1])

        return bumpiness