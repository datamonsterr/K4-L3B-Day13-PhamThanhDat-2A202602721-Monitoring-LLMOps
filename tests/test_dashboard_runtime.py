import json
from pathlib import Path

import pytest

from app.dashboard import panel_rows
from app.logging_config import scrub_event


def test_queries_use_window_and_retrieval_outcomes(tmp_path: Path):
    path = tmp_path / "logs.jsonl"
    records = [
        {"ts": "2026-09-30T00:00:00Z", "event": "request_received"},
        {"ts": "2026-09-30T00:00:01Z", "event": "response_sent", "latency_ms": 100, "ttft_ms": 10, "tool_name": "retrieval", "tool_success": True, "tokens_in": 12, "tokens_out": 4, "quality_score": .8, "cost_usd": .01},
        {"ts": "2026-09-30T00:00:02Z", "event": "request_received"},
        {"ts": "2026-09-30T00:00:03Z", "event": "request_failed", "tool_name": "retrieval", "tool_success": False, "error_type": "RuntimeError"},
        {"ts": "2026-09-29T00:00:00Z", "event": "response_sent", "latency_ms": 9999},
    ]
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n{")
    start, end = 1790726400000, 1790726460000
    assert panel_rows("errors", start, end, path) == [{"error_rate_pct": 50, "retrieval_success_pct": 50, "errors_RuntimeError": 1}]
    assert panel_rows("latency", start, end, path)[0]["p95"] == 100
    assert panel_rows("tokens", start, end, path) == [{"tokens_in": 12, "tokens_out": 4}]
    assert panel_rows("traffic", start, end, path)[0]["request_count"] == 2
    assert panel_rows("cost", start, end, path)[0]["total_usd"] == pytest.approx(.01)
    assert panel_rows("quality", start, end, path)[0]["quality_mean"] == .8
    assert panel_rows("quality", end, end + 1, path)[0]["quality_mean"] is None


def test_pii_scrubs_nested_context_and_exception():
    event = {"session_id": "person@example.com", "payload": {"nested": ["0901234567"]}, "exception": "person@example.com"}
    scrubbed = scrub_event(None, "error", event)
    assert "person@example.com" not in json.dumps(scrubbed)
    assert "0901234567" not in json.dumps(scrubbed)
