import * as vscode from "vscode";

/**
 * 内联补全（Copilot 式 ghost text）——纯粹的核心功能。
 *
 * 用户按快捷键 → 上下文（含 proof state）注入 → 光标下方生成虚字补全 → Tab 接受。
 *
 * 实现：InlineCompletionItemProvider（VS Code 原生机制，Copilot 同款）。
 */

// 找到光标所在位置的定理名 + 该定理已写的行
function findTheoremContext(document: vscode.TextDocument, position: vscode.Position) {
  const lines = document.getText().split("\n");
  const cursorLine = position.line;
  let theoremName: string | undefined;
  let theoremStart = -1;

  for (let i = cursorLine; i >= 0; i--) {
    const m = /\b(theorem|lemma|example|def)\s+([A-Za-z_][A-Za-z0-9_']*)?/.exec(lines[i]);
    if (m && m[2]) {
      theoremName = m[2];
      theoremStart = i;
      break;
    }
  }
  if (!theoremName || theoremStart < 0) return undefined;

  // 收集从定理声明到光标之间的行（去掉 import/注释）
  const written: string[] = [];
  for (let i = theoremStart + 1; i < cursorLine; i++) {
    const t = lines[i].trim();
    if (t && !t.startsWith("--") && !t.startsWith("/-") && !t.startsWith("import")) {
      written.push(t);
    }
  }
  return { theoremName, theoremStart, written };
}

/** 把整个文件写临时文件，调 CLI complete，返回补全文本。 */
async function getCompletion(
  source: string,
  theoremName: string,
  numLines: number
): Promise<string> {
  const { execFile } = await import("child_process");
  const fs = await import("fs");
  const os = await import("os");
  const path = await import("path");

  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const cli = cfg.get<string>("leanweaverCli", "python3 -m leanweaver");

  const dir = path.join(os.tmpdir(), "leanweaver-inline");
  fs.mkdirSync(dir, { recursive: true });
  const f = path.join(dir, `input-${Date.now()}.lean`);
  fs.writeFileSync(f, source);

  const cmd = `${cli} complete "${f}" --theorem "${theoremName}" --lines ${numLines}`;
  return new Promise<string>((resolve, reject) => {
    execFile("/bin/bash", ["-c", cmd], { timeout: 60000 }, (err, stdout, stderr) => {
      fs.unlink(f, () => {});
      if (err && !stdout) {
        reject(new Error(stderr || err.message));
        return;
      }
      resolve(stdout.trim());
    });
  });
}

export function registerInlineCompletion(context: vscode.ExtensionContext) {
  const provider: vscode.InlineCompletionItemProvider = {
    async provideInlineCompletionItems(
      document,
      position,
      _context,
      token
    ): Promise<vscode.InlineCompletionItem[] | vscode.InlineCompletionList> {
      // 只在 Lean 文件里工作
      if (document.languageId !== "lean") {
        return { items: [] };
      }

      const ctx = findTheoremContext(document, position);
      if (!ctx) return { items: [] };
      // 光标必须在定理内部（声明行之后）
      if (position.line <= ctx.theoremStart) return { items: [] };

      const numLines = vscode.workspace
        .getConfiguration("leanweaver")
        .get<number>("completeLines", 3);

      try {
        const completionText = await getCompletion(
          document.getText(),
          ctx.theoremName,
          numLines
        );
        if (!completionText || token.isCancellationRequested) {
          return { items: [] };
        }
        // 补全文本从光标位置开始插入
        const item = new vscode.InlineCompletionItem(
          completionText,
          new vscode.Range(position, position)
        );
        return { items: [item] };
      } catch (e: any) {
        console.log(`[LeanWeaver inline] ${e.message}`);
        return { items: [] };
      }
    },
  };

  context.subscriptions.push(
    vscode.languages.registerInlineCompletionItemProvider("lean", provider)
  );
}
