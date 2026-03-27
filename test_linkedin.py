#!/usr/bin/env python3
"""
Quick LinkedIn Poster - Test script for LinkedIn automation.
Run this directly to test LinkedIn posting.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright
import time


def test_linkedin_post():
    """Test posting to LinkedIn."""
    
    post_text = "TEST POST from AI Employee! Automation test at " + time.strftime("%H:%M:%S")
    hashtags = "AI, Automation, Test"
    full_text = f"{post_text} {' '.join(['#' + tag.strip() for tag in hashtags.split(',')])}"
    
    print("=" * 60)
    print("LINKEDIN POST TEST")
    print("=" * 60)
    print(f"Content: {post_text}")
    print(f"Hashtags: {hashtags}")
    print(f"Full: {full_text}")
    print("=" * 60)
    print()
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(Path.home() / '.linkedin_session'),
            headless=False
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        try:
            # Navigate
            print("Navigating to LinkedIn...")
            page.goto('https://www.linkedin.com/feed/', timeout=60000)
            time.sleep(5)
            
            # Click Start a post
            print("Clicking 'Start a post'...")
            page.click('button[aria-label="Start a post"]', timeout=10000)
            time.sleep(3)
            
            # Wait for text area
            print("Waiting for text area...")
            text_area = page.locator('div[contenteditable="true"]').first
            text_area.wait_for(state='visible', timeout=10000)
            
            # Type content
            print("Typing content...")
            text_area.click()
            time.sleep(1)
            text_area.type(full_text, delay=50)
            time.sleep(2)
            
            # CLICK POST BUTTON - using JavaScript to bypass LinkedIn protections
            print("Clicking Post button (JavaScript)...")
            
            # Remove overlays
            page.evaluate("""
                () => {
                    const interop = document.querySelector('#interop-outlet');
                    if (interop) interop.remove();
                }
            """)
            
            # Find and click Post button via JavaScript
            result = page.evaluate("""
                () => {
                    const btn = document.querySelector('button[aria-label="Post"]');
                    if (btn && !btn.disabled) {
                        btn.click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if result:
                print("✓ Post button clicked via JavaScript!")
            else:
                print("✗ Post button not found or disabled")
                print("MANUALLY CLICK POST IN THE BROWSER!")
            
            # Wait and check
            time.sleep(5)
            print("✓ Check your LinkedIn profile for the post!")
            
        except Exception as e:
            print(f"ERROR: {e}")
            print("Browser is open - you can complete manually!")
            time.sleep(10)
        
        finally:
            print("Closing browser...")
            browser.close()


if __name__ == "__main__":
    test_linkedin_post()
