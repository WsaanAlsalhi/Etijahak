"""
main.py — اتجاهك (Etijahak) Backend — نسخة الإنتاج (مع تسجيل دخول وقاعدة بيانات)

التشغيل محليًا:
    uvicorn main:app --reload
"""

import json
import os
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from db_models import User, ProfileData
from auth import hash_password, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

from models import (
    SignupRequest, LoginRequest, TokenResponse, UserOut,
    AnalyzeRequest, AnalyzeResponse, UserProfile,
)
from ai_engine import analyze_capabilities, capability_dict
from gap_engine import analyze_gaps
from bridge_engine import build_bridge
from opportunity_engine import match_opportunities
from network_engine import suggest_connections

# ينشئ الجداول في قاعدة البيانات إذا لم تكن موجودة (لا يمسح بيانات موجودة)
Base.metadata.create_all(bind=engine)

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

    # ننشئ سجل ملف شخصي فارغ لهذا المستخدم
    profile = ProfileData(user_id=user.id, skills=[], projects=[], experiences=[], certificates=[])
    db.add(profile)
    db.commit()

    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token, user_name=user.name, user_email=user.email)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")

    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token, user_name=user.name, user_email=user.email)


@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(id=current_user.id, name=current_user.name, email=current_user.email, major=current_user.major)


# ==================== Goals ====================

@app.get("/goals")
def get_goals():
    return [{"key": k, "name_ar": v["name_ar"]} for k, v in GOALS.items()]


# ==================== Profile (لجلب آخر بيانات محفوظة عند تسجيل الدخول) ====================

@app.get("/profile")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    if not profile:
        return {"skills": [], "projects": [], "experiences": [], "certificates": []}
    return {
        "skills": profile.skills or [],
        "projects": profile.projects or [],
        "experiences": profile.experiences or [],
        "certificates": profile.certificates or [],
        "last_goal_key": profile.last_goal_key,
    }


# ==================== Analyze (محمي بتسجيل الدخول، ويحفظ في قاعدة البيانات) ====================

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = GOALS.get(payload.goal_key)
    if goal is None:
        raise HTTPException(status_code=404, detail="الهدف غير موجود")

    capabilities = analyze_capabilities(payload.profile)
    scores = capability_dict(capabilities)

    gaps = analyze_gaps(scores, goal)
    bridge = build_bridge(gaps)
    connections = suggest_connections(scores)

    required_skills = goal.get("required_skills", {})
    if required_skills:
        readiness_values = []
        for skill, weight in required_skills.items():
            required_score = weight * 100
            current = scores.get(skill, 0)
            readiness_values.append(min(current / required_score, 1.0) if required_score else 1.0)
        overall_readiness = int(round((sum(readiness_values) / len(readiness_values)) * 100))
    else:
        overall_readiness = 0

    # حفظ دائم في قاعدة البيانات (بدل ذاكرة مؤقتة) — مرتبط بالمستخدم المسجّل دخوله
    profile_row = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    if not profile_row:
        profile_row = ProfileData(user_id=current_user.id)
        db.add(profile_row)

    profile_row.skills = [s.dict() for s in payload.profile.skills]
    profile_row.projects = [p.dict() for p in payload.profile.projects]
    profile_row.experiences = [e.dict() for e in payload.profile.experiences]
    profile_row.certificates = [c.dict() for c in payload.profile.certificates]
    profile_row.last_goal_key = payload.goal_key
    profile_row.last_capability_scores = scores
    db.commit()

    return AnalyzeResponse(
        goal_name_ar=goal["name_ar"],
        overall_readiness=overall_readiness,
        capabilities=capabilities,
        gaps=gaps,
        bridge=bridge,
        connections=connections,
    )


# ==================== Opportunities (محمي، يعتمد على آخر تحليل محفوظ للمستخدم) ====================

@app.get("/opportunities")
def get_opportunities(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile_row = db.query(ProfileData).filter(ProfileData.user_id == current_user.id).first()
    scores = (profile_row.last_capability_scores if profile_row else None) or {}
    if not scores:
        raise HTTPException(status_code=400, detail="لم يتم تحليل أي ملف مستخدم بعد. استدعِ /analyze أولًا.")
    return match_opportunities(scores)
