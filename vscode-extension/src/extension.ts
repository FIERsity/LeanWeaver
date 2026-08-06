import * as vscode from "vscode";
import { detectEnvironment, type EnvironmentStatus } from "./env";
import { registerHoverProvider } from "./hover";
import { registerCodeLens } from "./codelens";
import { showOutput, closePanel } from "./webview";
import { updateStatusBar, disposeStatusBar } from "./statusbar";
import { translateFile, translateSelection, checkFile } from "./leanweaver";

/**
 * LeanWeaver VS Code 扩展主入口。
 *
 * 能力：
 *  - 报错悬停中文解释（hover，规则层毫秒级）
 *  - 定理行 CodeLens「翻译证明」
 *  - 命令：翻译当前文件/选中、解释报错
 *  - 状态栏环境检测 + 首次激活引导
 */

let envStatus: EnvironmentStatus = { cli: false, lean: false, llm: false };

async function refreshEnvironment() {
  envStatus = await detectEnvironment();
  updateStatusBar(envStatus);
  return envStatus;
}

/** 首次激活引导：缺依赖时提示。 */
async function maybeShowSetup() {
  const status = await refreshEnvironment();
  if (status.cli && status.lean) return; // 环境 OK

  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const alreadyDismissed = cfg.get<boolean>("setupPromptDismissed", false);
  if (alreadyDismissed) return;

  const missing: string[] = [];
  if (!status.lean) missing.push("Lean 工具链 (elan)");
  if (!status.cli) missing.push("leanweaver CLI");

  const action = await vscode.window.showWarningMessage(
    `LeanWeaver：检测到缺少 ${missing.join("、")}。报错解释需要它们。是否查看安装指引？`,
    "查看指引",
    "暂时不用"
  );
  if (action === "查看指引") {
    vscode.commands.executeCommand("leanweaver.openSetup");
  } else if (action === "暂时不用") {
    await cfg.update("setupPromptDismissed", true, vscode.ConfigurationTarget.Global);
  }
}

function currentLeanSource(): { editor: vscode.TextEditor; text: string } | undefined {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("LeanWeaver：请先打开一个 .lean 文件");
    return undefined;
  }
  return { editor, text: editor.document.getText() };
}

async function runWithProgress(title: string, fn: () => Promise<void>) {
  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title },
    async () => {
      await fn();
    }
  );
}

// 诊断输出通道（可在 VS Code「输出」面板查看 LeanWeaver 日志）
export const output = vscode.window.createOutputChannel("LeanWeaver");

function log(msg: string) {
  output.appendLine(`[${new Date().toLocaleTimeString()}] ${msg}`);
}

