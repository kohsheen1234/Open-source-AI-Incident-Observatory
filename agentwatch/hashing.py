import hashlib
import json
from collections.abc import Mapping
from typing import Any


def compute_content_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_author(author: str | None, salt: str) -> str | None:
    if author is None:
        return None
    return hashlib.sha256(f"{salt}:{author}".encode()).hexdigest()
