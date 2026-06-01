import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)


# ─── Jira ────────────────────────────────────────────────────────────────────

def fetch_jira_tickets(jira_url, email, token, project_key):
    try:
        url = f"{jira_url.rstrip('/')}/rest/api/3/search"
        auth = (email, token)
        headers = {"Accept": "application/json"}
        params = {
            "jql": f"project={project_key} ORDER BY updated DESC",
            "maxResults": 50,
            "fields": "summary,status,priority,assignee"
        }

        resp = requests.get(url, auth=auth, headers=headers, params=params)

        if resp.status_code == 401:
            return {"error": "Invalid Jira credentials. Check your email and API token."}
        if resp.status_code == 400:
            return {"error": f"Invalid project key '{project_key}' or JQL query."}
        if not resp.ok:
            return {"error": f"Jira API error {resp.status_code}: {resp.text}"}

        issues = resp.json().get("issues", [])
        tickets = []
        for issue in issues:
            f = issue["fields"]
            tickets.append({
                "key":      issue["key"],
                "title":    f.get("summary", ""),
                "status":   f["status"]["name"],
                "priority": f["priority"]["name"] if f.get("priority") else "None",
                "assignee": f["assignee"]["displayName"] if f.get("assignee") else "Unassigned"
            })

        completed   = sum(1 for t in tickets if t["status"] in ["Done", "Closed", "Resolved"])
        blocked     = sum(1 for t in tickets if t["status"] in ["Blocked", "Impediment"])
        in_progress = sum(1 for t in tickets if t["status"] in ["In Progress", "In Review"])
        total       = len(tickets)
        completion_rate = round((completed / total) * 100, 1) if total else 0

        return {
            "tickets": tickets,
            "metrics": {
                "completed": completed,
                "blocked": blocked,
                "in_progress": in_progress,
                "completion_rate": completion_rate
            }
        }

    except requests.exceptions.ConnectionError:
        return {"error": f"Could not connect to {jira_url}. Check the URL."}
    except Exception as e:
        return {"error": str(e)}


# ─── GitHub ──────────────────────────────────────────────────────────────────

def fetch_github_data(token, repo):
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        base = "https://api.github.com"

        pr_resp = requests.get(
            f"{base}/repos/{repo}/pulls?state=open&per_page=10",
            headers=headers
        )
        if pr_resp.status_code == 401:
            return {"error": "Invalid GitHub token."}
        if pr_resp.status_code == 404:
            return {"error": f"Repo '{repo}' not found. Check owner/repo format."}
        if not pr_resp.ok:
            return {"error": f"GitHub API error {pr_resp.status_code}"}

        prs = pr_resp.json()
        pr_details = [{
            "title":      pr["title"],
            "author":     pr["user"]["login"],
            "url":        pr["html_url"],
            "created_at": pr["created_at"],
            "draft":      pr.get("draft", False)
        } for pr in prs]

        commit_resp = requests.get(
            f"{base}/repos/{repo}/commits?per_page=10",
            headers=headers
        )
        commits = commit_resp.json() if commit_resp.ok else []
        recent_commits = [{
            "sha":     c["sha"][:7],
            "message": c["commit"]["message"].split("\n")[0][:80],
            "author":  c["commit"]["author"]["name"],
            "date":    c["commit"]["author"]["date"][:10]
        } for c in commits]

        return {
            "repo":           repo,
            "open_prs":       len(pr_details),
            "pr_details":     pr_details,
            "recent_commits": recent_commits
        }

    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to GitHub API."}
    except Exception as e:
        return {"error": str(e)}


# ─── Slack ───────────────────────────────────────────────────────────────────

