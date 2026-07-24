from dashboard.client import AgentWatchClient, APIUnavailable

# Plain-language descriptions of each incident category, shown in the UI so a
# first-time visitor understands what the labels mean.
INCIDENT_TYPES = {
    "unauthorized_action": "The agent took an action it wasn't authorised to take.",
    "resistance_to_correction": "The agent ignored or resisted instructions to stop.",
    "deception": "The agent misrepresented what it did or was doing.",
    "goal_persistence": "The agent kept pursuing a goal after it should have stopped.",
    "privilege_escalation": "The agent gained access or permissions beyond what it was given.",
    "sandbox_escape": "The agent broke out of its intended environment.",
    "destructive_action": "The agent deleted, overwrote, or destroyed something.",
    "resource_acquisition": "The agent acquired money, compute, or other resources.",
    "harmless_malfunction": "A minor glitch with no real harm.",
    "insufficient_evidence": "Not enough information to decide — the classifier abstained.",
}

INTRO = (
    "**AgentWatch** collects public reports of AI-agent incidents (an agent deleting "
    "files, ignoring instructions, acting without permission, behaving deceptively…), "
    "preserves each as tamper-evident evidence, and **classifies** it into an incident "
    "type. Machine labels are treated as opinions — a human **review** step can accept, "
    "override, or reject them."
)


def _sidebar(st):
    st.sidebar.title("🔭 AgentWatch")
    st.sidebar.caption("Observatory for public AI-agent incidents")
    page = st.sidebar.radio("View", ["Overview", "Incident Explorer", "Review Queue"])
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ About this dashboard", expanded=False):
        st.markdown(
            "This is a **demo instance**. Incidents are collected from public sources "
            "(Hacker News and a bundled sample set) and classified automatically by a "
            "pluggable classifier.\n\n"
            "**Classifications are automated and unverified** — the Review Queue is where "
            "a human checks them.\n\n"
            "- [Documentation](https://kohsheen1234.github.io/Open-source-AI-Incident-Observatory/)\n"
            "- [Source code](https://github.com/kohsheen1234/Open-source-AI-Incident-Observatory)"
        )
    return page


def _type_glossary(st):
    with st.expander("What do these incident types mean?"):
        for name, desc in INCIDENT_TYPES.items():
            st.markdown(f"- **{name}** — {desc}")


def _render_overview(st, api):
    st.subheader("Overview")
    st.markdown(INTRO)
    stats = api.stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("Incidents", stats["total_incidents"],
                help="Public posts collected as potential AI-agent incidents.")
    col2.metric("Classified", stats["total_classified"],
                help="Incidents the classifier has labelled.")
    col3.metric("Abstention rate", f"{stats['abstention_rate']:.0%}",
                help="Share the classifier marked 'insufficient evidence' rather than guessing.")

    st.markdown("### Incidents by type")
    st.caption(
        "How many incidents fall into each category. `insufficient_evidence` means the "
        "classifier abstained instead of guessing."
    )
    if stats["by_incident_type"]:
        st.bar_chart(stats["by_incident_type"])
    else:
        st.info("No incidents yet.")
    _type_glossary(st)


def _classification_caption(cls: dict) -> str:
    if not cls:
        return "Not yet classified."
    conf = cls.get("confidence")
    conf_s = f"{conf:.0%}" if isinstance(conf, (int, float)) else "—"
    return (
        f"**{cls.get('incident_type')}** · severity {cls.get('severity') or '—'} · "
        f"confidence {conf_s} · model `{cls.get('model_name')}`"
    )


