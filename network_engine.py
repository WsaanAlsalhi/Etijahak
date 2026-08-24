"""
network_engine.py
يقترح باحثين/موجّهين/متعاونين، بمخرجات ثنائية اللغة.
"""

import json
import os
from typing import Dict, List
from models import Connection

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "network.json")


def _load_network() -> list:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def suggest_connections(capability_scores: Dict[str, int], top_n: int = 4) -> List[Connection]:
    people = _load_network()
    results: List[Connection] = []

    user_strong_skills = {s for s, v in capability_scores.items() if v >= 40}

    for person in people:
        tags = set(person["tags"])
        overlap = tags & user_strong_skills
        if not overlap:
            continue
        match_score = int(round((len(overlap) / len(tags)) * 100))
        overlap_ar = "، ".join(s.replace("_", " ") for s in overlap)
        overlap_en = ", ".join(s.replace("_", " ").title() for s in overlap)

        reason_ar = f"مشاريعك/مهاراتك في ({overlap_ar}) تتقاطع مع مجال عمل هذا الشخص، مما يجعل التواصل معه منطقيًا ومبنيًا على سبب حقيقي."
        reason_en = f"Your skills/projects in ({overlap_en}) overlap with this person's field, making it a genuine reason to connect."

        results.append(Connection(
            id=person["id"], name_ar=person["name_ar"], name_en=person.get("name_en", person["name_ar"]),
            role_ar=person["role_ar"], role_en=person.get("role_en", person["role_ar"]),
            type=person["type"], icon=person["icon"],
            reason_ar=reason_ar, reason_en=reason_en,
            match_score=match_score,
        ))

    results.sort(key=lambda c: c.match_score, reverse=True)
    return results[:top_n]
