"""
惩罚机制模块

核心规则：当任意玩家一次消除4行时，立即在其他两个玩家的板子最底部随机增加一行障碍（留一个缺口）
"""
from typing import Dict, List, Any


class PunishmentManager:
    """惩罚管理器"""

    def __init__(self, num_players: int = 3):
        self.num_players = num_players
        # 待执行的惩罚列表
        self._pending_punishments: List[Dict[str, Any]] = []

    def record_lines_cleared(self, player_id: int, lines: int) -> Dict[str, Any]:
        """
        记录玩家消除的行数

        Args:
            player_id: 玩家ID
            lines: 消除的行数

        Returns:
            包含是否需要惩罚的信息
        """
        # 累积行数
        if not hasattr(self, '_accumulated_lines'):
            self._accumulated_lines = {i: 0 for i in range(self.num_players)}
        
        self._accumulated_lines[player_id] += lines

        result = {
            'player_id': player_id,
            'lines_cleared': lines,
            'accumulated': self._accumulated_lines[player_id],
            'should_punish': False,
            'punished_players': [],
        }

        # 检查是否达到惩罚条件（每累积4行）
        if self._accumulated_lines[player_id] >= 4:
            result['should_punish'] = True
            result['punished_players'] = [
                pid for pid in range(self.num_players) if pid != player_id
            ]

            # 添加到待执行惩罚
            self._pending_punishments.append({
                'from_player': player_id,
                'punished_players': result['punished_players'],
                'times': self._accumulated_lines[player_id] // 4,
            })

            # 重置累积
            self._accumulated_lines[player_id] = self._accumulated_lines[player_id] % 4

        return result

    def get_pending_punishments(self) -> List[Dict[str, Any]]:
        """获取待执行的惩罚列表"""
        return self._pending_punishments.copy()

    def clear_pending_punishments(self, from_player: int) -> None:
        """清除指定玩家的待执行惩罚"""
        self._pending_punishments = [
            p for p in self._pending_punishments if p['from_player'] != from_player
        ]

    def apply_punishment(self, board) -> None:
        """
        对棋盘应用惩罚（添加底部障碍行）

        Args:
            board: 要添加障碍行的棋盘
        """
        board.add_bottom_row()

    def apply_all_punishments(self, games: List) -> None:
        """
        对所有游戏应用待执行的惩罚

        Args:
            games: 游戏实例列表
        """
        for punishment in self._pending_punishments:
            punishment['from_player']
            times = punishment['times']

            for player_id in punishment['punished_players']:
                for _ in range(times):
                    games[player_id].board.add_bottom_row()

        # 清除已应用的惩罚
        self._pending_punishments = []

    def reset(self) -> None:
        """重置惩罚管理器"""
        self._accumulated_lines = {i: 0 for i in range(self.num_players)}
        self._pending_punishments = []