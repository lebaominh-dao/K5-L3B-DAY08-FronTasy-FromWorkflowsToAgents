# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: FronTasy (lớp L3B)
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

**Bài toán.** LogiX-VN nhận claim hoàn phí vận chuyển. Nhóm cài cùng một quy trình xử lý claim theo bốn kiến trúc có chung chữ ký `run_claim`, đo chúng trên cùng claim, cùng seed, cùng bảng giá, rồi chọn kiến trúc ít tự chủ nhất mà vẫn làm được việc. Ranh giới nhóm giữ ở cả ba shape tự viết: số tiền do code tính (`compute_compensation`), việc ghi refund do host quyết (`durability.issue_refund` kiểm approval, trần theo đơn và idempotency), còn chữ trong ticket là dữ liệu người dùng chứ không phải lệnh.

**Chia việc.** Nhóm 4 người, mỗi người một nhánh riêng và một nhóm file riêng để không conflict:

| Thành viên | Vai | Phần giữ |
| --- | --- | --- |
| Đào Lê Bảo Minh | workflow + integration | `workflow.py`, review và merge PR, ADR |
| Nguyễn Đức Hải | single agent | `single.py`, phiếu nghiên cứu R4 |
| Nguyễn Văn Lên | orchestrator + handoff | `orchestrator.py`, test quét trace và stdout cho cả ba shape |
| Cao Phạm Thành Đạt | ledger + evaluation | test durability cho cả bốn shape, benchmark, crash suite |

**Thứ tự làm.** Workflow được viết trước vì là shape đơn giản nhất, sau đó single và orchestrator được làm song song. Khi cả ba shape qua ma trận public, nhóm bổ sung phần crash (truyền `crash_at`), rồi mỗi người thêm test cho các điều kiện must-pass. Benchmark và crash suite được chạy sau khi code shape đã ổn định. Swarm giữ nguyên bản tham chiếu, chỉ dùng để đối chứng cost và variance.

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

### Shape A — workflow

- **Đọc gì:** claim qua `get_claim_view`, order qua `lookup_order`. Cả hai chỉ trả các field trong allowlist. Shape không đọc nội dung ticket.
- **Quyết định gì:** các bước Python cố định, không có vòng lặp. Không thấy claim thì `failed`; thiếu `order_id` thì `needs_info`; đơn không visible thì `escalated`; quote bằng 0 thì `denied`.
- **Gọi host ra sao:** khi quote lớn hơn 0, shape gọi `durability.issue_refund` với quote đầy đủ từ `compute_compensation` và chuyển thẳng `crash_at`. Host kiểm approval, trần theo đơn và idempotency. Host từ chối thì `denied` (hoặc `failed` nếu xung đột số tiền), chấp nhận thì `resolved`.
- **Ranh giới code / model:** workflow không gọi model. Số tiền do code tính, việc ghi refund do host quyết.
- **Trace:** các event `claim` (chỉ `found`, `has_order_id`), `order` (kết quả `lookup_order`), `quote`, `refund` (`ok`, `reason`, `conflict`) và `decision`. Ticket và `parent_secret` không được ghi.

### Shape B — single agent

- **Đọc gì:** ba tool đọc qua vòng `run_react`: `get_claim_view`, `lookup_order`, `compute_compensation`. Vòng lặp dừng ở tối đa 8 bước.
- **Quyết định gì:** hàm `decide` nhìn kết quả tool vừa có, lưu vào bộ nhớ của lần chạy, rồi chọn tool đọc tiếp theo hoặc kết thúc. Mỗi lần `decide` chạy được tính là một lần gọi MockLLM trong Budget. Mã đơn chỉ lấy từ dòng claim; số ngày trễ, phí và hỏng hàng chỉ lấy từ dòng order.
- **Gọi host ra sao:** `decide` không được gọi `issue_refund`. Sau khi vòng lặp trả về quote, code của shape mới gọi `durability.issue_refund` với quote đầy đủ và `crash_at`. Chạm trần 8 bước hoặc tool bị từ chối thì shape kết thúc mà không ghi tiền.
- **Ranh giới code / model:** model chỉ tham gia bước "nghĩ" chọn tool đọc. Số tiền do `compute_compensation` tính, việc ghi do host quyết.
- **Trace:** các event `tool_call` (chỉ tên tool), `order` (các field allowlist của đơn, hoặc lý do không visible), `quote`, `refund`, `decision`, và `crash` khi có crash được tiêm. Prompt gửi cho model không được ghi vào trace.

