"""
main.py — اتجاهك (Etijahak) Backend — نسخة الإنتاج (مع تسجيل دخول وقاعدة بيانات)

التشغيل محليًا:
    uvicorn main:app --reload
"""

import json
import os
import re
from datetime import timedelta, datetime

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import engine, get_db, Base, run_lightweight_migrations, SessionLocal
from db_models import User, ProfileData, CustomGoal, CompetitionStatus, Message
from auth import hash_password, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, decode_token_for_user_id
import oauth
import goal_ai
import competitions_engine

from models import (
    SignupRequest, LoginRequest, TokenResponse, UserOut,
    AnalyzeRequest, AnalyzeResponse, UserProfile, CapabilityScore,
)
from ai_engine import analyze_capabilities, capability_dict
from gap_engine import analyze_gaps
from bridge_engine import build_bridge
from opportunity_engine import match_opportunities
from network_engine import suggest_connections

# ينشئ الجداول في قاعدة البيانات إذا لم تكن موجودة (لا يمسح بيانات موجودة)
# نصلح أي أعمدة ناقصة من إصدارات سابقة قبل إنشاء الجداول الجديدة
run_lightweight_migrations()
Base.metadata.create_all(bind=engine)


def slugify_username(name: str, fallback_source: str = "") -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "", name.strip().lower())[:20]
    if not base and fallback_source:
        # الاسم عربي بالكامل (بدون أحرف لاتينية) — نستخدم بداية الإيميل كبديل مفيد بدل "user" العام
        base = re.sub(r"[^a-zA-Z0-9]+", "", fallback_source.split("@")[0].strip().lower())[:20]
    return base or "user"


def generate_unique_username(db: Session, base_name: str, fallback_source: str = "") -> str:
    base = slugify_username(base_name, fallback_source)
    candidate = base
    counter = 1
    while db.query(User).filter(User.username == candidate).first():
        counter += 1
        candidate = f"{base}{counter}"
    return candidate


def _backfill_missing_usernames():
    """يولّد username لأي مستخدم قديم أُنشئ قبل إضافة هذي الميزة."""
    db = SessionLocal()
    try:
        users_without_username = db.query(User).filter(
            (User.username.is_(None)) | (User.username == "")
        ).all()
        for u in users_without_username:
            u.username = generate_unique_username(db, u.name, u.email)
        if users_without_username:
            db.commit()
            print(f"🔧 [MIGRATION] تم توليد username لعدد {len(users_without_username)} مستخدم قديم")
    finally:
        db.close()


_backfill_missing_usernames()

app = FastAPI(title="اتجاهك - Etijahak API", version="2.0.0")

# CORS — عدّلي allow_origins في الإنتاج لتحديد نطاق الفرونت إند فقط بدل "*"
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_ORIGINS == "*" else FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOALS_PATH = os.path.join(os.path.dirname(__file__), "data", "goals.json")
with open(GOALS_PATH, "r", encoding="utf-8") as f:
    GOALS = json.load(f)


@app.get("/")
def root():
    return {"status": "ok", "message": "اتجاهك API يعمل بنجاح 🚀"}


# ==================== Auth ====================

@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="هذا البريد الإلكتروني مسجّل مسبقًا")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        major=payload.major,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user.username = generate_unique_username(db, user.name, user.email)
    db.commit()

    # ننشئ سجل ملف شخصي فارغ لهذا المستخدم
    profile = ProfileData(user_id=user.id, skills=[], projects=[], experiences=[], certificates=[])
    db.add(profile)
    db.commit()

    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token, user_name=user.name, user_email=user.email, username=user.username)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")

    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token, user_name=user.name, user_email=user.email, username=user.username)


@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id, name=current_user.name, email=current_user.email,
        major=current_user.major, username=current_user.username,
    )


# ==================== Goals ====================

@app.get("/goals")
def get_goals():
    return [{"key": k, "name_ar": v["name_ar"], "name_en": v.get("name_en", v["name_ar"])} for k, v in GOALS.items()]


@app.get("/goals/ai-status")
def goals_ai_status():
    """يخبر الفرونت إند هل ميزة 'اكتبي هدفك الخاص بالذكاء الاصطناعي' مفعّلة حاليًا."""
    return {"enabled": goal_ai.is_enabled()}


