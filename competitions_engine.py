"""
competitions_engine.py
يجلب مسابقات/هاكاثونات حقيقية ومباشرة (من Devpost، عبر مصدر عام مجاني بدون مفتاح)،
ويطابقها مع قدرات المستخدم.

المصدر: https://webdevharsha.github.io/open-hackathons-api/data.json
(يسحب بيانات Devpost الحقيقية ويحدّثها بشكل دوري، بدون مصادقة، عام ومجاني).
"""

import re
import time
import html
import requests

LIVE_DATA_URL = "https://webdevharsha.github.io/open-hackathons-api/data.json"

# كاش بسيط بالذاكرة لتفادي إغراق المصدر الخارجي بطلبات متكررة
_cache = {"data": None, "fetched_at": 0}
CACHE_TTL_SECONDS = 20 * 60  # 20 دقيقة

# تحويل مواضيع Devpost إلى وسوم متوافقة مع محرك القدرات عندنا
THEME_TAG_MAP = {
    "Machine Learning/AI": "ai",
    "Cybersecurity": "cybersecurity",
    "Web": "software_engineering",
    "Mobile": "mobile_development",
    "Health": "healthcare",
    "Fintech": "financial_analysis",
    "Design": "ui_ux",
    "Gaming": "software_engineering",
    "DevOps": "cloud_computing",
    "Blockchain": "software_engineering",
    "Databases": "sql",
    "IoT": "hardware",
    "Enterprise": "business_strategy",
    "Social Good": "communication",
    "Education": "teaching",
    "Productivity": "product_thinking",
    "Low/No Code": "software_engineering",
    "Open Ended": "problem_solving",
    "Robotic Process Automation": "machine_learning",
    "Beginner Friendly": None,  # لا يمثل مهارة فعلية، نتجاهله
}


def _strip_price_html(price_text: str) -> str:
    """يحوّل '$<span data-currency-value>50,000</span>' إلى '$50,000'."""
    if not price_text:
        return "0"
    cleaned = re.sub(r"<[^>]+>", "", price_text)
    return html.unescape(cleaned).strip()


def _fetch_live_data() -> list:
    now = time.time()
    if _cache["data"] is not None and (now - _cache["fetched_at"]) < CACHE_TTL_SECONDS:
        return _cache["data"]

    resp = requests.get(LIVE_DATA_URL, timeout=15, headers={"User-Agent": "EtijahakBot/1.0"})
    resp.raise_for_status()
    data = resp.json()
    hackathons = data.get("hackathons", [])

    _cache["data"] = hackathons
    _cache["fetched_at"] = now
    return hackathons


def _normalize_hackathon(raw: dict) -> dict:
    tags = set()
    for theme in raw.get("themes", []):
        mapped = THEME_TAG_MAP.get(theme.get("name"))
        if mapped:
            tags.add(mapped)

    return {
        "id": str(raw.get("id")),
        "title": raw.get("title", "").strip(),
        "organizer": raw.get("organization_name", ""),
        "url": raw.get("url"),
        "location": raw.get("displayed_location", "Online"),
        "dates": raw.get("submission_period_dates", ""),
        "time_left": raw.get("time_left_to_submission", ""),
        "prize": _strip_price_html(raw.get("prizeText", "")),
        "registrations_count": raw.get("registrations_count", 0),
        "themes": [t.get("name") for t in raw.get("themes", [])],
        "tags": list(tags),
        "featured": raw.get("featured", False),
    }


def get_live_hackathons(capability_scores: dict = None, limit: int = 30) -> list:
    """
    يرجّع قائمة هاكاثونات حقيقية ومفتوحة حاليًا، مرتبة حسب مدى تطابقها
    مع قدرات المستخدم (لو تم تمريرها)، أو حسب عدد المسجّلين إذا لا.
    """
    raw_list = _fetch_live_data()
    normalized = [_normalize_hackathon(h) for h in raw_list if h.get("isOpen") == "open"]

    if capability_scores:
        user_strong_skills = {s for s, v in capability_scores.items() if v >= 25}
        for h in normalized:
            overlap = set(h["tags"]) & user_strong_skills
            h["match_score"] = int(round((len(overlap) / len(h["tags"])) * 100)) if h["tags"] else 0
            h["matched_tags"] = list(overlap)
        normalized.sort(key=lambda h: (h["match_score"], h["registrations_count"]), reverse=True)
    else:
        for h in normalized:
            h["match_score"] = 0
            h["matched_tags"] = []
        normalized.sort(key=lambda h: h["registrations_count"], reverse=True)

    return normalized[:limit]
