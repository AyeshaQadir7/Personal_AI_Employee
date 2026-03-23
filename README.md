# AI Employee - Bronze Tier Setup Guide

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

This guide walks you through setting up the Bronze Tier of your Personal AI Employee.

---

## 📋 Bronze Tier Deliverables

By completing this setup, you will have:

- ✅ Obsidian vault with Dashboard.md and Company_Handbook.md
- ✅ One working Watcher script (Filesystem Watcher)
- ✅ Orchestrator for processing action items
- ✅ Basic folder structure: /Inbox, /Needs_Action, /Done
- ✅ Ralph Wiggum stop hook for autonomous task completion

---

## 🛠️ Prerequisites

| Component | Version | Installation |
|-----------|---------|--------------|
| Python | 3.13+ | [python.org](https://python.org) |
| Obsidian | v1.10.6+ | [obsidian.md](https://obsidian.md) |
| Claude Code | Latest | `npm install -g @anthropic/claude-code` |
| Git | Latest | [git-scm.com](https://git-scm.com) |

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.13+

# Check Claude Code
claude --version

# Check Git
git --version
```

---

## 📁 Project Structure

```
personal_ai_employee/
├── AI_Employee_Vault/          # Obsidian vault (open this in Obsidian)
│   ├── Dashboard.md            # Real-time status dashboard
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Business_Goals.md       # Objectives and metrics
│   ├── Inbox/                  # Raw incoming files
│   ├── Needs_Action/           # Items requiring processing
│   ├── Done/                   # Completed items
│   ├── Plans/                  # Task plans
│   ├── Pending_Approval/       # Awaiting human decision
│   ├── Approved/               # Ready for execution
│   ├── Logs/                   # System logs
│   └── .claude/plugins/        # Ralph Wiggum stop hook
├── src/
│   ├── base_watcher.py         # Base class for all watchers
│   ├── filesystem_watcher.py   # Bronze tier watcher
│   └── orchestrator.py         # Master orchestration process
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Step 1: Open Vault in Obsidian

1. Open Obsidian
2. Click "Open folder as vault"
3. Select: `E:\personal_ai_employee\AI_Employee_Vault`

### Step 2: Review Core Documents

Read these files in Obsidian:
- `Dashboard.md` - Your main interface
- `Company_Handbook.md` - Operating rules
- `Business_Goals.md` - Your objectives

### Step 3: Start the Filesystem Watcher

Open a terminal and run:

```bash
cd E:\personal_ai_employee
python src/filesystem_watcher.py AI_Employee_Vault
```

You should see:
```
📁 Filesystem Watcher Started
   Vault: AI_Employee_Vault
   Inbox: AI_Employee_Vault\Inbox
   Check Interval: 5s

💡 Drop files into: AI_Employee_Vault\Inbox
   Press Ctrl+C to stop
```

### Step 4: Start the Orchestrator

Open a **second terminal** and run:

```bash
cd E:\personal_ai_employee
python src/orchestrator.py AI_Employee_Vault
```

You should see:
```
🎵 AI Employee Orchestrator Started
   Vault: AI_Employee_Vault
   Check Interval: 30s
   Qwen Integration: Enabled

📁 Monitoring folders:
   - /Needs_Action
   - /Approved
```

### Step 5: Test the System

1. **Create a test file:**
   ```
   # Test Task
   
   Please process this test file and create a plan.
   
   - [ ] Acknowledge receipt
   - [ ] Create action plan
   - [ ] Move to Done when complete
   ```

2. **Save it to the Inbox folder:**
   - `E:\personal_ai_employee\AI_Employee_Vault\Inbox\test_task.txt`

3. **Watch the magic happen:**
   - Filesystem Watcher detects the file in /Inbox
   - Creates action file in `/Needs_Action`
   - Orchestrator picks it up
   - Creates plan in `/Plans`
   - Moves to `/In_Progress`

4. **Process with Qwen Code:**
   ```bash
   cd AI_Employee_Vault
   qwen "Process the test task in /In_Progress. Follow the Company Handbook rules."
   ```

---

## 🔧 Configuration

### Adjust Check Intervals

For faster response (more CPU usage):
```bash
python src/filesystem_watcher.py AI_Employee_Vault --interval 2
```

For slower response (less CPU usage):
```bash
python src/filesystem_watcher.py AI_Employee_Vault --interval 30
```

### Disable Qwen Integration

For manual-only processing:
```bash
python src/orchestrator.py AI_Employee_Vault --no-qwen
```

---

## 📖 Usage Patterns

### Pattern 1: Inbox Drop Processing (Recommended)

1. Drop any file into `AI_Employee_Vault/Inbox/`
2. Watcher creates action file in `/Needs_Action`
3. Orchestrator moves to `/In_Progress`
4. Qwen Code processes and creates plan
5. Human approves if needed
6. Action executed, moved to `/Done`

### Pattern 2: Direct Vault Action

1. Create `.md` file directly in `/Needs_Action`
2. Use this template:
   ```markdown
   ---
   type: manual_task
   priority: normal
   status: pending
   ---

   # Task Description

   What needs to be done...

   ## Suggested Actions
   - [ ] Step 1
   - [ ] Step 2
   ```
3. Orchestrator will pick it up automatically

### Pattern 3: Ralph Wiggum Autonomous Loop

For multi-step tasks:

```bash
cd AI_Employee_Vault
qwen "Process ALL files in /Needs_Action. For each file:
1. Read and understand the request
2. Create or update the plan
3. Execute actions within your capabilities
4. Request approval for sensitive actions
5. Move completed items to /Done
Output TASK_COMPLETE when all items are processed."
```

The stop hook will keep Qwen working until completion.

---

## 🔍 Monitoring

### Check Logs

```bash
# View today's watcher log
type AI_Employee_Vault\Logs\watcher_2026-01-07.log

# View orchestrator log
type AI_Employee_Vault\Logs\orchestrator_2026-01-07.log

# View activity log
type AI_Employee_Vault\Logs\activity_2026-01-07.log
```

### Check Dashboard

Open `Dashboard.md` in Obsidian to see:
- Item counts in each folder
- Recent activity
- System status

---

## 🐛 Troubleshooting

### Watcher Not Detecting Files

1. Verify file was placed in the Inbox folder:
   ```bash
   dir AI_Employee_Vault\Inbox
   ```

2. Check watcher logs for errors:
   ```bash
   type AI_Employee_Vault\Logs\watcher_*.log
   ```

3. Ensure file has valid encoding (UTF-8 text files work best)

### Orchestrator Not Processing

1. Check Qwen Code is installed:
   ```bash
   qwen --version
   ```

2. Verify vault path is correct

3. Check orchestrator logs

### Claude Not Responding

1. Ensure you're in the vault directory:
   ```bash
   cd AI_Employee_Vault
   ```

2. Check Ralph Wiggum plugin is loaded:
   ```bash
   dir .claude\plugins
   ```

---

## 📊 Bronze Tier Checklist

Use this to verify your setup:

- [ ] Obsidian vault opens without errors
- [ ] Dashboard.md displays correctly
- [ ] Company_Handbook.md is readable
- [ ] Business_Goals.md has your objectives
- [ ] All folders exist (Inbox, Needs_Action, Done, etc.)
- [ ] Filesystem Watcher starts without errors
- [ ] Orchestrator starts without errors
- [ ] Dropping a file into /Inbox creates an action file
- [ ] Qwen Code can be triggered to process items
- [ ] Logs are being written

---

## 🎯 Next Steps (Silver Tier)

After mastering Bronze tier, consider adding:

1. **Gmail Watcher** - Monitor email automatically
2. **WhatsApp Watcher** - Track messages via Playwright
3. **MCP Servers** - Enable external actions (send email, make payments)
4. **Scheduled Tasks** - Run daily briefings via cron/Task Scheduler
5. **Human-in-the-Loop** - Full approval workflow

---

## 📚 Additional Resources

- [Hackathon Blueprint](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Ralph Wiggum Pattern](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- [Claude Code Docs](https://agentfactory.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)
- [Obsidian Help](https://help.obsidian.md)

---

## 🆘 Getting Help

1. Check logs in `/Logs` folder
2. Review `Company_Handbook.md` for rules
3. Re-read this setup guide
4. Check hackathon documentation

---

*Bronze Tier Complete! You now have a functioning AI Employee foundation.*
