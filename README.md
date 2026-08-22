# 🧠 Dayflow HR
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B.svg?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit Badge">
  <img src="https://img.shields.io/badge/SQLite-003B57.svg?style=for-the-badge&logo=SQLite&logoColor=white" alt="SQLite Badge">
  <img src="https://img.shields.io/badge/Google_Cloud-4285F4.svg?style=for-the-badge&logo=Google-Cloud&logoColor=white" alt="Google Cloud Badge">
  <img src="https://img.shields.io/badge/Gemini_AI-8E75B2.svg?style=for-the-badge&logo=Google-gemini&logoColor=white" alt="Gemini AI Badge">
</p>

A robust, role-based HR Management System built with **Streamlit + SQLite + Gmail API + Gemini AI**.

---

## ✨ Features

| Area | Details |
|------|---------|
| **Auth** | Sign-up with OTP email verification, robust password validation, login by Employee ID or Email |
| **Employee Portal** | Manage profile, Check-in/out attendance, View payroll, Apply for leave (Sick/Paid/Unpaid), Track status |
| **HR Portal** | Real-time metrics dashboard, View/edit employee profiles, Monitor daily attendance logs, Manage payroll structures, Approve/reject leave requests |
| **Gmail Dashboard** | Read inbox via Gmail API (OAuth 2.0) directly inside the app |
| **AI Email Classification** | Smartly classify incoming emails into Important / Job Application / General / Spam using Gemini AI |
| **AI Resume Parsing** | Automatically extract text from PDF attachments (via PyPDF2) and parse candidate details using Gemini |

---

## 📁 Project Structure

```text
Dayflow-HR/
├── app/
│   ├── main.py              # Entry point — run this with Streamlit
│   ├── db.py                # SQLite connection + auto schema init
│   ├── auth.py              # Login, signup, password hashing
│   ├── otp_utils.py         # OTP generation, verification, email delivery
│   ├── profile.py           # Employee profile management
│   ├── attendance.py        # Daily check-in/out and logging
│   ├── payroll.py           # Salary structure and net pay calculation
│   ├── leave_employee.py    # Employee dashboard (attendance, payroll, leaves)
│   ├── leave_hr.py          # HR dashboard (metrics, profiles, payroll, leaves)
│   ├── gmail_reader.py      # Gmail API integration + PyPDF2 extraction
│   └── email_classifier.py  # Gemini AI email classification & resume parsing
├── tests/
│   └── test_core_features.py # Comprehensive single-file test suite
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
```env
SECRET_KEY=...              # Any long random string
EMAIL_SENDER=...            # Your Gmail address
EMAIL_PASSWORD=...          # Gmail App Password (not your account password)
GEMINI_API_KEY=...          # From Google AI Studio
```

### 5. Set up Gmail API (for HR Email Dashboard)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Gmail API**
3. Create **OAuth 2.0 credentials** (Desktop app)
4. Download as `credentials.json` → place in project root.
5. **⚠️ IMPORTANT: Test Users Configuration**
   - If your Google Cloud OAuth Consent Screen is set to "Testing", you will get an `Error 403: access_denied` unless you explicitly whitelist your email address.
   - Go to **APIs & Services > OAuth consent screen**.
   - Scroll down to **Test users**.
   - Click **+ ADD USERS** and add authorized test users (e.g., `mukulprasad957@gmail.com`).
6. On first run, a browser window will open to authorize the app.

### 6. Run the application
```bash
streamlit run app/main.py
```

---

## 🧪 Running Tests

To run the comprehensive test suite verifying the database, auth, OTP generation, and leave management lifecycle:

```bash
pytest tests/test_core_features.py -v
```

---

## 🔒 Security Notes

- Passwords are hashed with SHA-256 + SECRET_KEY salt before storage.
- `.env`, `credentials.json`, and `token.json` are gitignored — never commit them.
- If you previously committed secrets, rotate your API keys immediately.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend + Backend** | Python · Streamlit |
| **Database** | SQLite (built-in) |
| **Auth** | OTP via SMTP · SHA-256 hashing |
| **Email Reading** | Gmail API · OAuth 2.0 · PyPDF2 |
| **AI Classification** | Google Gemini 1.5 Flash |

---

Made by **Mukul Prasad**
