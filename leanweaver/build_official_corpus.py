"""从 Lean 官方测试构建报错语料库。

来源：lean4 仓库 tests/elab 和 tests/elab_fail 下的
`.lean.expected.out` 文件——官方验证过的"代码 → 确切报错"。

每个 expected.out 里是形如 `file.lean:行:列: error: <报错>` 的行。
我们提取这些 error 文本，用 leanweaver 分类器测覆盖，输出语料 + 覆盖报告。

用法：
    python -m leanweaver.build_official_corpus --lean4 /path/to/lean4 --out data/official_corpus.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from .errors.classify import classify_error, ErrorCategory

# 匹配报错起始行。Lean 的列范围格式是 LINE:STARTCOL-LINE:ENDCOL（如 7:14-7:17）
_ERROR_START = re.compile(
    r"^\S+\.lean:(\d+):(\d+)(?:-(\d+):(\d+))?:\s*(error|warning)(?:\(([^)]*)\))?:\s*(.*)$"
)


def extract_errors(expected_text: str) -> list[str]:
    """从 expected.out 提取所有报错/警告文本（含多行）。"""
    errors = []
    lines = expected_text.splitlines()
    i = 0
    while i < len(lines):
        m = _ERROR_START.match(lines[i])
        if m:
            groups = m.groups()
            # groups: (line, startcol, endline?, endcol?, severity, code?, message)
            severity = groups[4]
            first_msg = groups[6]
            # 跳过环境噪音
            if "unknown module prefix" in first_msg:
                i += 1
                continue
            # 收集后续行（报错通常跨多行，直到下一个 error/warning 或非缩进行）
            collected = [first_msg.strip()]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if _ERROR_START.match(nxt):
                    break
                if nxt.strip() and not nxt.startswith((" ", "\t")) and not nxt.strip().startswith(("⊢", "case", "with errors", "Note:")):
                    break
                collected.append(nxt.rstrip())
                j += 1
            errors.append("\n".join(collected).strip())
            i = j
        else:
            i += 1
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="从 Lean 官方测试构建报错语料")
    parser.add_argument("--lean4", required=True, help="lean4 仓库路径（需要 git 可访问）")
    parser.add_argument("--out", default="data/official_corpus.json")
    parser.add_argument("--sample", type=int, default=0, help="只抽样 N 条（0=全部）")
    args = parser.parse_args()

    lean4 = Path(args.lean4)
    # 用 git ls-tree 列出 expected.out（不依赖本地检出全部文件）
    subdirs = ["tests/elab_fail", "tests/elab"]
    expected_files: list[str] = []
    for sd in subdirs:
        r = subprocess.run(
            ["git", "-C", str(lean4), "ls-tree", "-r", "--name-only", "HEAD", sd],
            capture_output=True, text=True,
        )
        for line in r.stdout.splitlines():
            if line.endswith(".expected.out") or line.endswith(".out.expected"):
                expected_files.append(line)

    print(f"找到 {len(expected_files)} 个官方报错期望文件")

    corpus = []
    seen = set()
    for ef in expected_files:
        # 读文件内容
        r = subprocess.run(
            ["git", "-C", str(lean4), "show", f"HEAD:{ef}"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            continue
        errors = extract_errors(r.stdout)
        for msg in errors:
            # 按完整报错文本去重（多行报错也能区分）
            if msg in seen:
                continue
            seen.add(msg)
            cat = classify_error(msg).category
            corpus.append({
                "source_file": ef,
                "error_text": msg,
                "category": cat.value if cat != ErrorCategory.UNKNOWN else "unknown",
                "recognized": cat != ErrorCategory.UNKNOWN,
            })

    if args.sample:
        corpus = corpus[: args.sample]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"source": "lean4 official tests", "count": len(corpus), "items": corpus},
        ensure_ascii=False, indent=2,
    ), encoding="utf-8")

    recog = sum(1 for c in corpus if c["recognized"])
    print(f"\n✅ 语料 {len(corpus)} 条 → {args.out}")
    print(f"识别率: {recog}/{len(corpus)} = {recog/len(corpus)*100:.1f}%")
    print("\n未识别样例（我们的规则库缺口）:")
    for c in corpus:
        if not c["recognized"]:
            print(f"  [{c['source_file'].split('/')[-1]}] {c['error_text'][:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
