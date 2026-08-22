"""
app/gmail_reader.py – Gmail API integration via OAuth 2.0.

Credentials file location: <project_root>/credentials.json
Token cache:               <project_root>/token.json (auto-created on first auth)

Both files are excluded from git via .gitignore.
"""

import base64
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
from email.utils import parsedate_to_datetime

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CREDENTIALS_PATH = _PROJECT_ROOT / "credentials.json"
_TOKEN_PATH = _PROJECT_ROOT / "token.json"
_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_credentials() -> Optional[Credentials]:
    """Load or refresh OAuth credentials, triggering browser auth if needed."""
    creds: Optional[Credentials] = None

    if _TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), _SCOPES)
        except Exception:
            pass

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _TOKEN_PATH.write_text(creds.to_json())
            return creds
        except Exception:
            pass

    if not _CREDENTIALS_PATH.exists():
        st.error(
            f"Gmail credentials not found at `{_CREDENTIALS_PATH}`. "
            "Download your OAuth 2.0 credentials from Google Cloud Console and "
            "place them at the project root as `credentials.json`."
        )
        return None

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS_PATH), _SCOPES)
        creds = flow.run_local_server(port=0)
        _TOKEN_PATH.write_text(creds.to_json())
        return creds
    except Exception as exc:
        st.error(f"Gmail authentication failed: {exc}")
        return None


def get_email_service():
    """Return an authenticated Gmail API service, or None on failure."""
    creds = _get_credentials()
    if not creds:
        return None
    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as exc:
        st.error(f"Failed to build Gmail service: {exc}")
        return None


def _get_header(headers: List[Dict[str, str]], name: str) -> Optional[str]:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None


def _decode_body(part: Dict[str, Any]) -> str:
    data = part.get("body", {}).get("data", "")
    if not data:
        return ""
    data = data.replace("-", "+").replace("_", "/")
    padding = len(data) % 4
    if padding:
        data += "=" * (4 - padding)
    try:
        return base64.b64decode(data).decode("utf-8", errors="replace")
    except Exception:
        return ""


import io
import PyPDF2

def _extract_pdf_text(data_b64: str) -> str:
    """Decodes base64 PDF data and extracts text using PyPDF2."""
    try:
        data = data_b64.replace("-", "+").replace("_", "/")
        padding = len(data) % 4
        if padding:
            data += "=" * (4 - padding)
        pdf_bytes = base64.b64decode(data)
        
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"[gmail] Error extracting PDF text: {e}")
        return ""

def _get_email_body(message: Dict[str, Any], service: Any = None, message_id: str = None) -> str:
    payload = message.get("payload", {})
    body_text = ""
    
    # 1. Extract plain text body
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            body_text += _decode_body(part) + "\n"
        elif part.get("mimeType") == "multipart/alternative":
            for sub in part.get("parts", []):
                if sub.get("mimeType") == "text/plain":
                    body_text += _decode_body(sub) + "\n"
                    
    # 2. Extract PDF attachments if service and message_id are provided
    if service and message_id:
        for part in payload.get("parts", []):
            filename = part.get("filename", "")
            if filename and filename.lower().endswith(".pdf"):
                attachment_id = part.get("body", {}).get("attachmentId")
                if attachment_id:
                    try:
                        att = service.users().messages().attachments().get(
                            userId="me", messageId=message_id, id=attachment_id
                        ).execute()
                        data_b64 = att.get("data", "")
                        if data_b64:
                            pdf_text = _extract_pdf_text(data_b64)
                            if pdf_text:
                                body_text += f"\n\n--- EXTRACTED ATTACHMENT ({filename}) ---\n"
                                body_text += pdf_text
                    except Exception as e:
                        print(f"[gmail] Failed to fetch attachment {filename}: {e}")

    if body_text.strip():
        return body_text.strip()
        
    return message.get("snippet", "")


def read_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    """Fetch and return a list of email dicts from the user's inbox."""
    service = get_email_service()
    if not service:
        return []

    try:
        result = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, labelIds=["INBOX"])
            .execute()
        )
        messages = result.get("messages", [])
        emails: List[Dict[str, Any]] = []

        for msg in messages:
            try:
                msg_data = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )
                headers = msg_data.get("payload", {}).get("headers", [])

                raw_date = _get_header(headers, "Date") or ""
                try:
                    formatted_date = parsedate_to_datetime(raw_date).strftime(
                        "%Y-%m-%d %H:%M"
                    )
                except Exception:
                    formatted_date = raw_date

                emails.append(
                    {
                        "id": msg["id"],
                        "subject": _get_header(headers, "Subject") or "(No Subject)",
                        "from": _get_header(headers, "From") or "Unknown",
                        "to": _get_header(headers, "To") or "",
                        "date": formatted_date,
                        "body": _get_email_body(msg_data, service, msg["id"]),
                        "snippet": msg_data.get("snippet", ""),
                        "labels": msg_data.get("labelIds", []),
                        "has_attachments": any(
                            p.get("filename")
                            for p in msg_data.get("payload", {}).get("parts", [])
                            if p.get("filename")
                        ),
                    }
                )
            except Exception as exc:
                print(f"[gmail] Error processing message {msg.get('id')}: {exc}")
                continue

        return emails

    except Exception as exc:
        st.error(f"Error fetching emails: {exc}")
        return []


def display_emails(emails: List[Dict[str, Any]]) -> None:
    """Render email list in Streamlit."""
    if not emails:
        st.warning("No emails found in your inbox.")
        return

    from app.ui_utils import render_badge
    for email in emails:
        attachment_badge = f" {render_badge('Attachment', 'employee')}" if email["has_attachments"] else ""
        with st.expander(f"✉️ {email['subject']} — {email['from']}"):
            st.markdown(
                f"""
                <div style="margin-bottom: 12px; font-size:14px; color:#e2e8f0; line-height: 1.6;">
                    <div><b>From:</b> {email['from']}</div>
                    <div><b>To:</b> {email['to']}</div>
                    <div><b>Date:</b> {email['date']}{attachment_badge}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown("**Preview:**")
            st.info(email["snippet"])
            
            st.markdown("**Full Body:**")
            st.text_area(
                "Email Content", 
                value=email["body"] or "(No plain-text body found)", 
                height=180, 
                disabled=True, 
                key=f"body_view_{email['id']}"
            )
