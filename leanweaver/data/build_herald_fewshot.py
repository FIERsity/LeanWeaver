"""从 Herald_proofs 数据集构建 few-shot 示例库。

Herald（ICLR 2025）提供 44,553 条「形式化证明 ↔ 自然语言证明 ↔ 逐行注释证明」配对。
这里挑选一小批高质量、有代表性的样本，转成轻量 JSON，
供 LeanWeaver 翻译器作为 few-shot 示例注入 prompt。

用法：
    python -m leanweaver.data.build_herald_fewshot \
        data/herald/data/train-00000-of-00001.parquet \
        leanweaver/data/herald_fewshot.json

策略：
- 按 tactic 步数分层（1/2/3-5 步各挑一些）
- 优先选 commented_proof 完整、informal_proof 清楚的
- 领域多样化
- 每条约 200-400 token，总量控制在 few-shot 预算内（10 条左右）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def count_tactics(fp: str) -> int:
    if not isinstance(fp, str):
        return 0
    m = re.search(r":=\s*by\s*(.*)", fp, re.S)
    if not m:
        return 0
    return len(
        [
            l
            for l in m.group(1).splitlines()
            if l.strip() and not l.strip().startswith("--")
        ]
    )


def pick_samples(df, n_per_bucket: int = 3) -> list[dict]:
    """按复杂度分层采样。"""
    buckets = [(1, 1), (2, 2), (3, 5), (6, 12)]
    picked: list[dict] = []
    seen_names: set[str] = set()

    for lo, hi in buckets:
        cand = df[
            (df["tactic_count"] >= lo)
            & (df["tactic_count"] <= hi)
            & (df["commented_proof"].notna())
        ]
        count = 0
        for _, row in cand.iterrows():
            if count >= n_per_bucket:
                break
            name = str(row["name"])
            if name in seen_names:
                continue
            seen_names.add(name)
            picked.append(
                {
                    "name": name,
                    "formal_theorem": str(row["formal_theorem"]),
                    "formal_proof": str(row["formal_proof"]),
                    "informal_proof": str(row["informal_proof"]),
                    "commented_proof": str(row["commented_proof"]),
                }
            )
            count += 1
    return picked


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 Herald few-shot 示例库")
    parser.add_argument("parquet", help="Herald_proofs parquet 路径")
    parser.add_argument("output", help="输出 JSON 路径")
    parser.add_argument("--per-bucket", type=int, default=3, help="每层采样数")
    args = parser.parse_args()

    import pyarrow.parquet as pq

    df = pq.read_table(args.parquet).to_pandas()
    df["tactic_count"] = df["formal_proof"].apply(count_tactics)

    samples = pick_samples(df, n_per_bucket=args.per_bucket)
    out = {"source": "Herald (ICLR 2025)", "count": len(samples), "samples": samples}
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {len(samples)} 条 few-shot 样本 → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
