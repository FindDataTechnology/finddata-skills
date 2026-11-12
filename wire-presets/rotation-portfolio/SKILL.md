---
name: rotation-portfolio
description: 柏讯自适应轮动 · 风险预算建仓与风控参数。当用户要求"按排序结果给个仓位方案""组之间怎么分配""止损怎么设"时使用。产出：TargetWeights 契约实例（组权重 → 资产权重）+ 风险预算依据 + 风控参数（并写明：契约本身没有止损字段；轮动是权重轨，run 级 risk 覆盖对权重轨会被显式拒绝，止损必须写进 weights_series）。
---

<!-- ATTRIBUTION
  source_repo: https://github.com/AI4Finance-Foundation/FinRL-X
  source_skill: src/strategies/adaptive_rotation/portfolio_builder.py + risk_manager.py
  source_license: Apache-2.0
  adapted_by: 柏讯/谦面 wire-adaptive-rotation 套件
  data_binding: 通道 Q（fd-quant 确定性计算面，不取数）——
  mcp__fd-quant__summarize_concentration（集中度 HHI / 前 N 权重占比）;
  mcp__fd-quant__summarize_turnover（换手率：两期权重序列）;
  mcp__fd-quant__summarize_volatility / summarize_drawdown（组合层波动与回撤）;
  mcp__fd-quant__check_observation_sufficiency（样本前置）
  通道 T（柏讯模拟交易，paper-only，mesh 直连）—— 权重 spec 的落地与运行：
  mcp__fd-paper-trading__create_strategy / update_strategy / get_strategy（weight 模式 spec）;
  mcp__fd-paper-trading__search_instruments / get_bars（标的可用性）;
  mcp__fd-paper-trading__run_backtest / list_strategy_runs（回测）
  改述说明：风险预算与例外框架借鉴 FinRL-X（Apache-2.0）。**关键差异**不在"能不能自动止损"，
  而在**止损不在契约里**：FinRL-X 的止损写在策略内部；柏讯的 `TargetWeights` 契约只承载权重
  （`constraints` 只有单票与板块两个上限），权重模式只消费 weights_series。要让它真正被执行，
  须给 run 带 `risk` 覆盖（`stop_loss_pct`/`trailing_stop_pct`/`cooldown_bars`）——由平台逐 bar
  （跳空保守成交）/逐 tick 执行，并在快照里以 `effective_weights` 与 `target_weights` 并列归因；
  **不配覆盖则不存在隐式止损**，须在权重序列内表达或由人执行。本稿不得暗示"不配也会有人替你
  止损"，也不得反过来说"引擎永远不执行止损"（2026-11-06 `stop-order-execution` 之后已不成立）。
  上游业绩数字不引用。
-->

# 柏讯自适应轮动 · 风险预算建仓与风控

你的职责：**把排序结果变成一份可执行的 `TargetWeights` 契约实例与一份 weight 模式策略 spec**，并把风控参数与它们的归属讲清楚。你不选组也不选股——那是 `rotation-ranking` 的事。

**防编造硬约束**：权重向量里的每个数字必须由本稿的分配规则从**已取得的 IR 与稳健 Z**算出，并给出计算链。取不到的组/标的一律不给权重，写"未取得（原因 + 可取路径）"。**禁止编造权重、禁止凭记忆填标的、禁止把上一轮的权重直接复用**。契约校验被拒时原样转述拒绝原因，**不得偷偷归一化后重试**。

---

## 阶段 0：契约语义（先讲清，避免用户误解）

`TargetWeights` 契约的三条硬约束（由 `strategy-weight-mode` 实现，本稿如实转述）：

1. **权重非负**：负权重（做空）会被契约**拒绝**，不是被裁剪。
2. **权重和 ≤ 1**（容差 1e-9）：和小于 1 的余量自动留现金；和大于 1 会被**原样拒绝**，不会被归一化。
3. **symbol ⊆ universe**：权重里出现 universe 之外的标的会被拒。

因此：**现金下限是通过"权重和 < 1"表达的**，不是另设字段。regime 为 neutral 时现金下限 20% ⇒ 权重和 ≤ 0.80。

