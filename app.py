"""NewsLens: polished Streamlit dashboard for the five-node news agent."""
from __future__ import annotations

import json
import os
from html import escape

import streamlit as st
from dotenv import load_dotenv

from storage import get_run, get_run_stats, list_runs
from workflow import CATEGORIES, MIN_WORDS, MODEL_NAME, run_agent

load_dotenv()
st.set_page_config(
    page_title="NewsLens · AI News Summarizer",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "NewsLens: five-node LangGraph + Groq news agent with local execution history."},
)

# Static CSS only: user-provided article text is never interpolated into styles.
st.markdown("""
<style>
:root { --nl-border: #27364b; --nl-muted: #9badc5; --nl-accent: #64cbb9; }
.stApp { background: #0a1220; color: #eef4fc; }
[data-testid="stHeader"] { background: rgba(10,18,32,.88); }
[data-testid="stSidebar"] { background: #101b2c; border-right: 1px solid #223147; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height: 1.6; }
.block-container { max-width: 1390px; padding: 1.7rem 2.25rem 4rem; }
section[data-testid="stSidebar"] .block-container { padding: 1.6rem 1.05rem; }
h1, h2, h3 { letter-spacing: -.025em; }
[data-testid="stVerticalBlock"] { gap: .85rem; }
.hero {
    padding: 2.05rem 2.5rem; border: 1px solid #28485a; border-radius: 22px;
    background: radial-gradient(ellipse at 100% 0, rgba(38,120,128,.25), transparent 48%),
                linear-gradient(135deg, #14263a 0%, #0f1b30 75%);
    box-shadow: 0 14px 40px rgba(0,0,0,.14); margin-bottom: 1.45rem;
}
.eyebrow { font-size:.72rem; letter-spacing:.16em; font-weight:750; text-transform:uppercase;
    color:#78dbca; margin-bottom:.58rem; }
.hero h1 { font-size:clamp(1.9rem,3vw,2.9rem); line-height:1.12; font-weight:800; margin:0 0 .75rem; color:#f3f8ff; }
.hero p { max-width:780px; color:#b9cae0; font-size:1rem; line-height:1.65; margin:0 0 1.1rem; }
.chip { display:inline-flex; align-items:center; border:1px solid #375167;
    background:rgba(25,47,65,.72); color:#cde2f1; font-size:.77rem;
    line-height:1.4; font-weight:600; padding:.4rem .7rem; border-radius:50px; margin:0 .4rem .35rem 0; }
.sidebar-logo { padding:.45rem .1rem 1rem; }
.sidebar-logo .logo-line { font-size:1.5rem; font-weight:850; color:#f0f7ff; letter-spacing:-.04em; }
.sidebar-logo .logo-line span { color:#6dd6c5; }
.sidebar-logo .logo-sub { color:#9db1c9; font-size:.84rem; margin-top:.1rem; }
.side-card { border:1px solid #2c4057; background:#162438; border-radius:14px;
    padding:.92rem 1rem; margin:.4rem 0 1rem; }
.side-label { font-size:.68rem; letter-spacing:.13em; font-weight:800; color:#a2bad4; margin-bottom:.4rem; }
.online { color:#83e1b0; font-weight:750; font-size:.9rem; }
.offline { color:#ffce86; font-weight:750; font-size:.9rem; }
.side-small { color:#9fb2c9; font-size:.78rem; overflow-wrap:anywhere; margin-top:.35rem; line-height:1.55; }
.stTabs [data-baseweb="tab-list"] { border-bottom:1px solid #2a3a4e; gap:.8rem; }
.stTabs [data-baseweb="tab"] { color:#b7c9e0; font-weight:650; padding:.75rem 1.1rem; }
.stTabs [aria-selected="true"] { color:#76dcca !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color:#64cbb9 !important; }
.stTabs [data-baseweb="tab-border"] { background:#29394f; }
.heading-line { margin:.45rem 0 .95rem; }
.heading-line h2 { font-size:1.26rem; color:#eef5ff; margin:0 .0rem .28rem; }
.heading-line p { font-size:.89rem; color:#aebed2; margin:0; line-height:1.55; }
div[data-testid="stForm"] { background:#101d2f; border:1px solid #293b52;
    border-radius:17px; padding:1.2rem 1.35rem .7rem; }
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
    background:#0c1829; border:1px solid #30465e; color:#f1f7ff; border-radius:11px;
}
[data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus {
    border-color:#64cbb9; box-shadow:0 0 0 1px rgba(100,203,185,.25);
}
div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(100deg,#3ca99d,#227b92); color:white; border:none;
    border-radius:11px; font-weight:750; min-height:48px; box-shadow:0 8px 20px #0d394540;
}
div.stButton > button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] button:hover {
    background:linear-gradient(100deg,#48bfaf,#2b92ab); color:white;
}
.result-shell { padding:1.2rem 1.3rem; border:1px solid #2b4057;
    background:#111e31; border-radius:17px; }
.result-label { text-transform:uppercase; font-size:.68rem; font-weight:800;
    letter-spacing:.13em; color:#9aaec5; margin-bottom:.6rem; }
.result-title { font-size:1.3rem; font-weight:800; line-height:1.35; color:#edf7ff; }
.result-sub { color:#acbfd6; font-size:.87rem; line-height:1.6; }
.stat-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.75rem; margin:0 0 1rem; }
.stat-box { min-width:0; border:1px solid #2b3e56; border-radius:13px; background:#142338;
    padding:.95rem 1rem; }
.stat-label { font-size:.69rem; color:#9fb5cd; margin-bottom:.35rem; letter-spacing:.04em; font-weight:700; }
.stat-value { font-size:1.05rem; line-height:1.4; font-weight:800; color:#edf5ff;
    overflow-wrap:anywhere; }
.stat-value.big { font-size:1.55rem; }
.stat-value.teal { color:#7ee0cd; }
.stat-value.amber { color:#f8c783; }
.stat-value.red { color:#ff9da1; }
.progress-track { width:100%; height:8px; background:#27384e; border-radius:999px; overflow:hidden; margin:.65rem 0 .25rem; }
.progress-bar { height:100%; background:linear-gradient(90deg,#2599a7,#77dccc); border-radius:999px; }
.progress-caption { color:#a9bdd2; font-size:.77rem; }
.summary-card { border:1px solid #2c4851; background:linear-gradient(120deg,#112f32,#152537);
    padding:1.1rem 1.25rem; border-radius:14px; margin:.85rem 0; }
.summary-head { color:#7be0d0; font-size:.73rem; letter-spacing:.12em; font-weight:800;
    text-transform:uppercase; margin-bottom:.35rem; }
.trace { border-left:2px solid #36536b; margin:.5rem 0 .2rem .35rem; padding-left:1rem; }
.trace-item { position:relative; padding:.25rem 0 1.15rem; }
.trace-item:before { content:""; position:absolute; left:-1.38rem; top:.55rem;
    border-radius:50%; width:.67rem; height:.67rem; background:#77d2c5; border:2px solid #13283b; }
.trace-name { font-size:.9rem; font-weight:750; color:#e6f1ff; }
.trace-meta { color:#a4b8d1; font-size:.78rem; line-height:1.45; overflow-wrap:anywhere; margin-top:.15rem; }
.empty-card { border:1px dashed #426079; border-radius:17px; background:#111f31;
    text-align:center; padding:2.8rem 1.25rem; }
.empty-icon { font-size:2.5rem; margin-bottom:.6rem; }
.empty-card h3 { margin:0 0 .45rem; font-size:1.2rem; color:#edf6ff; }
.empty-card p { color:#b0c2d7; max-width:370px; margin:auto; font-size:.89rem; line-height:1.65; }
.note { color:#a7bad0; font-size:.81rem; line-height:1.65; }
[data-testid="stExpander"] { border:1px solid #2d4058; border-radius:12px; background:#101d2e; }
[data-testid="stAlert"] { border-radius:12px; }
[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }
.footer { border-top:1px solid #25354a; margin-top:2rem; padding-top:1rem;
    font-size:.75rem; color:#8da5bd; }
@media (max-width:950px) {
    .block-container { padding:1.2rem .9rem 2.5rem; }
    .hero { padding:1.45rem 1.25rem; }
    .stat-grid { gap:.45rem; }
    .stat-box { padding:.72rem .65rem; }
    .stat-value { font-size:.88rem; }
    .stat-value.big { font-size:1.2rem; }
}
@media (max-width:570px) {
    .stat-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .stTabs [data-baseweb="tab"] { padding:.65rem .4rem; font-size:.75rem; }
}
</style>
""", unsafe_allow_html=True)


