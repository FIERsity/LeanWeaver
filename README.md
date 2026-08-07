<p align="center">
  <img src="assets/icon-128.png" width="96" height="96" alt="LeanWeaver icon">
</p>

# LeanWeaver

> Rule-based Lean 4 error explainer — hover any error, get a clear explanation.
> 纯规则 Lean 4 报错解释器 —— 悬停报错，秒懂修复。

LeanWeaver explains Lean 4 error messages in plain language. Hover over any red squiggle in a `.lean` file, and LeanWeaver tells you **what the error means, why it happened, and how to fix it** — built entirely on a deterministic rule engine, with **no LLM, no network, no API key, fully offline.**

## 核心形态 / Primary Form

**LeanWeaver is a VS Code extension.** Install it, hover over a Lean error, read the explanation. That's it — no Python, no CLI, no configuration.

## Features

- 🖱️ **Hover to explain** — point at any Lean error/warning, get a plain-language explanation
- 🌍 **English first, 中文可切** — default English, switch to Chinese in one setting
- ⚡ **Instant & offline** — pure rule engine embedded in the extension
- 🔒 **Deterministic** — the same error always gets the same explanation (no hallucination)
- 🎓 **Actionable** — every explanation includes: what it means + common causes + how to fix

## Quick Start

1. Install **LeanWeaver** from the VS Code Marketplace.
2. Install the **official Lean extension** (`leanprover.lean4`) — it provides the diagnostics that LeanWeaver explains. LeanWeaver prompts you if it's missing.
3. Open a `.lean` file and hover over an error.

## Example

Hover over the red squiggle:

```lean
theorem bad (a : Nat) : a = 0 := by
  rfl        ← hover here
```

You get:

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

## Covered Errors

**29 categories**, built from the **official Lean test corpus (691 verified real errors)**:

| Category | Example |
|---|---|
| `type_mismatch` | `Type mismatch ... has type Nat but is expected to have type String` |
| `unknown_identifier` | `Unknown identifier \`foo\`` |
| `unsolved_goals` | `unsolved goals ... ⊢ ...` |
| `calc_error` | `invalid 'calc' step, right-hand side is ... but is expected to be ...` |
| `invalid_target` | `Invalid target: Target (or one of its indices) occurs more than once` |
| `not_proposition` | `type of theorem \`t\` is not a proposition` |
| `infer_failed` | `failed to infer type of binder` |
| `synthesize_implicit` | `don't know how to synthesize implicit argument` |
| `tactic_failed` | `Tactic \`assumption\` failed` |
| `decreasing_failed` | `could not find a decreasing measure` |
| … | 29 categories total, each with en/zh explanations |

**Measured coverage**: 78.4% of user-facing errors in the official corpus are recognized (the rest are long-tail / internal errors).

## Language

English by default. Switch to Chinese:

```json
{
  "leanweaver.lang": "zh"
}
```

## Architecture

```
VS Code extension (self-contained, zero Python dependency)
├── src/engine.ts          # rule engine (error code + text matching, 29 categories)
├── src/generated/rules.ts # auto-generated from Python rule library (single source of truth)
└── src/hover.ts           # hover integration
```

The **Python package** (`leanweaver/`) is the **single source of truth** for the rule library (29 categories, 91 rules, en/zh templates). The extension's `rules.ts` is auto-generated from it:

```bash
python -m leanweaver.gen_rules_ts --out vscode-extension/src/generated/rules.ts
```

Corpus pipeline (all data from official Lean sources, not LLM-generated):

```
lean4 official tests (tests/elab, tests/elab_fail)
  → build_official_corpus.py → data/official_corpus.json (691 errors)
  → classify coverage report
```

## Repository Layout

```
├── vscode-extension/       # the product (self-contained VS Code extension)
├── leanweaver/             # Python rule library (source of truth)
│   ├── errors/             # classify + templates (en/zh)
│   ├── gen_rules_ts.py     # generates extension rules.ts
│   ├── build_official_corpus.py
│   ├── collect_issues.py
│   └── extract_official.py
├── data/official_corpus.json  # 691 official verified errors
├── assets/                 # icon source (icon.svg) + build-icon.sh
├── docs/                   # methodology & real error samples
└── tests/                  # 34 tests
```

The icon lives in `assets/icon.svg` as the single source; `assets/build-icon.sh` rasterises it
to `assets/icon-{128,256}.png` and copies the 256px variant to `vscode-extension/icon.png`.

## Commands

| Command | Description |
|---|---|
| `LeanWeaver: Setup` | Check environment & guide installation of missing pieces |
| `LeanWeaver: Settings` | Open extension settings |

## License

MIT
