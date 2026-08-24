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


# ============================================================
# نظام ترحيل بسيط وآمن (Lightweight Migrations)
# ============================================================
# المشكلة: Base.metadata.create_all() ينشئ الجداول الناقصة فقط، ولا يضيف
# أعمدة جديدة لجدول موجود مسبقًا بقاعدة بيانات حقيقية بالإنتاج. فأي عمود
# أضفناه لاحقًا لجدول قديم (مثل github_username) يبقى غائبًا فعليًا من
# قاعدة البيانات المنشورة رغم وجوده بتعريف SQLAlchemy بالكود.
#
# الحل: قبل create_all، نتحقق يدويًا من كل عمود متوقع، ونضيفه بأمان
# لو كان ناقصًا فعليًا (تعمل بأمان مع SQLite و PostgreSQL معًا).
# ============================================================

_EXPECTED_COLUMNS = [
    # (اسم الجدول، اسم العمود، نوع SQL للإضافة)
    ("users", "github_username", "VARCHAR"),
    ("users", "github_access_token", "VARCHAR"),
    ("users", "github_connected_at", "TIMESTAMP"),
    ("users", "linkedin_verified", "BOOLEAN"),
    ("users", "linkedin_name", "VARCHAR"),
    ("users", "linkedin_connected_at", "TIMESTAMP"),
    ("users", "username", "VARCHAR"),
    ("profile_data", "github_projects", "TEXT"),
    ("profile_data", "last_capabilities", "TEXT"),
]


def run_lightweight_migrations():
    from sqlalchemy import inspect, text as sql_text

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, column, col_type in _EXPECTED_COLUMNS:
            if table not in existing_tables:
                continue  # الجدول نفسه غير موجود بعد؛ create_all سينشئه بكل أعمدته لاحقًا

            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            if column in existing_columns:
                continue

            try:
                conn.execute(sql_text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                print(f"🔧 [MIGRATION] تمت إضافة العمود الناقص: {table}.{column}")
            except Exception as e:
                print(f"⚠️ [MIGRATION] تعذّرت إضافة {table}.{column}: {e}")
