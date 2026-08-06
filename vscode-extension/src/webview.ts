import * as vscode from "vscode";

/**
 * 输出面板：把 leanweaver 的纯文本输出渲染成可读的 HTML。
 */

let panel: vscode.WebviewPanel | undefined;

function ensurePanel(): vscode.WebviewPanel {
  if (panel) {
    panel.reveal();
    return panel;
  }
  panel = vscode.window.createWebviewPanel(
    "leanweaver",
    "LeanWeaver",
    vscode.ViewColumn.Beside,
    { enableScripts: false }
  );
  panel.onDidDispose(() => {
    panel = undefined;
  });
  return panel;
}

/** 简单 Markdown-ish 渲染：标题/粗体/代码/换行 */
function renderMarkdown(text: string): string {
  const esc = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  let html = esc(text);
  // 代码块 ```...```
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (_m, _lang, code) => {
    return `<pre class="code">${code.trim()}</pre>`;
  });
  // 行内代码 `xxx`
  html = html.replace(/`([^`\n]+)`/g, (_m, code) => `<code>${code}</code>`);
  // 粗体 **xxx**
  html = html.replace(/\*\*([^*]+)\*\*/g, (_m, t) => `<strong>${t}</strong>`);
  // 【标题】行
  html = html.replace(/【([^】]+)】/g, (_m, t) => `<h4>${t}</h4>`);
  // 换行
  html = html.replace(/\n/g, "<br>");
  return html;
}

export function showOutput(title: string, content: string) {
  const p = ensurePanel();
  p.title = title;
  p.webview.html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         padding: 16px; line-height: 1.7; color: #333; }
  h4 { color: #007acc; margin: 12px 0 4px; }
  pre.code { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px;
             white-space: pre-wrap; word-wrap: break-word; font-size: 13px; }
  code { background: #f0f0f0; padding: 1px 5px; border-radius: 3px; }
  strong { color: #c7254e; }
  .muted { color: #888; font-size: 12px; margin-top: 16px; }
</style>
</head>
<body>
  ${renderMarkdown(content)}
  <div class="muted">— LeanWeaver · 让形式化证明可读 —</div>
</body>
</html>`;
}

export function closePanel() {
  if (panel) panel.dispose();
}
