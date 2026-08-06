# LeanWeaver VS Code 扩展

> 让 Lean 4 形式化证明对人类可读——报错中文解释 + 证明翻译。

## 核心能力

| 能力 | 触发方式 | 说明 |
|---|---|---|
| **🖱️ 报错悬停解释** | 鼠标悬停在红波浪线上 | 秒出中文解释（规则层，免费离线） |
| **🔍 定理行翻译按钮** | 定理上方 CodeLens「翻译证明」 | 逐定理精确翻译 |
| **📖 翻译当前文件** | 右键 / 命令面板 | 中文可读证明 + 逐行注释 |
| **✂️ 翻译选中代码** | 选中后右键 | 翻译一段证明片段 |
| **🔧 解释报错** | 右键 / 命令面板 | 列出文件所有报错的中文解释 |
| **📊 状态栏** | 左下角 | 环境状态（CLI/Lean/LLM） |

## 安装

```bash
# 1. LeanWeaver CLI
pip install leanweaver

# 2. Lean 工具链
curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# 3. 安装扩展
code --install-extension leanweaver-0.2.0.vsix
# 或从扩展市场安装（发布后）
```

## 配置

VS Code 设置搜索 `leanweaver`：

| 设置 | 默认 | 说明 |
|---|---|---|
| `leanweaver.leanweaverCli` | `python3 -m leanweaver` | CLI 调用命令 |
| `leanweaver.lang` | `zh` | 输出语言（zh/en） |
| `leanweaver.llmFallback` | `false` | 规则未命中时用 LLM 兜底 |

## LLM 配置（翻译需要；报错解释不需要）

```bash
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.deepseek.com/v1   # DeepSeek 示例
export LEANWEAVER_MODEL=deepseek-chat
```

## 架构

```
src/
├── extension.ts   # 入口：命令注册 + 激活引导
├── env.ts         # 环境检测（CLI/Lean/LLM）
├── leanweaver.ts  # CLI 调用封装
├── hover.ts       # 报错悬停解释（规则层，带缓存）
├── codelens.ts    # 定理行「翻译证明」按钮
├── webview.ts     # 输出面板（Markdown 渲染）
└── statusbar.ts   # 状态栏
```

设计原则：**所有功能复用 Python CLI**（单一实现源），TypeScript 层只做 UI 集成。

## 开发 / 打包

```bash
npm install
npm run compile     # 编译 TS
npx @vscode/vsce package --no-dependencies   # 打包 vsix
```

## 许可

MIT
