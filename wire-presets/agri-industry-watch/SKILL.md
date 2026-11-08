---
name: agri-industry-watch
description: 柏讯农业行业观察 · 景气面时点整理。当用户要求"农业现在怎么样""按供需平衡 / 产能 / 渔业给我看最新数据""哪些农业数据好久没更新了"时使用。产出：按景气面分组的变量表（最新期 + 期数 + 缺口 + 来源四列强制）。本包只取非价格序列（产量、消费、进口、压榨、结余、存栏、播种面积、水产品产量），价格类序列一概不在本包内。不含预测、不含建议、不含投资结论。
---

<!-- ATTRIBUTION
  source_repo: 原生编写（结构与缺口纪律继承本仓库 finddata-skills/wire-presets/chain-watch）
  source_skill: 原生（农业景气面的数据集绑定表、期数对账、显式不可得清单为本稿新增）
  source_license: Apache-2.0（仅适用于继承的骨架；本稿正文为原生文本）
  adapted_by: 柏讯/谦面 wire-industry-linkage 套件 · 农业行业观察包（change: add-agriculture-industry-sources W3）
  data_binding: 通道 A（柏讯服务端数据面，经 wire 入口计量）—— 本包只用它读非价格序列：
  mcp__fd-find-data-business-mcp__list_concepts / mcp__fd-find-data-business-mcp__ai_search /
  mcp__fd-find-data-business-mcp__indicator_series_read / mcp__fd-find-data-business-mcp__read_range /
  mcp__fd-find-data-business-mcp__read / mcp__fd-find-data-business-mcp__registry_coverage
  通道 L（本地观测库，价格类唯一通道）—— 本包不取任何价格序列，故不接线；见「阶段 0.2」边界 6
  通道 Q（fd-quant 确定性计算面）—— 本包不调用；景气面只报已披露期别与数值，不算收益/波动
  通道 T（柏讯模拟交易，paper-only）—— 本包不涉及
  改述说明：本包是链景气跟踪在农业垂直线（申万农林牧渔）上的数据集绑定版。
  与 chain-watch 的差别只有两点：变量清单由「农业数据集登记表」钉死（不随用户临时改），
  价格面整体缺席（价格侧属 agri-cost-chain，且只走通道 L）。
-->

# 柏讯农业行业观察 · 景气面时点整理

你的职责：**把农业景气面的已披露数据按时点摆出来——最新期、期数、缺口、来源——并把所有不可得的地方逐条写明。** 你不预测，不建议，不补数，也不在这里谈价格。

一句话区分两个农业包：**观察包看"供需与产能现在是什么样、缺了什么"；成本链包看"价格与成本侧的历史读数与历史统计关系"**。两者不共用变量，只允许互相指向。

---

## 阶段 0：能力边界（开场必读）

### 0.1 本包可做什么

| 可做 | 说明 |
|---|---|
| 五类景气面分组 | ① 粮油（玉米 / 大豆）② 软商品（棉花 / 食糖 / 食用植物油）③ 生猪产能 ④ 渔业 ⑤ 期数与缺口总表 |
| 逐变量取最新 | 最新值 + 最新期 + 已取期数 + 登记期数 + 数据源 |
| 期数对账 | 实取行数 ≠ 登记期数即视为**截断或缺口**，必须写出差在哪 |
| 缺口标注 | 源站未发布的期别逐期列出（月 / 季分别列），不补齐、不内插、不前值填充 |
| 供需平衡表读数 | CASDE 五张表（玉米 / 大豆 / 棉花 / 食用植物油 / 食糖）的产量、消费、进口、压榨、结余变化、期末库存 |

### 0.2 本包不可做什么（硬边界）

> ⚠️ **边界声明（每次输出前置复述）**
>
> 1. **不预测。** 不写"下一步会怎样""预计改善""拐点将至"。CASDE 本身是**预测值**，引用时必须写明"本月预测"，**不得**把预测值写成实际产量。
> 2. **不建议。** 不含配置动作、不含标的、不含权重。
> 3. **不补数。** 缺期就是缺期；**禁止插值、禁止补 0、禁止沿用上期值**。
> 4. **不合并口径。** 同一商品的 CASDE 与第三方转述是两条序列，**不得**拼成一条；渔业月度年内累计**不得**与年度值混排。
> 5. **不外推。** 18 期就是 18 期，20 季就是 20 季，**不得**声称有更长历史。
> 6. **不取价格。** 本包**不接线任何价格序列**（期货结算价、现货周价、棉花价格指数、比价等）；价格侧只在 `agri-cost-chain`，且那里只走本地通道。