def _render_explorer(st, api):
    st.subheader("Incident Explorer")
    st.markdown(
        "Every collected incident with its most recent classification. **Each row is a "
        "real public post.** Use the filter to focus on one incident type."
    )
    incident_type = st.sidebar.selectbox(
        "Filter by incident type", ["(all)", *INCIDENT_TYPES.keys()]
    )
    ftype = None if incident_type == "(all)" else incident_type
    data = api.incidents(incident_type=ftype, limit=200)
    st.caption(f"Showing {len(data['items'])} of {data['total']} incidents.")
    st.dataframe(
        [
            {
                "id": item["id"],
                "source": item["source"],
                "title": item["title"],
                "type": (item["classification"] or {}).get("incident_type"),
                "severity": (item["classification"] or {}).get("severity"),
                "confidence": (item["classification"] or {}).get("confidence"),
                "link": item["url"],
            }
            for item in data["items"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### 🔎 Inspect an incident")
    st.caption("Pick an incident to see the original evidence and why it was classified.")
    options = {f"#{i['id']} — {i['title'][:70]}": i["id"] for i in data["items"]}
    if options:
        label = st.selectbox("Incident", list(options), key="explore")
        _show_detail(st, api, options[label])


def _show_detail(st, api, incident_id: int):
    detail = api.incident(incident_id)
    st.markdown(f"**{detail.get('title', '')}**")
    if detail.get("url"):
        st.markdown(f"[View original post]({detail['url']})")
    cls = detail.get("classification") or {}
    st.markdown(_classification_caption(cls))
    if cls.get("reasoning_summary"):
        st.info(f"Classifier reasoning: {cls['reasoning_summary']}")
    with st.expander("Evidence (original text)"):
        st.write(detail.get("body") or "(no body text)")


def _render_review(st, api):
    st.subheader("Review Queue")
    st.markdown(
        "Human-in-the-loop review. The classifier's label is a machine **opinion**; here "
        "a person **accepts**, **overrides**, or flags it as a **false positive**. Both the "
        "machine label and the human decision are kept, so the classifier's accuracy can "
        "be measured over time."
    )
    data = api.incidents(limit=200)
    options = {f"#{i['id']} — {i['title'][:70]}": i["id"] for i in data["items"]}
    if not options:
        st.info("No incidents yet. Seed some with `agentwatch collect` and `agentwatch classify`.")
        return
    label = st.selectbox("Incident to review", list(options))
    incident_id = options[label]
    detail = api.incident(incident_id)

    st.markdown("#### Evidence")
    if detail.get("url"):
        st.markdown(f"[View original post]({detail['url']})")
    st.write(detail.get("body") or "(no body text)")

    st.markdown("#### Machine classification")
    cls = detail.get("classification") or {}
    st.markdown(_classification_caption(cls))
    if cls.get("reasoning_summary"):
        st.info(f"Classifier reasoning: {cls['reasoning_summary']}")

    st.markdown("#### Your review")
    reviewer = st.text_input("Reviewer", value="reviewer")
    decision = st.selectbox(
        "Decision",
        ["accept", "override", "false_positive"],
        help="accept = label is right · override = wrong type · false_positive = not an incident",
    )
    notes = st.text_area("Notes (optional)")
    if st.button("Submit review"):
        api.review(incident_id, reviewer=reviewer, decision=decision, notes=notes or None)
        st.success("Review saved. It's now attached to this incident's classification.")


def render() -> None:
    import streamlit as st

    st.set_page_config(page_title="AgentWatch — AI Incident Observatory", layout="wide")
    api = AgentWatchClient()
    page = _sidebar(st)
    st.title("AgentWatch — AI Incident Observatory")

    try:
        if page == "Overview":
            _render_overview(st, api)
        elif page == "Incident Explorer":
            _render_explorer(st, api)
        elif page == "Review Queue":
            _render_review(st, api)
    except APIUnavailable:
        st.warning(
            "⏳ The API isn't responding yet. This demo runs on Render's free tier, "
            "where services sleep after ~15 minutes of inactivity and take 30–60s to "
            "wake up. Give it a moment and retry."
        )
        if st.button("Retry"):
            st.rerun()


if __name__ == "__main__":
    render()
