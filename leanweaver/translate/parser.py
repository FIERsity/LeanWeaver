"""Lean 证明提取与 tactic 序列解析。

v1 策略：**不依赖 Lean 状态机**（Pantograph/REPL 留到 v2）。
直接从 Lean 源码文本提取 `by ...` 证明块，按行切分 tactic 序列，
再用 LLM 逐步解释。优点是零环境依赖、快速跑通链路。

限制（v2 改进方向）：
- 无法知道每个 tactic 前后的 proof state（需要 Pantograph 提供）
- 块内缩进结构（· / tactic 块）需要启发式处理
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProofBlock:
    """一个 `by ...` 证明块。"""

    theorem_name: str            # 定理名（或 "example"/"anonymous"）
    theorem_stmt: str            # 定理声明（不含证明）
    source: str                  # 原始 by 块文本（含 by 前缀）
    tactics: list[str] = field(default_factory=list)  # 切分后的 tactic 序列

    def __repr__(self) -> str:
        return f"<ProofBlock {self.theorem_name}: {len(self.tactics)} tactics>"


# 匹配 `theorem/lemma/def/example <name> ... : <stmt> := by` 或 `:= <term>`
_THEOREM_RE = re.compile(
    r"^(?P<kind>theorem|lemma|def|example|axiom|corollary)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_']*)?"
    r"(?P<sig>.*?)(?P<colon>\s*:\s*)?(?P<stmt>.*?)\s*:=",
    re.MULTILINE | re.DOTALL,
)

# 找到 from := 之后的 by 块
def _find_by_block(source: str, start: int) -> tuple[Optional[str], int]:
    """从 start 找第一个顶层 `by` 块（处理嵌套括号/方括号）。"""
    i = source.find("by", start)
    if i < 0:
        return None, -1
    j = i + 2
    depth_paren = 0
    depth_brace = 0
    depth_bracket = 0
    depth_angle = 0
    while j < len(source):
        c = source[j]
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren = max(0, depth_paren - 1)
        elif c == "{":
            depth_brace += 1
        elif c == "}":
            depth_brace = max(0, depth_brace - 1)
        elif c == "[":
            depth_bracket += 1
        elif c == "]":
            depth_bracket = max(0, depth_bracket - 1)
        elif c == "<":
            depth_angle += 1
        elif c == ">":
            depth_angle = max(0, depth_angle - 1)
        if depth_paren == 0 and depth_brace == 0 and depth_bracket == 0 and depth_angle == 0:
            if c == "\n" and (j + 1 >= len(source) or source[j + 1] != " "):
                # 到达 by 块的逻辑结尾：下一行顶格或文件结尾
                return source[i:j + 1], j + 1
        j += 1
    return source[i:], len(source)


def _split_tactics(block_body: str) -> list[str]:
    """把 by 块体按策略切分。

    启发式：按行切，保留缩进（· 分支用前缀标记）。空行和注释剔除。
    """
    lines = block_body.splitlines()
    tactics: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("--") or stripped.startswith("/-"):
            continue
        # 续行：以 "(" 或 "," 结尾，或行首有缩进（非顶格）
        indent = len(line) - len(line.lstrip())
        if current and (indent > 0 or current[-1].rstrip().endswith((",", "("))):
            current.append(line)
            continue
        if current:
            tactics.append("\n".join(current))
            current = []
        # 新 tactic
        current.append(line.strip())
    if current:
        tactics.append("\n".join(current))
    return tactics


def extract_proofs(source: str) -> list[ProofBlock]:
    """从 Lean 源码提取所有证明块。

    Args:
        source: Lean 源码文本。

    Returns:
        提取到的 ProofBlock 列表。
    """
    blocks: list[ProofBlock] = []
    for m in _THEOREM_RE.finditer(source):
        kind = m.group("kind")
        name = m.group("name") or (kind if kind in ("example",) else "anonymous")
        stmt = m.group("stmt") or ""
        # 找这个定理的 := 之后的 by 块
        body, _ = _find_by_block(source, m.end())
        if body is None:
            continue
        # 去掉 "by " 前缀
        body_content = body[2:].strip()
        if not body_content:
            continue
        tactics = _split_tactics(body_content)
        if not tactics:
            continue
        blocks.append(
            ProofBlock(
                theorem_name=name,
                theorem_stmt=stmt.strip(),
                source=body.strip(),
                tactics=tactics,
            )
        )
    return blocks


def extract_proof(source: str, theorem_name: str | None = None) -> Optional[ProofBlock]:
    """提取指定定理的证明块（不指定名字时取第一个）。"""
    blocks = extract_proofs(source)
    if not blocks:
        return None
    if theorem_name is None:
        return blocks[0]
    for b in blocks:
        if b.theorem_name == theorem_name:
            return b
    return None
