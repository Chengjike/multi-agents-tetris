"""
记忆管理器 - 长期记忆存储、检索和反思生成

使用 ChromaDB 作为向量数据库，sentence-transformers 作为嵌入模型
"""
import os
import json
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import asdict

import aiohttp
from backend.agents.memory.experience import Experience


class MemoryManager:
    """
    记忆管理器
    
    负责：
    - 存储游戏经验到向量数据库
    - 检索相似历史经验
    - 调用 LLM 生成反思
    """
    
    def __init__(
        self,
        player_id: int,
        max_experiences: int = 1000,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.player_id = player_id
        self.max_experiences = max_experiences
        self.embedding_model = embedding_model
        
        # 内存存储（简化版，可用 ChromaDB 替换）
        self.experiences: List[Experience] = []
        self.embeddings: List[List[float]] = []
        
        # 向量数据库集合（预留）
        self.collection = f"player_{player_id}_memories"
        
        # 反思缓存
        self._reflections: List[str] = []
    
    async def store_experience(self, experience: Experience) -> None:
        """
        存储游戏经验
        
        Args:
            experience: 经验对象
        """
        # 生成嵌入向量
        embedding = await self._generate_embedding(experience.state_description)
        experience.embedding = embedding
        
        # 存储
        self.experiences.append(experience)
        self.embeddings.append(embedding)
        
        # 限制最大数量
        if len(self.experiences) > self.max_experiences:
            self.experiences = self.experiences[-self.max_experiences:]
            self.embeddings = self.embeddings[-self.max_experiences:]
    
    async def retrieve_similar(
        self,
        state_description: str,
        top_k: int = 5
    ) -> List[Experience]:
        """
        检索相似的历史经验
        
        Args:
            state_description: 当前状态描述
            top_k: 返回最相似的 k 条经验
            
        Returns:
            相似经验列表
        """
        if not self.experiences:
            return []
        
        # 生成查询嵌入
        query_embedding = await self._generate_embedding(state_description)
        
        # 计算相似度（余弦相似度）
        similarities = []
        for i, emb in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_embedding, emb)
            similarities.append((i, sim))
        
        # 排序并返回 top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i in range(min(top_k, len(similarities))):
            idx = similarities[i][0]
            exp = self.experiences[idx]
            results.append(exp)
        
        return results
    
    async def generate_reflection(
        self,
        game_summary: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> str:
        """
        生成游戏反思
        
        Args:
            game_summary: 游戏总结数据
            api_key: Qwen API 密钥（可选）
            
        Returns:
            反思文本
        """
        # 如果没有 API key，返回默认反思
        if not api_key:
            return self._generate_default_reflection(game_summary)
        
        # 构建提示词
        prompt = self._build_reflection_prompt(game_summary)
        
        try:
            reflection = await self._call_qwen_api(prompt, api_key)
            self._reflections.append(reflection)
            return reflection
        except Exception as e:
            print(f"生成反思失败: {e}")
            return self._generate_default_reflection(game_summary)
    
    async def get_recent_reflections(self, limit: int = 5) -> List[str]:
        """获取最近的反思"""
        return self._reflections[-limit:]
    
    # ========== 内部方法 ==========
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入（简化版本）
        
        实际生产中应使用 sentence-transformers
        """
        # 简化实现：基于文本长度和字符生成伪嵌入
        # 生产环境请使用: from sentence_transformers import SentenceTransformer
        import hashlib
        
        # 生成固定维度的伪嵌入
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        embedding = []
        for i in range(384):  # all-MiniLM-L6-v2 输出 384 维
            embedding.append(((hash_val >> i) % 100) / 100.0)
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _build_reflection_prompt(self, game_summary: Dict[str, Any]) -> str:
        """构建反思提示词"""
        prompt = f"""你是一个俄罗斯方块游戏分析师。请分析以下游戏数据并生成反思。

游戏数据：
- 玩家ID: {game_summary.get('player_id', 0)}
- 得分: {game_summary.get('score', 0)}
- 消除行数: {game_summary.get('lines_cleared', 0)}
- 游戏结束: {game_summary.get('game_over', False)}
- 存活tick数: {game_summary.get('survived_ticks', 0)}

请从以下方面进行分析：
1. 游戏策略是否合理
2. 关键决策点是什么
3. 可以改进的地方
4. 学到的经验

请用中文生成一段100字左右的反思。"""
        
        return prompt
    
    async def _call_qwen_api(self, prompt: str, api_key: str) -> str:
        """调用 Qwen API 生成反思"""
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise Exception(f"API returned {response.status}")
                
                data = await response.json()
                return data['choices'][0]['message']['content']
    
    def _generate_default_reflection(self, game_summary: Dict[str, Any]) -> str:
        """生成默认反思（无 API 时使用）"""
        lines = game_summary.get('lines_cleared', 0)
        score = game_summary.get('score', 0)
        
        if game_summary.get('game_over', False):
            return f"游戏结束。最终得分 {score}，消除 {lines} 行。需要注意板面管理，避免过早满板。"
        else:
            return f"当前得分 {score}，已消除 {lines} 行。保持当前策略，继续观察对手行为。"