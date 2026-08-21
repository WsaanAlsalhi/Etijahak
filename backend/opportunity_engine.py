"""
opportunity_engine.py
يطابق قدرات المستخدم مع الفرص المتاحة (تدريب، مسابقات، برامج، منح)
ويحسب نسبة Match% مع تفسير مختصر لسبب المطابقة.
"""

import json
import os
from typing import Dict, List
from models import Opportunity

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "opportunities.json")


def _load_opportunities() -> list:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def match_opportunities(capability_scores: Dict[str, int], top_n: int = 5) -> List[Opportunity]:
    opportunities = _load_opportunities()
    results: List[Opportunity] = []

    for op in opportunities:
        required = op["required_skills"]
        total_weight = sum(required.values()) or 1
        achieved = 0.0
        matched_skills = []

        for skill, weight in required.items():
            user_score = capability_scores.get(skill, 0) / 100.0
            achieved += min(user_score, 1.0) * weight
            if user_score >= weight * 0.7:
                matched_skills.append(skill)

        match_pct = int(round((achieved / total_weight) * 100))
        match_pct = max(0, min(100, match_pct))

        if matched_skills:
            reason = "تطابق قوي في: " + "، ".join(s.replace("_", " ") for s in matched_skills[:3])
        else:
            reason = "يحتاج بناء المهارات الأساسية المطلوبة لهذه الفرصة"

        results.append(Opportunity(
            id=op["id"],
            name_ar=op["name_ar"],
            type=op["type"],
            icon=op["icon"],
            match_score=match_pct,
            reason_ar=reason,
        ))

    results.sort(key=lambda o: o.match_score, reverse=True)
    return results[:top_n]
