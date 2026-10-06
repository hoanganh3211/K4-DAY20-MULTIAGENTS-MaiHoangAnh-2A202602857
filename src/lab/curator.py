"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    else:
        out_dir = Path(out_dir)

    results_path = Path(results_dir) / source_condition
    if not results_path.exists():
        print(f"Warning: Results path {results_path} does not exist.")
        return []

    runs = []
    for run_file in sorted(results_path.glob("*/run.json")):
        try:
            r = json.loads(run_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if r.get("role") != "learn":
            continue

        task_id = r.get("task", run_file.parent.name)
        failed_checks = []
        for c in r.get("checks", []):
            if not c.get("passed", False):
                failed_checks.append({
                    "name": c.get("name", ""),
                    "detail": c.get("detail", ""),
                })

        trace_file = run_file.parent / "trace.md"
        trace_text = ""
        if trace_file.exists():
            trace_text = trace_file.read_text(encoding="utf-8")[-6000:]

        runs.append({
            "task": task_id,
            "failed_checks": failed_checks,
            "trace": trace_text,
        })

    failed_runs = [run for run in runs if run["failed_checks"]]
    if not failed_runs:
        print("Warning: No failed checks found in learning tasks.")
        return []

    run_summaries = []
    for run in failed_runs:
        lines = [f"Task: {run['task']}"]
        lines.append("Failed checks:")
        for fc in run["failed_checks"]:
            lines.append(f"  - Check: {fc['name']}")
            if fc["detail"]:
                lines.append(f"    Feedback: {fc['detail']}")
        if run["trace"]:
            lines.append("Execution trace excerpt:")
            lines.append(run["trace"])
        run_summaries.append("\n".join(lines))

    prompt = (
        "You are writing reusable SKILL modules for a coding and data engineering assistant.\n"
        f"Below are failed checks (check names and evaluator feedback) and execution traces from training runs.\n"
        f"Identify common procedural errors and create up to {max_skills} concise skills to prevent them.\n\n"
        "Rules:\n"
        "- Skills must be general: do not mention specific task IDs, task-specific file names, hardcoded numbers or answers.\n"
        "- Each skill must have YAML frontmatter with 'name' (lowercase alphanumeric with hyphens, max 64 chars) "
        "and 'description' (one sentence explaining WHEN to use it, max 1024 chars), "
        "followed by at most 40 lines of imperative procedural instructions (e.g. checklists).\n"
        "- Exact output format for each skill:\n"
        "=== SKILL: <name> ===\n"
        "---\n"
        "name: <name>\n"
        "description: <when to use>\n"
        "---\n"
        "<instructions>\n"
        "=== END ===\n\n"
        "Failed runs:\n"
        + "\n\n---\n\n".join(run_summaries)
    )

    if model is None:
        model = make_model()

    reply = model.invoke(prompt)
    content = reply.content if hasattr(reply, "content") else str(reply)

    blocks = parse_skill_blocks(content)
    written = []
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue
        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        file_path = skill_dir / "SKILL.md"
        file_path.write_text(text, encoding="utf-8")
        written.append(file_path)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
