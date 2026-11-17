# Báo cáo cá nhân — 2A202604010_DaoLeBaoMinh

## 1. Thông tin thành viên

- Họ tên: Đào Lê Bảo Minh
- MSSV: 2A202604010
- Email: 26ai.minhdlb@vinuni.edu.vn
- GitHub: https://github.com/lebaominh-dao

## 2. Phần việc phụ trách

- Nhóm trưởng, vai workflow + integration.
- Shape A `workflow` trong `src/lab8/shapes/workflow.py`: CP2 (luồng xử lý claim), CP3 (crash và resume), CP4 (rà các nhánh approval hỏng).
- Integration: review và merge PR của các thành viên vào `main`, giữ cổng host `python -m pytest -q` xanh sau mỗi lần merge.

## 3. Đóng góp cụ thể

Commit chính:

| Commit | Nội dung |
| --- | --- |
| `f504017` | Viết shape workflow (CP2) |
| `ea8639f` | Truyền `crash_at` vào `durability.issue_refund`, không bắt `InjectedCrash` (CP3) |
| `158d7f9` | Thêm test `src/tests/test_workflow_approval_gate.py` (CP4) |

Shape workflow đi theo 7 bước cố định, không có vòng lặp và không gọi model:

1. Đọc claim bằng `get_claim_view`. Không thấy claim thì trả `failed`.
2. Claim thiếu `order_id` thì trả `needs_info`. Không lấy mã đơn từ câu chữ trong ticket.
3. `lookup_order` trả về không visible (không tìm thấy đơn, hoặc người gửi không sở hữu đơn) thì trả `escalated`.
4. Tính quote bằng `compute_compensation` từ dòng order và policy hiện hành.
5. Quote bằng 0 thì trả `denied`, không gọi host.
6. Quote lớn hơn 0 thì gọi `durability.issue_refund` với quote đầy đủ. Host từ chối thì `denied`, xung đột số tiền thì `failed`; `proposal_amount` vẫn là quote đầy đủ.
7. Host chấp nhận thì trả `resolved`.

Quyết định kỹ thuật:

- **Không gọi MockLLM.** `RunResult` không có field chứa câu trả lời cho khách, nên một lần gọi model chỉ làm tăng cost mà không đổi kết quả. Workflow chỉ tính 3 tool call đọc.
- **Không đọc nội dung ticket.** Số ngày trễ và mã đơn chỉ lấy từ dữ liệu có cấu trúc, vì chữ trong ticket là dữ liệu người dùng.
- **Shape không tự kiểm approval.** Việc kiểm approval, trần theo đơn và idempotency thuộc về host. Shape truyền quote đầy đủ để host tự trừ phần đã hoàn (T13, T14) và tự ghi audit `policy_denied`.
- **Mọi nhánh return đi qua một hàm `end()`.** Hàm này ghi event `decision` rồi gọi `finish()`, nên không nhánh nào thiếu trace.
- **Trace chỉ ghi dữ liệu đã qua allowlist.** Claim chỉ ghi `found` và `has_order_id`; order ghi đúng kết quả của `lookup_order`; ngoài ra có quote, kết quả của host và quyết định cuối. Ticket và `parent_secret` không được ghi.
- **Không bắt `InjectedCrash`.** `crash_at` được chuyển thẳng xuống host và crash thoát ra khỏi `run_claim`, để lần chạy lại trên cùng DB chứng minh được vẫn chỉ có một refund.

Test đã thêm: `src/tests/test_workflow_approval_gate.py`. Test tạo một claim mới trên đơn `O-808` (trễ 4 ngày, phí ship 35.000) với ticket cố tình nói dối và ra lệnh, rồi cho approval hỏng theo 6 kiểu, mỗi kiểu chạy workflow hai lần:

| Trường hợp | Lý do host từ chối |
| --- | --- |
| Claim không có `approval_id` | `missing_approval` |
| `approval_id` trỏ tới approval không tồn tại | `missing_approval` |
| Mượn approval `A-001` của claim `C-001` | `approval_claim_mismatch` |
| Approval bị thu hồi | `approval_revoked` |
| Approval hết hạn | `approval_expired` |
| Approval duyệt 0 đồng | `non_positive_amount` |

Mỗi lần chạy đều kiểm: `status` là `denied`, `proposal_amount` vẫn là 35.000, không có dòng ledger, có audit `policy_denied` đúng lý do, và trace không chứa `parent_secret` hay câu chữ trong ticket.