### Shape C — orchestrator

- **Đọc gì:** orchestrator đọc claim qua `get_claim_view`, rồi giao việc tra cứu cho investigator. Investigator chạy ba tool đọc: `lookup_order`, `lookup_policy`, `lookup_refund_history`.
- **Handoff:** dựng bằng `make_handoff`. Gói tin chỉ gồm các field trong allowlist (`contract_version`, `request_id`, `claim_id`, `principal_scope`, `task`, `facts`, `allowed_tools`, `max_output_tokens`). `facts` chỉ nhận các khóa trong `FACT_KEYS`, nên `order_id` orchestrator đưa vào bị lọc bỏ và investigator tự tra đơn theo `claim_id`. `make_handoff` từ chối mọi tool ghi, và `sanitize` chặn gói tin còn chứa secret hay header.
- **Quyết định gì:** orchestrator nhận order view từ investigator. Đơn không visible thì `escalated`; ngược lại orchestrator tự tính quote bằng `compute_compensation`.
- **Gọi host ra sao:** chỉ orchestrator gọi `durability.issue_refund`, với quote đầy đủ và `crash_at`. Investigator không có tool ghi.
- **Ranh giới code / model:** bản này không gọi model. Phần phân vai nằm ở ranh giới dữ liệu: investigator chỉ thấy handoff đã sanitize và các tool đọc.
- **Trace:** các event `handoff` (bản đã sanitize, không phải parent context), `investigation` (kết quả các tool đọc), `quote`, `refund`, `decision`.

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

**Benchmark public** (`src/reports/benchmark.json`): 4 shape × 14 claim × 5 seed (`11, 22, 33, 44, 55`), tổng 280 trial, mỗi trial một file SQLite mới.

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean steps | p95 steps | Model call / trial | Tool call / trial |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.0 | 1.0 | 1.0–1.0 | 0.0 | 27,86 | 4,43 | 5 | 0 | 2,79 |
| single | 1.0 | 1.0 | 1.0–1.0 | 0.0 | 32,39 | 6,21 | 7 | 3,79 | 2,79 |
| orchestrator | 1.0 | 1.0 | 1.0–1.0 | 0.0 | 55,71 | 4,36 | 5 | 0 | 5,57 |
| swarm | 0,986 | 0,929 | 0,929–1.0 | 0,0008 | 49,57 | 2,80 | 3 | 3,00 | 4,66 |

- Ba shape nhóm viết pass cả 70 trial. Swarm fail đúng một trial, `R-swarm-C-002-s55`: ticket ghi trễ 5 ngày, order ghi 2 ngày, swarm trả `resolved` thay vì `denied`.
- Workflow có cost/success thấp nhất. Orchestrator đắt nhất trong ba shape nhóm viết vì số tool call gấp đôi (5,57 so với 2,79), dù không gọi model.
- Cột steps đếm số event trong trace nên phụ thuộc cách mỗi shape ghi trace. Nhóm không dùng cột này để so khối lượng việc giữa các shape; phần này được phân tích trong `research_card.md`.
- Cost là giá mô phỏng, latency là `unavailable`.

**Crash safety** (`src/reports/crash.json`): 20/20. Gồm 5 điểm `before_effect`, 7 điểm `after_effect_before_checkpoint`, 5 điểm `after_checkpoint`, 1 kịch bản gọi lại với số tiền khác, 1 kịch bản gọi lại khi không có approval, và 1 kịch bản crash trên swarm.

**Test của nhóm.** Cổng host `python -m pytest -q`: 102 passed. Ma trận student `python -m pytest -q -m student -o addopts=`: 305 passed, trong đó mỗi shape nhóm viết đạt 62/62 trên `tests/test_public_matrix.py`. Các test nhóm thêm:

| File | Kiểm gì |
| --- | --- |
| `tests/test_workflow_approval_gate.py` | Workflow với 6 kiểu approval hỏng, mỗi kiểu chạy hai lần |
| `tests/test_single_shape.py` | Single (đối chiếu với swarm): gọi lại cùng claim, approval của claim khác, không lộ canary, giữ quote đầy đủ khi host từ chối, dừng đúng 8 bước |
| `tests/test_trace_privacy.py` | Trace, stdout và stderr của ba shape trên 14 claim không chứa secret hay thông tin cá nhân |
| `tests/test_shape_durability.py` | Bốn shape: gọi lại với seed khác, approval của claim khác trên cùng đơn, resume từ cả ba điểm crash |

