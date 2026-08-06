import * as vscode from "vscode";
import { execFile } from "child_process";
import * as fs from "fs";
import * as path from "path";

/**
 * 环境检测 —— 扩展现在自包含（内置规则引擎），不再依赖 Python CLI。
 * 只需要：
 *  - 官方 Lean 扩展（提供红线/诊断，我们的触发源）
 *  - lean 工具链（用户写 Lean 本来就需要）
 */

export interface EnvironmentStatus {
  lean: boolean;          // lean 工具链是否可用
  officialLean: boolean;  // 官方 Lean 扩展 (leanprover.lean4) 是否已安装
}

function execOk(cmd: string, timeout = 15000): Promise<boolean> {
  return new Promise((resolve) => {
    execFile("/bin/bash", ["-c", cmd], { timeout }, (err, stdout) => {
      resolve(!err && !!stdout);
    });
  });
}

export function hasOfficialLean(): boolean {
  return !!vscode.extensions.getExtension("leanprover.lean4");
}

export async function detectEnvironment(): Promise<EnvironmentStatus> {
  // lean 工具链（~/.elan 是标准安装位置）
  const homeLean = path.join(process.env.HOME || "", ".elan", "bin", "lean");
  const leanOk = fs.existsSync(homeLean) || (await execOk("lean --version"));
  return { lean: leanOk, officialLean: hasOfficialLean() };
}

/** 打开官方 Lean 扩展的市场页（引导用户安装）。 */
export function openLeanExtension() {
  vscode.commands.executeCommand(
    "workbench.extensions.installExtension",
    "leanprover.lean4"
  );
}
