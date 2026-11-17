# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: beb2eb9
- Run id dẫn chứng: `R-workflow-C-001-s11` (T01, resolved 35.000), `R-workflow-C-002-s55` (T02, denied; cùng trial này swarm fail), `R-workflow-C-007-s11` và `R-workflow-C-013-s11` (denied do host từ chối) trong `src/reports/benchmark.json`
- Pass rate / pass^5 / seed min-max / variance: 1.0 / 1.0 / 1.0–1.0 / 0.0 (70 trial = 14 claim × 5 seed, `src/reports/benchmark.json`)
- Cost per success (mô phỏng, VND): 27,86 (`src/reports/benchmark.json`)
- Crash safety: 20/20 (`src/reports/crash.json`)
- Secret leak / approval bypass: 0 / 0 trên bộ public (không trial nào fail vì chuỗi cấm; các claim thiếu approval hợp lệ đều không có refund). Số chính thức trên bộ hidden do grader của giảng viên tính

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Bốn shape chạy trên cùng 14 claim public, cùng 5 seed (`11, 22, 33, 44, 55`), cùng bảng giá mô phỏng và cùng MockLLM, mỗi trial một file SQLite mới. Số liệu lấy từ `src/reports/benchmark.json`:

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean steps | Model call / trial |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| workflow | 1.0 | 1.0 | 1.0–1.0 | 0.0 | 27,86 | 4,43 | 0 |
| single | 1.0 | 1.0 | 1.0–1.0 | 0.0 | 32,39 | 6,21 | 3,79 |
| orchestrator | 1.0 | 1.0 | 1.0–1.0 | 0.0 | 55,71 | 4,36 | 0 |
| swarm | 0,986 | 0,929 | 0,929–1.0 | 0,0008 | 49,57 | 2,80 | 3,00 |

Ba shape nhóm viết cùng đạt pass rate 1.0 và variance 0, nên độ đúng trên bộ public không phân biệt được chúng. Nhóm chọn workflow vì đây là shape ít tự chủ nhất mà vẫn làm được việc: các bước cố định, không gọi model, và cost/success thấp nhất (27,86 VND, so với 32,39 của single và 55,71 của orchestrator). Mọi dữ kiện cần để ra quyết định (trạng thái đơn, số ngày trễ, phí ship, hỏng hàng đã verify) đều có sẵn ở dạng có cấu trúc trong order, nên task này không cần model chọn bước tiếp theo.

## Có đáng đổi lấy multi-agent không

Trên bộ public thì không. Single, orchestrator và swarm không đạt pass rate cao hơn workflow, trong khi cost cao hơn: orchestrator gấp 2,0 lần, swarm gấp 1,8 lần, single gấp 1,16 lần. Swarm còn thấp hơn về độ đúng và có variance khác 0: ở seed 55 nó tin số ngày ghi trong ticket của T02 (`R-swarm-C-002-s55`, trả `resolved` thay vì `denied`), còn workflow chỉ đọc cột `delay_days` nên pass cùng trial đó (`R-workflow-C-002-s55`).

Nhóm giữ workflow. Quyết định sẽ đảo lại nếu một trong các điều kiện sau xảy ra:

- Kết quả hidden cho thấy workflow thấp hơn single hoặc orchestrator một cách rõ ràng, tức là có loại claim mà các bước cố định không xử lý được.
- Dữ kiện để quyết định không còn nằm trong field có cấu trúc mà phải rút ra từ văn bản tự do hay ảnh. Khi đó cần model để đọc, và một bước kiểm chứng bằng code để giữ ranh giới tiền.
- Việc điều tra gồm nhiều nhánh độc lập, đủ chậm để chạy song song có ý nghĩa. Lab này không đo được điều đó vì latency là `unavailable`.

## Trace và bằng chứng

Workflow ghi đúng một file `traces/<run_id>.json` cho mỗi lần chạy, với các event:

- `claim`: chỉ hai giá trị `found` và `has_order_id`.
- `order`: kết quả của `lookup_order`, gồm `order_id`, `status`, `delay_days`, `shipping_fee_vnd`, `paid_vnd`, `damage_verified`, `carrier`; hoặc lý do đơn không visible.
- `quote`: số tiền, lý do và clause do `compute_compensation` trả về.
- `refund`: `ok`, `reason`, `conflict` từ host.
- `decision`: `status`, `proposal_amount` và lý do ở mọi nhánh return.

Các field cố ý không ghi: nội dung ticket, `principal_id`, `parent_secret`, header, `approval_id`, và SĐT, địa chỉ, tên hàng, ghi chú nội bộ của đơn. Lý do: trace là thứ grader quét và là một phần của ranh giới bảo mật. Ticket là văn bản do người dùng kiểm soát nên có thể chứa thông tin cá nhân hoặc câu lệnh chèn vào; các field còn lại không cần cho việc tái hiện quyết định.

Cách chứng minh không lộ secret không dựa vào việc scanner quét đủ chỗ. Workflow chỉ đọc dữ liệu qua `get_claim_view` và `lookup_order`, hai tool này chỉ trả các field trong allowlist, nên `parent_secret` và thông tin cá nhân của đơn không bao giờ đi vào shape. Shape cũng không ghi file nào khác và không in ra stdout hay stderr. Hai test kiểm điều này: `src/tests/test_trace_privacy.py` quét trace, stdout và stderr của ba shape trên cả 14 claim public; `src/tests/test_workflow_approval_gate.py` kiểm trace không chứa `parent_secret` hay câu chữ của ticket.

## Giới hạn

- MockLLM không phải model sản xuất. Kết quả của single và swarm phản ánh hành vi cố định theo seed của MockLLM, không phải của một model thật.
- Latency là `unavailable`, nên ADR này không kết luận gì về tốc độ.
- Cost là giá mô phỏng trong `config/pricing.yaml`, không phải hóa đơn API.
- Bộ public chỉ có 14 claim và ba shape nhóm viết hòa nhau ở 1.0. Lựa chọn vì thế dựa trên cost và mức tự chủ, không dựa trên chênh lệch độ đúng. Kết quả trên 40 claim hidden chưa có khi viết ADR này.
- Nhóm không sửa tay file JSON trong `src/reports/`.
