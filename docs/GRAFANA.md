# Live Grafana dashboard

The six panels read `data/logs.jsonl` through the read-only `/dashboard/{panel}` API. Every query filters the Grafana time range, so appended workload records become visible on the next 30-second refresh. Existing logs are never reset by dashboard setup.

Start from the repository root:

```bash
.venv/bin/python scripts/build_grafana.py
.venv/bin/uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
docker compose -f compose.grafana.yaml up -d
.venv/bin/python scripts/load_test.py --concurrency 5
```

Open http://127.0.0.1:3000/d/day13-llmops. This Linux setup uses host networking; Grafana and the API bind to localhost. Anonymous access is read-only. Persistent Grafana storage is in a named Docker volume.

Latency, tokens, errors and quality show aggregations over the selected time range. Traffic and cost show minute buckets and window totals. Error rate counts failed requests divided by received requests. Retrieval success counts successful and failed retrieval attempts from terminal events, including `response_sent`; using only the YAML errors event list would omit successful attempts. No observations means no data, rather than invented healthy values.

The YAML alert rules define conditions and runbooks. This setup does not configure a Slack webhook or claim Slack delivery is working.

## Evidence pause before CP3

Keep the API, Grafana, logs and Langfuse observations intact while capturing CP2 evidence. Open your personal Langfuse project in your browser; never open API Keys while capturing.

1. Save `02-trace-list.png` with project name, at least ten traces and timestamps visible.
2. Prepare `04-prompt-versioning.png`: show a trace that used production v2 beside the versions page after production rolled back to v1. Both versions, labels and the trace ID must be readable.
3. Inspect a CP2 waterfall showing `lab-agent-run`, retrieval and generation, with correlation ID and safe usage/cost metadata.
4. Open Grafana with all six panels, time range, units and thresholds visible. Hover a panel title to inspect its threshold description.

The official incident screenshots `01-incident-log.png`, `03-incident-trace.png` and `05-dashboard-incident.png` require CP3 data. A CP2 baseline capture cannot prove the official incident. Keep interim captures outside the final evidence folder, or replace the corresponding capture after CP3. Final submission must contain exactly the five named runtime images.

Do not run the challenge, remove logs, or replace evidence until the student confirms CP2 capture is finished and authorizes CP3.
