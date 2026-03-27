---
name: linkedin-mcp-server
description: |
  Model Context Protocol (MCP) server for LinkedIn automation using Playwright.
  Create and schedule posts, share business updates, and generate engagement summaries.
  All posts require human approval before publishing (HITL pattern).
---

# LinkedIn MCP Server

MCP server for LinkedIn posting automation via Playwright browser automation.

## ⚠️ Important Notice

**LinkedIn Terms of Service**: This tool uses browser automation. Ensure you:
- Only use for your own LinkedIn account
- Don't use for spam, bulk posting, or automated engagement
- Respect rate limits (max 3-5 posts per day)
- Understand that automated access may violate LinkedIn's ToS

## Features

- **create_post**: Create a text/image post on LinkedIn
- **schedule_post**: Draft post for later review (HITL)
- **get_analytics**: Get post engagement metrics
- **list_recent_posts**: Get recent posts for audit

## Setup

### 1. Install Dependencies

```bash
pip install playwright
playwright install chromium
```

### 2. Start the Server

```bash
# Start LinkedIn MCP server
python .agents/skills/linkedin-mcp-server/scripts/linkedin_mcp_server.py

# With custom port
python .agents/skills/linkedin-mcp-server/scripts/linkedin_mcp_server.py --port 8810
```

### 3. Configure Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "linkedin",
      "command": "python",
      "args": ["/path/to/linkedin_mcp_server.py"],
      "env": {
        "LINKEDIN_SESSION_PATH": "/path/to/session"
      }
    }
  ]
}
```

## Usage

### Create Post

```python
# Via MCP client
python scripts/mcp-client.py call -u http://localhost:8810 -t create_post \
  -p '{
    "content": "Excited to announce our new AI Employee product!",
    "image_path": "/path/to/image.png",
    "hashtags": ["AI", "Automation", "Startup"]
  }'
```

### Schedule Post (Draft for Approval)

```python
python scripts/mcp-client.py call -u http://localhost:8810 -t schedule_post \
  -p '{
    "content": "Weekly business update: Revenue up 20% this month...",
    "scheduled_time": "2026-01-08T09:00:00Z"
  }'
```

## Human-in-the-Loop Pattern

For LinkedIn posts, always use the approval workflow:

1. **Claude drafts post** → Creates approval file in `/Pending_Approval/`
2. **Human reviews** → Moves file to `/Approved/`
3. **Orchestrator triggers MCP** → LinkedIn MCP publishes the post
4. **Log action** → Move to `/Done/`

### Approval File Format

```markdown
---
type: approval_request
action: linkedin_post
content: Excited to announce...
hashtags: AI, Automation
scheduled_time: 2026-01-08T09:00:00Z
created: 2026-01-07T10:30:00Z
status: pending
---

## LinkedIn Post Details

### Content
Excited to announce our new AI Employee product!

### Hashtags
#AI #Automation #Startup

### Scheduled Time
January 8, 2026 at 9:00 AM

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
```

## Content Strategy Integration

The AI Employee can automatically generate LinkedIn posts based on:

| Trigger | Post Type | Example |
|---------|-----------|---------|
| Invoice paid | Milestone celebration | "Just completed project for Client A!" |
| Weekly audit | Business update | "Week 2 revenue: $5,000. On track!" |
| New client | Announcement | "Welcome to our newest client, Company X!" |
| Project complete | Case study | "How we helped Client Y achieve Z..." |

## Tools Reference

| Tool | Description | Requires Approval |
|------|-------------|-------------------|
| `create_post` | Publish post immediately | **Always** |
| `schedule_post` | Draft for later | Yes |
| `get_analytics` | Get engagement metrics | No |
| `list_recent_posts` | Get recent posts | No |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login required | Run with `--login` flag first |
| Session expired | Delete session and re-login |
| Post failed | Check LinkedIn UI changed - update selectors |
| Rate limited | Reduce posting frequency |

## Security Notes

- **Never commit** session files to git
- Session gives full access to your LinkedIn - protect it
- Use for personal account only
- Log out from LinkedIn when not in use

## Best Practices

1. **Draft first, publish later** - Always use HITL
2. **Limit to 3-5 posts/day** - Avoid rate limits
3. **Business-focused content** - Revenue, milestones, learnings
4. **Include engagement hooks** - Questions, insights
5. **Track analytics** - Review what resonates
