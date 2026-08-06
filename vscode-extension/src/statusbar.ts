import * as vscode from "vscode";
import type { EnvironmentStatus } from "./env";

let item: vscode.StatusBarItem | undefined;

export function updateStatusBar(status: EnvironmentStatus) {
  if (!item) {
    item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 20);
    item.command = "leanweaver.openSettings";
    item.show();
  }
  if (status.cli) {
    item.text = "$(check) LeanWeaver";
    item.tooltip = "LeanWeaver 就绪：纯规则报错解释（离线、免费）";
    item.backgroundColor = undefined;
  } else {
    item.text = "$(warning) LeanWeaver: 未安装";
    item.tooltip = "未检测到 leanweaver CLI。请 pip install leanweaver";
    item.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
  }
}

export function disposeStatusBar() {
  if (item) item.dispose();
}