Phần integration: merge PR #2 (orchestrator), #3 và #4 (single) vào `main`.

## 4. Bằng chứng

- Commit: [`f504017`](https://github.com/lebaominh-dao/K5-L3B-DAY08-FronTasy-FromWorkflowsToAgents/commit/f504017), [`ea8639f`](https://github.com/lebaominh-dao/K5-L3B-DAY08-FronTasy-FromWorkflowsToAgents/commit/ea8639f), [`158d7f9`](https://github.com/lebaominh-dao/K5-L3B-DAY08-FronTasy-FromWorkflowsToAgents/commit/158d7f9).
- PR của phần workflow: #1, #5, #6.
- `python -m pytest -q -m student -o addopts= -k workflow`: 62 passed (60 test chạy một lần, T11, T12).
- `python -m pytest -q tests/test_workflow_approval_gate.py`: 6 passed.
- `python -m pytest -q` (cổng host) sau khi merge các PR trên: 60 passed.
- Thử tay ba điểm crash trên claim `C-012` bằng `python -m lab8.run --shape workflow --claim-id C-012 --seed 11 --db <file> --crash-at <điểm>` rồi chạy lại trên cùng DB không có `--crash-at`. Cả ba điểm (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) đều ra `resolved`, 35.000, một audit `refund_committed`.

## 5. Công cụ AI đã dùng

- Công cụ: Claude Code (Anthropic).
- Dùng vào việc: hướng dẫn cài môi trường; tóm tắt `docs/business_rules.md`, `docs/contracts.md` và `swarm_reference.py`; gợi ý bảng phân công theo checkpoint; viết code `workflow.py` cho CP2 và CP3; viết test `test_workflow_approval_gate.py`; soạn nháp báo cáo này.
- Cách tự kiểm tra: chạy lại ma trận student cho workflow và cổng host sau mỗi thay đổi; thử tay ba điểm crash rồi resume; đọc lại code và hỏi lại luồng `InjectedCrash` (host ném, shape không chặn, test bắt) cho tới khi tự giải thích được.
- Mục 6 "Tự đánh giá": nội dung là câu trả lời của mình cho các câu hỏi AI đặt ra; AI chỉ diễn đạt lại thành câu.

## 6. Tự đánh giá

**Mức độ hiểu code.** Mình giải thích được luồng của `workflow.py`: `run_claim` nhận `claim_id`, mở database rồi gọi `_run` để xử lý. `_run` chạy từng bước: đọc claim, truy xuất đơn, tra cứu chính sách và tính số tiền khách được hoàn, rồi ở bước cuối giao quote cho host để chốt hoàn đủ, hoàn một phần hay không hoàn. Mình cũng nắm các trường hợp biên: không tìm được claim, claim thiếu `order_id`, không xem được order, và bước chuyển từ quote thành refund. Phần mình còn mơ hồ là logic bên trong các tool chạy phía dưới workflow.

**Phần tự làm và phần dựa vào AI.** Mình tự đọc tài liệu, tự nắm quy trình của workflow và mục đích của từng bước. Mình cũng tự hiểu vì sao bản đầu "ngậm" `crash_at` nên test không thấy `InjectedCrash`, và tự đọc, merge PR của các thành viên. Mình dựa vào AI nhiều nhất ở việc biến các quy tắc thành code cho `workflow.py` và `test_workflow_approval_gate.py`.

**Vai nhóm trưởng.** Mình làm tốt việc phân vai, theo dõi tiến độ của các thành viên và đọc review. Điểm chưa tốt là mình phải hỏi AI nhiều lượt, kể cả ở các phiên làm việc khác, và vẫn còn một số phần logic chưa rõ, cần đọc kỹ hơn.

**Khó khăn.** Thời gian hơi ít. Phần lớn thời gian mình dành để đọc tài liệu và hiểu bài toán, vì mình chưa có kiến thức về nghiệp vụ này.

**Bài học.** Mình hiểu được quy trình nghiệp vụ của một workflow rule-based, và thấy được AI có thể làm tốt hơn ở những điểm nào khi dùng single agent hoặc orchestrator. Nếu có thêm thời gian, mình sẽ làm một giao diện để demo cuối giờ; lần này mình không kịp làm demo.
