import * as vscode from "vscode";
import { detectEnvironment, openLeanExtension, hasOfficialLean, execDetail } from "./env";
import { registerHoverProvider } from "./hover";
import { updateStatusBar, disposeStatusBar } from "./statusbar";

/**
 * LeanWeaver VS Code 扩展 —— 纯规则，零 LLM。
 *
 * 依赖：官方 Lean 扩展 (leanprover.lean4) 提供红线/诊断，
 * 我们在此基础上加"报错悬停中文解释"。
 */

export function activate(context: vscode.ExtensionContext) {
  // 注册 hover（核心：报错悬停解释）
  registerHoverProvider(context);

  // 命令：安装官方 Lean 扩展
  const installLeanCmd = vscode.commands.registerCommand(
    "leanweaver.installLean",
    () => openLeanExtension()
  );
  context.subscriptions.push(installLeanCmd);

  // 诊断命令：显示环境检测详情 + 实际报错（排查用）
  const diagnoseCmd = vscode.commands.registerCommand("leanweaver.diagnose", async () => {
    const env = await detectEnvironment();
    const cfg = vscode.workspace.getConfiguration("leanweaver");
    const configured = cfg.get<string>("leanweaverCli", "");
    const fs = require("fs") as typeof import("fs");
    const venv = "/Volumes/DataHub/Dev/LeanWeaver/.venv/bin/python3";
    const cli = configured || (fs.existsSync(venv) ? `${venv} -m leanweaver` : "python3 -m leanweaver");
    // 实际执行并捕获 stderr（直接 execFile，不走 bash）
    const { execFile } = require("child_process") as typeof import("child_process");
    const runDirect = (py: string) =>
      new Promise<{ ok: boolean; out: string; err: string }>((res) => {
        execFile(py, ["-m", "leanweaver", "--help"], { timeout: 20000 }, (e, so, se) =>
          res({ ok: !e, out: (so || "").slice(0, 80).trim(), err: ((se || "") + (e ? " " + e.message : "")).slice(0, 300) })
        );
      });
    const d = await runDirect(venv);
    const msg =
      `直接 execFile(${venv} -m leanweaver --help)\n` +
      `结果: ${d.ok ? "✅ 成功" : "❌ 失败"}\n` +
      `stdout: ${d.out || "(空)"}\n` +
      `stderr: ${d.err || "(无)"}\n` +
      `---\n` +
      `detectEnvironment: cli=${env.cli} lean=${env.lean} official=${env.officialLean}\n` +
      `configured: ${configured || "(自动)"}`;
    vscode.window.showInformationMessage(msg, { modal: false });
  });
  context.subscriptions.push(diagnoseCmd);

  // 打开设置
  const settingsCmd = vscode.commands.registerCommand(
    "leanweaver.openSettings",
    () => {
      vscode.commands.executeCommand("workbench.action.openSettings", "@ext:fiersity.leanweaver");
    }
  );
  context.subscriptions.push(settingsCmd);

  // 环境检测 + 状态栏（启动延迟检测 + 失败重试，避免启动繁忙误报）
  const refresh = async () => {
    const env = await detectEnvironment();
    updateStatusBar(env);
    return env;
  };
  setTimeout(() => {
    refresh().then((env) => {
      // CLI 失败时延迟重试一次（可能是启动瞬间的环境问题）
      if (!env.cli) {
        setTimeout(() => refresh(), 5000);
      }
    });
  }, 2000);

  // 若官方扩展未装，首次提醒一次
  const alreadyWarned = context.globalState.get<boolean>("leanExtWarned", false);
  if (!hasOfficialLean() && !alreadyWarned) {
    vscode.window
      .showWarningMessage(
        "LeanWeaver 需要官方 Lean 扩展才能工作（它提供红线/报错诊断）。是否安装 leanprover.lean4？",
        "安装",
        "稍后"
      )
      .then((choice) => {
        if (choice === "安装") openLeanExtension();
        context.globalState.update("leanExtWarned", true);
      });
  }
}

export function deactivate() {
  disposeStatusBar();
}
