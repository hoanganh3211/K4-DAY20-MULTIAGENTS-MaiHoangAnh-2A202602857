"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use proactively to explore the workspace, inspect files, check logs, "
                "or examine documentation (README, docstrings, data schemas) before making modifications. "
                "The explorer only investigates and reports factual findings; it never modifies files."
            ),
            "system_prompt": (
                "You are an exploratory subagent. Your role is to examine the sandbox, inspect file contents, "
                "read logs or documentation, and report factual findings back to the main agent. "
                "Do NOT modify any files. Be concise, accurate, and cite specific filenames and line excerpts."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use to execute specific code modifications, process/clean data files, or fix bugs "
                "according to precise instructions, and verify the changes by running scripts or tests. "
                "Always provide full context and target file paths in the delegation prompt."
            ),
            "system_prompt": (
                "You are an implementation subagent. Your role is to perform specific coding, data processing, "
                "or bug fixing tasks as instructed by the main agent. Modify only the necessary files, "
                "and execute tests or scripts using the shell to verify correctness before returning a final summary."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use independently after changes or data outputs are produced to verify that all task instructions, "
                "formatting rules, and edge cases are satisfied. The reviewer inspects modified files and runs checks, "
                "reporting any discrepancies without making changes."
            ),
            "system_prompt": (
                "You are an independent reviewer subagent. Your role is to strictly verify that the completed work "
                "satisfies all constraints, schemas, and requirements from the instructions. "
                "Check edge cases, inspect output files, run verification tests, and report any defects found. "
                "Do NOT modify files."
            ),
        },
    ]
