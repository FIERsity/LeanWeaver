import * as vscode from "vscode";
import { detectEnvironment, openLeanExtension, hasOfficialLean } from "./env";
import { registerHoverProvider } from "./hover";
import { updateStatusBar, disposeStatusBar } from "./statusbar";

/**
 * LeanWeaver VS Code 扩展 —— 纯规则，零 LLM。
 *
 * 依赖：官方 Lean 扩展 (leanprover.lean4) 提供红线/诊断，
 * 我们在此基础上加"报错悬停解释"。
 */

function getLang(): string {
  return vscode.workspace.getConfiguration("leanweaver").get<string>("lang", "en");
}

/** 打开安装引导（Webview 或消息）。 */
async function showSetup() {
  const env = await detectEnvironment();
  const lang = getLang();
  const isZh = lang === "zh";

  const missing: string[] = [];
  if (!env.officialLean) missing.push(isZh ? "官方 Lean 扩展 (leanprover.lean4)" : "Official Lean extension (leanprover.lean4)");
  if (!env.lean) missing.push(isZh ? "Lean 工具链 (elan)" : "Lean toolchain (elan)");
  if (!env.cli) missing.push(isZh ? "leanweaver CLI (pip install leanweaver)" : "leanweaver CLI (pip install leanweaver)");

  const title = isZh ? "LeanWeaver 安装引导" : "LeanWeaver Setup";
  const intro = isZh
    ? `检测到缺少：${missing.join("、") || "（无，一切就绪）"}`
    : `Missing: ${missing.join(", ") || "(all set)"}`;

  const items: vscode.QuickPickItem[] = [];
  if (!env.officialLean) {
    items.push({ label: isZh ? "安装官方 Lean 扩展" : "Install official Lean extension", detail: "leanprover.lean4", picked: true });
  }
  if (!env.lean) {
    items.push({
      label: isZh ? "安装 Lean 工具链 (elan)" : "Install Lean toolchain (elan)",
      detail: "curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh",
    });
  }
  if (!env.cli) {
    items.push({
      label: isZh ? "安装 leanweaver CLI" : "Install leanweaver CLI",
      detail: "pip install leanweaver",
    });
  }
  if (items.length === 0) {
    vscode.window.showInformationMessage(
      isZh ? "✓ LeanWeaver 环境就绪（纯规则、离线、免费）" : "✓ LeanWeaver is ready (rule-based, offline, free)"
    );
    return;
  }

  const picked = await vscode.window.showQuickPick(items, {
    title,
    placeHolder: intro,
    canPickMany: true,
  });
  if (!picked) return;

  // 执行选中的安装动作
  for (const item of items) {
    if (!picked.includes(item)) continue;
    if (item.label.includes("Lean 扩展") || item.label.includes("Lean extension")) {
      openLeanExtension();
    } else if (item.label.includes("elan") || item.label.includes("工具链")) {
      vscode.env.openExternal(vscode.Uri.parse("https://leanprover-community.github.io/get_started.html"));
    } else if (item.label.includes("CLI")) {
      vscode.window.showInformationMessage(
        isZh
          ? "请在终端执行: pip install leanweaver （或配置 leanweaver.leanweaverCli 指向你的安装）"
          : "Run in terminal: pip install leanweaver (or set leanweaver.leanweaverCli to your install)"
      );
    }
  }
  // 稍后重新检测
  setTimeout(() => detectEnvironment().then(updateStatusBar), 8000);
}

export function activate(context: vscode.ExtensionContext) {
  // 核心：报错悬停解释
  registerHoverProvider(context);

  // 安装引导命令（状态栏点击也走这里）
  const setupCmd = vscode.commands.registerCommand("leanweaver.setup", () => showSetup());
  context.subscriptions.push(setupCmd);

  // 打开设置
  const settingsCmd = vscode.commands.registerCommand("leanweaver.openSettings", () => {
    vscode.commands.executeCommand("workbench.action.openSettings", "@ext:fiersity.leanweaver");
  });
  context.subscriptions.push(settingsCmd);

  // 环境检测 + 状态栏（启动延迟检测 + 失败重试）
  const refresh = async () => {
    const env = await detectEnvironment();
    updateStatusBar(env);
    return env;
  };
  setTimeout(() => {
    refresh().then((env) => {
      if (!env.cli || !env.lean || !env.officialLean) {
        setTimeout(() => refresh(), 5000);
      }
    });
  }, 2000);
}

export function deactivate() {
  disposeStatusBar();
}
