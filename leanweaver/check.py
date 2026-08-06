"""Lean 文件诊断分析。

通过调用本机 `lean --json` 获取结构化诊断（等价于 LSP Diagnostic）：
- data: 报错文本
- kind: 错误种类（如 lean.invalidField._namedError，含 error code）
- severity: error / warning / info
- pos / endPos: 行列位置
- fileName: 文件

这是"接入 LSP"的第一层（CLI 级）：不依赖完整 LSP 协议，
直接解析 lean 的 JSON 输出，即可批量解释一个文件里所有报错。
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .errors.explain import ExplainResult, explain


@dataclass
class LeanDiagnostic:
    """一条结构化诊断（Lean LSP / --json 的同款数据）。"""

    severity: str                    # error / warning / info
    data: str                        # 报错文本
    kind: str = ""                   # 错误种类，含 error code
    file: str = ""
    line: int = 0
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}:{self.column}" if self.file else f"{self.line}:{self.column}"
        return f"{loc}: {self.severity}: {self.data.splitlines()[0]}"


@dataclass
class CheckResult:
    """一个文件的分析结果。"""

    path: str
    diagnostics: list[LeanDiagnostic] = field(default_factory=list)
    explanations: list[ExplainResult] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == "warning")


def find_lean() -> Optional[str]:
    """定位 lean 可执行文件（优先 PATH，其次 ~/.elan）。"""
    import shutil

    exe = shutil.which("lean")
    if exe:
        return exe
    home_lean = Path.home() / ".elan" / "bin" / "lean"
    if home_lean.exists():
        return str(home_lean)
    return None


def parse_diagnostic(raw: dict) -> LeanDiagnostic:
    """把 lean --json 的一行解析为 LeanDiagnostic。"""
    pos = raw.get("pos") or {}
    end_pos = raw.get("endPos") or {}
    return LeanDiagnostic(
        severity=raw.get("severity", "info"),
        data=raw.get("data", ""),
        kind=raw.get("kind", ""),
        file=raw.get("fileName", ""),
        line=pos.get("line", 0),
        column=pos.get("column", 0),
        end_line=end_pos.get("line"),
        end_column=end_pos.get("column"),
    )


def check_file(
    path: str | Path,
    use_llm: bool = False,
    lang: str = "en",
    lean: str | None = None,
) -> CheckResult:
    """分析一个 Lean 文件，解释其中所有诊断。

    Args:
        path: .lean 文件路径。
        use_llm: 规则未命中时是否用 LLM 兜底。
        lang: 解释语言（en 默认 / zh 插件）。
        lean: lean 可执行文件路径（默认自动查找）。

    Returns:
        CheckResult：诊断 + 解释。
    """
    path = Path(path)
    exe = lean or find_lean()
    if exe is None:
        raise RuntimeError(
            "找不到 lean 可执行文件。请先安装 elan: "
            "curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y"
        )

    proc = subprocess.run(
        [exe, "--json", str(path)],
        capture_output=True,
        text=True,
        timeout=300,
    )

    result = CheckResult(path=str(path))
    # lean 的诊断输出到 stdout（--json 模式下）
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "data" not in raw:
            continue
        diag = parse_diagnostic(raw)
        result.diagnostics.append(diag)
        # 只解释错误和警告
        if diag.severity in ("error", "warning"):
            exp = explain(diag.data, use_llm=use_llm, lang=lang)
            result.explanations.append(exp)
    return result


def check_text(
    source: str,
    use_llm: bool = False,
    lang: str = "en",
    lean: str | None = None,
) -> CheckResult:
    """分析一段 Lean 源码文本（临时文件方式）。"""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False) as f:
        f.write(source)
        tmp_path = f.name
    try:
        return check_file(tmp_path, use_llm=use_llm, lang=lang, lean=lean)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
