"""
通信模块 - Agent间通信与协作能力

包含：
- Message 消息协议
- MessageChannel 消息通道
- Strategy 通信策略
"""
from backend.agents.communication.message import Message, MessageType
from backend.agents.communication.channel import MessageChannel
from backend.agents.communication.strategy import (
    generate_propose_message,
    generate_threat_message,
    generate_promise_message,
    analyze_message_intent
)

__all__ = [
    'Message', 'MessageType',
    'MessageChannel',
    'generate_propose_message',
    'generate_threat_message', 
    'generate_promise_message',
    'analyze_message_intent'
]