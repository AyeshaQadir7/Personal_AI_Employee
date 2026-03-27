#!/usr/bin/env python3
"""
Simple Email MCP Server - Sends emails via Gmail API.

Usage:
    python email_mcp_simple.py
    
Or call directly from Python:
    from email_mcp_simple import send_email
    send_email("to@example.com", "Subject", "Body")
"""

import os
import base64
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    raise

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]


def get_gmail_service():
    """Get authenticated Gmail service."""
    creds = None
    token_path = Path(__file__).parent.parent / 'token.json'
    credentials_path = Path(__file__).parent.parent / 'credentials.json'
    
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
        token_path.write_text(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def send_email(to: str, subject: str, body: str, html: bool = False) -> dict:
    """
    Send an email via Gmail API.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        html: If True, treat body as HTML
    
    Returns:
        dict with success status and message_id
    """
    try:
        service = get_gmail_service()
        
        # Create message
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = 'me'
        message['subject'] = subject
        
        # Add body
        mime_type = 'html' if html else 'plain'
        message.attach(MIMEText(body, mime_type))
        
        # Encode
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send
        sent = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✓ Email sent to {to}: {sent['id']}")
        return {
            'success': True,
            'message_id': sent['id'],
            'thread_id': sent['threadId']
        }
        
    except Exception as e:
        print(f"✗ Email failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# MCP Server Protocol (stdio)
if __name__ == "__main__":
    import sys
    import json
    
    print("Email MCP Server started (stdio mode)", file=sys.stderr)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            method = request.get('method', '')
            params = request.get('params', {})
            request_id = request.get('id')
            
            result = None
            error = None
            
            if method == 'send_email':
                result = send_email(
                    to=params.get('to', ''),
                    subject=params.get('subject', ''),
                    body=params.get('body', ''),
                    html=params.get('html', False)
                )
            elif method == 'initialize':
                result = {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {'tools': {}},
                    'serverInfo': {'name': 'email-mcp', 'version': '0.1.0'}
                }
            else:
                error = f"Method not found: {method}"
            
            # Send response
            response = {'jsonrpc': '2.0', 'id': request_id}
            if error:
                response['error'] = {'code': -32000, 'message': error}
            else:
                response['result'] = result
            
            print(json.dumps(response), flush=True)
            
        except Exception as e:
            response = {'jsonrpc': '2.0', 'error': {'code': -32000, 'message': str(e)}}
            print(json.dumps(response), flush=True)
