"""
app/email_classifier.py – Gmail email classification using Gemini AI.

Fix applied: API key read from GEMINI_API_KEY environment variable.
Never hardcode credentials in source.
"""

import json
import os
from typing import Any, Dict, List

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY")
if _API_KEY:
    genai.configure(api_key=_API_KEY)


def classify_emails_with_gemini(
    emails: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Classify a list of emails into Important / General / Spam using Gemini.

    Args:
        emails: List of email dicts (each has 'subject', 'from', 'snippet', …)

    Returns:
        Dict with keys "Important", "General", "Spam" each mapping to a list of
        email dicts from the input (not just indices).
    """
    if not _API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )

    if not emails:
        return {"Important": [], "General": [], "Spam": []}

    model = genai.GenerativeModel("gemini-1.5-flash")

    # Build a concise email summary for the prompt
    email_summaries = ""
    for i, email in enumerate(emails, 1):
        subject = email.get("subject", "(no subject)")
        sender = email.get("from", "unknown")
        snippet = email.get("snippet", "")[:200]
        email_summaries += f"Email {i}: Subject: {subject} | From: {sender} | Preview: {snippet}\n"

    prompt = (
        "You are an HR email assistant. Classify each email below into exactly one of:\n"
        "  - Job Application: resumes, CVs, job applications, candidate submissions\n"
        "  - Important: urgent tasks, HR matters, password resets, deadlines\n"
        "  - General: newsletters, known senders, routine updates\n"
        "  - Spam: promotions, advertisements, unknown senders, unwanted\n\n"
        f"{email_summaries}\n\n"
        "Respond with ONLY valid JSON (no markdown), in this exact format:\n"
        '{"Job Application": [1], "Important": [3], "General": [2], "Spam": [4, 5]}'
    )

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        classification: Dict[str, List[int]] = json.loads(text)

        def _collect(indices: List[int]) -> List[Dict[str, Any]]:
            return [
                emails[i - 1]
                for i in indices
                if isinstance(i, int) and 1 <= i <= len(emails)
            ]

        return {
            "Job Application": _collect(classification.get("Job Application", [])),
            "Important": _collect(classification.get("Important", [])),
            "General": _collect(classification.get("General", [])),
            "Spam": _collect(classification.get("Spam", [])),
        }

    except json.JSONDecodeError as exc:
        print(f"[classifier] JSON parse error: {exc}\nRaw response: {text!r}")
        return {"Job Application": [], "Important": [], "General": [], "Spam": []}
    except Exception as exc:
        print(f"[classifier] Gemini error: {exc}")
        return {"Job Application": [], "Important": [], "General": [], "Spam": []}


def parse_resume_with_gemini(email_body: str) -> Dict[str, Any]:
    """
    Parses a job application email body + PDF attachment text to extract candidate info.
    """
    if not _API_KEY:
        return {}

    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        "You are an expert HR resume parser. Extract the following information from "
        "the provided email and resume text. Respond with ONLY valid JSON (no markdown) "
        "using this exact structure:\n"
        "{\n"
        '  "Candidate Name": "Full Name",\n'
        '  "Role Applied For": "Job Title or None",\n'
        '  "Years of Experience": "e.g., 5 years or Unknown",\n'
        '  "Skills": ["Skill 1", "Skill 2"],\n'
        '  "Education": "Highest degree/university or Unknown",\n'
        '  "Summary": "A brief 2-sentence summary of the candidate\'s fit"\n'
        "}\n\n"
        f"EMAIL / RESUME TEXT:\n{email_body}"
    )

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        
        parsed_data = json.loads(text)
        return parsed_data
    except Exception as exc:
        print(f"[resume_parser] Gemini error: {exc}")
        return {}
