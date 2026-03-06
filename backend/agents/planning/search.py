"""
最佳动作搜索模块

使用树搜索找到最佳动作
"""
from backend.game.board import Board
from backend.game.tetris import PlayerAction
from backend.agents.planning.tree_search import SearchTree, SearchNode, expand_actions
from backend.agents.planning.evaluator import evaluate_state
from backend.agents.planning.simulator import simulate_action


# 可用的基础动作
BASIC_ACTIONS = [
    PlayerAction.WAIT,
    PlayerAction.MOVE_LEFT,
    PlayerAction.MOVE_RIGHT,
]


def find_best_action(
    board: Board,
    piece_type: str,
    depth: int = 2,
    max_evaluations: int = 100
) -> PlayerAction:
    """
    找到最佳动作（使用树搜索）
    
    Args:
        board: 当前棋盘
        piece_type: 当前方块类型
        depth: 搜索深度
        max_evaluations: 最大评估次数（用于剪枝）
        
    Returns:
        最佳动作
    """
    # 构建初始状态
    initial_state = {
        'board': _board_to_list(board),
        'piece_type': piece_type
    }
    
    # 创建搜索树
    tree = SearchTree(max_depth=depth)
    root = tree.create_root(initial_state)
    
    # BFS 搜索
    evaluation_count = 0
    queue = [root]
    
    while queue and evaluation_count < max_evaluations:
        node = queue.pop(0)
        
        if node.depth >= depth:
            # 达到最大深度，评估
            node.score = _evaluate_node(node)
            evaluation_count += 1
            continue
        
        # 展开子节点
        children = expand_actions(node, BASIC_ACTIONS)
        
        for child in children:
            # 模拟动作
            new_board, lines = simulate_action(
                board, piece_type, child.action
            )
            
            child.state['board'] = _board_to_list(new_board)
            child.lines_cleared = lines
            
            # 评估子节点
            child.score = _evaluate_node(child) + lines * 10  # 消除行加分
            evaluation_count += 1
            
            queue.append(child)
    
    # 获取最佳路径
    best_path = tree.get_best_path()
    
    if best_path:
        return best_path[0]
    
    # 默认返回等待
    return PlayerAction.WAIT


def _board_to_list(board: Board) -> list:
    """将 Board 对象转换为列表"""
    # 简化实现
    grid = board.grid if hasattr(board, 'grid') else []
    result = []
    
    for row in grid:
        result.append(['X' if cell else ' ' for cell in row])
    
    # 补齐到 20x10
    while len(result) < 20:
        result.append([' '] * 10)
    
    return result


def _evaluate_node(node: SearchNode) -> float:
    """评估节点分数"""
    board = node.state.get('board', [])
    
    if not board:
        return 0.0
    
    return evaluate_state(board)


def evaluate_with_planning(
    board: Board,
    piece_type: str,
    use_cot: bool = True,
    use_tree_search: bool = True
) -> PlayerAction:
    """
    使用规划找到最佳动作
    
    Args:
        board: 当前棋盘
        piece_type: 当前方块类型
        use_cot: 是否使用思维链
        use_tree_search: 是否使用树搜索
        
    Returns:
        最佳动作
    """
    if use_tree_search:
        return find_best_action(board, piece_type, depth=2)
    else:
        # 简单贪心策略
        return PlayerAction.WAIT