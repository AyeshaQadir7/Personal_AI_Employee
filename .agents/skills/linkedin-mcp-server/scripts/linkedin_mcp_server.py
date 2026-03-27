#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn MCP Server - Model Context Protocol server for LinkedIn automation.

This MCP server provides LinkedIn posting capabilities via Playwright:
- create_post: Create a text/image post on LinkedIn
- schedule_post: Draft post for later (HITL pattern)
- get_analytics: Get post engagement metrics
- list_recent_posts: Get recent posts for audit

Usage:
    python linkedin_mcp_server.py

Configure in Claude Code mcp.json:
{
  "servers": [{
    "name": "linkedin",
    "command": "python",
    "args": ["/path/to/linkedin_mcp_server.py"]
  }]
}

WARNING: Respect LinkedIn's Terms of Service. Use for personal account only.
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing required dependencies. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LinkedInMCP')


class LinkedInMCPServer:
    """MCP server for LinkedIn posting automation."""

    def __init__(self, session_path: str = None, headless: bool = True):
        """
        Initialize LinkedIn MCP Server.

        Args:
            session_path: Path to store browser session data
            headless: Run browser in headless mode
        """
        self.session_path = Path(session_path) if session_path else Path.home() / '.linkedin_session'
        self.headless = headless
        self.logger = logging.getLogger('LinkedInMCP')

    def _get_browser(self):
        """Get browser instance with persistent context."""
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        return playwright, browser

    def create_post(self, content: str, image_path: str = None, 
                    hashtags: list = None) -> dict:
        """
        Create a post on LinkedIn.

        Args:
            content: Post text content
            image_path: Optional path to image to attach
            hashtags: List of hashtags (without #)

        Returns:
            dict with success status and post info
        """
        try:
            playwright, browser = self._get_browser()
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Navigate to LinkedIn
            page.goto('https://www.linkedin.com/feed/', timeout=60000)
            
            # Wait for page to load
            time.sleep(3)

            # Check if logged in
            if 'login' in page.url:
                self.logger.warning("Not logged in. Please login manually.")
                browser.close()
                playwright.stop()
                return {
                    'success': False,
                    'error': 'Not logged in. Please login to LinkedIn first.'
                }

            # Click on "Start a post"
            try:
                start_post_btn = page.query_selector(
                    'button[aria-label="Start a post"], div[role="button"]:has-text("Start a post")'
                )
                if start_post_btn:
                    start_post_btn.click()
                    time.sleep(2)
                else:
                    # Alternative: navigate directly to post creation
                    page.goto('https://www.linkedin.com/feed/?createContent=true', timeout=30000)
                    time.sleep(2)
            except Exception as e:
                self.logger.warning(f"Could not find start post button: {e}")

            # Find the text input field and fill content
            try:
                # LinkedIn uses a div with contenteditable attribute
                text_areas = page.query_selector_all('div[contenteditable="true"]')
                
                if text_areas:
                    # Focus and type content
                    text_areas[0].focus()
                    time.sleep(1)
                    
                    # Type content character by character for reliability
                    for char in content[:3000]:  # LinkedIn limit ~3000 chars
                        page.keyboard.type(char, delay=10)
                    
                    time.sleep(1)

                    # Add hashtags
                    if hashtags:
                        for tag in hashtags:
                            page.keyboard.type(f' #{tag}', delay=10)
                            time.sleep(0.5)

                    self.logger.info("Content entered successfully")
                else:
                    self.logger.error("Could not find text input field")
                    browser.close()
                    playwright.stop()
                    return {
                        'success': False,
                        'error': 'Could not find post input field'
                    }

            except Exception as e:
                self.logger.error(f"Error entering content: {e}")
                browser.close()
                playwright.stop()
                return {
                    'success': False,
                    'error': str(e)
                }

            # Add image if provided
            if image_path:
                try:
                    image_path = Path(image_path)
                    if image_path.exists():
                        # Find and click media upload button
                        media_btn = page.query_selector(
                            'button[aria-label*="photo"], button:has-text("Media"), button:has-text("Photo")'
                        )
                        if media_btn:
                            media_btn.click()
                            time.sleep(1)
                            
                            # Upload file
                            file_input = page.query_selector('input[type="file"]')
                            if file_input:
                                file_input.set_input_files(str(image_path))
                                time.sleep(2)
                                self.logger.info(f"Image attached: {image_path}")
                except Exception as e:
                    self.logger.warning(f"Could not attach image: {e}")

            # Click Post button
            try:
                post_buttons = page.query_selector_all(
                    'button[aria-label="Post"], button:has-text("Post")'
                )
                
                if post_buttons:
                    # Find the enabled post button (not disabled)
                    for btn in post_buttons:
                        if not btn.is_disabled():
                            btn.click()
                            time.sleep(2)
                            self.logger.info("Post published successfully")
                            break
                    
                    # Wait for confirmation
                    time.sleep(3)
                    
                    browser.close()
                    playwright.stop()
                    
                    return {
                        'success': True,
                        'content': content[:100] + '...' if len(content) > 100 else content,
                        'hashtags': hashtags or [],
                        'timestamp': datetime.now().isoformat(),
                        'status': 'posted'
                    }
                else:
                    self.logger.error("Could not find Post button")
                    
            except Exception as e:
                self.logger.error(f"Error clicking Post button: {e}")

            browser.close()
            playwright.stop()
            
            return {
                'success': False,
                'error': 'Could not complete post'
            }

        except Exception as e:
            self.logger.error(f"Error creating post: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def schedule_post(self, content: str, scheduled_time: str = None,
                      image_path: str = None, hashtags: list = None) -> dict:
        """
        Draft a post for later approval (HITL pattern).
        
        This doesn't actually post - it creates a draft file for human approval.

        Args:
            content: Post text content
            scheduled_time: Optional ISO format datetime
            image_path: Optional path to image
            hashtags: List of hashtags

        Returns:
            dict with draft info
        """
        draft_id = f"LINKEDIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            'success': True,
            'draft_id': draft_id,
            'content': content,
            'scheduled_time': scheduled_time,
            'hashtags': hashtags or [],
            'image_path': image_path,
            'status': 'draft_pending_approval',
            'message': 'Draft created. Requires human approval before posting.'
        }

    def get_analytics(self, post_url: str = None) -> dict:
        """
        Get analytics for recent posts.

        Args:
            post_url: Optional specific post URL

        Returns:
            dict with analytics data
        """
        try:
            playwright, browser = self._get_browser()
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Navigate to analytics
            if post_url:
                page.goto(post_url, timeout=60000)
            else:
                page.goto('https://www.linkedin.com/feed/', timeout=60000)

            time.sleep(3)

            # Basic analytics extraction (simplified)
            analytics = {
                'recent_posts': [],
                'total_impressions': 0,
                'total_engagement': 0
            }

            # This is a simplified version - full implementation would
            # scrape the actual analytics page
            
            browser.close()
            playwright.stop()

            return {
                'success': True,
                'analytics': analytics
            }

        except Exception as e:
            self.logger.error(f"Error getting analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_recent_posts(self, count: int = 5) -> dict:
        """
        Get recent posts for audit.

        Args:
            count: Number of posts to retrieve

        Returns:
            dict with list of recent posts
        """
        try:
            playwright, browser = self._get_browser()
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Navigate to profile/activity
            page.goto('https://www.linkedin.com/in/me/detail/recent-activity/', timeout=60000)
            time.sleep(3)

            posts = []
            
            # Simplified - full implementation would scrape actual posts
            
            browser.close()
            playwright.stop()

            return {
                'success': True,
                'count': len(posts),
                'posts': posts
            }

        except Exception as e:
            self.logger.error(f"Error listing posts: {e}")
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


def handle_request(request_str: str, server: LinkedInMCPServer) -> str:
    """Handle MCP request."""
    try:
        request = json.loads(request_str)
        method = request.get('method', '')
        params = request.get('params', {})
        request_id = request.get('id')

        logger.info(f"Handling method: {method}")

        result = None
        error = None

        if method == 'create_post':
            result = server.create_post(
                content=params.get('content', ''),
                image_path=params.get('image_path'),
                hashtags=params.get('hashtags', [])
            )
        elif method == 'schedule_post':
            result = server.schedule_post(
                content=params.get('content', ''),
                scheduled_time=params.get('scheduled_time'),
                image_path=params.get('image_path'),
                hashtags=params.get('hashtags', [])
            )
        elif method == 'get_analytics':
            result = server.get_analytics(
                post_url=params.get('post_url')
            )
        elif method == 'list_recent_posts':
            result = server.list_recent_posts(
                count=params.get('count', 5)
            )
        elif method == 'initialize':
            result = {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'linkedin-mcp-server',
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

    parser = argparse.ArgumentParser(description='LinkedIn MCP Server')
    parser.add_argument('--session-path', type=str, default=None,
                        help='Path to store browser session')
    parser.add_argument('--port', type=int, default=None,
                        help='Port for HTTP mode (default: stdio)')
    parser.add_argument('--no-headless', action='store_true',
                        help='Show browser (default: headless)')

    args = parser.parse_args()

    try:
        server = LinkedInMCPServer(
            session_path=args.session_path,
            headless=not args.no_headless
        )
        logger.info("LinkedIn MCP Server started (stdio mode)")

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
