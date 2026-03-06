"""
Qwen Agent

调用 Qwen API 进行决策的 AI Agent
支持：记忆与反思、多步规划、通信协作
"""
import json
import os
from typing import Dict, Any, List, Optional
import aiohttp

from backend.game.tetris import TetrisGame, PlayerAction
from backend.agents.rule_agent import RuleAgent
from backend.agents.memory import MemoryManager, Experience
from backend.agents.planning import build_cot_prompt
from backend.agents.communication import MessageChannel, Message, MessageType


class QwenAPIError(Exception):
    """Qwen API 错误"""
    pass


class QwenAgent:
    """基于 Qwen API 的 AI Agent
    
    支持增强功能：
    - 记忆与反思 (memory)
    - 多步规划 (planning)
    - 通信协作 (communication)
    """

    # 可用动作映射
    ACTION_MAP = {
        'left': PlayerAction.MOVE_LEFT,
        'right': PlayerAction.MOVE_RIGHT,
        'rotate': PlayerAction.ROTATE,
        'soft_drop': PlayerAction.SOFT_DROP,
        'hard_drop': PlayerAction.HARD_DROP,
        'wait': PlayerAction.WAIT,
    }

    SYSTEM_PROMPT = """你是一个俄罗斯方块 AI。

游戏规则：
- 棋盘大小：20行 x 10列
- 7种方块：I, J, L, O, S, T, Z
- 动作：left(左移), right(右移), rotate(旋转), soft_drop(软降), hard_drop(硬降), wait(等待)

策略：
1. 尽量消除行（消除4行会惩罚对手）
2. 保持棋盘低高度
3. 减少空洞
4. 保持棋盘平整
5. 考虑未来几步的动作序列

请以 JSON 格式返回决策：
{"action": "动作名", "reasoning": "简短理由", "message": "可选的通信消息"}
"""

    def __init__(
        self,
        player_id: int,
        api_key: str = None,
        model: str = "qwen-turbo",
        timeout: float = 5.0,
        fallback_agent: RuleAgent = None,
        enable_memory: bool = True,
        enable_planning: bool = True,
        enable_communication: bool = True,
    ):
        self.player_id = player_id
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY', '')
        self.model = model
        self.timeout = timeout
        self.fallback_agent = fallback_agent or RuleAgent(player_id)
        
        # 启用特性开关
        self.enable_memory = enable_memory
        self.enable_planning = enable_planning
        self.enable_communication = enable_communication

        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
        
        # 记忆管理器
        self.memory_manager = MemoryManager(player_id) if enable_memory else None
        
        # 通信通道
        self.message_channel = MessageChannel(num_players=3) if enable_communication else None
        
        # 当前游戏状态（用于记录经验）
        self._last_state_description = ""

    def _build_prompt(self, game: TetrisGame) -> str:
        """构建游戏状态提示（支持记忆和规划）"""
        # 获取棋盘状态
        board_data = game.board.get_board_data()

        # 转换为可视化格式
        board_str = self._format_board(board_data)

        # 当前方块信息
        piece_info = ""
        if game.current_piece:
            piece = game.current_piece
            piece_type = piece.type.value if hasattr(piece.type, 'value') else str(piece.type)
            piece_info = f"""
当前方块：{piece_type}
位置：({piece.x}, {piece.y})
旋转：{piece.rotation * 90}度
"""

        # 下一个方块
        next_info = ""
        if game.next_piece:
            next_piece = game.next_piece
            next_type = next_piece.type.value if hasattr(next_piece.type, 'value') else str(next_piece.type)
            next_info = f"下一个方块：{next_type}\n"

        prompt = f"""当前棋盘状态：
{board_str}
{piece_info}{next_info}分数：{game.score}
已消除行数：{game.lines_cleared}

"""

        # 添加记忆上下文
        if self.enable_memory and self.memory_manager:
            prompt += self._get_memory_context(game)
        
        # 添加规划（思维链）
        if self.enable_planning:
            game_state = {
                'board': board_data,
                'current_piece': game.current_piece.type.value if game.current_piece else '?',
                'score': game.score,
                'lines_cleared': game.lines_cleared
            }
            prompt += "\n" + build_cot_prompt(game_state, depth=2)
        
        # 添加通信消息
        if self.enable_communication and self.message_channel:
            prompt += "\n" + self._get_message_context()
        
        prompt += "\n请决定下一步动作。"
        
        # 保存状态描述用于记忆
        self._last_state_description = f"得分{game.score}, 消除{game.lines_cleared}行, 当前{game.current_piece.type.value if game.current_piece else '?'}"

        return prompt
    
    def _get_memory_context(self, game: TetrisGame) -> str:
        """获取记忆上下文"""
        if not self.memory_manager:
            return ""
        
        # 检索相似经验
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.new_event_loop()
        
        # 简单的状态描述
        
        # 注意：这里需要 async 调用，在 decide 中处理
        return "\n[历史经验将在这里显示]\n"
    
    def _get_message_context(self) -> str:
        """获取通信消息上下文"""
        if not self.message_channel:
            return ""
        
        messages = self.message_channel.get_recent_messages(self.player_id, count=3)
        if not messages:
            return ""
        
        msg_lines = ["\n其他玩家的消息："]
        for msg in messages:
            if msg.sender_id != self.player_id:
                msg_lines.append(f"- 玩家{msg.sender_id}: {msg.content}")
        
        return "\n".join(msg_lines) + "\n"

    def _format_board(self, board_data: List[List[int]]) -> str:
        """格式化棋盘为可视化字符串"""
        lines = []
        for row in board_data:
            line = "".join(["█" if cell else " " for cell in row])
            lines.append(line)
        return "\n".join(lines)

    def _build_action_prompt(self, available_actions: List[str]) -> str:
        """构建动作选择提示"""
        actions_str = ", ".join(available_actions)
        return f"可用动作：{actions_str}"

    async def _call_api(self, prompt: str) -> str:
        """调用 Qwen API"""
        if not self.api_key:
            raise QwenAPIError("No API key provided")

        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.conversation_history,
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.7,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        raise QwenAPIError(f"API returned {response.status}")

                    data = await response.json()
                    return data['choices'][0]['message']['content']

        except aiohttp.ClientError as e:
            raise QwenAPIError(f"Network error: {e}")

    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析 API 响应"""
        try:
            # 尝试提取 JSON
            if '{' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            return None
        except json.JSONDecodeError:
            return None

    async def decide(self, game: TetrisGame) -> PlayerAction:
        """
        决定最佳动作

        Args:
            game: 当前游戏实例

        Returns:
            最佳动作
        """
        try:
            # 构建提示
            prompt = self._build_prompt(game)
            available_actions = list(self.ACTION_MAP.keys())
            prompt += "\n" + self._build_action_prompt(available_actions)

            # 调用 API
            response = await self._call_api(prompt)

            # 解析响应
            result = self._parse_response(response)
            if result is None:
                return self.fallback_agent.decide(game)

            action_str = result.get('action', 'wait')
            result.get('reasoning', '')

            # 记录对话历史（限制长度）
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response})

            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            # 转换动作
            action = self.ACTION_MAP.get(action_str, PlayerAction.WAIT)
            return action

        except Exception:
            # 出错时使用 fallback
            return self.fallback_agent.decide(game)

    def clear_history(self) -> None:
        """清除对话历史"""
        self.conversation_history = []
    
    # ========== 记忆功能 ==========
    
    async def store_experience(
        self,
        action: PlayerAction,
        outcome: str
    ) -> None:
        """
        存储游戏经验
        
        Args:
            action: 采取的动作
            outcome: 结果描述
        """
        if not self.enable_memory or not self.memory_manager:
            return
        
        exp = Experience(
            state_description=self._last_state_description,
            action_taken=action.value,
            outcome=outcome
        )
        
        await self.memory_manager.store_experience(exp)
    
    async def generate_reflection(
        self,
        score: int,
        lines_cleared: int,
        game_over: bool
    ) -> Optional[str]:
        """
        生成游戏反思
        
        Args:
            score: 最终得分
            lines_cleared: 消除行数
            game_over: 是否游戏结束
            
        Returns:
            反思文本
        """
        if not self.enable_memory or not self.memory_manager:
            return None
        
        game_summary = {
            'player_id': self.player_id,
            'score': score,
            'lines_cleared': lines_cleared,
            'game_over': game_over
        }
        
        return await self.memory_manager.generate_reflection(
            game_summary=game_summary,
            api_key=self.api_key if self.api_key else None
        )
    
    # ========== 通信功能 ==========
    
    async def send_message(
        self,
        receiver_id: int,
        message_type: MessageType,
        content: str
    ) -> bool:
        """
        发送消息给其他玩家
        
        Args:
            receiver_id: 接收者 ID，None 表示广播
            message_type: 消息类型
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        if not self.enable_communication or not self.message_channel:
            return False
        
        msg = Message(
            sender_id=self.player_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content
        )
        
        return self.message_channel.send_message(msg)
    
    def get_messages(self, count: int = 10) -> List[Message]:
        """
        获取接收到的消息
        
        Args:
            count: 获取消息数量
            
        Returns:
            消息列表
        """
        if not self.enable_communication or not self.message_channel:
            return []
        
        return self.message_channel.get_recent_messages(self.player_id, count)
    
    def receive_broadcast(self) -> List[Message]:
        """接收广播消息"""
        if not self.enable_communication or not self.message_channel:
            return []
        return self.message_channel.get_recent_messages(self.player_id, count=5)