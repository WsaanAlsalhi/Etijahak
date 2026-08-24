"""
oauth.py
منطق الربط الحقيقي مع GitHub (سحب المشاريع) وLinkedIn (تأكيد الهوية فقط).

آلية الربط:
- المستخدم أصلًا مسجّل دخوله بحسابه بموقعنا (Email/Password → JWT).
- يضغط "ربط GitHub" → نحوّله لصفحة GitHub → يوافق → GitHub يرجعه لنا مع "code".
- نستخدم الـcode لجلب "access token" خاص بـGitHub، ونستخدمه لجلب مستودعاته.
- نربط كل هذا بحساب المستخدم عندنا عن طريق تمرير الـJWT تبعه كـ"state" بالرحلة كاملة.
"""

import os
import requests
from datetime import datetime
from urllib.parse import urlencode

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "http://127.0.0.1:8000/auth/github/callback")

LINKEDIN_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI", "http://127.0.0.1:8000/auth/linkedin/callback")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5500")


# ==================== GitHub ====================

def github_authorize_url(state: str) -> str:
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "read:user public_repo",
        "state": state,
    }
    return "https://github.com/login/oauth/authorize?" + urlencode(params)


def github_exchange_code_for_token(code: str) -> str:
    resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(data.get("error_description", "فشل ربط GitHub"))
    return data["access_token"]


def github_fetch_user(access_token: str) -> dict:
    resp = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# لغات البرمجة الشائعة بـGitHub -> tags متوافقة مع محرك القدرات عندنا
LANGUAGE_TAG_MAP = {
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "javascript",
    "Jupyter Notebook": "python",
    "HTML": "software_engineering",
    "CSS": "software_engineering",
    "Java": "software_engineering",
    "C++": "software_engineering",
    "C": "software_engineering",
    "Go": "software_engineering",
    "Rust": "software_engineering",
}


def github_fetch_repos(access_token: str, max_repos: int = 20) -> list:
    """يجلب مستودعات المستخدم الحقيقية ويحوّلها لصيغة 'مشروع' متوافقة مع محرك التحليل."""
    resp = requests.get(
        "https://api.github.com/user/repos",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        params={"sort": "updated", "per_page": max_repos, "affiliation": "owner"},
        timeout=15,
    )
    resp.raise_for_status()
    repos = resp.json()

    projects = []
    for repo in repos:
        if repo.get("fork"):
            continue  # نتجاهل المستودعات المنسوخة (Forks)، نريد المشاريع الحقيقية للمستخدم فقط

        tags = set()
        lang = repo.get("language")
        if lang and lang in LANGUAGE_TAG_MAP:
            tags.add(LANGUAGE_TAG_MAP[lang])
        elif lang:
            tags.add(lang.lower().replace(" ", "_"))

        for topic in (repo.get("topics") or []):
            tags.add(topic.lower().replace("-", "_"))

        projects.append({
            "title": repo.get("name"),
            "description": repo.get("description") or "",
            "tags": list(tags),
            "has_repo": True,  # مستودع GitHub حقيقي = دليل قوي دائمًا
            "url": repo.get("html_url"),
            "stars": repo.get("stargazers_count", 0),
            "updated_at": repo.get("updated_at"),
        })

    return projects


# ==================== LinkedIn (Sign In - تأكيد هوية فقط، بدون بيانات خبرات) ====================

def linkedin_authorize_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": "openid profile email",
        "state": state,
    }
    return "https://www.linkedin.com/oauth/v2/authorization?" + urlencode(params)


def linkedin_exchange_code_for_token(code: str) -> str:
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINKEDIN_REDIRECT_URI,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(data.get("error_description", "فشل تسجيل الدخول عبر LinkedIn"))
    return data["access_token"]


def linkedin_fetch_userinfo(access_token: str) -> dict:
    """يجلب فقط: الاسم + الإيميل + الصورة (Sign In with LinkedIn using OpenID Connect)."""
    resp = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
