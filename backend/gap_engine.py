"""
gap_engine.py
يقارن قدرات المستخدم الحالية بمتطلبات الهدف، ويحدد نوعين من الفجوات
كما ورد في وثيقة اتجاهك:

  1) Capability & Evidence Gap  -> "لدي مهارة، لكن ليس لدي خبرة/دليل كافٍ لإثباتها"
  2) Network Gap                -> "لدي القدرة، لكن لا أعرف الأشخاص/الجهات الموصلة للفرص"
"""

from typing import Dict, List
from models import Gap

EVIDENCE_LABELS = {
    "research_experience": "خبرة بحثية (Research Experience)",
    "technical_writing": "الكتابة التقنية (Technical Writing)",
    "research_evidence": "دليل بحثي (Research Evidence)",
    "deployed_project": "مشروع منشور فعليًا (Deployed Project)",
    "portfolio": "معرض أعمال (Portfolio)",
    "github_projects": "مشاريع على GitHub",
}

NETWORK_LABELS = {
    "academic_network": "شبكة أكاديمية (Academic Network)",
    "industry_network": "شبكة صناعية / مهنية (Industry Network)",
    "mentor_network": "شبكة موجّهين (Mentor Network)",
}

GAP_THRESHOLD = 15  # الحد المسموح دون اعتبارها فجوة فعلية


def analyze_gaps(capability_scores: Dict[str, int], goal: dict) -> List[Gap]:
    gaps: List[Gap] = []

    # فجوات القدرات (Skill Gaps) -> Capability & Evidence Gap
    for skill, weight in goal.get("required_skills", {}).items():
        required_score = int(weight * 100)
        current = capability_scores.get(skill, 0)
        if current + GAP_THRESHOLD < required_score:
            gaps.append(Gap(
                skill=skill,
                gap_type="capability_evidence",
                label_ar=skill.replace("_", " ").title(),
                current_score=current,
                required_score=required_score,
            ))

    # فجوات الأدلة الإضافية المطلوبة (خبرة بحثية، كتابة تقنية...)
    for ev_key in goal.get("required_evidence", []):
        current = capability_scores.get(ev_key, 0)
        if current < 50:
            gaps.append(Gap(
                skill=ev_key,
                gap_type="capability_evidence",
                label_ar=EVIDENCE_LABELS.get(ev_key, ev_key),
                current_score=current,
                required_score=70,
            ))

    # فجوات الشبكة (Network Gap)
    for net_key in goal.get("required_network", []):
        gaps.append(Gap(
            skill=net_key,
            gap_type="network",
            label_ar=NETWORK_LABELS.get(net_key, net_key),
            current_score=0,
            required_score=100,
        ))

    return gaps
