import * as vscode from "vscode";
import { detectEnvironment } from "./env";
import { registerHoverProvider } from "./hover";
import { updateStatusBar, disposeStatusBar } from "./statusbar";

/**
 * LeanWeaver VS Code 扩展 —— 纯规则，零 LLM。
 *
 * 唯一功能：报错悬停中文解释（规则层，毫秒级，离线）。
 */

export function activate(context: vscode.ExtensionContext) {
  // 注册 hover（核心功能：报错悬停解释）
  registerHoverProvider(context);

  // 环境检测 + 状态栏（提示 CLI 是否可用）
  detectEnvironment().then((env) => {
    updateStatusBar(env);
  });

  // 打开设置（状态栏点击）
  const settingsCmd = vscode.commands.registerCommand(
    "leanweaver.openSettings",
    () => {
      vscode.commands.executeCommand("workbench.action.openSettings", "@ext:fiersity.leanweaver");
    }
  );
  context.subscriptions.push(settingsCmd);
}

export function deactivate() {
  disposeStatusBar();
}