def safe(value: object) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def tiles(items: list[tuple[str, str, str]]) -> None:
    """Render responsive statistics; always escape run-derived text."""
    html = '<div class="stat-grid">'
    for label, value, variant in items:
        theme = variant if variant in {"teal", "amber", "red", "big"} else ""
        html += (
            '<div class="stat-box"><div class="stat-label">'
            + safe(label) + '</div><div class="stat-value ' + theme + '">'
            + safe(value) + '</div></div>'
        )
    st.markdown(html + "</div>", unsafe_allow_html=True)


def section(heading: str, subtext: str) -> None:
    st.markdown(
        f'<div class="heading-line"><h2>{safe(heading)}</h2><p>{safe(subtext)}</p></div>',
        unsafe_allow_html=True,
    )


def node_trace(events: list[dict]) -> None:
    parts = ['<div class="trace">']
    for event in events:
        name = str(event.get("node", "node")).replace("_", " ").title()
        detail = str(event.get("details", ""))
        action = str(event.get("action", ""))
        time_text = str(event.get("time", ""))
        parts.append(
            '<div class="trace-item"><div class="trace-name">'
            + safe(name) + '</div><div class="trace-meta">'
            + safe(action) + (" · " + safe(detail) if detail else "")
            + ('<div>' + safe(time_text) + '</div>' if time_text else "")
            + '</div></div>'
        )
    st.markdown("".join(parts) + "</div>", unsafe_allow_html=True)


