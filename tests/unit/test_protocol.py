"""
测试用例：WebSocket 消息协议

测试客户端-服务端消息格式
"""
from backend.protocol.messages import (
    ClientMessage,
    GameStateMessage,
    GameOverMessage,
    ErrorMessage,
)


class TestServerMessages:
    """测试服务端消息"""

    def test_game_state_message(self):
        """测试游戏状态消息"""
        msg = GameStateMessage(
            players=[
                {
                    'player_id': 0,
                    'board': [[0] * 10] * 20,
                    'current_piece': {'type': 'T', 'x': 3, 'y': 0, 'rotation': 0},
                    'score': 100,
                    'status': 'running',
                }
            ],
            game_status='running',
        )

        data = msg.to_dict()
        assert data['type'] == 'game_state'
        assert 'players' in data

    def test_game_over_message(self):
        """测试游戏结束消息"""
        msg = GameOverMessage(winner=0, final_scores=[100, 50, 0])

        data = msg.to_dict()
        assert data['type'] == 'game_over'
        assert data['winner'] == 0

    def test_error_message(self):
        """测试错误消息"""
        msg = ErrorMessage(error='Invalid action')

        data = msg.to_dict()
        assert data['type'] == 'error'
        assert data['error'] == 'Invalid action'


class TestClientMessages:
    """测试客户端消息"""

    def test_start_game_message(self):
        """测试开始游戏消息"""
        msg = ClientMessage(type='start')

        data = msg.to_dict()
        assert data['type'] == 'start'

    def test_action_message(self):
        """测试动作消息"""
        msg = ClientMessage(type='action', player_id=0, action='left')

        data = msg.to_dict()
        assert data['type'] == 'action'
        assert data['action'] == 'left'