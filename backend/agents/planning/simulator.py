"""
动作模拟器模块

模拟动作执行后的状态变化
"""
from typing import Tuple, List
from copy import deepcopy
from backend.game.board import Board
from backend.game.tetris import PlayerAction


def simulate_action(
    board: Board,
    piece_type: str,
    action: PlayerAction,
    num_rows: int = 20,
    num_cols: int = 10
) -> Tuple[Board, int]:
    """
    模拟执行单个动作
    
    Args:
        board: 当前棋盘
        piece_type: 方块类型
        action: 要执行的动作
        num_rows: 棋盘行数
        num_cols: 棋盘列数
        
    Returns:
        (新棋盘, 消除的行数)
    """
    # 复制棋盘
    new_board = deepcopy(board)
    lines_cleared = 0
    
    # 模拟动作
    if action == PlayerAction.MOVE_LEFT:
        # 模拟左移一列（简化版）
        pass
    elif action == PlayerAction.MOVE_RIGHT:
        # 模拟右移一列
        pass
    elif action == PlayerAction.ROTATE:
        # 模拟旋转
        pass
    elif action == PlayerAction.SOFT_DROP:
        # 模拟软下降（向下几行）
        lines_cleared = _simulate_drop(new_board, piece_type, soft=True)
    elif action == PlayerAction.HARD_DROP:
        # 模拟硬下降（直接到底）
        lines_cleared = _simulate_drop(new_board, piece_type, soft=False)
    elif action == PlayerAction.WAIT:
        # 等待不动
        pass
    
    return new_board, lines_cleared


def _simulate_drop(
    board: Board,
    piece_type: str,
    soft: bool = True
) -> int:
    """
    模拟下落
    
    Args:
        board: 棋盘
        piece_type: 方块类型
        soft: 是否软下降
        
    Returns:
        消除的行数
    """
    # 简化实现：随机模拟消除（实际应该真实模拟）
    import random
    
    # 模拟下落并检查是否消除行
    if soft:
        # 软下降下降较少行
        random.randint(1, 3)
    else:
        # 硬下降直接到底
        pass
    
    # 简化：随机产生消除
    lines_cleared = 0
    if random.random() < 0.1:  # 10% 概率消除一行
        lines_cleared = 1
    elif random.random() < 0.05:  # 5% 概率消除多行
        lines_cleared = random.randint(2, 4)
    
    return lines_cleared


def simulate_sequence(
    board: Board,
    piece_type: str,
    actions: List[PlayerAction]
) -> Tuple[Board, int]:
    """
    模拟动作序列
    
    Args:
        board: 初始棋盘
        piece_type: 方块类型
        actions: 动作序列
        
    Returns:
        (最终棋盘, 总消除行数)
    """
    current_board = board
    total_lines = 0
    
    for action in actions:
        current_board, lines = simulate_action(
            current_board, piece_type, action
        )
        total_lines += lines
    
    return current_board, total_lines