@app.post("/goals/generate")
def generate_custom_goal(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """يولّد متطلبات هدف حر كتبه المستخدم عبر Claude، ويحفظه كهدف مخصص له."""
    goal_text = (payload.get("goal_text") or "").strip()
    if not goal_text:
        raise HTTPException(status_code=400, detail="الرجاء كتابة نص الهدف")

    if not goal_ai.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="ميزة تحليل الأهداف المخصصة بالذكاء الاصطناعي غير مفعّلة حاليًا. اختاري هدفًا من القائمة الجاهزة.",
        )

    try:
        definition = goal_ai.generate_goal_requirements(goal_text)
    except Exception:
        raise HTTPException(status_code=502, detail="تعذّر تحليل هذا الهدف حاليًا، جربي صياغة أوضح أو اختاري من القائمة")

    custom = CustomGoal(user_id=current_user.id, goal_text=goal_text, definition=definition)
    db.add(custom)
    db.commit()
    db.refresh(custom)

    return {
        "key": f"custom:{custom.id}",
        "name_ar": definition["name_ar"],
        "name_en": definition.get("name_en", definition["name_ar"]),
        "definition": definition,
    }


@app.get("/goals/mine")
def my_custom_goals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """قائمة الأهداف المخصصة اللي ولّدها هذا المستخدم سابقًا، لعرضها بالقائمة المنسدلة."""
    rows = db.query(CustomGoal).filter(CustomGoal.user_id == current_user.id).order_by(CustomGoal.created_at.desc()).all()
    return [{"key": f"custom:{r.id}", "name_ar": r.definition.get("name_ar", r.goal_text), "name_en": r.definition.get("name_en", r.definition.get("name_ar", r.goal_text))} for r in rows]


# ==================== Profile (لجلب آخر بيانات محفوظة عند تسجيل الدخول) ====================

@app.get("/profile")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    if not profile:
        return {"skills": [], "projects": [], "experiences": [], "certificates": [], "github_projects": []}
    return {
        "skills": profile.skills or [],
        "projects": profile.projects or [],
        "experiences": profile.experiences or [],
        "certificates": profile.certificates or [],
        "github_projects": profile.github_projects or [],
        "last_goal_key": profile.last_goal_key,
    }


# ==================== Analyze (محمي بتسجيل الدخول، ويحفظ في قاعدة البيانات) ====================

def _resolve_goal(db: Session, current_user: User, goal_key: str) -> dict:
    if goal_key.startswith("custom:"):
        try:
            custom_id = int(goal_key.split(":", 1)[1])
        except (IndexError, ValueError):
            raise HTTPException(status_code=404, detail="الهدف غير موجود")
        custom_row = db.query(CustomGoal).filter(
            CustomGoal.id == custom_id, CustomGoal.user_id == current_user.id
        ).first()
        if not custom_row:
            raise HTTPException(status_code=404, detail="الهدف المخصص غير موجود")
        return custom_row.definition

    goal = GOALS.get(goal_key)
    if goal is None:
        raise HTTPException(status_code=404, detail="الهدف غير موجود")
    return goal


def _compute_readiness(goal: dict, scores: dict) -> int:
    required_skills = goal.get("required_skills", {})
    if not required_skills:
        return 0
    readiness_values = []
    for skill, weight in required_skills.items():
        required_score = weight * 100
        current = scores.get(skill, 0)
        readiness_values.append(min(current / required_score, 1.0) if required_score else 1.0)
    return int(round((sum(readiness_values) / len(readiness_values)) * 100))


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = _resolve_goal(db, current_user, payload.goal_key)

    # ندمج مشاريع GitHub المسحوبة تلقائيًا (لو موجودة) مع المشاريع المُدخلة يدويًا
    profile_row = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    github_projects = (profile_row.github_projects if profile_row else None) or []

    from models import ProjectInput
    merged_profile = payload.profile.copy(deep=True)
    existing_titles = {p.title for p in merged_profile.projects}
    for gh in github_projects:
        if gh["title"] not in existing_titles:
            merged_profile.projects.append(ProjectInput(
                title=gh["title"],
                description=gh.get("description", ""),
                tags=gh.get("tags", []),
                has_repo=True,
            ))

    capabilities = analyze_capabilities(merged_profile)
    scores = capability_dict(capabilities)

    gaps = analyze_gaps(scores, goal)
    bridge = build_bridge(gaps)
    connections = suggest_connections(scores)
    overall_readiness = _compute_readiness(goal, scores)

    # حفظ دائم في قاعدة البيانات (بدل ذاكرة مؤقتة) — مرتبط بالمستخدم المسجّل دخوله
    if not profile_row:
        profile_row = ProfileData(user_id=current_user.id)
        db.add(profile_row)

    profile_row.skills = [s.dict() for s in payload.profile.skills]
    profile_row.projects = [p.dict() for p in payload.profile.projects]
    profile_row.experiences = [e.dict() for e in payload.profile.experiences]
    profile_row.certificates = [c.dict() for c in payload.profile.certificates]
    profile_row.last_goal_key = payload.goal_key
    profile_row.last_capability_scores = scores
    profile_row.last_capabilities = [c.dict() for c in capabilities]
    db.commit()

    return AnalyzeResponse(
        goal_name_ar=goal["name_ar"],
        goal_name_en=goal.get("name_en", goal["name_ar"]),
        overall_readiness=overall_readiness,
        capabilities=capabilities,
        gaps=gaps,
        bridge=bridge,
        connections=connections,
    )