**止损与冷却（口径最后更新 2026-11-12）**：账户层现在有 STOP/STOP_LIMIT
订单型，run 级有风控覆盖（`risk` 配置：`stop_loss_pct`/`trailing_stop_pct`/`cooldown_bars`）。
**但覆盖只对单标的轨生效**——轮动是权重（多标的）轨，传到权重轨会被**显式拒绝**
（`risk_not_supported_on_weight_track`）。所以轮动的止损表达只有一条主路：

1. **写进权重序列（轮动的唯一自动路径）**：在每个调仓点先判断触发条件，触发则该标的
   目标权重写 0——**把止损表达为权重**，由权重引擎照常执行（回测与 live 都成立）。
   这是轮动唯一"到点自动执行"的形态。
2. **不要给轮动 run 带 `risk`**：单标的轨才有 overlay；权重轨的回测与 live 都**没有**
   overlay 通道（回测 `replay_weights` 无该形参、live 只消费一个永不 arm 的冷却），
   所以带上去会被 400 拒绝。拒绝是刻意的：收下再忽略等于给出"带了止损"的记录而实际
   零保护。
3. **单标的策略则可以直接用**：`run_backtest(risk=...)` 与 `start_strategy(risk=...)`
   都已透传且生效（回测逐 bar、live 每根新 bar 复查，触发即平仓；快照留 `risk_triggers`）。

向用户询问"止损会自动执行吗"时的准确答案：**契约里没有止损字段；单标的轨配了 `risk` 覆盖
才由平台执行；权重（轮动）轨没有覆盖通道，止损必须写进 `weights_series`**。

---

## 判定前提（可核）

> 与 `basis` **并存，互不替代**：`basis` 是给人读的理由，本节是给机器核的条件。
> 把条件只写进 `basis` 等于放弃监控——「前提失效」将无法被发现。
> 形状说明：`Decision v2` 落地后，本节表格直接搬进契约的 `preconditions` 字段，正文形状不变。

| # | 前提 | 指标引用 | 比较 | 阈值 | 口径日 |
|---|---|---|---|---|---|
| 1 | 组权重和 = 1 | `weights.group_sum` | `eq` | 1 | <as_of> |
| 2 | 单组权重不越风险预算上限 | `weights.max_group` | `lte` | <预算上限> | <as_of> |
| 3 | 排序打分为当期值（非前一期沿用） | `ranking.as_of` | `eq` | <本期> | <as_of> |

三条硬纪律：

1. **每行五字段齐全**；任一行缺字段即视为该前提不可核，须在表下点名。
2. **`metric_ref` 必须可解析**（柏讯概念标识 / 计算面工具参数 / 本地数据集字段）。解析不了就写「不可核（指标未接入）」并给补证路径，不得留空。
3. **凑不出前提时不许编**：写「本判定无结构化前提」并说明原因。一条永远成立的前提比没有前提更糟。

自查：方案发布前逐行核对上表；发布后若某前提已不成立，必须在正文显著位置说明。

---

## 阶段 1：组权重（风险预算）

**输入**：`rotation-regime` 的 regime 判定（决定名额与现金下限）+ `rotation-ranking` 的组 IR 排序。

**分配规则**：

1. 按 IR 从高到低给入选组分配预算，**IR 越高预算越大**，但单组上限默认 **40%**（防单一行业押注）。
2. 预算按 IR 的**正部**归一化后乘以「1 − 现金下限」。
3. **组数受 regime 名额约束**（risk_on ≤4、neutral ≤2、risk_off ≤1 或全现金），超出名额的组不分配预算。
4. 分配完成后过 `mcp__fd-quant__summarize_concentration` 检查集中度：若 HHI 超过阈值（默认 0.35），**下调最大组预算并重算**，并在输出中记录这次调整。

**输出组预算表**：

```
组 | IR | 预算占比 | 调整前 | 调整原因
合计 = 1 − 现金下限
```

---

## 阶段 2：资产权重（组内分配）

在每个组内部，按 `rotation-ranking` 给出的组内排序与稳健 Z 分配该组的预算：

1. 组内默认**等权**（简单、可解释）；用户要求按信号强度加权时，用稳健 Z 的正部归一化。
2. 单只上限默认 **15%**（防单票风险），超限的部分**回流到同组其余标的**；同组标的不足时回流到现金并在输出注明。
3. 四舍五入到 **6 位小数**，取整残差归入现金（**不得强行凑到 1.0**——残差留现金是正常且诚实的形态）。

