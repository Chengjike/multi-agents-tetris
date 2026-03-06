"""
消息通道模块

管理 Agent 之间的消息传递
"""
from typing import List, Dict
from collections import defaultdict
from backend.agents.communication.message import Message


class MessageChannel:
    """
    消息通道
    
    管理多个玩家之间的消息传递
    """
    
    def __init__(self, num_players: int = 3, max_history: int = 100):
        self.num_players = num_players
        self.max_history = max_history
        
        # 每个玩家的消息队列
        self.queues: Dict[int, List[Message]] = defaultdict(list)
        
        # 全局消息历史
        self.global_history: List[Message] = []
    
    def send_message(self, message: Message) -> bool:
        """
        发送消息
        
        Args:
            message: 消息对象
            
        Returns:
            是否发送成功
        """
        # 添加到全局历史
        self.global_history.append(message)
        
        # 限制历史长度
        if len(self.global_history) > self.max_history:
            self.global_history = self.global_history[-self.max_history:]
        
        # 根据接收者分发
        if message.receiver_id is None:
            # 广播：所有玩家都能看到
            for player_id in range(self.num_players):
                self.queues[player_id].append(message)
        else:
            # 单播：只发给指定玩家
            if 0 <= message.receiver_id < self.num_players:
                self.queues[message.receiver_id].append(message)
        
        # 限制每个队列的长度
        for player_id in range(self.num_players):
            if len(self.queues[player_id]) > self.max_history:
                self.queues[player_id] = self.queues[player_id][-self.max_history:]
        
        return True
    
    def get_messages(self, player_id: int) -> List[Message]:
        """
        获取玩家未读消息
        
        Args:
            player_id: 玩家 ID
            
        Returns:
            消息列表
        """
        return self.queues.get(player_id, [])
    
    def get_recent_messages(
        self,
        player_id: int,
        count: int = 10
    ) -> List[Message]:
        """
        获取玩家最近的 N 条消息
        
        Args:
            player_id: 玩家 ID
            count: 消息数量
            
        Returns:
            消息列表
        """
        messages = self.get_messages(player_id)
        return messages[-count:]
    
    def clear_messages(self, player_id: int) -> None:
        """
        清除玩家的消息
        
        Args:
            player_id: 玩家 ID
        """
        self.queues[player_id] = []
    
    def clear_all_messages(self) -> None:
        """清除所有消息"""
        self.queues.clear()
        self.global_history.clear()
    
    def get_all_messages(self) -> List[Message]:
        """获取全局消息历史"""
        return self.global_history.copy()
    
    def get_messages_between(
        self,
        player_a: int,
        player_b: int
    ) -> List[Message]:
        """获取两个玩家之间的消息历史"""
        messages = []
        
        for msg in self.global_history:
            # 发送者或接收者是 player_a 或 player_b
            if (msg.sender_id == player_a and msg.receiver_id == player_b) or \
               (msg.sender_id == player_b and msg.receiver_id == player_a) or \
               (msg.sender_id in [player_a, player_b] and msg.receiver_id is None):
                messages.append(msg)
        
        return messages