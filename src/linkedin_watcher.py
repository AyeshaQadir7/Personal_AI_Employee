#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Watcher - Monitors LinkedIn for business opportunities and engagement.

This is a Silver Tier watcher that uses Playwright to automate LinkedIn Web
and detect:
- New connection requests from potential clients
- Messages about business opportunities
- Post engagement (likes, comments) on business content
- Job postings matching skills

Usage:
    python src/linkedin_watcher.py /path/to/obsidian/vault

Prerequisites:
    pip install playwright
    playwright install chromium

WARNING: Respect LinkedIn's Terms of Service. Use for personal account only.
         Do not use for spam, bulk messaging, or automated engagement.

Author: AI Employee Project
Tier: Silver
"""

import sys
import os
import argparse
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    PLAYWRIGHT_AVAILABLE = False
    print("=" * 60)
    print("PLAYWRIGHT IMPORT ERROR")
    print("=" * 60)
    print(f"Error: {e}")
    print()
    print("This is typically caused by Python 3.14 compatibility issues.")
    print()
    print("SOLUTION 1: Install Microsoft Visual C++ Redistributable")
    print("  Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("  Install and restart your terminal")
    print()
    print("SOLUTION 2: Use Python 3.12 or 3.13 (recommended)")
    print("  Playwright has better compatibility with these versions")
    print()
    print("SOLUTION 3: Use LinkedIn MCP Server instead")
    print("  See .agents/skills/linkedin-mcp-server/SKILL.md")
    print("=" * 60)

# Add parent directory to path for base_watcher import
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


# Keywords for business opportunity detection
BUSINESS_KEYWORDS = [
    'hiring', 'freelance', 'contract', 'project', 'opportunity',
    'looking for', 'need help', 'recommend', 'referral',
    'collaboration', 'partnership', 'consulting', 'services'
]

URGENT_KEYWORDS = ['urgent', 'asap', 'immediate', 'deadline', 'rush']

# Keywords to ignore (reduce noise)
IGNORE_KEYWORDS = ['congratulations', 'happy to announce', 'new role', 'started at']


class LinkedInWatcher(BaseWatcher):
    """
    Watches LinkedIn for business opportunities and engagement.

    When a relevant activity is detected:
    1. Extract activity details via Playwright automation
    2. Create a .md action file in Needs_Action folder
    3. Track the activity to avoid reprocessing
    4. Qwen Code will process and suggest responses

    Note: This uses browser automation. Be aware of LinkedIn's ToS.
    """

    def __init__(self, vault_path: str, session_path: str = None,
                 check_interval: int = 300, dry_run: bool = False,
                 login: bool = False, headless: bool = True):
        """
        Initialize the LinkedIn Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 300 = 5 min)
            dry_run: If True, log actions but don't create files
            login: If True, show browser for manual login
            headless: Run browser in headless mode
        """
        super().__init__(vault_path, check_interval=check_interval)

        # Session path for persistent browser context
        if session_path:
            self.session_path = Path(session_path)
        else:
            self.session_path = Path.home() / '.linkedin_session'

        self.dry_run = dry_run
        self.login_mode = login
        self.headless = headless and not login

        # Track processed activity IDs
        self.processed_activities: set = set()

        # Load previously processed IDs
        self._load_processed_ids()

        self.logger.info(f"LinkedIn Watcher initialized")
        self.logger.info(f"Session: {self.session_path}")
        if self.dry_run:
            self.logger.warning("DRY RUN MODE - No action files will be created")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn for new notifications and activities.

        Returns:
            List of dictionaries containing activity data
        """
        new_activities = []

        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to LinkedIn
                try:
                    page.goto('https://www.linkedin.com/', timeout=60000)
                    
                    # Wait for page to load
                    time.sleep(3)

                    # Check if logged in
                    if 'login' in page.url or 'checkpoint' in page.url:
                        self.logger.warning("Not logged in to LinkedIn")
                        if self.login_mode:
                            self.logger.info("Please login manually. Waiting 2 minutes...")
                            time.sleep(120)
                            # Refresh and check again
                            page.reload()
                            time.sleep(3)
                            
                            if 'login' in page.url:
                                self.logger.error("Login not completed. Please run with --login flag.")
                                browser.close()
                                return []
                        else:
                            self.logger.info("Run with --login flag to authenticate")
                            browser.close()
                            return []

                    self.logger.info("LinkedIn loaded successfully")

                    # Check notifications
                    notifications = self._check_notifications(page)
                    new_activities.extend(notifications)

                    # Check messages for business opportunities
                    messages = self._check_messages(page)
                    new_activities.extend(messages)

                    # Check feed for business posts
                    feed_items = self._check_feed(page)
                    new_activities.extend(feed_items)

                except PlaywrightTimeout as e:
                    self.logger.error(f"Page load timeout: {e}")
                except Exception as e:
                    self.logger.error(f"Error navigating LinkedIn: {e}")
                finally:
                    browser.close()

        except Exception as e:
            self.logger.error(f"Playwright error: {e}")

        return new_activities

    def _check_notifications(self, page) -> List[Dict[str, Any]]:
        """
        Check LinkedIn notifications for relevant activity.

        Args:
            page: Playwright page object

        Returns:
            List of notification data
        """
        notifications = []

        try:
            # Navigate to notifications page
            page.goto('https://www.linkedin.com/notifications/', timeout=30000)
            time.sleep(3)

            # Find notification elements
            # LinkedIn uses various selectors - try multiple
            notification_selectors = [
                'div.notification-item',
                'div[id*="notification"]',
                'li.notification-item',
                'div.scaffold-finite-scroll__content > div'
            ]

            notification_elements = []
            for selector in notification_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        notification_elements = elements[:10]  # Limit to 10 most recent
                        break
                except:
                    continue

            # If no specific selector works, try to get any recent activity
            if not notification_elements:
                self.logger.info("Using fallback notification detection")
                # Look for any text containing our keywords
                try:
                    page_content = page.content()
                    # Simple heuristic - check if business keywords appear
                    for keyword in BUSINESS_KEYWORDS:
                        if keyword.lower() in page_content.lower():
                            notifications.append({
                                'type': 'linkedin_notification',
                                'activity_type': 'keyword_mention',
                                'content': f"Business keyword detected: {keyword}",
                                'timestamp': datetime.now().isoformat(),
                                'priority': 'medium',
                                'url': page.url
                            })
                            break
                except:
                    pass

            for elem in notification_elements:
                try:
                    text = elem.inner_text(timeout=5000)
                    
                    # Skip if contains ignore keywords
                    if any(kw in text.lower() for kw in IGNORE_KEYWORDS):
                        continue

                    # Check for business relevance
                    if any(kw in text.lower() for kw in BUSINESS_KEYWORDS):
                        # Generate unique ID
                        activity_id = self._generate_id(text[:100])
                        
                        if activity_id not in self.processed_activities:
                            notifications.append({
                                'type': 'linkedin_notification',
                                'activity_type': 'business_opportunity',
                                'content': text[:500],  # Limit content
                                'timestamp': datetime.now().isoformat(),
                                'priority': 'high' if any(kw in text.lower() for kw in URGENT_KEYWORDS) else 'medium',
                                'activity_id': activity_id
                            })
                            self.logger.info(f"Business notification detected")

                except Exception as e:
                    self.logger.warning(f"Error processing notification: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Error checking notifications: {e}")

        return notifications

    def _check_messages(self, page) -> List[Dict[str, Any]]:
        """
        Check LinkedIn messages for business opportunities.

        Args:
            page: Playwright page object

        Returns:
            List of message data
        """
        messages = []

        try:
            # Navigate to messaging
            page.goto('https://www.linkedin.com/messaging/', timeout=30000)
            time.sleep(3)

            # Look for unread messages with business keywords
            # LinkedIn message selectors
            message_selectors = [
                'div.msg-conversations-container',
                'ul.msg-conversation-list__list',
                'div.conversation-card'
            ]

            message_elements = []
            for selector in message_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        message_elements = elements[:10]
                        break
                except:
                    continue

            for elem in message_elements:
                try:
                    text = elem.inner_text(timeout=5000)
                    
                    # Check for unread indicator and business keywords
                    is_unread = 'unread' in text.lower() or 'aria-label' in str(elem)
                    has_business_keyword = any(kw in text.lower() for kw in BUSINESS_KEYWORDS)

                    if is_unread and has_business_keyword:
                        # Extract sender name if possible
                        sender = "Unknown"
                        try:
                            sender_elem = elem.query_selector('span[dir="auto"]')
                            if sender_elem:
                                sender = sender_elem.inner_text(timeout=2000)
                        except:
                            pass

                        activity_id = self._generate_id(f"message_{sender}_{text[:50]}")
                        
                        if activity_id not in self.processed_activities:
                            messages.append({
                                'type': 'linkedin_message',
                                'activity_type': 'business_message',
                                'sender': sender,
                                'content': text[:500],
                                'timestamp': datetime.now().isoformat(),
                                'priority': 'high',
                                'activity_id': activity_id
                            })
                            self.logger.info(f"Business message from: {sender}")

                except Exception as e:
                    self.logger.warning(f"Error processing message: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Error checking messages: {e}")

        return messages

    def _check_feed(self, page) -> List[Dict[str, Any]]:
        """
        Check LinkedIn feed for business opportunities.

        Args:
            page: Playwright page object

        Returns:
            List of feed item data
        """
        feed_items = []

        try:
            # Navigate to home feed
            page.goto('https://www.linkedin.com/feed/', timeout=30000)
            time.sleep(3)

            # Look for posts with business keywords
            # Scroll to load more content
            for _ in range(2):
                page.evaluate('window.scrollBy(0, 1000)')
                time.sleep(1)

            # Post selectors
            post_selectors = [
                'div.update-components-text',
                'div.feed-shared-update-v2',
                'div.scaffold-update__content'
            ]

            post_elements = []
            for selector in post_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        post_elements = elements[:15]
                        break
                except:
                    continue

            for elem in post_elements:
                try:
                    text = elem.inner_text(timeout=5000)
                    
                    # Check for business opportunities
                    has_opportunity = any(kw in text.lower() for kw in BUSINESS_KEYWORDS)
                    is_ignored = any(kw in text.lower() for kw in IGNORE_KEYWORDS)

                    if has_opportunity and not is_ignored:
                        activity_id = self._generate_id(text[:100])
                        
                        if activity_id not in self.processed_activities:
                            feed_items.append({
                                'type': 'linkedin_post',
                                'activity_type': 'business_opportunity',
                                'content': text[:500],
                                'timestamp': datetime.now().isoformat(),
                                'priority': 'medium',
                                'activity_id': activity_id
                            })

                except Exception as e:
                    self.logger.warning(f"Error processing feed item: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Error checking feed: {e}")

        return feed_items

    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.

        Args:
            item: Dictionary containing activity data

        Returns:
            Path to created action file, or None if creation failed
        """
        # Check if already processed
        activity_id = item.get('activity_id', self._generate_id(item['content']))
        if activity_id in self.processed_ids:
            self.logger.debug(f"Activity already processed: {activity_id}")
            return None

        # Create action file
        timestamp = self._get_timestamp()
        activity_type = item.get('activity_type', 'unknown')
        filename = f"LINKEDIN_{activity_type.upper()}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Generate suggested actions
        suggested_actions = self._get_suggested_actions(item)

        # Format content
        content = f"""---
