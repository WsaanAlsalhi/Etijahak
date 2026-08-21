"""
main.py — اتجاهك (Etijahak) Backend
منصة تبني جسرًا بين قدرات المستخدم الحالية والفرص التي يريد الوصول إليها.

التشغيل:
    uvicorn main:app --reload
"""

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import AnalyzeRequest, AnalyzeResponse, CapabilityScore
from ai_engine import analyze_capabilities, capability_dict
from gap_engine import analyze_gaps
from bridge_engine import build_bridge
from opportunity_engine import match_opportunities
from network_engine import suggest_connections

app = FastAPI(title="اتجاهك - Etijahak API", version="1.0.0")

# CORS: يسمح للـ Frontend (يعمل على منفذ مختلف مثل Live Server) بالاتصال بالـ API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOALS_PATH = os.path.join(os.path.dirname(__file__), "data", "goals.json")
with open(GOALS_PATH, "r", encoding="utf-8") as f:
    GOALS = json.load(f)

# حالة بسيطة في الذاكرة لآخر تحليل (كافٍ لمرحلة الهاكاثون/العرض التجريبي)
LAST_STATE = {"capability_scores": {}, "goal_key": None}


@app.get("/")
def root():
    return {"status": "ok", "message": "اتجاهك API يعمل بنجاح 🚀"}


@app.get("/goals")
def get_goals():
    """قائمة الأهداف المتاحة لعرضها في نموذج اختيار الهدف بالواجهة."""
    return [{"key": k, "name_ar": v["name_ar"]} for k, v in GOALS.items()]


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    goal = GOALS.get(payload.goal_key)
    if goal is None:
        raise HTTPException(status_code=404, detail="الهدف غير موجود")

    capabilities = analyze_capabilities(payload.profile)
    scores = capability_dict(capabilities)

    gaps = analyze_gaps(scores, goal)
    bridge = build_bridge(gaps)
    connections = suggest_connections(scores)

    # نسبة الجاهزية العامة تجاه الهدف = متوسط (1 - نسبة الفجوة) على المهارات المطلوبة
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

    # نحفظ آخر حالة لاستخدامها لاحقًا في GET /opportunities
    LAST_STATE["capability_scores"] = scores
    LAST_STATE["goal_key"] = payload.goal_key

    return AnalyzeResponse(
        goal_name_ar=goal["name_ar"],
        overall_readiness=overall_readiness,
        capabilities=capabilities,
        gaps=gaps,
        bridge=bridge,
        connections=connections,
    )


@app.get("/opportunities")
def get_opportunities():
    """
    يطابق الفرص بناءً على آخر تحليل تم إجراؤه عبر /analyze.
    (استدعِ /analyze أولًا، ثم استدعِ هذا المسار)
    """
    scores = LAST_STATE.get("capability_scores") or {}
    if not scores:
        raise HTTPException(status_code=400, detail="لم يتم تحليل أي ملف مستخدم بعد. استدعِ /analyze أولًا.")
    return match_opportunities(scores)