import * as vscode from "vscode";
import * as assert from "assert";
import * as fs from "fs";
import { exec } from "child_process";

/**
 * LeanWeaver 扩展集成测试。
 *
 * 验证：
 * 1. 扩展激活（命令已注册）
 * 2. CodeLens 在定理行生成「翻译证明」按钮
 * 3. hover provider 可调用（不抛异常）
 * 4. CLI explain 命令返回中文解释
 */

function run(cmd: string, timeout = 120000): Promise<string> {
  return new Promise((resolve, reject) => {
    exec(cmd, { timeout }, (err, stdout, stderr) => {
      if (err && !stdout) return reject(new Error(stderr || err.message));
      resolve(stdout || stderr);
    });
  });
}

suite("LeanWeaver 集成测试", () => {
  test("扩展已激活，命令已注册", async () => {
    const cmds = await vscode.commands.getCommands();
    assert.ok(cmds.includes("leanweaver.translate"), "translate 命令应存在");
    assert.ok(cmds.includes("leanweaver.check"), "check 命令应存在");
    assert.ok(
      cmds.includes("leanweaver.translateSelection"),
      "translateSelection 应存在"
    );
  });

  test("CodeLens 在定理行生成按钮", async () => {
    const doc = await vscode.workspace.openTextDocument({
      language: "lean",
      content: [
        "import Mathlib",
        "",
        "theorem demo (P Q R : Prop) (h1 : P → Q) (h2 : Q → R) (hp : P) : R := by",
        "  apply h2",
        "  apply h1",
        "  exact hp",
        "",
        "theorem broken (a : Nat) : a = 0 := by",
        "  rfl",
      ].join("\n"),
    });
    await vscode.window.showTextDocument(doc);

    const lenses = await vscode.commands.executeCommand<vscode.CodeLens[]>(
      "vscode.executeCodeLensProvider",
      doc.uri
    );
    assert.ok(
      lenses && lenses.length >= 2,
      `应至少找到 2 个 CodeLens，实际 ${lenses?.length}`
    );
    const titles = lenses.map((l) => (l.command?.title || "")).join("|");
    assert.ok(titles.includes("翻译"), `按钮标题应含翻译: ${titles}`);
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

  test("CLI explain 命令返回解释", async function () {
    this.timeout(60000);
    // 优先用 venv python（开发环境），否则用系统 python3
    const py = fs.existsSync(
      "/Volumes/DataHub/Dev/LeanWeaver/.venv/bin/python3"
    )
      ? "/Volumes/DataHub/Dev/LeanWeaver/.venv/bin/python3"
      : "python3";
    const out = await run(
      `${py} -m leanweaver explain "type mismatch
  term
    a + b
  has type
    Nat
  but is expected to have type
    String"`
    );
    assert.ok(
      out.includes("Type mismatch") || out.includes("类型不匹配"),
      `应包含报错解释: ${out.slice(0, 50)}`
    );
  });
});
