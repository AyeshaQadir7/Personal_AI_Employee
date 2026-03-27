#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhatsApp Watcher - Monitors WhatsApp Web for new messages with urgent keywords.

This is a Silver Tier watcher that uses Playwright to automate WhatsApp Web
and detect messages requiring immediate attention.

Usage:
    python whatsapp_watcher.py /path/to/obsidian/vault

Prerequisites:
    pip install playwright
    playwright install chromium

WARNING: Respect WhatsApp's Terms of Service. Use for personal/business
automation only, not for spam or bulk messaging.
"""

import sys
import argparse
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing required dependencies. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

from src.base_watcher import BaseWatcher


# Keywords for priority detection
HIGH_PRIORITY_KEYWORDS = ['urgent', 'asap', 'emergency', 'invoice', 'payment', 'bill']
MEDIUM_PRIORITY_KEYWORDS = ['help', 'support', 'question', 'issue']
LOW_PRIORITY_KEYWORDS = ['thanks', 'ok', 'sure', 'yes', 'no']


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new messages containing urgent keywords.

    When a matching message is detected:
    1. Extract message content and sender info
    2. Create a .md action file in Needs_Action
    3. Track the message to avoid reprocessing
    """

    def __init__(self, vault_path: str, session_path: str = None,
                 check_interval: int = 30, dry_run: bool = False, login: bool = False):
        """
        Initialize the WhatsApp Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 30)
            dry_run: If True, log actions but don't create files
            login: If True, show browser for QR code login
        """
        super().__init__(vault_path, check_interval=check_interval)

        # Session path
        self.session_path = Path(session_path) if session_path else Path.home() / '.whatsapp_session'
        self.dry_run = dry_run
        self.login_mode = login

        # Keywords
        self.keywords = HIGH_PRIORITY_KEYWORDS + MEDIUM_PRIORITY_KEYWORDS

        # Track processed messages
        self.processed_messages: set = set()

        # Load previously processed IDs
        self._load_processed_ids()

        self.logger.info(f"Watching WhatsApp Web: {self.session_path}")
        if self.dry_run:
            self.logger.warning("DRY RUN MODE - No action files will be created")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new unread messages with keywords.

        Returns:
            List of dictionaries containing message data
        """
        new_messages = []

        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=not self.login_mode,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox'
                    ]
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to WhatsApp Web
                try:
                    page.goto('https://web.whatsapp.com', timeout=60000)
                    
                    # Wait for chat list to load
                    try:
                        page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                        self.logger.info("WhatsApp Web loaded successfully")
                    except PlaywrightTimeout:
                        # Check if we need to show QR code
                        if page.query_selector('[data-testid="qr-code"]'):
                            self.logger.warning("QR code detected - please scan with WhatsApp")
                            if not self.login_mode:
                                self.logger.info("Run with --login flag to scan QR code")
                                browser.close()
                                return []
                            # Wait for login
                            page.wait_for_selector('[data-testid="chat-list"]', timeout=120000)
                    
                    # Small delay for content to load
                    time.sleep(2)

                    # Find unread chats
                    unread_chats = self._get_unread_chats(page)
                    
                    for chat in unread_chats:
                        try:
                            message_data = self._extract_message_data(page, chat)
                            
                            if message_data:
                                # Check for keywords
                                if self._contains_keywords(message_data['text']):
                                    new_messages.append(message_data)
                                    self.logger.info(
                                        f"New message from {message_data['sender']}: "
                                        f"{message_data['text'][:50]}..."
                                    )
                        except Exception as e:
                            self.logger.warning(f"Error extracting message: {e}")
                            continue

                except Exception as e:
                    self.logger.error(f"Error loading WhatsApp Web: {e}")
                
                finally:
                    browser.close()

        except Exception as e:
            self.logger.error(f"Playwright error: {e}")

        return new_messages

    def _get_unread_chats(self, page) -> List:
        """
        Get list of unread chats from the chat list.

        Args:
            page: Playwright page object

        Returns:
            List of chat element handles
        """
        try:
            # Look for chats with unread indicator
            # WhatsApp uses various selectors for unread messages
            unread_selectors = [
                '[aria-label*="unread"]',
                '[data-testid="chat-list"] span:has-text("@")',
                'div[role="row"][aria-label*="unread"]',
            ]

            unread_chats = []
            for selector in unread_selectors:
                try:
                    chats = page.query_selector_all(selector)
                    if chats:
                        unread_chats.extend(chats)
                        break
                except:
                    continue

            # If no unread found with specific selectors, get recent chats
            if not unread_chats:
                all_chats = page.query_selector_all('[data-testid="chat-list"] div[role="row"]')
                unread_chats = all_chats[:10]  # Check last 10 chats

            return unread_chats

        except Exception as e:
            self.logger.warning(f"Error getting unread chats: {e}")
            return []

    def _extract_message_data(self, page, chat_element) -> Optional[Dict[str, Any]]:
        """
        Extract message data from a chat element.

        Args:
            page: Playwright page object
            chat_element: Chat element handle

        Returns:
            Dictionary with message data or None
        """
        try:
            # Get sender/name
            sender_elem = chat_element.query_selector('[dir="auto"]')
            sender = sender_elem.inner_text() if sender_elem else "Unknown"

            # Get last message text
            message_elem = chat_element.query_selector('span[dir="auto"]')
            message_text = message_elem.inner_text() if message_elem else ""

            # Get timestamp if available
            time_elem = chat_element.query_selector('span[dir="auto"][title]')
            timestamp = time_elem.get_attribute('title') if time_elem else datetime.now().isoformat()

            # Click on chat to get full context (optional)
            # chat_element.click()
            # time.sleep(1)

            return {
                'type': 'whatsapp',
                'sender': sender,
                'text': message_text,
                'timestamp': timestamp,
                'received': datetime.now().isoformat(),
                'priority': self._determine_priority(message_text),
                'chat_element': chat_element  # Keep reference for reply
            }

        except Exception as e:
            self.logger.warning(f"Error extracting message: {e}")
            return None

    def _contains_keywords(self, text: str) -> bool:
        """Check if text contains any monitored keywords."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.keywords)

    def _determine_priority(self, text: str) -> str:
        """
        Determine message priority based on keywords.

        Args:
            text: Message text

        Returns:
            'high', 'medium', or 'low'
        """
        text_lower = text.lower()

        if any(kw in text_lower for kw in HIGH_PRIORITY_KEYWORDS):
            return 'high'
        elif any(kw in text_lower for kw in MEDIUM_PRIORITY_KEYWORDS):
            return 'medium'
        return 'low'

    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.

        Args:
            item: Dictionary containing message data

        Returns:
            Path to created action file, or None if creation failed
        """
        # Generate unique ID
        item_id = self._generate_id(f"{item['sender']}_{item['timestamp']}")

        # Check if already processed
        if item_id in self.processed_ids:
            self.logger.debug(f"Message already processed: {item_id}")
            return None

        # Create action file
        timestamp = self._get_timestamp()
        filename = f"WHATSAPP_{self._sanitize_filename(item['sender'])}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Generate suggested actions
        suggested_actions = self._get_suggested_actions(item)

        # Extract detected keywords
        detected_keywords = [kw for kw in self.keywords if kw in item['text'].lower()]

        content = f"""---
