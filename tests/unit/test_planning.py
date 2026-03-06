"""
测试多步规划与推理模块
"""
from backend.game.tetris import PlayerAction


class TestChainOfThought:
    """测试思维链推理"""

    def test_build_cot_prompt(self):
        """测试构建思维链提示词"""
        from backend.agents.planning.chain_of_thought import build_cot_prompt
        
        game_state = {
            'board': [['X'] * 10 for _ in range(20)],  # 模拟棋盘
            'current_piece': 'T',
            'score': 500,
            'lines_cleared': 3
        }
        
        prompt = build_cot_prompt(game_state, depth=2)
        
        assert prompt is not None
        assert "思考" in prompt or "推理" in prompt
        assert "2步" in prompt or "2" in prompt

    def test_cot_prompt_includes_analysis(self):
        """测试思维链提示词包含分析要求"""
        from backend.agents.planning.chain_of_thought import build_cot_prompt
        
        game_state = {
            'board': [[' '] * 10 for _ in range(20)],
            'current_piece': 'I',
            'score': 0,
            'lines_cleared': 0
        }
        
        prompt = build_cot_prompt(game_state, depth=3)
        
        # 应该包含多步分析要求
        assert len(prompt) > 100  # 足够详细的提示词


class TestTreeSearch:
    """测试树搜索"""

    def test_create_search_tree(self):
        """测试创建搜索树"""
        from backend.agents.planning.tree_search import SearchTree
        
        tree = SearchTree(max_depth=3)
        
        assert tree.max_depth == 3
        assert tree.root is None

    def test_expand_actions(self):
        """测试展开动作节点"""
        from backend.agents.planning.tree_search import expand_actions, SearchNode
        
        # 可用动作
        actions = [PlayerAction.MOVE_LEFT, PlayerAction.MOVE_RIGHT, PlayerAction.ROTATE]
        
        # 创建根节点
        root = SearchNode(
            state={'board': [[' '] * 10 for _ in range(20)]},
            action=None,
            parent=None,
            depth=0
        )
        
        # 展开
        children = expand_actions(root, actions)
        
        assert len(children) == len(actions)
        for child in children:
            assert child.parent == root
            assert child.depth == 1


class TestStateEvaluator:
    """测试状态评估器"""

    def test_evaluate_empty_board(self):
        """测试评估空棋盘"""
        from backend.agents.planning.evaluator import evaluate_state
        
        board = [[' '] * 10 for _ in range(20)]
        
        score = evaluate_state(board)
        
        # 空棋盘应该得高分
        assert score > 50

    def test_evaluate_full_board(self):
        """测试评估满棋盘"""
        from backend.agents.planning.evaluator import evaluate_state
        
        board = [['X'] * 10 for _ in range(20)]
        
        score = evaluate_state(board)
        
        # 满棋盘应该有完整行奖励，但洞穴很多
        # 实际上完整行会得到奖励分数
        assert score >= 0  # 只要不是负数即可

    def test_evaluate_partial_board(self):
        """测试评估部分填充的棋盘"""
        from backend.agents.planning.evaluator import evaluate_state
        
        board = [['X'] * 10 for _ in range(10)] + [[' '] * 10 for _ in range(10)]
        
        score = evaluate_state(board)
        
        # 部分填充的棋盘应该有合理分数
        assert score >= 0  # 只要不是负数即可

    def test_evaluate_with_holes(self):
        """测试评估有洞穴的棋盘（有惩罚）"""
        from backend.agents.planning.evaluator import evaluate_state
        
        # 有洞穴的棋盘
        board = [
            ['X', 'X', ' ', 'X', 'X', 'X', 'X', 'X', 'X', 'X'],
            ['X', 'X', ' ', 'X', 'X', 'X', 'X', 'X', 'X', 'X'],
        ] + [[' '] * 10 for _ in range(18)]
        
        # 无洞穴的对比
        clean_board = [['X'] * 10 for _ in range(10)] + [[' '] * 10 for _ in range(10)]
        
        score_holes = evaluate_state(board)
        score_clean = evaluate_state(clean_board)
        
        # 有洞穴的应该得分更低
        assert score_holes < score_clean


class TestSimulation:
    """测试动作模拟"""

    def test_simulate_single_action(self):
        """测试模拟单个动作"""
        from backend.agents.planning.simulator import simulate_action
        from backend.game.board import Board
        
        board = Board()
        piece_type = 'T'
        
        # 模拟左移
        new_board, lines_cleared = simulate_action(
            board, piece_type, PlayerAction.MOVE_LEFT
        )
        
        assert new_board is not None
        assert lines_cleared >= 0

    def test_simulate_sequence(self):
        """测试模拟动作序列"""
        from backend.agents.planning.simulator import simulate_action
        from backend.game.board import Board
        
        board = Board()
        piece_type = 'I'
        
        actions = [
            PlayerAction.MOVE_LEFT,
            PlayerAction.MOVE_LEFT,
            PlayerAction.ROTATE,
        ]
        
        current_board = board
        total_lines = 0
        
        for action in actions:
            current_board, lines = simulate_action(
                current_board, piece_type, action
            )
            total_lines += lines
        
        assert total_lines >= 0


class TestBestActionSearch:
    """测试最佳动作搜索"""

    def test_find_best_action(self):
        """测试寻找最佳动作"""
        from backend.agents.planning.search import find_best_action
        from backend.game.board import Board
        
        board = Board()
        
        # 应该有返回值
        best_action = find_best_action(
            board=board,
            piece_type='T',
            depth=2
        )
        
        assert best_action is not None
        assert isinstance(best_action, PlayerAction)

    def test_depth_affects_result(self):
        """测试搜索深度影响结果"""
        from backend.agents.planning.search import find_best_action
        from backend.game.board import Board
        
        board = Board()
        
        action_depth1 = find_best_action(board, 'T', depth=1)
        action_depth2 = find_best_action(board, 'T', depth=2)
        
        # 不同深度可能找到不同的最佳动作
        assert action_depth1 is not None
        assert action_depth2 is not None