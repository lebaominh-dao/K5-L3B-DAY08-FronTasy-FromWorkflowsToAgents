# Team

## Thông tin nhóm

- Tên nhóm: FronTasy
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-FronTasy-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: [pending]

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Đào Lê Bảo Minh | 2A202604010 | 26ai.minhdlb@vinuni.edu.vn | https://github.com/lebaominh-dao | workflow + integration |
|   2 | Nguyễn Đức Hải | 2A202603943 | ndhai255.work@gmail.com | https://github.com/ndhai255 | single agent |
|   3 | Nguyễn Văn Lên | 2A202604007 | [pending] | [pending] | orchestrator + handoff |
|   4 | Cao Phạm Thành Đạt | 2A202603970 | 26ai.datcpt@vinuni.edu.vn | https://github.com/tcaopham216-gif | ledger + evaluation |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Đào Lê Bảo Minh | workflow + integration | `f504017` (workflow CP2), `ea8639f` (workflow CP3: truyền `crash_at`), `158d7f9` (test approval) | `src/tests/test_workflow_approval_gate.py` (thêm mới, 6 trường hợp) |
| Nguyễn Đức Hải | single agent | `528121c` (single CP2 và CP3), `c2e0aa0` (test retry, approval, canary), `01f66f8` (test host từ chối, trần 8 bước) | `src/tests/test_single_shape.py` (thêm mới, 5 test chạy trên swarm và single) |
| Cao Phạm Thành Đạt | ledger + evaluation | `dc76b0e` | `src/tests/test_shape_durability.py` (20 trường hợp trên bốn shape) |
| Nguyễn Văn Lên | orchestrator + handoff | `443e207` (orchestrator CP2 và CP3), `a2ea4fd` (test approval) | `src/tests/test_trace_privacy.py` (thêm mới, quét trace/stdout/stderr của 3 shape × 14 claim) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202604010_DaoLeBaoMinh

### Phần việc phụ trách

- Shape A `workflow` (`src/lab8/shapes/workflow.py`): CP2, CP3 và rà các nhánh approval ở CP4.
- Integration: review và merge PR của các thành viên vào `main`, giữ cổng host `python -m pytest -q` xanh.

### Đóng góp cụ thể

- `f504017`: viết workflow theo 7 bước cố định. Tiền do `compute_compensation` tính, shape truyền quote đầy đủ vào `durability.issue_refund`, mọi nhánh return đều ghi trace qua `finish()`. Workflow không gọi MockLLM.
- `ea8639f`: truyền `crash_at` xuống `issue_refund` và không bắt `InjectedCrash`, để T12 crash rồi resume vẫn chỉ có một refund.
- `158d7f9`: thêm `src/tests/test_workflow_approval_gate.py`, kiểm 6 kiểu approval hỏng, mỗi kiểu chạy hai lần.
- Merge PR #2 (orchestrator), #3 và #4 (single) vào `main`.

### Bằng chứng

- `python -m pytest -q -m student -o addopts= -k workflow`: 62 passed.
- `python -m pytest -q tests/test_workflow_approval_gate.py`: 6 passed.
- PR của phần workflow: #1, #5, #6. Báo cáo cá nhân: `report/team/2A202604010_DaoLeBaoMinh.md`.

## 2A202603943_NguyenDucHai

### Phần việc phụ trách

- Shape B `single` (`src/lab8/shapes/single.py`): CP2, CP3 và test riêng cho shape.
- Research card R4 kèm ablation single vs swarm; phần so sánh 4 shape trong `report/team/group_report.md`.

### Đóng góp cụ thể

- `528121c`: viết single theo ReAct. `decide()` chỉ chọn tool đọc (`get_claim_view`, `lookup_order`, `compute_compensation`) và tự giữ memory; tiền do `compute_compensation` tính, shape truyền quote đầy đủ cùng `crash_at` vào `durability.issue_refund`, không nuốt `InjectedCrash`. Trace chỉ ghi field allowlist.
- `c2e0aa0`, `01f66f8`: thêm `src/tests/test_single_shape.py` gồm 5 test (gọi lại cùng claim, mượn approval claim khác, canary leak, host từ chối vẫn giữ quote đầy đủ, dừng đúng 8 bước), chạy trên cả swarm và single.
- `b029bbb`: điền research card R4 và `src/reports/ablation_r4_single_vs_swarm.json`.

### Bằng chứng

- `python -m pytest -q -m student -o addopts= -k "single and not swarm and not workflow and not orchestrator"`: 86 passed.
- `python -m pytest -q tests/test_single_shape.py -o addopts=`: 37 passed.
- PR của phần single: #3, #4, #8, #13. Báo cáo cá nhân: `report/team/2A202603943_NguyenDucHai.md`.

## 2A202603970_CaoPhamThanhDat

### Phần việc phụ trách

- Thành viên 4, phụ trách ledger và evaluation. Kiểm thử retry, approval, trace và crash trên cả bốn shape, chạy crash suite và benchmark public.

### Đóng góp cụ thể

- `dc76b0e`: thêm `src/tests/test_shape_durability.py` và báo cáo `src/reports/benchmark.json`, `src/reports/crash.json`.

### Bằng chứng

- Crash suite 20/20. Benchmark public gồm 280 lượt thử, có một lượt lỗi của Swarm là `R-swarm-C-002-s55`.
- [PR #9](https://github.com/lebaominh-dao/K5-L3B-DAY08-FronTasy-FromWorkflowsToAgents/pull/9). [Báo cáo cá nhân](report/team/2A202603970_CaoPhamThanhDat.md).

## 2A202604007_NguyenVanLen

### Phần việc phụ trách

- Shape C: Orchestrator + handoff; rà trace/stdout của ba shape.

### Đóng góp cụ thể

- `443e207`: triển khai orchestrator dùng `make_handoff`, investigator chỉ đọc, quote từ order view và host `issue_refund` với quote đầy đủ cùng `crash_at`.
- `a2ea4fd`Thêm `src/tests/test_trace_privacy.py` để rà secret và dữ liệu riêng tư trong trace/stdout/stderr của ba shape.

### Bằng chứng

- `python -m pytest -q -m student -o addopts= -k orchestrator`: 62 passed.
- `python -m pytest -q tests/test_trace_privacy.py`: 42 passed.
- Báo cáo cá nhân: `report/team/2A202604007_NguyenVanLen.md`.
