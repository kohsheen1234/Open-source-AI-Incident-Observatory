from agentwatch.hashing import compute_content_hash, hash_author


def test_content_hash_is_deterministic_and_order_independent():
    a = compute_content_hash({"source": "hn", "source_id": "1", "url": "u", "title": "t", "body": "b"})
    b = compute_content_hash({"body": "b", "title": "t", "url": "u", "source_id": "1", "source": "hn"})
    assert a == b
    assert len(a) == 64


def test_content_hash_changes_with_content():
    a = compute_content_hash({"title": "one"})
    b = compute_content_hash({"title": "two"})
    assert a != b


def test_hash_author_salted_and_none_passthrough():
    assert hash_author(None, "salt") is None
    h = hash_author("alice", "salt")
    assert h is not None and len(h) == 64
    assert h != hash_author("alice", "other-salt")
