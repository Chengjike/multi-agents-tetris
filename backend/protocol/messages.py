"""
WebSocket 消息协议定义
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ServerMessage:
    """服务端消息基类"""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerMessage':
        return cls(**data)


@dataclass
class GameStateMessage(ServerMessage):
    """游戏状态消息"""
    type: str = 'game_state'
    players: List[Dict[str, Any]] = None
    game_status: str = 'waiting'
    tick: int = 0

    def __post_init__(self):
        if self.players is None:
            self.players = []


@dataclass
class GameOverMessage(ServerMessage):
    """游戏结束消息"""
    type: str = 'game_over'
    winner: int = -1
    final_scores: List[int] = None

    def __post_init__(self):
        if self.final_scores is None:
            self.final_scores = []


@dataclass
class ErrorMessage(ServerMessage):
    """错误消息"""
    type: str = 'error'
    error: str = ''


@dataclass
class ClientMessage:
    """客户端消息"""
    type: str = ''
    player_id: Optional[int] = None
    action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {'type': self.type}
        if self.player_id is not None:
            result['player_id'] = self.player_id
        if self.action is not None:
            result['action'] = self.action
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClientMessage':
        return cls(
            type=data.get('type', ''),
            player_id=data.get('player_id'),
            action=data.get('action'),
        )


def parse_message(data: str) -> Optional[ClientMessage]:
    """解析客户端消息"""
    import json
    try:
        parsed = json.loads(data)
        return ClientMessage.from_dict(parsed)
    except (json.JSONDecodeError, TypeError):
        return None


def create_game_state(players: List, game_status: str, tick: int = 0) -> Dict[str, Any]:
    """创建游戏状态消息"""
    player_states = []
    for player in players:
        state = player.get_state()
        player_states.append(state)

    return {
        'type': 'game_state',
        'players': player_states,
        'game_status': game_status,
        'tick': tick,
    }


def create_game_over(winner: int, final_scores: List[int]) -> Dict[str, Any]:
    """创建游戏结束消息"""
    return {
        'type': 'game_over',
        'winner': winner,
        'final_scores': final_scores,
    }


def create_error(error: str) -> Dict[str, Any]:
    """创建错误消息"""
    return {
        'type': 'error',
        'error': error,
    }