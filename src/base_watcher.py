#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Watcher - Abstract template for all Watcher scripts.

Watchers are lightweight Python scripts that run continuously in the background,
monitoring various inputs (Gmail, WhatsApp, filesystems, etc.) and creating
actionable files for Claude to process.

All Watchers follow this pattern:
1. Check for new items periodically
2. Create .md files in /Needs_Action folder for each new item
3. Track processed items to avoid duplicates
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib


class BaseWatcher(ABC):
    """Abstract base class for all Watcher implementations."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs_dir = self.vault_path / 'Logs'
        self.check_interval = check_interval

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Track processed items to avoid duplicates
        self.processed_ids: set = set()

        # Load previously processed IDs from disk
        self._load_processed_ids()

    def _setup_logging(self):
        """Configure logging to file and console."""
        log_file = self.logs_dir / f'watcher_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _load_processed_ids(self):
        """Load previously processed item IDs from disk."""
        state_file = self.vault_path / f'.state_{self.__class__.__name__}.txt'
        if state_file.exists():
            try:
                self.processed_ids = set(state_file.read_text(encoding='utf-8').strip().split('\n'))
                self.processed_ids.discard('')  # Remove empty strings
                self.logger.info(f"Loaded {len(self.processed_ids)} previously processed IDs")
            except Exception as e:
                self.logger.warning(f"Could not load state file: {e}")
                self.processed_ids = set()

    def _save_processed_ids(self):
        """Save processed item IDs to disk for persistence."""
        state_file = self.vault_path / f'.state_{self.__class__.__name__}.txt'
        try:
            state_file.write_text('\n'.join(self.processed_ids), encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Could not save state file: {e}")

    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for an item based on its content."""
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # Limit length
        return name[:100]

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new items to process.

        Returns:
            List of dictionaries containing item data
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.

        Args:
            item: Dictionary containing item data

        Returns:
            Path to created file, or None if creation failed
        """
        pass

    def run(self):
        """Main run loop - continuously check for updates and process them."""
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")

        try:
            while True:
                try:
                    # Check for new items
                    items = self.check_for_updates()

                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")

                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                if filepath:
                                    self.logger.info(f"Created action file: {filepath.name}")
                            except Exception as e:
                                self.logger.error(f"Error creating action file: {e}")

                    # Save state periodically
                    self._save_processed_ids()

                except Exception as e:
                    self.logger.error(f"Error in check loop: {e}")

                # Wait before next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Watcher stopped by user")
        finally:
            # Save final state
            self._save_processed_ids()
            self.logger.info(f"{self.__class__.__name__} shutdown complete")

    def stop(self):
        """Gracefully stop the watcher."""
        self._save_processed_ids()
        self.logger.info("Watcher stopping...")


# Example implementation (for reference)
class ExampleWatcher(BaseWatcher):
    """Example watcher implementation for documentation purposes."""

    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=30)
        self.last_check = datetime.now()

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check for new items (example implementation)."""
        # This would be replaced with actual API calls or file monitoring
        items = []

        # Example: Check for new files in a drop folder
        drop_folder = Path("~/DropFolder").expanduser()
        if drop_folder.exists():
            for file in drop_folder.iterdir():
                if file.is_file() and file.stat().st_mtime > self.last_check.timestamp():
                    try:
                        content = file.read_text(encoding='utf-8')
                    except UnicodeDecodeError:
                        content = file.read_text(encoding='latin-1')
                    items.append({
                        'type': 'file_drop',
                        'source': str(file),
                        'name': file.name,
                        'content': content
                    })

        self.last_check = datetime.now()
        return items

    def create_action_file(self, item: Dict[str, Any]) -> Optional[Path]:
        """Create action file for the item."""
        item_id = self._generate_id(item['source'])

        if item_id in self.processed_ids:
            self.logger.debug(f"Item already processed: {item_id}")
            return None

        filename = f"FILE_{self._sanitize_filename(item['name'])}_{self._get_timestamp()}.md"
        filepath = self.needs_action / filename

        content = f"""---
type: {item['type']}
source: {item['source']}
received: {datetime.now().isoformat()}
status: pending
---

# {item['name']}

## Content
{item.get('content', 'No content')}

## Suggested Actions
- [ ] Review content
- [ ] Take necessary action
- [ ] Move to /Done when complete
"""

        filepath.write_text(content, encoding='utf-8')
        self.processed_ids.add(item_id)
        return filepath


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <vault_path>")
        print("Example: python example_watcher.py /path/to/obsidian/vault")
        sys.exit(1)

    vault_path = sys.argv[1]

    # Use the example watcher for testing
    watcher = ExampleWatcher(vault_path)
    watcher.run()
