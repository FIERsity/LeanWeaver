# LeanWeaver 路线图

> 主线：证明翻译器（formal ↔ natural language）
> 铺路：错误解释器（规则层 → LLM 兜底）

## 阶段 ①：错误解释器 · 规则层 ✅

- [x] 错误分类器（classify.py）：20+ 类高频错误（error code + 文本双通道）
- [x] 英文模板库（locales/en.py，默认）+ 中文插件（locales/zh.py）
- [x] 解释器入口 + CLI（leanweaver explain [--lang zh]）
- [x] 13 个真实 Lean 4.32 报错样本（tests/test_real_errors.py）
- [x] `leanweaver check <file.lean>`：直接分析文件（调用 lean --json）
- [ ] VS Code 扩展：诊断面板内联显示解释

## 阶段 ①+：错误解释器 · LLM 兜底

- [x] LLM 适配器（OpenAI / Ollama 双通道，接口可插拔）
- [x] 语言感知 prompt（en 默认 / zh 插件）
- [ ] 让 LLM 解释带上"从 Lean 环境取到的定义"

## 阶段 ②：证明翻译器 v1 ✅（主线）

- [x] 证明提取器（parser.py）：从 Lean 源码提取 by 块 + 切分 tactic
- [x] 逐步解释 + 连贯可读证明（LLM 驱动，zh/en）
- [x] CLI：leanweaver translate <file.lean> [--theorem NAME]
- [x] 战术↔中文术语对照表（data/tactic_glossary.json）注入翻译
- [ ] 用 LeanREPL / Pantograph 获取真实 proof state（当前是文本级，无状态）
- [ ] 对 AI 生成的整段证明做"人话化"（主线价值）

## 阶段 ②+：反向翻译

- [ ] 中文/自然语言证明 → Lean 骨架
- [ ] 中文教学文档：verbose-lean4 示例的中文对照阅读

## 调研沉淀（2026-08-06）

- [x] docs/verbose-lean4-study.md：verbose-lean4 架构学习笔记
- [x] docs/lean-chinese-support.md：**Lean 4 不支持中文 tactic 关键词**（实测）
      → 中文词表改为数据层（术语表）+ 教学文档路线
- [x] docs/real-error-samples.md：真实报错收集方法论

## 技术选型备忘

- 语言：Python（规则层 + LLM 适配） / Lean 侧走 LSP / lean --json
- 错误解释：LSP Diagnostic { message, range, severity }；CLI 用 lean --json
- 证明解析：文本级（parser.py），v2 接 LeanREPL / Pantograph
- LLM：OpenAI 兼容 API + Ollama 双通道，接口在 translate/llm.py
- 许可：MIT
