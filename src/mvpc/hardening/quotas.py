"""Layer 2b: resource quotas for sandboxed solver subprocesses."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class ResourceQuota:
    timeout_seconds: float = 30.0
    max_memory_mb: int = 512
    max_output_bytes: int = 2_000_000


class QuotaExceeded(Exception):
    pass


def enforce_quota_timeout(fn: Callable[[], T], quota: ResourceQuota) -> T:
    start = time.monotonic()
    result = fn()
    elapsed = time.monotonic() - start
    if elapsed > quota.timeout_seconds:
        raise QuotaExceeded(f"exceeded {quota.timeout_seconds}s (took {elapsed:.3f}s)")
    return result


def truncate_output(text: str, quota: ResourceQuota) -> str:
    raw = text.encode("utf-8", errors="replace")
    if len(raw) <= quota.max_output_bytes:
        return text
    return raw[: quota.max_output_bytes].decode("utf-8", errors="replace") + "\n...[truncated]"
