#!/usr/bin/env python3
"""
Orchestrator - Full workflow with Qwen Code + Email MCP.

Workflow:
1. Gmail Watcher creates action file in /Needs_Action
2. Orchestrator detects → triggers Qwen Code
3. Qwen creates plan.md in /Plans/
4. Qwen creates approval file in /Pending_Approval/
5. User moves to /Approved/
6. Orchestrator detects → calls Email MCP
7. Email sent → file moved to /Done/
"""

import sys
import argparse
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class Orchestrator:
    def __init__(self, vault_path: str, check_interval: int = 10, qwen_enabled: bool = True):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.qwen_enabled = qwen_enabled
        
        self.needs_action = self.vault_path / 'Needs_Action'
        self.in_progress = self.vault_path / 'In_Progress'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.logs_dir = self.vault_path / 'Logs'
        
        for folder in [self.needs_action, self.in_progress, self.pending_approval,
                       self.approved, self.done, self.plans, self.logs_dir]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        self.logger.info(f"Orchestrator started (Qwen: {qwen_enabled})")
        
    def _setup_logging(self):
        log_file = self.logs_dir / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
        )
        self.logger = logging.getLogger('Orchestrator')
    
    def run(self):
        """Main orchestration loop."""
        self.logger.info("Starting main loop")
        while True:
            try:
                self._process_needs_action()
                self._process_approved()
            except Exception as e:
                self.logger.error(f"Error in loop: {e}")
            time.sleep(self.check_interval)
    
    def _process_needs_action(self):
        """Process new action files from Gmail Watcher."""
        action_files = list(self.needs_action.glob('*.md'))
        if not action_files:
            return
        
        self.logger.info(f"Found {len(action_files)} item(s) in /Needs_Action")
        
        for action_file in action_files:
            try:
                self._process_action_file(action_file)
            except Exception as e:
                self.logger.error(f"Error processing {action_file.name}: {e}")
    
    def _process_action_file(self, action_file: Path):
        """Process a single action file with Qwen Code."""
        self.logger.info(f"Processing: {action_file.name}")
        
        # Move to In_Progress
        in_progress_file = self.in_progress / action_file.name
        action_file.rename(in_progress_file)
        
        # Create initial plan
        plan_file = self._create_plan(in_progress_file)
        
        # Trigger Qwen Code
        if self.qwen_enabled:
            self._trigger_qwen(in_progress_file, plan_file)
        else:
            self.logger.info("Qwen disabled - manual processing required")
    
    def _create_plan(self, action_file: Path) -> Path:
        """Create a plan file."""
        plan_name = f"PLAN_{action_file.stem}.md"
        plan_file = self.plans / plan_name
        
        content = f"""---
created: {datetime.now().isoformat()}
status: in_progress
action_file: {action_file.name}
---

# Plan: {action_file.stem}

## Objective
<!-- Qwen Code will fill this in -->

## Steps
- [ ] Review action file
- [ ] Create response draft
- [ ] Create approval request
- [ ] Move to /Done when complete

## Notes
<!-- Qwen Code will add notes here -->
"""
        plan_file.write_text(content, encoding='utf-8')
        self.logger.info(f"Created plan: {plan_name}")
        return plan_file
    
    def _trigger_qwen(self, action_file: Path, plan_file: Path):
        """Trigger Qwen Code to process the action."""
        self.logger.info("Triggering Qwen Code...")
        
        # Create prompt file
        prompt_file = self.vault_path / '.qwen_prompt.md'
        prompt = f"""
# AI Employee Task

Please process this email action item:

**Action File:** `{action_file.absolute()}`
**Plan File:** `{plan_file.absolute()}`

## Instructions

1. **Read** the action file completely
2. **Understand** what type of email this is (invoice request, inquiry, etc.)
3. **Update the Plan** with specific steps
4. **Create a draft response** in the action file
5. **Create an approval request** in `/Pending_Approval/` with:
   - type: approval_request
   - action: send_email
   - to: [recipient]
   - subject: [subject]
   - content: [draft response]
   - status: pending

6. **Do NOT send the email yourself** - wait for human approval

## Company Handbook
Refer to `{self.vault_path / 'Company_Handbook.md'}` for communication rules.

## Business Goals
Consider `{self.vault_path / 'Business_Goals.md'}` for context.
"""
        prompt_file.write_text(prompt, encoding='utf-8')
        
        self.logger.info(f"Created prompt: {prompt_file}")
        self.logger.info("=" * 60)
        self.logger.info("TO PROCESS WITH QWEN CODE:")
        self.logger.info(f"  cd {self.vault_path.absolute()}")
        self.logger.info("  qwen")
        self.logger.info("  Then paste the prompt from .qwen_prompt.md")
        self.logger.info("=" * 60)
    
    def _process_approved(self):
        """Process approved actions."""
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
        """Execute an approved action (send email, post LinkedIn, etc.)."""
        self.logger.info(f"Executing: {approved_file.name}")
        
        content = approved_file.read_text(encoding='utf-8')
        metadata = self._parse_frontmatter(content)
        action_type = metadata.get('action', 'unknown')
        
        self.logger.info(f"Action type: {action_type}")
        
        # Support multiple action type names
        if action_type in ['send_email', 'email_send']:
            self._execute_send_email(approved_file, metadata)
        elif action_type == 'linkedin_post':
            self.logger.info("LinkedIn posting - moving to Done (manual posting required)")
            approved_file.rename(self.done / approved_file.name)
        else:
            self.logger.info(f"Unknown action: {action_type} - moving to Done")
            approved_file.rename(self.done / approved_file.name)
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter."""
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
    
    def _execute_send_email(self, approved_file: Path, metadata: Dict[str, Any]):
        """Send email via Email MCP Server."""
        self.logger.info("Sending email via MCP...")
        
        try:
            # Import the email MCP function
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / '.agents' / 'skills' / 'email-mcp-server' / 'scripts'))
            from email_mcp_simple import send_email
            
            # Extract email details from frontmatter first
            to_email = metadata.get('to', '')
            subject = metadata.get('subject', '')
            email_body = metadata.get('content', '')
            
            # If not in frontmatter, extract from markdown table in file body
            content = approved_file.read_text(encoding='utf-8')
            
            if not to_email:
                # Look for "**To** | email" pattern in table
                import re
                to_match = re.search(r'\|\s*\*\*To\*\*\s*\|\s*([^\|]+)\|', content)
                if to_match:
                    to_email = to_match.group(1).strip()
                    self.logger.info(f"Extracted to_email from table: {to_email}")
            
            if not subject:
                # Look for "**Subject** | subject" pattern
                subject_match = re.search(r'\|\s*\*\*Subject\*\*\s*\|\s*([^\|]+)\|', content)
                if subject_match:
                    subject = subject_match.group(1).strip()
                    self.logger.info(f"Extracted subject from table: {subject}")
            
            if not email_body:
                # Extract from "Draft Response" section
                if '## Draft Response' in content:
                    draft_section = content.split('## Draft Response')[1]
                    # Get content between ``` markers
                    if '```' in draft_section:
                        parts = draft_section.split('```')
                        if len(parts) > 1:
                            email_body = parts[1].strip()
                            self.logger.info(f"Extracted email body from draft section")
            
            # Validate
            if not to_email or not subject:
                self.logger.error(f"Missing email details - to: '{to_email}', subject: '{subject}'")
                self.logger.info("Moving to Done (manual sending required)")
                approved_file.rename(self.done / approved_file.name)
                return
            
            # Send the email!
            self.logger.info(f"Sending to: {to_email}")
            self.logger.info(f"Subject: {subject}")
            result = send_email(to_email, subject, email_body)
            
            if result.get('success'):
                self.logger.info(f"Email sent! Message ID: {result.get('message_id')}")
                approved_file.rename(self.done / approved_file.name)
                self.logger.info("Moved to /Done")
            else:
                self.logger.error(f"Email failed: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"Email MCP error: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--interval', '-i', type=int, default=10, help='Check interval')
    parser.add_argument('--no-qwen', action='store_true', help='Disable Qwen integration')
    args = parser.parse_args()
    
    vault = Path(args.vault_path)
    if not vault.exists():
        print(f"Error: Vault not found: {vault}")
        sys.exit(1)
    
    orch = Orchestrator(str(vault), check_interval=args.interval, qwen_enabled=not args.no_qwen)
    orch.run()


if __name__ == "__main__":
    main()
