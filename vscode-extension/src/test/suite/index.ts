import * as path from "path";
import * as fs from "fs";

// 确保测试运行器能找到 mocha（扩展宿主进程的 require 路径可能不含 node_modules）
const extRoot = path.resolve(__dirname, "../../..");
try {
  require("module").Module._initPaths();
} catch {
  /* ignore */
}
// 显式把扩展的 node_modules 加入 require 搜索路径
const Module = require("module") as any;
const nodeModules = path.join(extRoot, "node_modules");
Module.globalPaths.push(nodeModules);

const Mocha = require("mocha") as typeof import("mocha");

/**
 * VS Code 扩展测试入口（Mocha 运行器）。
 * 加载本目录下 *.test.js 文件。
 */

export async function run(): Promise<void> {
  const mocha = new (Mocha as any)({
    ui: "tdd",
    color: true,
    timeout: 120000,
  });

  const testsRoot = __dirname;
  const files = fs.readdirSync(testsRoot).filter((f) => f.endsWith(".test.js"));
  files.forEach((f) => mocha.addFile(path.resolve(testsRoot, f)));

  await new Promise<void>((resolve, reject) => {
    mocha.run((failures: number) => {
      if (failures > 0) return reject(new Error(`${failures} tests failed.`));
      resolve();
    });
  });
}