**Tự kiểm trên `student_drop/`:** chưa chạy tại thời điểm viết báo cáo.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

**Không tạo được venv trên Ubuntu.** Lệnh trong README:

```text
$ python3 -m venv .venv
The virtual environment was not created successfully because ensurepip is not
available.  On Debian/Ubuntu systems, you need to install the python3-venv
package using the following command.

    apt install python3.12-venv
```

Cách xử lý: tạo venv bằng `uv venv .venv --python 3.12 --seed` (không cần `sudo`), sau đó `python -m pip install -r requirements.txt` và `python -m lab8.smoke` chạy bình thường.

**T12 báo `crash did not fire`.** Sau khi viết xong luồng chính của workflow, ma trận student của workflow ra `1 failed, 61 passed`:

```text
FAILED tests/test_public_matrix.py::test_t12_crash_before_checkpoint_does_not_double_pay[workflow]
AssertionError: crash did not fire: pass crash_at to durability.issue_refund and do not catch InjectedCrash
```

Nguyên nhân: shape nhận `crash_at` nhưng không chuyển xuống host, nên host không ném `InjectedCrash` và refund được ghi như một lần chạy bình thường. Cách xử lý: truyền `crash_at` vào `durability.issue_refund` và không bắt `InjectedCrash` (commit `ea8639f`). Sau đó workflow đạt 62/62.

**Thời gian đọc tài liệu.** Phần lớn thời gian đầu buổi dành cho việc đọc luật nghiệp vụ và contract, vì nhóm chưa quen nghiệp vụ hoàn phí. Nhóm chia phần đọc theo vai để mỗi người chỉ cần nắm sâu phần liên quan tới shape của mình.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

**Hạn chế**

- MockLLM cố định theo seed, không phải model sản xuất. Kết quả của single và swarm không nói lên hành vi của một model thật.
- Latency là `unavailable` và cost là giá mô phỏng, nên nhóm không kết luận gì về tốc độ hay hóa đơn API.
- Bộ public chỉ có 14 claim và ba shape nhóm viết hòa nhau ở pass rate 1.0. Lựa chọn workflow dựa trên cost và mức tự chủ, không dựa trên chênh lệch độ đúng. Chênh lệch với swarm đến từ một trial duy nhất.
- Trong shape single, quy tắc chọn tool của `decide` là code cố định, model chỉ được gọi để tính cost. Shape này vì thế chưa thể hiện rủi ro của một agent thật sự tự chọn bước.
- Handoff của orchestrator hiện không mang fact nào, vì `order_id` không nằm trong `FACT_KEYS`. Investigator vẫn làm đúng vì tự tra đơn theo `claim_id`.
- Nhóm chưa có kết quả trên bộ hidden và chưa chạy tự kiểm trên `student_drop/`.
- Nhóm không làm topic bonus.

**Điều kiện làm kết luận thay đổi**

- Bộ hidden cho thấy workflow thấp hơn single hoặc orchestrator một cách rõ ràng.
- Dữ kiện để quyết định phải rút từ văn bản tự do hay ảnh, thay vì có sẵn trong field có cấu trúc của order.
- Việc điều tra gồm nhiều nhánh độc lập, đủ chậm để chạy song song có ý nghĩa.

**Hướng cải thiện**

- Chạy tự kiểm trên `student_drop/` và thêm test cho các loại claim đối kháng của bộ hidden (homoglyph, policy tương lai, principal lẫn).
- Làm một giao diện nhỏ để demo luồng xử lý claim và trace; lần này nhóm không kịp làm.

## 8. Tài liệu tham khảo

- Tài liệu của lab trong repo: `README.md`, `CHECKPOINTS.md`, `RUBRIC.md`, `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`, `docs/architecture.md`.
- Nguồn của phiếu nghiên cứu R4: *Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems*; thông tin trích dẫn đầy đủ nằm trong `report/team/research_card.md`.
- Công cụ AI từng thành viên đã dùng: ghi trong báo cáo cá nhân `report/team/MSSV_HoTen.md`.
