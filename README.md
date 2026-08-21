# اتجاهك | Etijahak 🌉

### From Potential to Opportunity

**اتجاهك** is an AI-powered platform designed to help students and young people understand where they are now, identify what is missing between their current capabilities and their goals, and build a practical path toward real opportunities.

Instead of simply showing courses or job opportunities, Etijahak focuses on the **missing bridge** between a young person's potential and the opportunity they want.

---

## 🎯 The Problem

Many students and young people have skills, projects, and ambition, but still struggle to reach opportunities because of two major gaps:

| Gap                                  | Problem                                                                                                       |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| 🧠 **Capabilities & Experience Gap** | They may have skills but lack practical experience or strong evidence of their abilities.                     |
| 🤝 **Network Gap**                   | They may have the potential but lack connections to mentors, researchers, companies, or relevant communities. |

This creates a cycle:

```text
No Experience
      ↓
No Opportunity
      ↓
No Experience
```

And:

```text
No Network
      ↓
Limited Opportunities
      ↓
No Network Growth
```

---

# 💡 Our Solution

Etijahak uses AI to analyze a user's:

* Skills
* Projects
* Experience
* Interests
* Career or academic goals

Then it identifies:

```text
Current Capabilities
        ↓
Evidence
        ↓
Missing Skills / Experience
        ↓
Missing Connections
        ↓
Personalized Bridge
        ↓
Relevant Opportunities
```

The platform answers one important question:

> **"What exactly is missing between where I am and where I want to be?"**

---

# 🌉 The Missing Bridge

The core concept of Etijahak is the **Missing Bridge Engine**.

For example, a student wants:

> **AI Research Internship**

The system may identify:

```text
Current Capabilities
✓ Python
✓ Artificial Intelligence
✓ Computer Vision

Missing
⚠ Research Experience
⚠ Academic Network
```

Etijahak then creates a practical path:

```text
Build Research Project
        ↓
Create Technical Report
        ↓
Connect with Researcher
        ↓
Gain Research Experience
        ↓
Apply for AI Research Internship
```

Instead of telling users:

> "You need more experience."

Etijahak tells them:

> **"Here is the experience you need, how to build it, and what you should do next."**

---

# 🚀 Core Features

### 🧠 AI Capability Analysis

Analyzes the user's skills, projects, and experience to identify their current capabilities.

### ⚠️ Gap Analysis

Compares the user's current profile with the requirements of their target goal.

### 🌉 Missing Bridge

Generates practical steps to close the gap between the user's current position and their target.

### 🎯 Goal-Based Guidance

The recommendations are based on what the user actually wants to achieve.

### 🤝 Connection Recommendations

Future versions will identify relevant:

* Researchers
* Mentors
* Professionals
* Organizations
* Communities

### 🚀 Opportunity Matching

Matches users with relevant:

* Internships
* Hackathons
* Research opportunities
* Training programs
* Competitions
* Fellowships

---

# 🏗️ Current Architecture

```text
                    ETIJAHak
                       │
                       ▼
                 User Profile
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Skills       Projects     Experience
          │            │            │
          └────────────┼────────────┘
                       ▼
               AI Analysis Engine
                       │
                       ▼
                Capability Analysis
                       │
                       ▼
                  Gap Analysis
                       │
                       ▼
              🌉 Missing Bridge
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Connections          Opportunities
```

---

# 🛠️ Technology Stack

| Component            | Technology                                      |
| -------------------- | ----------------------------------------------- |
| Backend              | Python                                          |
| API                  | FastAPI                                         |
| Server               | Uvicorn                                         |
| Data Validation      | Pydantic                                        |
| AI Engine            | Python-based analysis + LLM integration planned |
| Database             | Planned                                         |
| Frontend             | In development                                  |
| GitHub Integration   | Planned                                         |
| LinkedIn Integration | Planned                                         |

---

# 📁 Project Structure

```text
etijahak/
│
├── backend/
│   │
│   ├── main.py
│   ├── models.py
│   ├── ai_engine.py
│   ├── gap_engine.py
│   ├── bridge_engine.py
│   ├── opportunity_engine.py
│   │
│   ├── data/
│   │   └── opportunities.json
│   │
│   └── venv/
│
├── frontend/
│
└── README.md
```

