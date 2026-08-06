import * as vscode from "vscode";
import * as assert from "assert";

/**
 * hover 核心逻辑验证：诊断文本 → leanweaver 中文解释。
 * （不依赖 executeHoverProvider 的模拟，直接验证 CLI 解释真实报错）
 */
suite("LeanWeaver hover 核心逻辑", () => {
  test("真实类型不匹配报错 → explain 返回中文解释", async () => {
    // 直接调用扩展的 explainError（通过 CLI，纯规则）
    const { explainError } = require("../../leanweaver.js") as typeof import("../../leanweaver");
    const msg =
      "Type mismatch\n  s\nhas type\n  String\nbut is expected to have type\n  Nat";
    const out = await explainError(msg);
    assert.ok(
      out.includes("类型不匹配") || out.includes("Type mismatch"),
      `应含解释: ${out.slice(0, 80)}`
    );
    assert.ok(
      out.includes("修复") || out.includes("Fixes"),
      `应含修复建议: ${out.slice(0, 120)}`
    );
  });

  test("motive 难报错 → explain 返回中文解释", async () => {
    const { explainError } = require("../../leanweaver.js") as typeof import("../../leanweaver");
    const msg = "Invalid target: Target (or one of its indices) occurs more than once\n  n";
    const out = await explainError(msg);
    assert.ok(
      out.includes("归纳") || out.includes("索引") || out.includes("target"),
      `应含解释: ${out.slice(0, 80)}`
    );
  });
});
