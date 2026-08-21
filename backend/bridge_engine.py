"""
bridge_engine.py
يبني "الجسر المفقود": خطوات عملية ومرتّبة تنقل المستخدم من
Capability -> Evidence -> Experience -> Connection -> Opportunity
"""

from typing import List
from models import Gap, BridgeStep

STEP_TEMPLATES = {
    "capability_evidence": [
        ("ابنِ مشروعًا عمليًا في {label}", "أنشئ مشروعًا حقيقيًا (مع مستودع GitHub) يثبت مهارتك في {label} بدلًا من الادّعاء بها فقط."),
        ("وثّق تجربتك في تقرير تقني", "اكتب تقريرًا تقنيًا مختصرًا (Technical Report) يشرح المشكلة، الحل، والنتائج."),
    ],
    "research_experience": [
        ("ابدأ تحديًا بحثيًا صغيرًا", "شارك في Research Challenge أو مسابقة بحثية قصيرة لبناء أول خبرة بحثية موثّقة."),
    ],
    "technical_writing": [
        ("اكتب تقريرًا بحثيًا مختصرًا", "حوّل أحد مشاريعك إلى تقرير مكتوب بأسلوب علمي."),
    ],
    "network": [
        ("تواصل مع باحث/خبير مناسب", "تواصل مع أحد الأشخاص المقترحين في قسم Connections - لديك سبب حقيقي للتواصل."),
        ("ابنِ تعاونًا بسيطًا", "حوّل التواصل الأولي إلى تعاون صغير لبناء شبكة حقيقية."),
    ],
}

FINAL_STEP = ("تقدّم للفرصة المستهدفة", "بعد إغلاق الفجوات الأساسية، قدّم رسميًا على الفرصة/التدريب المستهدف مع ملف الأدلة.")


def build_bridge(gaps: List[Gap]) -> List[BridgeStep]:
    steps: List[BridgeStep] = []
    order = 1

    evidence_gaps = [g for g in gaps if g.gap_type == "capability_evidence"]
    network_gaps = [g for g in gaps if g.gap_type == "network"]

    for g in evidence_gaps[:3]:
        templates = STEP_TEMPLATES.get(g.skill, None)
        if templates is None:
            templates = STEP_TEMPLATES["capability_evidence"]
            label = g.label_ar
            for title, desc in templates:
                steps.append(BridgeStep(
                    order=order,
                    title_ar=title.format(label=label),
                    description_ar=desc.format(label=label),
                    related_gap=g.skill,
                ))
                order += 1
        else:
            for title, desc in templates:
                steps.append(BridgeStep(order=order, title_ar=title, description_ar=desc, related_gap=g.skill))
                order += 1

    for g in network_gaps[:2]:
        for title, desc in STEP_TEMPLATES["network"]:
            steps.append(BridgeStep(order=order, title_ar=title, description_ar=desc, related_gap=g.skill))
            order += 1

    steps.append(BridgeStep(order=order, title_ar=FINAL_STEP[0], description_ar=FINAL_STEP[1], related_gap=None))
    return steps