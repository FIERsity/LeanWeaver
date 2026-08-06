import * as vscode from "vscode";
import type { EnvironmentStatus } from "./env";

let item: vscode.StatusBarItem | undefined;

export function updateStatusBar(status: EnvironmentStatus) {
  if (!item) {
    item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 20);
    item.command = "leanweaver.openSettings";
    item.show();
  }

  if (!status.officialLean) {
    // 官方 Lean 扩展未装 → 无法产生红线，提示安装
    item.text = "$(warning) LeanWeaver: 需要官方 Lean 扩展";
    item.tooltip = "未安装 leanprover.lean4。没有它就不会有红线/诊断，LeanWeaver 无法工作。点击安装";
    item.command = "leanweaver.installLean";
    item.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
    return;
  }
  if (status.cli) {
    item.text = "$(check) LeanWeaver";
    item.tooltip = "LeanWeaver 就绪：纯规则报错解释（离线、免费）";
    item.command = "leanweaver.openSettings";
    item.backgroundColor = undefined;
  } else {
    item.text = "$(error) LeanWeaver: 未安装 CLI";
    item.tooltip = "未检测到 leanweaver CLI。请 pip install leanweaver";
    item.command = "leanweaver.openSettings";
    item.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
  }
}

export function disposeStatusBar() {
  if (item) item.dispose();
}
