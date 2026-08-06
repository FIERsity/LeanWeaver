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


export function registerHoverProvider(context: vscode.ExtensionContext) {
  const provider = vscode.languages.registerHoverProvider([{ language: "lean4" }, { language: "lean" }], {
    async provideHover(document, position) {
      // 1. 找到该位置的诊断
      const diags = vscode.languages.getDiagnostics(document.uri);
      const diag = diags.find((d) => {
        return d.range.contains(position) && d.severity === vscode.DiagnosticSeverity.Error;
      });
      if (!diag || !diag.message) return undefined;
      console.log(`[LeanWeaver hover] 命中诊断: ${diag.message.split("\n")[0].slice(0, 60)}`);

      // 2. 尝试缓存
      const cached = getCached(diag.message);
      if (cached) {
        return new vscode.Hover(
          new vscode.MarkdownString(cached, true),
          diag.range
        );
      }

      // 3. 调用 leanweaver（规则层快，异常时提示而非静默）
      try {
        const explanation = await explainError(diag.message);
        // 直接存原始文本，让 MarkdownString 原生渲染（自动适配主题）
        const md = `**LeanWeaver 解释**\n\n${explanation.trim()}`;
        setCached(diag.message, md);
        return new vscode.Hover(new vscode.MarkdownString(md, true), diag.range);
      } catch (e: any) {
        console.error(`[LeanWeaver] explain 失败: ${e.message}`);
        // CLI 不可用时给个提示，而不是完全静默
        return new vscode.Hover(
          new vscode.MarkdownString(`**LeanWeaver**\n\n⚠️ 未找到 leanweaver CLI（${e.message}）。\n请安装: \`pip install leanweaver\``, true),
          diag.range
        );
      }
    },
  });

  context.subscriptions.push(provider);
}
