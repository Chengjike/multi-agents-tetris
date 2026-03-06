"""
状态评估器模块

评估游戏状态的优劣
"""
from typing import List


def evaluate_state(board: List[List[str]]) -> float:
    """
    评估棋盘状态
    
    评分标准：
    - 棋盘高度越低越好
    - 洞穴越少越好
    - 行越完整越好（即将消除的行）
    
    Args:
        board: 20x10 棋盘，'X'表示已填充，' '表示空
        
    Returns:
        评分 (0-100)，越高越好
    """
    if not board:
        return 0.0
    
    len(board)
    len(board[0]) if board else 0
    
    # 1. 计算棋盘高度分数（高度越低越好）
    height_score = _evaluate_height(board)
    
    # 2. 计算洞穴惩罚（洞穴越少越好）
    hole_penalty = _evaluate_holes(board)
    
    # 3. 计算完整行奖励（即将消除的行）
    line_bonus = _evaluate_complete_lines(board)
    
    # 4. 计算平坦度（避免凹凸不平）
    smoothness_bonus = _evaluate_smoothness(board)
    
    # 综合评分
    total_score = (
        height_score * 0.3 +
        (100 - hole_penalty) * 0.35 +
        line_bonus * 0.25 +
        smoothness_bonus * 0.1
    )
    
    return max(0, min(100, total_score))


def _evaluate_height(board: List[List[str]]) -> float:
    """评估棋盘高度"""
    rows = len(board)
    
    # 找到最高填充行
    highest_filled = 0
    for row in range(rows):
        if any(cell != ' ' and cell != '' for cell in board[row]):
            highest_filled = rows - row
    
    # 归一化到 0-100（高度越低分数越高）
    return ((rows - highest_filled) / rows) * 100


def _evaluate_holes(board: List[List[str]]) -> int:
    """计算洞穴数"""
    if not board:
        return 0
    
    rows = len(board)
    cols = len(board[0]) if board else 0
    holes = 0
    
    for col in range(cols):
        filled = False
        for row in range(rows):
            cell = board[row][col] if col < len(board[row]) else ' '
            if cell != ' ' and cell != '':
                filled = True
            elif filled and (cell == ' ' or cell == ''):
                holes += 1
    
    return holes


def _evaluate_complete_lines(board: List[List[str]]) -> float:
    """评估完整行（即将消除的行）"""
    if not board:
        return 0.0
    
    complete_rows = 0
    for row in board:
        if all(cell != ' ' and cell != '' for cell in row):
            complete_rows += 1
    
    # 每完整一行加 20 分
    return complete_rows * 20


def _evaluate_smoothness(board: List[List[str]]) -> float:
    """评估棋盘平坦度"""
    if not board:
        return 100.0
    
    rows = len(board)
    cols = len(board[0]) if board else 0
    
    # 计算每列的高度差
    heights = []
    for col in range(cols):
        col_height = 0
        for row in range(rows):
            cell = board[row][col] if col < len(board[row]) else ' '
            if cell != ' ' and cell != '':
                col_height = rows - row
                break
        heights.append(col_height)
    
    # 计算高度差
    total_diff = 0
    for i in range(len(heights) - 1):
        total_diff += abs(heights[i] - heights[i + 1])
    
    # 平坦度 = 100 - 总高度差 * 10
    return max(0, 100 - total_diff * 10)