# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Phạm Thanh Dat
- **MSSV:** 2A202602721
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/datamonsterr/K4-L3B-Day13-PhamThanhDat-2A202602721-Monitoring-LLMOps
- **Commit SHA cuối:** 6165a607f65eef0e20837cd2fa8527162eb18dda
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602721`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/pytest.txt` |
| Log validator | `evidence/log-validator.txt` |
| Dashboard validator | `evidence/dashboard-validator.txt` |
| Structured log + incident log | `evidence/01-incident-log.png` |
| Trace list | `evidence/02-trace-list.png` |
| Trace waterfall + metadata + incident trace | `evidence/03-incident-trace.png` |
| Prompt versions + promote/rollback | `evidence/04-prompt-versioning.png` |
| Dashboard + incident metric | `evidence/05-dashboard-incident.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 0/100 (chưa implement) | 100/100 | Đạt chuẩn JSON schema, correlation propagation, context enrichment & PII scrubbing |
| `validate_dashboard.py` | 0/6 panel | 6/6 panel | Đủ 6 panel theo hợp đồng `config/dashboard.yaml` |
| `pytest` | 24 passed | 26 passed | Pass toàn bộ test suite bao gồm test mở rộng |
| Số traces hợp lệ | 0 | > 50 traces | Tạo thành công trên Langfuse cá nhân `day13-k4-l3b-2A202602721` |
| Số PII leak | 4 phát hiện (mẫu) | 0 leak | Toàn bộ Phone, Email, CCCD, Credit Card đều được scrub sang `[REDACTED_...]` |
| Latency P95 / TTFT P95 | ~152ms / 50ms | 2.65s / 50ms (Challenge) | Phản ánh chính xác hiện tượng suy giảm hiệu năng do sự cố RAG |
| Retrieval success rate | 100% | 100% | Toàn bộ quá trình retrieval hoạt động thông suốt, không timeout |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  - Nhận qua header `x-request-id` dạng `req-<8-hex>`. Nếu thiếu hoặc sai định dạng, `CorrelationIdMiddleware` tự sinh một ID mới bằng `uuid.uuid4().hex[:8]`.
  - Context được bind vào `structlog.contextvars` trước mỗi request và clear sạch sau khi hoàn thành.
  - Correlation ID được trả về trong header phản hồi `x-request-id` và truyền sang Langfuse metadata.
- **Các metadata được ghi vào structured log:**
  - `ts`, `level`, `service`, `event`, `correlation_id`, `user_id_hash` (SHA256 băm 12 ký tự), `session_id`, `feature`, `model`, `env`, cùng với `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `trace_id`.
- **Cách bảo đảm PII được scrub trước khi ghi:**
  - Đăng ký processor `scrub_pii_processor` trong pipeline của `structlog` trước khi chuyển sang JSON renderer / file writer.
  - Sử dụng Regex an toàn che giấu đệ quy toàn bộ chuỗi Email, Số điện thoại VN (`0x` hoặc `+84x`), CCCD (12 số), Số thẻ tín dụng (13-19 số).
- **Cách kiểm chứng kết quả:**
  - Chạy `python scripts/validate_logs.py` đạt điểm số 100/100, 0 PII leak trên toàn bộ file log `data/logs.jsonl`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  - Tự cấu hình API key cá nhân vào `.env` trỏ về project `day13-k4-l3b-2A202602721`.
  - Toàn bộ trace hiển thị tags `lab`, `monitoring`/`qa`/`summary`, `claude-sonnet-4-5` cùng metadata `correlation_id` khớp với log cục bộ.
- **Cấu trúc root/retrieval/generation observations:**
  - Root span: `lab-agent-run` (type: `agent`).
  - Child span 1: `retrieve` (type: `retriever`) đo đạc việc trích xuất văn bản corpus.
  - Child span 2: `generation` (type: `generation`) ghi nhận model, input tokens, output tokens, cost details và latency/TTFT.
- **Cách nối trace với log:**
  - Cả structured log và trace cùng chứa chung trường metadata `correlation_id: req-...`. Trường `trace_id` của Langfuse cũng được lưu trực tiếp vào event log `response_sent`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 mang label `baseline`, sau đó nhận label `production`.
- **Version/label candidate:** Version 2 mang label `candidate`, `latest`.
- **Trace ID của mỗi version:**
  - Baseline v1: correlation ID `req-d4642a7f`, trace ID `ed7b518f146dd7f08c65a54c19ddf0e6`.
  - Candidate v2: correlation ID `req-ceeb5e19`, trace ID `8d1d2f8c05f5bfaf38b1e6a11dfb472e`.
  - Production v2 (trước rollback): correlation ID `req-97cf1972`, trace ID `a5ac9ef8aa2b1a45a0fa2d5fd7beecc4`.
- **Cách promote và rollback `production`:**
  - Promote: gán label `production` cho Version 2.
  - Rollback: chuyển lại label `production` về Version 1 khi phát hiện sự cố chất lượng hoặc chi phí.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  - Dựng bằng Grafana qua Infinity Datasource đọc read-only từ `/dashboard/{panel}` và `data/logs.jsonl`.
  - 6 Panels gồm: (1) Latency percentiles and TTFT, (2) Request traffic, (3) Error rate and retrieval success, (4) Cost over time, (5) Input and output tokens, (6) Quality proxy.
- **SLO và lý do chọn:**
  - SLO: 99.5% request đạt latency <= 3000ms trong cửa sổ 28 ngày. Ngưỡng này đảm bảo trải nghiệm tương tác trực tiếp của người dùng không bị gián đoạn hay timeout.
