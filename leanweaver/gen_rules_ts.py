"""从 Python 规则库生成 TypeScript 规则文件（单一事实源 = Python）。

用法：
    python -m leanweaver.gen_rules_ts \
        --out /path/to/vscode-extension/src/generated/rules.ts

生成 rules.ts 内容：
- CATEGORIES: 类别名列表
- ERROR_CODES: {code -> category}
- RULES: [{keyword, category}]（按优先级排序）
- TEMPLATES: {category: {en: {...}, zh: {...}}}

扩展直接用这份 TS 做匹配，不依赖 Python CLI。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors.classify import _ERROR_CODES, _RULES, ErrorCategory
from .errors.templates import _load_templates


def _to_ts_string(s: str) -> str:
    """转成 TS 字符串字面量。"""
    return json.dumps(s, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 TS 规则文件")
    parser.add_argument("--out", required=True, help="输出 rules.ts 路径")
    args = parser.parse_args()

    en = _load_templates("en")
    zh = _load_templates("zh")

    # 类别列表（去掉 UNKNOWN）
    cats = [c.value for c in ErrorCategory if c != ErrorCategory.UNKNOWN]

    # error codes
    codes = {code: cat.value for code, cat in _ERROR_CODES.items()}

    # 文本规则（保持顺序）
    rules = [{"keyword": kw, "category": cat.value} for kw, cat in _RULES]

    # 模板（按类别，en + zh）
    templates = {}
    for cat in cats:
        e = en.get(ErrorCategory(cat))
        z = zh.get(ErrorCategory(cat))
        if e is None or z is None:
            continue
        templates[cat] = {
            "en": {"title": e["title"], "what": e["what"], "why": e["why"], "fix": e["fix"], "example": e.get("example")},
            "zh": {"title": z["title"], "what": z["what"], "why": z["why"], "fix": z["fix"], "example": z.get("example")},
        }

    # 正确生成 union type：每行以 | 开头
    union_lines = "\n  | ".join(_to_ts_string(c) for c in cats)

    ts = f"""// Auto-generated from Python rule library. DO NOT EDIT BY HAND.
// Source: leanweaver/errors (classify.py + locales)
// Regenerate: python -m leanweaver.gen_rules_ts --out vscode-extension/src/generated/rules.ts

export type ErrorCategory =
  | {union_lines};

export const CATEGORIES: ErrorCategory[] = {json.dumps(cats)};

export const ERROR_CODES: Record<string, ErrorCategory> = {json.dumps(codes)};

export interface Rule {{
  keyword: string;
  category: ErrorCategory;
}}

export const RULES: Rule[] = {json.dumps(rules)};

export interface Template {{
  title: string;
  what: string;
  why: string[];
  fix: string[];
  example?: string | null;
}}

export const TEMPLATES: Record<string, {{ en: Template; zh: Template }}> = {json.dumps(templates, ensure_ascii=False)};
"""

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(ts, encoding="utf-8")
    print(f"✅ 已生成 {out}（{len(cats)} 类, {len(rules)} 规则, {len(templates)} 模板）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