type: {item['type']}
activity_type: {activity_type}
received: {item['timestamp']}
priority: {item['priority']}
status: pending
linkedin_activity_id: {activity_id}
---

# LinkedIn {activity_type.replace('_', ' ').title()}

## Activity Details
- **Type:** {item['type']}
- **Activity:** {activity_type}
- **Detected:** {datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %I:%M %p')}
- **Priority:** {item['priority'].upper()}

{f"**Sender:** {item.get('sender', 'Unknown')}\n" if item.get('sender') else ""}
## Content
{item['content']}

## Suggested Actions
{suggested_actions}

## Response Draft
<!-- Qwen Code will help draft a response -->
<!-- Remember: Be professional, authentic, and value-focused -->

## Notes
<!-- Add context about this opportunity -->

---
*Created by LinkedIn Watcher (Silver Tier)*
*Activity ID: {activity_id}*
"""

        if not self.dry_run:
            filepath.write_text(content, encoding='utf-8')
            self.processed_ids.add(activity_id)
            self._save_processed_ids()
            self.logger.info(f"Created action file: {filepath.name}")
        else:
            self.logger.info(f"[DRY RUN] Would create: {filepath.name}")
            self.logger.info(f"  Type: {activity_type}")
            self.logger.info(f"  Priority: {item['priority']}")

        return filepath

    def _get_suggested_actions(self, item: Dict[str, Any]) -> str:
        """
        Generate suggested actions based on activity type.

        Args:
            item: Activity data dictionary

        Returns:
            Markdown formatted list of suggested actions
        """
        actions = []
        activity_type = item.get('activity_type', 'unknown')
        content = item.get('content', '').lower()

        # Business opportunity
        if activity_type == 'business_opportunity' or 'hiring' in content or 'freelance' in content:
            actions.extend([
                "- [ ] Review the opportunity details",
                "- [ ] Research the person/company",
                "- [ ] Assess fit with current skills/availability",
                "- [ ] Draft personalized response (requires approval)",
                "- [ ] Check Company_Handbook.md for rate guidelines",
            ])

        # Business message
        elif activity_type == 'business_message':
            actions.extend([
                "- [ ] Read full message thread",
                "- [ ] Understand sender's needs",
                "- [ ] Check if this is a potential client",
                "- [ ] Draft helpful response (HITL for new contacts)",
            ])

        # Connection request with business potential
        elif 'connection' in content:
            actions.extend([
                "- [ ] Review sender's profile",
                "- [ ] Check mutual connections",
                "- [ ] Accept if relevant to business goals",
                "- [ ] Send welcome message (optional)",
            ])

        # Post engagement opportunity
        elif activity_type == 'linkedin_post':
            actions.extend([
                "- [ ] Evaluate post relevance",
                "- [ ] Consider adding thoughtful comment",
                "- [ ] Share if valuable to network (approval required)",
            ])

        # Default actions
        if not actions:
            actions = [
                "- [ ] Review LinkedIn activity",
                "- [ ] Determine business relevance",
                "- [ ] Take appropriate action",
            ]

        # Always add completion action
        actions.append("- [ ] Move to /Done when complete")

        return '\n'.join(actions)

    def stop(self):
        """Gracefully stop the watcher."""
        self.logger.info("LinkedIn Watcher stopping...")
        super().stop()


def main():
    """Main entry point."""
    
    # Check if Playwright is available before proceeding
    if not PLAYWRIGHT_AVAILABLE:
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='LinkedIn Watcher - Monitor LinkedIn for business opportunities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python src/linkedin_watcher.py AI_Employee_Vault
    python src/linkedin_watcher.py AI_Employee_Vault --login
    python src/linkedin_watcher.py AI_Employee_Vault --interval 600

Setup:
    1. Install: pip install playwright && playwright install chromium
    2. First run with --login to authenticate
    3. Session saved for future runs

WARNING: Respect LinkedIn's Terms of Service.
         Use for personal account monitoring only.
         Do not use for spam or bulk automation.
        """
    )

    parser.add_argument(
        'vault_path',
        help='Path to the Obsidian vault root'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300 = 5 min)'
    )
    parser.add_argument(
        '--session-path', '-s',
        type=str,
        default=None,
        help='Path to store browser session'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without creating action files'
    )
    parser.add_argument(
        '--login',
        action='store_true',
        help='Show browser for manual login'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Show browser (default: headless)'
    )

    args = parser.parse_args()

    # Validate vault path
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Create and run watcher
    watcher = LinkedInWatcher(
        vault_path=str(vault_path),
        session_path=args.session_path,
        check_interval=args.interval,
        dry_run=args.dry_run,
        login=args.login,
        headless=not args.no_headless
    )

    print()
    print("=" * 60)
    print("💼 LinkedIn Watcher Started")
    print("=" * 60)
    print(f"   Vault: {vault_path}")
    print(f"   Check Interval: {args.interval}s")
    print(f"   Session: {watcher.session_path}")
    print(f"   Dry Run: {'Yes' if args.dry_run else 'No'}")
    print(f"   Headless: {'Yes' if watcher.headless else 'No'}")
    print()
    if args.login:
        print("📱 LOGIN REQUIRED - Browser will open for authentication")
        print("   1. Login to LinkedIn when browser opens")
        print("   2. Session will be saved for future runs")
        print()
    print("💼 Watching for business opportunities...")
    print(f"   Action files will be created in: {watcher.needs_action}")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    print()

    watcher.run()


if __name__ == "__main__":
    main()
