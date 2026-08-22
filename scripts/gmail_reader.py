from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.utils import parsedate_to_datetime
import base64
import re
from typing import List, Dict, Any, Optional
import streamlit as st

def get_email_service():
    """Authenticate and return the Gmail service."""
    import os
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    try:
        # Get the absolute path to credentials.json in the project root
        credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials.json')
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        st.error(f"Failed to authenticate with Gmail: {e}")
        st.error(f"Looking for credentials at: {credentials_path}")
        return None

def get_header(headers: List[Dict[str, str]], name: str) -> Optional[str]:
    """Get a header value from email headers."""
    for header in headers:
        if header.get('name', '').lower() == name.lower():
            return header.get('value')
    return None

def decode_body(part: Dict[str, Any]) -> str:
    """Decode email body from base64."""
    data = part.get('body', {}).get('data', '')
    if not data:
        return ""
    
    # Replace URL-safe base64 characters and add padding if needed
    data = data.replace('-', '+').replace('_', '/')
    padding = len(data) % 4
    if padding:
        data += '=' * (4 - padding)
    
    try:
        return base64.b64decode(data).decode('utf-8')
    except Exception as e:
        return f"[Error decoding email body: {str(e)}]"

def get_email_body(message: Dict[str, Any]) -> str:
    """Extract and decode the email body."""
    if 'parts' in message.get('payload', {}):
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                return decode_body(part)
            elif part['mimeType'] == 'multipart/alternative':
                for subpart in part.get('parts', []):
                    if subpart['mimeType'] == 'text/plain':
                        return decode_body(subpart)
    
    # Fallback to snippet if no plain text body found
    return message.get('snippet', '')

def read_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch and process emails from Gmail.
    
    Args:
        max_results: Maximum number of emails to fetch
        
    Returns:
        List of dictionaries containing email details
    """
    service = get_email_service()
    if not service:
        return []
    
    try:
        # Fetch email metadata
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        email_list = []
        
        for msg in messages:
            try:
                # Get full message details
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                headers = msg_data.get('payload', {}).get('headers', [])
                
                # Extract email details
                email = {
                    'id': msg['id'],
                    'subject': get_header(headers, 'Subject') or '(No Subject)',
                    'from': get_header(headers, 'From') or 'Unknown Sender',
                    'to': get_header(headers, 'To') or '',
                    'date': get_header(headers, 'Date') or '',
                    'body': get_email_body(msg_data),
                    'snippet': msg_data.get('snippet', ''),
                    'labels': msg_data.get('labelIds', []),
                    'has_attachments': any(
                        part.get('filename') 
                        for part in msg_data.get('payload', {}).get('parts', [])
                        if part.get('filename')
                    )
                }
                
                # Parse and format date
                if email['date']:
                    try:
                        dt = parsedate_to_datetime(email['date'])
                        email['date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                email_list.append(email)
                
            except Exception as e:
                print(f"Error processing email {msg.get('id')}: {e}")
                continue
                
        return email_list
        
    except Exception as e:
        st.error(f"Error fetching emails: {e}")
        return []

def display_emails(emails: List[Dict[str, Any]]) -> None:
    """Display emails in a user-friendly format using Streamlit."""
    if not emails:
        st.warning("No emails found in your inbox.")
        return
    
    st.subheader("📧 Your Emails")
    
    for i, email in enumerate(emails, 1):
        # Create a card for each email
        with st.container():
            st.markdown("---")
            
            # Email header with expander for full content
            with st.expander(f"{email['subject']} - {email['from']}"):
                # Email metadata in two columns
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown("**From:**")
                    st.markdown("**To:**")
                    st.markdown("**Date:**")
                    if email['has_attachments']:
                        st.markdown("**Attachments:**")
                
                with col2:
                    st.text(email['from'])
                    st.text(email['to'])
                    st.text(email['date'])
                    if email['has_attachments']:
                        st.text("📎 Yes")
                
                # Email body preview
                st.markdown("---")
                st.markdown("**Preview:**")
                st.text(email['snippet'])
                
                # Full email content
                st.markdown("---")
                st.markdown("### Full Email")
                st.text(email['body'])
