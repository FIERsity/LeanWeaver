import * as vscode from "vscode";

/**
 * 输出面板：把 leanweaver 的纯文本输出渲染成可读的 HTML。
 *
 * 关键：所有颜色都用 VS Code 主题 CSS 变量（--vscode-*），
 * 这样深色/浅色主题都能自动适配，不会出现"一团黑/亮白框"。
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
    { enableScripts: false, localResourceRoots: [] }
  );
  panel.onDidDispose(() => {
    panel = undefined;
  });
  return panel;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * 轻量 Markdown 渲染（足够覆盖 leanweaver 输出格式）：
 * - 代码块 ```lean ... ```
 * - 行内代码 `x`
 * - 标题（# / ## / 【x】）
 * - 加粗 **x**
 * - 无序列表 - item
 * - 分隔线 / 换行
 */
function renderMarkdown(text: string): string {
  const lines = text.split("\n");
  const out: string[] = [];
  let inCode = false;
  let codeBuf: string[] = [];

  for (const line of lines) {
    // 代码块
    if (/^\s*```/.test(line)) {
      if (inCode) {
        out.push(`<pre class="code">${escapeHtml(codeBuf.join("\n"))}</pre>`);
        codeBuf = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeBuf.push(line);
      continue;
    }

    const trimmed = line.trim();
    if (!trimmed) {
      out.push('<div class="gap"></div>');
      continue;
    }

    // 标题：### / ## / # 或【xxx】
    let m = /^(#{1,3})\s+(.*)$/.exec(trimmed);
    if (m) {
      const level = m[1].length;
      const cls = level === 1 ? "h1" : level === 2 ? "h2" : "h3";
      out.push(`<div class="${cls}">${inline(m[2])}</div>`);
      continue;
    }
    m = /^【([^】]+)】$/.exec(trimmed);
    if (m) {
      out.push(`<div class="h1">${inline(m[1])}</div>`);
      continue;
    }

    // 分隔线
    if (/^[-=]{3,}$/.test(trimmed)) {
      out.push('<div class="hr"></div>');
      continue;
    }

    // 无序列表
    m = /^[-*•]\s+(.*)$/.exec(trimmed);
    if (m) {
      out.push(`<div class="li">• ${inline(m[1])}</div>`);
      continue;
    }

    // 普通段落
    out.push(`<div class="p">${inline(line)}</div>`);
  }
  if (inCode && codeBuf.length) {
    out.push(`<pre class="code">${escapeHtml(codeBuf.join("\n"))}</pre>`);
  }
  return out.join("\n");
}

/** 行内元素：加粗、行内代码、强调 */
function inline(s: string): string {
  let t = escapeHtml(s);
  // 行内代码 `x`
  t = t.replace(/`([^`\n]+)`/g, (_m, code) => `<code>${code}</code>`);
  // 加粗 **x**
  t = t.replace(/\*\*([^*]+)\*\*/g, (_m, b) => `<strong>${b}</strong>`);
  // 斜体 *x*
  t = t.replace(/(^|[^*])\*([^*\n]+)\*/g, (_m, pre, i) => `${pre}<em>${i}</em>`);
  return t;
}

export function showOutput(title: string, content: string) {
  const p = ensurePanel();
  p.title = title;
  p.webview.html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {
    /* 全部使用 VS Code 主题变量，深浅主题自适应 */
    color-scheme: light dark;
  }
  body {
    margin: 0;
    padding: 16px 18px;
    font-family: var(--vscode-font-family, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif);
    font-size: var(--vscode-font-size, 13px);
    line-height: 1.7;
    color: var(--vscode-editor-foreground, #d4d4d4);
    background-color: var(--vscode-editor-background, #1e1e1e);
  }
  .h1 {
    font-size: 15px; font-weight: 600;
    color: var(--vscode-editor-foreground, #d4d4d4);
    border-bottom: 1px solid var(--vscode-panel-border, #454545);
    padding-bottom: 6px; margin: 14px 0 8px;
  }
  .h2 {
    font-size: 14px; font-weight: 600;
    color: var(--vscode-symbolIcon-propertyForeground, #9cdcfe);
    margin: 12px 0 6px;
  }
  .h3 {
    font-size: 13px; font-weight: 600;
    color: var(--vscode-textLink-foreground, #4fc1ff);
    margin: 10px 0 4px;
  }
  .p { margin: 6px 0; }
  .li { margin: 3px 0 3px 8px; }
  .gap { height: 6px; }
  .hr {
    border-top: 1px solid var(--vscode-panel-border, #454545);
    margin: 12px 0;
  }
  pre.code {
    background-color: var(--vscode-textCodeBlock-background, #2d2d2d);
    color: var(--vscode-editor-foreground, #d4d4d4);
    border: 1px solid var(--vscode-panel-border, #454545);
    border-radius: 4px;
    padding: 10px 12px;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: var(--vscode-editor-font-family, Menlo, Monaco, "Courier New", monospace);
    font-size: var(--vscode-editor-font-size, 12px);
    margin: 8px 0;
  }
  code {
    background-color: var(--vscode-textCodeBlock-background, #2d2d2d);
    color: var(--vscode-textPreformat-foreground, #ce9178);
    border-radius: 3px;
    padding: 1px 5px;
    font-family: var(--vscode-editor-font-family, Menlo, Monaco, monospace);
    font-size: 0.95em;
  }
  strong { font-weight: 600; }
  em { font-style: italic; }
  .muted {
    color: var(--vscode-descriptionForeground, #8a8a8a);
    font-size: 11px;
    margin-top: 18px;
  }
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