**输出资产权重表**：

```
标的 | 组 | 组内排名 | 稳健Z | 权重 | 上限检查 | 取整残差
合计权重 = X（现金 = 1 − X）
数据期数：排序输入来源（组 IR 与个股稳健 Z 的计算窗口）+ 起止日 + 有效点数
```

---

## 阶段 3：产出 `TargetWeights` 契约实例

按 `strategy-weight-mode` 的 `weight` kind 组装 spec：

```json
{
  "kind": "weight",
  "universe": ["<按流动性排序，主标的在前>"],
  "rebalance": {"every_n_bars": 20},
  "weights_series": [
    {"as_of": "<日期>", "weights": {"600519": 0.18, "000858": 0.12, "...": 0.0}}
  ]
}
```

**产出时必须交代的四件事**：

1. **as_of**：权重对应的口径日。
2. **现金占比**：`1 − sum(weights)`，并说明它来自 regime 的现金下限还是取整残差。
3. **调仓频率**：`every_n_bars`，并说明与换手的关系（用 `mcp__fd-quant__summarize_turnover` 给出本期相对上期的换手）。
4. **权重来源链**：组来自哪个申万 L1、组内标的来自哪次排序、例外框架是否改动过名单。

---

## 阶段 4：风控参数（**归属必须讲明**）

三档止损参数（来自 FinRL-X 的 `risk_manager`，量级为公开起点，需按标的重标）：

| 参数 | 默认值 | 触发后动作 |
|---|---|---|
| 绝对止损 | 单标的相对成本价 **-5%** | 清出该标的，权重归零 |
| 移动止损 | 相对持有期高点回撤 **-10%** | 同上 |
| 冷却期 | 止损后 **10 个交易日**内不得重新入选 | 排序阶段排除 |

### ⚠️ 归属声明（每次给风控参数都必须附这段）

> **这些数字本身不会被引擎自动执行**——它们只是参数取值。柏讯的权重模式只按 `weights_series` 调仓，契约的 `constraints` 也只有单票/板块两个上限字段，没有任何止损字段。**轮动是权重轨，没有 overlay 通道**：把 `risk` 传给权重轨的回测或 live 都会被显式拒绝（`risk_not_supported_on_weight_track`）。所以止损真正生效只有两条路：
> 1. **写进权重序列（轮动的唯一自动路径）**：在每个调仓点（或每日）先判断止损条件，触发则在 `weights_series` 里把该标的权重置 0——即**把止损表达为权重**，权重引擎照常执行。回测与 live 都成立。
> 2. **由人执行**：监控到触发后手工调整策略。
>
> 单标的策略另说：`run_backtest(risk=...)` 与 `start_strategy(risk=...)` 都已透传且由平台执行（回测逐 bar、live 每根新 bar 复查，触发即平仓，快照留 `risk_triggers`）。**不要**把这条能力写成轮动可用。

---

## 阶段 5：量级参考与代价（必须给，防止用户误以为免费）

- **换手成本**：调仓频率越高，换手越大。A 股成本默认：佣金 0.025%（双边）、印花税 0.05%（卖出）、滑点 5bp（双边）。用 `mcp__fd-quant__summarize_turnover` 给出本期换手，并换算成成本量级。
- **集中度代价**：组数越少、单组预算越高，行业集中风险越大；HHI 与"前 N 权重占比"两个指标一并给出。
- **止损代价**：止损越紧，被"噪声扫出"的概率越高，冷却期会放大这个代价（错过反弹）。

---

## 降级路径

| 情形 | 处理 |
|---|---|
| regime 判定不可用 | 明示"无 regime 判定，无法确定名额与现金下限"，**不自行假定** |
| 排序结果缺失 | 明示"无排序输入，无法建仓" |
| 契约校验被拒 | 原样转述拒绝原因（点名日期与权重和），**不偷偷归一化后重试** |
| 用户要求做空/杠杆 | 明确说明契约拒绝负权重、权重和 ≤1，本套件不支持 |

---

## 交接

产出契约实例与 spec 后 → `rotation-run`：回测 → 模拟盘 → 权重快照解读。

---

研究参考，不构成投资建议。上游 FinRL-X 业绩数字为未经审计的自述回测，不作为预期。
