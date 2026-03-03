"""
树搜索模块

使用 BFS/DFS 搜索最佳动作序列
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from backend.game.tetris import PlayerAction


@dataclass
class SearchNode:
    """
    搜索树节点
    """
    state: Dict[str, Any]       # 棋盘状态
    action: Optional[PlayerAction]  # 执行的动作
    parent: Optional['SearchNode'] = None  # 父节点
    children: List['SearchNode'] = field(default_factory=list)  # 子节点
    depth: int = 0              # 深度
    score: float = 0.0          # 评估分数
    lines_cleared: int = 0      # 消除行数
    
    def is_leaf(self) -> bool:
        return len(self.children) == 0


class SearchTree:
    """
    搜索树
    
    用于存储所有可能的动作序列及其评估结果
    """
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.root: Optional[SearchNode] = None
        
    def create_root(self, initial_state: Dict[str, Any]) -> SearchNode:
        """创建根节点"""
        self.root = SearchNode(
            state=initial_state,
            action=None,
            parent=None,
            depth=0
        )
        return self.root
    
    def get_best_leaf(self) -> SearchNode:
        """获取分数最高的叶节点"""
        if not self.root:
            raise ValueError("Tree has no root")
        
        return self._find_best_leaf(self.root)
    
    def _find_best_leaf(self, node: SearchNode) -> SearchNode:
        """递归查找最佳叶节点"""
        if node.is_leaf():
            return node
        
        best_child = max(node.children, key=lambda n: n.score)
        return self._find_best_leaf(best_child)
    
    def get_best_path(self) -> List[PlayerAction]:
        """获取从根到最佳叶节点的路径"""
        if not self.root:
            return []
        
        path = []
        node = self._find_best_leaf(self.root)
        
        # 回溯获取路径
        while node.parent is not None:
            if node.action is not None:
                path.insert(0, node.action)
            node = node.parent
        
        return path


def expand_actions(
    node: SearchNode,
    actions: List[PlayerAction]
) -> List[SearchNode]:
    """
    展开动作节点
    
    Args:
        node: 父节点
        actions: 可用动作列表
        
    Returns:
        子节点列表
    """
    children = []
    
    for action in actions:
        child = SearchNode(
            state=node.state.copy(),  # 复制状态
            action=action,
            parent=node,
            depth=node.depth + 1
        )
        children.append(child)
        node.children.append(child)
    
    return children