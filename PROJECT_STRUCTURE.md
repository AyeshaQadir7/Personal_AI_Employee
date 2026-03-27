# AI Employee Project - Organized Structure

## 📁 Project Structure

```
personal_ai_employee/
├── 📁 AI_Employee_Vault/          # Obsidian vault (DO NOT DELETE)
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Business_Goals.md
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── In_Progress/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Done/
│   ├── Plans/
│   └── Logs/
│
├── 📁 src/                        # Python source code (CORE - DO NOT MODIFY)
│   ├── base_watcher.py           # Base class for all watchers
│   ├── filesystem_watcher.py     # Filesystem watcher (Bronze)
│   ├── gmail_watcher.py          # Gmail watcher (Silver) ✅ WORKING
│   ├── linkedin_watcher.py       # LinkedIn watcher (Silver)
│   ├── orchestrator.py           # Original orchestrator
│   ├── orchestrator_full.py      # Full orchestrator with Qwen + MCP ✅ USE THIS
│   └── orchestrator_minimal.py   # Minimal orchestrator for LinkedIn
│
├── 📁 .agents/skills/             # MCP Servers and Skills
│   ├── browsing-with-playwright/  # Playwright browser automation
│   ├── email-mcp-server/          # Email MCP server ✅ WORKING
│   ├── gmail-watcher/             # Gmail watcher skill
│   ├── linkedin-mcp-server/       # LinkedIn MCP server
│   ├── whatsapp-watcher/          # WhatsApp watcher skill
│   ├── hitl-approval-workflow/    # HITL workflow
│   └── scheduler/                 # Scheduler skill
│
├── 📁 docs/                       # Documentation
│   ├── Personal AI Employee Hackathon 0_....md
│   ├── QWEN_CODE_GUIDE.md
│   ├── QWEN_CODE_INTEGRATION.md
│   ├── SILVER_TIER_QUICKSTART.md
│   ├── SILVER_TIER_SETUP.md
│   └── QUICKSTART.md
│
├── 📁 tests/                      # Test scripts
│   ├── post_linkedin.py
│   └── test_linkedin.py
│
├── 📁 temp/                       # Temporary files, screenshots
│   └── linkedin_before_post.png
│
├── 📁 venv/                       # Python virtual environment
│
├── credentials.json               # Gmail OAuth2 credentials ✅ REQUIRED
├── token.json                     # Gmail OAuth2 token ✅ AUTO-GENERATED
├── mcp.json                       # MCP server configuration
├── requirements.txt               # Python dependencies
├── skills-lock.json              # Installed skills registry
│
├── QWEN.md                        # Main project documentation
└── README.md                      # This file
```

---

## ✅ Working Components (DO NOT MODIFY)

| File | Purpose | Status |
|------|---------|--------|
| `src/gmail_watcher.py` | Monitors Gmail | ✅ WORKING |
| `src/orchestrator_full.py` | Main orchestrator with Qwen + MCP | ✅ WORKING |
| `.agents/skills/email-mcp-server/scripts/email_mcp_simple.py` | Sends emails | ✅ WORKING |
| `credentials.json` | Gmail OAuth2 | ✅ REQUIRED |
| `token.json` | Gmail auth token | ✅ AUTO-GENERATED |

---

## 🚀 Quick Start

### Start Gmail Watcher + Orchestrator

```bash
cd E:\personal_ai_employee
venv\Scripts\activate

# Terminal 1: Gmail Watcher
python src/gmail_watcher.py AI_Employee_Vault --interval 120

# Terminal 2: Full Orchestrator
python src/orchestrator_full.py AI_Employee_Vault --interval 10
```

### Process with Qwen Code

```bash
cd AI_Employee_Vault
qwen
# Process action files when they appear
```

---

## 📋 Workflow

```
Email arrives → Gmail Watcher → /Needs_Action/ → Orchestrator → /In_Progress/
                                                              ↓
Qwen Code creates plan + draft + approval request
                                                              ↓
/Pending_Approval/ → You approve → /Approved/ → Email MCP → Sent! → /Done/
```

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `credentials.json` | Gmail OAuth2 credentials (download from Google Cloud) |
| `token.json` | Auto-generated after first OAuth login |
| `mcp.json` | MCP server configuration for Qwen Code |
| `requirements.txt` | Python dependencies |

---

## 📚 Documentation

See `docs/` folder for:
- Hackathon blueprint
- Silver Tier setup guide
- Qwen Code integration guide
- Quick start guides

---

## ⚠️ Important Notes

1. **DO NOT DELETE** `credentials.json` or `token.json` - required for Gmail API
2. **DO NOT MODIFY** `src/orchestrator_full.py` unless you know what you're doing
3. **ALWAYS USE** `venv\Scripts\activate` before running Python commands
4. **KEEP** `AI_Employee_Vault/` folder structure intact

---

*Last organized: March 27, 2026*
*Status: Silver Tier Fully Working* ✅
