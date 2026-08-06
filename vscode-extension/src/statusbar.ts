import * as vscode from "vscode";
import type { EnvironmentStatus } from "./env";

/**
 * 状态栏：显示 LeanWeaver 环境状态，点击打开设置。
 */

let item: vscode.StatusBarItem | undefined;

export function updateStatusBar(status: EnvironmentStatus) {
  if (!item) {
    item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 20);
    item.command = "leanweaver.openSettings";
    item.tooltip = "LeanWeaver 环境状态，点击打开设置";
    item.show();
  }

  if (status.cli && status.lean) {
    item.text = "$(book) LeanWeaver";
    if (status.llm) {
      item.tooltip = "LeanWeaver 就绪：CLI ✓ Lean ✓ LLM ✓";
      item.backgroundColor = undefined;
    } else {
      item.tooltip = "LeanWeaver：CLI ✓ Lean ✓，LLM 未配置（翻译不可用，报错解释可用）";
      item.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
    }
  } else if (status.cli && !status.lean) {
    item.text = "$(warning) LeanWeaver: 缺 Lean";
    item.tooltip = "未检测到 lean 工具链。请安装 elan，或配置 leanweaver.leanPath";
    item.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
  } else {
    item.text = "$(error) LeanWeaver: 未安装";
    item.tooltip = "未检测到 leanweaver CLI。请 pip install leanweaver，或检查 leanweaverCli 配置";
    item.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
  }
}

export function disposeStatusBar() {
  if (item) item.dispose();
}
