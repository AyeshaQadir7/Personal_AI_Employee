---
name: scheduler
description: |
  Task scheduler for AI Employee operations. Supports cron-style scheduling
  on Linux/Mac and Task Scheduler on Windows. Use for daily briefings,
  weekly audits, scheduled posts, and recurring tasks.
---

# Scheduler

Task scheduling for AI Employee operations.

## Features

- **Daily Briefing**: 8 AM summary of tasks, finances, and priorities
- **Weekly Audit**: Sunday night business review with CEO briefing
- **Scheduled Posts**: LinkedIn posts at optimal engagement times
- **Recurring Tasks**: Invoice follow-ups, subscription audits, etc.

## Platform Support

| Platform | Scheduler | Setup Script |
|----------|-----------|--------------|
| Windows | Task Scheduler | `scheduler_windows.bat` |
| Linux | cron | `scheduler_linux.sh` |
| macOS | cron/launchd | `scheduler_macos.sh` |

## Quick Setup

### Windows (Task Scheduler)

```bash
# Run setup script
python .agents/skills/scheduler/scripts/scheduler_windows.py setup

# Or manually create task:
# 1. Open Task Scheduler
# 2. Create Basic Task
# 3. Trigger: Daily at 8:00 AM
# 4. Action: Start program
#    - Program: python.exe
#    - Arguments: orchestrator.py AI_Employee_Vault --scheduled-task daily_briefing
#    - Start in: E:\personal_ai_employee
```

### Linux/Mac (cron)

```bash
# Run setup script
bash .agents/skills/scheduler/scripts/scheduler_unix.sh setup

# Or manually add to crontab (crontab -e):
# Daily briefing at 8 AM
0 8 * * * cd /path/to/personal_ai_employee && python orchestrator.py AI_Employee_Vault --scheduled-task daily_briefing

# Weekly audit every Sunday at 10 PM
0 22 * * 0 cd /path/to/personal_ai_employee && python orchestrator.py AI_Employee_Vault --scheduled-task weekly_audit
```

## Scheduled Tasks

### Daily Briefing (8:00 AM)

Generates morning summary:

```markdown
# Daily Briefing - 2026-01-07

## Yesterday's Summary
- Tasks completed: 5
- Emails processed: 12
- Revenue: $1,500

## Today's Priorities
1. Project Alpha deadline (EOD)
2. Client B follow-up
3. Weekly audit prep

## Pending Approvals
- Payment: Client A invoice ($500)
- LinkedIn post: Product announcement

## Action Items
See /Needs_Action folder (3 items)
```

### Weekly Audit (Sunday 10:00 PM)

Generates CEO briefing:

```markdown
# Weekly CEO Briefing

## Week of Jan 1-7, 2026

### Revenue
- This Week: $2,450
- MTD: $4,500 (45% of $10,000 target)
- Trend: On track

### Completed Tasks
- [x] Client A invoice sent and paid
- [x] Project Alpha milestone 2 delivered

### Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Client B proposal | 2 days | 5 days | +3 days |

### Proactive Suggestions
- **Notion**: No team activity in 45 days. Cost: $15/month.
  - [ACTION] Cancel subscription? Move to /Pending_Approval
```

### Subscription Audit (1st of month)

Reviews all subscriptions:

```python
# In orchestrator.py
def monthly_subscription_audit(self):
    subscriptions = self._load_subscriptions()
    
    for sub in subscriptions:
        if sub['last_used'] < (datetime.now() - timedelta(days=30)):
            self._create_approval_request({
                'type': 'subscription_review',
                'name': sub['name'],
                'cost': sub['monthly_cost'],
                'reason': 'No activity in 30 days'
            })
```

## Configuration

Create `scheduler_config.yaml`:

```yaml
# .agents/skills/scheduler/scheduler_config.yaml

schedules:
  daily_briefing:
    enabled: true
    time: "08:00"
    timezone: "America/New_York"
    output: "/Vault/Briefings/daily_briefing.md"
    
  weekly_audit:
    enabled: true
    day: "sunday"
    time: "22:00"
    timezone: "America/New_York"
    output: "/Vault/Briefings/weekly_audit.md"
    
  subscription_audit:
    enabled: true
    day: 1  # First day of month
    time: "09:00"
    timezone: "America/New_York"
    
  invoice_followup:
    enabled: true
    days: ["monday", "wednesday", "friday"]
    time: "14:00"
    timezone: "America/New_York"
```

## Usage

### Trigger Scheduled Task Manually

```bash
# Daily briefing
python orchestrator.py AI_Employee_Vault --scheduled-task daily_briefing

# Weekly audit
python orchestrator.py AI_Employee_Vault --scheduled-task weekly_audit

# List all scheduled tasks
python .agents/skills/scheduler/scripts/scheduler_cli.py list
```

### Python Scheduler (Alternative)

For cross-platform scheduling without cron:

```python
# scheduler_python.py
from apscheduler.schedulers.blocking import BlockingScheduler
from orchestrator import Orchestrator

def daily_briefing():
    orchestrator = Orchestrator("AI_Employee_Vault")
    orchestrator.generate_daily_briefing()

def weekly_audit():
    orchestrator = Orchestrator("AI_Employee_Vault")
    orchestrator.generate_weekly_audit()

scheduler = BlockingScheduler()

# Daily at 8 AM
scheduler.add_job(daily_briefing, 'cron', hour=8, minute=0)

# Sunday at 10 PM
scheduler.add_job(weekly_audit, 'cron', day_of_week='sun', hour=22, minute=0)

scheduler.start()
```

Install: `pip install APScheduler`

## Integration with Orchestrator

The Orchestrator handles scheduled task execution:

```python
# In orchestrator.py
def execute_scheduled_task(self, task_name: str):
    self.logger.info(f"Executing scheduled task: {task_name}")
    
    if task_name == 'daily_briefing':
        self.generate_daily_briefing()
    elif task_name == 'weekly_audit':
        self.generate_weekly_audit()
    elif task_name == 'subscription_audit':
        self.audit_subscriptions()
    
    self._log_activity(f"Scheduled task completed: {task_name}")
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Task not running | Check scheduler service is running |
| Wrong timezone | Update timezone in config |
| Python not found | Use absolute path to python.exe |
| Permission denied | Run scheduler as appropriate user |

## Best Practices

1. **Log everything** - Scheduled tasks should log to /Logs
2. **Handle failures** - Retry logic for transient errors
3. **Notify on completion** - Send briefing via email/WhatsApp
4. **Test manually first** - Run task manually before scheduling
5. **Review regularly** - Audit scheduled tasks monthly
