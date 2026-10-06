# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Mai Hoàng Anh | 2A202602857 | 100% |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `openai:gpt-4o-mini`, `0`, `60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `0.7.21`, Windows 11 (chạy trực tiếp)
- Số lần chạy tác vụ đã dùng / ngân sách: 21 / 24
- Commit của tag `freeze`: `6ee1fd5`

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Điều kiện `subagents` sẽ đạt điểm tương đương hoặc nhỉnh hơn `baseline` trên các tác vụ đánh giá nhờ khả năng phân tách luồng công việc giúp ngăn ngừa hiện tượng lặp vô hạn (như từng thấy ở `data-learn`), nhưng chi phí token trung bình sẽ cao hơn do overhead mô tả vai trò các subagent.
- H2 (skills-auto so với baseline): Điều kiện `skills-auto` sẽ không tạo ra sự khác biệt vượt trội hoặc có thể tương đương `baseline` trên tác vụ đánh giá do cơ chế nạp dần khiến tác tử thường bỏ qua việc đọc skill (`skills_read = 0`), đồng thời các quy ước mới của tác vụ đánh giá chưa từng xuất hiện trong phản hồi lỗi mà curator đã học (phù hợp với phát hiện của nghiên cứu SkillsBench và SkillEvolBench).
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trung bình trên tác vụ đánh giá sẽ thấp hơn hoặc xấp xỉ tác vụ học ở mọi điều kiện, do tác vụ đánh giá bổ sung thêm các quy ước tổ chức mới (`house rules`) và các trường hợp biên dữ liệu mới mà tác tử chưa từng tiếp xúc.

## 3. Làm quen Deep Agents (Phần 0.3)

