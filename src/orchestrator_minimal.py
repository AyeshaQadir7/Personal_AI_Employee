#!/usr/bin/env python3
"""
Orchestrator - Minimal version with LinkedIn posting support.
"""

import sys
import argparse
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class Orchestrator:
    def __init__(self, vault_path: str, check_interval: int = 5):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        
        self.needs_action = self.vault_path / 'Needs_Action'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logs_dir = self.vault_path / 'Logs'
        
        for folder in [self.needs_action, self.approved, self.done, self.logs_dir]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        
    def _setup_logging(self):
        log_file = self.logs_dir / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
        )
        self.logger = logging.getLogger('Orchestrator')
    
    def run(self):
        self.logger.info("Starting Orchestrator")
        while True:
            try:
                self._process_approved()
            except Exception as e:
                self.logger.error(f"Error: {e}")
            time.sleep(self.check_interval)
    
    def _process_approved(self):
        approved_files = list(self.approved.glob('*.md'))
        if not approved_files:
            return
        
        self.logger.info(f"Found {len(approved_files)} approved item(s)")
        
        for approved_file in approved_files:
            try:
                self._execute_approved_action(approved_file)
            except Exception as e:
                self.logger.error(f"Error executing {approved_file.name}: {e}")
    
    def _execute_approved_action(self, approved_file: Path):
        self.logger.info(f"Executing: {approved_file.name}")
        
        content = approved_file.read_text(encoding='utf-8')
        metadata = self._parse_frontmatter(content)
        action_type = metadata.get('action', 'unknown')
        
        if action_type == 'linkedin_post':
            self._execute_linkedin_post(approved_file, metadata)
        else:
            self.logger.info(f"Unknown action: {action_type}")
            # Just move to Done
            approved_file.rename(self.done / approved_file.name)
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        metadata = {}
        if content.startswith('---'):
            lines = content.split('\n')
            for line in lines[1:]:
                if line.strip() == '---':
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        return metadata
    
    def _execute_linkedin_post(self, approved_file: Path, metadata: Dict[str, Any]):
        """Post to LinkedIn via Playwright."""
        self.logger.info("Posting to LinkedIn...")
        
        try:
            from playwright.sync_api import sync_playwright
            import time
            from pathlib import Path as P
            
            # Extract content from frontmatter or body
            post_text = metadata.get('content', '')
            hashtags = metadata.get('hashtags', '')
            
            # If not in frontmatter, extract from body
            if not post_text or post_text == '#':
                content = approved_file.read_text(encoding='utf-8')
                if '**Content:**' in content:
                    parts = content.split('**Content:**')
                    if len(parts) > 1:
                        post_text = parts[1].split('**Hashtags:**')[0].strip().replace('>', '').strip()
                if '**Hashtags:**' in content:
                    hashtag_part = content.split('**Hashtags:**')[1].split('\n')[0].strip()
                    hashtags = hashtag_part.replace('#', '').strip()
            
            # Fallback
            if not post_text or post_text == '#':
                post_text = "AI Employee Test Post"
                hashtags = "AI, Test"
            
            full_text = post_text + ' ' + ' '.join(['#' + tag.strip() for tag in hashtags.split(',')])
            self.logger.info(f"Post content: {full_text[:100]}...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(P.home() / '.linkedin_session'),
                    headless=False,
                    args=['--start-maximized']
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                try:
                    # Navigate to LinkedIn
                    self.logger.info("Navigating to LinkedIn login...")
                    page.goto('https://www.linkedin.com/login', timeout=60000)
                    time.sleep(3)
                    
                    # Check if already logged in
                    if 'feed' in page.url or 'linkedin.com/feed' in page.url:
                        self.logger.info("Already logged in!")
                    else:
                        # Check if we're on login page
                        if 'login' in page.url:
                            self.logger.info("=" * 60)
                            self.logger.info("NOT LOGGED IN - PLEASE LOGIN MANUALLY!")
                            self.logger.info("Browser will wait 60 seconds for login...")
                            self.logger.info("=" * 60)
                            
                            # Wait for user to login
                            for i in range(60):
                                if i % 10 == 0:
                                    self.logger.info(f"Login window: {60-i} seconds remaining...")
                                time.sleep(1)
                                
                                # Check if logged in
                                if 'feed' in page.url:
                                    self.logger.info("✓ Login detected!")
                                    break
                            
                            # Final check
                            if 'login' in page.url:
                                self.logger.error("Login not completed. Please login to LinkedIn.")
                                raise Exception("LinkedIn login required")
                    
                    # Navigate to feed
                    self.logger.info("Navigating to feed...")
                    page.goto('https://www.linkedin.com/feed/', timeout=60000)
                    time.sleep(8)  # Wait longer for full page load
                    
                    # Take screenshot to see what's on the page
                    page.screenshot(path='linkedin_before_post.png')
                    self.logger.info("Screenshot saved: linkedin_before_post.png")
                    
                    # Click Start a post - try multiple selectors
                    self.logger.info("Looking for 'Start a post' button...")
                    
                    start_post_clicked = False
                    selectors = [
                        'button[aria-label="Start a post"]',
                        'button:has-text("Start a post")',
                        'div[role="button"]:has-text("Start a post")',
                        'button[data-test-id="start-a-post"]',
                    ]
                    
                    for sel in selectors:
                        try:
                            btn = page.locator(sel).first
                            btn.wait_for(state='visible', timeout=5000)
                            btn.click()
                            self.logger.info(f"✓ Clicked with selector: {sel}")
                            start_post_clicked = True
                            time.sleep(3)
                            break
                        except Exception as e:
                            self.logger.warning(f"Selector {sel} failed: {e}")
                            continue
                    
                    if not start_post_clicked:
                        self.logger.error("Could not find 'Start a post' button!")
                        self.logger.info("CHECK THE SCREENSHOT: linkedin_before_post.png")
                        self.logger.info("BROWSER STAYS OPEN - you can manually click 'Start a post'")
                        time.sleep(60)  # Wait for manual interaction
                    
                    # Wait for text area
                    text_area = page.locator('div[contenteditable="true"]').first
                    text_area.wait_for(state='visible', timeout=10000)
                    text_area.click()
                    time.sleep(1)
                    
                    # Type content
                    text_area.type(full_text, delay=50)
                    time.sleep(2)
                    
                    # Try to click Post button
                    self.logger.info("Attempting to click Post button...")
                    try:
                        post_btn = page.locator('button[aria-label="Post"]').first
                        post_btn.click(timeout=5000)
                        self.logger.info("✓ Post button clicked!")
                    except Exception as e:
                        self.logger.warning(f"Post button click failed: {e}")
                        self.logger.info("BROWSER STAYS OPEN - CLICK POST MANUALLY!")
                        time.sleep(30)
                    
                    time.sleep(3)
                    
                    # Move to Done
                    approved_file.rename(self.done / approved_file.name)
                    self.logger.info("✓ Moved to /Done")
                    
                except Exception as e:
                    self.logger.error(f"LinkedIn error: {e}")
                    raise
                finally:
                    browser.close()
                    
        except Exception as e:
            self.logger.error(f"LinkedIn post failed: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Check interval in seconds')
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault not found: {vault_path}")
        sys.exit(1)
    
    orchestrator = Orchestrator(str(vault_path), check_interval=args.interval)
    orchestrator.run()


if __name__ == "__main__":
    main()
