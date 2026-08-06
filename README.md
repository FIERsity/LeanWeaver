# LeanWeaver

> 让形式化证明对人类可读。
> Make formal proofs readable to humans.

**LeanWeaver** 是一个面向 **Lean 4 定理证明器** 的中文 AI4Math 工具链，围绕一个核心理念：数学社区对 AI 产出的形式化证明最大的抱怨是"证明了但人读不懂"（见 MathOverflow 关于 AI-generated Lean proofs 的争论）。LeanWeaver 要织起"形式化证明 ↔ 自然语言"之间的桥。

## 当前功能（v0.1：错误解释器 · 规则层）

Lean 4 的报错对新手极不友好（`type mismatch`、`motive is not type correct`、`unsolved goals`……全是英文晦涩术语）。LeanWeaver 提供一个 **中文错误解释器**：

- **纯规则引擎，不依赖任何 LLM**：内置 20+ 类高频 Lean 错误的中文解释模板，毫秒级返回，可离线使用
- 输入 = Lean LSP 的结构化诊断（range + message），输出 = 中文人话解释 + 常见原因 + 修复建议
- 规则没命中时才可选用 LLM 兜底（可选，默认关闭）

```bash
# 输入一条 Lean 报错
$ leanweaver explain "type mismatch
  term
    a + b
  has type
    Nat
  but is expected to have type
    String"

# 输出
【类型不匹配 (type mismatch)】
Lean 发现一个表达式的类型与期望类型不一致……
```

## 路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| ① 错误解释器 · 规则层 | 高频 Lean 错误分类 + 中文模板 | ✅ 进行中 |
| ①+ 错误解释器 · LLM 兜底 | 规则未命中时接模型（API / 本地 Ollama 双通道） | ⬜ |
| ①+ VS Code / MCP 集成 | 把解释器接入编辑器诊断面板 | ⬜ |
| ② 证明翻译器 · v1 | formal proof → 中文可读证明（接模型，主线） | ⬜ |
| ②+ 反向翻译 | 中文/自然语言证明 → Lean 骨架 | ⬜ |
| 彩蛋 | 中文 tactic 词表（verbose-lean4 的中文版） | ⬜ |

## 设计原则

1. **信任机制优先**：数学场景下 LLM 幻觉代价最高，能确定性解释的绝不让模型猜
2. **分层架构**：规则层（快/免费/离线）→ LLM 兜底层（慢/按次计费），80% 报错走规则层
3. **模型可插拔**：OpenAI / DeepSeek / Claude / 本地 Ollama 统一接口
4. **面向中文社区**：文档、报错解释、教学路径全部中文优先

## 快速开始

```bash
pip install -e .
# 或者直接运行
python -m leanweaver explain "paste lean error message here"
```

## 许可

MIT
