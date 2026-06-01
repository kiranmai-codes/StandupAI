import streamlit as st
import pandas as pd
from datetime import datetime

from utils import generate_report, fetch_jira_tickets, fetch_github_data, fetch_slack_messages
from export_utils import report_to_pdf, report_to_docx

st.set_page_config(page_title="StandupAI", page_icon="📊", layout="wide")
st.title("📊 StandupAI")
st.caption("Connect your tools for a real-time AI-powered sprint brief")

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔌 Connections")

    st.subheader("Jira")
    jira_url     = st.text_input("Jira URL", placeholder="https://yourcompany.atlassian.net")
    jira_email   = st.text_input("Email", placeholder="you@company.com")
    jira_token   = st.text_input("API Token", type="password",
                                  help="Create at id.atlassian.com/manage-profile/security/api-tokens")
    jira_project = st.text_input("Project Key", placeholder="e.g. PROJ")

    st.divider()

    st.subheader("GitHub")
    github_token = st.text_input("GitHub Token", type="password",
                                  help="Create at github.com/settings/tokens")
    github_repo  = st.text_input("Repo", placeholder="owner/repo-name")

    st.divider()

    st.subheader("Slack")
    slack_token   = st.text_input(
        "Bot Token", type="password",
        help="Create a Slack app at api.slack.com/apps → OAuth & Permissions → Bot Token (xoxb-...)"
    )
    slack_channel = st.text_input(
        "Channel ID", placeholder="e.g. C01234ABCDE",
        help="Right-click channel → View channel details → Copy channel ID at the bottom"
    )
    slack_limit   = st.slider("Messages to fetch", min_value=10, max_value=100, value=30, step=10)

    st.divider()
    st.caption("Or upload a CSV to demo without credentials")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔗 Live Data", "📁 CSV Upload"])

with tab1:
    col_j, col_g, col_s = st.columns(3)

    with col_j:
        if st.button("Fetch Jira Tickets", use_container_width=True):
            if not all([jira_url, jira_email, jira_token, jira_project]):
                st.warning("Fill in all Jira fields in the sidebar.")
            else:
                with st.spinner("Fetching Jira..."):
                    result = fetch_jira_tickets(jira_url, jira_email, jira_token, jira_project)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["jira_data"] = result
                        st.success(f"✅ {len(result['tickets'])} tickets fetched")

    with col_g:
        if st.button("Fetch GitHub Data", use_container_width=True):
            if not all([github_token, github_repo]):
                st.warning("Fill in GitHub fields in the sidebar.")
            else:
                with st.spinner("Fetching GitHub..."):
                    result = fetch_github_data(github_token, github_repo)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["github_data"] = result
                        st.success(f"✅ {result['open_prs']} PRs, {len(result['recent_commits'])} commits")

    with col_s:
        if st.button("Fetch Slack Messages", use_container_width=True):
            if not all([slack_token, slack_channel]):
                st.warning("Fill in Slack fields in the sidebar.")
            else:
                with st.spinner("Fetching Slack..."):
                    result = fetch_slack_messages(slack_token, slack_channel, slack_limit)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["slack_data"] = result
                        st.success(f"✅ {result['message_count']} messages fetched")

    # ── Display fetched data ──
    if "jira_data" in st.session_state:
        jira_data = st.session_state["jira_data"]
        st.subheader("📋 Jira Tickets")
        st.dataframe(pd.DataFrame(jira_data["tickets"]), use_container_width=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Completed",    jira_data["metrics"]["completed"])
        c2.metric("Blocked",      jira_data["metrics"]["blocked"])
        c3.metric("In Progress",  jira_data["metrics"]["in_progress"])
        c4.metric("Completion %", jira_data["metrics"]["completion_rate"])

    if "github_data" in st.session_state:
        github_data = st.session_state["github_data"]
        st.subheader("🐙 GitHub Activity")
        gc1, gc2 = st.columns(2)
        with gc1:
            st.markdown("**Open Pull Requests**")
            for pr in github_data["pr_details"]:
                badge = " `DRAFT`" if pr["draft"] else ""
                st.markdown(f"- [{pr['title']}]({pr['url']}) by `{pr['author']}`{badge}")
        with gc2:
            st.markdown("**Recent Commits**")
            for c in github_data["recent_commits"][:5]:
                st.markdown(f"- `{c['sha']}` {c['message']} — *{c['author']}*")

    if "slack_data" in st.session_state:
        slack_data = st.session_state["slack_data"]
        st.subheader("💬 Slack Messages")
        st.caption(f"Last {slack_data['message_count']} messages from channel `{slack_data['channel_id']}`")
        with st.expander("View messages", expanded=False):
            for msg in slack_data["messages"]:
                st.markdown(f"**{msg['user']}**: {msg['text']}")
                st.divider()

with tab2:
    uploaded_file = st.file_uploader("Upload Jira CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, on_bad_lines='skip', quotechar='"', encoding='utf-8')
        st.subheader("Tickets")
        st.dataframe(df, use_container_width=True)

        completed       = len(df[df["status"] == "Done"])
        blocked         = len(df[df["status"] == "Blocked"])
        in_progress     = len(df[df["status"] == "In Progress"])
        total           = len(df)
        completion_rate = round((completed / total) * 100, 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Completed",    completed)
        c2.metric("Blocked",      blocked)
        c3.metric("In Progress",  in_progress)
        c4.metric("Completion %", completion_rate)

        st.session_state["csv_metrics"] = {
            "completed": completed, "blocked": blocked,
            "in_progress": in_progress, "completion_rate": completion_rate
        }
        st.session_state["csv_tickets"] = df.to_dict(orient="records")

# ─── Generate Report ──────────────────────────────────────────────────────────
st.divider()

has_jira   = "jira_data"   in st.session_state
has_github = "github_data" in st.session_state
has_slack  = "slack_data"  in st.session_state
has_csv    = "csv_metrics" in st.session_state

if has_jira or has_csv:
    # Show which sources will be included
    sources = []
    if has_jira:   sources.append("✅ Jira")
    if has_csv:    sources.append("✅ CSV")
    if has_github: sources.append("✅ GitHub")
    if has_slack:  sources.append("✅ Slack")
    st.caption(f"Report will include: {' · '.join(sources)}")

    if st.button("🚀 Generate Unified AI Report", use_container_width=True, type="primary"):
        with st.spinner("Generating AI Product Brief..."):
            metrics = st.session_state["jira_data"]["metrics"] if has_jira else st.session_state["csv_metrics"]
            tickets = st.session_state["jira_data"]["tickets"] if has_jira else st.session_state["csv_tickets"]
            gh      = st.session_state.get("github_data")
            slack   = st.session_state.get("slack_data")

            report = generate_report(metrics, tickets, gh, slack)
        st.session_state["report"] = report
else:
    st.info("👈 Connect Jira / GitHub / Slack in the sidebar, or upload a CSV to get started.")

# ─── Report + Downloads ───────────────────────────────────────────────────────
if "report" in st.session_state:
    report    = st.session_state["report"]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    st.subheader("📋 AI Product Brief")
    st.markdown(report)

    st.divider()
    st.markdown("**Download Report**")
    dl1, dl2, _ = st.columns([1, 1, 4])

    with dl1:
        st.download_button(
            label="⬇️ Download PDF",
            data=report_to_pdf(report),
            file_name=f"sprint_report_{timestamp}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with dl2:
        st.download_button(
            label="⬇️ Download DOCX",
            data=report_to_docx(report),
            file_name=f"sprint_report_{timestamp}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )