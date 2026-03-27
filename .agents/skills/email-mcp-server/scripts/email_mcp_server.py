#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email MCP Server - Model Context Protocol server for Gmail operations.

This MCP server provides email capabilities to Claude Code:
- send_email: Send emails via Gmail API
- draft_email: Create drafts without sending
- search_emails: Search Gmail
- mark_read: Mark emails as read
- list_labels: Get Gmail labels

Usage:
    python email_mcp_server.py

Configure in Claude Code mcp.json:
{
  "servers": [{
    "name": "email",
    "command": "python",
    "args": ["/path/to/email_mcp_server.py"]
  }]
}
"""

import sys
import os
import json
import base64
import logging
from pathlib import Path
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing required dependencies. Install with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EmailMCP')


class EmailMCPServer:
    """MCP server for Gmail operations."""

    def __init__(self, credentials_path: str = None, token_path: str = None):
        """
        Initialize Email MCP Server.

        Args:
            credentials_path: Path to Gmail OAuth2 credentials.json
            token_path: Path to store token.json
        """
        self.credentials_path = Path(credentials_path) if credentials_path else Path('credentials.json')
        self.token_path = Path(token_path) if token_path else Path('token.json')
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API."""
        try:
            creds = None

            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired token...")
                    creds.refresh(Request())
                else:
                    logger.info("Starting OAuth2 flow...")
                    if not self.credentials_path.exists():
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_path}\n"
                            "Download from Google Cloud Console > APIs & Services > Credentials"
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0, open_browser=False)

                self.token_path.write_text(creds.to_json())
                logger.info(f"Token saved to: {self.token_path}")

            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authenticated successfully")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def send_email(self, to: str, subject: str, body: str, 
                   attachments: list = None, cc: str = None) -> dict:
        """
        Send an email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            attachments: List of file paths to attach
            cc: CC recipient

        Returns:
            dict with message_id and status
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['from'] = 'me'
            message['subject'] = subject
            if cc:
                message['cc'] = cc

            # Add body
            if body.startswith('<') and body.endswith('>'):
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for filepath in attachments:
                    filepath = Path(filepath)
                    if not filepath.exists():
                        logger.warning(f"Attachment not found: {filepath}")
                        continue
                    
                    with open(filepath, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=filepath.name)
                        part['Content-Disposition'] = f'attachment; filename="{filepath.name}"'
                        message.attach(part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent to {to}: {sent_message['id']}")

            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message['threadId'],
                'status': 'sent'
            }

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def draft_email(self, to: str, subject: str, body: str,
                    attachments: list = None, cc: str = None) -> dict:
        """
        Create a draft email without sending.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            attachments: List of file paths to attach
            cc: CC recipient

        Returns:
            dict with draft_id and status
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['from'] = 'me'
            message['subject'] = subject
            if cc:
                message['cc'] = cc

            # Add body
            if body.startswith('<') and body.endswith('>'):
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for filepath in attachments:
                    filepath = Path(filepath)
                    if filepath.exists():
                        with open(filepath, 'rb') as f:
                            part = MIMEApplication(f.read(), Name=filepath.name)
                            part['Content-Disposition'] = f'attachment; filename="{filepath.name}"'
                            message.attach(part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()

            logger.info(f"Draft created: {draft['id']}")

            return {
                'success': True,
                'draft_id': draft['id'],
                'message_id': draft['message']['id'],
                'status': 'draft'
            }

        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_emails(self, query: str, max_results: int = 10) -> dict:
        """
        Search Gmail for messages.

        Args:
            query: Gmail search query (e.g., "is:unread from:example@gmail.com")
            max_results: Maximum number of results

        Returns:
            dict with list of messages
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            email_list = []

            for msg in messages:
                try:
                    full_msg = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
                    ).execute()

                    headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
                    email_list.append({
                        'id': msg['id'],
                        'thread_id': msg['threadId'],
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'subject': headers.get('Subject', ''),
                        'date': headers.get('Date', ''),
                        'snippet': full_msg.get('snippet', '')
                    })
                except Exception as e:
                    logger.warning(f"Error fetching message {msg['id']}: {e}")

            return {
                'success': True,
                'count': len(email_list),
                'messages': email_list
            }

        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def mark_read(self, message_id: str) -> dict:
        """
        Mark an email as read.

        Args:
            message_id: Gmail message ID

        Returns:
            dict with status
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            logger.info(f"Marked message {message_id} as read")

            return {
                'success': True,
                'message_id': message_id,
                'status': 'read'
            }

        except Exception as e:
            logger.error(f"Error marking read: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_labels(self) -> dict:
        """
        Get Gmail labels/folders.

        Returns:
            dict with list of labels
        """
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            return {
                'success': True,
                'count': len(labels),
                'labels': [
                    {'id': l['id'], 'name': l['name']} 
                    for l in labels
                ]
            }

        except Exception as e:
            logger.error(f"Error listing labels: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# MCP Server Protocol Implementation

def create_response(result: dict, error: str = None) -> str:
    """Create JSON-RPC response."""
    response = {
        'jsonrpc': '2.0',
        'id': None,
    }
    if error:
        response['error'] = {'code': -32000, 'message': error}
    else:
        response['result'] = result
    return json.dumps(response)


def handle_request(request_str: str, server: EmailMCPServer) -> str:
    """Handle MCP request."""
    try:
        request = json.loads(request_str)
        method = request.get('method', '')
        params = request.get('params', {})
        request_id = request.get('id')

        logger.info(f"Handling method: {method}")

        result = None
        error = None

        if method == 'send_email':
            result = server.send_email(
                to=params.get('to', ''),
                subject=params.get('subject', ''),
                body=params.get('body', ''),
                attachments=params.get('attachments', []),
                cc=params.get('cc')
            )
        elif method == 'draft_email':
            result = server.draft_email(
                to=params.get('to', ''),
                subject=params.get('subject', ''),
                body=params.get('body', ''),
                attachments=params.get('attachments', []),
                cc=params.get('cc')
            )
        elif method == 'search_emails':
            result = server.search_emails(
                query=params.get('query', 'is:unread'),
                max_results=params.get('max_results', 10)
            )
        elif method == 'mark_read':
            result = server.mark_read(
                message_id=params.get('message_id', '')
            )
        elif method == 'list_labels':
            result = server.list_labels()
        elif method == 'initialize':
            result = {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'email-mcp-server',
                    'version': '0.1.0'
                }
            }
        else:
            error = f"Method not found: {method}"

        response = create_response(result or {}, error)
        if request_id is not None:
            response_dict = json.loads(response)
            response_dict['id'] = request_id
            response = json.dumps(response_dict)

        return response

    except Exception as e:
        return create_response({}, str(e))


def main():
    """Main entry point - stdio MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description='Email MCP Server')
    parser.add_argument('--credentials', type=str, default=None,
                        help='Path to credentials.json')
    parser.add_argument('--token', type=str, default=None,
                        help='Path to token.json')
    parser.add_argument('--port', type=int, default=None,
                        help='Port for HTTP mode (default: stdio)')

    args = parser.parse_args()

    try:
        server = EmailMCPServer(
            credentials_path=args.credentials,
            token_path=args.token
        )
        logger.info("Email MCP Server started (stdio mode)")

        # Read requests from stdin
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            response = handle_request(line, server)
            print(response, flush=True)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