type: {item['type']}
from: {item['sender']}
received: {item['received']}
priority: {item['priority']}
status: pending
chat_id: {item_id}
---

# WhatsApp Message: {item['sender']}

## Sender
{item['sender']}

## Received
{datetime.fromisoformat(item['received']).strftime('%Y-%m-%d %I:%M %p')}

## Message
{item['text']}

## Detected Keywords
{', '.join(detected_keywords) if detected_keywords else 'None'}

## Suggested Actions
{suggested_actions}

## Notes
<!-- Add any additional context or instructions here -->

---
*Created by WhatsApp Watcher*
"""

        if not self.dry_run:
            filepath.write_text(content, encoding='utf-8')
            self.processed_ids.add(item_id)
            self._save_processed_ids()
            self.logger.info(f"Created action file: {filepath.name}")
        else:
            self.logger.info(f"[DRY RUN] Would create: {filepath.name}")

        return filepath

    def _get_suggested_actions(self, item: Dict[str, Any]) -> str:
        """
        Generate suggested actions based on message content.

        Args:
            item: Message data dictionary

        Returns:
            Markdown formatted list of suggested actions
        """
        actions = []
        text = item['text'].lower()

        # Invoice/payment related
        if any(kw in text for kw in ['invoice', 'payment', 'bill']):
            actions.extend([
                "- [ ] Extract invoice details (amount, due date, vendor)",
                "- [ ] Log in accounting tracker",
                "- [ ] Generate and send invoice",
            ])

        # Urgent/emergency
        elif any(kw in text for kw in ['urgent', 'asap', 'emergency']):
            actions.extend([
                "- [ ] Respond immediately",
                "- [ ] Determine required action",
                "- [ ] Escalate if necessary",
            ])

        # Help/support request
        elif any(kw in text for kw in ['help', 'support', 'question']):
            actions.extend([
                "- [ ] Understand the issue",
                "- [ ] Provide solution or workaround",
                "- [ ] Follow up to ensure resolution",
            ])

        # Default actions
        if not actions:
            actions = [
                "- [ ] Read and understand message",
                "- [ ] Draft response",
                "- [ ] Send reply via WhatsApp",
            ]

        # Always add completion action
        actions.append("- [ ] Move to /Done when complete")

        return '\n'.join(actions)

    def stop(self):
        """Gracefully stop the watcher."""
        super().stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='WhatsApp Watcher - Monitor WhatsApp Web for urgent messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python whatsapp_watcher.py /path/to/vault
    python whatsapp_watcher.py /path/to/vault --interval 60
    python whatsapp_watcher.py /path/to/vault --login

Setup:
    1. Install: pip install playwright && playwright install chromium
    2. First run with --login to scan QR code
    3. Session saved for future runs

WARNING: Respect WhatsApp's Terms of Service.
        """
    )

    parser.add_argument(
        'vault_path',
        help='Path to the Obsidian vault root'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--session-path', '-s',
        type=str,
        default=None,
        help='Path to store browser session (default: ~/.whatsapp_session)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without creating action files'
    )
    parser.add_argument(
        '--login',
        action='store_true',
        help='Show browser for QR code login'
    )

    args = parser.parse_args()

    # Validate vault path
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Create and run watcher
    watcher = WhatsAppWatcher(
        vault_path=str(vault_path),
        session_path=args.session_path,
        check_interval=args.interval,
        dry_run=args.dry_run,
        login=args.login
    )

    print(f"\n💬 WhatsApp Watcher Started")
    print(f"   Vault: {vault_path}")
    print(f"   Check Interval: {args.interval}s")
    print(f"   Session: {watcher.session_path}")
    print(f"   Dry Run: {'Yes' if args.dry_run else 'No'}")
    if args.login:
        print(f"\n📱 SCAN QR CODE with WhatsApp mobile app")
    print(f"\n💬 Watching for urgent WhatsApp messages...")
    print(f"   Press Ctrl+C to stop\n")

    watcher.run()


if __name__ == "__main__":
    main()
