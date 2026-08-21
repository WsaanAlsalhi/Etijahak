from pydantic import BaseModel, Field
from typing import List, Optional


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
    current_score: int
    required_score: int


class BridgeStep(BaseModel):
    order: int
    title_ar: str
    description_ar: str
    related_gap: Optional[str] = None


class Connection(BaseModel):
    id: str
    name_ar: str
    role_ar: str
    type: str
    icon: str
    reason_ar: str
    match_score: int


class Opportunity(BaseModel):
    id: str
    name_ar: str
    type: str
    icon: str
    match_score: int
    reason_ar: str


class AnalyzeResponse(BaseModel):
    goal_name_ar: str
    overall_readiness: int
    capabilities: List[CapabilityScore]
    gaps: List[Gap]
    bridge: List[BridgeStep]
    connections: List[Connection]