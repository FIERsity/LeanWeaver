import * as vscode from "vscode";
import * as assert from "assert";
import { classify, explain, pretty } from "../../engine";

/**
 * LeanWeaver 扩展集成测试 —— 纯规则引擎内嵌，零 CLI 依赖。
 */

suite("LeanWeaver 集成测试（内置引擎）", () => {
  test("扩展已激活，无 CLI 命令残留", async () => {
    const cmds = await vscode.commands.getCommands();
    assert.ok(!cmds.includes("leanweaver.diagnose"), "diagnose 应已移除");
    assert.ok(!cmds.includes("leanweaver.translate"), "translate 应已移除");
  });

  test("hover provider 可调用（不抛异常）", async () => {
    const doc = await vscode.workspace.openTextDocument({
      language: "lean4",
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

  test("内置引擎：type mismatch 分类正确", () => {
    const r = classify(
      "Type mismatch\n  s\nhas type\n  String\nbut is expected to have type\n  Nat"
    );
    assert.strictEqual(r.category, "type_mismatch");
  });

  test("内置引擎：error code 优先", () => {
    const r = classify("error(lean.invalidField): Invalid field `z`");
    assert.strictEqual(r.category, "invalid_field");
  });

  test("内置引擎：中文解释（默认 en，可切 zh）", () => {
    const en = explain(
      "Unknown identifier `foo`",
      "en"
    );
    assert.ok(en.title.includes("Unknown") || en.title.includes("unknown"));

    const zh = explain(
      "Unknown identifier `foo`",
      "zh"
    );
    assert.ok(zh.title.includes("未知标识符") || zh.title.includes("未知"));
    assert.ok(zh.fix.length > 0);
    assert.ok(pretty(zh).includes("修复"));
  });

  test("内置引擎：motive 难报错可解释", () => {
    const zh = explain(
      "Invalid target: Target (or one of its indices) occurs more than once\n  n",
      "zh"
    );
    assert.notStrictEqual(zh.category, "unknown");
    assert.ok(zh.fix.length > 0);
  });

  test("内置引擎：calc 报错可解释", () => {
    const zh = explain(
      "invalid 'calc' step, right-hand side is\n  n - n : Nat\nbut is expected to be\n  1 : Nat",
      "zh"
    );
    assert.strictEqual(zh.category, "calc_error");
  });
});