@app.get("/analyze/last", response_model=AnalyzeResponse)
def get_last_analysis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    يرجّع آخر تحليل محفوظ للمستخدم (يُعاد حسابه من القدرات المخزّنة)
    بدون الحاجة لإعادة تعبئة النموذج من جديد. مفيد لصفحات منفصلة
    (المهارات، الجسر، الفرص...) تُفتح مباشرة بعد تسجيل الدخول.
    """
    profile_row = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    if not profile_row or not profile_row.last_goal_key or not profile_row.last_capability_scores:
        raise HTTPException(status_code=404, detail="لا يوجد تحليل سابق بعد. ابدئي تحليلًا جديدًا أولًا.")

    goal = _resolve_goal(db, current_user, profile_row.last_goal_key)
    scores = profile_row.last_capability_scores

    capabilities = [CapabilityScore(**c) for c in (profile_row.last_capabilities or [])]
    if not capabilities:
        # توافق مع بيانات قديمة أُنشئت قبل إضافة last_capabilities
        capabilities = [CapabilityScore(skill=k, score=v, evidence=[]) for k, v in scores.items()]
        capabilities.sort(key=lambda c: c.score, reverse=True)

    gaps = analyze_gaps(scores, goal)
    bridge = build_bridge(gaps)
    connections = suggest_connections(scores)
    overall_readiness = _compute_readiness(goal, scores)

    return AnalyzeResponse(
        goal_name_ar=goal["name_ar"],
        goal_name_en=goal.get("name_en", goal["name_ar"]),
        overall_readiness=overall_readiness,
        capabilities=capabilities,
        gaps=gaps,
        bridge=bridge,
        connections=connections,
    )


# ==================== البحث عن مستخدمين + الرسائل المباشرة ====================

@app.get("/users/search")
def search_users(q: str = "", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """يبحث عن مستخدمين بالاسم أو الـusername للتواصل معهم (يستثني نفس المستخدم)."""
    q = q.strip()
    if len(q) < 2:
        return []
    like_pattern = f"%{q}%"
    results = db.query(User).filter(
        User.id != current_user.id,
        (User.name.ilike(like_pattern)) | (User.username.ilike(like_pattern)),
    ).limit(10).all()
    return [{"username": u.username, "name": u.name, "major": u.major} for u in results]


@app.get("/messages/conversations")
def list_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """قائمة كل المحادثات الحالية مع آخر رسالة وعدد غير المقروء لكل واحدة."""
    all_msgs = db.query(Message).filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.created_at.desc()).all()

    conversations = {}
    for m in all_msgs:
        other_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in conversations:
            conversations[other_id] = {"last_message": m.content, "last_at": m.created_at, "unread": 0}
        if m.receiver_id == current_user.id and not m.is_read:
            conversations[other_id]["unread"] += 1

    result = []
    for other_id, info in conversations.items():
        other_user = db.query(User).filter(User.id == other_id).first()
        if not other_user:
            continue
        result.append({
            "username": other_user.username,
            "name": other_user.name,
            "last_message": info["last_message"],
            "last_at": info["last_at"].isoformat() if info["last_at"] else None,
            "unread": info["unread"],
        })

    result.sort(key=lambda c: c["last_at"] or "", reverse=True)
    return result


@app.get("/messages/with/{username}")
def get_conversation_thread(username: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """يرجّع كل الرسائل المتبادلة مع مستخدم معيّن، ويعلّم الرسائل الواردة كمقروءة."""
    other_user = db.query(User).filter(User.username == username).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    msgs = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    # نعلّم الرسائل الواردة كمقروءة تلقائيًا عند فتح المحادثة
    unread_incoming = [m for m in msgs if m.receiver_id == current_user.id and not m.is_read]
    for m in unread_incoming:
        m.is_read = True
    if unread_incoming:
        db.commit()

    return {
        "other_user": {"username": other_user.username, "name": other_user.name},
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "from_me": m.sender_id == current_user.id,
                "created_at": m.created_at.isoformat(),
            }
            for m in msgs
        ],
    }


@app.post("/messages/send")
def send_message(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    to_username = (payload.get("to_username") or "").strip()
    content = (payload.get("content") or "").strip()

    if not to_username or not content:
        raise HTTPException(status_code=400, detail="بيانات الرسالة ناقصة")
    if len(content) > 2000:
        raise HTTPException(status_code=400, detail="الرسالة طويلة جدًا")

    receiver = db.query(User).filter(User.username == to_username).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="المستخدم المستقبل غير موجود")
    if receiver.id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكنك مراسلة نفسك")

    msg = Message(sender_id=current_user.id, receiver_id=receiver.id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {"id": msg.id, "content": msg.content, "from_me": True, "created_at": msg.created_at.isoformat()}


@app.get("/messages/unread-count")
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """عدد كل الرسائل غير المقروءة (لعرض شارة تنبيه بالواجهة)."""
    count = db.query(Message).filter(Message.receiver_id == current_user.id, Message.is_read == False).count()
    return {"unread_count": count}


# ==================== البروفايل العام (بدون تسجيل دخول) ====================

@app.get("/u/{username}")
def public_profile(username: str, db: Session = Depends(get_db)):
    """
    صفحة بروفايل عامة يقدر أي شخص يشوفها بدون تسجيل دخول — تعرض
    مهارات وقدرات ومشاريع المستخدم (بما فيها مشاريع GitHub المتزامنة).
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="لا يوجد مستخدم بهذا الرابط")

    profile = db.query(ProfileData).filter(ProfileData.user_id == user.id).first()

    capabilities = []
    if profile and profile.last_capability_scores:
        capabilities = sorted(
            [{"skill": k, "score": v} for k, v in profile.last_capability_scores.items()],
            key=lambda c: c["score"], reverse=True,
        )

    manual_projects = (profile.projects if profile else []) or []
    github_projects = (profile.github_projects if profile else []) or []
    all_projects = manual_projects + github_projects

    return {
        "name": user.name,
        "username": user.username,
        "major": user.major,
        "member_since": user.created_at.strftime("%Y-%m-%d") if user.created_at else None,
        "capabilities": capabilities,
        "projects": all_projects,
        "github_username": user.github_username,
        "linkedin_verified": user.linkedin_verified,
    }


