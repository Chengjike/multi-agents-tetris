"""
游戏管理器

管理多个游戏实例、主循环和惩罚
"""
import asyncio
from typing import List, Dict, Any, Optional
from backend.game.tetris import TetrisGame, GameStatus, PlayerAction
from backend.game.punishment import PunishmentManager
from backend.agents.rule_agent import RuleAgent
from backend.protocol.messages import create_game_state, create_game_over


class GameManager:
    """游戏管理器"""

    def __init__(
        self,
        num_players: int = 3,
        tick_interval: float = 0.1,  # 100ms per tick
    ):
        self.num_players = num_players
        self.tick_interval = tick_interval

        # 创建游戏实例
        self.games: List[TetrisGame] = [
            TetrisGame(player_id=i) for i in range(num_players)
        ]

        # 创建AI代理
        self.agents: List[RuleAgent] = [
            RuleAgent(player_id=i) for i in range(num_players)
        ]

        # 惩罚管理器
        self.punishment_manager = PunishmentManager(num_players)

        # 游戏状态
        self.game_status = GameStatus.WAITING
        self.tick_count = 0
        self.running = False
        self._task: Optional[asyncio.Task] = None

    def start_game(self) -> None:
        """开始游戏"""
        for game in self.games:
            game.start()
        self.game_status = GameStatus.RUNNING
        self.running = True

    def stop_game(self) -> None:
        """停止游戏"""
        self.running = False
        self.game_status = GameStatus.PAUSED

    async def game_loop(self) -> None:
        """游戏主循环"""
        while self.running:
            self.tick()
            await asyncio.sleep(self.tick_interval)

    def tick(self) -> None:
        """单次游戏tick"""
        if not self.running or self.game_status != GameStatus.RUNNING:
            return

        self.tick_count += 1

        # 每个玩家执行动作
        for i, (game, agent) in enumerate(zip(self.games, self.agents)):
            if game.status == GameStatus.GAME_OVER:
                continue

            # AI决定动作
            action = agent.decide(game)

            # 执行动作
            game.perform_action(action)

            # 检查是否需要生成新方块（硬降后会自动生成）
            # 软降和移动后检查碰撞
            if game.current_piece and game.board.check_collision(game.current_piece):
                # 方块无法移动，需要放置
                game.spawn_new_piece()
                game._process_line_clearing()

            # 记录消除行数
            if game.current_piece is None:
                lines = 0
            else:
                # 从上次tick计算消除行数
                lines = game.lines_cleared_total

            # 记录并检查惩罚
            if lines > 0:
                self.punishment_manager.record_lines_cleared(i, lines)

        # 应用惩罚
        self.apply_punishments()

        # 检查游戏结束
        if self.check_all_game_over():
            self.game_status = GameStatus.GAME_OVER
            self.running = False

    def apply_punishments(self) -> None:
        """应用惩罚"""
        self.punishment_manager.apply_all_punishments(self.games)

    def check_all_game_over(self) -> bool:
        """检查是否所有游戏都结束"""
        alive_count = sum(
            1 for game in self.games
            if game.status != GameStatus.GAME_OVER
        )
        return alive_count == 0

    def get_game_states(self) -> List[Dict[str, Any]]:
        """获取所有游戏状态"""
        return [game.get_state() for game in self.games]

    def get_broadcast_state(self) -> Dict[str, Any]:
        """获取广播给客户端的状态"""
        return create_game_state(
            players=self.games,
            game_status=self.game_status.value,
            tick=self.tick_count,
        )

    def get_winner(self) -> Optional[int]:
        """获取获胜者"""
        if not self.check_all_game_over():
            return None

        # 按分数排序
        scores = [(i, game.score) for i, game in enumerate(self.games)]
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[0][0]

    def get_final_scores(self) -> List[int]:
        """获取最终分数"""
        return [game.score for game in self.games]

    async def run(self) -> None:
        """运行游戏（异步）"""
        self.start_game()
        await self.game_loop()