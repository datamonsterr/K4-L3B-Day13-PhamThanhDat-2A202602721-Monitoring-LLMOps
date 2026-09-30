# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-2A202602721`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`, ngưỡng SLO 3000ms
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút liên tục
- Ảnh hưởng tới người dùng: người dùng chờ lâu hơn 3 giây trước khi nhận câu trả lời; nếu kéo dài, p99 tệ hơn nữa
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Latency**, xác nhận P95/P99 tăng từ khoảng thời gian nào và TTFT P95 có tăng cùng lúc không.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao bất thường.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh span `retrieve` và `generation` để xác định bước nào chiếm thời gian.
- Mitigation tạm thời: nếu span retrieval chậm (incident `rag_slow`), tắt scenario tại `POST /incidents/rag_slow/disable`; nếu generation chậm/token tăng (incident `cost_spike`), kiểm tra prompt version gần nhất và rollback `production` về version trước qua Langfuse.
- Owner: `student-2A202602721`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: error rate trên panel **Errors** (tỷ lệ `request_failed` / `request_received`), budget 2% guardrail
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` trong 5 phút liên tục
- Ảnh hưởng tới người dùng: request bị trả HTTP 500, không nhận được câu trả lời; vi phạm trực tiếp SLO 99.5%
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Errors**, xác nhận error rate vượt 2% từ khi nào và `count_by(error_type)` cho loại lỗi nào nổi bật.
  2. Lọc `data/logs.jsonl` theo event `request_failed`, lấy một `correlation_id` và đọc `error_type`, `tool_name`.
  3. Mở trace cùng `correlation_id`, kiểm tra span nào màu đỏ (ERROR) — thường là span retrieval khi `tool_fail` bật.
- Mitigation tạm thời: nếu `error_type=RuntimeError` và span retrieval lỗi, tắt scenario `POST /incidents/tool_fail/disable`; xác nhận error rate trở về dưới ngưỡng trên dashboard trong 5 phút tiếp theo.
- Owner: `student-2A202602721`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: retrieval success rate trên panel **Errors** (`tool_success` của `response_sent`), guardrail tối thiểu 90%
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90` trong 10 phút liên tục
- Ảnh hưởng tới người dùng: câu trả lời mất grounding từ RAG, chất lượng giảm (quality proxy giảm kèm theo) dù request vẫn thành công HTTP 200
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel **Errors**, xác nhận `tool_success_rate` giảm từ khi nào và panel **Quality** có giảm cùng lúc không.
  2. Lọc `data/logs.jsonl` theo `tool_success == false`, lấy một `correlation_id` đại diện.
  3. Mở trace cùng `correlation_id`, kiểm tra metadata span `retrieve` (`doc_count`, `query_prompt`) và so sánh với run bình thường.
- Mitigation tạm thời: kiểm tra trạng thái vector store/scenario `rag_slow` hoặc `tool_fail`, tắt scenario gây lỗi; nếu do prompt mới dẫn query sai, rollback `production` về version cũ; theo dõi quality proxy sau khi can thiệp.
- Owner: `student-2A202602721`
