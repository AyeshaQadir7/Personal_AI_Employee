#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher - Monitors Gmail for new unread/important messages.

This is a Silver Tier watcher that integrates with Gmail API to detect
new emails and create action files for AI processing.

Usage:
    python gmail_watcher.py /path/to/obsidian/vault

Prerequisites:
    1. Enable Gmail API in Google Cloud Console
    2. Download credentials.json to project root
    3. Run once to authenticate (creates token.json)
"""

import sys
import argparse
import os
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from email import message_from_bytes

try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import reauth
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing required dependencies. Install with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

from src.base_watcher import BaseWatcher


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Keywords for priority detection
HIGH_PRIORITY_KEYWORDS = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 'bill', 'help', 'support']
INVOICE_KEYWORDS = ['invoice', 'bill', 'payment', 'receipt', 'due']
CONTRACT_KEYWORDS = ['contract', 'agreement', 'proposal', 'terms']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new unread/important messages and creates action files.

    When a new email is detected:
    1. Fetch email metadata and content
    2. Create a .md action file in Needs_Action
    3. Track the message ID to avoid reprocessing
    """

    def __init__(self, vault_path: str, credentials_path: str = None, 
                 check_interval: int = 120, dry_run: bool = False):
        """
        Initialize the Gmail Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to Gmail OAuth2 credentials.json
            check_interval: Seconds between checks (default: 120)
            dry_run: If True, log actions but don't create files
        """
        super().__init__(vault_path, check_interval=check_interval)

        # Credentials path
        self.credentials_path = Path(credentials_path) if credentials_path else Path('credentials.json')
        self.token_path = Path('token.json')
        self.dry_run = dry_run

        # Gmail service
        self.service = None

        # Track processed message IDs
        self.processed_ids: set = set()

        # Load previously processed IDs
        self._load_processed_ids()

        # Initialize Gmail service
        self._authenticate()

        self.logger.info(f"Watching Gmail inbox: {self.credentials_path}")
        if self.dry_run:
            self.logger.warning("DRY RUN MODE - No action files will be created")

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        try:
            creds = None

            # Load token if exists
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    self.token_path, SCOPES
                )

            # Refresh or re-authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired token...")
                    creds.refresh(Request())
                else:
                    self.logger.info("Starting OAuth2 flow...")
                    if not self.credentials_path.exists():
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_path}\n"
                            "Download from Google Cloud Console > APIs & Services > Credentials"
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0, open_browser=True)

                # Save token for future runs
                self.token_path.write_text(creds.to_json())
                self.logger.info(f"Token saved to: {self.token_path}")

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API authenticated successfully")

        except FileNotFoundError as e:
            self.logger.error(str(e))
            raise
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new unread/important emails.

        Returns:
            List of dictionaries containing email data
        """
        if not self.service:
            self.logger.error("Gmail service not initialized")
            return []

        new_emails = []

        try:
            # Search for unread messages (optionally filter by IMPORTANT label)
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=50
            ).execute()

            messages = results.get('messages', [])

            self.logger.info(f"Found {len(messages)} unread message(s)")

            for message in messages:
                msg_id = message['id']

                # Skip if already processed
                if msg_id in self.processed_ids:
                    continue

                # Fetch full message
                try:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='full'
                    ).execute()

                    email_data = self._parse_email(msg)
                    
                    if email_data:
                        new_emails.append(email_data)
                        self.logger.info(f"New email: {email_data['subject'][:50]}...")

                except HttpError as e:
                    self.logger.error(f"Error fetching message {msg_id}: {e}")

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            if e.resp.status == 401:
                self.logger.warning("Authentication expired, will re-authenticate on next cycle")
                self.service = None
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")

        return new_emails

    def _parse_email(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse Gmail message into structured data.

        Args:
            msg: Gmail API message object

        Returns:
            Dictionary with email data or None if parsing fails
        """
        try:
            payload = msg.get('payload', {})
            headers = {h['name']: h['value'] for h in payload.get('headers', [])}

            # Extract basic info
            from_email = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date = headers.get('Date', '')
            message_id = msg['id']

            # Extract body
            body = self._extract_body(payload)

            # Extract attachments
            attachments = self._get_attachments_info(payload)

            # Determine priority
            priority = self._determine_priority(subject, body)

            return {
                'type': 'email',
                'message_id': message_id,
                'from': from_email,
                'subject': subject,
                'date': date,
                'received': datetime.now().isoformat(),
                'priority': priority,
                'body': body,
                'attachments': attachments,
                'snippet': msg.get('snippet', '')
            }

        except Exception as e:
            self.logger.error(f"Error parsing email: {e}")
            return None

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body text
        """
        body = ""

        # Try multipart first
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    body = self._decode_part(part)
                    break
                elif mime_type == 'text/html' and not body:
                    body = self._decode_part(part)
        else:
            # Single part message
            body = self._decode_part(payload)

        # Clean up body text
        if body:
            # Remove excessive whitespace
            body = '\n'.join([line.strip() for line in body.split('\n')])

        return body or "[No text content]"

    def _decode_part(self, part: Dict[str, Any]) -> str:
        """Decode a MIME part of the email."""
        try:
            data = part.get('body', {}).get('data', '')
            if data:
                # Gmail uses URL-safe base64 encoding
                decoded = base64.urlsafe_b64decode(data)
                return decoded.decode('utf-8', errors='replace')
        except Exception as e:
            self.logger.warning(f"Error decoding email part: {e}")
        return ""

    def _get_attachments_info(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get attachment information from email.

        Args:
            payload: Gmail message payload

        Returns:
            List of attachment metadata
        """
        attachments = []

        def traverse_parts(part):
            if 'parts' in part:
                for child in part['parts']:
                    traverse_parts(child)
            else:
                filename = part.get('filename', '')
                if filename:
                    mime_type = part.get('mimeType', 'application/octet-stream')
                    size = part.get('body', {}).get('length', 0)
                    attachments.append({
                        'filename': filename,
                        'mime_type': mime_type,
                        'size': size
                    })

        traverse_parts(payload)
        return attachments

    def _determine_priority(self, subject: str, body: str) -> str:
        """
        Determine email priority based on keywords.

        Args:
            subject: Email subject
            body: Email body

        Returns:
            'high', 'medium', or 'low'
        """
        text = f"{subject} {body}".lower()

        # High priority keywords
        if any(kw in text for kw in HIGH_PRIORITY_KEYWORDS):
            return 'high'

        # Medium priority: invoice/contract related
        if any(kw in text for kw in INVOICE_KEYWORDS + CONTRACT_KEYWORDS):
            return 'medium'

        return 'low'

    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.

        Args:
            item: Dictionary containing email data

        Returns:
            Path to created action file, or None if creation failed
        """
        # Check if already processed
        if item['message_id'] in self.processed_ids:
            self.logger.debug(f"Email already processed: {item['message_id']}")
            return None

        # Create action file
        timestamp = self._get_timestamp()
        filename = f"EMAIL_{self._sanitize_filename(item['subject'])}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Generate suggested actions based on content
        suggested_actions = self._get_suggested_actions(item)

        # Format attachments
        attachments_text = self._format_attachments(item['attachments'])

        content = f"""---
