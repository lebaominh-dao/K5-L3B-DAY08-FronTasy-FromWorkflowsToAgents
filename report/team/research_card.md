# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R4 · Evaluation confounders |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | J. Zhang, L. Zhang, P. Lu et al. (Rice University, Case Western Reserve University), *Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems*, arXiv:2609.05933v1, 5/9/2026, https://arxiv.org/abs/2609.05933 (code: https://github.com/chili-lab/rethinking-mas-efficiency-eval). Slide ghi EMNLP 2026; bản arXiv v1 không ghi venue. Loại bằng chứng: benchmark chẩn đoán có kiểm soát |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Các đánh giá hiện có có thể phóng đại khả năng tăng hiệu quả của các phương pháp MAS efficiency (pruning agent/edge, tìm topology gọn): gain thường được đo dưới prompt và topology khởi đầu riêng của từng phương pháp nên khó quy cho thay đổi cấu trúc, và nhiều thành công nằm ở setting không đòi hỏi MAS, nơi một agent đơn hoặc random pruning đã giữ được hiệu năng |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Paper đo các phương pháp pruning/topology search (GPTSwarm, AgentPrune, AgentDropout, AGP, DAGP) với LLM thật, chung backbone, agent registry và runtime, trên 6-agent setting và 4 task. Lab này dùng MockLLM seeded, 14 claim public, 4 shape viết tay; không có pruning, token và giá là giả lập, latency `unavailable`. Ta chỉ mượn nguyên tắc "cố định mọi thứ trừ topology", không kiểm lại kết quả của paper |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Đổi D swarm → B single, giữ nguyên mọi thứ khác: pass rate tăng khoảng +0.01 đến +0.02 (bỏ được trial swarm tin delay trong ticket ở seed 55), seed variance về 0, cost/success giảm khoảng 30–35%. Metric `steps` sẽ KHÔNG so được giữa hai shape vì nó đếm event trong trace, phụ thuộc cách mỗi shape ghi trace chứ không phải topology. Ghi chú trung thực: hypothesis viết sau một lần chạy thử cùng lệnh |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, `config/tools.manifest.v1.1.yaml`, seed 11,22,33,44,55, `data/public_claims.jsonl` (14 claim), `config/pricing.yaml`, evaluator `lab8.metrics.trial_pass`, as_of 2026-11-15, SQLite mới cho mỗi trial, cùng host `durability.issue_refund`. Biến duy nhất được thay đổi: topology (swarm → single) |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: swarm tin số ngày trễ ghi trong ticket thay vì order row khi seed % 5 == 0, đo bằng pass rate, pass^5 và seed variance. Confounder cần loại: `steps` đếm event trace, nên so khối lượng việc bằng `mean_model_calls` và `mean_tool_calls` thay cho `steps` |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes single,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r4_single_vs_swarm.json`
- Run id / file report: `src/reports/ablation_r4_single_vs_swarm.json` (70 trial mỗi shape); trial swarm fail duy nhất: `R-swarm-C-002-s55`
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu:

  | Metric | single (B) | swarm (D) | Chênh B − D |
  | --- | --- | --- | --- |
  | pass rate | 1.000 | 0.986 | +0.014 |
  | pass^5 | 1.000 | 0.929 | +0.071 |
  | seed variance | 0.000000 | 0.000816 | về 0 |
  | cost/success (VND giả lập) | 32.39 | 49.57 | −34.6% |
  | mean model calls | 3.79 | 3.00 | +0.79 |
  | mean tool calls | 2.79 | 4.66 | −1.87 |
  | mean steps (event trace) | 6.21 | 2.80 | không so được |

  - Pass rate, pass^5, variance: **đúng hypothesis**. Chênh lệch nằm trọn ở một trial (`R-swarm-C-002-s55`: ticket ghi trễ 5 ngày, order row ghi 2 ngày, swarm trả `resolved` thay vì `denied`). Đây là khác biệt do cách shape quyết định, vì tool, seed, giá và host là chung.
  - Cost/success: **đúng hướng (−34.6%), nhưng chỉ kết luận được một phần**. Single gọi model nhiều hơn (3.79 so với 3.00); swarm đắt hơn vì nhiều tool call hơn (4.66 so với 2.79), một phần do cách viết reference (đọc claim view hai lần), chưa tách được khỏi topology.
  - Steps: **xác nhận confounder**. Swarm có `steps` 2.80 dù thực hiện khoảng 7.7 hành động/trial, single có 6.21 cho khoảng 6.6 hành động. Kết luận "swarm ít bước hơn" từ cột này là sai do cách đo, đúng loại rủi ro paper cảnh báo.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Chỉ 14 claim public × 5 seed, chênh lệch pass rate đến từ 1 trial nên không đủ để khẳng định ý nghĩa thống kê. Kết luận chỉ áp dụng cho bộ public của lab, không suy rộng ra "single tốt hơn swarm".

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
