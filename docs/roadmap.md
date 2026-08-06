# LeanWeaver 路线图

> 主线：证明翻译器（formal ↔ natural language）
> 铺路：错误解释器（规则层 → LLM 兜底）

## 阶段 ①：错误解释器 · 规则层（当前）

**目标**：Lean 4 高频报错的中文解释，纯规则、毫秒级、可离线。

- [x] 错误分类器（classify.py）：20+ 类高频错误关键词匹配
- [x] 中文模板库（templates.py）：每个类别 = 通俗解释 + 常见原因 + 修复建议
- [x] 解释器入口（explain.py）+ CLI（leanweaver explain）
- [x] 单元测试
- [ ] **补充真实报错样本**：跑一批真实 Lean 文件，把漏分类的报错补进规则库
- [ ] **接入 LSP**：从 Lean LSP 读取结构化诊断（range + message），而非手工粘贴
- [ ] **VS Code 扩展**：诊断面板内联显示中文解释

## 阶段 ①+：错误解释器 · LLM 兜底

- [ ] 规则未命中时调用 LLM（OpenAI / DeepSeek / Ollama 双通道，接口已预留）
- [ ] 让 LLM 解释带上"从 Lean 环境取到的定义"（差异化：类型/上下文越全解释越准）

## 阶段 ②：证明翻译器 v1（主线）

**目标**：把形式化证明逐步翻译成中文可读证明。

- [ ] 解析 Lean 证明：读 tactic 序列 + 每一步的 proof state（用 LeanREPL / Pantograph）
- [ ] 定义"逐步解释"数据格式：{tactic, 做了什么, 为什么, 前后状态}
- [ ] prompt 设计：喂 状态差 + tactic → 中文解释
- [ ] CLI：`leanweaver translate <file.lean> <thm>` → 中文可读证明
- [ ] 支持对 AI 生成的整段证明做"人话化"（解决"证明了但人读不懂"）

## 阶段 ②+：反向翻译

- [ ] 中文/自然语言证明 → Lean 骨架（先用 verbose-lean4 思路做中文 tactic 词表）

## 彩蛋

- [ ] 中文 tactic 词表包（`改写`≈`rw`、`恰好`≈`exact`，verbose-lean4 的中文版）
- [ ] `leanweaver bench`：统一跑 MiniF2F / ProofNet 的脚手架（社区缺口）

## 技术选型备忘

- 语言：Python（规则层 + LLM 适配） / Lean 侧走 LSP / LeanREPL
- 错误解释：LSP Diagnostic { message, range, severity }
- 证明解析：LeanREPL（leanprover）或 Pantograph（状态快照更精细）
- LLM：OpenAI 兼容 API + Ollama 双通道，接口在 `translate/llm.py`
- 许可：MIT
