"""从 Lean 官方源码提取权威错误消息定义。

来源：leanprover/lean4 源码 src/Lean 里的 throwError 调用。
这些是**官方写死的错误消息原文**——最权威、不经过 LLM 的语料。

输出：JSON 列表，每条 {file, line, message} 其中 message 是官方定义的报错文本模板。

用法：
    python -m leanweaver.extract_official --src /path/to/lean4/src/Lean --out data/official_errors.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 匹配 throwError 的错误消息（支持 "..." 字符串、m!"..." 多行插值）
_PATTERNS = [
    # throwError "plain string"
    re.compile(r'throwError\s+"((?:[^"\\]|\\.)*)"', re.S),
    # throwError m!"... "（带格式的，可能多行）
    re.compile(r'throwError\s+m!"((?:[^"\\]|\\.)*)"', re.S),
    # throwError s!"..."（纯字符串插值，不保留，因为含变量）
]


def extract_from_file(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    found: list[dict] = []
    for pattern in _PATTERNS[:2]:  # 只用前两个（纯文本 + m!格式）
        for m in pattern.finditer(text):
            msg = m.group(1)
            # 清理：去掉转义、缩进、插值语法留下的空格
            msg = msg.replace('\\"', '"').replace("\\n", "\n")
            # 跳过太短/太长的（噪音）
            if len(msg.strip()) < 5 or len(msg) > 500:
                continue
            # 跳过明显含插值变量 {} 的（模板，不是完整报错）
            if "{" in msg:
                continue
            # 行号
            line = text[: m.start()].count("\n") + 1
            found.append({"file": str(path.relative_to(path.parent.parent.parent)), "line": line, "message": msg.strip()})
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="从 Lean 源码提取官方错误消息")
    parser.add_argument("--src", required=True, help="lean4 源码 src/Lean 目录")
    parser.add_argument("--out", default="data/official_errors.json")
    args = parser.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f"目录不存在: {src}", file=sys.stderr)
        return 1

    all_msgs: list[dict] = []
    for f in src.rglob("*.lean"):
        all_msgs.extend(extract_from_file(f))

    # 去重（按消息文本）
    seen = set()
    uniq = []
    for m in all_msgs:
        key = m["message"][:80]
        if key not in seen:
            seen.add(key)
            uniq.append(m)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": "lean4 src/Lean throwError", "count": len(uniq), "items": uniq}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 提取 {len(uniq)} 条官方错误消息 → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