---

# ⚙️ Current Backend

The current MVP provides three main API endpoints:

| Endpoint             | Purpose                                         |
| -------------------- | ----------------------------------------------- |
| `GET /`              | Check whether the API is running                |
| `POST /analyze`      | Analyze a user's capabilities, gaps, and bridge |
| `GET /opportunities` | Retrieve available opportunities                |

Interactive API documentation is available through FastAPI Swagger.

```text
http://127.0.0.1:8000/docs
```

---

# ▶️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/etijahak.git
cd etijahak
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate it on Windows

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install fastapi uvicorn pydantic
```

### 5. Run the backend

```bash
cd backend
python -m uvicorn main:app --reload
```

### 6. Open the API

```text
http://127.0.0.1:8000
```

### Swagger Documentation

```text
http://127.0.0.1:8000/docs
```

---

# 🧪 Example User Input

```json
{
    "name": "Student",
    "education": "Engineering Student",
    "skills": [
        "Python",
        "AI",
        "YOLO"
    ],
    "projects": [
        "Computer Vision Project",
        "Satellite Image Analysis"
    ],
    "experience": [
        "Hackathon"
    ],
    "interests": [
        "Artificial Intelligence",
        "Computer Vision",
        "Research"
    ],
    "goal": "AI Research Internship"
}
```

### Example Output

```text
Capabilities
├── Python
├── Artificial Intelligence
└── Computer Vision

Gaps
└── Research Experience

Missing Bridge
├── Build Research Project
├── Create Technical Report
├── Connect with Researcher
└── Apply to Target Opportunity
```

---

# 🗺️ Roadmap

### Phase 1 — MVP

* [x] FastAPI backend
* [x] User profile model
* [x] Capability analysis
* [x] Gap analysis
* [x] Missing Bridge engine
* [x] Opportunity data structure

### Phase 2 — Product

* [ ] Interactive frontend
* [ ] User dashboard
* [ ] Visual skill profile
* [ ] Personalized roadmap
* [ ] Opportunity matching

### Phase 3 — AI

* [ ] LLM-powered profile analysis
* [ ] Project understanding
* [ ] Better skill extraction
* [ ] Personalized recommendations
* [ ] AI-generated development plans

### Phase 4 — Integrations

* [ ] GitHub integration
* [ ] LinkedIn integration
* [ ] Portfolio analysis
* [ ] Research profile integration

### Phase 5 — Network

* [ ] Mentor matching
* [ ] Researcher matching
* [ ] Professional connections
* [ ] Organization partnerships

---

# 🔮 Future Vision

Etijahak aims to become more than a career platform.

The long-term vision is to create an **AI-powered personal opportunity map** for every young person.

```text
                 YOUR GOAL
                     │
                     ▼
             ┌───────────────┐
             │  AI ANALYSIS  │
             └───────┬───────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Skills      Experience   Network
          │          │          │
          └──────────┼──────────┘
                     ▼
               MISSING GAPS
                     │
                     ▼
              🌉 YOUR BRIDGE
                     │
                     ▼
              REAL OPPORTUNITY
```

---

# 👩‍💻 Team

### Team of 3

| Member      | Role                                     |
| ----------- | ---------------------------------------- |
| **Wasan**   | AI, Product & Technical Development      |
| **Farah**   | Marketing, UX Research & Branding        |
| **Shaikha** | Operations, Partnerships & Opportunities |

Together, the team combines:

**Technology + User Understanding + Real-World Connections**

---

# 🎯 Mission

> **To help young people turn their potential into evidence, experience, connections, and real opportunities.**

### اتجاهك

**اعرف قدراتك. ابنِ خبرتك. اصنع طريقك.**

---

## 📌 Project Status

**Current Status:** 🚧 MVP in Development

The backend prototype is currently operational, with the core analysis pipeline implemented.

The next major milestone is connecting the AI engine to an interactive frontend and transforming the **Missing Bridge** concept into a complete user experience.

