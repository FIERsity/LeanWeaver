"""从 GitHub issue 收集真实 Lean 报错语料。

原理：Lean 社区用户报 bug / 求助时，会在 issue 正文里贴：
- 能复现报错的完整 Lean 代码（```lean 代码块）
- 报错文本（通常在 /- ERROR: ... -/ 注释 或 "error:" 之后）

这些是"真实用户遇到的真实报错"，比手工构造的样本更有价值。

用法：
    python -m leanweaver.collect_issues --owner leanprover --repo lean4 \
        --keywords "type mismatch,application type mismatch,unsolved goals" \
        --out data/issues_corpus.json

输出 JSON：每条含 {issue_url, title, error_text, category, code}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

from .errors.classify import classify_error, ErrorCategory

# GitHub 搜索 API
SEARCH_API = "https://api.github.com/search/issues"


def gh_search(keyword: str, owner: str, repo: str, per_page: int = 30) -> list[dict]:
    """用 GitHub search API 搜 issue。"""
    q = f"repo:{owner}/{repo} is:issue \"{keyword}\" in:body"
    url = f"{SEARCH_API}?q={urllib.parse.quote(q)}&per_page={per_page}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("items", [])
    except Exception as exc:
        print(f"搜索失败 [{keyword}]: {exc}", file=sys.stderr)
        return []


# 从 issue 正文提取报错文本
# 报错通常在 "ERROR:" 注释里，形如：
#   /-\nERROR:\n(kernel) application type mismatch\n  ...\n-/
# 或正文中的 "error: ..." 行
def extract_errors(body: str) -> list[str]:
    errors: list[str] = []
    # 1. ERROR: 注释块（最常见）
    for m in re.finditer(r"/-\s*(?:.*?\n)?ERROR:\s*(.*?)-/", body, re.S):
        block = m.group(1).strip()
        # 去掉行首缩进和多余符号
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if lines:
            errors.append("\n".join(lines[:15]))
    # 2. "error: ..." 文本
    for m in re.finditer(r"(?:^|\n)\s*(?:error|Error):\s*(.*?)(?=\n\s*(?:error|Error)|\Z)", body, re.S):
        txt = m.group(1).strip()
        if txt and len(txt) > 5 and "lean" not in txt.lower()[:20]:
            errors.append(txt[:300])
    return errors


# 提取 issue 里的 lean 代码块
def extract_lean_code(body: str) -> list[str]:
    return re.findall(r"```lean\s*\n(.*?)```", body, re.S)


def main() -> int:
    parser = argparse.ArgumentParser(description="从 GitHub issue 收集真实 Lean 报错")
    parser.add_argument("--owner", default="leanprover")
    parser.add_argument("--repo", default="lean4")
    parser.add_argument("--keywords", default="type mismatch,application type mismatch,unsolved goals,unknown identifier")
    parser.add_argument("--out", default="data/issues_corpus.json")
    parser.add_argument("--per-keyword", type=int, default=10)
    args = parser.parse_args()

    import urllib.parse  # noqa: F401

    corpus = []
    seen = set()
    for kw in [k.strip() for k in args.keywords.split(",") if k.strip()]:
        print(f"搜索: {kw} ...")
        items = gh_search(kw, args.owner, args.repo, args.per_keyword)
        for it in items:
            num = it.get("number")
            if num in seen:
                continue
            seen.add(num)
            body = it.get("body") or ""
            errors = extract_errors(body)
            code = extract_lean_code(body)
            if not errors and not code:
                continue
            for err in errors:
                cat = classify_error(err).category
                corpus.append({
                    "issue": f"{args.owner}/{args.repo}#{num}",
                    "title": it.get("title", ""),
                    "url": it.get("html_url", ""),
                    "error_text": err,
                    "category": cat.value if cat != ErrorCategory.UNKNOWN else "unknown",
                    "has_code": bool(code),
                })
        print(f"  → {len(items)} issues, 累计 {len(corpus)} 条报错")

    # 去重（按 error_text）
    uniq = {}
    for c in corpus:
        key = c["error_text"][:100]
        if key not in uniq:
            uniq[key] = c
    final = list(uniq.values())

    import pathlib

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": "GitHub issues", "count": len(final), "items": final}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 已写入 {len(final)} 条真实报错 → {args.out}")
    print("类别分布:")
    from collections import Counter

    for cat, n in Counter(c["category"] for c in final).most_common():
        print(f"  {cat}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
