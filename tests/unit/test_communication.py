"""
测试 Agent 通信与协作模块
"""
import pytest
from unittest.mock import Mock
from dataclasses import asdict


class TestMessageProtocol:
    """测试消息协议"""

    def test_create_propose_message(self):
        """测试创建提议消息"""
        from backend.agents.communication.message import Message, MessageType
        
        msg = Message(
            sender_id=0,
            receiver_id=1,
            message_type=MessageType.PROPOSE,
            content="让我们一起攻击玩家2！"
        )
        
        assert msg.sender_id == 0
        assert msg.receiver_id == 1
        assert msg.message_type == MessageType.PROPOSE
        assert msg.content == "让我们一起攻击玩家2！"

    def test_create_threat_message(self):
        """测试创建威胁消息"""
        from backend.agents.communication.message import Message, MessageType
        
        msg = Message(
            sender_id=0,
            receiver_id=2,
            message_type=MessageType.THREAT,
            content="如果你继续，我会攻击你！"
        )
        
        assert msg.message_type == MessageType.THREAT

    def test_create_promise_message(self):
        """测试创建承诺消息"""
        from backend.agents.communication.message import Message, MessageType
        
        msg = Message(
            sender_id=1,
            receiver_id=0,
            message_type=MessageType.PROMISE,
            content="我保证不攻击你"
        )
        
        assert msg.message_type == MessageType.PROMISE

    def test_create_info_message(self):
        """测试创建信息消息"""
        from backend.agents.communication.message import Message, MessageType
        
        msg = Message(
            sender_id=0,
            receiver_id=None,  # 广播
            message_type=MessageType.INFO,
            content="玩家2已经game over"
        )
        
        assert msg.receiver_id is None  # 广播
        assert msg.message_type == MessageType.INFO

    def test_message_to_dict(self):
        """测试消息转字典"""
        from backend.agents.communication.message import Message, MessageType
        
        msg = Message(
            sender_id=0,
            receiver_id=1,
            message_type=MessageType.PROPOSE,
            content="Test"
        )
        
        msg_dict = msg.to_dict()
        
        assert isinstance(msg_dict, dict)
        assert msg_dict['sender_id'] == 0
        assert msg_dict['message_type'] == 'propose'


class TestMessageChannel:
    """测试消息通道"""

    def test_create_channel(self):
        """测试创建消息通道"""
        from backend.agents.communication.channel import MessageChannel
        
        channel = MessageChannel(num_players=3)
        
        assert channel.num_players == 3
        # queues 是 defaultdict，开始时为空是正常的
        assert channel.max_history == 100

    def test_send_message(self):
        """测试发送消息"""
        from backend.agents.communication.channel import MessageChannel
        from backend.agents.communication.message import Message, MessageType
        
        channel = MessageChannel(num_players=3)
        
        msg = Message(
            sender_id=0,
            receiver_id=1,
            message_type=MessageType.INFO,
            content="Hello"
        )
        
        success = channel.send_message(msg)
        
        assert success is True

    def test_receive_message(self):
        """测试接收消息"""
        from backend.agents.communication.channel import MessageChannel
        from backend.agents.communication.message import Message, MessageType
        
        channel = MessageChannel(num_players=3)
        
        # 玩家0发送消息给玩家1
        msg = Message(
            sender_id=0,
            receiver_id=1,
            message_type=MessageType.INFO,
            content="Test message"
        )
        channel.send_message(msg)
        
        # 玩家1接收消息
        messages = channel.get_messages(1)
        
        assert len(messages) >= 1

    def test_broadcast_message(self):
        """测试广播消息"""
        from backend.agents.communication.channel import MessageChannel
        from backend.agents.communication.message import Message, MessageType
        
        channel = MessageChannel(num_players=3)
        
        # 广播消息
        msg = Message(
            sender_id=0,
            receiver_id=None,
            message_type=MessageType.INFO,
            content="Broadcast"
        )
        channel.send_message(msg)
        
        # 所有玩家都应该能收到
        for player_id in range(3):
            messages = channel.get_messages(player_id)
            # 广播消息对所有人可见
            assert len(messages) >= 1

    def test_clear_messages(self):
        """测试清除消息"""
        from backend.agents.communication.channel import MessageChannel
        from backend.agents.communication.message import Message, MessageType
        
        channel = MessageChannel(num_players=3)
        
        msg = Message(
            sender_id=0,
            receiver_id=1,
            message_type=MessageType.INFO,
            content="Test"
        )
        channel.send_message(msg)
        
        # 清除玩家1的消息
        channel.clear_messages(1)
        
        messages = channel.get_messages(1)
        assert len(messages) == 0


class TestCommunicationStrategy:
    """测试通信策略"""

    def test_generate_propose_message(self):
        """测试生成提议消息"""
        from backend.agents.communication.strategy import generate_propose_message
        
        leader_id = 1
        target_id = 2
        
        msg = generate_propose_message(leader_id, target_id)
        
        assert msg is not None
        assert "攻击" in msg or "联手" in msg or "一起" in msg

    def test_generate_threat_message(self):
        """测试生成威胁消息"""
        from backend.agents.communication.strategy import generate_threat_message
        
        enemy_id = 2
        
        msg = generate_threat_message(enemy_id)
        
        assert msg is not None

    def test_generate_promise_message(self):
        """测试生成承诺消息"""
        from backend.agents.communication.strategy import generate_promise_message
        
        msg = generate_promise_message()
        
        assert msg is not None

    def test_analyze_received_message(self):
        """测试分析接收到的消息"""
        from backend.agents.communication.strategy import analyze_message_intent
        
        # 分析提议
        propose_text = "我们联手攻击玩家2吧！"
        intent = analyze_message_intent(propose_text)
        
        assert intent is not None