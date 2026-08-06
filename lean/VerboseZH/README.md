# VerboseZH — Verbose Lean 中文语言层（已暂停，见下）

> ⚠️ **重要更新（2026-08-06）**：实测确认 **Lean 4.31 不支持中文字符作为 tactic 关键词**
> （详见 [docs/lean-chinese-support.md](../docs/lean-chinese-support.md)）。
> "中文 tactic 词表"（本子项目原始目标）在当前 Lean 版本下**不可行**，方向已重新定位。

## 为什么做这个

verbose-lean4 的目标是"让 Lean 代码更容易转化成传统论文证明"——它用受控自然语言
（`By h we get`、`It suffices to prove`）把证明步骤变成可读的句子。作者明确表示
不维护自己不懂的语言，欢迎社区做其他语言版本。**中文版目前是空白**。

## 调研结论（关键）

实测 Lean 4.31：
- ❌ tactic 关键词（`elab "平凡" : tactic`）不支持中文
- ❌ 中文标识符（定义名/变量名/定理名）不支持
- ✅ term 级 `notation` 支持中文（`notation "真" => True`）

**结论**：中文 tactic 词表在当前 Lean 版本不可行——是词法限制，不是实现问题。

## 方向调整

1. **战术↔中文术语对照表**（数据层）→ 喂给 LeanWeaver 证明翻译器提升质量
2. **中文教学文档**：verbose-lean4 示例的中文对照阅读
3. **中文 notation**：为常用数学概念定义中文 term 记号（有限可用）
4. 若 Lean 未来支持 CJK 标识符（lean4-unicode-basic 等探索中），本源码可重启

## 保留的源码（已验证可编译）

- `VerboseZH/Chinese/Common.lean`：中文语法类别设计
- `VerboseZH/Chinese/Tactics.lean`：中文战术定义（编译通过，但运行时 Lean 不识别中文关键词）
- `VerboseZH/Chinese/All.lean`：中文错误信息（`implement_endpoint (lang := zh)`）
- `VerboseZH/Chinese/Examples.lean`：示例

> 技术验证价值：确认了 `syntax`/`elab` 机制与 `implement_endpoint (lang := zh)` 多语言机制
> 在中文下的边界——对将来支持 CJK 的 Lean 版本有直接参考价值。

## 架构

```
VerboseZH/Chinese/
├── Common.lean    # 中文语法类别（maybeAppliedZH / newStuffZH / factsZH）
├── Tactics.lean   # 中文战术定义（我们由...得到 / 只需证明 / 恰有 ...）
├── All.lean       # 中文错误信息（implement_endpoint lang := zh）
└── Examples.lean  # 可编译的用法示例
```

核心思想（与 verbose-lean4 一致）：**机制与语言分离**。
机制层（`Verbose.Tactics.*`）完全复用，语言层只做两件事：
1. 用 `elab`/`syntax` 定义中文自然语言命令 → 转成机制层能理解的形式
2. 用 `implement_endpoint (lang := zh)` 提供中文错误信息

## 中文词表示例

```lean
import VerboseZH.Chinese.All

-- 分解合取假设
example (P Q : Prop) (h : P ∧ Q) : Q := by
  我们由 h 得到 (hQ : Q)
  恰有 hQ

-- 存在量词
example (n : Nat) (h : ∃ k, n = 2*k) : True := by
  我们由 h 得到 k 使得 (H : n = 2*k)
  平凡

-- 蕴含应用
example (P Q : Prop) (h : P → Q) (h' : P) : Q := by
  我们由 h 只需证明 P
  恰有 h'

-- 分类讨论
example (P Q : Prop) (h : P ∨ Q) : True := by
  分类讨论 P 或 Q
  · 恰有 h
    平凡
  · 平凡
```

## 当前词表（v0.1）

| 中文命令 | 对应英文 | 底层行为 |
|---|---|---|
| `我们由 h 得到 ...` | `By h we get ...` | 分解假设（rcases/obtain） |
| `我们由 h 选取 ...` | `By h we choose ...` | 选择函数（choose） |
| `我们由 h 只需证明 P` | `By h it suffices to prove P` | 应用假设 |
| `我们得以 h` | `We conclude by h` | 结束目标（exact） |
| `我们计算` | `We compute` | 计算化简 |
| `设 x := v` | `Set x := v` | let |
| `先证 P` | `Let's first prove that` | have |
| `固定 x` | `Fix x` | intro |
| `反证` | `We contrapose` | 反证法 |
| `分类讨论 P 或 Q` | `We discuss ... or ...` | by_cases |
| `恰有 t` | `exact t` | exact |
| `平凡` | `trivial` | trivial |
| `假设成立` | `hypothesis` | assumption 强化版 |

## 编译

依赖 Lean 4.31 + mathlib v4.31 + verbose-lean4：

```bash
cd lean/VerboseZH
lake build   # 首次会下载 mathlib（较大）
```

## 路线

- [x] v0.1：核心词表 + 中文错误信息 + 示例
- [ ] 扩充：`我们得名`（rename）、`改写`（rw）、`展开`（unfold）、`归纳`（induction）
- [ ] `help` 建议机制的中文化（Verbose 的"下一步提示"）
- [ ] 教学 DSL 中文化（Exercise/Given/Assume/Proof/QED → 题目/已知/求证/证明/证毕）

## 许可

MIT（LeanWeaver 项目）；依赖的 verbose-lean4 为 Apache-2.0。
