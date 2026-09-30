"""Generate a provisioned six-panel dashboard from config/dashboard.yaml."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def build():
    contract = yaml.safe_load((ROOT / "config/dashboard.yaml").read_text())["dashboard"]
    panels = []
    units = {"ms": "ms", "requests_per_minute": "reqpm", "percent": "percent", "usd": "currencyUSD", "tokens": "short", "score_0_to_1": "none"}
    for index, definition in enumerate(contract["panels"]):
        name = definition["id"]
        threshold = definition["threshold"]
        good = "green" if threshold["operator"] == "lte" else "red"
        bad = "red" if good == "green" else "green"
        panel = {
            "id": index + 1, "title": definition["title"], "type": "stat",
            "description": f"Source: data/logs.jsonl. Window aggregation. Threshold: {threshold['aggregation']} {threshold['operator']} {threshold['value']}. " + ("Retrieval denominator includes successful responses and failed retrieval attempts. Error counts use requests as denominator." if name == "errors" else definition["query"]),
            "gridPos": {"x": (index % 3) * 8, "y": (index // 3) * 10, "w": 8, "h": 10},
            "datasource": {"type": "yesoreyeram-infinity-datasource", "uid": "day13-logs"},
            "targets": [{"refId": "A", "type": "json", "source": "url", "parser": "uql", "uql": "parse-json", "url": f"http://127.0.0.1:8000/dashboard/{name}?start=${{__from}}&end=${{__to}}", "url_options": {"method": "GET", "data": ""}, "root_selector": "", "columns": []}],
            "fieldConfig": {"defaults": {"unit": units[definition["unit"]], "thresholds": {"mode": "absolute", "steps": [{"color": good, "value": None}, {"color": bad, "value": threshold["value"]}]}}, "overrides": []},
            "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "colorMode": "value", "graphMode": "none", "textMode": "value_and_name"},
        }
        if name == "errors":
            panel["fieldConfig"]["overrides"] = [{"matcher": {"id": "byName", "options": "retrieval_success_pct"}, "properties": [{"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 90}]}}]}, {"matcher": {"id": "byRegexp", "options": "^errors_"}, "properties": [{"id": "unit", "value": "short"}]}]
        if name in ("traffic", "cost"):
            panel["type"] = "timeseries"
            panel["targets"][0]["columns"] = [{"selector": "time", "text": "Time", "type": "timestamp_epoch"}, {"selector": "requests_per_minute" if name == "traffic" else "cost_usd", "text": "Requests/min" if name == "traffic" else "Cost/min", "type": "number"}, {"selector": "request_count" if name == "traffic" else "total_usd", "text": "Window request count" if name == "traffic" else "Window total USD", "type": "number"}]
            panel["options"] = {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["lastNotNull"]}, "tooltip": {"mode": "multi"}}
            panel["fieldConfig"]["defaults"]["custom"] = {"thresholdsStyle": {"mode": "line"}, "drawStyle": "line", "showPoints": "always"}
            if name == "traffic":
                panel["fieldConfig"]["overrides"] = [{"matcher": {"id": "byName", "options": "Window request count"}, "properties": [{"id": "unit", "value": "short"}]}]
        panels.append(panel)
    dashboard = {"uid": "day13-llmops", "title": contract["title"], "schemaVersion": 39, "version": 1, "refresh": "30s", "time": {"from": "now-60m", "to": "now"}, "timezone": "browser", "panels": panels, "tags": ["CP2", "JSONL", "K4-L3B"]}
    destination = ROOT / "config/grafana/dashboards/day13.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dashboard, indent=2) + "\n")
    print(f"Generated {len(panels)} panels: {destination}")


if __name__ == "__main__":
    build()
