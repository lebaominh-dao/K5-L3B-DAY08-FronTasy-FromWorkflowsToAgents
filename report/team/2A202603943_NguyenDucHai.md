# Báo cáo cá nhân — 2A202603943_NguyenDucHai

## 1. Thông tin thành viên

- Họ tên: Nguyễn Đức Hải
- MSSV: 2A202603943
- Email: ndhai255.work@gmail.com
- GitHub: ndhai255

## 2. Phần việc phụ trách

Thành viên 2, phụ trách **shape B `single`** (một ReAct agent):

- Viết `src/lab8/shapes/single.py` và test cho shape trong `src/tests/test_single_shape.py`.
- Điền research card R4 (`report/team/research_card.md`) kèm một ablation single vs swarm.
- Viết phần so sánh 4 shape (mục 4) trong `report/team/group_report.md` bằng số benchmark của Thành viên 4.

## 3. Đóng góp cụ thể

### Commit chính (nhánh `feat/single`, đã merge vào `main` qua PR #3, #4, #8)

| Commit | Nội dung |
| --- | --- |
| `528121c` | feat(single): cài đặt shape ReAct single-agent |
| `c2e0aa0` | test(single): retry, approval mismatch, canary leak |
| `b029bbb` | docs(research): research card R4 và ablation single vs swarm |
| `01f66f8` | test(single): host từ chối vẫn giữ quote đầy đủ, dừng đúng 8 bước |

### Test đã thêm (`src/tests/test_single_shape.py`, chạy trên cả swarm và single)

1. `test_retry_same_claim_keeps_one_ledger_row`: chạy C-011 hai lần vẫn chỉ 1 dòng ledger, 1 audit `refund_committed`.
2. `test_approval_of_another_claim_pays_nothing`: claim C-901 mượn approval A-001 của C-001 → `denied`, `proposal_amount` 35000, audit `approval_claim_mismatch`.
3. `test_trace_and_result_never_leak_canary`: 14 claim public, trace và kết quả không chứa `CANARY_SECRET_`.
4. `test_host_denial_keeps_full_quote`: C-007 (approval hết hạn) và C-013 (đơn đã hoàn đủ) → `denied`, quote đầy đủ, không có dòng ledger, có `policy_denied` đúng lý do.
5. `test_single_stops_at_exactly_eight_steps`: một `decide()` không bao giờ kết thúc thì vòng lặp dừng sau đúng 8 bước, trả `failed`/`step_cap`, không trả tiền, vẫn ghi trace.

### Quyết định kỹ thuật

- **Ranh giới code / model.** `decide()` chỉ chọn tool đọc (`get_claim_view`, `lookup_order`, `compute_compensation`). Sau vòng lặp, code của shape mới gọi `durability.issue_refund`. Model không chọn số tiền và không ghi tiền.
- **`decide()` tự giữ memory.** `run_react` chỉ trả lại kết quả của tool vừa gọi, nên `decide` lưu claim, đơn và quote vào một dict riêng; nếu không, agent lặp lại từ đầu cho tới khi chạm trần 8 bước.
- **Tin order row, không tin ticket.** `delay_days` lấy từ `lookup_order`. Ở C-002 seed 55, ticket ghi trễ 5 ngày, DB ghi 2 ngày: single trả `denied` đúng luật, swarm trả nhầm `resolved`.
- **Truyền quote đầy đủ vào host.** Shape không tự trừ phần đã hoàn của đơn (nếu tự trừ, host trừ thêm lần nữa và T14 fail). Khi host từ chối, `proposal_amount` vẫn là quote đầy đủ để audit `policy_denied` có nghĩa.
- **Một model call mỗi bước `decide`** được đếm vào `Budget` để chi phí so được với các shape khác.
- **Crash.** Truyền `crash_at` vào `issue_refund`; khi `InjectedCrash` xảy ra thì ghi trace rồi `raise` lại, không nuốt lỗi.
- **Trace chỉ ghi field đã allowlist:** tên tool, order view từ `lookup_order`, quote, quyết định, phản hồi host (event `refund`, đặt tên giống workflow của nhóm trưởng). Cố ý không ghi ticket, dòng claim thô (có `parent_secret`) hay dòng order thô (có SĐT, địa chỉ).

## 4. Bằng chứng

