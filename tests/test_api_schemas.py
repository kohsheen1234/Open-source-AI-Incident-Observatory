from agentwatch.api.schemas import Page, ReviewIn, Stats


def test_review_in_requires_decision():
    r = ReviewIn(reviewer="me", decision="accept")
    assert r.notes is None


def test_page_and_stats_construct():
    p = Page(items=[1, 2], total=2, limit=50, offset=0)
    assert p.total == 2
    s = Stats(
        total_incidents=3,
        total_classified=2,
        abstention_rate=0.5,
        by_incident_type={"deception": 1},
    )
    assert s.by_incident_type["deception"] == 1
