#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Master process for AI Employee.

The Orchestrator:
1. Monitors /Needs_Action folder for new items
2. Triggers Qwen Code to process items
3. Manages task state and movement between folders
4. Updates Dashboard.md with activity
5. Handles scheduled tasks (daily briefings, weekly audits)

Usage:
    python orchestrator.py /path/to/obsidian/vault

With Qwen Code integration:
    python orchestrator.py /path/to/obsidian/vault --qwen
"""

import sys
import argparse
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import re

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')


class Orchestrator:
    """
    Master orchestrator for AI Employee operations.

    Coordinates between watchers, Qwen Code, and the Obsidian vault.
    """

    def __init__(self, vault_path: str, check_interval: int = 30, qwen_enabled: bool = True):
        """
        Initialize the Orchestrator.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between orchestration cycles
            qwen_enabled: Whether to trigger Qwen Code processing
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.qwen_enabled = qwen_enabled

        # Folder references
        self.needs_action = self.vault_path / 'Needs_Action'
        self.in_progress = self.vault_path / 'In_Progress'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.logs_dir = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'

        # Ensure directories exist
        for folder in [self.needs_action, self.in_progress, self.pending_approval,
                       self.approved, self.rejected, self.done, self.plans, self.logs_dir]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Activity tracking
        self.activity_log: List[Dict[str, Any]] = []
        self.last_dashboard_update = datetime.now()

        self.logger.info(f"Orchestrator initialized")
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Qwen integration: {'enabled' if self.qwen_enabled else 'disabled'}")

    def _setup_logging(self):
        """Configure logging."""
        log_file = self.logs_dir / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Orchestrator')

    def run(self):
        """Main orchestration loop."""
        self.logger.info("Starting Orchestrator")
        self._log_activity("Orchestrator started")

        try:
            while True:
                try:
                    # Process needs_action folder
                    self._process_needs_action()

                    # Process approved folder
                    self._process_approved()

                    # Update dashboard periodically
                    if (datetime.now() - self.last_dashboard_update).total_seconds() > 300:
                        self._update_dashboard()
                        self.last_dashboard_update = datetime.now()

                except Exception as e:
                    self.logger.error(f"Error in orchestration cycle: {e}")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Orchestrator stopped by user")
        finally:
            self._log_activity("Orchestrator stopped")
            self._update_dashboard()

    def _process_needs_action(self):
        """Process items in /Needs_Action folder."""
        # Get all .md files in Needs_Action
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
        """
        Process a single action file.

        Args:
            action_file: Path to the action file
        """
        self.logger.info(f"Processing: {action_file.name}")

        # Read the file
        content = self._read_file_safe(action_file)

        # Extract metadata
        metadata = self._parse_frontmatter(content)
        file_type = metadata.get('type', 'unknown')
        status = metadata.get('status', 'pending')

        if status == 'completed':
            self.logger.debug(f"File already completed: {action_file.name}")
            return

        # Move to In_Progress
        in_progress_file = self.in_progress / action_file.name
        action_file.rename(in_progress_file)

        # Create a plan file
        plan_file = self._create_plan(in_progress_file, metadata)

        # Log activity
        self._log_activity(f"Started processing: {action_file.name} (type: {file_type})")

        # Trigger Qwen Code if enabled
        if self.qwen_enabled:
            self._trigger_qwen(in_progress_file, plan_file)
        else:
            self.logger.info("Qwen integration disabled - manual processing required")
            # For Bronze tier without Qwen, just mark as ready for human review
            self._update_file_status(in_progress_file, 'ready_for_review')

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown content."""
        metadata = {}

        # Simple frontmatter parsing
        if content.startswith('---'):
            lines = content.split('\n')
            in_frontmatter = False
            for line in lines[1:]:
                if line.strip() == '---':
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

        return metadata

    def _create_plan(self, action_file: Path, metadata: Dict[str, Any]) -> Path:
        """
        Create a plan file for the action.

        Args:
            action_file: Path to the action file
            metadata: File metadata

        Returns:
            Path to created plan file
        """
        plan_name = f"PLAN_{action_file.stem}.md"
        plan_file = self.plans / plan_name

        content = f"""---
created: {datetime.now().isoformat()}
status: pending
action_file: {action_file.name}
type: {metadata.get('type', 'unknown')}
---

# Plan: {metadata.get('original_name', action_file.stem)}

## Objective
<!-- Define the main goal -->

## Steps
- [ ] Review input file
- [ ] Identify required actions
- [ ] Execute actions
- [ ] Verify completion
- [ ] Move to /Done

## Notes
<!-- Add observations and decisions here -->

---
*Created by Orchestrator*
"""

        self._write_file_safe(plan_file, content)
        return plan_file

    def _trigger_qwen(self, action_file: Path, plan_file: Path):
        """
        Trigger Qwen Code to process the action.

        Args:
            action_file: Path to the action file
            plan_file: Path to the plan file
        """
        self.logger.info("Triggering Qwen Code...")

        # Create a prompt file for Qwen
        prompt = f"""
Please process the following action file and its associated plan:

**Action File:** `{action_file}`
**Plan File:** `{plan_file}`

**Instructions:**
1. Read both files completely
2. Understand the type of request and required actions
3. Update the plan with specific steps
4. Execute any actions within your capabilities
5. For actions requiring approval, create a file in /Pending_Approval
6. Update the status in both files
7. When complete, move files to appropriate folders

**Company Handbook:** Refer to `{self.vault_path / 'Company_Handbook.md'}` for rules.
**Business Goals:** Consider `{self.vault_path / 'Business_Goals.md'}` for context.

