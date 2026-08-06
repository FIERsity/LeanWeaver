import * as vscode from "vscode";
import type { EnvironmentStatus } from "./env";

let item: vscode.StatusBarItem | undefined;

export function updateStatusBar(status: EnvironmentStatus) {
  if (!item) {
    item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 20);
    item.command = "leanweaver.setup";
    item.show();
  }

  const isZh = vscode.workspace.getConfiguration("leanweaver").get<string>("lang", "en") === "zh";

  if (status.cli && status.lean && status.officialLean) {
    item.text = "$(check) LeanWeaver";
    item.tooltip = isZh ? "就绪：纯规则报错解释（离线、免费）" : "Ready: rule-based error explainer (offline, free)";
    item.backgroundColor = undefined;
  } else {
    const missing = [
      !status.officialLean ? (isZh ? "Lean扩展" : "Lean ext") : "",
      !status.lean ? "Lean" : "",
      !status.cli ? (isZh ? "CLI" : "CLI") : "",
    ].filter(Boolean);
    item.text = `$(warning) LeanWeaver: ${missing.join(" / ")}`;
    item.tooltip = isZh
      ? `缺少 ${missing.join("、")}，点击查看安装引导`
      : `Missing: ${missing.join(", ")}. Click to set up.`;
    item.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
  }
}

export function disposeStatusBar() {
  if (item) item.dispose();
}
