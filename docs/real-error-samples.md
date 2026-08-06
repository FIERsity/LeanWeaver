# 真实 Lean 报错样本库

> 规则库的扩充方法论：**不是靠猜，而是用真实 Lean 跑出报错，再固化进分类器。**
> 本文件的报错文本均来自本机 `lean 4.32.2` 实际运行输出。

## 如何复现 / 扩充

```bash
# 1. 准备工具链（lean 4.32.2）
curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y

# 2. 写一个故意出错的 .lean 文件，用 lean 直接跑
lean bad.lean   # 输出: file.lean:行:列: error: <真实报错>

# 3. 把报错文本粘进 tests/test_real_errors.py，确认分类正确
# 4. 若分类错误 → 更新 classify.py 的 _RULES / _ERROR_CODES
```

## 关键发现

### 1. Lean 4.32 的诊断带结构化 error code
LSP 诊断的 message 形如 `error(lean.<code>): <detail>`。**error code 比文本匹配更可靠**：

| error code | 对应类别 |
|---|---|
| `lean.unknownIdentifier` | UNKNOWN_IDENTIFIER |
| `lean.invalidField` | INVALID_FIELD |
| `lean.synthInstanceFailed` | FAILED_TO_SYNTHESIZE |
| `lean.invalidMotive` | MOTIVE_NOT_CORRECT |

> 💡 这是规则引擎的重大升级方向：**优先解析 error code，文本匹配作为兜底**。

### 2. 真实报错格式（与理想样例的差异）

| 错误 | 真实格式（Lean 4.32） |
|---|---|
| type mismatch | `Type mismatch\n  n\nhas type\n  Nat\nbut is expected to have type\n  String` |
| unknown identifier | `error(lean.unknownIdentifier): Unknown identifier \`bar\`` |
| unsolved goals | `unsolved goals\na b c : Nat\n⊢ c + (a + b) = c + b + a` |
| no goals | `No goals to be solved` |
| synth failed | `error(lean.synthInstanceFailed): failed to synthesize instance of type class\n  HAdd Nat Nat String` |
| invalid field | `error(lean.invalidField): Invalid field \`z\`: The environment does not contain \`Point.z\`` |
| function expected | `Function expected at\n  foo\nbut this term has type\n  Nat` |
| rfl failed | `Tactic \`rfl\` failed: The left-hand side\n  1\nis not definitionally equal to the right-hand side\n  2` |
| recursion | `fail to show termination for ... failed to infer structural recursion:` |
| missing import | `unknown module prefix 'DoesNotExist'` |
| unused var (警告) | `Variable name \`a\` is not explicitly referenced.` |
| sorry (警告) | `declaration uses \`sorry\`` |

### 3. 重要陷阱
- **`x + 1` 期望 String 现在报的是 synthInstanceFailed 而非 type mismatch**——因为 `HAdd Nat Nat String` 找不到实例。真正的 type mismatch 要用"表达式类型与期望不符"触发（如 `def bar : Nat → String | n => n`）。
- **warning 和 error 分离**：LSP 里 severity 区分。`unused variable`、`sorry` 都是 warning，分类器要靠文本兜底。
- **Lean 版本演进会改报错文案**：规则库必须跟随 lean-toolchain 版本维护，这是长期维护成本，也是 error code 方案更稳的原因。

## 已固化的样本（tests/test_real_errors.py）

共 13 个真实场景，覆盖：type mismatch / unknown identifier / unsolved goals / no goals / synth failed / invalid field / function expected / rfl failed / recursion / missing import / unused var / sorry / invalid motive。