Remember: Always follow the Human-in-the-Loop pattern for sensitive actions.
"""

        prompt_file = self.vault_path / '.qwen_prompt.md'
        self._write_file_safe(prompt_file, prompt)

        self.logger.info(f"Prompt written to: {prompt_file}")
        self.logger.info("To process with Qwen Code, run:")
        self.logger.info(f"  qwen --prompt-file {prompt_file}")

        # Log for Ralph Wiggum loop integration
        self._log_activity(f"Qwen prompt created for: {action_file.name}")

    def _process_approved(self):
        """Process items in /Approved folder (ready for execution)."""
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
        """
        Execute an approved action.

        Args:
            approved_file: Path to the approved file
        """
        self.logger.info(f"Executing approved action: {approved_file.name}")

        # Read the file
        content = self._read_file_safe(approved_file)
        metadata = self._parse_frontmatter(content)

        action_type = metadata.get('action', 'unknown')

        # Log the execution
        self._log_activity(f"Executing: {action_type} ({approved_file.name})")

        # For Bronze tier, we just log and move to Done
        # Higher tiers would integrate with MCP servers here

        # Move to Done
        done_file = self.done / approved_file.name
        approved_file.rename(done_file)

        # Update status
        self._update_file_status(done_file, 'completed')

        self._log_activity(f"Completed: {action_type}")

    def _update_file_status(self, file_path: Path, status: str):
        """
        Update the status in a file's frontmatter.

        Args:
            file_path: Path to the file
            status: New status value
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Simple status update in frontmatter
            if 'status:' in content:
                content = re.sub(
                    r'status:\s*\w+',
                    f'status: {status}',
                    content,
                    count=1
                )
            else:
                # Add status to frontmatter
                content = content.replace('---\n', f'---\nstatus: {status}\n', count=1)

            file_path.write_text(content, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Could not update status in {file_path.name}: {e}")

    def _read_file_safe(self, file_path: Path) -> str:
        """Read file with UTF-8 encoding and error handling."""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            return file_path.read_text(encoding='latin-1')

    def _write_file_safe(self, file_path: Path, content: str):
        """Write file with UTF-8 encoding."""
        file_path.write_text(content, encoding='utf-8')

    def _update_dashboard(self):
        """Update the Dashboard.md with current status."""
        if not self.dashboard.exists():
            self.logger.warning("Dashboard.md not found")
            return

        try:
            content = self._read_file_safe(self.dashboard)

            # Count items in each folder
            counts = {
                'inbox': len(list((self.vault_path / 'Inbox').glob('*'))),
                'needs_action': len(list(self.needs_action.glob('*.md'))),
                'pending_approval': len(list(self.pending_approval.glob('*.md'))),
                'in_progress': len(list(self.in_progress.glob('*.md'))),
            }

            # Update counts table
            for folder, count in counts.items():
                pattern = rf'(\| `/{folder.replace("_", "_")}` \|) \d+'
                replacement = rf'\1 {count}'
                content = re.sub(pattern, replacement, content)

            # Update timestamp
            content = re.sub(
                r'last_updated: [\w:-]+',
                f'last_updated: {datetime.now().isoformat()}',
                content
            )

            # Add recent activity
            if self.activity_log:
                recent = self.activity_log[-5:]
                activity_rows = '\n'.join([
                    f"| {item['time']} | {item['action']} |"
                    for item in recent
                ])

                # Find and update Recent Activity section
                activity_section = re.search(
                    r'(## ✅ Recent Activity\n\n\| Date \| Action \| Status \|\n\|------\|--------\|--------\|)',
                    content
                )
                if activity_section:
                    end_pos = activity_section.end()
                    # Find the end of the table (next section or empty line)
                    next_section = content.find('\n\n', end_pos)
                    if next_section > end_pos:
                        content = content[:end_pos + 1] + '\n' + activity_rows + content[next_section:]

            self._write_file_safe(self.dashboard, content)
            self.logger.info("Dashboard updated")

        except Exception as e:
            self.logger.error(f"Could not update dashboard: {e}")

    def _log_activity(self, action: str):
        """
        Log an activity entry.

        Args:
            action: Description of the action
        """
        entry = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': action
        }
        self.activity_log.append(entry)

        # Also write to daily log file
        log_entry = f"{entry['time']} - {action}\n"
        log_file = self.logs_dir / f'activity_{datetime.now().strftime("%Y-%m-%d")}.log'

        try:
            with open(log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            self.logger.error(f"Could not write to activity log: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI Employee Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python orchestrator.py /path/to/vault
    python orchestrator.py /path/to/vault --no-qwen
    python orchestrator.py /path/to/vault --interval 60
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
        '--no-qwen',
        action='store_true',
        help='Disable Qwen Code integration'
    )

    args = parser.parse_args()

    # Validate vault path
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Create and run orchestrator
    orchestrator = Orchestrator(
        vault_path=str(vault_path),
        check_interval=args.interval,
        qwen_enabled=not args.no_qwen
    )

    print(f"\n🎵 AI Employee Orchestrator Started")
    print(f"   Vault: {vault_path}")
    print(f"   Check Interval: {args.interval}s")
    print(f"   Qwen Integration: {'Enabled' if not args.no_qwen else 'Disabled'}")
    print(f"\n📁 Monitoring folders:")
    print(f"   - /Needs_Action")
    print(f"   - /Approved")
    print(f"\n💡 Drop files into the vault to trigger processing")
    print(f"   Press Ctrl+C to stop\n")

    orchestrator.run()


if __name__ == "__main__":
    main()
