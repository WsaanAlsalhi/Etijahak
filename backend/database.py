"""
database.py
إعداد الاتصال بقاعدة البيانات.

- محليًا (تطوير): يستخدم SQLite تلقائيًا (ملف etijahak.db) — صفر إعداد.
- في الإنتاج (Railway/Render): يقرأ DATABASE_URL من متغيرات البيئة تلقائيًا
  ويتصل بـ PostgreSQL الحقيقي.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./etijahak.db")

# Railway/Render أحيانًا تعطي رابط يبدأ بـ postgres:// بدل postgresql://
# و SQLAlchemy الحديث يحتاج postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
