"""
db_models.py
جداول قاعدة البيانات الفعلية (SQLAlchemy ORM).
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    major = Column(String, default="")
    username = Column(String, unique=False, nullable=True, index=True)  # للبروفايل العام (مثال: /u/ahmed123)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ---- ربط GitHub ----
    github_username = Column(String, nullable=True)
    github_access_token = Column(String, nullable=True)  # يُستخدم لسحب المستودعات لاحقًا
    github_connected_at = Column(DateTime, nullable=True)

    # ---- ربط LinkedIn (تأكيد هوية فقط) ----
    linkedin_verified = Column(Boolean, default=False)
    linkedin_name = Column(String, nullable=True)
    linkedin_connected_at = Column(DateTime, nullable=True)

    profile = relationship("ProfileData", back_populates="user", uselist=False)


class CustomGoal(Base):
    """أهداف مخصصة ولّدها الذكاء الاصطناعي بناءً على نص حر كتبه المستخدم."""
    __tablename__ = "custom_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_text = Column(String, nullable=False)
    definition = Column(JSON, nullable=False)  # نفس شكل عنصر بـ goals.json
    created_at = Column(DateTime, default=datetime.utcnow)


class CompetitionStatus(Base):
    """
    حالة مشاركة المستخدم بمسابقة/هاكاثون معيّن (يعلّمها المستخدم يدويًا،
    لأن Devpost لا يوفر وصولًا خارجيًا لبيانات تسجيل المستخدم الفعلية).
    status: 'registered' | 'participated' | 'organizer'
    """
    __tablename__ = "competition_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_id = Column(String, nullable=False)   # معرّف الهاكاثون الخارجي (من Devpost)
    competition_title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    """رسالة مباشرة بين مستخدمين."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProfileData(Base):
    __tablename__ = "profile_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    skills = Column(JSON, default=list)
    projects = Column(JSON, default=list)          # مشاريع أدخلها المستخدم يدويًا
    github_projects = Column(JSON, default=list)    # مشاريع مسحوبة تلقائيًا من GitHub
    experiences = Column(JSON, default=list)
    certificates = Column(JSON, default=list)

    last_goal_key = Column(String, nullable=True)
    last_capability_scores = Column(JSON, default=dict)
    last_capabilities = Column(JSON, default=list)  # القدرات الكاملة (مع الأدلة) لاسترجاعها لاحقًا بدون إعادة التحليل

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
