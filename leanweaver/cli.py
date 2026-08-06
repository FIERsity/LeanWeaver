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


def _cmd_check(args: argparse.Namespace) -> int:
    from .check import check_file

    try:
        result = check_file(args.path, use_llm=args.llm, lang=args.lang)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not result.diagnostics:
        print(f"✓ {args.path}: no diagnostics")
        return 0

    print(f"{args.path}: {result.error_count} error(s), {result.warning_count} warning(s)\n")
    for diag, exp in zip(result.diagnostics, result.explanations):
        loc = f"{diag.line}:{diag.column}"
        print(f"── {loc} [{diag.severity}] ──")
        print(diag.data.splitlines()[0])
        print(exp.pretty())
        print()
    return 0 if result.error_count == 0 else 1


def _cmd_translate(args: argparse.Namespace) -> int:
    from .translate.llm import get_default_llm
    from .translate.proof import translate_source

    llm = get_default_llm()
    if llm is None:
        print(
            "未配置 LLM。证明翻译器需要模型。\n"
            "设置环境变量：\n"
            "  LEANWEAVER_LLM_PROVIDER=openai  +  OPENAI_API_KEY=...\n"
            "  或 LEANWEAVER_LLM_PROVIDER=ollama（本地 Ollama）",
            file=sys.stderr,
        )
        return 1

    # 支持从文件读取：leanweaver translate <file.lean> [--theorem NAME]
    source = args.message
    if args.message.endswith(".lean"):
        from pathlib import Path

        try:
            source = Path(args.message).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    try:
        results = translate_source(
            source, theorem_name=args.theorem, target_lang=args.lang, llm=llm
        )
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not results:
        print("（未找到证明块）", file=sys.stderr)
        return 1
    for r in results:
        print(r.pretty())
        print("\n" + "=" * 60 + "\n")
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

    p_check = sub.add_parser("check", help="Analyze a .lean file and explain all diagnostics")
    p_check.add_argument("path", help="path to .lean file")
    p_check.add_argument("--lang", default="en", choices=["en", "zh"], help="explanation language (default: en)")
    p_check.add_argument("--llm", action="store_true", help="fall back to LLM when rules miss")
    p_check.set_defaults(func=_cmd_check)

    p_translate = sub.add_parser("translate", help="Translate a formal proof into readable prose (needs LLM)")
    p_translate.add_argument("message", help="Lean source text or path to a .lean file")
    p_translate.add_argument("--theorem", help="only translate this theorem (default: all)")
    p_translate.add_argument("--lang", default="zh", choices=["zh", "en"], help="target language (default: zh)")
    p_translate.set_defaults(func=_cmd_translate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