# ==================== GitHub Integration ====================

@app.get("/auth/github/connect")
def github_connect(current_user: User = Depends(get_current_user)):
    """يرجّع رابط توجيه لـGitHub. الفرونت إند يوجّه المتصفح لهذا الرابط مباشرة."""
    token = create_access_token({"sub": str(current_user.id)}, timedelta(minutes=10))
    return {"authorize_url": oauth.github_authorize_url(state=token)}


@app.get("/auth/github/callback")
def github_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        user_id = decode_token_for_user_id(state)
    except ValueError:
        return RedirectResponse(f"{oauth.FRONTEND_URL}/?github_error=session_expired")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(f"{oauth.FRONTEND_URL}/?github_error=user_not_found")

    try:
        access_token = oauth.github_exchange_code_for_token(code)
        gh_user = oauth.github_fetch_user(access_token)
    except Exception:
        return RedirectResponse(f"{oauth.FRONTEND_URL}/?github_error=connection_failed")

    user.github_username = gh_user.get("login")
    user.github_access_token = access_token
    user.github_connected_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(f"{oauth.FRONTEND_URL}/?github_connected=1")


@app.post("/github/sync")
def github_sync(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """يسحب مستودعات GitHub الحقيقية للمستخدم ويحفظها كمشاريع بملفه."""
    if not current_user.github_access_token:
        raise HTTPException(status_code=400, detail="لم تربطي حساب GitHub بعد")

    try:
        repos = oauth.github_fetch_repos(current_user.github_access_token)
    except Exception:
        raise HTTPException(status_code=502, detail="تعذّر جلب مستودعات GitHub، حاولي ربط الحساب من جديد")

    profile_row = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    if not profile_row:
        profile_row = ProfileData(user_id=current_user.id)
        db.add(profile_row)

    profile_row.github_projects = repos
    db.commit()

    return {"github_username": current_user.github_username, "projects": repos, "count": len(repos)}


@app.get("/github/status")
def github_status(current_user: User = Depends(get_current_user)):
    return {
        "connected": bool(current_user.github_username),
        "github_username": current_user.github_username,
    }


# ==================== LinkedIn (تسجيل دخول/تأكيد هوية فقط) ====================

@app.get("/auth/linkedin/connect")
def linkedin_connect(current_user: User = Depends(get_current_user)):
    token = create_access_token({"sub": str(current_user.id)}, timedelta(minutes=10))
    return {"authorize_url": oauth.linkedin_authorize_url(state=token)}


@app.get("/auth/linkedin/callback")
def linkedin_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        user_id = decode_token_for_user_id(state)
    except ValueError:
        return RedirectResponse(f"{oauth.FRONTEND_URL}/?linkedin_error=session_expired")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(f"{oauth.FRONTEND_URL}/?linkedin_error=user_not_found")

    try:
        access_token = oauth.linkedin_exchange_code_for_token(code)
        info = oauth.linkedin_fetch_userinfo(access_token)
    except Exception:
        return RedirectResponse(f"{oauth.FRONTEND_URL}/?linkedin_error=connection_failed")

    user.linkedin_verified = True
    user.linkedin_name = info.get("name")
    user.linkedin_connected_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(f"{oauth.FRONTEND_URL}/?linkedin_connected=1")


@app.get("/linkedin/status")
def linkedin_status(current_user: User = Depends(get_current_user)):
    return {
        "verified": current_user.linkedin_verified,
        "linkedin_name": current_user.linkedin_name,
    }


# ==================== Competitions / Hackathons (بيانات حقيقية من Devpost) ====================

@app.get("/competitions")
def get_competitions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    يرجّع مسابقات/هاكاثونات حقيقية ومفتوحة حاليًا (من مصدر Devpost العام)،
    مرتبة حسب مدى تطابقها مع قدرات المستخدم إن وجدت، مع حالة مشاركته
    المسجّلة يدويًا (إن وجدت) لكل مسابقة.
    """
    profile_row = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    scores = (profile_row.last_capability_scores if profile_row else None) or {}

    try:
        hackathons = competitions_engine.get_live_hackathons(capability_scores=scores)
    except Exception:
        raise HTTPException(status_code=502, detail="تعذّر جلب المسابقات حاليًا، حاولي لاحقًا")

    my_statuses = {
        s.competition_id: s.status
        for s in db.query(CompetitionStatus).filter(CompetitionStatus.user_id == current_user.id).all()
    }
    for h in hackathons:
        h["my_status"] = my_statuses.get(h["id"])

    return hackathons


@app.post("/competitions/status")
def set_competition_status(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    تعليم حالة مشاركة المستخدم بمسابقة معيّنة (مسجّل / شارك سابقًا / مشرف)،
    يُحفظ فورًا ويظهر مباشرة بالواجهة بدون إعادة تحميل الصفحة.
    """
    competition_id = str(payload.get("competition_id", "")).strip()
    competition_title = (payload.get("competition_title") or "").strip()
    status_value = payload.get("status")

    if not competition_id or not competition_title:
        raise HTTPException(status_code=400, detail="بيانات المسابقة ناقصة")
    if status_value not in ("registered", "participated", "organizer", None):
        raise HTTPException(status_code=400, detail="حالة غير صالحة")

    row = db.query(CompetitionStatus).filter(
        CompetitionStatus.user_id == current_user.id,
        CompetitionStatus.competition_id == competition_id,
    ).first()

    if status_value is None:
        # إزالة الحالة (المستخدم ضغط "إلغاء التعليم")
        if row:
            db.delete(row)
            db.commit()
        return {"competition_id": competition_id, "status": None}

    if row:
        row.status = status_value
        row.competition_title = competition_title
    else:
        row = CompetitionStatus(
            user_id=current_user.id,
            competition_id=competition_id,
            competition_title=competition_title,
            status=status_value,
        )
        db.add(row)
    db.commit()

    return {"competition_id": competition_id, "status": status_value}


@app.get("/competitions/mine")
def my_competitions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """قائمة كل المسابقات اللي علّم عليها المستخدم حالة (لعرضها بصفحة 'مسابقاتي')."""
    rows = db.query(CompetitionStatus).filter(CompetitionStatus.user_id == current_user.id).all()
    return [{"competition_id": r.competition_id, "competition_title": r.competition_title, "status": r.status} for r in rows]


# ==================== Opportunities (محمي، يعتمد على آخر تحليل محفوظ للمستخدم) ====================

@app.get("/opportunities")
def get_opportunities(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile_row = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    scores = (profile_row.last_capability_scores if profile_row else None) or {}
    if not scores:
        raise HTTPException(status_code=400, detail="لم يتم تحليل أي ملف مستخدم بعد. استدعِ /analyze أولًا.")
    return match_opportunities(scores)