type: {item['type']}
from: {item['from']}
subject: {item['subject']}
received: {item['received']}
priority: {item['priority']}
status: pending
message_id: {item['message_id']}
---

# Email: {item['subject']}

## Sender
{item['from']}

## Received
{datetime.fromisoformat(item['received']).strftime('%Y-%m-%d %I:%M %p')}

## Content
{item['body']}

## Attachments
{attachments_text}

## Suggested Actions
{suggested_actions}

## Notes
<!-- Add any additional context or instructions here -->

---
*Created by Gmail Watcher*
"""

        if not self.dry_run:
            filepath.write_text(content, encoding='utf-8')
            self.processed_ids.add(item['message_id'])
            self._save_processed_ids()
            self.logger.info(f"Created action file: {filepath.name}")
        else:
            self.logger.info(f"[DRY RUN] Would create: {filepath.name}")

        return filepath

    def _get_suggested_actions(self, item: Dict[str, Any]) -> str:
        """
        Generate suggested actions based on email content.

        Args:
            item: Email data dictionary

        Returns:
            Markdown formatted list of suggested actions
        """
        actions = []
        text = f"{item['subject']} {item['body']}".lower()

        # Invoice/payment related
        if any(kw in text for kw in INVOICE_KEYWORDS):
            actions.extend([
                "- [ ] Extract invoice details (amount, due date, vendor)",
                "- [ ] Log in accounting tracker",
                "- [ ] Schedule payment if approved",
            ])

        # Contract/agreement related
        elif any(kw in text for kw in CONTRACT_KEYWORDS):
            actions.extend([
                "- [ ] Review key terms and dates",
                "- [ ] Extract action items",
                "- [ ] Schedule follow-up if needed",
            ])

        # Urgent/emergency
        elif any(kw in text for kw in ['urgent', 'asap', 'emergency']):
            actions.extend([
                "- [ ] Respond immediately",
                "- [ ] Determine required action",
                "- [ ] Escalate if necessary",
            ])

        # Help/support request
        elif any(kw in text for kw in ['help', 'support']):
            actions.extend([
                "- [ ] Understand the issue",
                "- [ ] Provide solution or workaround",
                "- [ ] Follow up to ensure resolution",
            ])

        # Default actions
        if not actions:
            actions = [
                "- [ ] Read and understand email",
                "- [ ] Determine required action",
                "- [ ] Draft response if needed",
            ]

        # Always add completion action
        actions.append("- [ ] Move to /Done when complete")

        return '\n'.join(actions)

    def _format_attachments(self, attachments: List[Dict[str, Any]]) -> str:
        """Format attachments list for display."""
        if not attachments:
            return "None"

        lines = []
        for att in attachments:
            size = self._format_size(att['size'])
            lines.append(f"- {att['filename']} ({size})")

        return '\n'.join(lines)

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def stop(self):
        """Gracefully stop the watcher."""
        # Mark last processed emails as read (optional)
        super().stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Gmail Watcher - Monitor Gmail for new messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python gmail_watcher.py /path/to/vault
    python gmail_watcher.py /path/to/vault --interval 60
    python gmail_watcher.py /path/to/vault --credentials /path/to/credentials.json

Setup:
    1. Enable Gmail API in Google Cloud Console
    2. Download credentials.json
    3. Run watcher (will open browser for OAuth2 consent)
    4. Token saved for future runs
        """
    )

    parser.add_argument(
        'vault_path',
        help='Path to the Obsidian vault root'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=120,
        help='Check interval in seconds (default: 120)'
    )
    parser.add_argument(
        '--credentials', '-c',
        type=str,
        default=None,
        help='Path to Gmail OAuth2 credentials.json (default: ./credentials.json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without creating action files'
    )

    args = parser.parse_args()

    # Validate vault path
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Create and run watcher
    watcher = GmailWatcher(
        vault_path=str(vault_path),
        credentials_path=args.credentials,
        check_interval=args.interval,
        dry_run=args.dry_run
    )

    print(f"\n📧 Gmail Watcher Started")
    print(f"   Vault: {vault_path}")
    print(f"   Check Interval: {args.interval}s")
    print(f"   Dry Run: {'Yes' if args.dry_run else 'No'}")
    print(f"\n📬 Watching for new unread emails...")
    print(f"   Press Ctrl+C to stop\n")

    watcher.run()


if __name__ == "__main__":
    main()
