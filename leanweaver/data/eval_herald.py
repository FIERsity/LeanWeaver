"""用 Herald 数据集评估 LeanWeaver 翻译质量。

方法：从 Herald_proofs 抽 N 条样本，用我们的翻译器把 formal_proof 翻译成
自然语言，和 Herald 的标准答案（informal_proof / commented_proof）对比。

评估维度（自动 + 可人工抽查）：
1. 翻译成功率（LLM 是否产出非空结果）
2. 与 Herald 答案的相似度（ROUGH/字符重叠，仅供参考，数学翻译本质是开放式）
3. 输出可读性（长度、是否包含被翻译的 tactic 名）

用法：
    python -m leanweaver.data.eval_herald --parquet <path> --n 5 [--max-steps 3]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ..translate.llm import get_default_llm
from ..translate.parser import extract_proof


def count_tactics(fp: str) -> int:
    if not isinstance(fp, str):
        return 0
    m = re.search(r":=\s*by\s*(.*)", fp, re.S)
    if not m:
        return 0
    return len([l for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith("--")])


def simple_similarity(a: str, b: str) -> float:
    """极简相似度：字符 bigram 重叠（仅供参考）。"""
    if not a or not b:
        return 0.0
    def bigrams(s: str) -> set:
        s = s.lower()
        return {s[i:i+2] for i in range(len(s)-1)}
    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)


def main() -> int:
    parser = argparse.ArgumentParser(description="Herald 评估")
    parser.add_argument("--parquet", required=True, help="Herald_proofs parquet")
    parser.add_argument("--n", type=int, default=5, help="评估样本数")
    parser.add_argument("--max-steps", type=int, default=3, help="只评估 ≤N 步的证明")
    parser.add_argument("--lang", default="en", help="翻译目标语言（Herald 是英文）")
    parser.add_argument("--skip-llm", action="store_true", help="只跑数据检查，不调 LLM")
    args = parser.parse_args()

    import pyarrow.parquet as pq

    df = pq.read_table(args.parquet).to_pandas()
    df["tactic_count"] = df["formal_proof"].apply(count_tactics)
    cand = df[(df["tactic_count"] >= 1) & (df["tactic_count"] <= args.max_steps)]
    cand = cand[cand["informal_proof"].notna()]

    llm = None if args.skip_llm else get_default_llm()
    if not args.skip_llm and llm is None:
        print("未配置 LLM，跳过翻译", file=sys.stderr)
        return 1

    print(f"评估 {args.n} 条样本（≤{args.max_steps} 步，语言={args.lang}）\n")
    total_sim, count = 0.0, 0
    for _, row in cand.head(args.n).iterrows():
        formal = str(row["formal_proof"])
        informal = str(row["informal_proof"])
        # 用我们的 parser 提取
        block = extract_proof(formal, None)
        print(f"### {row['name']}")
        print(f"  步数: {row['tactic_count']}")

        if block is None:
            print("  ⚠️ parser 无法解析，跳过")
            print()
            continue

        print(f"  formal: {block.tactics}")
        if args.skip_llm:
            print(f"  Herald 标准答案: {informal[:150]}...")
        else:
            try:
                from ..translate.proof import translate_proof_block
                res = translate_proof_block(block, target_lang=args.lang, llm=llm)
                sim = simple_similarity(res.full_proof, informal)
                total_sim += sim
                count += 1
                print(f"  相似度(参考): {sim:.2f}")
                print(f"  LeanWeaver: {res.full_proof[:200]}...")
            except Exception as e:
                print(f"  ❌ 翻译失败: {e}")
        print()
    if count:
        print(f"平均相似度: {total_sim/count:.2f}（数学翻译为开放式，相似度仅供参考）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
