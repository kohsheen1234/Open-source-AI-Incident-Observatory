"""AgentWatch dashboard — a context-rich, interactive view over the incident API.

Streamlit / pandas / plotly are imported lazily inside functions so importing this
module (e.g. in tests) has no heavy dependencies.
"""

from dashboard.client import AgentWatchClient, APIUnavailable

# Plain-language descriptions of each incident category.
INCIDENT_TYPES = {
    "unauthorized_action": "Took an action it wasn't authorised to take.",
    "resistance_to_correction": "Ignored or resisted instructions to stop.",
    "deception": "Misrepresented what it did or was doing.",
    "goal_persistence": "Kept pursuing a goal after it should have stopped.",
    "privilege_escalation": "Gained access or permissions beyond what it was given.",
    "sandbox_escape": "Broke out of its intended environment.",
    "destructive_action": "Deleted, overwrote, or destroyed something.",
    "resource_acquisition": "Acquired money, compute, or other resources.",
    "harmless_malfunction": "A minor glitch with no real harm.",
    "insufficient_evidence": "Not enough information to decide — the classifier abstained.",
}

MISSION = (
    "As AI systems increasingly **act on their own** — running tools, taking actions, "
    "operating autonomously — people post about what happens when they misbehave. "
    "**AgentWatch turns those scattered, disappearing reports into a durable, "
    "measurable evidence base**, so researchers and safety teams can track how often "
    "these incidents happen, what kinds occur, and how the picture changes over time."
)

# (emoji, title, body) — the pipeline, shown as a visual "how it works" strip.
PIPELINE = [
    ("📥", "Collect", "Public posts pulled from **Hacker News** (live search API), "
     "**Reddit** (optional), and a bundled sample set."),
    ("🔒", "Preserve", "Each post stored verbatim with a **SHA-256 hash**, so evidence "
     "survives even if the original is deleted."),
    ("🧭", "Classify", "An LLM/baseline classifier labels the **incident type**, severity, "
     "and confidence — and **abstains** when unsure."),
    ("✅", "Review", "Machine labels are opinions; a **human** can accept, override, or "
     "reject them. Both are kept."),
]

TYPE_COLORS = {
    "destructive_action": "#e4572e",
    "privilege_escalation": "#f3a712",
    "sandbox_escape": "#d7263d",
    "deception": "#8f2d56",
    "resistance_to_correction": "#3f88c5",
    "unauthorized_action": "#2e86ab",
    "goal_persistence": "#5b8c5a",
    "resource_acquisition": "#8367c7",
    "harmless_malfunction": "#9aa5b1",
    "insufficient_evidence": "#c9ced6",
}

# Severity 1 (minor) → 5 (critical).
SEV_COLORS = {1: "#3ECF8E", 2: "#a3d9b1", 3: "#f3a712", 4: "#e4572e", 5: "#d7263d"}

