"""Transparent keyword classification; an article can belong to several sections."""
import re

TOPICS = ('safety', 'deep-learning', 'rl', 'foundation-models')
TOPIC_LIMIT = 30
TOPIC_LABELS = {'safety': 'Safety', 'deep-learning': 'Deep Learning',
                'rl': 'RL', 'foundation-models': '基座模型研究'}
PATTERNS = {
    'safety': r'\bsafety\b|\bunsafe\b|\bsecurity\b|\bcyber|\balignment\b|\bmisalign|\bharmless|prompt.injection|\bjailbreak|red.team|\bcontainment\b|\bsandbox\b|runtime.control|\bmonitoring\b|安全|对齐|越狱|提示注入',
    'deep-learning': r'deep.learning|neural.network|\btransformers?\b|\bdiffusion\b|\bbackpropagation\b|representation.learning|self.supervised|contrastive.learning|深度学习|神经网络|扩散模型|表征学习',
    'rl': r'reinforcement.learning|\bRL\b|\bRLHF\b|\bRLAIF\b|\bGRPO\b|\bPPO\b|policy.gradient|actor.critic|\bQ.learning\b|reward.model|强化学习|奖励模型',
    'foundation-models': r'foundation.models?|base.models?|large.language.models?|\bLLMs?\b|\bVLMs?\b|vision.language.models?|\bpre.?train(?:ing|ed)?\b|\bpost.?train(?:ing|ed)?\b|scaling.laws?|基座模型|基础模型|大语言模型|预训练|后训练',
}


def classify(text, source=''):
    ai_context = source == 'METR' or bool(re.search(
        r'\bAI\b|artificial.intelligence|\bLLMs?\b|language.models?|\bagents?\b|\bagentic\b|'
        r'\balignment\b|machine.learning|deep.learning|neural|reinforcement.learning|'
        r'foundation.models?|\bVLMs?\b|模型|智能体|人工智能|学习', text, re.I))
    result = [topic for topic, pattern in PATTERNS.items()
              if re.search(pattern, text, re.I) and (topic != 'safety' or ai_context)]
    if source == 'METR' and 'safety' not in result:
        result.insert(0, 'safety')
    return result


def migrate_topics(data):
    # Earlier issues were collected exclusively for Safety; keep that membership.
    for issue in data['issues']:
        for article in issue['articles']:
            if 'topics' not in article:
                inferred = classify(' '.join([article['title'], article['summary'], *article['tags']]), article['source'])
                article['topics'] = list(dict.fromkeys(['safety', *inferred]))
    return data
