# اتجاهك — From Potential to Opportunity 🌉

نسخة **إنتاج حقيقية** تشمل: تسجيل دخول (Email + Password)، قاعدة بيانات حقيقية،
حفظ دائم لكل مستخدم، وجاهزة للنشر على الإنترنت.

## ما الجديد في هذه النسخة

- ✅ **تسجيل حساب / تسجيل دخول** حقيقي (كلمات المرور مشفّرة بـ bcrypt، جلسات JWT)
- ✅ **قاعدة بيانات حقيقية** (PostgreSQL بالإنتاج / SQLite تلقائيًا محليًا) بدل ملفات JSON المؤقتة
- ✅ كل مستخدم له بياناته الخاصة (لا يشوف بيانات غيره)
- ✅ الملف الشخصي يُحفظ تلقائيًا ويُسترجع عند تسجيل الدخول من جديد
- ✅ جاهز للنشر على Railway (Backend) + Vercel (Frontend)

## البنية

```
etijahak/
├── backend/
│   ├── main.py               ← FastAPI + Auth + كل الـ endpoints
│   ├── database.py            ← اتصال قاعدة البيانات (SQLite محليًا / PostgreSQL بالإنتاج)
│   ├── db_models.py           ← جداول SQLAlchemy (User, ProfileData)
│   ├── auth.py                 ← تشفير كلمات المرور + JWT
│   ├── models.py               ← Pydantic schemas
│   ├── ai_engine.py / gap_engine.py / bridge_engine.py
│   ├── opportunity_engine.py / network_engine.py
│   ├── Procfile                ← لتشغيل الخادم عند النشر
│   ├── .env.example
│   ├── requirements.txt
│   └── data/goals.json, opportunities.json, network.json
│
└── frontend/
    ├── index.html   ← Landing / Signup / Login / Onboarding / Dashboard
    ├── style.css
    ├── config.js    ← عنوان الـ Backend (تغيّرينه بعد النشر)
    └── app.js
```

---

## 1) التشغيل محليًا (قبل النشر، للتجربة)

```cmd
cd etijahak\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

يعمل تلقائيًا بقاعدة بيانات SQLite محلية (ملف `etijahak.db` يُنشأ تلقائيًا) — صفر إعداد إضافي.

افتحي `frontend/index.html` بـ Live Server. `config.js` مضبوط افتراضيًا على `http://127.0.0.1:8000`.

---

## 2) النشر الفعلي على الإنترنت

### التوصية: **Railway** للـ Backend + قاعدة البيانات، و **Vercel** للـ Frontend

**ليش هذا الخيار؟**
- Railway يعطيك PostgreSQL حقيقي بضغطة واحدة، ويشتغل ممتاز مع FastAPI.
- Vercel مجاني وسريع لاستضافة الملفات الثابتة (HTML/CSS/JS)، ودومين مجاني فورًا.
- كلاهما يدعمان **نطاق مخصص لاحقًا** (Custom Domain) بسهولة إذا حبيتِ تشترين دومين مثل etijahak.com.
- يتحمّلان عدد كبير من المستخدمين مع خطط ترقية بسيطة إذا كبر الاستخدام.

### الخطوة أ) رفع الكود على GitHub

```cmd
cd etijahak
git init
git add .
git commit -m "اتجاهك - نسخة أولى"
```
أنشئي مستودع جديد على GitHub وارفعي الكود له (`git remote add origin ...` ثم `git push`).

### الخطوة ب) نشر الـ Backend على Railway

1. روحي railway.app وسجّلي بحساب GitHub.
2. **New Project → Deploy from GitHub repo** → اختاري المستودع.
3. من إعدادات المشروع، حددي **Root Directory = backend** (لأن الـbackend داخل مجلد فرعي).
4. **New → Database → Add PostgreSQL** — Railway بيربطها تلقائيًا ويولّد متغيّر `DATABASE_URL` بنفسه.
5. من تبويب **Variables** أضيفي:
   - `JWT_SECRET` = أي نص عشوائي طويل وسري
   - `FRONTEND_ORIGINS` = رابط الفرونت إند بعد نشره على Vercel (خطوة قادمة) — مؤقتًا خليها `*`
6. Railway بيقرأ `Procfile` تلقائيًا ويشغّل السيرفر. انتظري حتى يصير الـDeploy أخضر ✅
7. من تبويب **Settings → Networking**، فعّلي **Generate Domain** — بتحصلين رابط مثل:
   `https://etijahak-backend-production.up.railway.app`

✅ جربي الرابط + `/docs` بالمتصفح — لازم يطلع توثيق FastAPI.

### الخطوة ج) نشر الـ Frontend على Vercel

1. روحي vercel.com وسجّلي بحساب GitHub.
2. **Add New → Project** → اختاري نفس المستودع.
3. في إعدادات الاستيراد، حددي **Root Directory = frontend**.
4. Framework Preset اختاري **Other** (لأنه HTML/CSS/JS عادي بدون build).
5. اضغطي **Deploy**. بتحصلين رابط مثل:
   `https://etijahak.vercel.app`

### الخطوة د) اربطي الفرونت بالباك

افتحي `frontend/config.js` وعدّلي السطر:
```js
window.ETIJAHAK_API_BASE = "https://etijahak-backend-production.up.railway.app";
```
احفظي، اعملي `git push` — Vercel بينشر النسخة الجديدة تلقائيًا خلال ثوانٍ.

ثم ارجعي لـ Railway وحدّثي متغيّر `FRONTEND_ORIGINS` بنفس رابط Vercel النهائي (بدل `*`) لتقييد CORS بأمان أكبر.

---

## 3) بعد النشر — تأكدي إن كل شيء يشتغل

1. افتحي رابط Vercel من متصفح (أو جوالك).
2. أنشئي حساب جديد (Email + Password).
3. عبّي مهاراتك ومشاريعك واختاري هدف.
4. لازم تطلع لك الـDashboard الكاملة.
5. سجّلي خروج وادخلي مرة ثانية — لازم بياناتك تكون محفوظة زي ما هي.

---

## نقاط أمان مهمة قبل الإطلاق الفعلي لعدد كبير

- ✅ **غيّري `JWT_SECRET`** لقيمة عشوائية قوية (لا تستخدمي القيمة الافتراضية بالكود أبدًا).
- ✅ **حدّدي `FRONTEND_ORIGINS`** برابط موقعك فقط بدل `*` بعد التأكد من عمل كل شي.
- ✅ فعّلي **HTTPS** (Railway و Vercel يفعّلانه تلقائيًا بدون أي إعداد إضافي منك).
- 🔜 لاحقًا: أضيفي Rate Limiting على `/auth/login` لمنع محاولات تخمين كلمات المرور المتكررة.
- 🔜 لاحقًا: فعّلي نسخ احتياطي دوري (Backups) لقاعدة بيانات Railway من لوحة التحكم.

---

## تخصيص الأهداف والفرص

البيانات (الأهداف، الفرص، الشبكة) في `backend/data/*.json` — عدّليها وارفعيها (git push)
بدون الحاجة لتعديل أي كود بايثون؛ Railway بينشرها تلقائيًا.

## تطوير مستقبلي (متوافق مع خارطة الطريق الأصلية)

- **GitHub Integration:** جلب المشاريع تلقائيًا من حساب GitHub الحقيقي للمستخدم.
- **LLM حقيقي:** استبدال منطق `ai_engine.py` القائم على القواعد بنموذج Embeddings لتحليل أدق.
- **OAuth (Google/GitHub):** إضافة تسجيل دخول اجتماعي بجانب Email/Password الحالي.
