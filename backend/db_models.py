"""
db_models.py
جداول قاعدة البيانات الفعلية (SQLAlchemy ORM).

نستخدم أعمدة JSON للمهارات/المشاريع/الشهادات (بدل جداول منفصلة لكل واحدة)
لتبسيط النموذج في هذه المرحلة، مع إمكانية تطويره لجداول علائقية كاملة لاحقًا
دون كسر أي API خارجي (Phase موضحة في README).
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
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
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("ProfileData", back_populates="user", uselist=False)


class ProfileData(Base):
    """آخر ملف/تحليل محفوظ للمستخدم - يُستخدم كذاكرة دائمة بدل الحالة المؤقتة بالسيرفر."""
    __tablename__ = "profile_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    skills = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    experiences = Column(JSON, default=list)
    certificates = Column(JSON, default=list)

    last_goal_key = Column(String, nullable=True)
    last_capability_scores = Column(JSON, default=dict)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
