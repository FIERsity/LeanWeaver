import {
  ERROR_CODES,
  RULES,
  TEMPLATES,
  ErrorCategory,
  Template,
} from "./generated/rules";

/**
 * 纯规则报错解释引擎（TypeScript，零依赖，自包含）。
 * 逻辑与 Python 版 leanweaver/errors 等价：
 * 1. 归一化文本
 * 2. error code 优先（error(lean.xxx)）
 * 3. 文本规则顺序匹配
 * 4. 渲染模板（en/zh）
 */

export interface ExplainResult {
  category: ErrorCategory | "unknown";
  title: string;
  what: string;
  why: string[];
  fix: string[];
  example?: string | null;
  matchedKeyword?: string | null;
  lang: string;
}

function normalize(message: string): string {
  return message.replace(/\s+/g, " ").trim().toLowerCase();
}

export function classify(message: string): { category: ErrorCategory | "unknown"; matchedKeyword: string | null } {
  // 1. error code 优先
  const codeMatch = /error\(lean\.([a-zA-Z]+)\)/.exec(message);
  if (codeMatch) {
    const code = `lean.${codeMatch[1]}`;
    const cat = ERROR_CODES[code];
    if (cat) return { category: cat, matchedKeyword: code };
  }

  // 2. 文本规则顺序匹配
  const lowered = normalize(message);
  for (const rule of RULES) {
    if (lowered.includes(rule.keyword)) {
      return { category: rule.category, matchedKeyword: rule.keyword };
    }
  }

  return { category: "unknown", matchedKeyword: null };
}

/** 渲染解释（lang: en/zh）。 */
export function explain(message: string, lang: string = "en"): ExplainResult {
  const { category, matchedKeyword } = classify(message);
  const langKey = lang === "zh" ? "zh" : "en";
  // unknown 不在 TEMPLATES 里，用类型断言访问（访问不到时走下面的 !tpl 分支）
  const tpls = TEMPLATES[category as ErrorCategory];
  let tpl: Template | undefined;

  if (tpls) {
    tpl = tpls[langKey];
    // 该语言缺模板时回退英文
    if (!tpl) tpl = tpls["en"];
  }

  if (!tpl) {
    return {
      category,
      title: lang === "zh" ? "未能识别的错误" : "Unrecognized error",
      what:
        lang === "zh"
          ? "规则库还没收录这类报错。如果它经常出现，欢迎到仓库提 issue。"
          : "This error is not yet covered by the rule library. Open an issue if you see it often.",
      why: [],
      fix: [lang === "zh" ? "欢迎提 issue 补充模板" : "Open an issue to add a template"],
      example: null,
      matchedKeyword,
      lang,
    };
  }

  return {
    category,
    title: tpl.title,
    what: tpl.what,
    why: tpl.why,
    fix: tpl.fix,
    example: tpl.example ?? null,
    matchedKeyword,
    lang,
  };
}

/** 输出为多行文本（hover 展示用）。 */
export function pretty(result: ExplainResult): string {
  const isZh = result.lang === "zh";
  const lines: string[] = [`[${result.title}]`, "", result.what];
  if (result.why.length) {
    lines.push("", isZh ? "常见原因:" : "Common causes:");
    for (const w of result.why) lines.push(`  - ${w}`);
  }
  if (result.fix.length) {
    lines.push("", isZh ? "修复建议:" : "Fixes:");
    for (const f of result.fix) lines.push(`  - ${f}`);
  }
  if (result.example) {
    lines.push("", isZh ? "示例:" : "Example:", `  ${result.example}`);
  }
  if (result.matchedKeyword) {
    lines.push("", `(${isZh ? "命中关键词" : "matched"}: ${result.matchedKeyword})`);
  }
  return lines.join("\n");
}
