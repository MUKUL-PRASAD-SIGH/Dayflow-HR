# 🧠 Dayflow HR

A role-based HR Management System built with **Streamlit + SQLite + Gmail API + Gemini AI**.

---

## ✨ Features

| Area | Details |
|------|---------|
| **Auth** | Sign-up with OTP email verification, hashed passwords, role-based login |
| **Employee Portal** | Apply for leave, track status, view approved history |
| **HR Portal** | Approve / reject leave requests, view employee directory |
| **Gmail Dashboard** | Read inbox via Gmail API (OAuth 2.0) |
| **AI Classification** | Classify emails into Important / General / Spam using Gemini AI |

---

## 📁 Project Structure

```
Dayflow-HR/
├── app/
│   ├── main.py              # Entry point — run this with Streamlit
│   ├── db.py                # SQLite connection + auto schema init
│   ├── auth.py              # Login, signup, password hashing
│   ├── otp_utils.py         # OTP generation, verification, email delivery
│   ├── leave_employee.py    # Employee leave management UI
│   ├── leave_hr.py          # HR leave management dashboard
│   ├── gmail_reader.py      # Gmail API integration
│   └── email_classifier.py  # Gemini AI email classification
├── tests/
│   ├── test_db.py
│   ├── test_auth.py
│   ├── test_otp.py
│   └── test_leave.py
├── .streamlit/
│   └── config.toml          # Dark theme + server settings
├── .env.example             # Template — copy to .env and fill in values
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/MUKUL-PRASAD-SIGH/Dayflow-HR
cd Dayflow-HR
```

### 2. Set up a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env and fill in your values
```

Required `.env` values:
```
SECRET_KEY=...              # Any long random string
EMAIL_SENDER=...            # Your Gmail address
EMAIL_PASSWORD=...          # Gmail App Password (not your account password)
GEMINI_API_KEY=...          # From Google AI Studio
```

### 5. Set up Gmail API (for HR Email Dashboard)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Gmail API**
3. Create **OAuth 2.0 credentials** (Desktop app)
4. Download as `credentials.json` → place in project root
5. On first run, a browser window will open to authorize the app

### 6. Run the application
```bash
streamlit run app/main.py
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔒 Security Notes

- Passwords are hashed with SHA-256 + SECRET_KEY salt before storage
- `.env`, `credentials.json`, and `token.json` are gitignored — never commit them
- If you previously committed secrets, rotate your API keys immediately

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend + Backend | Python · Streamlit |
| Database | SQLite (built-in) |
| Auth | OTP via SMTP · SHA-256 hashing |
| Email Reading | Gmail API · OAuth 2.0 |
| AI Classification | Google Gemini 1.5 Flash |

---

Made by **Mukul Prasad**