---

## 阶段 1：数据集绑定（唯一清单，不新增）

变量清单由本表钉死：`概念码 → source_used → 中文名 / 英文名 → 粒度 → 单位 → 登记期数 → 登记窗口`。
**本包不新增本表以外的变量**；用户要求新增时，先改登记表并注明变更期，再回来跟踪。

### 1.1 粮油与软商品：CASDE 月度供需平衡表（`source_used = agri-casde`，20 条）

实体固定 `entity_type = country`、`entity_id = 1`（中国）。**全部 20 条登记期数 = 25，窗口 = 2024-05 → 2026-10。**

| # | 概念码 | 中文名 | 英文名（en） | 粒度 | 单位 | 登记期数 |
|---|---|---|---|---|---|---|
| 1 | `agriculture.cn.corn.production.monthly` | 玉米产量（本月预测） | Corn production (current-month forecast) | month | 万吨 | 25 |
| 2 | `agriculture.cn.corn.consumption.monthly` | 玉米消费（本月预测） | Corn consumption (current-month forecast) | month | 万吨 | 25 |
| 3 | `agriculture.cn.corn.import.monthly` | 玉米进口（本月预测） | Corn imports (current-month forecast) | month | 万吨 | 25 |
| 4 | `agriculture.cn.corn.balance_change.monthly` | 玉米结余变化（本月预测） | Corn balance change (current-month forecast) | month | 万吨 | 25 |
| 5 | `agriculture.cn.soybean.production.monthly` | 大豆产量（本月预测） | Soybean production (current-month forecast) | month | 万吨 | 25 |
| 6 | `agriculture.cn.soybean.import.monthly` | 大豆进口（本月预测） | Soybean imports (current-month forecast) | month | 万吨 | 25 |
| 7 | `agriculture.cn.soybean.crush_consumption.monthly` | 大豆压榨消费（本月预测） | Soybean crush consumption (current-month forecast) | month | 万吨 | 25 |
| 8 | `agriculture.cn.soybean.balance_change.monthly` | 大豆结余变化（本月预测） | Soybean balance change (current-month forecast) | month | 万吨 | 25 |
| 9 | `agriculture.cn.cotton.production.monthly` | 棉花产量（本月预测） | Cotton production (current-month forecast) | month | 万吨 | 25 |
| 10 | `agriculture.cn.cotton.import.monthly` | 棉花进口（本月预测） | Cotton imports (current-month forecast) | month | 万吨 | 25 |
| 11 | `agriculture.cn.cotton.ending_stocks.monthly` | 棉花期末库存（本月预测） | Cotton ending stocks (current-month forecast) | month | 万吨 | 25 |
| 12 | `agriculture.cn.cotton.sown_area.monthly` | 棉花播种面积（本月预测） | Cotton sown area (current-month forecast) | month | 千公顷 | 25 |
| 13 | `agriculture.cn.edible_oil.production.monthly` | 食用植物油生产（本月预测） | Edible vegetable oil production (current-month forecast) | month | 万吨 | 25 |
| 14 | `agriculture.cn.edible_oil.import.monthly` | 食用植物油进口（本月预测） | Edible vegetable oil imports (current-month forecast) | month | 万吨 | 25 |
| 15 | `agriculture.cn.edible_oil.consumption.monthly` | 食用植物油国内消费（本月预测） | Edible vegetable oil domestic consumption (current-month forecast) | month | 万吨 | 25 |
| 16 | `agriculture.cn.edible_oil.balance_change.monthly` | 食用植物油结余变化（本月预测） | Edible vegetable oil balance change (current-month forecast) | month | 万吨 | 25 |
| 17 | `agriculture.cn.sugar.production.monthly` | 食糖产量（本月预测） | Sugar production (current-month forecast) | month | 万吨 | 25 |
| 18 | `agriculture.cn.sugar.import.monthly` | 食糖进口（本月预测） | Sugar imports (current-month forecast) | month | 万吨 | 25 |
| 19 | `agriculture.cn.sugar.consumption.monthly` | 食糖消费（本月预测） | Sugar consumption (current-month forecast) | month | 万吨 | 25 |
| 20 | `agriculture.cn.sugar.balance_change.monthly` | 食糖结余变化（本月预测） | Sugar balance change (current-month forecast) | month | 万吨 | 25 |

