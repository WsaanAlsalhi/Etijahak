"""
bridge_engine.py
يبني "الجسر المفقود" (Missing Bridge): خطوات عملية ومرتّبة، بمخرجات
ثنائية اللغة (عربي/إنجليزي).
"""

from typing import List
from models import Gap, BridgeStep

STEP_TEMPLATES = {
    "capability_evidence": [
        {
            "title_ar": "ابنِ مشروعًا عمليًا في {label_ar}",
            "title_en": "Build a hands-on project in {label_en}",
            "desc_ar": "أنشئ مشروعًا حقيقيًا (مع مستودع GitHub) يثبت مهارتك في {label_ar} بدلًا من الادّعاء بها فقط.",
            "desc_en": "Create a real project (with a GitHub repo) that proves your {label_en} skill instead of just claiming it.",
        },
        {
            "title_ar": "وثّق تجربتك في تقرير تقني",
            "title_en": "Document your work in a technical report",
            "desc_ar": "اكتب تقريرًا تقنيًا مختصرًا يشرح المشكلة، الحل، والنتائج - هذا يتحول لاحقًا إلى Evidence رسمي.",
            "desc_en": "Write a short technical report explaining the problem, solution, and results - this becomes formal evidence later.",
        },
    ],
    "research_experience": [
        {
            "title_ar": "ابدأ تحديًا بحثيًا صغيرًا",
            "title_en": "Start a small research challenge",
            "desc_ar": "شارك في Research Challenge أو مسابقة بحثية قصيرة لبناء أول خبرة بحثية موثّقة.",
            "desc_en": "Join a research challenge or short competition to build your first documented research experience.",
        },
    ],
    "technical_writing": [
        {
            "title_ar": "اكتب تقريرًا بحثيًا مختصرًا",
            "title_en": "Write a short research report",
            "desc_ar": "حوّل أحد مشاريعك إلى تقرير مكتوب بأسلوب علمي، هذا يبني دليل الكتابة التقنية المطلوب.",
            "desc_en": "Turn one of your projects into a scientifically written report - this builds the required technical writing evidence.",
        },
    ],
    "network": [
        {
            "title_ar": "تواصل مع باحث/خبير مناسب",
            "title_en": "Connect with a relevant researcher/expert",
            "desc_ar": "تواصل مع أحد الأشخاص المقترحين في قسم Connections - لديك سبب حقيقي للتواصل بناءً على مشاريعك.",
            "desc_en": "Reach out to one of the suggested people in the Connections section - you have a real reason to connect based on your projects.",
        },
        {
            "title_ar": "ابنِ تعاونًا بسيطًا",
            "title_en": "Build a small collaboration",
            "desc_ar": "حوّل التواصل الأولي إلى تعاون صغير (مراجعة، ورشة، أو مشاركة في بحث) لبناء شبكة حقيقية.",
            "desc_en": "Turn the initial contact into a small collaboration (a review, a workshop, or joining research) to build a real network.",
        },
    ],
}

FINAL_STEP = {
    "title_ar": "تقدّم للفرصة المستهدفة",
    "title_en": "Apply to the target opportunity",
    "desc_ar": "بعد إغلاق الفجوات الأساسية، قدّم رسميًا على الفرصة/التدريب المستهدف مع ملف الأدلة (Capability Passport).",
    "desc_en": "Once the core gaps are closed, formally apply to the target opportunity/internship with your evidence file (Capability Passport).",
}


def build_bridge(gaps: List[Gap]) -> List[BridgeStep]:
    steps: List[BridgeStep] = []
    order = 1

    evidence_gaps = [g for g in gaps if g.gap_type == "capability_evidence"]
    network_gaps = [g for g in gaps if g.gap_type == "network"]

    for g in evidence_gaps[:3]:
        templates = STEP_TEMPLATES.get(g.skill, STEP_TEMPLATES["capability_evidence"])
        for t in templates:
            steps.append(BridgeStep(
                order=order,
                title_ar=t["title_ar"].format(label_ar=g.label_ar, label_en=g.label_en),
                title_en=t["title_en"].format(label_ar=g.label_ar, label_en=g.label_en),
                description_ar=t["desc_ar"].format(label_ar=g.label_ar, label_en=g.label_en),
                description_en=t["desc_en"].format(label_ar=g.label_ar, label_en=g.label_en),
                related_gap=g.skill,
            ))
            order += 1

    for g in network_gaps[:2]:
        for t in STEP_TEMPLATES["network"]:
            steps.append(BridgeStep(
                order=order,
                title_ar=t["title_ar"], title_en=t["title_en"],
                description_ar=t["desc_ar"], description_en=t["desc_en"],
                related_gap=g.skill,
            ))
            order += 1

    steps.append(BridgeStep(
        order=order,
        title_ar=FINAL_STEP["title_ar"], title_en=FINAL_STEP["title_en"],
        description_ar=FINAL_STEP["desc_ar"], description_en=FINAL_STEP["desc_en"],
        related_gap=None,
    ))
    return steps
