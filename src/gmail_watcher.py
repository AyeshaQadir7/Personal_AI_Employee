#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher - Monitors Gmail for new unread/important messages.

This is a Silver Tier watcher that integrates with Gmail API to detect
new emails and create action files for Qwen Code processing.

Usage:
    python src/gmail_watcher.py /path/to/obsidian/vault

Prerequisites:
    1. Enable Gmail API in Google Cloud Console
    2. credentials.json in project root
    3. Run once to authenticate (creates token.json)

Author: AI Employee Project
Tier: Silver
"""

import sys
import os
import argparse
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
    print("=" * 60)
    print("MISSING DEPENDENCIES")
    print("=" * 60)
    print("Install required packages with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    print("=" * 60)
    sys.exit(1)

# Add parent directory to path for base_watcher import
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


# Gmail API scopes - we need read-only for the watcher
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Keywords for priority detection
HIGH_PRIORITY_KEYWORDS = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 'bill', 'help', 'support']
INVOICE_KEYWORDS = ['invoice', 'bill', 'payment', 'receipt', 'due', 'amount']
CONTRACT_KEYWORDS = ['contract', 'agreement', 'proposal', 'terms', 'sign']
CLIENT_KEYWORDS = ['client', 'customer', 'project', 'deliver', 'deadline']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new unread/important messages and creates action files.

    When a new email is detected:
    1. Fetch email metadata and content via Gmail API
    2. Create a .md action file in Needs_Action folder
    3. Track the message ID to avoid reprocessing
    4. Qwen Code will process the action file automatically
    """

    def __init__(self, vault_path: str, credentials_path: str = None, 
                 check_interval: int = 120, dry_run: bool = False,
                 max_results: int = 50):
        """
        Initialize the Gmail Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to Gmail OAuth2 credentials.json
            check_interval: Seconds between checks (default: 120)
            dry_run: If True, log actions but don't create files
            max_results: Maximum emails to fetch per check
        """
        super().__init__(vault_path, check_interval=check_interval)

        # Credentials path - look in project root
        if credentials_path:
            self.credentials_path = Path(credentials_path)
        else:
            # Search for credentials.json in common locations
            self.credentials_path = self._find_credentials_file()
        
        self.token_path = Path(__file__).parent.parent / 'token.json'
        self.dry_run = dry_run
        self.max_results = max_results

        # Gmail service
        self.service = None

        # Initialize Gmail service
        self._authenticate()

        self.logger.info(f"Gmail Watcher initialized")
        self.logger.info(f"Credentials: {self.credentials_path}")
        self.logger.info(f"Token: {self.token_path}")
        if self.dry_run:
            self.logger.warning("DRY RUN MODE - No action files will be created")

    def _find_credentials_file(self) -> Path:
        """Search for credentials.json in common locations."""
        possible_paths = [
            Path(__file__).parent.parent / 'credentials.json',
            Path(__file__).parent / 'credentials.json',
            Path.cwd() / 'credentials.json',
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Default to project root
        return Path(__file__).parent.parent / 'credentials.json'

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        try:
            creds = None

            # Load token if exists
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    self.token_path, SCOPES
                )
                self.logger.info("Loaded existing OAuth token")

            # Refresh or re-authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired token...")
                    try:
                        creds.refresh(Request())
                        self.logger.info("Token refreshed successfully")
                    except Exception as e:
                        self.logger.warning(f"Token refresh failed: {e}")
                        creds = None
                
                if not creds:
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
                    self.logger.info("OAuth2 authentication successful")

                # Save token for future runs
                self.token_path.write_text(creds.to_json())
                self.logger.info(f"Token saved to: {self.token_path}")

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            self.logger.info(f"Gmail API authenticated: {profile['emailAddress']}")

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
            # Search for unread messages
            # Query: is:unread - newer_than:1d (unread from last 24 hours)
            query = 'is:unread'
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=self.max_results
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
                        self.logger.info(f"New email: {email_data['subject'][:60]}...")

                except HttpError as e:
                    self.logger.error(f"Error fetching message {msg_id}: {e}")
                    if e.resp.status == 404:
                        # Message deleted, skip
                        continue

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
            headers = {h['name'].lower(): h['value'] for h in payload.get('headers', [])}

            # Extract basic info
            from_email = headers.get('from', 'Unknown')
            to_email = headers.get('to', '')
            subject = headers.get('subject', 'No Subject')
            date = headers.get('date', '')
            message_id = msg['id']
            
            # Get thread ID for conversation tracking
            thread_id = msg.get('threadId', '')

            # Extract body
            body = self._extract_body(payload)

            # Extract attachments info
            attachments = self._get_attachments_info(payload)

            # Determine priority based on keywords
            priority = self._determine_priority(subject, body)

            # Detect email type
            email_type = self._detect_email_type(subject, body, from_email)

            return {
                'type': 'email',
                'message_id': message_id,
                'thread_id': thread_id,
                'from': from_email,
                'to': to_email,
                'subject': subject,
                'date': date,
                'received': datetime.now().isoformat(),
                'priority': priority,
                'body': body,
                'attachments': attachments,
                'snippet': msg.get('snippet', ''),
                'email_type': email_type
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
                    if body:
                        break
                elif mime_type == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    body = self._decode_part(part)
        else:
            # Single part message
            body = self._decode_part(payload)

        # Clean up body text
        if body:
            # Remove excessive whitespace
            lines = [line.strip() for line in body.split('\n') if line.strip()]
            body = '\n'.join(lines[:100])  # Limit to 100 lines

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

        # Medium priority: invoice/contract/client related
        if any(kw in text for kw in INVOICE_KEYWORDS + CONTRACT_KEYWORDS + CLIENT_KEYWORDS):
            return 'medium'

        return 'low'

    def _detect_email_type(self, subject: str, body: str, from_email: str) -> str:
        """
        Detect the type of email for better categorization.

        Args:
            subject: Email subject
            body: Email body
            from_email: Sender email

        Returns:
            Email type string
        """
        text = f"{subject} {body}".lower()

        if any(kw in text for kw in INVOICE_KEYWORDS):
            return 'invoice_request'
        elif any(kw in text for kw in ['reply', 're:', 'fwd:', 'forward']):
            return 'reply'
        elif any(kw in text for kw in ['meeting', 'schedule', 'calendar', 'zoom']):
            return 'meeting_request'
        elif any(kw in text for kw in ['welcome', 'subscribe', 'newsletter']):
            return 'newsletter'
        elif any(kw in text for kw in ['verify', 'confirm', 'code', 'otp']):
            return 'verification'
        elif any(kw in text for kw in CONTRACT_KEYWORDS):
            return 'business'
        elif any(kw in text for kw in CLIENT_KEYWORDS):
            return 'client_communication'
        
        return 'general'

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
        safe_subject = self._sanitize_filename(item['subject'][:50])
        filename = f"EMAIL_{safe_subject}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Generate suggested actions based on email type
        suggested_actions = self._get_suggested_actions(item)

        # Format attachments
        attachments_text = self._format_attachments(item['attachments'])

        # Format email content
        content = f"""---
type: {item['type']}
from: {item['from']}
to: {item['to']}
subject: {item['subject']}
received: {item['received']}
date: {item['date']}
priority: {item['priority']}
status: pending
message_id: {item['message_id']}
thread_id: {item['thread_id']}
email_type: {item['email_type']}
---

# Email: {item['subject']}

## Sender Information
- **From:** {item['from']}
- **To:** {item['to']}
- **Date:** {item['date']}
- **Priority:** {item['priority'].upper()}

## Email Content
{item['body']}

## Attachments
{attachments_text}

## Suggested Actions
{suggested_actions}

## Notes for Qwen Code
<!-- Qwen Code will process this email and update the plan -->
<!-- Refer to Company_Handbook.md for communication rules -->

---
*Created by Gmail Watcher (Silver Tier)*
*Message ID: {item['message_id']}*
"""

        if not self.dry_run:
            filepath.write_text(content, encoding='utf-8')
            self.processed_ids.add(item['message_id'])
            self._save_processed_ids()
            self.logger.info(f"Created action file: {filepath.name}")
        else:
            self.logger.info(f"[DRY RUN] Would create: {filepath.name}")
            self.logger.info(f"  Subject: {item['subject']}")
            self.logger.info(f"  From: {item['from']}")
            self.logger.info(f"  Priority: {item['priority']}")

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
        email_type = item.get('email_type', 'general')
        text = f"{item['subject']} {item['body']}".lower()

        # Invoice/payment related
        if email_type == 'invoice_request' or any(kw in text for kw in INVOICE_KEYWORDS):
            actions.extend([
                "- [ ] Extract invoice details (amount, due date, vendor)",
                "- [ ] Log in accounting tracker (/Accounting folder)",
                "- [ ] Generate invoice if requested",
                "- [ ] Schedule payment if approved (requires HITL for >$100)",
            ])

        # Meeting request
        elif email_type == 'meeting_request' or any(kw in text for kw in ['meeting', 'schedule', 'zoom']):
            actions.extend([
                "- [ ] Check calendar availability",
                "- [ ] Propose meeting times",
                "- [ ] Send calendar invite (requires approval)",
            ])

        # Client communication
        elif email_type == 'client_communication' or any(kw in text for kw in CLIENT_KEYWORDS):
            actions.extend([
                "- [ ] Understand client request",
                "- [ ] Check project status",
                "- [ ] Draft response (requires approval for new contacts)",
            ])

        # Business/Contract
        elif email_type == 'business' or any(kw in text for kw in CONTRACT_KEYWORDS):
            actions.extend([
                "- [ ] Review key terms and dates",
                "- [ ] Extract action items",
                "- [ ] Flag for human review (legal document)",
            ])

        # Verification emails (auto-archive)
        elif email_type == 'verification':
            actions.extend([
                "- [ ] Extract verification code if needed",
                "- [ ] Archive after reading",
            ])

        # Newsletter (auto-archive)
        elif email_type == 'newsletter':
            actions.extend([
                "- [ ] Skim for important updates",
                "- [ ] Archive",
            ])

        # Reply emails
        elif email_type == 'reply':
            actions.extend([
                "- [ ] Review conversation thread",
                "- [ ] Determine if response needed",
                "- [ ] Draft reply if needed",
            ])

        # Default actions
        if not actions:
            actions = [
                "- [ ] Read and understand email content",
                "- [ ] Determine required action",
                "- [ ] Draft response if needed (HITL for new contacts)",
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
            lines.append(f"- 📎 {att['filename']} ({size})")

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
        self.logger.info("Gmail Watcher stopping...")
        super().stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Gmail Watcher - Monitor Gmail for new messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python src/gmail_watcher.py AI_Employee_Vault
    python src/gmail_watcher.py AI_Employee_Vault --interval 60
    python src/gmail_watcher.py AI_Employee_Vault --dry-run

Setup:
    1. Enable Gmail API in Google Cloud Console
    2. Download credentials.json to project root
    3. Run watcher (will open browser for OAuth2 consent)
    4. Token saved for future runs

Workflow:
    1. Watcher polls Gmail every 120 seconds
    2. New unread emails create action files in /Needs_Action
    3. Orchestrator detects action files
    4. Qwen Code processes emails and creates plans
    5. Human approves sensitive actions (HITL)
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
        help='Path to Gmail OAuth2 credentials.json'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without creating action files'
    )
    parser.add_argument(
        '--max-results', '-m',
        type=int,
        default=50,
        help='Maximum emails to fetch per check (default: 50)'
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
        dry_run=args.dry_run,
        max_results=args.max_results
    )

    print()
    print("=" * 60)
    print("📧 Gmail Watcher Started")
    print("=" * 60)
    print(f"   Vault: {vault_path}")
    print(f"   Check Interval: {args.interval}s")
    print(f"   Dry Run: {'Yes' if args.dry_run else 'No'}")
    print(f"   Credentials: {watcher.credentials_path}")
    print()
    print(f"📬 Watching for new unread emails...")
    print(f"   Action files will be created in: {watcher.needs_action}")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    print()

    watcher.run()


if __name__ == "__main__":
    main()
