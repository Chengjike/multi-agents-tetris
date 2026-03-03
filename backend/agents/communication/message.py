"""
消息协议模块

定义 Agent 之间的通信消息格式
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class MessageType(Enum):
    """消息类型"""
    PROPOSE = "propose"      # 提议
    THREAT = "threat"        # 威胁
    PROMISE = "promise"      # 承诺
    INFO = "info"            # 信息
    ACKNOWLEDGE = "ack"     # 确认


@dataclass
class Message:
    """
    通信消息
    
    用于 Agent 之间发送的自然语言消息
    """
    sender_id: int           # 发送者 ID
    receiver_id: Optional[int]  # 接收者 ID，None 表示广播
    message_type: MessageType  # 消息类型
    content: str             # 消息内容
    timestamp: float = field(default_factory=time.time)  # 时间戳
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type.value,
            'content': self.content,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """从字典创建"""
        return cls(
            sender_id=data['sender_id'],
            receiver_id=data.get('receiver_id'),
            message_type=MessageType(data['message_type']),
            content=data['content'],
            timestamp=data.get('timestamp', time.time())
        )
    
    def is_broadcast(self) -> bool:
        """是否是广播消息"""
        return self.receiver_id is None
    
    def is_for_player(self, player_id: int) -> bool:
        """是否发送给指定玩家"""
        if self.receiver_id is None:
            return True  # 广播对所有人可见
        return self.receiver_id == player_id
    
    def __str__(self) -> str:
        receiver = "广播" if self.receiver_id is None else f"玩家{self.receiver_id}"
        return f"[玩家{self.sender_id} -> {receiver}] {self.message_type.value}: {self.content}"