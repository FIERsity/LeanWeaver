# LeanWeaver

> 纯规则、零 LLM 的 Lean 4 报错解释器。
> Rule-based, zero-LLM Lean 4 error explainer — deterministic, offline, free.

Lean 4 的报错对新手极其不友好（`type mismatch`、`motive is not type correct`、`invalid 'calc' step`……全是英文晦涩术语）。**LeanWeaver 把报错翻译成人话**——用确定性规则，不用任何大模型。

## 为什么不用 LLM

- **确定性**：同一个报错，永远得到同一个解释。可复现、无幻觉。
- **离线**：不需要网络、不需要 API key。
- **免费**：零成本，毫秒级返回。
- **可信**：Lean 社区信任"编译器验证"，不信任 AI 猜。

## 快速开始

```bash
pip install -e .
leanweaver explain --lang zh "type mismatch
  term
    a + b
  has type
    Nat
  but is expected to have type
    String"
```

或者从 stdin：

```bash
echo "unsolved goals
⊢ a + b = b + a" | leanweaver explain --lang zh
```

## 支持的错误类别（20+）

| 类别 | 示例报错 |
|---|---|
| `type_mismatch` | `Type mismatch ... has type Nat but is expected to have type String` |
| `app_type_mismatch` | `Application type mismatch: The argument "hello" has type String but is expected to have type Nat` |
| `unknown_identifier` | `Unknown identifier \`foo\`` |
| `unsolved_goals` | `unsolved goals ... ⊢ c + (a + b) = c + b + a` |
| `no_goals` | `No goals to be solved` |
| `failed_to_synthesize` | `failed to synthesize instance of type class HAdd Nat String String` |
| `invalid_target` | `Invalid target: Target (or one of its indices) occurs more than once` |
| `calc_error` | `invalid 'calc' step, right-hand side is ... but is expected to be ...` |
| `recursive_failed` | `fail to show termination for ... failed to infer structural recursion` |
| `invalid_field` | `Invalid field \`z\` ... does not have field` |
| `function_expected` | `Function expected at ... but this term has type Nat` |
| `motive_not_correct` | `motive is not type correct` |
| `missing_import` | `unknown module prefix` |
| … | 更多见 `leanweaver/errors/classify.py` |

每个类别都有中英双语解释：**含义 + 常见原因 + 可操作修复**。

## 架构

```
leanweaver/
├── errors/
│   ├── classify.py     # 确定性分类（error code + 文本模式）
│   ├── templates.py    # 语言注册表 + 缺失回退
│   ├── explain.py      # 解释器入口（纯规则）
│   └── locales/
│       ├── en.py       # 英文模板（默认）
│       └── zh.py       # 中文模板（插件）
└── cli.py              # leanweaver explain
```

设计原则：
- **机制与语言分离**：分类逻辑与文案完全解耦，加语言只需加一个 locale 文件
- **优先 error code**：Lean 诊断里的 `error(lean.xxx)` 比文本匹配更可靠
- **版本演进可维护**：报错文本随 Lean 版本变化，规则库按版本维护

## 测试

```bash
pip install -e ".[dev]" && pytest
```

包含 15+ 个真实 Lean 报错样本（从本机 `lean` 实际运行收集）。

## 许可

MIT
