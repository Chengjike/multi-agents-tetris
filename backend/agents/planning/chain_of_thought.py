"""
思维链 (Chain of Thought) 推理模块

在输出动作前，先推演未来几步的可能结果
"""
from typing import Dict, Any, List


def build_cot_prompt(
    game_state: Dict[str, Any],
    depth: int = 2,
    include_history: bool = True
) -> str:
    """
    构建思维链推理提示词
    
    Args:
        game_state: 游戏状态
        depth: 推理深度（模拟几步）
        include_history: 是否包含历史经验
        
    Returns:
        提示词字符串
    """
    board = game_state.get('board', [])
    current_piece = game_state.get('current_piece', '?')
    score = game_state.get('score', 0)
    lines_cleared = game_state.get('lines_cleared', 0)
    
    # 计算棋盘高度（从底部往上数有多少行非空）
    board_height = _calculate_board_height(board)
    
    # 统计洞穴数
    holes = _count_holes(board)
    
    prompt = f"""你正在玩俄罗斯方块。请进行{depth}步深度思考后再决定动作。

当前游戏状态：
- 当前方块：{current_piece}
- 当前得分：{score}
- 已消除行数：{lines_cleared}
- 棋盘高度：{board_height}/20
- 洞穴数量：{holes}

请按以下格式思考：

第1步分析：
- 如果我[动作A]，会...
- 如果我[动作B]，会...
- 比较各动作的优劣

第2步分析：
- 基于第1步的选择，接下来会...
- 评估长期收益

请在充分思考后，输出最终选择的动作。

可用动作：left, right, rotate, soft_drop, hard_drop, wait

请按以下JSON格式输出：
{{
    "reasoning": "你的思考过程",
    "action": "最终选择的动作"
}}
"""
    
    if include_history:
        # 可以在这里加入历史经验
        pass
    
    return prompt


def _calculate_board_height(board: List[List[str]]) -> int:
    """计算棋盘高度（从底部往上非空行数）"""
    if not board:
        return 0
    
    height = 0
    for row in reversed(board):
        if any(cell != ' ' and cell != '' for cell in row):
            height += 1
    return height


def _count_holes(board: List[List[str]]) -> int:
    """计算棋盘中的洞穴数"""
    if not board:
        return 0
    
    holes = 0
    rows = len(board)
    cols = len(board[0]) if board else 0
    
    for col in range(cols):
        # 找到第一个被填充的位置
        filled = False
        for row in range(rows):
            cell = board[row][col] if col < len(board[row]) else ' '
            if cell != ' ' and cell != '':
                filled = True
            elif filled and (cell == ' ' or cell == ''):
                # 下方有填充，上方为空，这就是一个洞
                holes += 1
    
    return holes