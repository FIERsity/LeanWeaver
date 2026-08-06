# LeanWeaver

> Rule-based Lean 4 error explainer — hover any error, get a clear explanation.
> 纯规则 Lean 4 报错解释器 —— 悬停报错，秒懂修复。

**LeanWeaver** is a VS Code extension that explains Lean 4 error messages in plain language. Hover over any red squiggle, and LeanWeaver tells you what the error means, why it happened, and how to fix it — **without any LLM, fully offline, free, and deterministic.**

## Features

- 🖱️ **Hover to explain** — point at any Lean error, get a clear explanation
- 🌍 **English first, 中文可切** — default English, switch to Chinese in settings
- ⚡ **Instant & offline** — pure rule engine in the extension, no network, no API key
- 🔒 **Deterministic** — same error always gets the same explanation
- 🎓 **Beginner-friendly** — each error gets: what it means + common causes + how to fix

## Installation

1. Install **LeanWeaver** from the VS Code Marketplace.
2. Install the **official Lean extension** ([leanprover.lean4](https://marketplace.visualstudio.com/items?itemName=leanprover.lean4)) — it provides the red squiggles that LeanWeaver explains. LeanWeaver will prompt you if it's missing.
3. Open a `.lean` file. That's it.

> No Python, no CLI, no configuration. LeanWeaver is fully self-contained.

## Usage

Hover your mouse over any red (error) or yellow (warning) squiggle in a `.lean` file:

```
theorem bad (a : Nat) : a = 0 := by
  rfl        ← hover here
```

You'll see the original Lean error plus LeanWeaver's plain-language explanation:

```
LeanWeaver
[Type mismatch]

Lean is a strongly-typed system. It found that an expression you wrote
has a type that does not match the type it expected at that position...

Common causes:
  - Mixing values of different types...
Fixes:
  - Look at the two lines: `has type` vs `but is expected to have type`...
```

## Language

English is the default. To switch to Chinese:

1. Open Settings (`Cmd+,` / `Ctrl+,`)
2. Search for `leanweaver.lang`
3. Set it to `zh`

Or set it in `settings.json`:

```json
{
  "leanweaver.lang": "zh"
}
```

## Setup guide

If something is missing (the official Lean extension, or the Lean toolchain), click the **LeanWeaver** item in the status bar, or run the **`LeanWeaver: Setup`** command — it will guide you through installing what's needed.

## Covered errors (29 categories)

Type mismatch, unknown identifier, unsolved goals, no goals, failed to synthesize, calc errors, motive/induction errors, recursion termination, inference failures, implicit argument synthesis, tactic failures, and more — all built from **official Lean test corpus** (691 verified real errors).

## Commands

| Command | Description |
|---|---|
| `LeanWeaver: Setup` | Check environment & guide installation of missing pieces |
| `LeanWeaver: Settings` | Open extension settings |

## License

MIT