- Test shape single trên bộ public: `python -m pytest -q -m student -o addopts= -k "single and not swarm and not workflow and not orchestrator"` → 81 passed (62 test ma trận public + 19 test của tôi).
- Toàn repo trên commit `0d4e2a8`: `python -m pytest -q` → 102 passed; `python -m pytest -q -m student -o addopts=` → 305 passed.
- Crash: `python -m lab8.crash_test --count 20 --out reports/crash.json` → `crash_safety 20/20`. Chạy tay C-012 với `--crash-at` ở cả ba điểm (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`), resume xong đều còn đúng 1 dòng ledger 35000 và 1 audit.
- Benchmark (`src/reports/benchmark.json`): single đạt pass rate 1.000, pass^5 1.000, variance 0, cost/success 32.39 VND mô phỏng, 3.79 model call và 2.79 tool call mỗi trial. Chạy lại lệnh benchmark ra số trùng khớp với file đã commit.
- Ablation R4 (`src/reports/ablation_r4_single_vs_swarm.json`): trial swarm fail duy nhất là `R-swarm-C-002-s55`.
- Quét 71 file trace `traces/R-single-*.json`: không có `CANARY_SECRET_`, SĐT, địa chỉ, ghi chú nội bộ hay ticket.

## 5. Công cụ AI đã dùng

- **Công cụ:** Claude Code (Claude Opus 5.5) trong VS Code.
- **Dùng vào việc:** giải thích khái niệm (ReAct, idempotency, trace contract); gợi ý và viết `single.py` cùng các test; tìm và đọc paper cho research card; soạn phần so sánh trong báo cáo nhóm và bản nháp báo cáo này.
- **Cách tự kiểm tra:**
  - Chạy lại test ở mọi bước (host gate, ma trận public, test của shape) và chỉ commit khi xanh.
  - Chạy test mới trên swarm (shape tham chiếu) trước để chắc chính test viết đúng.
  - Cố tình gài hai lỗi vào single (tự ghi ledger bỏ qua host; ghi secret vào trace) để xác nhận test đỏ đúng chỗ.
  - Chạy crash bằng tay ở ba điểm crash và đếm dòng ledger, audit trong SQLite.
  - Đọc trace JSON thật để chắc không có dữ liệu nhạy cảm.
  - Paper trong research card được xác nhận bằng cách mở chính file PDF trên arXiv, không dựa vào tóm tắt của công cụ tìm kiếm.
  - Mọi số liệu trong báo cáo lấy từ file trong `src/reports/` do lệnh của lab sinh ra; benchmark được chạy lại để đối chiếu.

## 6. Tự đánh giá

### 6.1 Mức độ tự hiểu và giải thích kỹ thuật

Tôi hoàn toàn tự tin giải thích và bảo vệ trực tiếp trước người chấm các quyết định kỹ thuật cốt lõi trong shape `single`:

1. **Vì sao truyền quote đầy đủ vào `durability.issue_refund`:**
   - `durability.issue_refund` đóng vai trò là Host Gate — chốt chặn duy nhất thực thi quyền ghi vào cơ sở dữ liệu (`ledger`) và kiểm soát luật nghiệp vụ `per-order cap`: tổng tiền hoàn của một đơn không vượt entitlement lớn nhất của đơn đó (và không vượt `paid_vnd`). Trần này không phải phí ship: ở C-014, đơn O-515 đã được hoàn 30.000 tiền ship, nay hỏng hàng đã verify với entitlement 150.000, host chỉ trả thêm phần chênh 120.000.
   - Shape không được tự ý trừ đi số tiền đã hoàn trước đó (net amount) rồi mới gửi sang host. Nếu shape tự trừ trước, khi host thực thi đối soát lại trừ tiếp lần thứ hai, dẫn đến số tiền hoàn bị sai lệch và chắc chắn sẽ trượt các ca kiểm thử đơn hàng hoàn nhiều lần (như test T14).
   - Khi host từ chối yêu cầu (do approval hết hạn như C-007 hoặc đơn đã hoàn chạm trần như C-013), việc shape giữ nguyên `proposal_amount` là giá trị quote đầy đủ đảm bảo audit log `policy_denied` phản ánh chính xác số tiền mà luồng nghiệp vụ đã đề xuất, phục vụ đúng mục đích đối soát và kiểm toán tài chính.

2. **Vì sao `decide()` phải tự duy trì `memory`:**
   - Hàm runtime `run_react` của lab được thiết kế tinh gọn: ở mỗi bước lặp, nó chỉ phản hồi kết quả của tool vừa thực thi gần nhất (`last_tool`, `last_result`), chứ không tự động tích lũy toàn bộ lịch sử các tool đã gọi trước đó trong tham số `seen`.
   - Nếu hàm `decide()` không có một cấu trúc lưu trữ riêng (`memory: dict[str, Any]` thông qua closure của `make_decide`), thì sau khi agent gọi tool thứ hai (`lookup_order`), thông tin từ `get_claim_view` sẽ bị mất. Khi đó, agent sẽ bị kẹt trong vòng lặp vô tận (liên tục đọc lại claim) cho đến khi bị ngắt cưỡng bức ở trần 8 bước (`step_cap`).

3. **Trace cố ý không ghi các field nào và lý do:**
   - Tuân thủ tuyệt đối [Trace contract v1](docs/contracts.md#trace-contract-v1) và nguyên tắc bảo vệ dữ liệu nhạy cảm:
     - **Không ghi token bí mật:** Loại bỏ hoàn toàn `parent_secret` và các token canary (`CANARY_SECRET_*`) có trong dòng claim thô.
     - **Không ghi dữ liệu định danh cá nhân (PII):** Số điện thoại khách hàng, địa chỉ giao hàng, ghi chú nội bộ từ bảng `orders` đều bị loại trừ vì trace chỉ ghi order view do `lookup_order` trả về, mà `lookup_order` chỉ lấy các field trong allowlist `ORDER_FIELDS` (`src/lab8/tools.py`). Hàm `safe_dump()` chỉ sao chép payload để ghi vào trace, không tự lọc gì.
     - **Không ghi nội dung thô của `ticket`:** Ticket là dữ liệu do người dùng nhập từ bên ngoài, tiềm ẩn nguy cơ prompt injection hoặc thông tin sai sự thật (như case C-002 seed 55 khai khống trễ 5 ngày thay vì 2 ngày như dữ liệu DB).
     - **Không ghi prompt đầy đủ:** Không đưa toàn bộ prompt gửi MockLLM vào trace để tránh phình dung lượng lưu trữ không cần thiết.
   - Trace chỉ ghi đúng các sự kiện nằm trong danh sách allowlist: `tool_call`, `order` (sanitized), `quote` (sanitized), `refund`, `decision`, `crash`.

### 6.2 Đánh giá phần tự chủ và phần phụ thuộc trợ lý AI

- **Những phần làm tốt và hoàn toàn làm chủ:**
  - **Ranh giới Code / Model vững chắc:** Xác lập nguyên tắc bất di bất dịch là model chỉ đóng vai trò bộ điều hướng đọc thông tin (`get_claim_view` -> `lookup_order` -> `compute_compensation`); tuyệt đối không để model tự tính tiền bồi thường hay ghi sổ. Toàn bộ logic tính toán tiền thuộc về hàm nghiệp vụ xác định, và ghi sổ thuộc về Host Gate.
  - **Hệ thống kiểm thử toàn diện:** Tự thiết kế và cài đặt 5 nhóm test case chuyên biệt trong `src/tests/test_single_shape.py`, bao phủ đầy đủ các kịch bản biên: tính lũy đẳng (idempotency, với C-011), phát hiện mượn approval trái phép (C-901), kiểm soát rò rỉ secret/PII, bảo toàn quote khi host từ chối, và cơ chế ngắt cưỡng bức đúng 8 bước.
  - **Nghiên cứu thực nghiệm và phân tích số liệu:** Thực hiện trọn vẹn Research Card R4 và ablation single vs swarm; phát hiện chính xác điểm lỗi then chốt của swarm ở trial `R-swarm-C-002-s55` (do tin ticket thay vì order row), đồng thời chỉ ra confounder của việc so sánh số bước `steps` giữa các topology khác nhau.
  - **Kiểm chứng độc lập:** Tự tay chạy lại toàn bộ test suite, benchmark suite, kiểm tra các dòng ledger/audit trong SQLite sau crash test, không phụ thuộc vào bất kỳ kết quả suy đoán nào.

- **Những phần còn phụ thuộc vào trợ lý AI:**
  - Trong giai đoạn đầu, tôi dùng Claude Code để gợi ý cấu trúc khung cho closure `make_decide` và cách bắt ngoại lệ `InjectedCrash` sao cho vẫn kịp ghi trace ra đĩa trước khi `raise` lại lỗi.
  - Sử dụng AI để tìm kiếm nhanh các bài báo liên quan đến đánh giá hiệu năng hệ thống multi-agent (dù sau đó tôi đã tự mở bản PDF trên arXiv để đọc kỹ và trích xuất đúng luận điểm gốc).
  - Nhờ AI hỗ trợ định dạng bảng Markdown và chuẩn hóa văn phong trình bày trong các tài liệu báo cáo.

### 6.3 Bài học kinh nghiệm và hướng cải tiến nếu làm lại

1. **Linh hoạt hóa cơ chế rẽ nhánh trong `decide()`:** Hiện tại, logic ra quyết định của `single.py` vẫn mang tính bán tuần tự (kiểm tra lần lượt từng điều kiện trong memory). Nếu phát triển cho môi trường production với nhiều trường hợp ngoại lệ, tôi sẽ cho phép agent có khả năng tra cứu bù thông tin (ví dụ: tìm kiếm qua mã vận đơn phụ khi không tìm thấy order_id) hoặc tự động retry khi gặp lỗi mạng tạm thời.
2. **Thiết kế kiến trúc Hybrid (Workflow-First, Agent-Fallback):** Dữ liệu thực nghiệm trên 14 claim public cho thấy Workflow đạt pass rate 1.000 với chi phí chỉ 27.86 VND mỗi lần thành công, rẻ hơn khoảng 14% so với Single (32.39 VND; nói cách khác Single đắt hơn Workflow khoảng 16%) do Single tốn thêm trung bình 3.79 model calls cho mỗi trial. Nếu làm lại, tôi sẽ đề xuất kiến trúc ưu tiên chạy Workflow cho 90% trường hợp chuẩn, và chỉ chuyển giao (escalate/fallback) sang Single ReAct khi dữ liệu bị thiếu hoặc có mâu thuẫn phức tạp.
3. **Tự động hóa kiểm tra hợp đồng Trace (Contract Linter):** Xây dựng một script tiện ích riêng để quét và xác thực tự động toàn bộ file trace JSON sau các lượt chạy benchmark, thay vì phải kiểm tra thủ công hoặc viết test assertion riêng lẻ cho từng file.
