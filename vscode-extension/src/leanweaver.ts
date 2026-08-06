import * as vscode from "vscode";
import { execFile } from "child_process";

/**
 * leanweaver CLI 调用封装 —— 纯规则，零 LLM。
 * 只保留一个功能：报错解释（explain）。
 * 用 execFile 传参数数组，避免 shell 转义问题。
 */

function getCliParts(): string[] {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const configured = cfg.get<string>("leanweaverCli", "");
  const fs = require("fs") as typeof import("fs");
  const venv = "/Volumes/DataHub/Dev/LeanWeaver/.venv/bin/python3";
  if (configured) return configured.split(/\s+/).filter(Boolean);
  if (fs.existsSync(venv)) return [venv, "-m", "leanweaver"];
  return ["python3", "-m", "leanweaver"];
}

function getLang(): string {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  return cfg.get<string>("lang", "zh");
}

function runCli(args: string[], timeout = 15000): Promise<string> {
  const parts = getCliParts();
  const [cmd, ...cmdArgs] = parts;
  const allArgs = [...cmdArgs, ...args];
  return new Promise((resolve, reject) => {
    execFile(cmd, allArgs, { timeout }, (err, stdout, stderr) => {
      if (err) {
        if (stdout && stdout.trim()) {
          resolve(stdout);
        } else {
          reject(new Error((stderr || err.message).slice(0, 200)));
        }
        return;
      }
      resolve(stdout);
    });
  });
}

/** 解释一条 Lean 报错（纯规则，毫秒级）。 */
export async function explainError(message: string, code?: string): Promise<string> {
  const lang = getLang();
  const args = ["explain"];
  if (code) args.push(`--code`, code);
  args.push(`--lang`, lang);
  args.push(message);
  return runCli(args);
}
