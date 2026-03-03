"""
Qwen Agent

调用 Qwen API 进行决策的 AI Agent
"""
import json
import os
from typing import Dict, Any, List, Optional
import aiohttp

from backend.game.tetris import TetrisGame, PlayerAction
from backend.agents.rule_agent import RuleAgent


class QwenAPIError(Exception):
    """Qwen API 错误"""
    pass


class QwenAgent:
    """基于 Qwen API 的 AI Agent"""

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

请以 JSON 格式返回决策：
{"action": "动作名", "reasoning": "简短理由"}
"""

    def __init__(
        self,
        player_id: int,
        api_key: str = None,
        model: str = "qwen-turbo",
        timeout: float = 5.0,
        fallback_agent: RuleAgent = None,
    ):
        self.player_id = player_id
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY', '')
        self.model = model
        self.timeout = timeout
        self.fallback_agent = fallback_agent or RuleAgent(player_id)

        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []

    def _build_prompt(self, game: TetrisGame) -> str:
        """构建游戏状态提示"""
        # 获取棋盘状态
        board_data = game.board.get_board_data()

        # 转换为可视化格式
        board_str = self._format_board(board_data)

        # 当前方块信息
        piece_info = ""
        if game.current_piece:
            piece = game.current_piece
            piece_info = f"""
当前方块：{piece.type.value}
位置：({piece.x}, {piece.y})
旋转：{piece.rotation * 90}度
"""

        # 下一个方块
        next_info = ""
        if game.next_piece:
            next_info = f"下一个方块：{game.next_piece.type.value}\n"

        prompt = f"""当前棋盘状态：
{board_str}
{piece_info}{next_info}分数：{game.score}

请决定下一步动作。"""

        return prompt

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
            reasoning = result.get('reasoning', '')

            # 记录对话历史（限制长度）
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response})

            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            # 转换动作
            action = self.ACTION_MAP.get(action_str, PlayerAction.WAIT)
            return action

        except Exception as e:
            # 出错时使用 fallback
            return self.fallback_agent.decide(game)

    def clear_history(self) -> None:
        """清除对话历史"""
        self.conversation_history = []