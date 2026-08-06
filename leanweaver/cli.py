"""LeanWeaver 命令行入口。

纯规则、零 LLM 依赖。只有一个功能：解释 Lean 报错。

用法：
    leanweaver explain "<lean error message>"        # 解释一条报错
    leanweaver explain --lang zh "<msg>"             # 中文解释
    echo "<msg>" | leanweaver explain                 # 从 stdin 读取
"""

from __future__ import annotations

import argparse
import sys


def _cmd_explain(args: argparse.Namespace) -> int:
    from .errors.explain import explain
    from .errors.templates import available_languages

    message = args.message
    if not message and not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    if not message:
        print('Error: missing error message. Usage: leanweaver explain "<error>"', file=sys.stderr)
        return 2

    try:
        result = explain(message, code=args.code, lang=args.lang)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print(f"Available languages: {available_languages()}", file=sys.stderr)
        return 2
    print(result.pretty())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="leanweaver",
        description="纯规则、零 LLM 的 Lean 4 报错解释器",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_explain = sub.add_parser("explain", help="Explain a Lean error message (rule-based)")
    p_explain.add_argument("message", nargs="?", help="Lean error text (reads stdin if omitted)")
    p_explain.add_argument("--code", help="optional snippet of the offending code")
    p_explain.add_argument("--lang", default="en", choices=["en", "zh"], help="explanation language (default: en)")
    p_explain.set_defaults(func=_cmd_explain)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
