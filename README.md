# finddata-skills

> **Part of the [Wire line (寻数·柏讯)](https://www.finddatatech.cloud/products/wire) of [FindData](https://www.finddatatech.cloud)** — skill sources for the wire presets.

FindData 精选 agent 技能库：经济、金融与通用数据分析。每个技能的核心价值是**分析方法论**，
数据源可替换——凡有数据源分层的技能，已注入 "FindData MCP 优先" 指引（`fd-open-data-mcp` /
`fd-find-data-business-mcp` 的 `read` / `read_range` / `list_concepts` / `ai_search` / `graph_search`）。

## 技能索引

### research-methods/ — 研报与估值方法论（8）
| 技能 | 说明 | 上游 |
|---|---|---|
| earnings-analysis | 财报点评研报（beat/miss、预期修正） | anthropics/financial-services |
| sector-overview | 行业概览研报 | anthropics/financial-services |
| comps-analysis | 可比公司估值 | anthropics/financial-services |
| dcf-model | DCF 建模 | anthropics/financial-services |
| 3-statement-model | 三表联动模型 | anthropics/financial-services |
| returns-analysis | 收益归因 | anthropics/financial-services |
| ic-memo | 投委会备忘录 | anthropics/financial-services |
| macro-rates-monitor | 宏观利率监控 | anthropics/financial-services (LSEG partner) |

### market-analysis/ — 市场分析（4）
| 技能 | 说明 | 上游 |
|---|---|---|
| company-valuation | 公司估值 | himself65/finance-skills |
| stock-correlation | 相关性/配对分析 | himself65/finance-skills |
| earnings-preview | 财报前瞻 | himself65/finance-skills |
| earnings-recap | 财报复盘 | himself65/finance-skills |

### cn-market/ — A股（1）
| 技能 | 说明 | 上游 |
|---|---|---|
| akshare-stock | A股全能分析（技术/基本面/资金流，adapter 可替换） | molezzz/openclaw-stock-skill |

### us-market/ — 美股（1）
| 技能 | 说明 | 上游 |
|---|---|---|
| stock-analysis | 美股/A股/港股基本面+技术面分析 | claude-office-skills/skills |

### sentiment/ — 舆情（1）
| 技能 | 说明 | 上游 |
|---|---|---|
| last30days | 近 30 天多平台舆情研究 | mvanhorn/last30days-skill |

### data-analysis/ — 通用数据分析（4）
| 技能 | 说明 | 上游 |
|---|---|---|
| data-analysis | 电子表格/CSV 分析与可视化 | claude-office-skills/skills |
| exploratory-data-analysis | 探索性数据分析（EDA） | k-dense-ai/scientific-agent-skills |
| statsmodels | 计量经济学（OLS/GLM/ARIMA 推断） | k-dense-ai/scientific-agent-skills |
| statistical-analysis | 统计检验选择与 APA 报告 | k-dense-ai/scientific-agent-skills |

### platform-ops/ — 平台运营（1）
| 技能 | 说明 | 上游 |
|---|---|---|
| xingyan-publish | 发布文章/教程到寻数·星研（canonical 起草→脱敏机检→CMS 录入→官网构建链） | 自研 |


## 本地安装（ZCode / Claude Code 适配）

仓库技能是**真源**，本地使用用安装器同步到各 agent 的技能目录（全部 agent 读同一
开放 SKILL.md 格式，无需改内容）：

```sh
python3 scripts/install_local.py            # 全量同步到 ~/.zcode/skills、~/.agents/skills、~/.claude/skills
python3 scripts/install_local.py --list     # 列出可安装技能
python3 scripts/install_local.py --only xingyan-publish   # 只装一个
```

- 目标目录：ZCode=`~/.zcode/skills`（及 `~/.agents/skills`）；Claude Code=`~/.claude/skills`。
- 幂等：内容一致不覆盖；`--force` 强制重拷。安装副本带真源指针横幅——**改技能改仓库，再跑安装器**。
- MCP Gateway 注册（agent 在线调用面）另见 `scripts/register_skills.py`。

## 未收录（及原因）

- gracefullight/stock-checker（stock-analysis 8 维版）— 仓库无 LICENSE，不能再分发；本机已另行安装
- nimrodfisher/data-analytics-skills（time-series-analysis 等）— 仓库无 LICENSE
- anthropics/knowledge-work-plugins@forecast — 销售管道预测（sales pipeline），非时间序列预测
- k-dense-ai@timesfm-forecasting — 2MB 示例 + 基础模型重依赖，收益比低

## License

仓库聚合层 MIT。每个技能保留上游 license，详见各技能目录 `ATTRIBUTION.md`（含上游 repo、commit 与本地改动说明）。