# Supabase-inspired dark theme injected as CSS.
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, p, span, div { font-family: 'Inter', sans-serif; }
.stApp { background-color: #1C1C1C; }

/* subtle green glow behind the hero */
.stApp::before {
  content: ""; position: fixed; top: -220px; left: 50%; transform: translateX(-50%);
  width: 900px; height: 420px; pointer-events: none; z-index: 0;
  background: radial-gradient(ellipse at center, rgba(62,207,142,0.13), rgba(62,207,142,0) 70%);
}
.block-container { padding-top: 2.2rem; }
h1, h2, h3, h4 { font-family: 'Inter', sans-serif; letter-spacing: -0.02em; font-weight: 700; }
h1 { color: #FFFFFF; }

/* metric cards */
[data-testid="stMetric"] {
  background: #181818; border: 1px solid #2E2E2E; border-radius: 12px; padding: 14px 18px;
}
[data-testid="stMetricLabel"] p {
  color: #A0A0A0; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
  text-transform: uppercase; letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] { color: #EDEDED; font-weight: 700; }

/* sidebar */
[data-testid="stSidebar"] { background: #171717; border-right: 1px solid #2E2E2E; }
[data-testid="stSidebar"] .stRadio label { color: #EDEDED; }

/* buttons */
.stButton > button {
  background: #3ECF8E; color: #0B0F0D; border: none; border-radius: 8px; font-weight: 600;
}
.stButton > button:hover { background: #34B87C; color: #0B0F0D; }

/* links, dividers, tabs, expanders */
a, a:visited { color: #3ECF8E !important; }
hr { border-color: #2E2E2E; }
[data-testid="stExpander"] { border: 1px solid #2E2E2E; border-radius: 10px; background: #181818; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [aria-selected="true"] { color: #3ECF8E; }
[data-testid="stDataFrame"] { border: 1px solid #2E2E2E; border-radius: 10px; }

/* caption tint */
[data-testid="stCaptionContainer"], .stCaption { color: #8B8B8B; }

/* monospace green eyebrow */
.aw-eyebrow {
  font-family: 'JetBrains Mono', ui-monospace, monospace; color: #3ECF8E;
  font-size: 0.78rem; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 500;
}
</style>
"""


def _style_fig(fig, height: int = 340):
    """Apply the dark Supabase-style chart theme."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#EDEDED", family="Inter"),
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    fig.update_xaxes(gridcolor="#2E2E2E", zerolinecolor="#2E2E2E")
    fig.update_yaxes(gridcolor="#2E2E2E", zerolinecolor="#2E2E2E")
    return fig


def _clean_text(s: str | None) -> str:
    """Strip HTML tags/entities from source text (e.g. Hacker News) for display."""
    import html as _html
    import re

    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", _html.unescape(s)).strip()


def _pill(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:12px;'
        f'font-size:0.82em;font-weight:600;white-space:nowrap;">{text}</span>'
    )


def _type_badge(itype: str | None) -> str:
    if not itype:
        return _pill("unclassified", "#9aa5b1")
    return _pill(itype, TYPE_COLORS.get(itype, "#6c757d"))


def _severity_chip(sev) -> str:
    if sev is None or (isinstance(sev, float) and sev != sev):  # None / NaN
        return _pill("severity —", "#9aa5b1")
    sev = int(sev)
    return _pill(f"severity {sev}/5", SEV_COLORS.get(sev, "#6c757d"))


# ----------------------------------------------------------------------------- data


def _load_df(api, **filters):
    import pandas as pd

    data = api.incidents(limit=500, **filters)
    rows = []
    for it in data["items"]:
        c = it.get("classification") or {}
        rows.append(
            {
                "id": it["id"],
                "source": it["source"],
                "title": it["title"],
                "url": it["url"],
                "published_at": it.get("published_at"),
                "type": c.get("incident_type"),
                "severity": c.get("severity"),
                "confidence": c.get("confidence"),
                "abstained": c.get("abstained"),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty and "published_at" in df:
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    return df, data["total"]


# --------------------------------------------------------------------------- layout


def _sidebar(st):
    st.sidebar.title("🔭 AgentWatch")
    st.sidebar.caption("Observatory for public AI-agent incidents")
    page = st.sidebar.radio("View", ["Overview", "Incident Explorer", "Review Queue"])
    st.sidebar.markdown("---")
    with st.sidebar.expander("Where does the data come from?", expanded=False):
        st.markdown(
            "**Live sources**\n"
            "- **Hacker News** — public [Algolia search API](https://hn.algolia.com)\n"
            "- **Reddit** — optional (needs API credentials)\n"
            "- **Replay** — a bundled sample set so it runs with no keys\n\n"
            "Each item is hashed and stored, then classified. This is a **demo instance**; "
            "classifications are automated and **unverified** until reviewed."
        )
    st.sidebar.markdown(
        "[📖 Docs](https://kohsheen1234.github.io/Open-source-AI-Incident-Observatory/) · "
        "[💻 Code](https://github.com/kohsheen1234/Open-source-AI-Incident-Observatory)"
    )
    return page


def _pipeline_strip(st):
    cols = st.columns(len(PIPELINE))
    for col, (emoji, title, body) in zip(cols, PIPELINE, strict=False):
        with col:
            st.markdown(f"### {emoji}")
            st.markdown(f"**{title}**")
            st.caption(body)


def _glossary(st):
    with st.expander("What do the incident types mean?"):
        for name, desc in INCIDENT_TYPES.items():
            st.markdown(f"- **{name}** — {desc}")


# ---------------------------------------------------------------------------- pages


def _render_overview(st, api):
    import plotly.express as px

    st.markdown('<div class="aw-eyebrow">Live · AI-agent incident monitoring</div>',
                unsafe_allow_html=True)
    st.markdown(MISSION)
    st.markdown("#### How it works")
    _pipeline_strip(st)
    st.divider()

    stats = api.stats()
    df, total = _load_df(api)

    n_sources = df["source"].nunique() if not df.empty else 0
    avg_sev = (
        round(float(df["severity"].dropna().mean()), 1)
        if not df.empty and df["severity"].notna().any()
        else "—"
    )
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Incidents", stats["total_incidents"], help="Public posts collected.")
    k2.metric("Classified", stats["total_classified"], help="Incidents labelled by the classifier.")
    k3.metric("Abstention", f"{stats['abstention_rate']:.0%}",
              help="Share marked 'insufficient evidence' rather than guessed.")
    k4.metric("Sources", n_sources, help="Distinct data sources represented.")
    k5.metric("Avg severity", avg_sev, help="Mean severity (1–5) of classified incidents.")

    if df.empty:
        st.info("No incidents yet. Seed with `agentwatch collect` + `agentwatch classify`.")
        return

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Incidents by type")
        counts = df["type"].value_counts().reset_index()
        counts.columns = ["type", "count"]
        fig = px.bar(
            counts, x="count", y="type", orientation="h",
            color="type", color_discrete_map=TYPE_COLORS,
        )
        _style_fig(fig, height=380)
        fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="incidents")
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("By source")
        src = df["source"].value_counts().reset_index()
        src.columns = ["source", "count"]
        fig = px.pie(src, names="source", values="count", hole=0.55,
                     color_discrete_sequence=["#3ECF8E", "#3f88c5", "#f3a712", "#8367c7"])
        _style_fig(fig, height=380)
        fig.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)

    tab_time, tab_sev, tab_conf, tab_mix, tab_scatter = st.tabs(
        ["📈 Over time", "🔥 Severity", "🎯 Confidence", "🌳 Type mix", "⚖️ Confidence × severity"]
    )
    with tab_time:
        st.caption("When the underlying posts were published.")
        ts = df.dropna(subset=["published_at"]).copy()
        if ts.empty:
            st.info("No publication dates available.")
        else:
            ts["date"] = ts["published_at"].dt.date
            series = ts.groupby("date").size().reset_index(name="incidents")
            fig = px.area(series, x="date", y="incidents", markers=True)
            fig.update_traces(line_color="#3ECF8E", fillcolor="rgba(62,207,142,0.15)")
            _style_fig(fig, height=320)
            fig.update_layout(xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
    with tab_sev:
        st.caption("How severe the classified incidents are (1 = minor, 5 = critical).")
        sev = df.dropna(subset=["severity"])
        if sev.empty:
            st.info("No severities yet.")
        else:
            sc = sev["severity"].astype(int).value_counts().sort_index().reset_index()
            sc.columns = ["severity", "count"]
            fig = px.bar(sc, x="severity", y="count", color="severity",
                         color_continuous_scale="OrRd")
            _style_fig(fig, height=320)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    with tab_conf:
        st.caption("How confident the classifier was. Low-confidence items are worth reviewing.")
        conf = df.dropna(subset=["confidence"])
        if conf.empty:
            st.info("No confidence values yet.")
        else:
            fig = px.histogram(conf, x="confidence", nbins=20)
            fig.update_traces(marker_color="#3ECF8E")
            _style_fig(fig, height=320)
            fig.update_layout(yaxis_title="incidents")
            st.plotly_chart(fig, use_container_width=True)
    with tab_mix:
        st.caption("The relative mix of incident types — area is proportional to count.")
        counts2 = df["type"].value_counts().reset_index()
        counts2.columns = ["type", "count"]
        fig = px.treemap(counts2, path=["type"], values="count",
                         color="type", color_discrete_map=TYPE_COLORS)
        _style_fig(fig, height=360)
        st.plotly_chart(fig, use_container_width=True)
    with tab_scatter:
        st.caption(
            "Each dot is an incident. Bottom-left (low confidence, high severity) is where "
            "human review matters most."
        )
        sc = df.dropna(subset=["severity", "confidence"])
        if sc.empty:
            st.info("Not enough classified data yet.")
        else:
            fig = px.scatter(
                sc, x="confidence", y="severity", color="type",
                color_discrete_map=TYPE_COLORS, hover_data=["title"],
            )
            fig.update_traces(marker=dict(size=12, opacity=0.8))
            _style_fig(fig, height=360)
            fig.update_layout(legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"Charts based on the latest {len(df)} of {total} incidents · "
        "data from Hacker News + bundled sample · classified by the baseline classifier."
    )
    _glossary(st)


def _styled_table(st, view):
    if view.empty:
        st.info("No incidents match the current filters.")
        return
    disp = view[["id", "type", "severity", "confidence", "source", "title", "url"]].copy()

    def _sty_type(v):
        c = TYPE_COLORS.get(v, "")
        return f"background-color:{c};color:white" if c else ""

    def _sty_sev(v):
        try:
            c = SEV_COLORS.get(int(v), "")
        except (TypeError, ValueError):
            c = ""
        return f"background-color:{c};color:white" if c else ""

    styler = disp.style.map(_sty_type, subset=["type"]).map(_sty_sev, subset=["severity"])
    st.dataframe(
        styler,
        use_container_width=True,
        hide_index=True,
        column_config={
            "confidence": st.column_config.ProgressColumn(
                "confidence", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "severity": st.column_config.NumberColumn("severity", format="%d"),
            "url": st.column_config.LinkColumn("link", display_text="open ↗"),
            "title": st.column_config.TextColumn("title", width="large"),
        },
    )


def _classification_badges(st, cls: dict) -> None:
    if not cls:
        st.markdown(_pill("unclassified", "#9aa5b1"), unsafe_allow_html=True)
        return
    conf = cls.get("confidence")
    conf_s = f"{conf:.0%}" if isinstance(conf, (int, float)) else "—"
    badges = " &nbsp; ".join(
        [
            _type_badge(cls.get("incident_type")),
            _severity_chip(cls.get("severity")),
            _pill(f"confidence {conf_s}", "#3f88c5"),
            _pill(f"model {cls.get('model_name', '—')}", "#495057"),
        ]
    )
    if cls.get("abstained"):
        badges += " &nbsp; " + _pill("abstained", "#6c757d")
    st.markdown(badges, unsafe_allow_html=True)


def _render_explorer(st, api):
    st.subheader("Incident Explorer")
    st.markdown("Browse and filter every collected incident. **Each row is a real public post.**")

    c1, c2, c3 = st.columns(3)
    itype = c1.selectbox("Incident type", ["(all)", *INCIDENT_TYPES.keys()])
    ftype = None if itype == "(all)" else itype
    df, total = _load_df(api, incident_type=ftype)

    if not df.empty:
        sources = sorted(s for s in df["source"].unique())
        chosen = c2.multiselect("Source", sources, default=sources)
        min_conf = c3.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)
        search = st.text_input("Search title", "")
        view = df[df["source"].isin(chosen)]
        view = view[(view["confidence"].fillna(0) >= min_conf)]
        if search:
            view = view[view["title"].str.contains(search, case=False, na=False)]
    else:
        view = df

    st.caption(f"Showing {len(view)} of {total} incidents.")
    _styled_table(st, view)

    st.markdown("### 🔎 Inspect an incident")
    st.caption("See the original evidence and why it was classified.")
    options = {f"#{r.id} — {str(r.title)[:70]}": int(r.id) for r in view.itertuples()}
    if options:
        label = st.selectbox("Incident", list(options), key="explore")
        _show_detail(st, api, options[label])


def _show_detail(st, api, incident_id: int):
    detail = api.incident(incident_id)
    st.markdown(f"**{detail.get('title', '')}**")
    if detail.get("url"):
        st.markdown(f"[View original post ↗]({detail['url']})")
    cls = detail.get("classification") or {}
    _classification_badges(st, cls)
    if cls.get("reasoning_summary"):
        st.info(f"Classifier reasoning: {cls['reasoning_summary']}")
    with st.expander("Evidence (original text)"):
        st.write(_clean_text(detail.get("body")) or "(no body text)")


def _render_review(st, api):
    st.subheader("Review Queue")
    st.markdown(
        "Human-in-the-loop review. The classifier's label is a machine **opinion**; here a "
        "person **accepts**, **overrides**, or flags it as a **false positive**. Both are "
        "kept, so the classifier's accuracy can be measured over time."
    )
    data = api.incidents(limit=200)
    options = {f"#{i['id']} — {i['title'][:70]}": i["id"] for i in data["items"]}
    if not options:
        st.info("No incidents yet. Seed with `agentwatch collect` and `agentwatch classify`.")
        return
    label = st.selectbox("Incident to review", list(options))
    incident_id = options[label]
    detail = api.incident(incident_id)

    st.markdown("#### Evidence")
    if detail.get("url"):
        st.markdown(f"[View original post ↗]({detail['url']})")
    st.write(_clean_text(detail.get("body")) or "(no body text)")

    st.markdown("#### Machine classification")
    cls = detail.get("classification") or {}
    _classification_badges(st, cls)
    if cls.get("reasoning_summary"):
        st.info(f"Classifier reasoning: {cls['reasoning_summary']}")

    st.markdown("#### Your review")
    reviewer = st.text_input("Reviewer", value="reviewer")
    decision = st.selectbox(
        "Decision", ["accept", "override", "false_positive"],
        help="accept = label is right · override = wrong type · false_positive = not an incident",
    )
    notes = st.text_area("Notes (optional)")
    if st.button("Submit review", type="primary"):
        api.review(incident_id, reviewer=reviewer, decision=decision, notes=notes or None)
        st.success("Review saved and attached to this incident's classification.")


def render() -> None:
    import streamlit as st

    st.set_page_config(page_title="AgentWatch — AI Incident Observatory", page_icon="🔭",
                       layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)
    api = AgentWatchClient()
    page = _sidebar(st)
    st.title("AgentWatch — AI Incident Observatory")

    # Both the dashboard and API sleep on Render's free tier. On the first load after
    # idle, patiently wait (with a spinner) for the API to wake instead of erroring out.
    with st.spinner(
        "Connecting to the API… first load after idle can take up to ~60s while "
        "Render's free tier wakes the service. Thanks for your patience!"
    ):
        ready = api.wait_until_ready(timeout=75)

    if not ready:
        st.warning(
            "⏳ The API is still waking up (Render free-tier cold start). It should be "
            "ready in a few more seconds — please retry."
        )
        if st.button("Retry"):
            st.rerun()
        return

    try:
        if page == "Overview":
            _render_overview(st, api)
        elif page == "Incident Explorer":
            _render_explorer(st, api)
        elif page == "Review Queue":
            _render_review(st, api)
    except APIUnavailable:
        st.warning("⏳ The API stopped responding mid-request. Please retry.")
        if st.button("Retry"):
            st.rerun()


if __name__ == "__main__":
    render()