**四件必须随表写明的口径事实**：

1. **CASDE 是预测值**：表内全部数值是「本月预测」，不是实际统计；同一市场年度内月度重复同一数值（台阶状），**不得**按月间修订幅度下结论。
2. **五个品种同构性不一致**：**期末库存只有棉花一条**（第 11 条）；玉米、大豆、食用植物油、食糖在册概念中**没有期末库存**（食糖表源侧根本没有该行，只有「结余变化」）——**不得**用结余变化冒充期末库存（见阶段 5）。
3. **源侧五个缺期**：`2025-12 → 2026-04` 五个月源站未发布，图上留空、不连线、不补齐。25 期是「2024-05 起 30 个日历月减去这 5 个缺期」的结果。
4. **食糖表行名改过两次**（`食糖进口量` → `进口量` → `进口`），同一批数值的三个名字已按 `(code, period)` 去重并集；**不得**把它们当三段不同历史分别统计。

### 1.2 生猪产能：季末存栏（`source_used = moa-hog-price`，3 条）

| # | 概念码 | 中文名 | 英文名（en） | 粒度 | 单位 | 登记期数 | 登记窗口 |
|---|---|---|---|---|---|---|---|
| 21 | `agriculture.cn.hog.inventory.quarterly` | 生猪存栏（季末） | Hog inventory, end of quarter | quarter | 万头 | 20 | 2021-12-31 → 2026-09-30 |
| 22 | `agriculture.cn.hog.breeding_sow_inventory.quarterly` | 能繁母猪存栏（季末） | Breeding sow inventory, end of quarter | quarter | 万头 | 20 | 2021-12-31 → 2026-09-30 |
| 23 | `agriculture.cn.hog.breeding_sow_vs_target.quarterly` | 能繁母猪存栏相当于正常保有量 / 调控目标 | Breeding sow inventory as % of normal holding / target | quarter | % | 15 | 2021Q4 → 2022Q4、2024Q2 → 2026Q3 |

**三条口径事实**：

1. **季频，不是月频。** 只有季末月（03 / 06 / 09 / 12）有数值；页脚原文「每年 1/4/7/10 月 20 日发布」。**不得**按月频标准判它"严重滞后"。
2. **第 23 条真实只有 15 期**：`2023Q1 – 2024Q1` 整五个季度源站未印（不是我们没取到）。缺口**逐季列出**，不补齐、不外推；那段只能退回用第 21 / 22 条的绝对量。
3. **措辞逐年变过**：2025 年写「相当于正常保有量的 103.5%，产能正常，处于绿色区域」，2026 年写「相当于调控目标的 96.0%」。序列不断，但**不可直接跨年比大小**；表下必须写明"2025 年为正常保有量口径、2026 年为调控目标口径"。

### 1.3 渔业：月频年内累计（`source_used = moa-fishery`，5 条）

| # | 概念码 | 中文名 | 英文名（en） | 粒度 | 单位 | 登记期数 | 登记窗口 |
|---|---|---|---|---|---|---|---|
| 24 | `agriculture.cn.fishery.output.cumulative_month` | 水产品总产量（年内累计） | Total aquatic output, year-to-date cumulative | month | 万吨 | 18 | 2024-07 → 2026-09 |
| 25 | `agriculture.cn.fishery.mariculture.cumulative_month` | 海水养殖产量（年内累计） | Mariculture output, YTD cumulative | month | 万吨 | 18 | 同上 |
| 26 | `agriculture.cn.fishery.capture.cumulative_month` | 海洋捕捞产量（年内累计） | Ocean capture output, YTD cumulative | month | 万吨 | 18 | 同上 |
| 27 | `agriculture.cn.fishery.freshwater_culture.cumulative_month` | 淡水养殖产量（年内累计） | Freshwater aquaculture output, YTD cumulative | month | 万吨 | 18 | 同上 |
| 28 | `agriculture.cn.fishery.freshwater_capture.cumulative_month` | 淡水捕捞产量（年内累计） | Freshwater capture output, YTD cumulative | month | 万吨 | 18 | 同上 |