def status_title(code: str) -> tuple[str, str]:
    names = {
        "completed": ("Analysis complete", "teal"),
        "skipped_short": ("Below word threshold", "amber"),
        "partial": ("Partially completed", "amber"),
        "error": ("Analysis could not finish", "red"),
    }
    return names.get(code, ("Workflow processed", ""))


def render_result(result: dict) -> None:
    status = str(result.get("status", ""))
    title, color = status_title(status)
    words = int(result.get("word_count") or 0)
    event_names = [str(e.get("node", "")).replace("_", " ").title() for e in result.get("events", [])]
    node_path = " → ".join(event_names)

    tiles([
        ("ARTICLE LENGTH", f"{words:,} words", "big"),
        ("RESULT", title, color),
        ("CATEGORY", result.get("category") or "Not assigned", ""),
    ])

    percentage = min(100, round(words * 100 / MIN_WORDS))
    st.markdown(
        '<div class="progress-track"><div class="progress-bar" style="width:'
        + str(percentage) + '%"></div></div><div class="progress-caption">'
        + safe(f"{words} / {MIN_WORDS} words needed for AI summarization") + '</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    if status == "skipped_short":
        st.info(
            f"The cleaned article has {words} words. Content below {MIN_WORDS} words "
            "goes directly from Processing to Execution Log, as specified by your workflow.",
            icon="ℹ️",
        )
    if result.get("error"):
        st.error(str(result["error"]), icon="🚫")
        if result.get("input_type") == "url":
            st.caption("Tip: use a link to one news article (not a site's home page) or paste the article text.")

    if result.get("summary"):
        st.markdown('<div class="summary-card"><div class="summary-head">✦ Groq AI summary</div></div>', unsafe_allow_html=True)
        st.write(result["summary"])
    elif status == "skipped_short":
        st.caption("Summary and category were intentionally skipped. Your article and execution events are still saved.")

    if node_path:
        st.markdown("**Execution path**")
        st.caption(node_path)

    st.markdown("---")
    run_id = str(result.get("run_id", ""))
    st.caption(
        ("✅ Saved to local SQLite" if result.get("logged") else "⚠️ Run not saved")
        + (f"  ·  Run ID: {run_id[:8]}…" if run_id else "")
    )
    with st.expander("See cleaned article"):
        st.text_area(
            "Extracted text", result.get("cleaned_content") or "No content extracted.",
            height=190, disabled=True, key=f"cleaned_{run_id}",
        )
    with st.expander("View node-by-node execution trace"):
        node_trace(result.get("events") or [])
        st.caption(f"Run ID: {run_id}")
    st.download_button(
        "↓ Export this run as JSON",
        json.dumps(result, ensure_ascii=False, indent=2),
        file_name=f"news_run_{run_id or 'latest'}.json", mime="application/json",
        use_container_width=True, key=f"export_{run_id}",
    )


key = os.getenv("GROQ_API_KEY", "").strip()
key_present = bool(key and key != "your_groq_api_key_here")

with st.sidebar:
    st.markdown('''<div class="sidebar-logo"><div class="logo-line">🗞️ News<span>Lens</span></div>
      <div class="logo-sub">An intelligent news processing studio</div></div>''', unsafe_allow_html=True)
    st.markdown("##### CONNECTIVITY")
    st.markdown(
        '<div class="side-card"><div class="side-label">GROQ API</div>'
        + ('<div class="online">● Key found in environment</div>' if key_present
           else '<div class="offline">● Key not configured</div>')
        + '<div class="side-small">Model: ' + safe(MODEL_NAME)
        + '<br>Connectivity is confirmed when the AI runs.</div></div>',
        unsafe_allow_html=True,
    )
    if not key_present:
        st.warning("Add GROQ_API_KEY to your .env file for 200+ word AI analysis.")
    st.markdown("##### YOUR WORKFLOW")
    st.markdown("**01**  Input article  ")
    st.markdown("**02**  Extract & clean  ")
    st.markdown("**03**  AI summary  ")
    st.markdown("**04**  News category  ")
    st.markdown("**05**  Execution log  ")
    st.divider()
    st.markdown("##### ROUTING RULE")
    st.caption(f"Under {MIN_WORDS} words → save directly to log. {MIN_WORDS}+ words → summarize, classify, then log.")
    st.markdown("##### LOCAL STORAGE")
    st.caption("Run history is saved to data/news_runs.db. The Groq key is never written to the log.")

st.markdown('''
<div class="hero">
  <div class="eyebrow">AI-POWERED NEWS WORKFLOW</div>
  <h1>News, distilled into insight.</h1>
  <p>Paste a news article or enter a direct article URL. LangGraph handles extraction,
  conditional routing, Groq summarization, classification and complete execution logging.</p>
  <span class="chip">⬡ 5 graph nodes</span>
  <span class="chip">✦ Groq-powered AI</span>
  <span class="chip">◉ 200-word rule</span>
  <span class="chip">▤ SQLite history</span>
</div>
''', unsafe_allow_html=True)

analyze_tab, history_tab, workflow_tab = st.tabs(
    ["✦  Analyze article", "◷  Execution history", "⬡  Workflow graph"]
)

with analyze_tab:
    left, right = st.columns([1.05, .95], gap="large")
    with left:
        section("Add your article", "Use the complete article text or a public URL to a specific news story.")
        mode = st.radio(
            "Input method", ("Paste article text", "Article URL"),
            horizontal=True, key="news_input_method",
        )
        with st.form("news_input_form", border=True, clear_on_submit=False):
            if mode == "Paste article text":
                content = st.text_area(
                    "Article text", placeholder="Paste the full news article here…",
                    height=255, key="news_article_text",
                )
                kind = "text"
                st.caption("Under 200 words: logged without AI analysis. At least 200: summary + category.")
            else:
                content = st.text_input(
                    "Direct article URL", placeholder="https://news-site.com/section/story",
                    key="news_article_url",
                )
                kind = "url"
                st.caption("Use a single article. Google News /home, search pages and news feeds are not articles.")
            submitted = st.form_submit_button("✦  Analyze news", type="primary", use_container_width=True)

        if mode == "Paste article text" and content.strip():
            count = len(content.split())
            pct = min(100, round(100 * count / MIN_WORDS))
            st.markdown(
                '<div class="progress-track"><div class="progress-bar" style="width:'
                + str(pct) + '%"></div></div><div class="progress-caption">'
                + safe(f"Draft: {count} words · Target: {MIN_WORDS} words") + '</div>',
                unsafe_allow_html=True,
            )

        if submitted:
            if not content.strip():
                st.session_state["latest_result"] = None
                st.warning("Enter the article text or an article URL before running the agent.")
            else:
                with st.spinner("Extracting, analyzing and saving execution steps…"):
                    try:
                        st.session_state["latest_result"] = run_agent(kind, content.strip())
                    except Exception as exc:
                        st.session_state["latest_result"] = None
                        st.error(f"Unable to start the workflow: {exc}")

        st.markdown("""<div class="note">🔒 <strong>Your data stays in your local run database.</strong>
        Groq receives the cleaned article text only when the article meets the word threshold.
        Never paste API keys or private documents as article content.</div>""", unsafe_allow_html=True)
    with right:
        section("Analysis result", "Summary, category and a transparent trace of every executed node.")
        result = st.session_state.get("latest_result")
        if result:
            render_result(result)
        else:
            st.markdown('''<div class="empty-card"><div class="empty-icon">🧭</div>
              <h3>Ready when you are</h3>
              <p>Choose your input source and run the agent. Your article summary,
              classification and processing history will appear here.</p></div>''',
              unsafe_allow_html=True)
            st.markdown("#### What happens next")
            st.markdown("🧹 **Clean** the article and calculate the word count.")
            st.markdown("◇ **Route** to AI for 200+ words, or directly to the log.")
            st.markdown("▤ **Save** the result and every execution step locally.")

with history_tab:
    section("Execution history", "Review and export previous runs from your local SQLite database.")
    try:
        stats = get_run_stats()
        history = list_runs(limit=100)
    except Exception as exc:
        stats, history = {}, []
        st.error(f"Unable to read the execution log: {exc}")
    tiles([
        ("TOTAL RUNS", str(stats.get("total", 0)), "big"),
        ("COMPLETED", str(stats.get("completed", 0)), "teal"),
        ("SKIPPED SHORT", str(stats.get("skipped_short", 0)), "amber"),
    ])
    if not history:
        st.info("No executions saved yet. Analyze a news article to create your first log.")
    else:
        status_filter = st.selectbox(
            "Filter history", ("All runs", "Completed", "Skipped short", "Partial", "Errors"),
            key="history_filter",
        )
        filter_key = {"All runs": None, "Completed": "completed", "Skipped short": "skipped_short",
                      "Partial": "partial", "Errors": "error"}[status_filter]
        visible = [r for r in history if filter_key is None or r["status"] == filter_key]
        if not visible:
            st.info("No runs match that filter.")
        else:
            display = [{
                "Date (UTC)": r.get("created_at", "")[:19].replace("T", " "),
                "Status": status_title(r.get("status", ""))[0],
                "Words": r.get("word_count", 0),
                "Category": r.get("category") or "—",
                "Run ID": r.get("run_id", "")[:8],
            } for r in visible]
            st.dataframe(display, hide_index=True, use_container_width=True)
            id_to_record = {r["run_id"]: r for r in visible}
            chosen = st.selectbox(
                "Open saved execution", list(id_to_record),
                format_func=lambda rid: (
                    f"{id_to_record[rid].get('created_at', '')[:19].replace('T', ' ')}"
                    f" · {status_title(id_to_record[rid].get('status',''))[0]}"
                    f" · {rid[:8]}"
                ),
            )
            saved = get_run(chosen)
            if saved:
                a, b = st.columns([1, 1], gap="large")
                with a:
                    st.markdown("**Saved summary**")
                    st.write(saved.get("summary") or "No summary was generated for this execution.")
                    st.caption("Category: " + (saved.get("category") or "Not assigned"))
                with b:
                    st.markdown("**Node execution trace**")
                    node_trace(saved.get("events") or [])
                with st.expander("Inspect complete saved state"):
                    st.json(saved)
                st.download_button(
                    "↓ Download saved record (JSON)",
                    json.dumps(saved, ensure_ascii=False, indent=2),
                    file_name=f"news_run_{chosen}.json", mime="application/json",
                    key=f"history_download_{chosen}",
                )

with workflow_tab:
    section("Five-node LangGraph workflow", "A deterministic graph with one conditional branch after the processing node.")
    st.graphviz_chart(r'''
    digraph G {
      rankdir=LR;
      graph [bgcolor="transparent", pad="0.18", nodesep="0.4", ranksep="0.66", splines=polyline];
      node [shape=box, style="rounded,filled", fillcolor="#1a3047", color="#557790",
            fontcolor="#f2f8ff", fontname="Arial", fontsize=12, margin="0.22,0.16"];
      edge [color="#84b5c7", fontcolor="#bed7e7", fontsize=10, fontname="Arial", arrowsize=0.7];
      input [label="01  Input"];
      processing [label="02  Processing"];
      summary [label="03  Summary"];
      category [label="04  Category"];
      execution_log [label="05  Execution Log", fillcolor="#143d40", color="#48bca9"];
      input -> processing;
      processing -> summary [label="≥ 200 words"];
      processing -> execution_log [label="< 200 words or error", color="#c09b65"];
      summary -> category;
      category -> execution_log;
    }
    ''', use_container_width=True)
    st.info("The decision diamond is a conditional edge, not a sixth node. Exactly 200 words takes the AI path.")
    st.markdown("##### Responsibilities")
    step_texts = [
        ("01 · Input", "Validate pasted text or article URL and record the source."),
        ("02 · Processing", "Fetch article content, remove noise, clean whitespace and count words."),
        ("03 · Summary", "Call Groq to generate a faithful and neutral summary for longer articles."),
        ("04 · Category", "Classify the news into one of the supported categories using Groq."),
        ("05 · Execution Log", "Save full state, errors and ordered node events in SQLite."),
    ]
    for heading, detail in step_texts:
        st.markdown(f"**{heading}** — {detail}")
    st.caption("Supported categories: " + ", ".join(CATEGORIES))

st.markdown('''<div class="footer">NewsLens · LangGraph orchestration · Groq AI ·
SQLite local history · Summaries reflect only supplied content, not independent fact-checking.</div>''',
unsafe_allow_html=True)
