from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional


# ==================== Auth Schemas ====================

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    major: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    user_email: str
    username: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    major: str
    username: Optional[str] = None


# ==================== Profile / Analysis Schemas ====================

class SkillInput(BaseModel):
    name: str
    level: int = Field(3, ge=1, le=5, description="تقييم ذاتي من 1 إلى 5")


class ProjectInput(BaseModel):
    title: str
    description: str = ""
    tags: List[str] = []  # e.g. ["python", "computer_vision"]
    has_repo: bool = False   # مرتبط بمستودع GitHub أو رابط فعلي = دليل أقوى


class ExperienceInput(BaseModel):
    title: str
    description: str = ""
    tags: List[str] = []


class CertificateInput(BaseModel):
    title: str
    tags: List[str] = []


class UserProfile(BaseModel):
    name: str
    major: str = ""
    skills: List[SkillInput] = []
    projects: List[ProjectInput] = []
    experiences: List[ExperienceInput] = []
    certificates: List[CertificateInput] = []


class AnalyzeRequest(BaseModel):
    profile: UserProfile
    goal_key: str


class CapabilityScore(BaseModel):
    skill: str
    score: int
    evidence: List[str]


class Gap(BaseModel):
    skill: str
    gap_type: str          # "capability_evidence" | "network"
    label_ar: str
    label_en: str
    current_score: int
    required_score: int


class BridgeStep(BaseModel):
    order: int
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    related_gap: Optional[str] = None


class Connection(BaseModel):
    id: str
    name_ar: str
    name_en: str
    role_ar: str
    role_en: str
    type: str
    icon: str
    reason_ar: str
    reason_en: str
    match_score: int


class Opportunity(BaseModel):
    id: str
    name_ar: str
    name_en: str
    type: str
    icon: str
    match_score: int
    reason_ar: str
    reason_en: str


class AnalyzeResponse(BaseModel):
    goal_name_ar: str
    goal_name_en: str
    overall_readiness: int
    capabilities: List[CapabilityScore]
    gaps: List[Gap]
    bridge: List[BridgeStep]
    connections: List[Connection]
