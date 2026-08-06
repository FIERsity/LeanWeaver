import * as vscode from "vscode";
import { exec } from "child_process";
import * as fs from "fs";
import * as path from "path";

/** 环境检测：leanweaver CLI 是否可用（纯规则，不需要 LLM）。 */

export interface EnvironmentStatus {
  cli: boolean;
  lean: boolean;
}

function execCheck(cmd: string): Promise<boolean> {
  return new Promise((resolve) => {
    exec(cmd, { timeout: 8000 }, (err) => resolve(!err));
  });
}

export async function detectEnvironment(): Promise<EnvironmentStatus> {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const cli = cfg.get<string>("leanweaverCli", "python3 -m leanweaver");
  let cliOk = false;
  for (const c of [cli, "leanweaver --help"]) {
    if (await execCheck(c)) {
      cliOk = true;
      break;
    }
  }
  // lean 工具链（报错解释本身不需要 lean，但提示环境完整性）
  const homeLean = path.join(process.env.HOME || "", ".elan", "bin", "lean");
  const leanOk = fs.existsSync(homeLean) || (await execCheck("lean --version"));
  return { cli: cliOk, lean: leanOk };
}
