"""
goal_ai.py
يستخدم نموذج Claude (Anthropic API) لتوليد متطلبات أي هدف يكتبه المستخدم
بحريّة (مو من قائمة ثابتة)، بنفس صيغة data/goals.json بالضبط.

⚠️ يحتاج متغيّر بيئة ANTHROPIC_API_KEY. إذا غير موجود، الميزة تُعطَّل بأمان
(الموقع يستمر بالعمل بالقائمة الثابتة بدون أي كسر).
"""

import os
import json
import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

SYSTEM_PROMPT = """أنتِ محرك تحليل يحدد متطلبات وظيفة أو هدف مهني معيّن يكتبه مستخدم بحريّة.
أعطي فقط كائن JSON صالح بدون أي نص أو شرح إضافي، بالضبط بهذا الشكل:

{
  "name_ar": "اسم الهدف بالعربية بصياغة واضحة ومختصرة",
  "name_en": "نفس اسم الهدف بالإنجليزية بصياغة واضحة ومختصرة",
  "required_skills": {"skill_key_english_snake_case": 0.0-1.0, ...},
  "required_evidence": ["research_experience" أو "deployed_project" أو "portfolio" أو "certifications" أو "technical_writing" أو "research_evidence" أو "github_projects" (اختاري 1-3 الأنسب)],
  "required_network": ["academic_network" أو "industry_network" أو "mentor_network" (اختاري 1-2 الأنسب)]
}

قواعد صارمة:
- required_skills: 4-7 مهارات، المفاتيح بالإنجليزية snake_case فقط (مثل: python, data_analysis, ui_ux)، والقيم بين 0 و1 تمثل الأهمية.
- لا تكتبي أي نص خارج كائن JSON. لا Markdown، لا علامات كود، لا شرح.
"""


def is_enabled() -> bool:
    return bool(ANTHROPIC_API_KEY)


def generate_goal_requirements(goal_text: str) -> dict:
    if not is_enabled():
        raise RuntimeError("ميزة تحليل الأهداف المخصصة بالذكاء الاصطناعي غير مفعّلة حاليًا")

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 800,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": f"الهدف: {goal_text}"}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    cleaned = text.strip()

    # تنظيف احتياطي لو رجع النص ملفوف بعلامات كود ماركداون رغم التعليمات
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    parsed = json.loads(cleaned)

    # تحقق أساسي من الشكل المتوقع قبل الاستخدام
    required_keys = {"name_ar", "required_skills", "required_evidence", "required_network"}
    if not required_keys.issubset(parsed.keys()):
        raise ValueError("الرد من النموذج غير مكتمل الشكل المتوقع")
    if not isinstance(parsed["required_skills"], dict) or not parsed["required_skills"]:
        raise ValueError("لا توجد مهارات محددة بالرد")

    return parsed
