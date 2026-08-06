import * as vscode from "vscode";
import { execFile } from "child_process";
import * as fs from "fs";
import * as path from "path";

/** 环境检测（纯规则，零 LLM）。 */

export interface EnvironmentStatus {
  cli: boolean;              // leanweaver CLI 是否可用
  lean: boolean;             // lean 工具链是否可用
  officialLean: boolean;     // 官方 Lean 扩展 (leanprover.lean4) 是否已安装
}

function execOk(cmd: string, timeout = 20000): Promise<boolean> {
  return new Promise((resolve) => {
    execFile("/bin/bash", ["-c", cmd], { timeout }, (err, stdout) => {
      resolve(!err && !!stdout);
    });
  });
}

/** 检测官方 Lean 扩展是否安装（它提供红线/诊断，是我们的触发源）。 */
export function hasOfficialLean(): boolean {
  return !!vscode.extensions.getExtension("leanprover.lean4");
}

/** 直接检测 python3 -m leanweaver（不走 bash，避免 Electron 环境差异）。 */
function checkPythonCli(python: string): Promise<boolean> {
  return new Promise((resolve) => {
    execFile(python, ["-m", "leanweaver", "--help"], { timeout: 20000 }, (err, stdout) => {
      resolve(!err && !!stdout);
    });
  });
}

export async function detectEnvironment(): Promise<EnvironmentStatus> {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const configured = cfg.get<string>("leanweaverCli", "");
  let cliOk = false;
  if (configured) {
    // 用户配置的完整命令（用户自己负责正确）
    cliOk = await execOk(configured);
  } else {
    // 自动检测：依次尝试 python3 / python / leanweaver（不依赖任何硬编码路径）
    cliOk = await checkPythonCli("python3");
    if (!cliOk) cliOk = await checkPythonCli("python");
    if (!cliOk) cliOk = await execOk("leanweaver --help");
  }
  // lean 工具链（~/.elan 是标准安装位置）
  const homeLean = path.join(process.env.HOME || "", ".elan", "bin", "lean");
  const leanOk = fs.existsSync(homeLean) || (await execOk("lean --version"));
  return { cli: cliOk, lean: leanOk, officialLean: hasOfficialLean() };
}

/** 打开官方 Lean 扩展的市场页（引导用户安装）。 */
export function openLeanExtension() {
  vscode.commands.executeCommand(
    "workbench.extensions.installExtension",
    "leanprover.lean4"
  );
}
