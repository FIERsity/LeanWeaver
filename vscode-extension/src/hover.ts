import * as vscode from "vscode";
import { explainError } from "./leanweaver";

/**
 * 报错悬停解释（杀手级 UX）。
 *
 * 当用户把鼠标悬停在 Lean 诊断（红波浪线）上时，除了 VS Code 显示原始英文报错，
 * 我们再叠加一条 leanweaver 的中文解释。
 *
 * 实现：注册 hover provider，读取该位置的诊断，把诊断 message 交给
 * leanweaver explain（规则层，毫秒级），以 MarkdownString 追加显示。
 */

// 缓存：诊断文本 -> 解释（同一报错不重复调用）
const cache = new Map<string, { html: string; ts: number }>();
const CACHE_TTL = 10 * 60 * 1000; // 10 分钟

function getCached(message: string): string | undefined {
  const hit = cache.get(message);
  if (hit && Date.now() - hit.ts < CACHE_TTL) return hit.html;
  if (hit) cache.delete(message);
  return undefined;
}

function setCached(message: string, html: string) {
  cache.set(message, { html, ts: Date.now() });
}

/** 把解释文本转成 HTML 片段（简单转义 + 换行）。 */
function toHtml(text: string): string {
  const esc = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // 去掉首行【标题】的方括号，保留结构
  return esc(text).replace(/\n/g, "<br>");
}

export function registerHoverProvider(context: vscode.ExtensionContext) {
  const provider = vscode.languages.registerHoverProvider("lean", {
    async provideHover(document, position) {
      // 1. 找到该位置的诊断
      const diags = vscode.languages.getDiagnostics(document.uri);
      const diag = diags.find((d) => {
        return d.range.contains(position) && d.severity === vscode.DiagnosticSeverity.Error;
      });
      if (!diag || !diag.message) return undefined;

      // 2. 尝试缓存
      const cached = getCached(diag.message);
      if (cached) {
        return new vscode.Hover(
          new vscode.MarkdownString(`**LeanWeaver 解释**\n\n${cached}`, true),
          diag.range
        );
      }

      // 3. 调用 leanweaver（规则层快，异常时静默降级为不显示）
      try {
        const explanation = await explainError(diag.message);
        const html = toHtml(explanation);
        setCached(diag.message, html);
        return new vscode.Hover(
          new vscode.MarkdownString(
            `**LeanWeaver 中文解释**\n\n${html}`,
            true
          ),
          diag.range
        );
      } catch (e) {
        // 不打断用户：leanweaver 不可用时保持 VS Code 原始 hover
        return undefined;
      }
    },
  });

  context.subscriptions.push(provider);
}
