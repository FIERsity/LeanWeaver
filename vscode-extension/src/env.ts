import * as vscode from "vscode";
import { execFile } from "child_process";
import * as fs from "fs";
import * as path from "path";

/** 环境检测（纯规则，零 LLM）。 */

export interface EnvironmentStatus {
  cli: boolean;              // leanweaver CLI 是否可用
  lean: boolean;             // lean 工具链是否可用
  officialLean: boolean;     // 官方 Lean 扩展 (vscode-lean4) 是否已安装
}

function execCheck(cmd: string): Promise<boolean> {
  return new Promise((resolve) => {
    // 超时给足 20s：启动时系统可能繁忙，python 冷启动 + import 可能慢
    execFile("/bin/bash", ["-c", cmd], { timeout: 20000 }, (err, stdout, stderr) => {
      console.log(`[execCheck] ${cmd} => err=${err?.message?.slice(0,80)} stdout=${(stdout||"").slice(0,40).trim()} stderr=${(stderr||"").slice(0,80).trim()}`);
      resolve(!err && !!stdout);
    });
  });
}

/** 执行命令并返回 {ok, stdout, stderr}（诊断用）。 */
export function execDetail(cmd: string): Promise<{ ok: boolean; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    execFile(
      "/bin/bash",
      ["-c", cmd],
      { timeout: 8000 },
      (err, stdout, stderr) => {
        resolve({ ok: !err, stdout: stdout || "", stderr: (stderr || err?.message || "") });
      }
    );
  });
}

/** 检测官方 Lean 扩展是否安装（它提供红线/诊断，是我们的触发源）。 */
export function hasOfficialLean(): boolean {
  return !!vscode.extensions.getExtension("leanprover.lean4");
}

/** 直接执行 venv python -m leanweaver（不走 bash，避免 Electron 环境差异）。 */
function checkPythonCli(python: string): Promise<boolean> {
  return new Promise((resolve) => {
    execFile(python, ["-m", "leanweaver", "--help"], { timeout: 20000 }, (err, stdout, stderr) => {
      console.log(`[checkPythonCli] ${python} => err=${err?.message?.slice(0,80)} out=${(stdout||"").slice(0,30).trim()}`);
      resolve(!err && !!stdout);
    });
  });
}

export async function detectEnvironment(): Promise<EnvironmentStatus> {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const configured = cfg.get<string>("leanweaverCli", "");
  const venv = "/Volumes/DataHub/Dev/LeanWeaver/.venv/bin/python3";
  let cliOk = false;
  // 1. 用户配置的完整命令（走 bash，用户自己负责）
  if (configured) {
    cliOk = await execCheck(configured);
  } else {
    // 2. 自动：直接用 execFile 跑 venv python（不走 bash，最稳）
    if (fs.existsSync(venv)) {
      cliOk = await checkPythonCli(venv);
      if (!cliOk) cliOk = await checkPythonCli("python3");
    } else {
      cliOk = await checkPythonCli("python3");
    }
  }
  const homeLean = path.join(process.env.HOME || "", ".elan", "bin", "lean");
  const leanOk = fs.existsSync(homeLean) || (await execCheck("lean --version"));
  console.log(`[LeanWeaver env] cliOk=${cliOk} leanOk=${leanOk} officialLean=${hasOfficialLean()}`);
  return { cli: cliOk, lean: leanOk, officialLean: hasOfficialLean() };
}

/** 打开官方 Lean 扩展的市场页（引导用户安装）。 */
export function openLeanExtension() {
  vscode.commands.executeCommand(
    "workbench.extensions.installExtension",
    "leanprover.lean4"
  );
}
