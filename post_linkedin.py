#!/usr/bin/env python3
"""
LinkedIn Post Executor - Posts approved LinkedIn content.

Usage:
    python post_linkedin.py
"""

from pathlib import Path
from playwright.sync_api import sync_playwright
import time


def post_to_linkedin():
    """Post approved LinkedIn content."""
    
    approved_folder = Path('AI_Employee_Vault/Approved')
    done_folder = Path('AI_Employee_Vault/Done')
    
    # Find approved LinkedIn posts
    post_files = list(approved_folder.glob('LINKEDIN_*.md'))
    
    if not post_files:
        print("No approved LinkedIn posts found!")
        print(f"Check: {approved_folder}")
        return
    
    for post_file in post_files:
        print(f"\n{'='*60}")
        print(f"Processing: {post_file.name}")
        print(f"{'='*60}")
        
        # Read the file
        content = post_file.read_text(encoding='utf-8')
        
        # Extract post content and hashtags
        post_text = ''
        hashtags = ''
        
        if 'content:' in content:
            post_text = content.split('content:')[1].split('hashtags:')[0].strip()
        if 'hashtags:' in content:
            hashtags = content.split('hashtags:')[1].split('\n')[0].strip()
        
        print(f"Content: {post_text[:100]}...")
        print(f"Hashtags: {hashtags}")
        
        # Post to LinkedIn
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(Path.home() / '.linkedin_session'),
                headless=False
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            try:
                # Go to LinkedIn
                print("\nNavigating to LinkedIn...")
                page.goto('https://www.linkedin.com/feed/', timeout=60000)
                time.sleep(3)
                
                # Click Start a post
                print("Clicking 'Start a post'...")
                page.click('button[aria-label="Start a post"]')
                time.sleep(2)
                
                # Type content
                print("Typing content...")
                full_text = post_text + ' ' + ' '.join(['#' + tag.strip() for tag in hashtags.split(',')])
                
                text_areas = page.query_selector_all('div[contenteditable="true"]')
                if text_areas:
                    text_areas[0].focus()
                    time.sleep(1)
                    for char in full_text[:2000]:
                        page.keyboard.type(char, delay=10)
                    time.sleep(1)
                
                # Click Post
                print("Clicking 'Post'...")
                post_buttons = page.query_selector_all('button[aria-label="Post"]')
                for btn in post_buttons:
                    if not btn.is_disabled():
                        btn.click()
                        time.sleep(2)
                        break
                
                print("\n✓ Posted successfully!")
                
                # Move to Done
                post_file.rename(done_folder / post_file.name)
                print(f"✓ Moved to /Done")
                
            except Exception as e:
                print(f"\n✗ Error: {e}")
            
            finally:
                browser.close()
    
    print(f"\n{'='*60}")
    print("Done!")


if __name__ == "__main__":
    post_to_linkedin()
