# Lean 4 中文支持调研（关键结论）

> 日期：2026-08-06，环境：Lean 4.31.0 / mathlib v4.31.0
> 结论直接影响"中文 tactic 词表"（VerboseZH）方向的可行性。

## 核心发现：Lean 4 对中文字符的支持极其有限

通过本机 `lean` 实测（每个结论都有对应测试验证）：

| 能力 | 中文 | 说明 |
|---|---|---|
| **tactic 关键词**（`elab "平凡" : tactic`） | ❌ 不支持 | 报 unsolved goals + expected token，tactic 完全没被解析 |
| **macro 关键词**（`macro "平凡的" : tactic`） | ❌ 不支持 | 同上 |
| **中文 + ASCII 组合**（`elab "由" h "得"`） | ❌ 不支持 | 同上 |
| **标识符**（`def 加法交换 ...`、变量名、定理名） | ❌ 不支持 | `expected token` |
| **term 级 notation**（`notation "真" => True`） | ✅ 支持 | 中文可作 term 记号 |

**结论**：Lean 4.31 的词法分析器（tokenizer）不把 CJK 字符当作合法标识符/关键词字符。
中文只能出现在 `notation` 的 term 层（因为那是纯字符串记号匹配），
不能用作 tactic 关键词、宏名、或任何标识符。

## 这意味着什么

### 1. "中文 tactic 词表"（VerboseZH 原方向）在 Lean 4.31 不可行
verbose-lean4 的英文/法文能用是因为它们是 ASCII。中文 tactic（`我们由...得到`、`恰有`）
**无法注册为 Lean 语法**——这是我们踩坑后实测确认的硬限制，不是实现问题。

### 2. 但"中文 notation"可行（有限用途）
```lean
notation "真" => True      -- ✅
notation "蕴含" => (· → ·) -- ✅（term 层）
```
这可以用于**中文数学记号**（如把常用符号/术语做中文别名），但无法定义"中文证明步骤"。

### 3. 需要规避的方向
- 不注册中文 tactic 关键词（死路）
- 不期望中文定义名/变量名（死路）

## 可行的替代方案（重新定位）

1. **中文教学文档层**：把 verbose-lean4 的教学 DSL 示例翻译成中文，附在 Lean 文件注释里
   （不改变 Lean 语法，只做"对照阅读"）
2. **中文术语对照表**：维护"Lean 战术 ↔ 中文术语"的映射文档/数据（如 `rw → 改写`），
   供学习者和我们的证明翻译器（LLM 层）使用——**这正好和 LeanWeaver 主线（证明翻译器）结合**
3. **中文 notation 补充**：为常用数学概念定义中文 term notation（有限但可用）
4. **等 Lean 未来版本**：若 Lean 增加 CJK 标识符支持（lean4-unicode-basic 等项目在探索），
   届时中文 tactic 词表可重启

## 对 LeanWeaver 的启示

这个发现**反而强化了主线的价值**：
- 用户想要"中文可读的证明"——既然 Lean 本身不支持中文，那么**用 LLM 把形式化证明翻译成中文**（我们的证明翻译器）
  就是唯一的路径，而且更彻底（不只是关键词，是整篇证明的中文化）。
- "中文 tactic 词表"（确定性路线）被技术限制挡住，**LLM 翻译路线（灵活路线）成为主答案**。
- 可以把"战术↔中文术语对照表"作为数据喂给翻译器，提升翻译质量。

## 附录：验证脚本

```bash
# 1. 中文 tactic（失败）
cat > t.lean <<'EOF'
import Mathlib
open Lean Elab Tactic
elab "平凡" : tactic => evalTactic (← `(tactic| trivial))
example : True := by 平凡
EOF
lean t.lean  # unsolved goals + expected token

# 2. 中文 identifier（失败）
cat > t.lean <<'EOF'
import Mathlib
def 加法交换 (a b : Nat) : a + b = b + a := by omega
EOF
lean t.lean  # expected token

# 3. 中文 notation（成功）
cat > t.lean <<'EOF'
import Mathlib
notation "真" => True
example : 真 := by trivial
EOF
lean t.lean  # ✅
```
