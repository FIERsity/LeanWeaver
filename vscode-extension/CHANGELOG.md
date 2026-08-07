# Changelog

All notable changes to LeanWeaver. Kept in sync with `vscode-extension/CHANGELOG.md`.

## [1.0.1] - 2026-08-07

### Added
- **Language auto-detection** — when `leanweaver.lang` is not set, explanations follow the VS Code UI language (a Chinese UI gets Chinese explanations; everything else gets English). An explicit setting still always wins.

### Changed
- Marketplace copy updated (README/description): describes current capabilities only, no LLM comparisons.

## [1.0.0] - 2026-08-07

First stable release.

### Added
- **Windows compatibility** — environment detection no longer shells out to `/bin/bash`; it checks `ELAN_HOME` / `~/.elan/bin` directly and falls back to PATH lookup of `lean --version` (works on Windows, macOS, and Linux).
- **Lean version compatibility declared** — the rule library is built and validated against **Lean 4.32.2** official corpus; error-code-based rules are the stable core across versions. See README → Compatibility.
- **GitHub Actions CI** — Python tests (34), `rules.ts` ↔ Python rule-library sync check, extension compile + integration tests (7) on Linux.
- **Changelog** — this file; the extension now ships its own copy for the marketplace.
- **Extension icon** — official LEAN mark with a VS Code-style red diagnostic squiggle (see `assets/`).

### Changed
- Version bumped to `1.0.0`.
- `package.json` gains `repository` field; `@vscode/test-electron` is now an explicit dev dependency (previously transitive only).
- The extension package now ships the MIT `LICENSE` inside the `.vsix`.

## [0.7.0] - 2026-08-06

### Changed
- **Self-contained architecture** — the rule engine was ported from a Python CLI dependency into the extension itself (TypeScript, `src/engine.ts` + generated `src/generated/rules.ts`).
- **Zero CLI / Python dependency** — installing the extension is all the user needs; no `pip install`, no Python runtime, no configuration.
- Hover explanations now come from the built-in engine (~1 ms, offline, deterministic); verified byte-for-byte consistent with the Python source of truth (691/691 corpus entries).
- The `leanweaverCli` setting and CLI detection were removed.

## [0.6.0] - 2026-08-05

### Added
- **English-first bilingual UI** — explanations default to English, switchable to Chinese via `leanweaver.lang`.
- **Setup onboarding** — the extension detects a missing official Lean extension / toolchain and guides installation.
- Data-driven rule library from the official Lean test corpus (29 categories, 91 rules, en/zh templates).

## Earlier

- Rule library and methodology documented (`docs/`); 691 official verified errors collected into the corpus.
- Initial rule-based explainer (20 hand-written categories) with coverage measured and iterated to ~78% of user-facing errors.
