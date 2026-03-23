#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filesystem Watcher - Monitors the vault's /Inbox folder for new files.

This is the Bronze Tier watcher - a simple, reliable way to trigger
AI Employee actions by dropping files into the Inbox folder.

Usage:
    python filesystem_watcher.py /path/to/obsidian/vault

Drop files into: /path/to/obsidian/vault/Inbox/
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from base_watcher import BaseWatcher


class FilesystemWatcher(BaseWatcher):
    """
    Watches the vault's /Inbox folder for new files and creates action files.

    When a file is detected:
    1. File is already in /Inbox (user drops it there)
    2. Create a corresponding .md action file in Needs_Action
    3. Track the file to avoid reprocessing
    """

    def __init__(self, vault_path: str, check_interval: int = 5):
        """
        Initialize the Filesystem Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 5 for responsive file drops)
        """
        super().__init__(vault_path, check_interval=check_interval)

        # The drop folder IS the Inbox folder inside the vault
        self.drop_folder = self.inbox

        # Track file modification times
        self.file_mtimes: Dict[str, float] = {}

        # Initialize mtimes for existing files
        self._scan_existing_files()

        self.logger.info(f"Watching Inbox: {self.drop_folder}")

    def _scan_existing_files(self):
        """Scan and record modification times for existing files."""
        try:
            for file in self.drop_folder.iterdir():
                if file.is_file():
                    self.file_mtimes[str(file)] = file.stat().st_mtime
            self.logger.info(f"Found {len(self.file_mtimes)} existing file(s) in drop folder")
        except Exception as e:
            self.logger.warning(f"Could not scan drop folder: {e}")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new or modified files in the drop folder.

        Returns:
            List of dictionaries containing file information
        """
        new_items = []

        try:
            for file in self.drop_folder.iterdir():
                if not file.is_file():
                    continue

                file_path = str(file)
                current_mtime = file.stat().st_mtime

                # Check if this is a new file or has been modified
                if file_path not in self.file_mtimes:
                    # New file detected
                    self.logger.info(f"New file detected: {file.name}")
                    new_items.append({
                        'type': 'file_drop',
                        'source_path': file_path,
                        'name': file.name,
                        'size': file.stat().st_size,
                        'modified': datetime.fromtimestamp(current_mtime).isoformat(),
                        'content': self._read_file_content(file)
                    })
                    self.file_mtimes[file_path] = current_mtime

                elif current_mtime > self.file_mtimes[file_path]:
                    # File was modified
                    self.logger.info(f"Modified file detected: {file.name}")
                    new_items.append({
                        'type': 'file_modified',
                        'source_path': file_path,
                        'name': file.name,
                        'size': file.stat().st_size,
                        'modified': datetime.fromtimestamp(current_mtime).isoformat(),
                        'content': self._read_file_content(file)
                    })
                    self.file_mtimes[file_path] = current_mtime

        except Exception as e:
            self.logger.error(f"Error scanning drop folder: {e}")

        return new_items

    def _read_file_content(self, file: Path) -> str:
        """
        Read file content, handling various encodings.

        Args:
            file: Path to the file

        Returns:
            File content as string, or error message if unreadable
        """
        encodings = ['utf-8', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                return file.read_text(encoding=encoding)
            except (UnicodeDecodeError, Exception):
                continue

        # If text reading fails, return file info
        return f"[Binary file: {file.suffix}]"

    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.

        The original file is already in /Inbox - no need to copy.

        Args:
            item: Dictionary containing file information

        Returns:
            Path to created action file, or None if creation failed
        """
        # Generate unique ID
        item_id = self._generate_id(item['source_path'])

        # Check if already processed
        if item_id in self.processed_ids:
            self.logger.debug(f"Item already processed: {item_id}")
            return None

        # File is already in Inbox - no copy needed
        inbox_copy = self.inbox / item['name']

        # Create action file
        timestamp = self._get_timestamp()
        filename = f"FILE_{self._sanitize_filename(item['name'])}_{timestamp}.md"
        filepath = self.needs_action / filename

        # Determine suggested actions based on file type
        suggested_actions = self._get_suggested_actions(item['name'], item['content'])

        content = f"""---
type: {item['type']}
original_name: {item['name']}
original_path: {item['source_path']}
file_size: {item['size']} bytes
received: {datetime.now().isoformat()}
modified: {item['modified']}
status: pending
priority: normal
---

# File Drop: {item['name']}

## File Information
- **Type:** {Path(item['name']).suffix.upper()}
- **Size:** {self._format_size(item['size'])}
- **Modified:** {item['modified']}
- **Source:** `/Inbox/{item['name']}`

## Content Preview
```
{self._truncate(item['content'], 2000)}
```

## Suggested Actions
{suggested_actions}

## Notes
<!-- Add any additional context or instructions here -->

---
*Created by Filesystem Watcher*
"""

        filepath.write_text(content, encoding='utf-8')
        self.processed_ids.add(item_id)

        return filepath

    def _get_suggested_actions(self, filename: str, content: str) -> str:
        """
        Generate suggested actions based on file type and content.

        Args:
            filename: Name of the file
            content: File content

        Returns:
            Markdown formatted list of suggested actions
        """
        actions = []
        filename_lower = filename.lower()

        # Invoice-related
        if 'invoice' in filename_lower or 'invoice' in content.lower():
            actions.extend([
                "- [ ] Extract invoice details (amount, due date, vendor)",
                "- [ ] Log in accounting tracker",
                "- [ ] Schedule payment if approved",
            ])

        # Receipt-related
        elif 'receipt' in filename_lower or 'receipt' in content.lower():
            actions.extend([
                "- [ ] Categorize expense",
                "- [ ] Log for tax purposes",
                "- [ ] Attach to relevant project/client",
            ])

        # Document/contract
        elif any(term in filename_lower for term in ['contract', 'agreement', 'proposal']):
            actions.extend([
                "- [ ] Review key terms and dates",
                "- [ ] Extract action items",
                "- [ ] Schedule follow-up if needed",
            ])

        # Task list
        elif any(term in filename_lower for term in ['task', 'todo', 'checklist']):
            actions.extend([
                "- [ ] Parse individual tasks",
                "- [ ] Add to task tracker",
                "- [ ] Set priorities and deadlines",
            ])

        # Default actions
        if not actions:
            actions = [
                "- [ ] Review file content",
                "- [ ] Determine required action",
                "- [ ] Execute or delegate",
            ]

        # Always add completion action
        actions.append("- [ ] Move to /Done when complete")

        return '\n'.join(actions)

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 50] + "\n\n... [content truncated]"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Filesystem Watcher - Monitor vault Inbox for new files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python filesystem_watcher.py /path/to/vault
    python filesystem_watcher.py /path/to/vault --interval 10

Usage:
    1. Start the watcher: python filesystem_watcher.py AI_Employee_Vault
    2. Drop files into: AI_Employee_Vault/Inbox/
    3. Watcher creates action files in /Needs_Action
    4. Orchestrator processes them automatically
        """
    )

    parser.add_argument(
        'vault_path',
        help='Path to the Obsidian vault root'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=5,
        help='Check interval in seconds (default: 5)'
    )

    args = parser.parse_args()

    # Validate vault path
    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Create and run watcher
    watcher = FilesystemWatcher(
        vault_path=str(vault_path),
        check_interval=args.interval
    )

    print(f"\n📁 Filesystem Watcher Started")
    print(f"   Vault: {vault_path}")
    print(f"   Inbox: {watcher.drop_folder}")
    print(f"   Check Interval: {args.interval}s")
    print(f"\n💡 Drop files into: {watcher.drop_folder}")
    print(f"   Press Ctrl+C to stop\n")

    watcher.run()


if __name__ == "__main__":
    main()
