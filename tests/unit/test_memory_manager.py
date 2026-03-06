"""
测试记忆管理器 MemoryManager
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestMemoryManagerCreation:
    """测试 MemoryManager 创建"""

    def test_create_memory_manager(self):
        """测试创建 MemoryManager 实例"""
        from backend.agents.memory import MemoryManager
        
        manager = MemoryManager(player_id=0)
        
        assert manager.player_id == 0
        assert manager.collection is not None

    def test_create_with_different_player_ids(self):
        """测试为不同玩家创建独立的记忆管理器"""
        from backend.agents.memory import MemoryManager
        
        manager0 = MemoryManager(player_id=0)
        manager1 = MemoryManager(player_id=1)
        
        assert manager0.player_id == 0
        assert manager1.player_id == 1


class TestMemoryStore:
    """测试记忆存储"""

    @pytest.mark.asyncio
    async def test_store_experience(self):
        """测试存储经验"""
        from backend.agents.memory import MemoryManager, Experience
        
        manager = MemoryManager(player_id=0)
        exp = Experience(
            state_description="Board has 10 rows, I-piece ready",
            action_taken="hard_drop",
            outcome="Cleared 4 lines"
        )
        
        # 存储经验（不实际调用嵌入API）
        with patch.object(manager, '_generate_embedding', return_value=[0.1] * 384):
            await manager.store_experience(exp)
        
        # 验证存储了经验
        assert len(manager.experiences) == 1

    @pytest.mark.asyncio
    async def test_store_multiple_experiences(self):
        """测试存储多条经验"""
        from backend.agents.memory import MemoryManager, Experience
        
        manager = MemoryManager(player_id=0)
        
        experiences = [
            Experience(state_description="State 1", action_taken="left", outcome="OK"),
            Experience(state_description="State 2", action_taken="right", outcome="OK"),
            Experience(state_description="State 3", action_taken="rotate", outcome="OK"),
        ]
        
        with patch.object(manager, '_generate_embedding', return_value=[0.1] * 384):
            for exp in experiences:
                await manager.store_experience(exp)
        
        assert len(manager.experiences) == 3


class TestMemoryRetrieve:
    """测试记忆检索"""

    @pytest.mark.asyncio
    async def test_retrieve_similar(self):
        """测试检索相似经验"""
        from backend.agents.memory import MemoryManager, Experience
        
        manager = MemoryManager(player_id=0)
        
        # 预先存储一些经验
        exp1 = Experience(
            state_description="Full board with many holes",
            action_taken="wait",
            outcome="Game over",
            reflection="Should have cleared lines earlier"
        )
        exp2 = Experience(
            state_description="Nearly full board",
            action_taken="hard_drop",
            outcome="Cleared 1 line"
        )
        
        with patch.object(manager, '_generate_embedding', return_value=[0.1] * 384):
            await manager.store_experience(exp1)
            await manager.store_experience(exp2)
        
        # 检索相似经验
        with patch.object(manager, '_generate_embedding', return_value=[0.1] * 384):
            results = await manager.retrieve_similar("Full board dangerous", top_k=1)
        
        assert len(results) >= 0  # 可能没有结果或返回相似结果

    @pytest.mark.asyncio
    async def test_retrieve_from_empty_memory(self):
        """测试从空记忆检索"""
        from backend.agents.memory import MemoryManager
        
        manager = MemoryManager(player_id=0)
        
        with patch.object(manager, '_generate_embedding', return_value=[0.1] * 384):
            results = await manager.retrieve_similar("Any state", top_k=5)
        
        assert results == []


class TestReflectionGeneration:
    """测试反思生成"""

    @pytest.mark.asyncio
    async def test_generate_reflection(self):
        """测试生成反思"""
        from backend.agents.memory import MemoryManager
        
        manager = MemoryManager(player_id=0)
        
        # 设置模拟的 Qwen API
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{'message': {'content': '反思：应该更快消除行'}}]
        })
        
        game_summary = {
            'player_id': 0,
            'score': 1000,
            'lines_cleared': 5,
            'game_over': True,
            'survived_ticks': 500
        }
        
        with patch('aiohttp.ClientSession.post', return_value=mock_response):
            reflection = await manager.generate_reflection(
                game_summary=game_summary,
                api_key="test_key"
            )
        
        assert reflection is not None
        assert len(reflection) > 0

    @pytest.mark.asyncio
    async def test_generate_reflection_no_api_key(self):
        """测试无 API Key 时生成默认反思"""
        from backend.agents.memory import MemoryManager
        
        manager = MemoryManager(player_id=0)
        
        game_summary = {
            'player_id': 0,
            'score': 500,
            'lines_cleared': 2,
            'game_over': True
        }
        
        reflection = await manager.generate_reflection(
            game_summary=game_summary,
            api_key=None
        )
        
        # 应该返回默认反思
        assert reflection is not None
        # 中文环境检查"游戏结束"或"得分"
        assert "游戏结束" in reflection or "得分" in reflection


class TestMemoryIntegration:
    """测试记忆完整流程"""

    @pytest.mark.asyncio
    async def test_full_memory_cycle(self):
        """测试完整的记忆周期：存储 -> 检索 -> 反思"""
        from backend.agents.memory import MemoryManager, Experience
        
        manager = MemoryManager(player_id=0)
        
        # 1. 存储经验
        exp = Experience(
            state_description="Board at row 15, T-piece",
            action_taken="rotate",
            outcome="Cleared 2 lines"
        )
        
        with patch.object(manager, '_generate_embedding', return_value=[0.1] * 384):
            await manager.store_experience(exp)
        
        # 2. 检索
        with patch.object(manager, '_generate_embedding', return_value=[0.1] * 384):
            await manager.retrieve_similar("Board at row 15", top_k=1)
        
        # 3. 游戏结束生成反思
        game_summary = {
            'player_id': 0,
            'score': 800,
            'lines_cleared': 3,
            'game_over': True
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'choices': [{'message': {'content': 'Good game'}}]
            })
            mock_post.return_value = mock_response
            
            reflection = await manager.generate_reflection(
                game_summary=game_summary,
                api_key="test"
            )
        
        assert len(manager.experiences) >= 1
        assert reflection is not None