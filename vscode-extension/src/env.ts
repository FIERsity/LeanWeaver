import * as vscode from "vscode";
import { execFile } from "child_process";
import * as fs from "fs";
import * as path from "path";

/**
 * 环境检测 —— 扩展自包含（内置规则引擎），不再依赖 Python CLI。
 * 只需要：
 *  - 官方 Lean 扩展（提供红线/诊断，我们的触发源）
 *  - lean 工具链（用户写 Lean 本来就需要）
 *
 * 平台兼容：Windows / macOS / Linux 全部走同一套检测逻辑，
 * 不依赖 bash、不硬编码 shell 路径。
 */

export interface EnvironmentStatus {
  lean: boolean;          // lean 工具链是否可用
  officialLean: boolean;  // 官方 Lean 扩展 (leanprover.lean4) 是否已安装
}

/** elan 的标准安装位置（跨平台：Windows 为 ~/.elan/bin/lean.exe）。 */
function leanPathCandidates(): string[] {
  const home = process.env.HOME || process.env.USERPROFILE || "";
  const candidates: string[] = [];
  if (process.env.ELAN_HOME) candidates.push(path.join(process.env.ELAN_HOME, "bin", "lean"));
  if (home) candidates.push(path.join(home, ".elan", "bin", "lean"));
  return candidates;
}

/** 通过 PATH 直接执行 lean --version（不经过 shell，Windows 也能解析 lean.exe）。 */
function leanOnPath(timeout = 15000): Promise<boolean> {
  return new Promise((resolve) => {
    execFile("lean", ["--version"], { timeout, windowsHide: true }, (err, stdout) => {
      resolve(!err && stdout.length > 0);
    });
  });
}

export function hasOfficialLean(): boolean {
  return !!vscode.extensions.getExtension("leanprover.lean4");
}

export async function detectEnvironment(): Promise<EnvironmentStatus> {
  const leanOk =
    leanPathCandidates().some((p) => fs.existsSync(p)) ||
    (await leanOnPath());
  return { lean: leanOk, officialLean: hasOfficialLean() };
}

/** 打开官方 Lean 扩展的市场页（引导用户安装）。 */
export function openLeanExtension() {
  vscode.commands.executeCommand(
    "workbench.extensions.installExtension",
    "leanprover.lean4"
  );
}
