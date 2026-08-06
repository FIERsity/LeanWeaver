import * as vscode from "vscode";
import { exec } from "child_process";
import * as fs from "fs";
import * as path from "path";

/**
 * 环境检测：Lean / leanweaver CLI / LLM 配置。
 * 首次激活时运行，结果反映在状态栏 + 引导提示。
 */

export interface EnvironmentStatus {
  /** leanweaver CLI 是否可用 */
  cli: boolean;
  /** lean 工具链是否可用 */
  lean: boolean;
  /** LLM 是否配置（翻译需要；报错解释规则层不需要） */
  llm: boolean;
  cliError?: string;
}

function execCheck(cmd: string): Promise<boolean> {
  return new Promise((resolve) => {
    exec(cmd, { timeout: 8000 }, (err) => {
      resolve(!err);
    });
  });
}

/** 检测 leanweaver CLI（支持用户配置的 cli 命令） */
export async function checkCli(): Promise<{ ok: boolean; error?: string }> {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const cli = cfg.get<string>("leanweaverCli", "python3 -m leanweaver");

  // 候选命令：用户配置的 + 常见 fallback
  const candidates = [cli];
  if (cli === "python3 -m leanweaver") {
    candidates.push("leanweaver --help");
    candidates.push("python -m leanweaver --help");
  }

  for (const c of candidates) {
    try {
      const ok = await execCheck(c);
      if (ok) return { ok: true };
    } catch (e: any) {
      // 继续尝试下一个
    }
  }
  return { ok: false, error: "未找到 leanweaver CLI" };
}

/** 检测 lean 工具链 */
export async function checkLean(): Promise<boolean> {
  // lean 可能在 ~/.elan/bin 下（不在 PATH）
  const homeLean = path.join(process.env.HOME || "", ".elan", "bin", "lean");
  if (fs.existsSync(homeLean)) return true;
  return execCheck("lean --version");
}

/** 检测 LLM 配置（从进程环境变量，无法直接读用户 .env，但 leanweaver CLI 自己会读） */
export function checkLlmEnv(): boolean {
  const env = process.env;
  return !!(
    env.OPENAI_API_KEY ||
    env.LEANWEAVER_LLM_PROVIDER?.toLowerCase() === "ollama"
  );
}

/** 综合检测 */
export async function detectEnvironment(): Promise<EnvironmentStatus> {
  const [cli, lean, llm] = await Promise.all([checkCli(), checkLean(), Promise.resolve(checkLlmEnv())]);
  return { cli: cli.ok, lean, llm, cliError: cli.error };
}
