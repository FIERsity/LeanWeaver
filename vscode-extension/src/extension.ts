import * as vscode from "vscode";
import { exec } from "child_process";
import * as path from "path";

/**
 * LeanWeaver VS Code extension.
 *
 * 核心思路：复用 Python CLI（leanweaver），把输出渲染到 Webview 面板。
 * - translate: 翻译当前 Lean 文件中的证明（中文可读 + 逐行注释）
 * - check:     解释当前文件的所有报错
 *
 * 需要本机已安装 leanweaver（pip install leanweaver）和 lean（elan）。
 */

let panel: vscode.WebviewPanel | undefined;

function getConfig(): { cli: string; lang: string } {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  return {
    cli: cfg.get<string>("leanweaverCli", "python3 -m leanweaver"),
    lang: cfg.get<string>("lang", "zh"),
  };
}

/** 执行 leanweaver 命令，返回 stdout。 */
function runLeanweaver(args: string[]): Promise<string> {
  const { cli } = getConfig();
  const cmd = `${cli} ${args.join(" ")}`;
  return new Promise((resolve, reject) => {
    exec(cmd, { cwd: vscode.workspace.rootPath ?? undefined, timeout: 120000 }, (err, stdout, stderr) => {
      if (err) {
        // 非零退出码（如 check 有错误）也可能是正常结果，stdout 里有内容就返回
        if (stdout && stdout.trim()) {
          resolve(stdout);
        } else {
          reject(new Error(stderr || err.message));
        }
        return;
      }
      resolve(stdout);
    });
  });
}

/** 把纯文本转成 HTML 展示（简单转义）。 */
function textToHtml(text: string): string {
  const esc = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return esc(text).replace(/\n/g, "<br>");
}

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

function renderResult(title: string, content: string): void {
  const p = ensurePanel();
  p.title = title;
  p.webview.html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; padding: 16px; }
    pre { background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; white-space: pre-wrap; word-wrap: break-word; }
    h3 { color: #569cd6; }
  </style>
</head>
<body>
  <h3>${title}</h3>
  <pre>${textToHtml(content)}</pre>
</body>
</html>`;
}

/** 收集当前文件的证明相关源码（整文件传给 CLI 由 parser 提取）。 */
async function currentDocument(): Promise<string | undefined> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("LeanWeaver: 请先打开一个 .lean 文件");
    return undefined;
  }
  return editor.document.getText();
}

export function activate(context: vscode.ExtensionContext) {
  // translate: 翻译证明
  const translateCmd = vscode.commands.registerCommand("leanweaver.translate", async () => {
    const src = await currentDocument();
    if (src === undefined) return;
    const { lang } = getConfig();
    const tmp = path.join(context.extensionPath, ".tmp");
    const { writeFileSync, mkdirSync } = require("fs");
    mkdirSync(tmp, { recursive: true });
    const f = path.join(tmp, "input.lean");
    writeFileSync(f, src);
    vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "LeanWeaver 正在翻译证明…" },
      async () => {
        try {
          const out = await runLeanweaver([`translate "${f}"`, `--lang ${lang}`]);
          renderResult("LeanWeaver · 证明翻译", out);
        } catch (e: any) {
          vscode.window.showErrorMessage(`LeanWeaver 翻译失败: ${e.message}`);
        }
      }
    );
  });

  // check: 解释报错
  const checkCmd = vscode.commands.registerCommand("leanweaver.check", async () => {
    const src = await currentDocument();
    if (src === undefined) return;
    const { lang } = getConfig();
    const tmp = path.join(context.extensionPath, ".tmp");
    const { writeFileSync, mkdirSync } = require("fs");
    mkdirSync(tmp, { recursive: true });
    const f = path.join(tmp, "input.lean");
    writeFileSync(f, src);
    vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "LeanWeaver 正在分析报错…" },
      async () => {
        try {
          const out = await runLeanweaver([`check "${f}"`, `--lang ${lang}`]);
          renderResult("LeanWeaver · 报错解释", out);
        } catch (e: any) {
          vscode.window.showErrorMessage(`LeanWeaver 检查失败: ${e.message}`);
        }
      }
    );
  });

  const openCmd = vscode.commands.registerCommand("leanweaver.openPanel", () => {
    ensurePanel();
  });

  context.subscriptions.push(translateCmd, checkCmd, openCmd);
}

export function deactivate() {}