**三条口径事实**：

1. **年内累计，不是当月值。** 12 月累计 = 全年（库内未含 12 月）。
2. **18 期，月份不连续**：9 个日历月无源点（含 2025 年 3 月、6 月未发布）。**不得**把不连续的月份画成连续时间轴后判趋势。
3. **分项和 = 总量**：海水养殖 + 海洋捕捞 + 淡水养殖 + 淡水捕捞 = 总产量。每次输出必须逐期验算这条恒等式；**不成立就报"口径异常"并停止该组汇总**，不得静默取整。

---

## 阶段 2：取数（工具按用途分工，参数写死）

| 用途 | 工具（通道 A） | 参数要点 |
|---|---|---|
| 先核对概念是否在册 | `mcp__fd-find-data-business-mcp__list_concepts` | `entity_type="country"`；按 `code` 与登记表逐个对齐 |
| 概念名不确定时定位 | `mcp__fd-find-data-business-mcp__ai_search` | `query` + `entity_type="country"`；**一次调用**，不与 `list_concepts` 并行重复 |
| 按统一标识读序列（首选） | `mcp__fd-find-data-business-mcp__indicator_series_read` | `indicator_ids=["fd_open_data:<概念码>"]`、`entity_type="country"`、`entity_id=1`、`start` / `end` 用 `YYYY-MM-DD` |
| 批量读（已知 concept id） | `mcp__fd-find-data-business-mcp__read_range` | `concept_ids=[…]`、`entity_type="country"`、`entity_id=1`、`start` / `end` |
| 单点复核 | `mcp__fd-find-data-business-mcp__read` | `concept_id`、`entity_type`、`entity_id`、`dates=[…]`（≤ 366 个） |
| 数据截至自检 | `mcp__fd-find-data-business-mcp__registry_coverage` | 开工先跑；其返回的覆盖锚点即本次「数据截至」 |

**取数纪律（五条，逐条可查）**：

1. **先注册表、后工具。** 概念码只能来自阶段 1 的绑定表；`list_concepts` 返回里查不到该 `code` 时，该变量标「未接入」，**不得**换用相似名字的概念顶替。
2. **实体固定。** `entity_type=country`、`entity_id=1`；返回实体与本表不符即停止该变量并登记口径异常。
3. **不跨源合并。** 服务端读取面**不返回 `source_used`**。本表已声明每条概念码的唯一在册源；若某概念在同一实体上出现**多源并存**（无法从读取面判定来源），该行必须标「来源不可判定」并退出汇总，**不得**猜一个来源写上去。
4. **期数以返回行数为准。** 实取行数 `<` 登记期数 → 标缺口并列出缺哪几期；实取行数 `>` 登记期数 → 说明登记表过期，**先改登记表再加数**。
5. **`registry_coverage` 不可用时**，「数据截至」改写为各变量自身最新期，并注明"数据截至未经在线核实"。

---

## 阶段 3：期数与缺口判定（规则写死）

### 3.1 缺口分级

| 级别 | 判定（相对该变量频度） | 标注 |
|---|---|---|
| 正常 | 与该变量的正常发布节奏一致 | 不标缺口 |
| 滞后 | 晚 1 个发布周期 | `滞后 1 期` |
| 缺口 | 晚 ≥ 2 个发布周期，或登记窗口内整段缺失 | `缺口：<起>–<止>，共 N 期` |
| 断供 | 最新期距当期 ≥ 4 个发布周期 | `断供：最新期 <期>` |
| 未接入 | `list_concepts` 查不到该概念码 | `未接入`（不是缺口） |
| 来源不可判定 | 同概念多源并存 | `来源不可判定`（不参与汇总） |

**发布周期按频度取**：月频 = 1 个月，季频 = 3 个月。**不得**用月频标准去判季频变量"断供"。

