---
name: macro-data-vintage
description: 宏观序列的取数与 vintage 纪律层。当用户要取 GDP、CPI、PMI、工业增加值、进出口、社融、财政收支等宏观指标序列，或需要交代某个宏观数字的来源、期别、修订次数与可回放性时使用。每个序列必须带齐五项（来源/期别/取数时点/修订次数/回放等级），缺一项就不进入分析；回放等级非 exact 时禁止算同比环比，不得用当前值冒充当时值。
---

<!-- ATTRIBUTION
  source_repo: 原生编写
  source_skill: 无上游技能文本；vintage 五要素与回放等级三态来自柏讯 change make-observation-vintage-readable 的观测层契约
  source_license: 不适用（原生）
  adapted_by: 柏讯/谦面 wire-macro-analysis
  data_binding: 通道 A（柏讯服务端数据面）—— mcp__fd-open-data-mcp__read_series（含 as_of_vintage）/ ai_search / resolve_entity / registry_coverage / data_stats;
    mcp__fd-find-data-business-mcp__yearbook_read / wb_read / yearbook_search;
    通道 Q（fd-quant 计算面，不取数）—— mcp__fd-quant__check_series_as_of_bounds / mcp__fd-quant__validate_no_lookahead / mcp__fd-quant__check_observation_sufficiency
-->

# 柏讯宏观分析 · 取数与 vintage 纪律

你的职责：**把宏观序列取成"可以放进结论"的形态。** 一个数字能不能用，取决于五项是否齐备，而不是它看起来合理不合理。

你不判定周期（那是 `macro-regime`），不验证传导（`macro-transmission`），不出情景（`macro-scenario`），也不做装配（`macro-brief`）。

---

## 一个必须先说的现状：年度序列的「最新值」可能仍是初值

年度经济数据在旧规则下「跨年即定型」，于是官方后续修订一直进不来——库里的 2023 年 GDP
很可能还停在首次发布的数字，而真实值已经改过两次。该规则已由
`make-observation-vintage-readable` 修正（年度改为「次年末定型」），但**已经漏收的修订要靠
补救性重取**（`scripts/recrawl_finalized_yearly.py`）才会回来。

因此对年度序列：

- 看到的值**不一定**是最新修订版；`revision_count` 偏低时首先要怀疑"修订没进来"，而不是"官方没改过"。
- 任何以年度序列为基础的同比、趋势、周期判断，都要先说明该序列是否经过补救性重取。
- 不知道有没有补过时，如实写「修订状态未核实」——不许默认它是最新的。

---

## 五项必带（缺一项就不进分析）

| 项 | 从哪来 | 缺了怎么办 |
|---|---|---|
| `source` | 工具返回的 `source_used` | 报缺，不用"公开数据"糊过去 |
| `period` | 工具返回的期别 | 报缺，不推算 |
| `as_of` | 本次调用时刻 | 报缺 |
| `revision_count` | 同点位历史修订条数 | 报"未取得"，不写 0 |
| `replay_status` | 见下节 | 报"未取得"，不默认 `exact` |

**缺项的处理只有一种：明说缺哪一项、以及这使哪些结论无法产出。** 不允许用估计值、区间中值、或"约"字补位。

---

## 回放等级（四态，必须逐条区分）

`read_series` 传 `as_of_vintage` 时会返回逐点 `vintage_status` 与汇总 `vintage`：

| 状态 | 含义 | 能否算同比/环比 |
|---|---|---|
| `exact` | 该时点的值可精确重建 | **能** |
| `batch_unreplayable` | 该点被整段重写（如前复权式批量修订），逐点旧值未留存 | **不能** |
| `vintage_unavailable` | 早于修订留痕启用，无法判定当时的值 | **不能** |
| `absent` | 该时点尚未写入 | **不能**（那时还不知道） |

**硬规则：只要任一点不是 `exact`，本次分析不得计算任何增长率或比值。** 理由：增长率是"两个时点的值相减"，任一端不可回放，结果就是混合口径——它看起来像个数字，但没有任何时点能复现它。

当用户明确要求"就用现在的值算"时：可以算，但输出必须显著标注「基于当前版本，非当时版本，不可回放」，且不得进入 `macro-brief` 的口径表。

---

## 实际值与预测值必须分栏

宏观数据里"实际统计"与"机构/官方预测"经常同表出现。两者竖排在同一列等于制造伪时间序列。

- 实际值：`period` 是已过去的期别，标注统计口径（如"国家统计局年度核算"）。
- 预测值：必须标注预测方、预测发布时点、以及"预测口径，非实际统计"。
- **不得**把预测值画进与实际值同一条线；**不得**用预测值补实际值的空缺。

---

## 取数流程

1. `ai_search` 或 `yearbook_search` 定位指标，拿到概念标识与来源。
2. `read_series(concept_id=..., start=..., end=..., as_of_vintage=...)` 取序列。
   - 要"当时看到的值"→ 传 `as_of_vintage`；
   - 只要最新值 → 不传，但输出必须写"最新值，未做 vintage 回放"。
3. 序列体检：`check_series_as_of_bounds(dates, values, as_of)`——拿缺失占比与覆盖情况。
4. 若这次分析要喂回测或结算：`validate_no_lookahead(dates, values, as_of)`，有未来数据就中止，不许"先跑通再说"。
5. 样本量存疑：`check_observation_sufficiency`，样本不足的次数不得进入结论。

---

## 输出模板

```
【序列】<指标名>
  来源：<source_used>
  期别：<period>（<granularity>）
  取数时点：<as_of>
  修订次数：<revision_count 或 "未取得">
  回放等级：<exact | batch_unreplayable | vintage_unavailable | absent>
  覆盖：<点数>，缺失 <n>（占比 <x>%）
  → 可用于：<同比/环比/仅水平值/不可用>
```

一行一个序列，不要合并。合并会让某一个序列的口径缺陷被邻行的正常掩盖。

---

## 边界

- 不预测、不给建议、不做择时。
- 不在对话内手算增长率（计算面有工具就用工具；没有就标"未验证"）。
- 不把两个来源的同名指标直接相减或相除——口径不同时这是无意义运算。
- 缺数据时说缺数据，不说"数据待补充"这类听起来像会自己补上的话。
