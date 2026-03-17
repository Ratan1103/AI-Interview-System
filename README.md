# InterviewAI 🎙️

An AI-powered mock interview web application built with Django and Gemini API.

## Features

- 📄 Resume upload with automatic text extraction (PDF)
- ⚙️ Interview configuration (experience level, difficulty, type, topic)
- 🤖 Adaptive AI interviewer powered by Google Gemini
- 🎙️ Voice answers via Web Speech API (no cost, browser-native)
- 📊 Real-time feedback: correctness, missing points, improvements, sample answer
- 🔁 Intelligent interview loop — AI adapts based on your performance

---

## Quick Start

### 1. Clone & set up environment

```bash
git clone <your-repo>
cd AI_Resume

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
DJANGO_SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

> Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Load environment variables

```bash
# Linux / macOS
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object { $key, $val = $_ -split '=', 2; [Environment]::SetEnvironmentVariable($key, $val) }
```

### 4. Set up the database

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for admin access
```

### 5. Run the development server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## Project Structure

```
AI_Resume/
├── ai_resume/              # Django project config
│   ├── settings.py         # All settings (reads from env vars)
│   └── urls.py             # Root URL routing
│
├── core/                   # Main application
│   ├── models.py           # Resume model
│   ├── views.py            # All views (auth, dashboard, interview loop)
│   ├── ai.py               # Gemini API integration
│   ├── utils.py            # PDF text extraction
│   └── admin.py            # Admin configuration
│
├── templates/              # HTML templates
│   ├── base.html           # Shared layout + navbar
│   ├── home.html           # Landing page
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html      # Resume status + interview config form
│   ├── upload_resume.html  # Drag & drop PDF upload
│   ├── interview.html      # Live interview loop
│   └── interview_end.html  # Session summary
│
├── static/
│   ├── css/style.css       # All styles
│   └── js/main.js          # Global JS utilities
│
├── media/                  # Uploaded resume files (git-ignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Interview Flow

```
Register → Login → Dashboard
  → Upload Resume (PDF)
  → Configure (experience / difficulty / type / topic)
  → Start Interview
      ↓
  AI generates Question 1
      ↓
  User answers (voice or text)
      ↓
  AI evaluates + generates Question 2
      ↓
  Repeat until "End Session"
      ↓
  Session summary
```

---

## Tech Stack

| Layer     | Technology                  |
|-----------|-----------------------------|
| Backend   | Django 4.x                  |
| AI        | Google Gemini 1.5 Flash     |
| PDF Parse | pypdf                       |
| Voice     | Web Speech API (browser)    |
| Frontend  | Django Templates + CSS + JS |
| Database  | SQLite (dev)                |

---

## Notes

- Voice recording requires **Chrome or Edge** (Web Speech API)
- The app stores only the resume file + extracted text. Interview history lives in the session only (not persisted to DB), as per the spec.
- The Gemini model used is `gemini-1.5-flash` — fast, cheap, and handles long resume contexts well.
