# LeanWeaver 报错语料库与方法论

> 规则引擎驱动的 Lean 4 报错解释器——用**官方验证过的真实报错**构建，
> 每个解释都可溯源、可复现、离线可用。

## 一句话

Lean 4 的报错对新手极不友好，而**官方扩展只显示原始报错，不做解释**。
LeanWeaver 把报错翻译成人话（含义 + 原因 + 修复），
且**语料全部来自 Lean 官方测试**。

---

## 一、数据来源（全部权威）

| 来源 | 规模 | 说明 |
|---|---|---|
| **lean4 官方测试** `tests/elab` + `tests/elab_fail` | **1074 个测试文件** → **691 条去重报错** | 官方验证过的"代码 → 确切报错"配对，是核心语料 |
| **Lean 源码** `src/Lean` 的 `throwError` | **427 条错误消息定义** | 官方写死的报错原文 |
| **GitHub issue**（leanprover/lean4 等） | 持续可收集 | 真实用户求助中的报错 |

**关键**：官方测试的 `#guard_msgs` 和 `.expected.out` 是 Lean 团队自己维护的
"这段代码应该产生这条确切报错"的断言——这是**最权威的报错语料**，
比任何手工收集都可靠。

## 二、采集管道（可复现）

### 1. 从官方测试构建语料
```bash
# 需要 lean4 仓库（git 可访问）
git clone --filter=blob:none --sparse https://github.com/leanprover/lean4.git
cd lean4 && git sparse-checkout set src/Lean tests

# 构建 691 条语料 + 识别率报告
python -m leanweaver.build_official_corpus --lean4 /path/to/lean4 --out data/official_corpus.json
```

### 2. 从 Lean 源码提取错误消息定义
```bash
python -m leanweaver.extract_official --src /path/to/lean4/src/Lean --out data/official_errors.json
```

### 3. 从 GitHub issue 收集用户真实报错
```bash
python -m leanweaver.collect_issues --owner leanprover --repo lean4 \
  --keywords "type mismatch,application type mismatch,unsolved goals" \
  --out data/issues_corpus.json
```

## 三、识别率（诚实报告）

### 关键区分：总识别率 vs 用户场景识别率
官方测试语料里混着**测试专用/元编程/内部错误**（如 `missing doc string` 30+条、
`fail tactic was invoked` 等），**真实写证明的用户永远遇不到**。
所以分开统计：

| 指标 | 数值 | 说明 |
|---|---|---|
| **总识别率** | **66.0%** | 对全部 691 条官方报错 |
| **用户场景识别率** | **78.4%** | 排除测试/元编程/内部错误后（552 条） |

> 用户场景 78.4% 意味着：**真实用户遇到的报错，近八成能被确定性识别并解释**。
> 剩余是低频长尾（每个 1-3 条），继续补边际收益极低。

## 四、方法论：数据驱动补规则循环

```
1. 跑 691 条官方语料 → 识别率
2. 聚类未识别报错 → 找高频缺口
3. 补规则 + 模板（含原因/修复）
4. 重跑 → 识别率变化
5. 复核：抽查分类是否合理（防止误配虚高）
```

**这条循环的价值**：
- 可复现（任何人 clone 就能跑）
- 数据说话（补什么规则由语料决定，不是猜）
- 诚实（复核能发现并修正虚高）

## 五、规则库设计

```
leanweaver/errors/
├── classify.py      # 分类：error code 优先 + 文本模式，29 类
├── templates.py     # 语言注册表 + 缺失回退
├── explain.py       # 入口（规则匹配）
└── locales/
    ├── en.py        # 英文模板（默认）
    └── zh.py        # 中文模板（插件）
```

**设计原则**：
- 机制与语言分离（加语言只需加 locale）
- error code 优先（`error(lean.xxx)` 比文本可靠）
- 版本可维护（报错随 Lean 版本变化，语料按版本记录）

## 六、已知边界（诚实）

1. **覆盖 78.4% 用户场景**，长尾未收录的仍显示"未能识别"（可提 issue 补）
2. **解释文本已固化进规则库，经人工复核**；
   建议未来为每条解释附加官方来源链接，供用户交叉验证
3. **Lean 版本演进会改报错文案**，规则库需随版本维护（语料带版本标记）

## 七、测试

```bash
pip install -e ".[dev]" && pytest   # 34 测试（含官方真实报错样本）
```

## 许可

MIT
