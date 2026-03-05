"""
游戏管理器

管理多个游戏实例、主循环和惩罚、通信
"""
import asyncio
from typing import List, Dict, Any, Optional
from backend.game.tetris import TetrisGame, GameStatus, PlayerAction
from backend.game.punishment import PunishmentManager
from backend.agents.rule_agent import RuleAgent
from backend.agents.communication import MessageChannel, Message
from backend.protocol.messages import create_game_state, create_game_over


class GameManager:
    """游戏管理器"""

    # 速度配置：分数越高，tick间隔越短（速度越快）
    BASE_TICK_INTERVAL = 0.2  # 基础速度：200ms per tick
    MIN_TICK_INTERVAL = 0.05  # 最快速度：50ms per tick
    SPEED_INCREASE_SCORE = 10  # 每增加10分，速度提升一次

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
        
        # 通信通道
        self.message_channel = MessageChannel(num_players=num_players)
        
        # 游戏反思记录
        self.reflections: Dict[int, str] = {}

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

    def get_current_tick_interval(self) -> float:
        """根据最高分数计算当前的 tick 间隔（分数越高速度越快）"""
        # 获取所有玩家中的最高分数
        max_score = max(game.score for game in self.games) if self.games else 0

        # 计算速度等级
        speed_level = max_score // self.SPEED_INCREASE_SCORE

        # 计算当前的 tick 间隔
        current_interval = self.BASE_TICK_INTERVAL - (speed_level * 0.01)

        # 确保不低于最小间隔
        return max(current_interval, self.MIN_TICK_INTERVAL)

    async def game_loop(self) -> None:
        """游戏主循环"""
        while self.running:
            self.tick()
            # 使用动态速度
            current_interval = self.get_current_tick_interval()
            await asyncio.sleep(current_interval)

    def tick(self) -> None:
        """单次游戏tick"""
        if not self.running or self.game_status != GameStatus.RUNNING:
            return

        self.tick_count += 1

        # 每个玩家执行动作
        for i, (game, agent) in enumerate(zip(self.games, self.agents)):
            if game.status == GameStatus.GAME_OVER:
                continue

            # 先执行方块自动下落
            game.tick()

            # 检查游戏是否结束
            if game.status == GameStatus.GAME_OVER:
                continue

            # 检查棋盘是否已满（游戏结束条件）
            if game.check_game_over():
                game.status = GameStatus.GAME_OVER
                continue

            # 检查自动下落是否导致需要生成新方块
            if game.current_piece is None:
                continue

            # 如果自动下落导致碰撞（方块落地），则生成新方块
            if game.board.check_collision(game.current_piece):
                result = game.spawn_new_piece()
                if not result:
                    # 游戏结束
                    continue
                game._process_line_clearing()

            # 检查游戏是否结束
            if game.status == GameStatus.GAME_OVER:
                continue

            # AI决定动作
            action = agent.decide(game)

            # 执行动作
            game.perform_action(action)

            # 注意：spawn_new_piece() 已经在 perform_action() 中处理了
            # 特别是 HARD_DROP 会自动调用 spawn_new_piece()
            # 对于其他动作（SOFT_DROP, MOVE_LEFT, MOVE_RIGHT, ROTATE, WAIT），如果碰撞了也需要生成新方块
            if action != PlayerAction.HARD_DROP:
                if game.current_piece and game.board.check_collision(game.current_piece):
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
    
    # ========== 通信功能 ==========
    
    def broadcast_message(
        self,
        sender_id: int,
        content: str
    ) -> bool:
        """
        广播消息给所有其他玩家
        
        Args:
            sender_id: 发送者 ID
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        from backend.agents.communication import Message, MessageType
        
        msg = Message(
            sender_id=sender_id,
            receiver_id=None,  # 广播
            message_type=MessageType.INFO,
            content=content
        )
        
        return self.message_channel.send_message(msg)
    
    def get_player_messages(
        self,
        player_id: int,
        count: int = 10
    ) -> List[Message]:
        """
        获取玩家收到的消息
        
        Args:
            player_id: 玩家 ID
            count: 消息数量
            
        Returns:
            消息列表
        """
        return self.message_channel.get_recent_messages(player_id, count)
    
    # ========== 反思功能 ==========
    
    async def trigger_reflections(
        self,
        agent_reflection_method: callable
    ) -> Dict[int, str]:
        """
        触发所有存活玩家的反思生成
        
        Args:
            agent_reflection_method: 回调方法，签名为 async fn(player_id, game) -> str
            
        Returns:
            玩家ID到反思内容的映射
        """
        for i, game in enumerate(self.games):
            if game.status != GameStatus.GAME_OVER:
                try:
                    reflection = await agent_reflection_method(i, game)
                    self.reflections[i] = reflection
                except Exception:
                    self.reflections[i] = "反思生成失败"
        
        return self.reflections
    
    def get_reflection(self, player_id: int) -> Optional[str]:
        """
        获取玩家反思
        
        Args:
            player_id: 玩家 ID
            
        Returns:
            反思内容，如果不存在则返回 None
        """
        return self.reflections.get(player_id)
    
    def get_all_reflections(self) -> Dict[int, str]:
        """获取所有玩家反思"""
        return self.reflections.copy()