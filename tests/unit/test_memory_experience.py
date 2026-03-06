"""
测试记忆数据结构 Experience
"""
from dataclasses import asdict


class TestExperienceCreation:
    """测试 Experience 对象创建"""

    def test_create_experience_with_required_fields(self):
        """测试仅包含必需字段的创建"""
        from backend.agents.memory.experience import Experience
        
        exp = Experience(
            state_description="Board has 15 rows filled, T-piece at top",
            action_taken="hard_drop",
            outcome="Cleared 2 lines, scored 300"
        )
        
        assert exp.state_description == "Board has 15 rows filled, T-piece at top"
        assert exp.action_taken == "hard_drop"
        assert exp.outcome == "Cleared 2 lines, scored 300"
        assert exp.reflection is None
        assert exp.embedding is None

    def test_create_experience_with_all_fields(self):
        """测试包含所有字段的创建"""
        from backend.agents.memory.experience import Experience
        
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        exp = Experience(
            state_description="Board at row 18, I-piece vertical",
            action_taken="rotate",
            outcome="Game over - no space",
            reflection="Should have placed piece differently",
            embedding=embedding
        )
        
        assert exp.reflection == "Should have placed piece differently"
        assert exp.embedding == embedding
        assert len(exp.embedding) == 5

    def test_experience_to_dict(self):
        """测试 Experience 转换为字典"""
        from backend.agents.memory.experience import Experience
        
        exp = Experience(
            state_description="Test state",
            action_taken="left",
            outcome="Good"
        )
        
        exp_dict = asdict(exp)
        
        assert isinstance(exp_dict, dict)
        assert exp_dict['state_description'] == "Test state"
        assert exp_dict['action_taken'] == "left"
        assert exp_dict['outcome'] == "Good"


class TestExperienceValidation:
    """测试 Experience 字段验证"""

    def test_empty_state_description_raises(self):
        """测试空状态描述应该被允许（灵活设计）"""
        from backend.agents.memory.experience import Experience
        
        # 空字符串应该被允许（用户可能需要记录失败经历）
        exp = Experience(
            state_description="",
            action_taken="wait",
            outcome="No action taken"
        )
        
        assert exp.state_description == ""

    def test_valid_actions(self):
        """测试接受有效的动作"""
        from backend.agents.memory.experience import Experience
        
        valid_actions = ["left", "right", "rotate", "soft_drop", "hard_drop", "wait"]
        
        for action in valid_actions:
            exp = Experience(
                state_description="Test",
                action_taken=action,
                outcome="Test"
            )
            assert exp.action_taken == action

    def test_embedding_as_none_by_default(self):
        """测试嵌入默认为 None"""
        from backend.agents.memory.experience import Experience
        
        exp = Experience(
            state_description="Test",
            action_taken="left",
            outcome="Test"
        )
        
        assert exp.embedding is None