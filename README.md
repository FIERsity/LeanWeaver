# LeanWeaver

> Make formal proofs readable to humans.

**LeanWeaver** is an AI4Math toolchain for the **Lean 4 theorem prover**, built around one idea: the math community's biggest complaint about AI-generated formal proofs is that *"it's proved, but humans can't read it"* (see the MathOverflow debate on AI-generated Lean proofs). LeanWeaver weaves a bridge between **formal proofs and natural language**.

Built primarily for the English-speaking formal-math community (mathlib, LeanDojo, MathOverflow), with **Chinese available as an optional locale plugin**.

## Current feature (v0.1: Error Explainer · rule-based)

Lean 4's error messages are notoriously opaque to newcomers (`type mismatch`, `motive is not type correct`, `unsolved goals`...). LeanWeaver provides a plain-language **error explainer**:

- **Pure rule engine — no LLM required**: 20+ categories of frequent Lean errors with clear explanations. Millisecond latency, works offline.
- Input = Lean LSP structured diagnostics (range + message), output = plain-language explanation + common causes + fixes.
- Optional LLM fallback when rules miss (disabled by default).

```bash
$ leanweaver explain "type mismatch
  term
    a + b
  has type
    Nat
  but is expected to have type
    String"

# → 【Type mismatch】
#   Lean is a strongly-typed system. It found that an expression you wrote
#   has a type that does not match the type it expected at that position...
```

**Chinese plugin**: pass `--lang zh` (or `explain(..., lang="zh")`) for Chinese explanations:

```bash
$ leanweaver explain --lang zh "type mismatch ..."
# → 【类型不匹配（type mismatch）】...
```

## Roadmap

| Stage | Content | Status |
|---|---|---|
| ① Error Explainer · rules | error classification + templates (EN core / ZH plugin) | 🚧 in progress |
| ①+ Error Explainer · LLM fallback | model fallback for unmatched errors (OpenAI / Ollama) | ⬜ |
| ①+ VS Code / MCP integration | inline explanations in the editor diagnostics | ⬜ |
| ② Proof Translator · v1 (**main line**) | formal proof → readable natural-language proof | ⬜ |
| ②+ Reverse translation | natural-language proof → Lean skeleton | ⬜ |
| Bonus | Chinese tactic aliases (a zh counterpart of verbose-lean4) | ⬜ |

## Design principles

1. **Trust first**: in math, LLM hallucination is the most costly failure. Anything that can be explained deterministically should not be left to a model to guess.
2. **Layered architecture**: rule layer (fast / free / offline) → LLM fallback layer (slow / per-call). ~80% of errors are handled by rules.
3. **Pluggable models**: OpenAI-compatible APIs and local Ollama behind one interface.
4. **Localization as plugins**: English is the default locale; other languages (zh) are optional plugins — easy to add more.

## Quick start

```bash
pip install -e .
# or run directly
python -m leanweaver explain "paste lean error message here"
python -m leanweaver explain --lang zh "paste lean error message here"
```

Run tests:

```bash
pip install -e ".[dev]" && pytest
```

## License

MIT