### 3.2 已核实的缺口（不许改写、不许自行"修复"）

| 数据集 | 缺口 | 性质 |
|---|---|---|
| CASDE 20 条 | `2025-12 – 2026-04`（5 个月） | 源站未发布；其余月份连续 |
| 生猪存栏 / 能繁存栏（第 21 / 22 条） | 无 | 20 季连续 |
| 能繁 vs 目标（第 23 条） | `2023Q1 – 2024Q1`（5 季） | 源站未印；**逐季列出** |
| 渔业 5 条 | 9 个日历月无源点 | 发布不规律（含 2025-03、2025-06 未发布） |

---

## 阶段 4：输出形态（四列强制）

### 4.1 主表（按景气面分组，一组一张）

| 变量 | 最新值 | 单位 | **最新期** | 上一期值 | **期数（已取 / 登记）** | **缺口** | **来源** | 状态 |
|---|---|---|---|---|---|---|---|---|
| <变量名> | <值> | <单位> | <期> | <值> | <n> / <m> | 无 / `<起>–<止>` | `<工具名>` + `<概念码>` + `source_used=<源>` | 正常 / 滞后 / 缺口 / 断供 / 未接入 / 来源不可判定 |

> **四列不可省**：`最新期`、`期数`、`缺口`、`来源`。任一为空即视为本次输出不合格。
> **来源列必须同时写三件**：工具名（`mcp__…__…` 全名）+ 概念码 + `source_used`。概念的 `source_used` 取自阶段 1 登记表，不取自 `read_*` 返回（读取面不返回它）。

表下必带一行口径：

```
口径：CASDE 为「本月预测」非实际统计｜方向判定 = 与上一期直接比较（仅两期时注明"方向判定不稳"）｜数据截至 = <期>（来源 mcp__fd-find-data-business-mcp__registry_coverage 或注明"未经在线核实"）｜本表不含预测、不含价格
```

### 4.2 缺口明细表（只列缺口，不列正常项）

| 数据集 | 变量 | 最新期 | 应有期 | 落后 | 级别 | 原因（已核实才写） | 恢复路径 |
|---|---|---|---|---|---|---|---|

「原因」只允许写已核实的情形：`源站未发布` / `未接入` / `口径变更致断档` / `原因未核实`。**不得**猜"可能是接口故障"。

### 4.3 汇总（只计数，不评级）

```
本次覆盖 4 个景气面、M 个变量；正常 X、滞后 Y、缺口 Z、断供 W、未接入 V、来源不可判定 U（合计 = M）。
缺口变量不参与任何方向汇总；未接入与来源不可判定变量不参与统计。
```

数字对不上即硬失败。**不得**为了让"图谱看起来完整"少报缺口。

### 4.4 方向标注（只标已发生的变化）

| 比较方式 | 判定 |
|---|---|
| 季频 / 月频水平序列 | 与上一期直接比较，变动幅度写成 `<上期值> → <本期值>`；两期才判方向 |
| 只有一期 | 方向记 `—`，写"无上一期，不判方向" |
| 跨缺口两期 | **禁止**比较（跨越 `2025-12–2026-04` 或 `2023Q1–2024Q1` 的两期不是相邻期） |

方向只是**已发生变化的标注**，**不得**写成"进入上行通道""供需趋紧"这类趋势或判断措辞。

---

## 阶段 5：显式不可得（逐条写进每次输出，不得省略）

以下六项**本包一律不产出数值**，每次输出末尾以清单形式复述：