def fetch_slack_messages(token, channel_id, limit=30):
    """
    Fetches recent messages from a Slack channel using the Web API.
    Requires a bot token with channels:history and users:read scopes.
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Fetch channel history
        resp = requests.get(
            "https://slack.com/api/conversations.history",
            headers=headers,
            params={"channel": channel_id, "limit": limit}
        )

        if not resp.ok:
            return {"error": f"Slack API error {resp.status_code}"}

        data = resp.json()

        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            if error == "invalid_auth":
                return {"error": "Invalid Slack token. Check your Bot Token."}
            if error == "channel_not_found":
                return {"error": f"Channel '{channel_id}' not found. Use the channel ID (e.g. C01234ABCDE), not the name."}
            if error == "not_in_channel":
                return {"error": "Bot is not in this channel. Invite it with /invite @YourBot"}
            return {"error": f"Slack error: {error}"}

        messages = data.get("messages", [])

        # Resolve user IDs to display names
        user_cache = {}

        def get_username(user_id):
            if not user_id:
                return "Unknown"
            if user_id in user_cache:
                return user_cache[user_id]
            u_resp = requests.get(
                "https://slack.com/api/users.info",
                headers=headers,
                params={"user": user_id}
            )
            if u_resp.ok:
                u_data = u_resp.json()
                name = u_data.get("user", {}).get("real_name") or \
                       u_data.get("user", {}).get("name", user_id)
            else:
                name = user_id
            user_cache[user_id] = name
            return name

        parsed = []
        for msg in messages:
            # Skip bot messages, join/leave events
            if msg.get("subtype") in ("channel_join", "channel_leave", "bot_message"):
                continue
            text = msg.get("text", "").strip()
            if not text:
                continue
            parsed.append({
                "user":      get_username(msg.get("user")),
                "text":      text,
                "timestamp": msg.get("ts", "")
            })

        return {
            "channel_id": channel_id,
            "message_count": len(parsed),
            "messages": parsed
        }

    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to Slack API."}
    except Exception as e:
        return {"error": str(e)}


# ─── AI Report ───────────────────────────────────────────────────────────────

def generate_report(metrics, tickets, github_data=None, slack_data=None):

    # GitHub section
    github_section = "No GitHub data provided."
    if github_data:
        pr_list = "\n".join([
            f"  - {pr['title']} by {pr['author']} ({'DRAFT' if pr['draft'] else 'Ready'})"
            for pr in github_data.get("pr_details", [])
        ])
        commit_list = "\n".join([
            f"  - [{c['sha']}] {c['message']} ({c['author']}, {c['date']})"
            for c in github_data.get("recent_commits", [])[:5]
        ])
        github_section = f"""GitHub Repository: {github_data.get('repo', 'N/A')}
Open Pull Requests ({github_data.get('open_prs', 0)}):
{pr_list}

Recent Commits:
{commit_list}"""

    # Slack section
    slack_section = "No Slack data provided."
    if slack_data and slack_data.get("messages"):
        msg_list = "\n".join([
            f"  - {m['user']}: {m['text'][:200]}"
            for m in slack_data["messages"][:20]
        ])
        slack_section = f"""Channel: {slack_data.get('channel_id', 'N/A')} ({slack_data.get('message_count', 0)} messages fetched)
Recent Messages:
{msg_list}"""

    prompt = f"""
You are an experienced Product Chief of Staff preparing a weekly brief for engineering leadership.

Analyze ALL the data sources below and produce a concise, insightful report.
When Slack messages are available, use them to add human context behind the ticket statuses —
what are people actually worried about, what's the team sentiment, are there blockers being discussed
informally that aren't reflected in Jira yet?

── JIRA SPRINT DATA ──
Metrics: {metrics}
Tickets: {tickets}

── GITHUB ACTIVITY ──
{github_section}

── SLACK TEAM CONVERSATIONS ──
{slack_section}

Produce a report with these sections:

1. **Key Wins** — what shipped, what's working well
2. **Risks & Blockers** — what could derail the sprint, cross-reference Jira blockers with Slack discussions
3. **Delays** — what's behind schedule and why
4. **Team Pulse** — only if Slack data is available: what is the team sentiment, informal concerns, and communication patterns
5. **Engineering Health** — PR velocity, commit activity (if GitHub data available)
6. **Leadership Summary** — 3-4 sentence executive summary with recommended actions

Be specific, reference actual ticket names, PR titles, and quote or paraphrase relevant Slack messages where insightful.
Use bullet points. Be concise and direct.
"""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content