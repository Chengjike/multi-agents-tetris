"""
通信策略模块

生成和分析 Agent 之间的通信消息
"""
import random
from typing import Optional


# 提议模板
PROPOSE_TEMPLATES = [
    "让我们一起攻击玩家{target}！",
    "联手吧，我们一起对付玩家{target}？",
    "建议我们一起消除行，给玩家{target}增加障碍！",
    "玩家{target}分数太高了，我们联手压制他！",
    "一起行动怎么样？攻击玩家{target}！"
]

# 威胁模板
THREAT_TEMPLATES = [
    "如果你继续这样，我会攻击你！",
    "别太过分了，小心我对付你！",
    "再这样做，我就让你尝尝苦头！",
    "你已经惹怒我了，等着瞧！",
    "停止你的行为，否则我会反击！"
]

# 承诺模板
PROMISE_TEMPLATES = [
    "我保证不攻击你！",
    "我们和平相处吧！",
    "我不会对你怎么样，相信我！",
    "我承诺不发起攻击！",
    "让我们保持友好！"
]

# 信息模板
INFO_TEMPLATES = [
    "玩家{player}的分数是{score}！",
    "玩家{player}已经消除了{lines}行！",
    "注意，玩家{player}准备发起攻击！",
    "游戏进行到{ticks}个tick了！",
    "当前领先者是玩家{player}！"
]


def generate_propose_message(
    sender_id: int,
    target_id: int,
    templates: Optional[list] = None
) -> str:
    """
    生成提议消息
    
    Args:
        sender_id: 发送者 ID
        target_id: 目标玩家 ID
        templates: 自定义模板
        
    Returns:
        消息文本
    """
    if templates is None:
        templates = PROPOSE_TEMPLATES
    
    template = random.choice(templates)
    return template.format(target=target_id)


def generate_threat_message(
    sender_id: int,
    target_id: Optional[int] = None,
    templates: Optional[list] = None
) -> str:
    """
    生成威胁消息
    
    Args:
        sender_id: 发送者 ID
        target_id: 目标玩家 ID
        templates: 自定义模板
        
    Returns:
        消息文本
    """
    if templates is None:
        templates = THREAT_TEMPLATES
    
    template = random.choice(templates)
    return template


def generate_promise_message(templates: Optional[list] = None) -> str:
    """
    生成承诺消息
    
    Args:
        templates: 自定义模板
        
    Returns:
        消息文本
    """
    if templates is None:
        templates = PROMISE_TEMPLATES
    
    template = random.choice(templates)
    return template


def generate_info_message(
    info_type: str,
    **kwargs
) -> str:
    """
    生成信息消息
    
    Args:
        info_type: 信息类型
        **kwargs: 格式化参数
        
    Returns:
        消息文本
    """
    template = random.choice(INFO_TEMPLATES)
    return template.format(**kwargs)


def analyze_message_intent(message: str) -> dict:
    """
    分析消息意图
    
    Args:
        message: 消息文本
        
    Returns:
        意图分析结果
    """
    message_lower = message.lower()
    
    # 检测意图类型
    intent = {
        'type': 'unknown',
        'target': None,
        'aggression': 0,
        'cooperation': 0
    }
    
    # 提议意图
    propose_keywords = ['联手', '一起', '合作', '联盟', '攻击']
    for kw in propose_keywords[:3]:
        if kw in message_lower:
            intent['type'] = 'propose'
            intent['cooperation'] += 0.3
            break
    
    # 威胁意图
    threat_keywords = ['攻击', '对付', '让你', '等着', '惹怒', '反击']
    for kw in threat_keywords:
        if kw in message_lower:
            intent['type'] = 'threat'
            intent['aggression'] += 0.3
            if intent['type'] == 'unknown':
                intent['type'] = 'threat'
            break
    
    # 承诺意图
    promise_keywords = ['保证', '承诺', '不会', '相信', '和平']
    for kw in promise_keywords:
        if kw in message_lower:
            intent['type'] = 'promise'
            intent['cooperation'] += 0.3
            if intent['type'] == 'unknown':
                intent['type'] = 'promise'
            break
    
    # 信息意图
    info_keywords = ['注意', '已经', '当前', '分数', '消除']
    for kw in info_keywords:
        if kw in message_lower:
            if intent['type'] == 'unknown':
                intent['type'] = 'info'
            break
    
    # 提取目标玩家
    import re
    player_match = re.search(r'玩家(\d+)', message)
    if player_match:
        intent['target'] = int(player_match.group(1))
    
    return intent