export function activate(context: vscode.ExtensionContext) {
  log("LeanWeaver 扩展已激活");
  log(`CLI 配置: ${vscode.workspace.getConfiguration("leanweaver").get("leanweaverCli", "python3 -m leanweaver")}`);

  // ---------- 命令：翻译当前文件 ----------
  const translateCmd = vscode.commands.registerCommand("leanweaver.translate", async () => {
    const src = currentLeanSource();
    if (!src) return;
    await runWithProgress("LeanWeaver 正在翻译证明…", async () => {
      try {
        const out = await translateFile(src.text);
        showOutput("LeanWeaver · 证明翻译", out);
      } catch (e: any) {
        vscode.window.showErrorMessage(`LeanWeaver 翻译失败：${e.message}`);
      }
    });
  });

  // ---------- 命令：翻译选中的证明片段 ----------
  const translateSelCmd = vscode.commands.registerCommand("leanweaver.translateSelection", async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const sel = editor.selection;
    if (sel.isEmpty) {
      vscode.window.showWarningMessage("LeanWeaver：请先选中要翻译的 Lean 代码");
      return;
    }
    const text = editor.document.getText(sel);
    await runWithProgress("LeanWeaver 正在翻译选中内容…", async () => {
      try {
        const out = await translateSelection(text);
        showOutput("LeanWeaver · 选中翻译", out);
      } catch (e: any) {
        vscode.window.showErrorMessage(`LeanWeaver 翻译失败：${e.message}`);
      }
    });
  });

  // ---------- 命令：翻译某个定理（CodeLens 调用） ----------
  const translateAtCmd = vscode.commands.registerCommand("leanweaver.translateAt", async (arg: { text: string }) => {
    const src = currentLeanSource();
    if (!src || !arg) return;
    await runWithProgress("LeanWeaver 正在翻译该定理…", async () => {
      try {
        // 提取定理名（简化：从 arg.text 正则）
        const m = /(?:theorem|lemma|example|def)\s+([A-Za-z_][A-Za-z0-9_']*)?/.exec(arg.text);
        const name = m && m[1];
        const out = await translateFile(src.text, name || undefined);
        showOutput(`LeanWeaver · ${name || "定理"}翻译`, out);
      } catch (e: any) {
        vscode.window.showErrorMessage(`LeanWeaver 翻译失败：${e.message}`);
      }
    });
  });

  // ---------- 命令：解释当前文件报错 ----------
  const checkCmd = vscode.commands.registerCommand("leanweaver.check", async () => {
    const src = currentLeanSource();
    if (!src) return;
    await runWithProgress("LeanWeaver 正在分析报错…", async () => {
      try {
        const out = await checkFile(src.text);
        showOutput("LeanWeaver · 报错解释", out);
      } catch (e: any) {
        vscode.window.showErrorMessage(`LeanWeaver 检查失败：${e.message}`);
      }
    });
  });

  // ---------- 命令：打开输出面板 ----------
  const openCmd = vscode.commands.registerCommand("leanweaver.openPanel", () => {
    showOutput("LeanWeaver", "打开一个 Lean 文件，然后：\n\n- 悬停报错 → 中文解释\n- 定理行点击「翻译证明」\n- 右键 → 翻译 / 检查");
  });

  // ---------- 命令：打开设置 ----------
  const settingsCmd = vscode.commands.registerCommand("leanweaver.openSettings", () => {
    vscode.commands.executeCommand("workbench.action.openSettings", "@ext:fiersity.leanweaver");
  });

  // ---------- 命令：安装指引 ----------
  const setupCmd = vscode.commands.registerCommand("leanweaver.openSetup", () => {
    const md = new vscode.MarkdownString(`# LeanWeaver 安装指引

LeanWeaver 需要以下组件：

### 1. Lean 工具链（报错解释、证明分析需要）
\`\`\`bash
curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
\`\`\`

### 2. leanweaver CLI
\`\`\`bash
pip install leanweaver
# 或从源码:
# pip install -e /path/to/LeanWeaver
\`\`\`

### 3. LLM API（翻译功能需要；报错解释不需要）
在设置里配置 \`leanweaver\`，或设置环境变量：
\`\`\`bash
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.deepseek.com/v1   # 以 DeepSeek 为例
export LEANWEAVER_MODEL=deepseek-chat
\`\`\`

> 提示：只想要报错解释（免费、离线、秒出）的话，装好 1 和 2 即可。`);
    vscode.window.showInformationMessage("LeanWeaver 安装指引（详见输出面板）", { modal: false });
    showOutput("LeanWeaver · 安装指引", md.value);
  });

  // ---------- 注册 hover / codelens / 状态栏 ----------
  registerHoverProvider(context);
  registerCodeLens(context);
  context.subscriptions.push(translateCmd, translateSelCmd, translateAtCmd, checkCmd, openCmd, settingsCmd, setupCmd);

  // 启动时检测环境 + 首次引导
  refreshEnvironment().then(() => {
    log(`环境检测完成: CLI=${envStatus.cli} Lean=${envStatus.lean} LLM=${envStatus.llm}`);
  });
  maybeShowSetup();
  log("LeanWeaver 扩展初始化完成（hover/CodeLens/命令已注册）");
}

export function deactivate() {
  closePanel();
  disposeStatusBar();
}
