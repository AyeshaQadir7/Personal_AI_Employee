#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler Setup Script for Windows Task Scheduler.

Creates scheduled tasks for AI Employee operations:
- Daily briefing at 8:00 AM
- Weekly audit on Sunday at 10:00 PM
- Monthly subscription audit on 1st of each month

Usage:
    python scheduler_windows.py setup
    python scheduler_windows.py list
    python scheduler_windows.py remove
"""

import sys
import os
import subprocess
from pathlib import Path


def get_python_path():
    """Get absolute path to Python executable."""
    return sys.executable


def get_script_dir():
    """Get directory containing this script."""
    return Path(__file__).parent.parent.parent.resolve()


def create_daily_briefing_task():
    """Create daily briefing task in Task Scheduler."""
    python_exe = get_python_path()
    script_dir = get_script_dir()
    orchestrator = script_dir / 'src' / 'orchestrator.py'
    vault_path = script_dir / 'AI_Employee_Vault'
    
    # Task Scheduler command
    task_name = "AI_Employee_Daily_Briefing"
    command = f'schtasks /Create /TN "{task_name}" /TR "{python_exe} {orchestrator} {vault_path} --scheduled-task daily_briefing" /SC DAILY /ST 08:00 /RL HIGHEST /F'
    
    print(f"Creating task: {task_name}")
    print(f"Command: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Task created successfully: {task_name}")
    else:
        print(f"✗ Failed to create task: {result.stderr}")
    
    return result.returncode == 0


def create_weekly_audit_task():
    """Create weekly audit task in Task Scheduler."""
    python_exe = get_python_path()
    script_dir = get_script_dir()
    orchestrator = script_dir / 'src' / 'orchestrator.py'
    vault_path = script_dir / 'AI_Employee_Vault'
    
    task_name = "AI_Employee_Weekly_Audit"
    # Sunday at 10:00 PM
    command = f'schtasks /Create /TN "{task_name}" /TR "{python_exe} {orchestrator} {vault_path} --scheduled-task weekly_audit" /SC WEEKLY /D SUN /ST 22:00 /RL HIGHEST /F'
    
    print(f"Creating task: {task_name}")
    print(f"Command: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Task created successfully: {task_name}")
    else:
        print(f"✗ Failed to create task: {result.stderr}")
    
    return result.returncode == 0


def create_monthly_subscription_audit_task():
    """Create monthly subscription audit task."""
    python_exe = get_python_path()
    script_dir = get_script_dir()
    orchestrator = script_dir / 'src' / 'orchestrator.py'
    vault_path = script_dir / 'AI_Employee_Vault'
    
    task_name = "AI_Employee_Monthly_Subscription_Audit"
    # 1st of every month at 9:00 AM
    command = f'schtasks /Create /TN "{task_name}" /TR "{python_exe} {orchestrator} {vault_path} --scheduled-task subscription_audit" /SC MONTHLY /MO 1 /ST 09:00 /RL HIGHEST /F'
    
    print(f"Creating task: {task_name}")
    print(f"Command: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Task created successfully: {task_name}")
    else:
        print(f"✗ Failed to create task: {result.stderr}")
    
    return result.returncode == 0


def list_tasks():
    """List AI Employee scheduled tasks."""
    print("\nAI Employee Scheduled Tasks:\n")
    
    task_names = [
        "AI_Employee_Daily_Briefing",
        "AI_Employee_Weekly_Audit",
        "AI_Employee_Monthly_Subscription_Audit"
    ]
    
    for task_name in task_names:
        command = f'schtasks /Query /TN "{task_name}" /FO TABLE'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ {task_name}")
            print(result.stdout)
        else:
            print(f"✗ {task_name} - Not found")
        print()


def remove_tasks():
    """Remove all AI Employee scheduled tasks."""
    task_names = [
        "AI_Employee_Daily_Briefing",
        "AI_Employee_Weekly_Audit",
        "AI_Employee_Monthly_Subscription_Audit"
    ]
    
    for task_name in task_names:
        command = f'schtasks /Delete /TN "{task_name}" /F'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Task removed: {task_name}")
        else:
            print(f"✗ Failed to remove: {task_name}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scheduler_windows.py <command>")
        print("\nCommands:")
        print("  setup   - Create all scheduled tasks")
        print("  list    - List all scheduled tasks")
        print("  remove  - Remove all scheduled tasks")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'setup':
        print("Setting up AI Employee scheduled tasks...\n")
        create_daily_briefing_task()
        create_weekly_audit_task()
        create_monthly_subscription_audit_task()
        print("\n✓ Setup complete!")
        
    elif command == 'list':
        list_tasks()
        
    elif command == 'remove':
        print("Removing AI Employee scheduled tasks...\n")
        remove_tasks()
        print("\n✓ Removal complete!")
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
