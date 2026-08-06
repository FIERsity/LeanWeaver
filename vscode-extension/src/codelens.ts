import * as vscode from "vscode";
import { translateFile, translateSelection } from "./leanweaver";

/**
 * CodeLens：在定理声明行显示「翻译此证明」按钮。
 *
 * 识别 theorem / lemma / example / def 行，放一个按钮，
 * 点击后翻译该定理（优先用 leanweaver translate 的 --theorem 精确翻译）。
 */

// 定理声明行的正则（Lean 4）
const DECL_RE = /^\s*(theorem|lemma|example|def)\s+([A-Za-z_][A-Za-z0-9_']*)?/;

/** 从选中范围提取要翻译的文本（若无选中，用整行）。 */
function selectedText(editor: vscode.TextEditor): string | undefined {
  const sel = editor.selection;
  if (!sel.isEmpty) {
    return editor.document.getText(sel);
  }
  return undefined;
}

export function registerCodeLens(context: vscode.ExtensionContext) {
  const lensProvider: vscode.CodeLensProvider = {
    provideCodeLenses(document): vscode.CodeLens[] {
      const lenses: vscode.CodeLens[] = [];
      const text = document.getText();
      const lines = text.split("\n");

      // 找到所有定理声明的行号
      for (let i = 0; i < lines.length; i++) {
        const m = DECL_RE.exec(lines[i]);
        if (!m) continue;
        console.log(`[LeanWeaver CodeLens] 行 ${i + 1}: 找到 ${m[1]} ${m[2] || ""}`.trim());
        const name = m[2] || m[1];
        const line = document.lineAt(i);
        const range = line.range;

        // 翻译此定理
        lenses.push(
          new vscode.CodeLens(range, {
            title: "🔍 翻译证明",
            command: "leanweaver.translateAt",
            arguments: [{ line: i, name, text: lines[i] }],
          })
        );

        // 只对前 20 行加按钮（避免文件过长时全是按钮）
        if (lenses.length > 60) break;
      }
      return lenses;
    },
    resolveCodeLens(lens) {
      return lens;
    },
  };

  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider("lean", lensProvider)
  );
}