- **Cách tính error budget:**
  - SLO 99.5% tương đương error budget 0.5%. Trên tổng 10,000 requests trong chu kỳ đánh giá, hệ thống chỉ cho phép tối đa 50 requests bị lỗi hoặc có độ trễ vượt quá 3000ms.
- **Ba alert và runbook tương ứng:**
  - **HighLatency:** Kích hoạt khi P95 latency > 3000ms trong 5 phút. Runbook: Kiểm tra span waterfall xem nút thắt nằm ở retrieval hay LLM generation, scale hoặc cache tài nguyên RAG.
  - **ElevatedErrorRate:** Kích hoạt khi tỷ lệ lỗi vượt quá 5% trong 5 phút. Runbook: Kiểm tra log `request_failed` tìm lỗi `error_type`, rà soát kết nối downstream tool.
  - **CostSpike:** Kích hoạt khi chi phí tích lũy trong giờ vượt 0.50 USD. Runbook: Rà soát token usage, rollback prompt v2 về v1 nếu prompt quá dài.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-30 15:40:00 – 15:45:00 (+07:00) (tức ~08:40:00 – 08:45:00 UTC)
- **Triệu chứng từ metrics:**
  - Trên Grafana dashboard (`evidence/05-dashboard-incident.png`), P95 Latency vọt tăng đột biến từ mức bình thường `~152ms - 579ms` lên **`2.65 s`** (vượt ngưỡng cho phép 2000ms trong cấu hình challenge).
  - Tỷ lệ lỗi vẫn giữ 0%, Retrieval success 100%, chứng tỏ request không bị drop mà bị nghẽn (tail latency).
- **Log line và correlation ID liên quan:**
  - Log line đại diện trong `data/logs.jsonl` (`evidence/01-incident-log.png`):
    ```json
    {"service": "api", "latency_ms": 2653, "ttft_ms": 50, "tokens_in": 61, "tokens_out": 167, "cost_usd": 0.002688, "quality_score": 0.8, "tool_name": "retrieval", "trace_id": "d0cc7d18f3d82ecda755f81f53fd2fc9", "tool_success": true, "event": "response_sent", "env": "dev", "correlation_id": "req-18b6d0f0", "feature": "monitoring", "model": "claude-sonnet-4-5", "session_id": "k4-l3b-challenge-s03", "ts": "2026-09-30T08:40:10.495148Z"}
    ```
  - Correlation ID: `req-18b6d0f0`.
- **Trace ID và span gây ảnh hưởng:**
  - Trace ID: `d0cc7d18f3d82ecda755f81f53fd2fc9`.
  - Span gây ảnh hưởng (`evidence/03-incident-trace.png`): Span `retrieve` (retriever) tiêu tốn **`2.50s`** trên tổng số 2.65s của root trace (`lab-agent-run`), trong khi span `generation` chỉ mất `0.15s`.
- **Root cause:**
  - Sự cố `rag_slow` được kích hoạt khiến vector store / tài nguyên retrieval bị chậm (mô phỏng delay 2.5s trong `mock_rag.py:retrieve`), làm toàn bộ pipeline RAG bị suy giảm hiệu năng nghiêm trọng.
- **Fix action:**
  - Tắt cờ sự cố `rag_slow` thông qua control API (`POST /incidents/rag_slow/disable`). Trong thực tế: tối ưu hóa chỉ mục vector database, thiết lập Redis/Memcached cache cho các truy vấn phổ biến, scale read-replicas cho vector database.
- **Preventive measure:**
  - Thiết lập timeout cho span `retrieve` (ví dụ: timeout sau 1500ms để kích hoạt cơ chế fallback document), bổ sung alert cảnh báo sớm khi P95 retrieval latency tăng cao, thiết lập circuit breaker.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  - Tách bạch rõ ràng cấu trúc quan sát Langfuse: Root observation (`agent`), Retrieval span (`retriever`), Generation span (`generation`). Quyết định này giúp khoanh vùng chính xác nút thắt cổ chai mà không cần phỏng đoán.
- **Một lỗi/blocker đã gặp:**
  - Khi Grafana nâng cấp lên v12.4.0 với Infinity plugin v4.0.0, chế độ `parser: backend` gặp lỗi crash `TypeError: Cannot read properties of undefined (reading 'method')` làm toàn bộ panel hiển thị No Data.
- **Cách tìm nguyên nhân và xử lý:**
  - Dùng `agent-browser` mở DevTools console kiểm tra stack trace JS, xác định plugin yêu cầu `url_options: {"method": "GET"}` và hoạt động trơn tru với `parser: uql` (`uql: parse-json`). Đã cập nhật lại generator script `scripts/build_grafana.py`.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics** phát hiện sự cố diện rộng (P95 latency tăng vọt lên 2.65s).
  - **Logs** cung cấp ngữ cảnh chi tiết và điểm neo điều tra (`correlation_id: req-18b6d0f0`).
  - **Traces** giúp bóc tách từng span con để chỉ điểm đích danh root cause (`retrieve` tốn 2.50s).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Giúp quản trị rủi ro toàn diện: Prompt versioning cho phép theo dõi sát sao sự thay đổi chất lượng/chi phí và rollback ngay lập tức mà không cần deploy lại code.
- **Điều quan trọng nhất đã học:**
  - Xây dựng hệ thống quan sát đa tầng đồng bộ (Logs, Metrics, Traces liên kết với nhau bằng Correlation ID) là điều kiện tiên quyết để vận hành các ứng dụng AI agent ổn định trong môi trường production.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  - Cần tích hợp thêm webhook cảnh báo thực tế đến Slack/PagerDuty thay vì chỉ mô phỏng qua cấu hình alert rules.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
