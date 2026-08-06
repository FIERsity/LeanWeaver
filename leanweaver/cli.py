"""LeanWeaver 命令行入口。

用法：
    leanweaver explain "<lean error message>"        # 解释一条报错
    leanweaver explain --code "..." "<msg>"           # 带出错代码
    echo "<msg>" | leanweaver explain                 # 从 stdin 读取
    leanweaver translate "<lean proof>"               # (开发中) 翻译证明
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
        result = explain(message, code=args.code, use_llm=args.llm, lang=args.lang)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print(f"Available languages: {available_languages()}", file=sys.stderr)
        return 2
    print(result.pretty())
    return 0


def _cmd_translate(args: argparse.Namespace) -> int:
    from .translate.llm import get_default_llm

    llm = get_default_llm()
    if llm is None:
        print(
            "证明翻译器尚未实现（roadmap 阶段 ②）。\n"
            "当前可先使用：leanweaver explain \"<报错>\"",
            file=sys.stderr,
        )
        return 1
    try:
        print(llm.translate_proof(args.message, target_lang=args.lang))
    except NotImplementedError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="leanweaver",
        description="让形式化证明对人类可读 —— Lean 4 中文错误解释器 + 证明翻译器",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_explain = sub.add_parser("explain", help="Explain a Lean error message")
    p_explain.add_argument("message", nargs="?", help="Lean error text (reads stdin if omitted)")
    p_explain.add_argument("--code", help="optional snippet of the offending code")
    p_explain.add_argument("--lang", default="en", choices=["en", "zh"], help="explanation language (default: en)")
    p_explain.add_argument("--llm", action="store_true", help="fall back to LLM when rules miss")
    p_explain.set_defaults(func=_cmd_explain)

    p_translate = sub.add_parser("translate", help="翻译形式化证明（开发中）")
    p_translate.add_argument("message", help="Lean 证明文本")
    p_translate.add_argument("--lang", default="zh", help="目标语言，默认 zh")
    p_translate.set_defaults(func=_cmd_translate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
