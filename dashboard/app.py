from dashboard.client import AgentWatchClient


def render() -> None:
    import streamlit as st

    st.set_page_config(page_title="AgentWatch", layout="wide")
    st.title("AgentWatch — AI Incident Observatory")

    api = AgentWatchClient()
    page = st.sidebar.radio("View", ["Overview", "Incident Explorer", "Review Queue"])

    if page == "Overview":
        stats = api.stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Incidents", stats["total_incidents"])
        col2.metric("Classified", stats["total_classified"])
        col3.metric("Abstention rate", f"{stats['abstention_rate']:.0%}")
        st.subheader("By incident type")
        st.bar_chart(stats["by_incident_type"])

    elif page == "Incident Explorer":
        incident_type = st.sidebar.text_input("Incident type filter") or None
        data = api.incidents(incident_type=incident_type, limit=200)
        st.caption(f"{data['total']} incidents")
        st.dataframe(
            [
                {
                    "id": item["id"],
                    "source": item["source"],
                    "title": item["title"],
                    "type": (item["classification"] or {}).get("incident_type"),
                    "severity": (item["classification"] or {}).get("severity"),
                    "confidence": (item["classification"] or {}).get("confidence"),
                }
                for item in data["items"]
            ],
            use_container_width=True,
        )

    elif page == "Review Queue":
        data = api.incidents(limit=200)
        options = {f"#{i['id']} — {i['title'][:60]}": i["id"] for i in data["items"]}
        if not options:
            st.info("No incidents yet. Run `agentwatch collect` and `agentwatch classify`.")
            return
        label = st.selectbox("Incident", list(options))
        incident_id = options[label]
        detail = api.incident(incident_id)
        st.write(detail.get("body", ""))
        st.json(detail.get("classification") or {})
        reviewer = st.text_input("Reviewer", value="reviewer")
        decision = st.selectbox("Decision", ["accept", "override", "false_positive"])
        notes = st.text_area("Notes")
        if st.button("Submit review"):
            api.review(incident_id, reviewer=reviewer, decision=decision, notes=notes or None)
            st.success("Review saved.")


if __name__ == "__main__":
    render()
