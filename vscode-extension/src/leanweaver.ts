import * as vscode from "vscode";
import { exec } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

/**
 * leanweaver CLI 调用封装。
 * 所有功能最终都通过 CLI 完成（保持单一实现源）。
 */

function getCli(): string {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  return cfg.get<string>("leanweaverCli", "python3 -m leanweaver");
}

function getLang(): string {
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  return cfg.get<string>("lang", "zh");
}

function runCli(args: string[], timeout = 120000): Promise<string> {
  const cli = getCli();
  const cmd = `${cli} ${args.join(" ")}`;
  return new Promise((resolve, reject) => {
    exec(cmd, { timeout }, (err, stdout, stderr) => {
      if (err) {
        if (stdout && stdout.trim()) {
          resolve(stdout); // 非零退出但有输出（如 check 有错误）也算结果
        } else {
          reject(new Error(stderr || err.message));
        }
        return;
      }
      resolve(stdout);
    });
  });
}

/** 把源码写进临时文件（CLI 接受文件路径）。 */
function writeTemp(source: string): string {
  const dir = path.join(os.tmpdir(), "leanweaver-vscode");
  fs.mkdirSync(dir, { recursive: true });
  const f = path.join(dir, `input-${Date.now()}-${Math.random().toString(36).slice(2, 8)}.lean`);
  fs.writeFileSync(f, source);
  return f;
}

function cleanup(file: string) {
  fs.unlink(file, () => {});
}

/** 解释一条报错（规则层为主，毫秒级）。返回 markdown 友好文本。 */
export async function explainError(message: string, code?: string): Promise<string> {
  // 直接传报错文本给 explain；--llm 可选由配置决定
  const cfg = vscode.workspace.getConfiguration("leanweaver");
  const useLlm = cfg.get<boolean>("llmFallback", false);
  const lang = getLang();
  const args = ["explain"];
  if (code) args.push(`--code`, JSON.stringify(code));
  if (useLlm) args.push("--llm");
  args.push(`--lang`, lang);
  // 通过 stdin 传报错文本：用临时文件方式更稳（避免 shell 转义）
  const f = writeTemp("");
  try {
    const out = await runCli([...args, JSON.stringify(message)]);
    return out;
  } finally {
    cleanup(f);
  }
}

/** 检查一个 .lean 文件的所有诊断（返回原始输出）。 */
export async function checkFile(source: string): Promise<string> {
  const f = writeTemp(source);
  try {
    return await runCli([`check "${f}"`, `--lang ${getLang()}`]);
  } finally {
    cleanup(f);
  }
}

/** 翻译一个 .lean 文件（或其中的某个定理）。 */
export async function translateFile(source: string, theorem?: string): Promise<string> {
  const f = writeTemp(source);
  try {
    const args = [`translate "${f}"`, `--lang ${getLang()}`];
    if (theorem) args.push(`--theorem "${theorem}"`);
    return await runCli(args);
  } finally {
    cleanup(f);
  }
}

/** 翻译一段选中的 Lean 源码（包成最小文件）。 */
export async function translateSelection(selection: string): Promise<string> {
  const f = writeTemp(selection);
  try {
    return await runCli([`translate "${f}"`, `--lang ${getLang()}`]);
  } finally {
    cleanup(f);
  }
}

/** 为当前文件的证明建议下一步（含验证层）。返回 CLI 原始输出。 */
export async function suggestNext(source: string, theorem?: string): Promise<string> {
  const f = writeTemp(source);
  try {
    const args = [`suggest "${f}"`, `--lang ${getLang()}`];
    if (theorem) args.push(`--theorem "${theorem}"`);
    return await runCli(args, 120000);
  } finally {
    cleanup(f);
  }
}
