"""
auth.py
تشفير كلمات المرور (bcrypt) وإصدار/التحقق من JWT للجلسات.

⚠️ مهم للإنتاج: غيّري قيمة SECRET_KEY عبر متغير بيئة حقيقي (JWT_SECRET)
ولا تتركيها بالقيمة الافتراضية عند النشر الفعلي.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from db_models import User

SECRET_KEY = os.environ.get("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION_1234567890")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # أسبوع

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token_for_user_id(token: str) -> int:
    """
    يفكّ تشفير JWT مباشرة (بدون الاعتماد على هيدر Authorization).
    يُستخدم في رحلات OAuth (GitHub/LinkedIn) حيث نمرر الـtoken كـ'state'
    داخل رابط إعادة التوجيه، لأن هذي الروابط لا تحمل هيدرز مخصصة.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("توكن غير صالح")
        return int(user_id)
    except JWTError:
        raise ValueError("انتهت الجلسة أو التوكن غير صالح، الرجاء تسجيل الدخول مجددًا")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="بيانات الدخول غير صالحة أو انتهت الجلسة، الرجاء تسجيل الدخول مجددًا",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
