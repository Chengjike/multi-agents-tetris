"""
测试用例：Qwen Agent

调用 Qwen API 的 AI Agent
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.agents.qwen_agent import QwenAgent


class TestQwenAgentCreation:
    """测试Agent创建"""

    def test_agent_creation(self):
        """测试创建Agent"""
        agent = QwenAgent(player_id=0, api_key='test_key')
        assert agent.player_id == 0
        assert agent.api_key == 'test_key'

    def test_default_timeout(self):
        """测试默认超时"""
        agent = QwenAgent(player_id=0, api_key='test_key')
        assert agent.timeout == 5.0  # 默认5秒超时


class TestQwenAgentPrompt:
    """测试Prompt生成"""

    def test_build_game_state_prompt(self):
        """测试游戏状态提示"""
        agent = QwenAgent(player_id=0, api_key='test_key')

        # 模拟游戏状态
        mock_game = Mock()
        mock_game.board.get_board_data.return_value = [[0] * 10] * 20
        mock_game.current_piece.type.value = 'T'
        mock_game.current_piece.x = 3
        mock_game.current_piece.y = 0
        mock_game.current_piece.rotation = 0
        mock_game.score = 100

        prompt = agent._build_prompt(mock_game)

        # 检查棋盘状态格式
        assert '当前棋盘状态' in prompt
        assert 'T' in prompt

    def test_available_actions_in_prompt(self):
        """测试可用动作在提示中"""
        agent = QwenAgent(player_id=0, api_key='test_key')

        prompt = agent._build_action_prompt(['left', 'right', 'rotate'])

        assert 'left' in prompt
        assert 'right' in prompt
        assert 'rotate' in prompt


class TestQwenAgentResponse:
    """测试响应解析"""

    def test_parse_valid_response(self):
        """测试解析有效响应"""
        agent = QwenAgent(player_id=0, api_key='test_key')

        response = '{"action": "left", "reasoning": "Because it is better"}'
        result = agent._parse_response(response)

        assert result['action'] == 'left'
        assert 'reasoning' in result

    def test_parse_invalid_response(self):
        """测试解析无效响应"""
        agent = QwenAgent(player_id=0, api_key='test_key')

        response = 'invalid json'
        result = agent._parse_response(response)

        assert result is None


class TestQwenAgentMock:
    """测试模拟调用"""

    @pytest.mark.asyncio
    async def test_decide_with_mock(self):
        """测试使用mock API"""
        agent = QwenAgent(player_id=0, api_key='test_key')

        mock_game = Mock()
        mock_game.board.get_board_data.return_value = [[0] * 10] * 20
        mock_game.current_piece.type.value = 'T'
        mock_game.current_piece.x = 3
        mock_game.current_piece.y = 0
        mock_game.current_piece.rotation = 0
        mock_game.score = 0

        # 模拟API调用
        with patch.object(agent, '_call_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"action": "wait"}'
            action = await agent.decide(mock_game)

            assert action is not None