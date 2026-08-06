# LeanWeaver VS Code 扩展

> 让 Lean 4 形式化证明对人类可读——证明翻译 + 报错解释。
> Make Lean 4 formal proofs readable to humans.

## 功能

在 `.lean` 文件里右键或命令面板：

| 命令 | 功能 |
|---|---|
| **LeanWeaver: 翻译当前证明** | 把文件里的证明翻译成中文可读证明 + 逐行注释（Herald 风格） |
| **LeanWeaver: 解释当前文件报错** | 把文件的每个报错翻译成中文人话 + 修复建议 |

输出显示在侧边 Webview 面板。

## 依赖（需先装好）

```bash
# 1. LeanWeaver CLI
pip install leanweaver        # 或从源码: pip install -e /path/to/LeanWeaver

# 2. Lean 工具链
curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# 3. LLM（翻译需要）— 配置 OpenAI 兼容 API（如 DeepSeek）
export LEANWEAVER_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.deepseek.com/v1
export LEANWEAVER_MODEL=deepseek-chat
```

## 配置项

在 VS Code 设置里搜索 `leanweaver`：

| 设置 | 默认 | 说明 |
|---|---|---|
| `leanweaver.leanweaverCli` | `python3 -m leanweaver` | CLI 调用命令 |
| `leanweaver.lang` | `zh` | 输出语言（zh/en） |

## 开发

```bash
cd vscode-extension
npm install
npm run compile     # 编译 TypeScript → dist/
# 在 VS Code 里 F5 启动调试宿主
```

## 发布（打包 vsix）

```bash
npm install -g @vscode/vsce
vsce package        # 生成 .vsix，可离线安装或上传扩展市场
```

## 许可

MIT