1. **Các công cụ của tác tử mặc định & công cụ chạy lệnh:**
   - Tác tử mặc định có 9 công cụ:
     - Công cụ tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`.
     - Công cụ shell: `execute`.
     - Công cụ subagent: `task`.
   - Công cụ cho phép chạy lệnh hệ thống là `execute`.

2. **Mô tả của `task` về `general-purpose` & ngữ cảnh nhìn thấy:**
   - Mô tả nêu: `general-purpose` là tác tử đa năng dùng cho việc nghiên cứu các câu hỏi phức tạp, tìm kiếm file/nội dung, và thực thi các tác vụ nhiều bước (có đầy đủ công cụ như tác tử chính).
   - Về ngữ cảnh: Mặc định mỗi lần gọi là phi trạng thái (stateless), subagent chỉ nhìn thấy duy nhất nội dung prompt được tác tử chính truyền vào khi gọi lệnh, không nhìn thấy lịch sử hội thoại trước đó của tác tử chính và chỉ trả về một báo cáo cuối cùng.

3. **Trích dẫn hướng dẫn hành vi từ mô tả công cụ:**
   - Từ mô tả công cụ `task`: *"Put full detail in the prompt and state exactly what it should return — unless an agent type below says it inherits your conversation instead."*
   - Từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `rule_changelog` | E. Vi phạm quy ước tổ chức | `detail`: `"RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets)."` |
| `code-learn` | `rule_type_hints` | E. Vi phạm quy ước tổ chức | `detail`: `"RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value."` |
| `code-learn` | `rule_regression_tests` | E. Vi phạm quy ước tổ chức | `detail`: `"RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass."` |
| `code-learn` | `csv_quoting_follows_docstring` | A. Bỏ qua đặc tả | `detail`: `"to_csv_row returned 'Desk, large \"oak\",10.00,2'"` (tác tử sửa code nhưng không bọc trích dẫn theo đúng docstring). |
| `code-learn` | `parse_price_all_formats` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `detail`: `"wrong for: ['(12.00)']"` (mô hình chỉ xử lý xóa dấu phẩy `,`, bỏ qua định dạng số âm kế toán trong ngoặc đơn). |
| `data-learn` | `rule_clean_csv` | E. Vi phạm quy ước tổ chức | `detail`: `"RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; ..."` |
| `logs-learn` | `rule_service_names` | E. Vi phạm quy ước tổ chức | `detail`: `"RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service)."` |
| `logs-learn` | `rule_sorted_errors` | E. Vi phạm quy ước tổ chức | `detail`: `"RULE: \`errors\` is sorted by service, then by timestamp_utc, ascending."` |
| `logs-learn` | `rule_schema_header` | E. Vi phạm quy ước tổ chức | `detail`: `"RULE: the top-level object has \"schema_version\": 2 and \"generated_by\": \"log-triage\"."` |

Nhận xét:
- **Nhóm lỗi chiếm đa số**: Nhóm **E (Vi phạm quy ước tổ chức / House Rules)** chiếm đa số tuyệt đối (toàn bộ 9/9 check quy ước thất bại ở cả 3 tác vụ học, đối chiếu số liệu từ `scripts/check_breakdown.py`: `house rules = 0/9`). Các quy tắc này bắt đầu bằng `RULE:` không hề có trong đề bài `instruction.md` mà do bot đánh giá nội bộ quy định.
- **Bằng chứng phủ định cho các nhóm A-D**: Các check kỹ thuật thuần túy mô hình vẫn giải quyết được một phần (`technical = 4/18` ở baseline trên `code-learn`, vượt qua 4 hàm logic).
- **Khả năng phòng ngừa của Skill**: Skill hoàn toàn **CÓ THỂ** phòng ngừa nhóm lỗi E nếu bộ tuyển chọn (`curator`) trích xuất các phản hồi quy tắc từ trường `detail` thành các checklist hành động trong `SKILL.md` và nạp vào prompt cho tác tử.

## 5. Điều kiện `subagents` (Phần 2.3)

- **Các subagent đã định nghĩa**:
  - `explorer`: Khảo sát cấu trúc sandbox, đọc README, docstring, schema trước khi can thiệp. Không sửa đổi tệp.
  - `implementer`: Trực tiếp chỉnh sửa code, tính toán dữ liệu, chạy script kiểm tra theo chỉ dẫn cụ thể.
  - `reviewer`: Kiểm tra độc lập các điều kiện biên, định dạng và quy tắc đề bài sau khi hoàn thành.
- **`subagent_calls` ở từng tác vụ và nhận xét**:
  - `code-learn`: 0 lần (tác tử chính tự dùng công cụ tệp và shell trực tiếp để sửa code).
  - `data-learn`: 1 lần (tác tử chính nhận diện tác vụ phân tích số liệu phức tạp nên đã ủy quyền cho subagent `implementer`).
  - `logs-learn`: 0 lần (tác tử chính tự đọc log và trích xuất).
  - *Nhận xét*: Tác tử LLM có xu hướng tự xử lý trực tiếp khi prompt chỉ khuyến khích chứ không ép buộc, và chỉ giao việc khi cảm thấy khối lượng xử lý nhiều bước.
- **Thông tin thiếu hoặc thừa khi giao việc**:
  - Ở `data-learn`, lời giao việc của tác tử chính: `{"description": "Analyze the sales data in 'workspace/sales.csv' to compute the following metrics: 1. Calculate 'north_q1_revenue' ... 2. Count distinct orders ... 3. Determine 'top_region' ... 4. Count distinct orders with missing 'amount' ... 5. Count and remove duplicate rows ... Output the results in 'workspace/answer.json' in the required format.", "subagent_type": "implementer"}`.
  - *Đánh giá*: Thông tin giao việc rất đầy đủ và bám sát đề bài. Tuy nhiên subagent `implementer` lại tự ý giả định có sẵn thư viện `pandas` và cố cài đặt thất bại trong môi trường sandbox cô lập thay vì viết script dùng module chuẩn `csv` của Python.
- **Ảnh hưởng đến token và thời gian**:
  - Ở `data-learn`: `baseline` bị lặp vô hạn chạm trần 60 bước tốn **377,744 tokens** (126.0s), trong khi `subagents` chỉ tốn **101,144 tokens** (65.3s) — giảm ~73% token do subagent chặn được hiện tượng kẹt lặp vòng lặp của tác tử chính.
  - Ở `code-learn`: `subagents` tốn **37,459 tokens** (cao hơn baseline 22,341 tokens do system prompt chứa thêm đặc tả các subagents).
  - Ở `logs-learn`: `subagents` tốn **20,058 tokens** (thấp hơn baseline 29,140 tokens và thời gian chỉ mất 9.3s so với 207.4s).

## 6. Self-evolving: skill do curator sinh (Phần 3)

- **Số lần chạy curator**: 1 lần (sinh 3 skill hợp lệ, không có skill nào bị xóa).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `prevent-file-modification` | Tổng quát (hướng dẫn bảo vệ các file kiểm thử gốc) | Đúng (khớp với yêu cầu kiểm thử không được sửa test có sẵn) | 12 dòng; `description`: "Use this skill to ensure that original test files are not modified during development."; `skills_read = 0` |
| `validate-data-format` | Tổng quát (hướng dẫn tiền kiểm tra và bắt lỗi parsing dữ liệu) | Đúng (phù hợp với các bài toán xử lý dữ liệu bảng/log) | 12 dòng; `description`: "Use this skill to ensure that data formats are correctly parsed and validated before processing."; `skills_read = 0` |
| `enforce-type-annotations` | Tổng quát (hướng dẫn bổ sung chú thích kiểu cho public functions) | Đúng (khớp với quy ước tổ chức `rule_type_hints` của Acme review bot) | 12 dòng; `description`: "Use this skill to ensure that all public functions have type annotations for parameters and return values."; `skills_read = 0` |

Nhận xét Phần 3.4:
- Cả 3 tác vụ học đều ghi nhận `skills_read = 0` (tác tử không chủ động gọi công cụ `read_file` để đọc bất kỳ skill nào).
- Nguyên nhân: Cơ chế nạp dần (*progressive disclosure*) của Deep Agents chỉ cung cấp `name` và `description` ở phần đầu; câu mô tả của các skill chưa đủ tính cưỡng chế hoặc tình huống kích hoạt chưa đủ sát với nội dung đề bài `instruction.md` để mô hình quyết định dừng lại tra cứu tài liệu trước khi bắt tay vào giải quyết tác vụ. Do đó, điểm số ở điều kiện `skills-auto` thực chất phản ánh hành vi mặc định kèm theo sự xáo trộn ngữ cảnh (sampling noise) chứ chưa tận dụng được tri thức thủ tục từ skill.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng so sánh tổng hợp sinh từ `python -m lab.compare`:

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 4/10 | 0/10 | 0/10 |
| data-learn | 0/8 | 0/8 | 0/8 |
| logs-learn | 0/9 | 1/9 | 1/9 |
| code-eval | 0/11 | 0/11 | 0/11 |
| data-eval | 0/9 | 3/9 | 0/9 |
| logs-eval | 1/10 | 0/10 | 1/10 |
| **Mean score - learning tasks** | 0.13 | 0.04 | 0.04 |
| **Mean score - evaluation tasks** | 0.03 | 0.11 | 0.03 |
| **Mean tokens per run** | 129,069 | 213,667 | 127,363 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Thống kê theo phân loại check từ `python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      1/18         0/12         115,063      0/3     
baseline      learn     4/18         0/9          143,075      0/3     
subagents     eval      3/18         0/12         374,447      0/3     
subagents     learn     1/18         0/9           52,887      0/3     
skills-auto   eval      1/18         0/12         114,675      0/3     
skills-auto   learn     1/18         0/9          140,052      0/3     
```

Các lần chạy có `error` và cách xử lý:
- `baseline/data-learn`: `GraphRecursionError` (chạm trần recursion limit 60) sau 126.0s (377,744 tokens).
- `baseline/code-eval`: `GraphRecursionError` sau 198.7s (283,366 tokens, 119 calls).
- `subagents/logs-eval`: `GraphRecursionError` sau 55.7s (186,045 tokens, 30 calls).
- `skills-auto/data-learn`: `GraphRecursionError` sau 117.1s (373,144 tokens, 30 calls).
- `skills-auto/code-eval`: `GraphRecursionError` sau 112.8s (248,044 tokens, 114 calls).
- *Cách xử lý*: Theo đúng thiết kế harness ở `03_runner.md`, hệ thống bắt ngoại lệ, không dừng chương trình, ghi nhận nguyên văn vào trường `error` của `run.json`, đồng thời sử dụng `agent.stream(stream_mode="values")` để lưu lại vết thực thi (`trace.md`) đến bước cuối cùng và chấm điểm trên thư mục workspace hiện hữu.
- *Kiểm soát sửa skill*: Toàn bộ các lần chạy đều ghi nhận `skills_modified = false`, công cụ `verify_freeze.py` xác nhận đạt chuẩn `OK`.

## 8. Phân tích

1. **So sánh tác vụ học và tác vụ đánh giá**:
   - Trên tác vụ **học**: `baseline` đạt điểm trung bình cao nhất (0.13), trong khi `subagents` và `skills-auto` đều đạt 0.04.
   - Trên tác vụ **đánh giá**: `subagents` vượt trội với điểm trung bình **0.11** (so với 0.03 của cả `baseline` và `skills-auto`), giải quyết được 3/9 check ở `data-eval`.
   - `baseline` đạt 0.13 ở tập học nhưng giảm xuống 0.03 ở tập đánh giá; đây là dấu hiệu cho thấy tác tử đơn lẻ bị giảm sút năng lực rõ rệt khi đối mặt với dữ liệu mới và bài toán có độ phức tạp cao hơn, dễ rơi vào trạng thái lặp vô hạn.

2. **Phân tách check kỹ thuật (`technical`) và check quy ước (`house rules`)**:
   - Thống kê từ `check_breakdown.py` chỉ ra rằng: Cả 3 điều kiện đều đạt **0/9** ở tập học và **0/12** ở tập đánh giá đối với nhóm check quy ước (`rule_*`). Toàn bộ điểm số đạt được của mọi điều kiện đều đến từ các check logic kỹ thuật.
   - Skill do curator sinh chưa giúp được nhóm check quy ước vì `skills_read = 0` (tác tử không đọc skill).
   - Đối với các quy ước **mới** của tác vụ đánh giá, skill của curator sinh ra trên tập học về mặt nguyên tắc không thể giúp được, vì curator không hề được tiếp cận phản hồi của tập đánh giá (đảm bảo không rò rỉ dữ liệu).

3. **Cơ chế dựa vào vết và `skills_read`**:
   - *Check đạt được*: Ở `subagents/data-eval`, việc phân quyền cho subagent `implementer` đã giúp tác tử hoàn thành 3 check kỹ thuật (`north_q1_orders`, `missing_amount_orders`, `duplicate_rows_removed`) nhờ việc phân tách luồng viết script xử lý dữ liệu chuẩn xác.
   - *Check không giúp*: Ở `skills-auto/code-learn`, check `rule_type_hints` vẫn không đạt mặc dù curator đã sinh ra skill `enforce-type-annotations`. Vết `trace.md` và trường `skills_read = 0` khẳng định tác tử không hề mở file `SKILL.md` ra đọc, nên hoàn toàn không biết đến sự tồn tại của quy ước này.

4. **Chi phí token**:
   - Số token trung bình mỗi lần chạy: `skills-auto` (127,363) $\approx$ `baseline` (129,069) < `subagents` (213,667).
   - Đa tác tử tốn thêm khoảng 65% token so với baseline do chi phí ngữ cảnh mô tả subagents và thông điệp trao đổi qua lại giữa tác tử chính và tác tử con. Tuy nhiên, trên tập đánh giá, `subagents` là điều kiện duy nhất ghi nhận điểm số tiến bộ (0.11), do đó chi phí token tăng thêm là hoàn toàn xứng đáng cho các tác vụ phân tích phức tạp.

5. **Dấu hiệu rò rỉ dữ liệu hoặc quá khớp**:
   - Không có bất kỳ dấu hiệu rò rỉ dữ liệu nào: Hàm `validate_skill` và thiết kế bộ lọc của `curator.py` đã loại trừ toàn bộ dữ liệu có `role == "eval"` và đối chiếu với `eval_markers()`. Các file `SKILL.md` sinh ra đều là các bước hướng dẫn quy trình mang tính tổng quát (12 dòng mỗi skill), không chứa bất kỳ tên file, giá trị hay hằng số nào của tập đánh giá.
   - Về quá khớp (overfitting): Do tác tử không đọc skill (`skills_read = 0`), hiện tượng quá khớp tri thức thủ tục chưa tác động tiêu cực đến tác tử, nhưng về mặt nội dung, các skill sinh ra chỉ bám theo phản hồi của tập học nên không bao quát được quy tắc mới của tập đánh giá.

6. **Đo lường nhiễu (Sampling noise)**:
   - Điểm tác vụ học của cùng bộ skill `skills-auto` ở Phần 3.4 (lưu tại `results/skills-auto-dev`) đạt tổng cộng 3/27 check (~0.111, trong đó `code-learn` đạt 2/10).
   - Khi chạy lại chính thức sau đóng băng (sau tag `freeze`), điểm tác vụ học đạt 1/27 check (~0.037, `code-learn` 0/10).
   - Độ chênh lệch do nhiễu: $|0.111 - 0.037| = 0.074$ (**7.4%**). Sự dao động 7.4% giữa hai lần chạy của cùng một bộ skill chỉ ra rằng độ bất định của mô hình LLM là đáng kể; mọi sự chênh lệch nhỏ trong bảng so sánh cần được đánh giá thận trọng và phải đối chiếu với vết `trace.md` cùng số lần đọc skill.

## 9. Hạn chế và tính hợp lệ

1. **Kích thước tập tác vụ nhỏ và số lần chạy đơn lẻ**: Mỗi họ bài toán chỉ gồm 1 tác vụ học và 1 tác vụ đánh giá (tổng 6 tác vụ), và mỗi cấu hình chỉ chạy một lần do giới hạn ngân sách API. Điều này làm giảm ý nghĩa thống kê của các giá trị trung bình.
2. **Nhiễu ngẫu nhiên của mô hình ngôn ngữ (Sampling Noise)**: Như đo đạc thực tế ở mục 8.6, độ dao động ngẫu nhiên giữa các lần chạy lên tới 7.4%, làm mờ ranh giới giữa sự cải thiện thực sự và biến động ngẫu nhiên nếu không chạy lặp lại nhiều lần.
3. **Cơ chế nạp dần phụ thuộc hoàn toàn vào quyết định tự chủ của LLM**: Việc Deep Agents chỉ cung cấp mô tả ngắn của skill mà không bắt buộc nạp nội dung khiến tác tử thường bỏ qua (`skills_read = 0`). Ngoài ra, thí nghiệm chỉ thực hiện trên một mô hình duy nhất (`gpt-4o-mini`), kết quả có thể thay đổi trên các mô hình có năng lực suy luận cao hơn.

## 10. Kết luận

Thí nghiệm chứng minh kiến trúc đa tác tử (`subagents`) đạt hiệu quả cao nhất trên các tác vụ đánh giá (điểm trung bình 0.11 so với 0.03 của baseline) nhờ khả năng phân tách luồng công việc để tránh kẹt lặp vòng lặp, dù chi phí token tăng 65%. Ngược lại, tác tử tự tiến hóa (`skills-auto`) với skill do mô hình tự sinh không cải thiện hiệu năng do tác tử không chủ động đọc tài liệu (`skills_read = 0`), khớp với kết luận từ nghiên cứu SkillsBench. Toàn bộ các quy ước tổ chức ngầm (`house rules`) đều thất bại ở cả 3 điều kiện do thiếu cơ chế kiểm tra bắt buộc trước khi kết thúc tác vụ. Độ nhiễu giữa các lần chạy đạt mức 7.4%, khẳng định việc đánh giá tác tử phải dựa trên bằng chứng vết thực thi thay vì chỉ dựa vào điểm số. Đề xuất cải tiến tiếp theo là bổ sung cơ chế cưỡng chế đọc checklist hoặc áp dụng vòng lặp tự phản biện (critic loop) trước khi hoàn tất công việc.

## Phụ lục

- **Lệnh đã chạy (theo thứ tự)**:
  1. `python scripts/tour.py`
  2. `pytest tests/test_01_provided.py tests/test_02_agent.py tests/test_03_runner.py tests/test_04_curator.py`
  3. `python -m lab.runner --condition baseline --tasks data-learn`
  4. `python -m lab.runner --condition baseline --tasks code-learn logs-learn`
  5. `python -m lab.runner --condition subagents --tasks learn`
  6. `python -m lab.curator`
  7. `python -m lab.runner --condition skills-auto --tasks learn` (sao lưu sang `results/skills-auto-dev`)
  8. `git add -A && git commit -m "hypotheses"`
  9. `git add -A && git commit --allow-empty -m "freeze skills" && git tag freeze`
  10. `python -m lab.runner --condition baseline --tasks eval`
  11. `python -m lab.runner --condition subagents --tasks eval`
  12. `python -m lab.runner --condition skills-auto --tasks all`
  13. `python scripts/verify_freeze.py`
  14. `python -m lab.compare > report/table.md`
  15. `python scripts/check_breakdown.py`
- **Ghi chú**: Đã lưu trữ toàn bộ các tệp kết quả `run.json` và `trace.md` trong thư mục `results/`.

