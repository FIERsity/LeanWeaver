import * as vscode from "vscode";
import { exec } from "child_process";

/**
 * leanweaver CLI 调用封装 —— 纯规则，零 LLM。
 * 只保留一个功能：报错解释（explain）。
 */

function getCli(): string {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  return cfg.get<string>("leanweaverCli", "python3 -m leanweaver");
}

function getLang(): string {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  return cfg.get<string>("lang", "zh");
}

function runCli(args: string[], timeout = 15000): Promise<string> {
  const cli = getCli();
  const cmd = `${cli} ${args.join(" ")}`;
  return new Promise((resolve, reject) => {
    exec(cmd, { timeout }, (err, stdout, stderr) => {
      if (err) {
        if (stdout && stdout.trim()) {
          resolve(stdout);
        } else {
          reject(new Error(stderr || err.message));
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
  if (code) args.push(`--code`, JSON.stringify(code));
  args.push(`--lang`, lang);
  // 直接传报错文本（避免 shell 转义问题）
  return runCli([...args, JSON.stringify(message)]);
}
