import * as vscode from "vscode";
import { explain, pretty } from "./engine";
import { getLang } from "./lang";

/**
 * 报错悬停解释（核心 UX）—— 纯规则引擎内嵌，零 CLI 依赖。
 *
 * 用户把鼠标悬停在 Lean 诊断（红波浪线）上时，
 * 用内置规则引擎（TypeScript）直接解释，毫秒级、离线。
 */

// 缓存：诊断文本 -> 解释（同一报错不重复算）
const cache = new Map<string, { text: string; ts: number }>();
const CACHE_TTL = 10 * 60 * 1000; // 10 分钟

function getCached(message: string): string | undefined {
  const hit = cache.get(message);
  if (hit && Date.now() - hit.ts < CACHE_TTL) return hit.text;
  if (hit) cache.delete(message);
  return undefined;
}

function setCached(message: string, text: string) {
  cache.set(message, { text, ts: Date.now() });
}

export function registerHoverProvider(context: vscode.ExtensionContext) {
  const provider = vscode.languages.registerHoverProvider(
    [{ language: "lean4" }, { language: "lean" }],
    {
      async provideHover(document, position) {
        // 1. 找到该位置的诊断
        const diags = vscode.languages.getDiagnostics(document.uri);
        const diag = diags.find(
          (d) =>
            d.range.contains(position) &&
            d.severity === vscode.DiagnosticSeverity.Error
        );
        if (!diag || !diag.message) return undefined;

        // 2. 缓存命中
        const cached = getCached(diag.message);
        if (cached) {
          return new vscode.Hover(new vscode.MarkdownString(cached, true), diag.range);
        }

        // 3. 用内置引擎解释（纯规则，毫秒级，零依赖）
        const lang = getLang();
        const result = explain(diag.message, lang);
        const isZh = lang === "zh";
        const header = isZh ? "**LeanWeaver 解释**" : "**LeanWeaver**";
        const text = `${header}\n\n${pretty(result)}`;
        setCached(diag.message, text);
        return new vscode.Hover(new vscode.MarkdownString(text, true), diag.range);
      },
    }
  );

  context.subscriptions.push(provider);
}
