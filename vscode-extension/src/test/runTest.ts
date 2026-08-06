import * as path from "path";
import { runTests } from "@vscode/test-electron";

/**
 * 运行集成测试：
 *   npm run test
 * 会下载 VS Code 测试版，加载本扩展，跑 src/test/suite/index.ts
 */

async function main() {
  try {
    const extensionDevelopmentPath = path.resolve(__dirname, "../../");
    const extensionTestsPath = path.resolve(__dirname, "./suite/index");
    await runTests({ extensionDevelopmentPath, extensionTestsPath });
  } catch (err) {
    console.error("集成测试失败:", err);
    process.exit(1);
  }
}

main();
