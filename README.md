# 🤖 StandupAI
### AI-powered sprint briefs for engineering teams — in one click.

StandupAI connects your Jira, GitHub, and Slack to automatically generate a weekly engineering brief for leadership. No more spending Friday afternoons manually pulling status updates.

**[▶️ Watch Demo](#)** · **[🚀 Live App](https://standupai.streamlit.app)**

---

## The Problem

Every Friday, PMs spend 2–3 hours:
- Checking Jira for ticket statuses
- Scanning GitHub for PR and commit activity
- Scrolling Slack to find the context behind every blocker
- Writing it all up into a report leadership will actually read

StandupAI does all of that in under 30 seconds.

---

## What It Does

Connect three data sources and get one AI-written brief:

| Source | What it pulls |
|--------|--------------|
| **Jira** | Ticket statuses, blockers, assignees, completion rate |
| **GitHub** | Open PRs, draft PRs, recent commits, authors |
| **Slack** | Team conversations, informal blockers, team sentiment |

The AI cross-references all three — so if a ticket says "Blocked" in Jira and someone said "still waiting on finance to send the API keys" in Slack 2 days ago, the report surfaces both together.

---

## Sample Output

```
Weekly Engineering Brief — Sprint 12

Key Wins
• PROJ-101 (User Auth Redesign): Completed ahead of schedule, all tests passing (8 SP)
• PROJ-113 (Webhook Reliability): Shipped with 99.98% delivery rate
• App Store Release v3.2: Approved by Apple and Google, live in both stores

Risks & Blockers
• Payments Epic: PROJ-102 blocked on third-party API credentials from finance team
• Auth Epic Collapsed: PROJ-109 (Okta SSO) and PROJ-115 (Admin Permissions)
  both blocked externally — three blockers in one epic this sprint
• PROJ-117 (Stripe Webhook): Due today, only 80% complete

Team Pulse  
• Slack shows growing frustration around the infosec review delay —
  mentioned in 4 separate threads this week
• Alice flagged the payment credentials issue 3 days ago with no response yet

Leadership Summary
Sprint 12 is at 35% completion with critical blockers in Payments and Auth.
Escalate the finance API credentials and infosec review immediately.
Reallocate resources to unblock PROJ-117 before end of day to avoid revenue impact.
```

---

## Tech Stack

- **Frontend** — Streamlit
- **AI** — OpenRouter (free tier) with Llama 3
- **Integrations** — Jira REST API, GitHub API, Slack Web API
- **Export** — ReportLab (PDF), python-docx (DOCX)
- **Language** — Python 3.11+

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/kiranmai-codes/standupai.git
cd standupai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the root folder:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get your free API key at [openrouter.ai/keys](https://openrouter.ai/keys)

### 4. Run the app
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Connecting Your Tools

### Jira
1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new API token
3. Enter your Jira URL, email, token, and project key in the sidebar

### GitHub
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Create a token with `repo` scope
3. Enter your token and `owner/repo-name` in the sidebar

### Slack
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App
2. Under **OAuth & Permissions**, add scopes: `channels:history`, `users:read`
3. Install to your workspace and copy the `xoxb-...` Bot Token
4. Invite the bot to your channel: `/invite @YourBotName`
5. Get the Channel ID: right-click channel → View channel details → copy ID at the bottom

### No credentials? Use CSV mode
Upload any Jira CSV export — the app works fully without API credentials.

---

## Project Structure

```
standupai/
├── app.py            # Streamlit UI
├── utils.py          # Jira, GitHub, Slack API integrations + AI report
├── export_utils.py   # PDF and DOCX generation
├── requirements.txt
└── .env              # Your API keys (never commit this)
```

---

## Roadmap

- [ ] Auto-schedule weekly reports via cron
- [ ] Post report directly to a Slack channel
- [ ] Support for Linear and Notion
- [ ] Email delivery to leadership

---

## License

MIT

---

*Built by [Kiranmai](https://github.com/kiranmai-codes)*