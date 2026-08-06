"""English templates for Lean error explanations (default locale).

Each category maps to:
- title: short human title
- what: plain-language explanation of what the error means
- why: common causes
- fix: actionable fixes
- example: common mistake → fix (optional)
"""

from __future__ import annotations

from typing import Any

from ..classify import ErrorCategory

# fmt: off
TEMPLATES_EN: dict[ErrorCategory, dict[str, Any]] = {
    ErrorCategory.TYPE_MISMATCH: {
        "title": "Type mismatch",
        "what": (
            "Lean is a strongly-typed system. It found that an expression you wrote "
            "has a type that does not match the type it expected at that position. "
            "In short: you supplied a value of type A where a value of type B was needed."
        ),
        "why": [
            "Mixing values of different types, e.g. using a Nat where a String is expected",
            "Using the wrong variable/function, e.g. string concatenation instead of addition",
            "In dependent-type scenarios, an intermediate type does not match the declaration",
        ],
        "fix": [
            "Look at the two lines in the error: `has type` (the actual type you gave) vs `but is expected to have type` (the expected type). Figure out why they differ",
            "Check whether an explicit coercion is missing (e.g. Nat → Int)",
            "If type families / dependent types are involved, check argument order",
        ],
        "example": (
            "Wrong: using `a + b` (Nat) where a String is expected.\n"
            "Fix: make sure the types of `a` and `b` fit the operation, or use the right type."
        ),
    },

    ErrorCategory.UNKNOWN_IDENTIFIER: {
        "title": "Unknown identifier",
        "what": (
            "Lean cannot find the name you wrote — it is not in the current scope. "
            "This can be a typo, a missing import, an undefined declaration, "
            "or using a variable outside its scope."
        ),
        "why": [
            "Misspelled name (case, underscores)",
            "Missing `import` for the module that defines it",
            "Referencing a local variable outside its scope (e.g. outside a `by` block or `have` block)",
            "The declaration is not yet written, or appears after the usage site",
        ],
        "fix": [
            "Check spelling and capitalization",
            "If it comes from mathlib, make sure you `import Mathlib.*` (or the right module)",
            "If it's a local definition, move it into scope",
            "Use IDE autocomplete to confirm the name actually exists",
        ],
    },

    ErrorCategory.UNSOLVED_GOALS: {
        "title": "Unsolved goals",
        "what": (
            "After your proof script, Lean found proof goals that were never closed. "
            "Your proof is incomplete: some propositions that should be proven are still open."
        ),
        "why": [
            "The proof ends halfway; some subgoals were left unhandled",
            "A `·` branch was opened but not fully closed",
            "The final tactic did not fully solve the goal",
        ],
        "fix": [
            "Read the remaining goals (`⊢ ...`) printed in the error and close each one",
            "If remaining goals are trivial, finish with `simp` / `omega` / `aesop`",
            "Check that every `·` indented block is closed",
        ],
    },

    ErrorCategory.NO_GOALS: {
        "title": "No goals to be solved",
        "what": (
            "The proof is already complete, but you keep writing proof steps. "
            "Lean rejects the extra commands because there is nothing left to prove."
        ),
        "why": [
            "Extra tactic at the end of a `by ...` block",
            "Two `by` blocks written in one theorem",
            "A `have` / `let` already solved the goal, then more steps were added",
        ],
        "fix": [
            "Delete the extra final step",
            "If two `by` blocks are adjacent, merge them into one",
        ],
    },

    ErrorCategory.FAILED_TO_SYNTHESIZE: {
        "title": "Failed to synthesize typeclass instance",
        "what": (
            "Lean tried to automatically find an instance of a typeclass "
            "(such as `OfNat`, `HMul`, `Decidable`, `Add`) and found none. "
            "This is the 'can't find the instance' error."
        ),
        "why": [
            "A required typeclass instance is missing",
            "The type is custom and has no registered operation instances",
            "Argument types do not satisfy the instance's preconditions",
        ],
        "fix": [
            "Read which typeclass is needed (e.g. `OfNat ... 2`) and find the missing instance",
            "Add an `instance` for your custom type",
            "Sometimes `import Mathlib.Data...` provides the instance for free",
        ],
    },

    ErrorCategory.MOTIVE_NOT_CORRECT: {
        "title": "Motive is not type correct",
        "what": (
            "This is one of the most confusing Lean errors, appearing in `match` / "
            "`induction` / dependent elimination. The motive is the proposition/type "
            "you want to prove or construct, and Lean requires it to be well-typed "
            "for every constructor branch."
        ),
        "why": [
            "The branches of a `match` return different types",
            "The motive mishandles the index parameters of an indexed type",
            "In dependent pattern matching, a branch uses the wrong variable",
        ],
        "fix": [
            "Make sure all `match` branches return the same type",
            "When handling indexed types (e.g. `Vec α n`), the motive must include the index variable",
            "Try `induction` instead of a hand-written `match` — Lean generates the correct motive for you",
        ],
    },

    ErrorCategory.RECURSIVE_FAILED: {
        "title": "Recursive definition failed termination check",
        "what": (
            "Lean's termination checker believes this recursion might not terminate, "
            "or the structural recursion does not decrease on an argument. "
            "Lean requires recursive calls to happen on a structurally smaller argument."
        ),
        "why": [
            "The recursive call is not on a smaller argument (e.g. `f n := f (n+1)`)",
            "The recursion happens in a non-structural position (e.g. passed inside another function)",
            "With multiple arguments, none is declared as the decreasing one",
        ],
        "fix": [
            "Recurse on a smaller argument (`n-1`, `xs.tail`, ...)",
            "Use `termination_by` to declare the decreasing quantity explicitly",
            "If needed, provide a proof with `decreasing_by`",
        ],
    },

    ErrorCategory.INVALID_FIELD: {
        "title": "Invalid field notation",
        "what": (
            "You used dot-notation field access (e.g. `x.field`), but that type has no "
            "such field, or Lean cannot infer the structure type of the expression."
        ),
        "why": [
            "Field name is misspelled or does not exist",
            "The type of the accessed object is ambiguous",
            "The object is not a structure type",
        ],
        "fix": [
            "Check the field name (IDE autocomplete after `x.` shows valid fields)",
            "Add an explicit type annotation to help inference",
            "Confirm the object is indeed a structure/typeclass field access",
        ],
    },

    ErrorCategory.FUNCTION_EXPECTED: {
        "title": "Function expected",
        "what": (
            "You called something that is not a function (it is followed by arguments). "
            "Lean says: a function is expected here, but what you gave is not one."
        ),
        "why": [
            "Wrong variable name — a plain value used as a function",
            "A function needs some arguments applied first",
            "Wrong argument type for a higher-order function",
        ],
        "fix": [
            "Check whether the called name is actually a function",
            "Confirm argument count and types",
        ],
    },

    ErrorCategory.UNEXPECTED_TOKEN: {
        "title": "Unexpected token",
        "what": (
            "The parser met a symbol at a position it did not expect — usually a syntax "
            "error: unbalanced parentheses, a wrong symbol, or a misplaced `by`."
        ),
        "why": [
            "Unbalanced parentheses / quotes",
            "A symbol Lean does not recognize",
            "A misspelled keyword (e.g. `theroem` → `theorem`)",
        ],
        "fix": [
            "Check parenthesis pairing near the reported position",
            "Look for `:=` written as `=` or a missing `:`",
            "Use IDE syntax highlighting to find the first position that turns red",
        ],
    },

    ErrorCategory.SYNTAX_ERROR: {
        "title": "Syntax error",
        "what": "Lean's parser could not understand the syntactic structure of this code.",
        "why": [
            "Incomplete declaration (missing `:=` / `:` / comma)",
            "Wrong symbol or keyword",
            "Malformed structure or term syntax",
        ],
        "fix": [
            "Look backwards from the error position for the nearest incomplete statement",
            "Compare against a known-good example (IDE or docs)",
        ],
    },

    ErrorCategory.UNUSED_VARIABLE: {
        "title": "Unused variable",
        "what": "(Warning) You introduced a variable but never used it in the proof/code.",
        "why": [
            "A leftover hypothesis or variable",
            "Meant to use it but wrote the wrong name",
        ],
        "fix": [
            "Remove it, or use `_` if you want a placeholder",
        ],
    },

    ErrorCategory.DECLARATION_USES_SORRY: {
        "title": "Declaration uses 'sorry'",
        "what": "(Warning) This theorem uses `sorry` / `admit` as a placeholder, meaning it is not actually proved.",
        "why": ["A temporary placeholder left from debugging"],
        "fix": [
            "Replace `sorry` with a real proof",
            "Grep for `sorry` across the repo before submitting",
        ],
    },

    ErrorCategory.INVALID_TARGET: {
        "title": "Invalid induction target (index occurs more than once)",
        "what": (
            "When you use `induction` (or dependent pattern matching) on a hypothesis, "
            "Lean needs to 'generalize' the target. This error means the variable you are "
            "inducting on appears multiple times in the target (or in the type of another "
            "hypothesis), so Lean cannot generalize it cleanly. This is one of the hardest "
            "Lean errors for beginners."
        ),
        "why": [
            "The induction variable appears more than once in the goal or in an index of the type",
            "The hypothesis you're inducting on has an index that also occurs elsewhere",
            "You need dependent pattern matching but wrote plain `induction`/`cases`",
        ],
        "fix": [
            "Try `generalize` on the problematic variable first, or revert other hypotheses that mention it",
            "Use `induction` with an explicit motive, or try `revert` on hypotheses mentioning the index",
            "Sometimes `rcases` / pattern matching on the actual constructor works better than `induction`",
        ],
    },

    ErrorCategory.CALC_ERROR: {
        "title": "Invalid calc step",
        "what": (
            "In a `calc` block, each line's right-hand side must be definitionally equal to "
            "the expected value from the chain. Lean found that what you wrote does not "
            "continue the chain correctly (type mismatch between steps)."
        ),
        "why": [
            "The intermediate expression in a `calc` line doesn't match what the chain requires",
            "A `by ...` proof for one step actually proves a different equality",
            "The chain's expected value (from the previous step) differs from what you claimed",
        ],
        "fix": [
            "Look at 'right-hand side is' (what you wrote) vs 'but is expected to be' (what the chain needs)",
            "Check that each step's left-hand side equals the previous step's right-hand side",
            "Make sure the proof after `:=` proves exactly the equality shown",
        ],
    },

    ErrorCategory.MISSING_IMPORT: {
        "title": "Missing import / unknown module",
        "what": "The module you are importing does not exist, or the path is wrong.",
        "why": [
            "Misspelled module name",
            "Wrong path within mathlib",
            "Dependencies not fetched (lake not updated)",
        ],
        "fix": [
            "Confirm the real module path (use IDE go-to-definition)",
            "Run `lake update` / `lake build` to fetch dependencies",
        ],
    },

    ErrorCategory.UNKNOWN: {
        "title": "Unrecognized error",
        "what": (
            "This error is not yet covered by the rule library. "
            "If you see it often, open an issue and we will add a template."
        ),
        "why": [],
        "fix": [
            "If it appears often, open an issue and we will add a template.",
        ],
    },
}
# fmt: on
