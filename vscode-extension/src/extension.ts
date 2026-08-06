import * as vscode from "vscode";
import { detectEnvironment, openLeanExtension, hasOfficialLean } from "./env";
import { registerHoverProvider } from "./hover";
import { updateStatusBar, disposeStatusBar } from "./statusbar";

/**
 * LeanWeaver VS Code 扩展 —— 纯规则、自包含、零 CLI 依赖。
 *
 * 内置规则引擎（TypeScript），装扩展即用，无需 Python。
 * 依赖：官方 Lean 扩展 (leanprover.lean4) 提供红线/诊断。
 */

function getLang(): string {
  return vscode.workspace.getConfiguration("leanweaver").get<string>("lang", "en");
}

/** 安装引导：检测缺失项，QuickPick 分步引导。 */
async function showSetup() {
  const env = await detectEnvironment();
  const isZh = getLang() === "zh";

  const missing: string[] = [];
  if (!env.officialLean) missing.push(isZh ? "官方 Lean 扩展" : "Official Lean extension");
  if (!env.lean) missing.push(isZh ? "Lean 工具链 (elan)" : "Lean toolchain (elan)");

  const items: vscode.QuickPickItem[] = [];
  if (!env.officialLean) {
    items.push({
      label: isZh ? "安装官方 Lean 扩展（提供红线/诊断）" : "Install official Lean extension (provides diagnostics)",
      detail: "leanprover.lean4",
      picked: true,
    });
  }
  if (!env.lean) {
    items.push({
      label: isZh ? "安装 Lean 工具链 (elan)" : "Install Lean toolchain (elan)",
      detail: "https://leanprover-community.github.io/get_started.html",
    });
  }
  if (items.length === 0) {
    vscode.window.showInformationMessage(
      isZh ? "✓ LeanWeaver 就绪（纯规则、离线、零依赖）" : "✓ LeanWeaver is ready (rule-based, offline, zero-dependency)"
    );
    return;
  }

  const picked = await vscode.window.showQuickPick(items, {
    title: isZh ? "LeanWeaver 安装引导" : "LeanWeaver Setup",
    placeHolder: isZh ? `检测到缺少：${missing.join("、")}` : `Missing: ${missing.join(", ")}`,
    canPickMany: true,
  });
  if (!picked) return;

  for (const item of items) {
    if (!picked.includes(item)) continue;
    if (item.label.includes("Lean 扩展") || item.label.includes("Lean extension")) {
      openLeanExtension();
    } else {
      vscode.env.openExternal(
        vscode.Uri.parse("https://leanprover-community.github.io/get_started.html")
      );
    }
  }
  setTimeout(() => detectEnvironment().then(updateStatusBar), 8000);
}

export function activate(context: vscode.ExtensionContext) {
  // 核心：报错悬停解释（内置规则引擎）
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
      if (!env.lean || !env.officialLean) {
        setTimeout(() => refresh(), 5000);
      }
    });
  }, 2000);
}

export function deactivate() {
  disposeStatusBar();
}
