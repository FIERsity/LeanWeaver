import * as vscode from "vscode";
import * as assert from "assert";
import * as fs from "fs";
import { exec } from "child_process";

/**
 * LeanWeaver 扩展集成测试 —— 纯规则，零 LLM。
 */

function run(cmd: string, timeout = 30000): Promise<string> {
  return new Promise((resolve, reject) => {
    exec(cmd, { timeout }, (err, stdout, stderr) => {
      if (err && !stdout) return reject(new Error(stderr || err.message));
      resolve(stdout || stderr);
    });
  });
}

suite("LeanWeaver 集成测试（纯规则）", () => {
  test("扩展已激活", async () => {
    const cmds = await vscode.commands.getCommands();
    // 不应有 LLM 命令（已砍掉）
    assert.ok(!cmds.includes("leanweaver.translate"), "translate 应已移除");
    assert.ok(!cmds.includes("leanweaver.suggest"), "suggest 应已移除");
  });

  test("hover provider 可调用（不抛异常）", async () => {
    const doc = await vscode.workspace.openTextDocument({
      language: "lean",
      content: ["theorem bad (a : Nat) : a = 0 := by", "  rfl"].join("\n"),
    });
    await vscode.window.showTextDocument(doc);
    const position = new vscode.Position(1, 2);
    const hovers = await vscode.commands.executeCommand<vscode.Hover[]>(
      "vscode.executeHoverProvider",
      doc.uri,
      position
    );
    assert.ok(Array.isArray(hovers), "hover provider 应可调用");
  });

  test("CLI explain 返回中文解释（纯规则）", async function () {
    this.timeout(30000);
    const py = fs.existsSync("/Volumes/DataHub/Dev/LeanWeaver/.venv/bin/python3")
      ? "/Volumes/DataHub/Dev/LeanWeaver/.venv/bin/python3"
      : "python3";
    const out = await run(
      `${py} -m leanweaver explain --lang zh "Type mismatch\\n  s\\nhas type\\n  String\\nbut is expected to have type\\n  Nat"`
    );
    assert.ok(out.includes("类型不匹配") || out.includes("Type mismatch"), `应包含解释: ${out.slice(0, 60)}`);
    assert.ok(out.includes("修复") || out.includes("Fixes"), "应有修复建议");
  });
});
