# Quick Start - AI Employee Bronze Tier

## 1-Minute Setup

### Step 1: Open Two Terminals

Open **two** terminal windows side by side.

### Step 2: Start Watcher (Terminal 1)

**Option A - Using batch file:**
```bash
start-watcher.bat
```

**Option B - Using Python:**
```bash
python src\filesystem_watcher.py AI_Employee_Vault
```

You should see:

```
📁 Filesystem Watcher Started
   Vault: AI_Employee_Vault
   Inbox: AI_Employee_Vault\Inbox
   Check Interval: 5s

💡 Drop files into: AI_Employee_Vault\Inbox
```

### Step 3: Start Orchestrator (Terminal 2)

**Option A - Using batch file:**
```bash
start-orchestrator.bat
```

**Option B - Using Python:**
```bash
python src\orchestrator.py AI_Employee_Vault
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

### Step 4: Test It!

1. Create a text file: `AI_Employee_Vault\Inbox\test.txt`
2. Write something in it: "Please process this test"
3. Save the file

**Watch Terminal 1** - You should see:
```
New file detected: test.txt
Action file created: FILE_test.txt_...
```

**Watch Terminal 2** - You should see:
```
Found 1 item(s) in /Needs_Action
Processing: FILE_test.txt_...
```

### Step 5: Check Obsidian

1. Open Obsidian
2. Open vault: `AI_Employee_Vault`
3. Check folders:
   - `/Inbox` - your original file
   - `/Needs_Action` - action file created
   - `/Plans` - plan created

---

## How to Know It's Working

| Indicator | What to Look For |
|-----------|------------------|
| **Console Output** | "New file detected" in Terminal 1 |
| **File Explorer** | New `.md` file appears in `/Needs_Action` |
| **Obsidian** | Dashboard shows updated counts |
| **Logs** | Check `AI_Employee_Vault\Logs\*.log` |

---

## Common Issues

### "Watcher not detecting files"
- Files must be added **after** watcher starts
- Solution: Delete state file and restart:
  ```bash
  del AI_Employee_Vault\.state_FilesystemWatcher.txt
  ```

### "Orchestrator not processing"
- Check Qwen Code is available: `qwen --version`
- Or run with `--no-qwen` for manual mode

### "Nothing happens"
- Keep both terminals open!
- Don't close them - they run continuously

---

## Stop Everything

Press `Ctrl+C` in both terminals.

---

## Next Steps

1. Read `README.md` for full documentation
2. Review `Company_Handbook.md` for rules
3. Check `Business_Goals.md` for objectives
4. Process items with Qwen Code:
   ```bash
   cd AI_Employee_Vault
   qwen "Process all items in /Needs_Action"
   ```