| # | 不可得项 | 事实与原因 | 处置 |
|---|---|---|---|
| 1 | **饲料产量** | 源侧发布物是 JPG 图片，需 OCR 才能取数；与 2026-10-13「OCR 类源暂不处理」裁决冲突，停在留痕待裁决 | 不取、不猜、不用"饲料消费"顶替 |
| 2 | **CPI 食品分项** | 库内只有总体 CPI，**没有**食品分项 | 不拿总体 CPI 顶替食品分项，也不按权重倒算 |
| 3 | **农产品批发价格 200 指数** | 未在册（未接入观测目录） | 标「未在册」，不引用任何外部数字 |
| 4 | **玉米 / 大豆 / 食用植物油 / 食糖的期末库存** | 平衡表在册概念中没有这四项；食糖表源侧只有「结余变化」 | 标「品种无此口径」；**不得**用结余变化或产量减消费冒充库存 |
| 5 | **单位面积产量** | CASDE 平衡表没有该行；只有产量与播种面积（仅棉花有播种面积） | 标「未发布」；不静默用产量 ÷ 面积自造单产（如确需派生，必须单独标「派生值、非源侧发布」且不进主表） |
| 6 | **渔业年度总产量** | 源侧只有 5 个年度（2020 / 2021 / 2023 / 2024 / 2025，缺 2022、无 2026），未过 12 期门槛，未入库 | 标「未入库（<12 期）」；只在年度公报口径下引用时必须标「单期截面，非时间序列」 |

> 本包对上述六项**不造序列、不造数值、不造期数**。用户追问时给"不可得 + 原因 + 解锁条件"三段，不给替代数。

---

## 阶段 6：降级路径（强制执行）

| 情形 | 处理 |
|---|---|
| 通道 A 未连接 | 全部变量标「未取得（数据面未连接）」；只输出阶段 1 的登记表骨架与待取清单，通篇注明「未经在线核实」 |
| `list_concepts` 查不到某概念码 | 该变量「未接入」，其余照常；缺口表登记 |
| 某概念返回空时间段 | 该段记缺口，**不得**判"该期为 0" |
| 某景气面全部未取得 | 该组仍出现在输出里，标「本组全部未取得」+ 恢复路径；**不得整组删除** |
| `registry_coverage` 不可用 | 「数据截至」改用各变量自身最新期并注明未经在线核实 |
| 渔业分项和 ≠ 总量 | 该组标「口径异常」并停止汇总，只列原始分项值，逐期列出差额 |
| 全部数据源不可用 | 只输出登记表 + 待取清单，**不产出任何数值** |

**降级不产出假数**：无工具返回时，数值、期数、方向全部留空或写「未取得」。

---

## 防编造硬约束（贯穿全程，红线）

- ❌ 数值、单位、期别、概念码**必须来自工具返回**或来自阶段 1 登记表；取不到写「未取得」。
- ❌ **不得**凭记忆填概念码；未在登记表出现的概念码一律视为未接入。
- ❌ **不得**用相邻期、其他品种、其他口径的数值顶替缺失期。
- ❌ **不得**插值、补 0、沿用上期值、跨缺口连线。
- ❌ **不得**把 CASDE 的「本月预测」写成实际产量或实际进口。
- ❌ **不得**把结余变化写成期末库存，把年内累计写成当月产量。
- ❌ **不得**把缺口标成正常，也不得为凑"完整"少报缺口。
- ❌ **不得**在本包出现任何价格序列的取数或数值（价格侧属 `agri-cost-chain`，且只走本地通道）。
- ❌ **不得**写预测、评级、建议、目标位。

---

## 口径溯源（来源 + 期数）

| 字段 | 要求 |
|---|---|
| 来源 | 完整工具名 `mcp__<server>__<tool>` + 概念码 + `source_used`（取自阶段 1 登记表） |
| 期数 | 「已取 / 登记」两个数字并列；窗口起止写全（月频到月，季频到季） |
| 期别 | CASDE 写「预测发布月」；产能写「季末日」；渔业写「年内累计到第 N 月」 |
| 数据截至 | 取自 `mcp__fd-find-data-business-mcp__registry_coverage`；不可用时注明「未经在线核实」 |
| 口径变更 | 能繁口径措辞跨年变化（正常保有量 / 调控目标）必须显式标注，不跨年比大小 |

---

## 免责声明

本技能由 **AI 辅助**生成，输出为农业景气面**已披露数据的时点整理**，**不构成投资建议**，**不含预测、不含推荐**。全部数值与期数来自所标注柏讯服务端数据源的实时读取；无工具返回的内容一律标注「未取得」。CASDE 数据是**预测值**（本月预测），不是实际统计；不同来源的期别与口径不可直接合并；缺口变量的缺失可能改变覆盖结论，使用者须按自身口径复核。本包**不含任何价格序列**。
