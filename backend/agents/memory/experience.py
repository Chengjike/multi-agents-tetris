"""
经验数据结构的定义

存储 Agent 的游戏经历，包含状态描述、动作、结果和反思
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Experience:
    """
    游戏经验数据
    
    用于存储 Agent 的关键游戏状态及其对应的动作和结果，
    支持长期记忆存储和检索。
    """
    state_description: str      # 状态的文本描述（用于嵌入）
    action_taken: str           # 当时采取的动作
    outcome: str                # 结果（如"成功消除两行"）
    reflection: Optional[str] = None      # 事后反思（可选）
    embedding: Optional[List[float]] = None  # 向量嵌入（可选）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'state_description': self.state_description,
            'action_taken': self.action_taken,
            'outcome': self.outcome,
            'reflection': self.reflection,
            'embedding': self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Experience':
        """从字典创建"""
        return cls(
            state_description=data.get('state_description', ''),
            action_taken=data.get('action_taken', ''),
            outcome=data.get('outcome', ''),
            reflection=data.get('reflection'),
            embedding=data.get('embedding')
        )