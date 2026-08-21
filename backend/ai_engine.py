"""
ai_engine.py
يحلل ملف المستخدم (المهارات + المشاريع + الخبرات + الشهادات)
ويحوّلها إلى درجات قدرة (Capability Scores) مدعومة بأدلة (Evidence).

هذا محرك قواعد بسيط (Rule-based) يمكن استبداله لاحقًا بنموذج LLM/Embeddings
حسب خطة التطوير (Phase 2 في وثيقة اتجاهك) دون تغيير الواجهة الخارجية للدالة.
"""

from typing import List, Dict
from models import UserProfile, CapabilityScore


def _normalize(tag: str) -> str:
    return tag.strip().lower().replace(" ", "_")


def analyze_capabilities(profile: UserProfile) -> List[CapabilityScore]:
    scores: Dict[str, int] = {}
    evidence: Dict[str, List[str]] = {}

    # 1) نقطة انطلاق: التقييم الذاتي للمهارة (1-5) -> يمثل حتى 55% من الدرجة
    for s in profile.skills:
        key = _normalize(s.name)
        base = min(s.level, 5) * 11  # 5 * 11 = 55
        scores[key] = scores.get(key, 0) + base
        evidence.setdefault(key, [])

    # 2) أدلة من المشاريع: كل مشروع يذكر المهارة يضيف نقاط، ومشروع له رابط/مستودع يضيف أكثر
    for p in profile.projects:
        for tag in p.tags:
            key = _normalize(tag)
            bonus = 18 if p.has_repo else 10
            scores[key] = scores.get(key, 0) + bonus
            evidence.setdefault(key, []).append(f"مشروع: {p.title}")

    # 3) أدلة من الخبرات العملية (مسابقات، تدريب، عمل تطوعي...)
    for e in profile.experiences:
        for tag in e.tags:
            key = _normalize(tag)
            scores[key] = scores.get(key, 0) + 12
            evidence.setdefault(key, []).append(f"خبرة: {e.title}")

    # 4) أدلة من الشهادات
    for c in profile.certificates:
        for tag in c.tags:
            key = _normalize(tag)
            scores[key] = scores.get(key, 0) + 15
            evidence.setdefault(key, []).append(f"شهادة: {c.title}")

    result: List[CapabilityScore] = []
    for key, raw_score in scores.items():
        capped = max(0, min(100, raw_score))
        result.append(CapabilityScore(skill=key, score=capped, evidence=evidence.get(key, [])))

    result.sort(key=lambda c: c.score, reverse=True)
    return result


def capability_dict(capabilities: List[CapabilityScore]) -> Dict[str, int]:
    return {c.skill: c.score for c in capabilities}