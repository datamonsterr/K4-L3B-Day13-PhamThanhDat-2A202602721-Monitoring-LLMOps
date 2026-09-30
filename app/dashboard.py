"""Read-only, time-filtered Grafana queries over the canonical JSONL log."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .logging_config import LOG_PATH


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def panel_rows(panel: str, start: int, end: int, path: Path = LOG_PATH) -> list[dict]:
    records = []
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    record = json.loads(line)
                    timestamp = int(datetime.fromisoformat(record["ts"].replace("Z", "+00:00")).timestamp() * 1000)
                except (ValueError, KeyError, TypeError):
                    continue  # A concurrent writer may not have finished the last line.
                if start <= timestamp < end:
                    records.append((timestamp, record))
    received = [r for _, r in records if r.get("event") == "request_received"]
    responses = [r for _, r in records if r.get("event") == "response_sent"]
    failures = [r for _, r in records if r.get("event") == "request_failed"]
    if panel == "latency":
        values = [r["latency_ms"] for r in responses if isinstance(r.get("latency_ms"), (int, float))]
        ttft = [r["ttft_ms"] for r in responses if isinstance(r.get("ttft_ms"), (int, float))]
        return [{"p50": percentile(values, .5), "p95": percentile(values, .95), "p99": percentile(values, .99), "ttft_p95": percentile(ttft, .95)}]
    if panel == "errors":
        tools = [r for r in responses + failures if r.get("tool_name") == "retrieval" and isinstance(r.get("tool_success"), bool)]
        row = {"error_rate_pct": 100 * len(failures) / len(received) if received else None,
               "retrieval_success_pct": 100 * sum(r["tool_success"] for r in tools) / len(tools) if tools else None}
        row.update({f"errors_{name}": count for name, count in Counter(r.get("error_type", "unknown") for r in failures).items()})
        return [row]
    if panel == "tokens":
        return [{field: sum(r.get(field, 0) for r in responses) if responses else None for field in ("tokens_in", "tokens_out")}]
    if panel == "quality":
        values = [r["quality_score"] for r in responses if isinstance(r.get("quality_score"), (int, float))]
        return [{"quality_mean": sum(values) / len(values) if values else None}]
    buckets: dict[int, float] = {}
    for timestamp, record in records:
        if record.get("event") == ("request_received" if panel == "traffic" else "response_sent"):
            minute = timestamp // 60000 * 60000
            buckets[minute] = buckets.get(minute, 0) + (1 if panel == "traffic" else record.get("cost_usd", 0))
    total = sum(buckets.values())
    return [{"time": minute, "requests_per_minute" if panel == "traffic" else "cost_usd": value,
             "request_count" if panel == "traffic" else "total_usd": total}
            for minute, value in sorted(buckets.items())]
