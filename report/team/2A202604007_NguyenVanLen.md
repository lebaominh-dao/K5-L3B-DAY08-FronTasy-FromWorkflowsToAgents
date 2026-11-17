# Báo cáo cá nhân — Nguyễn Văn Lên

## 1. Thông tin thành viên

- Họ tên: Nguyễn Văn Lên
- MSSV: 2A202604007
- Email: nguyenvanlen24122004@gmail.com
- GitHub: https://github.com/len2412

## 2. Phần việc phụ trách

Shape C — orchestrator và handoff (`src/lab8/shapes/orchestrator.py`); rà soát trace/stdout của `workflow`, `single` và `orchestrator`, đồng thời thêm test privacy cho ba shape.

## 3. Đóng góp cụ thể

- Hoàn thiện orchestrator: đọc claim qua `get_claim_view`, dựng handoff qua `make_handoff`, chỉ cấp investigator các tool đọc, chạy `run_readonly_investigators`, tính quote từ order view đã lọc field, rồi gọi host `durability.issue_refund` với quote đầy đủ.
- Chuyển `crash_at` tới `issue_refund` và để `InjectedCrash` truyền tiếp.
- Trace handoff đã sanitize cùng kết quả điều tra, quote, tóm tắt refund và quyết định; không ghi parent context.
- Thêm `src/tests/test_trace_privacy.py`, quét trace và stdout/stderr của ba shape trên 14 claim fixtures để phát hiện secret, header, ticket thô và dữ liệu riêng tư của order.
- Commit chính của phần orchestrator: `443e207` (`implement todo on orchestrator.py`).

## 4. Bằng chứng

- Orchestrator student matrix: `python -m pytest -q -m student -o addopts= -k orchestrator` — **62 passed**.
- Trace privacy: `python -m pytest -q tests/test_trace_privacy.py` — **42 passed**.
- Public benchmark (`src/reports/benchmark.json`), 14 claim × 5 seed: orchestrator **pass rate 1.000**, **pass⁵ 1.000**, variance **0**, simulated cost/success **55.71 VND**. Các run ID nằm trong artifact benchmark.
- Crash suite (`src/reports/crash.json`): **20/20**.
- Hidden selfcheck chưa có artifact/kết quả trong `src/reports/`; chưa có bằng chứng `error` hoặc `leak_suspect` để sửa orchestrator theo hidden.

## 5. Công cụ AI đã dùng

Dùng Codex để rà checkpoint, contract, handoff và trace; hỗ trợ soạn test và nội dung báo cáo. Đối chiếu thay đổi với code/allowlist và tự chạy các lệnh pytest, benchmark, crash suite trước khi ghi kết quả.

## 6. Tự đánh giá

Orchestrator đạt 62/62 student tests; test privacy ba shape đạt 42/42; public benchmark và crash suite đều đạt yêu cầu.
