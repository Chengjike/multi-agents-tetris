"""
游戏经验知识库

记录游戏过程中的关键发现和策略，供Agent参考
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Experience:
    """单条经验"""
    id: str
    category: str  # 'bug_fix', 'strategy', 'optimization'
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class GameExperience:
    """游戏经验知识库"""

    def __init__(self):
        self.experiences: List[Experience] = []
        self._init_founded_experiences()

    def _init_founded_experiences(self) -> None:
        """初始化已发现的经验"""
        founded = [
            Experience(
                id="exp_001",
                category="bug_fix",
                title="AI评估位置时未先落到底部",
                description="AI在评估最佳落点时，没有先让方块落到底部就检查碰撞，导致评估的位置不正确，无法有效消除行。修复方法：在检查碰撞前先调用get_piece_at_bottom()让方块落到底部。",
                impact="high",
                tags=["AI", "评估", "碰撞检测", "落点"]
            ),
            Experience(
                id="exp_002",
                category="bug_fix",
                title="AI只在落地后计算最佳位置",
                description="旧逻辑只在方块落地后才找最佳位置，此时方块已经无法移动，错过了优化机会。修复方法：每tick都计算最佳落点，边下落边移动/旋转到最优位置。",
                impact="high",
                tags=["AI", "决策", "实时优化"]
            ),
            Experience(
                id="exp_003",
                category="bug_fix",
                title="惩罚系统使用累计值而非增量",
                description="代码把lines_cleared_total（累计值）当成当次消除数传递，导致伊万消1行被记录为1，第二次变2，第三次变3，第四次变4就触发惩罚。修复方法：添加prev_lines_cleared_total追踪上次值，计算增量。",
                impact="high",
                tags=["惩罚系统", "计分", "bug"]
            ),
            Experience(
                id="exp_004",
                category="optimization",
                title="动态速度提升游戏紧张感",
                description="分数越高速度越快（200ms->50ms），增加游戏紧张感和对抗性。",
                impact="medium",
                tags=["速度", "动态难度"]
            ),
            Experience(
                id="exp_005",
                category="strategy",
                title="AI权重优化",
                description="消除行权重从10提高到100，优先选择能快速消除的落点。",
                impact="medium",
                tags=["AI", "策略", "权重"]
            ),
        ]
        self.experiences.extend(founded)

    def add_experience(
        self,
        category: str,
        title: str,
        description: str,
        impact: str = "medium",
        tags: Optional[List[str]] = None
    ) -> Experience:
        """添加新经验"""
        exp_id = f"exp_{len(self.experiences) + 1:03d}"
        experience = Experience(
            id=exp_id,
            category=category,
            title=title,
            description=description,
            impact=impact,
            tags=tags or []
        )
        self.experiences.append(experience)
        return experience

    def get_experience(self, exp_id: str) -> Optional[Experience]:
        """获取单条经验"""
        for exp in self.experiences:
            if exp.id == exp_id:
                return exp
        return None

    def get_all_experiences(self) -> List[Experience]:
        """获取所有经验"""
        return self.experiences

    def get_by_category(self, category: str) -> List[Experience]:
        """按类别获取经验"""
        return [exp for exp in self.experiences if exp.category == category]

    def get_by_impact(self, impact: str) -> List[Experience]:
        """按影响程度获取经验"""
        return [exp for exp in self.experiences if exp.impact == impact]

    def search(self, keyword: str) -> List[Experience]:
        """搜索经验"""
        keyword = keyword.lower()
        return [
            exp for exp in self.experiences
            if keyword in exp.title.lower() or
               keyword in exp.description.lower() or
               any(keyword in tag.lower() for tag in exp.tags)
        ]

    def get_ai_guidance(self) -> Dict[str, Any]:
        """获取AI指导建议"""
        high_impact = self.get_by_impact("high")
        
        guidance = {
            "summary": f"共{len(self.experiences)}条经验，其中{len(high_impact)}条高优先级",
            "critical_fixes": [
                {
                    "title": exp.title,
                    "action": exp.description.split("修复方法：")[1] if "修复方法：" in exp.description else "N/A"
                }
                for exp in high_impact if exp.category == "bug_fix"
            ],
            "strategy_tips": [
                exp.title
                for exp in self.experiences if exp.category == "strategy"
            ]
        }
        return guidance

    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典"""
        return [
            {
                "id": exp.id,
                "category": exp.category,
                "title": exp.title,
                "description": exp.description,
                "impact": exp.impact,
                "tags": exp.tags,
                "created_at": exp.created_at
            }
            for exp in self.experiences
        ]

    def save_to_file(self, filepath: str) -> None:
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str) -> None:
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.experiences = [
                Experience(
                    id=d['id'],
                    category=d['category'],
                    title=d['title'],
                    description=d['description'],
                    impact=d['impact'],
                    tags=d.get('tags', []),
                    created_at=d.get('created_at', datetime.now().isoformat())
                )
                for d in data
            ]


# 全局实例
game_experience = GameExperience()