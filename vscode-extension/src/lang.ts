import * as vscode from "vscode";

/**
 * 解释语言：
 * - 用户显式设置 `leanweaver.lang` 时，永远尊重用户设置；
 * - 未设置时，跟随 VS Code 界面语言（中文界面 → zh，其余 → en）。
 *
 * 这样中文用户装完即用中文，国际用户保持英文，互不打扰。
 */
export function getLang(): string {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const inspected = cfg.inspect<string>("lang");
  if (
    inspected &&
    (inspected.globalValue !== undefined || inspected.workspaceValue !== undefined)
  ) {
    return cfg.get<string>("lang", "en");
  }
  return vscode.env.language.toLowerCase().startsWith("zh") ? "zh" : "en";
}
