# Báo cáo cá nhân — 2A202603970_CaoPhamThanhDat

## 1. Thông tin thành viên

- Họ tên: Cao Phạm Thành Đạt
- MSSV: 2A202603970
- Email: 26ai.datcpt@vinuni.edu.vn
- GitHub: [tcaopham216-gif](https://github.com/tcaopham216-gif)

## 2. Phần việc phụ trách

Thành viên 4 của nhóm FronTasy (L3B), phụ trách ledger và evaluation. Phần việc gồm kiểm thử an toàn hoàn tiền trên bốn shape, kiểm tra crash và resume, chạy crash suite và benchmark public.

## 3. Đóng góp cụ thể

Commit `dc76b0e` bổ sung [test durability](../../src/tests/test_shape_durability.py) và hai báo cáo do lệnh lab tạo. Test gồm 20 trường hợp, với 5 trường hợp cho mỗi shape.

- Chạy lại cùng claim với seed 11 và 55. Kết quả phải giữ đúng một refund và một audit `refund_committed`.
- Dùng approval của claim khác trên cùng đơn và cùng khách hàng. Test kiểm tra lý do `approval_claim_mismatch`, ledger và audit, cùng việc trace và kết quả giữ an toàn cho canary.
- Dừng ở `before_effect`, `after_effect_before_checkpoint` và `after_checkpoint`. Test đối chiếu trạng thái ledger, audit và checkpoint tại thời điểm crash rồi kiểm lại sau resume trên cùng SQLite DB.
- Lần thử đầu phát hiện Workflow bỏ qua `crash_at`. Sau bản sửa `ea8639f` của người phụ trách Workflow, cả ba điểm crash đều kích hoạt đúng và mỗi lần resume để lại một refund và một audit.

## 4. Bằng chứng

- Đóng góp được merge qua [PR #9](https://github.com/lebaominh-dao/K5-L3B-DAY08-FronTasy-FromWorkflowsToAgents/pull/9). Xem [commit `dc76b0e`](https://github.com/lebaominh-dao/K5-L3B-DAY08-FronTasy-FromWorkflowsToAgents/commit/dc76b0e).
- Kiểm tra lại trên mã nhóm tại `97a6070`. `python -m pytest -q` đạt **102 pass** và `python -m pytest -q -m student -o addopts=` đạt **305 pass**.
- Crash suite đạt **20/20**. [Báo cáo crash](../../src/reports/crash.json).
- Benchmark CP5 gồm **280 lượt thử** trên 4 shape, 14 claim public và 5 seed (`11,22,33,44,55`). Lần chạy lại trên `main` tại `08f450e` khớp báo cáo đã commit. [Báo cáo benchmark](../../src/reports/benchmark.json).

| Shape | Pass rate | Pass^5 | Phương sai theo seed | Cost/success (VND mô phỏng) | Run ID dẫn chứng |
| --- | ---: | ---: | ---: | ---: | --- |
| Workflow | 100% | 100% | 0 | 27,86 | `R-workflow-C-002-s55` |
| Single | 100% | 100% | 0 | 32,39 | `R-single-C-002-s55` |
| Orchestrator | 100% | 100% | 0 | 55,71 | `R-orchestrator-C-002-s55` |
| Swarm | 98,57% | 92,86% | 0,000816 | 49,57 | `R-swarm-C-002-s55` |

Lượt lỗi duy nhất là `R-swarm-C-002-s55`. Ticket ghi trễ 5 ngày và đơn ghi 2 ngày. Swarm dùng dữ liệu ticket nên trả `resolved` trong khi nhãn là `denied`. Số liệu của Single và Swarm khớp phép đối chiếu R4 đã có trong [research card của nhóm](research_card.md).

## 5. Công cụ AI đã dùng

- ChatGPT (Codex) hỗ trợ viết test, chạy lab, đối chiếu bằng chứng và soạn báo cáo, gồm phần tự đánh giá dựa trên kết quả đã kiểm chứng.
- Kết quả được đối chiếu bằng `pytest`, thử crash và resume qua `lab8.run`, chạy `lab8.crash_test` và so sánh JSON do `lab8.benchmark` sinh ra.

## 6. Tự đánh giá

Tôi đã hoàn thành phần kiểm thử và đánh giá bằng các kịch bản có thể chạy lại trên cả bốn shape. Việc kiểm tra ledger, audit và checkpoint ngay lúc crash giúp tôi xác định chính xác lỗi ban đầu của Workflow: chương trình hoàn tiền nhưng điểm crash chưa được kích hoạt. Sau khi bản sửa được merge, kết quả chạy lại xác nhận cả ba điểm crash đều hoạt động và mỗi claim chỉ có một refund.

Điểm tôi cần cải thiện là ghi bằng chứng theo từng lớp kiểm thử rõ hơn. Crash suite đạt 20/20, phép thử ba điểm crash kiểm riêng đường chạy của từng shape, còn benchmark đo độ đúng và chi phí mô phỏng trên 14 claim public. Khi trình bày kết quả, tôi cần nêu rõ phạm vi của từng phép đo để nhóm có thể dùng đúng số liệu.
