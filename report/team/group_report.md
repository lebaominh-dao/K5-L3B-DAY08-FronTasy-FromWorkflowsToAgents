# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

...

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

...

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

### 4.1 So sánh 4 shape trên bộ public

Nguồn: `src/reports/benchmark.json`, sinh bằng lệnh dưới đây trên commit `0d4e2a8`. Cùng 14 claim (`data/public_claims.jsonl`), cùng 5 seed `11,22,33,44,55`, cùng bảng giá `config/pricing.yaml`, MockLLM, as_of 2026-11-15, SQLite mới cho mỗi trial. Mỗi shape chạy 70 trial. Chạy lại lệnh cho ra số trùng khớp hoàn toàn với file đã commit.

```bash
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps | Model calls / trial | Tool calls / trial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A workflow | 1.000 | 1.000 | 1.000–1.000 | 0 | **27.86** | 4.43 / 5 | 0 | 2.79 |
| B single | 1.000 | 1.000 | 1.000–1.000 | 0 | 32.39 | 6.21 / 7 | 3.79 | 2.79 |
| C orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0 | 55.71 | 4.36 / 5 | 0 | 5.57 |
| D swarm (tham chiếu) | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 | 3.00 | 4.66 |

Crash safety (`src/reports/crash.json`, lệnh `python -m lab8.crash_test --count 20 --out reports/crash.json`): **20/20**.

Tự kiểm trên bộ hidden (`student_drop/`): chưa chạy, vì chưa nhận được `student_drop/` từ giảng viên.

### 4.2 Đọc bảng

1. **Độ chính xác không phân biệt được A, B, C.** Cả ba đạt pass rate 1.000, pass^5 1.000 và variance 0. Chỉ swarm có trial fail: `R-swarm-C-002-s55`. Ở trial đó ticket ghi trễ 5 ngày nhưng order row ghi 2 ngày; swarm tin ticket khi `seed % 5 == 0` (`REFERENCE_WEAKNESS` viết sẵn trong reference) nên trả `resolved` thay vì `denied`. Ba shape nhóm viết đều lấy `delay_days` từ order row nên không mắc lỗi này.
2. **Chênh lệch nằm ở chi phí, và chi phí tăng theo mức tự chủ.**
   - Workflow rẻ nhất (27.86) vì không gọi model, chỉ 2.79 tool call mỗi trial.
   - Single gọi đúng số tool như workflow (2.79), nhưng mỗi bước `decide` thêm một model call (3.79 lần mỗi trial). Phần cho agent tự chọn bước tiếp theo đắt thêm 4.54 VND mỗi lần thành công (+16%) mà không tăng độ chính xác.
   - Orchestrator đắt nhất (55.71, gấp đôi workflow) dù không gọi model. Lý do là investigator gọi gấp đôi số tool (5.57).
   - Swarm đắt thứ hai (49.57) và là shape duy nhất có dao động giữa các seed.
3. **Không dùng cột steps để so mức "gọn" giữa các shape.** `steps` đếm số event mỗi shape tự ghi vào trace, không đếm việc thật sự làm. Swarm có 2.80 steps nhưng thực hiện khoảng 7.7 lần gọi model và tool mỗi trial; single có 6.21 steps cho khoảng 6.6 lần gọi. Để so khối lượng việc, dùng hai cột model calls và tool calls. Phân tích chi tiết và ablation single vs swarm (`src/reports/ablation_r4_single_vs_swarm.json`) ở `report/team/research_card.md`.
4. **Hệ quả cho quyết định kiến trúc.** Trên bộ public, task claim là chuỗi tuần tự: đọc claim, đọc đơn, tính tiền, gọi host. Shape ít tự chủ nhất (workflow) đã đạt độ chính xác tối đa với chi phí thấp nhất, nên số liệu public không cho thấy lợi ích nào của việc thêm model hay thêm agent. Kết luận này chỉ dựa trên 14 claim public và MockLLM; bộ hidden (40 claim) có thể thay đổi thứ hạng nếu có claim mà quy trình cố định không xử lý được.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

...

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
