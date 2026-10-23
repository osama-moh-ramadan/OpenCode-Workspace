"""Dump authored lesson content to content/lessons/<id>.json, with validation.

Run after editing tools/lessons_*.py:

    python3 tools/build_lessons.py
    python3 tools/build.py          # refresh hasContent flags in curriculum.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "content", "lessons")
sys.path.insert(0, HERE)

from lessons_s1_a import LESSONS_S1_A  # noqa: E402
from lessons_s1_b import LESSONS_S1_B  # noqa: E402
from lessons_s1_c import LESSONS_S1_C  # noqa: E402
from lessons_s1_d import LESSONS_S1_D  # noqa: E402
from lessons_s2_a import LESSONS_S2_A  # noqa: E402
from lessons_s2_b import LESSONS_S2_B  # noqa: E402
from lessons_s2_c import LESSONS_S2_C  # noqa: E402
from lessons_s2_d import LESSONS_S2_D  # noqa: E402
from lessons_s2_e import LESSONS_S2_E  # noqa: E402
from lessons_s2_f import LESSONS_S2_F  # noqa: E402
from lessons_s2_g import LESSONS_S2_G  # noqa: E402
from lessons_s3_a import LESSONS_S3_A  # noqa: E402
from lessons_s3_b import LESSONS_S3_B  # noqa: E402
from lessons_s3_c import LESSONS_S3_C  # noqa: E402
from lessons_s3_d import LESSONS_S3_D  # noqa: E402
from lessons_s3_e import LESSONS_S3_E  # noqa: E402
from lessons_s3_f import LESSONS_S3_F  # noqa: E402
from lessons_s4_a import LESSONS_S4_A  # noqa: E402
from lessons_s4_b import LESSONS_S4_B  # noqa: E402
from lessons_s4_c import LESSONS_S4_C  # noqa: E402
from lessons_s4_d import LESSONS_S4_D  # noqa: E402
from lessons_s4_e import LESSONS_S4_E  # noqa: E402
from lessons_s5_a import LESSONS_S5_A  # noqa: E402
from lessons_s5_b import LESSONS_S5_B  # noqa: E402
from lessons_s5_c import LESSONS_S5_C  # noqa: E402
from lessons_s5_d import LESSONS_S5_D  # noqa: E402
from lessons_s5_e import LESSONS_S5_E  # noqa: E402
from lessons_s5_f import LESSONS_S5_F  # noqa: E402
from lessons_s5_g import LESSONS_S5_G  # noqa: E402
from lessons_s5_h import LESSONS_S5_H  # noqa: E402
from lessons_s6_a import LESSONS_S6_A  # noqa: E402
from lessons_s6_b import LESSONS_S6_B  # noqa: E402
from lessons_s6_c import LESSONS_S6_C  # noqa: E402
from lessons_s6_d import LESSONS_S6_D  # noqa: E402
from lessons_s6_e import LESSONS_S6_E  # noqa: E402
from lessons_s6_f import LESSONS_S6_F  # noqa: E402
from lessons_s6_g import LESSONS_S6_G  # noqa: E402
from lessons_s6_h import LESSONS_S6_H  # noqa: E402
from lessons_s6_i import LESSONS_S6_I  # noqa: E402
from lessons_s6_j import LESSONS_S6_J  # noqa: E402
from lessons_s6_k import LESSONS_S6_K  # noqa: E402
from lessons_s7_a import LESSONS_S7_A  # noqa: E402
from lessons_s7_b import LESSONS_S7_B  # noqa: E402
from lessons_s7_c import LESSONS_S7_C  # noqa: E402
from lessons_s7_d import LESSONS_S7_D  # noqa: E402
from lessons_s7_e import LESSONS_S7_E  # noqa: E402
from lessons_s7_f import LESSONS_S7_F  # noqa: E402
from lessons_s7_g import LESSONS_S7_G  # noqa: E402
from lessons_s7_h import LESSONS_S7_H  # noqa: E402
from lessons_s7_i import LESSONS_S7_I  # noqa: E402
from lessons_s8_a import LESSONS_S8_A  # noqa: E402
from lessons_s8_b import LESSONS_S8_B  # noqa: E402
from lessons_s8_c import LESSONS_S8_C  # noqa: E402
from lessons_s8_d import LESSONS_S8_D  # noqa: E402
from lessons_s8_e import LESSONS_S8_E  # noqa: E402
from lessons_s8_f import LESSONS_S8_F  # noqa: E402
from lessons_s8_g import LESSONS_S8_G  # noqa: E402
from lessons_s8_h import LESSONS_S8_H  # noqa: E402
from lessons_s8_i import LESSONS_S8_I  # noqa: E402
from lessons_s8_cap import LESSONS_S8_CAP  # noqa: E402
from lessons_s9_a import LESSONS_S9_A  # noqa: E402
from lessons_s9_b import LESSONS_S9_B  # noqa: E402
from lessons_s9_c import LESSONS_S9_C  # noqa: E402
from lessons_s9_d import LESSONS_S9_D  # noqa: E402
from lessons_s9_e import LESSONS_S9_E  # noqa: E402
from lessons_s9_f import LESSONS_S9_F  # noqa: E402
from lessons_s9_g import LESSONS_S9_G  # noqa: E402
from lessons_s9_cap import LESSONS_S9_CAP  # noqa: E402
from lessons_s10_a import LESSONS_S10_A  # noqa: E402
from lessons_s10_b import LESSONS_S10_B  # noqa: E402
from lessons_s10_c import LESSONS_S10_C  # noqa: E402
from lessons_s10_d import LESSONS_S10_D  # noqa: E402
from lessons_s10_e import LESSONS_S10_E  # noqa: E402

LESSONS = [*LESSONS_S1_A, *LESSONS_S1_B, *LESSONS_S1_C, *LESSONS_S1_D, *LESSONS_S2_A, *LESSONS_S2_B, *LESSONS_S2_C, *LESSONS_S2_D, *LESSONS_S2_E, *LESSONS_S2_F, *LESSONS_S2_G, *LESSONS_S3_A, *LESSONS_S3_B, *LESSONS_S3_C, *LESSONS_S3_D, *LESSONS_S3_E, *LESSONS_S3_F, *LESSONS_S4_A, *LESSONS_S4_B, *LESSONS_S4_C, *LESSONS_S4_D, *LESSONS_S4_E, *LESSONS_S5_A, *LESSONS_S5_B, *LESSONS_S5_C, *LESSONS_S5_D, *LESSONS_S5_E, *LESSONS_S5_F, *LESSONS_S5_G, *LESSONS_S5_H, *LESSONS_S6_A, *LESSONS_S6_B, *LESSONS_S6_C, *LESSONS_S6_D, *LESSONS_S6_E, *LESSONS_S6_F, *LESSONS_S6_G, *LESSONS_S6_H, *LESSONS_S6_I, *LESSONS_S6_J, *LESSONS_S6_K, *LESSONS_S7_A, *LESSONS_S7_B, *LESSONS_S7_C, *LESSONS_S7_D, *LESSONS_S7_E, *LESSONS_S7_F, *LESSONS_S7_G, *LESSONS_S7_H, *LESSONS_S7_I, *LESSONS_S8_A, *LESSONS_S8_B, *LESSONS_S8_C, *LESSONS_S8_D, *LESSONS_S8_E, *LESSONS_S8_F, *LESSONS_S8_G, *LESSONS_S8_H, *LESSONS_S8_I, *LESSONS_S8_CAP, *LESSONS_S9_A, *LESSONS_S9_B, *LESSONS_S9_C, *LESSONS_S9_D, *LESSONS_S9_E, *LESSONS_S9_F, *LESSONS_S9_G, *LESSONS_S9_CAP, *LESSONS_S10_A, *LESSONS_S10_B, *LESSONS_S10_C,
         *LESSONS_S10_D, *LESSONS_S10_E]

BLOCK_TYPES = {
    "text", "md", "markdown", "heading", "code", "callout", "table",
    "steps", "terms", "quiz", "tasks", "checkpoints", "resources",
}
CALLOUT_KINDS = {"tip", "warn", "note", "goal", "danger"}
LANGS = {"csharp", "json", "bash", "yaml", "xml", "sql", "dockerfile", "http", "javascript", "python", "css", "text"}

problems = []


def check_code(block, where):
    if "code" not in block:
        problems.append(f"{where}: code block without 'code'")
        return
    lang = (block.get("lang") or "").lower()
    if lang and lang not in LANGS:
        problems.append(f"{where}: unknown lang '{lang}'")


def check_block(block, where):
    kind = block.get("type")
    if kind not in BLOCK_TYPES:
        problems.append(f"{where}: unknown block type {kind!r}")
        return
    if kind == "code":
        check_code(block, where)
    elif kind == "callout":
        if block.get("kind") not in CALLOUT_KINDS:
            problems.append(f"{where}: bad callout kind {block.get('kind')!r}")
        if not (block.get("md") or block.get("text")):
            problems.append(f"{where}: empty callout")
    elif kind in ("text", "md", "markdown"):
        if not (block.get("md") or block.get("text")):
            problems.append(f"{where}: empty text block")
    elif kind == "heading":
        if not block.get("text"):
            problems.append(f"{where}: empty heading")
    elif kind == "table":
        if not block.get("rows"):
            problems.append(f"{where}: table without rows")
        head = block.get("head") or []
        widths = {len(r) for r in block["rows"] if isinstance(r, list)}
        if head and widths and widths != {len(head)}:
            problems.append(f"{where}: table rows {widths} do not match head width {len(head)}")
    elif kind in ("steps", "terms", "checkpoints", "resources"):
        items = block.get("items")
        if not items:
            problems.append(f"{where}: {kind} without items")
        if kind == "resources":
            for it in items or []:
                if not it.get("url", "").startswith(("http://", "https://")):
                    problems.append(f"{where}: resource without http(s) url: {it}")
    elif kind == "quiz":
        questions = block.get("questions") or []
        if not questions:
            problems.append(f"{where}: quiz without questions")
        for qi, q in enumerate(questions, start=1):
            opts = q.get("options") or []
            if len(opts) < 2:
                problems.append(f"{where}: q{qi} needs >=2 options")
            ans = q.get("answer")
            if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                problems.append(f"{where}: q{qi} answer index {ans!r} out of range")
            if not q.get("explain"):
                problems.append(f"{where}: q{qi} has no explanation")
    elif kind == "tasks":
        items = block.get("items") or []
        if not items:
            problems.append(f"{where}: tasks without items")
        for ti, task in enumerate(items, start=1):
            if not task.get("title"):
                problems.append(f"{where}: task{ti} without title")
            if not task.get("criteria"):
                problems.append(f"{where}: task{ti} without acceptance criteria")


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    written = 0
    seen_ids = set()

    for lesson in LESSONS:
        lid = lesson.get("id")
        if not lid:
            problems.append("lesson without id")
            continue
        if lid in seen_ids:
            problems.append(f"duplicate lesson id {lid}")
        seen_ids.add(lid)

        blocks = lesson.get("blocks") or []
        if not blocks:
            problems.append(f"{lid}: no blocks")
        for bi, block in enumerate(blocks, start=1):
            check_block(block, f"{lid}/block{bi}")

        path = os.path.join(OUT, f"{lid}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(lesson, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        written += 1
        size = os.path.getsize(path)
        kinds = {}
        for b in blocks:
            kinds[b.get("type")] = kinds.get(b.get("type"), 0) + 1
        print(f"  {lid:<12} {size:>7,} B  blocks={len(blocks):>2}  {kinds}")

    print(f"\n{written} lesson files -> {OUT}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
