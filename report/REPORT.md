# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Mai Hoàng Anh | 2A202602857 | 100% |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `openai:gpt-4o-mini`, `0`, `60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `0.7.21`, Windows 11 (chạy trực tiếp)
- Số lần chạy tác vụ đã dùng / ngân sách: 0 / 18
- Commit của tag `freeze`: *(Chưa thực hiện - sẽ cập nhật ở Phần 4.1)*

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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
