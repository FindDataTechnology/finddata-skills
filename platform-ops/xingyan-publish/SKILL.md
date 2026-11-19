---
name: "xingyan-publish"
description: "把文章/教程写并发布到寻数·星研内容平台：按「为 AI 读者写作」纪律起草（双语成对 + claim 骨架）→ 脱敏与可读性机检 → CMS（Strapi）三集合录入发布 → 官网构建链（CMS 真源）自动出站 → 三 feed / llms.txt / 客户 agent 供给面验证。含全部已踩坑与三条发布腿的取舍。"
---

# xingyan-publish — 写并发布文章到寻数·星研

星研 = FindData 对外内容线。**读者已经不只是人**：同一篇内容要同时被三类机器读者消费，写作时就要按这个来组织。

| 读者 | 怎么拿到内容 | 对写作的要求 |
| --- | --- | --- |
| 客户决策者与从业者 | 官网页面 | 每节自足、术语唯一、结论先行 |
| 自家 agent / 已装 pack | 站内检索 + 三区 feed | 结构可解析、断言可锚定 |
| 客户 agent（柏讯供给面） | `wire_content_browse` / `wire_content_search` / `wire_claim_resolve` | claim 骨架 + 来源 id，否则只能给一段散文 |
| 外部答案引擎（GPTBot/ClaudeBot/PerplexityBot…） | `llms.txt` → 三区 feed → 页面 JSON-LD | 引用粒度要能落到 `slug/claim-id` |

**两个承载面**：

| 面 | 地址 | 角色 |
| --- | --- | --- |
| 星研 CMS（Strapi v5，**真源**） | `https://cms.finddatatech.cloud/admin` | 三集合托管：`briefing` / `course` / `research-article`；官网构建期经 REST 拉取 |
| 官网（fd-official-web，Astro 静态） | `https://www.finddatatech.cloud` | 消费面 + 机读面（三 feed / `llms.txt` / `robots.txt` / `sitemap.xml` / 页面 JSON-LD） |

**canonical 起草目录**：`~/finddata/docs/xingyan/`（三分区 `briefings/` `academy/` `research/`，双语 `zh/`+`en/` 成对，slug 必须相同）。README 与模板在该目录。

**线上 URL 与目录名不同名，别按目录猜**（2026-11-09 实测踩过）：课程必须写成 `/zh/research/academy/<slug>/` 与 `/research/academy/<slug>/`，**没有** `/academy/<slug>` 这条路由。用错前缀时 nginx 会回落到 10269 字节的通用外壳（HTTP 200，`<h1>` 是站点主标题，正文里没有课程词），看起来极像"内容没发出去"，其实只是路径不存在。另外**结尾斜杠必需**：省略时是 301 跳到带斜杠的地址，`curl` 不 `-L` 就只拿到跳转页。

---

## §0 为 AI 读者写作（写作纪律本体，先读这节）

机器读者不给耐心：它按标题切块、按 claim 取断言、按 id 找证据。写坏了机器不会「大概看懂」，它只会取到空。

### 0.1 结构纪律（机器按它切块）

1. **每节自足**：小节标题必须自带语境——写「W2 的数据校验规则」而不是「第二阶段」。正文里禁止「如前所述」「见上」「本文开头提到的」这类指代；每节要能单独被抽出仍成立。
2. **术语唯一**：一个概念全文只用一个词。别在同一篇里换着说「功能集 / 能力包 / 套件」（这三个在柏讯是**不同**的分类层级）。术语表见 `ai-readability-rules.txt` 的术语族。
3. **不写 H1**（标题由 frontmatter 承载）；二级标题是 claim 的锚点，**改了标题等于改了锚**。
4. **课程结构顺序固定**：学完能做什么 / 前置条件 / 步骤 / 自检练习 / 如果没成功 / 下一步。派生器按这个契约提取，顺序错会抽不出。
5. **表格与列表优先于长段散文**：机器解析表格比解析「此外还有一些」可靠得多。

### 0.2 断言纪律（机器按它取证据）

**凡是金额、比例、因果、承诺，必须能被机器追到来源**——这就是 claim 骨架：

```yaml
sources:
  - id: src-1               # 引用键；双语同键同序，被发布 claim 引用后不可变更/不可复用
    label: 来源说明
    url: https://…           # 可选；对外声称「可查全文」时必填公开地址
claims:
  - id: c0001               # 形如 c0001；双语共享同一 ID，发布后不得变更
    section: 结论先行        # 必须是正文 ## 标题的逐字文本（en 侧写英文标题）
    type: number            # number | causal | promise
    evidence: [src-1]       # 指向 sources 的 id，至少一条
```

- **不写断言文本**，只写锚 + 证据：断言文本在正文里，改正文不改 ID。
- 做不到给来源，就别写那个数字；确实只能是推测，就在正文里明写「待验证」（这是明示推测，不是豁免）。
- 强断言由门自动识别：`[¥￥]\d`、`\d+(\.\d+)?%`、`因为…所以/导致`、`一定/必然/保证能`。这类句子所在小节**必须**有锚定 claim。

### 0.3 门的判定口径

`python3 ~/finddata/docs/xingyan/scripts/ai_readable_check.py <文件或目录>` 必须 **0 错误**。一个脚本、两道门：

| 门 | 管什么 |
| --- | --- |
| 散文门（A–E） | 术语族一致、无跨节指代、必备字段、段落长度；存量债记在 `ai-readability-baseline.txt` |
| claim 门（F0–F5） | 来源键格式/重复、四要素完整、锚点存在、证据闭环、双语同构、已发布 ID 不得消失或复用 |

- 已发布 ID 登记在 `scripts/claims_ledger.json`（`--write-ledger` 只增不删）。
- **未声明 claims 的存量条目不阻断**（渐进补齐）；但一旦声明，四要素/锚点/证据/双语/强断言覆盖全部生效。

### 0.4 机读面是自动产物，不是手写物

写完就自动有了，**不需要也不允许另写一份**：三个 feed（`/briefings.json` `/academy.json` `/research.json`，顶层带 `schema_version`，每条含双语 title/summary/body/sources/claims + 页面 URL）、`llms.txt`（三 feed + 引用方式 `slug/claim-id`）、`robots.txt`（放行 7 类 AI 抓取）、`sitemap.xml`、六个详情页的 JSON-LD。

它们的唯一来源就是 frontmatter 与正文——**frontmatter 写歪了，机器面跟着歪**。构建门 `check-discoverable.mjs` 会在 feed 缺 `schema_version`、llms 指向不存在的地址、sitemap 漏分区时直接让构建失败。

---

## 硬规矩（发布 gate，逐条都会被机器拦）

1. **双语成对**：zh/en 缺一侧不得发布（官网构建门 + CMS 导入预检都拦）。claim ID 两侧同集、同序、同 type；只有 `section` 随语言变。
2. **脱敏机检**：`python3 ~/finddata/docs/xingyan/scripts/sanitize_check.py` 必须 0 命中（规则清单 `scripts/internal-identifiers.txt`：内部节点名/私有仓/集群/凭据形制）。CMS 侧发布闸打包了同源副本，双保险。
3. **use 层语言门**（`check-content-integrity.mjs`，仅 `level: use` 的课程）：正文不得含 `finddatatech.cloud` 等 URL/域名、控制台深链、错误码；错误码与代码块只能进「如果没成功」小节。**pack 链接放 frontmatter `pack_url`，不进正文**。
4. **终审留痕**：正式发布需人工终审；agent 代发时在交付说明里明示待终审项。
5. **凭据红线**：任何凭据不进内容、不进正文、不进提交。

---

## 发布流程

### 腿 1 · 起草（canonical）

- 课程 → `academy/{zh,en}/<slug>.md`（slug 定后不改）；内参 → `briefings/{zh,en}/<YYYY-MM-DD>-<短名>.md`；研究 → `research/{zh,en}/<slug>.md`。
- frontmatter 按类型套 `templates/`（course: `title/summary/level('use'|'build')/order/source_material/updated/pack_url`；briefing 加 `date/tags/sources`；research 加 `kind(paper|casestudy|note)`；有强断言则三类都要 `sources`+`claims`）。
- 先跑 §0.3 两道门 → 0 错误，再跑脱敏门 → 0 命中。

### 腿 2 · CMS 录入（CMS 是真源，这一步决定线上有没有）

凭据：应急本地账号 `xingyan-admin@finddatatech.cloud`（Editor，可发布）——密码在 CMS 主机的 `/opt/fd-strapi/.admin-credentials`（在 CMS 主机上读；官网发布主机上**没有**）；或浏览器 SSO `aloadtree@gmail.com` 走 UI。**程序化 REST 配方（实测可用）**：

```python
# POST {BASE}/admin/login {"email","password"} → data.token
# 建 zh 草稿：POST {BASE}/content-manager/collection-types/api::course.course?locale=zh
#   body: {slug,title,summary,order,level,updated,pack_url,source_material,body,claims,sources}
#   ⚠️ 字段值存裸文本（不带引号）；body=正文源文本，【不带 frontmatter】
#   ⚠️ claims/sources 是 JSON 字段，直接传数组，不要序列化成字符串
# 发布：POST .../api::course.course/{documentId}/actions/publish?locale=zh
# 建 en 变体：POST 同端点?locale=en，data 里【必须】显式带 documentId=zh的documentId
#   + 全部非本地化字段（slug/order/level/pack_url 等）→ 发布同款
# 幂等：先 GET ?locale=*&filters[$and][0][slug][$eq]=<slug> 判存在
# 验发布态：单 locale 视图看 `status`（publishedAt 恒 null，跨语言聚合视图的 modified 是展示差异）
```

- 三集合端点：`api::briefing.briefing` / `api::course.course` / `api::research-article.research-article`。
- 非本地化共享字段：`slug`/`date`/`kind`/`order`/`pack_url`；随语言变：`title/summary/tags/sources/source_material/body/**claims**`（claim 的 `section` 是各语言自己的标题文本）。
- 发布闸会拦内部标识与 claim 违规（400 + 命中行/字段报文）：`F3-证据悬空`、双语不同构等。**只有 publish 与 create/update(status=published) 会拦，PUT 存草稿不拦**——所以草稿能过不代表能发。

**三个 2026-11-09 实测的坑（都出在「校验全过、发布仍被拦」这条路上）**：

| 现象 | 真因 | 处置 |
| --- | --- | --- |
| 发布 400 `claim「cNNNN」缺 evidence` | 前端把 `evidence: [src-1]` 摊成了字符串 `"[src-1]"` | 解析器必须把内联 YAML 列表落成数组；字符串会被 claim 闸判成「没写」 |
| 发布 400 `F3-证据悬空`，本地 `ai_readable_check.py` 却是 0 错误 | **`course` 集合没有 `sources` 字段**（读回是 `null`），evidence 永远解析不到来源 | 本地门只校验 md，CMS 门校验入库后的字段；两者不同源。图文课程不要写 `claims`/`sources`（模板标为可选），除非该集合确实有 sources 字段 |
| en 变体 400 `slug must be a string, but the final value was: null` | PUT en 时没带非本地化字段 | zh 能过是因为建条目时字段已入库；en 必须显式带 `slug/order/level/pack_url` |

判定顺序建议：**先确认该集合有哪些字段**（`GET …?locale=zh` 看返回键），再决定要不要写 claims/sources——否则会在「本地全绿、发布必红」上来回空转。
- **图文课程的图片上传**：媒体库路由是 **`/upload`**（不是 `/admin/upload`，后者 405）：
  ```python
  # POST {BASE}/upload  multipart 字段 files，头 Authorization: Bearer <admin JWT>
  # → url 形如 /uploads/<名>_<hash>.png（公网可 GET）
  # 正文引图用绝对 URL https://cms.finddatatech.cloud/uploads/<file>
  # canonical 仓内用相对路径 media/<slug>/<file>，发布时替换
  ```

### 腿 3 · 官网站内呈现（两条线，别搞混）

**生产有两套出站机制，行为不同——这是最容易出错的地方**：

| 线 | 触发 | 内容来源 | 谁在用 |
| --- | --- | --- | --- |
| **宿主静态线（主）** | `bash /opt/fd/fd-web-deploy.sh`（另有 CMS publish webhook 自动触发） | **CMS 真源**——`/opt/fd/fd-web-build.env` 里 `STRAPI_URL=<CMS 服务内网地址>`，构建期经 REST 全量拉取 | 真实流量（宿主 nginx `root /opt/fd/web/dist`） |
| k8s pod 线（兜底） | ArgoCD 滚 `fd-web` | 仓内快照（Dockerfile 未传 `STRAPI_URL` 时 `strapi:fetch` 走快照分支） | 回退用，NodePort 30442 |

**由此得出三条铁律**：

1. **CMS 条目集合必须 ⊇ 仓内快照**。仓里有而 CMS 没有的条目，会在下一次 CMS 触发的部署里**被删掉**（2026-10-31 实测：`yizuo-machines-deploy-manage` 从线上消失，公网落回 SPA 外壳）。新增条目先建 CMS，再考虑仓内副本。
2. **改内容改 CMS**，不要以为改仓内 md 就生效——构建读的是 CMS。
3. **判断本次构建读的是哪一份**：看公网 `/content-manifest.json` 的 `source` 字段（`cms` | `snapshot` | `fixture`）。

| 情况 | 做法 |
| --- | --- |
| 日常发内容 | 腿 2 建 CMS 并发布 → 部署线自动带出站（可 `ssh cheap1 'bash /opt/fd/fd-web-deploy.sh'` 手动催） |
| 改站点代码/样式 | 直接改官网仓 + 出片（腿 4） |
| 仓内新增条目 | **先补 CMS**，否则下次部署会删 |
| 官网页面 404 / 列表没新条目 | 先看 `/content-manifest.json` 的 `source` 与 `total_files`，再查 CMS 是否有该条目且 `status=published` |

官网仓提交纪律：
- **只 add 自己的文件**——树上常有并行会话改动（`src/data/*.json` 抓取产物），勿 `-A`。
- **两个远端：`origin`=GitHub，`gitee`=gitee**。image workflow 只监听 GitHub `push: [main]`——**只推 gitee 不出片**，两个都推。

### 腿 4 · 出片滚版与验证（改代码时才需要）

1. 镜像：`gh run list -R FindDataTechnology/fd-official-web` 看 `image` workflow（tag=commit 7 位短 sha）。
2. relay：`ssh cheap3 '/usr/local/bin/tcr-relay-sync.sh'`，日志 grep `fd-web/official-web:sha-<tag>` OK。
3. bump：官网仓 `deploy/k8s/fd-web.yaml` image 行 → 新 sha，推 gitee（ArgoCD 源）。
4. 滚：生产在官网专用集群（远端主机 `fd-deploy`），**不在**柏讯集群。先 `kubectl config current-context` 确认目标是出片上下文（**context 名含空格，显式传 `--context` 反而报 does not exist——实测只用裸 kubectl**），再：
   ```bash
   kubectl -n argocd annotate application fd-web argocd.argoproj.io/refresh=hard --overwrite
   kubectl -n fd-web rollout status deploy/official-web
   ```
   等 `sync.revision` == 新 commit 再 rollout。
5. 验证防假阴性三层：pod 内 `grep <标记> /usr/share/nginx/html/...`（**英文页在无前缀根路径**，中文在 `/zh/…`）→ 源站 `ssh fd-deploy 'curl -s http://127.0.0.1:30442/<路径>/'` → 公网（EdgeOne `max-age=300` 起）。

### 腿 5 · 机读面与供给面验证（内容类发布必做）

| 验什么 | 怎么验 | 期望 |
| --- | --- | --- |
| feed 带契约版本 | `curl -s https://www.finddatatech.cloud/research.json \| head -3` | 顶层有 `"schema_version": "1"` |
| 条目进了 feed | 查该 JSON 里有无目标 slug，`claims` 双语 ID 是否与你写的一致 | 一致 |
| 构建读的是 CMS | `curl -s .../content-manifest.json` | `"source": "cms"` |
| 客户 agent 能取到 | 柏讯侧 `wire_content_browse(zone=…)` / `wire_claim_resolve(slug, "c0001")` | 返回骨架 + 锚小节正文 + 证据；`section_found=true` |
| 发现面可达 | `curl -s .../llms.txt` / `robots.txt` | 三 feed 在列；sitemap 行在 |

**注意**：内容进供给面是**下一轮摄取**才可见（摄取每日一次，同指纹短路）。要立刻验可手动触发：`POST /internal/xingyan/sync?force=true`（需 `XINGYAN_INTERNAL_TOKEN`），再用 `python scripts/xingyan_reconcile.py` 对账零漂移才算收口。

---

## 已踩坑速查

| 现象 | 真因 | 处置 |
| --- | --- | --- |
| 线上某门课/某篇**整页消失，落回首页外壳** | 仓内有、CMS 无 → CMS 真源部署把它删了 | 把该条目建进 CMS 并发布；见腿 3 铁律 1 |
| 改了 md 但官网没变 | 构建读 CMS（`STRAPI_URL` 已设），仓内 md 不生效 | 改 CMS；查 `content-manifest.json` 的 `source` |
| curl 公网 URL 得到首页壳 | 站点 SPA 兜底（未知路径 200 壳）+ EdgeOne 缓存 | **curl 200 ≠ 页面存在**，必须看 `<title>`/正文特征；验 pod 内文件与源站 30442 |
| feed 里 claims 全空 | CMS→仓序列化丢了契约字段（`claims`/`sources.id`） | 确认 serialize 输出含 claims；用 `research.json` 实读核 |
| feed 缺 `schema_version` | 构建门未覆盖或版本号写错 | 构建门会拦；`XINGYAN_FEED_SCHEMA_VERSION` 只在破坏性变更时提升 |
| use 层正文被 `tech-identifier` 拦 | 正文含域名/控制台深链/错误码 | 链接移 `pack_url`；错误码只进「如果没成功」 |
| claim 发布被拦「evidence 悬空」 | `claims[].evidence` 指向的 id 不在 `sources` 里 | 给来源条目加 `id: src-N`；双语同键同序 |
| claim 发布被拦「双语不同构」 | 两侧 ID 集合或 type 不一致 | 同 ID 集合、同 type；只有 `section` 随语言变 |
| claim 锚点取不到正文（`section_found=false`） | `section` 与正文 `##` 标题不是逐字一致 | 复制标题原文；改标题即改锚，须同步改 claim |
| CMS `GET .../{documentId}?locale=*` 返回空 | 单文档路径不吃 `*` | 逐 locale 查或用集合列表 filters |
| 建 en 变体成了独立新文档 | data 里没带 zh 的 `documentId` | en 载荷显式带 `documentId` + 全部非本地化字段 |
| 字段里出现 `\"…\"` 双引号壳 | frontmatter 解析没剥引号就入库 | 字段值一律裸文本入库 |
| 页面顶部出现第二块 frontmatter | `body` 字段带了 frontmatter | body 只放正文 |
| `POST /admin/upload` 405 | Strapi 5 媒体库路由在 `/upload`；`/admin/*` 全是 SPA 兜底 | `POST {BASE}/upload` multipart `files` + admin JWT |
| 找不到官网部署在哪 | 生产=官网专用集群的 `fd-web/official-web`（NodePort 30442←宿主 nginx←EdgeOne），**不在**柏讯集群 | 用**裸 kubectl**（当前 context `the vendor`，含空格，别加 `--context`）；别名 `fd-deploy`（地址内网留存） |
| `git push` 成功但 image workflow 没跑 | 只推了 gitee | 两个远端都推；`git ls-remote origin main` 对拍 |
| 公开读 CMS API 403 | 生产未开公开 find（正确姿态） | 走只读 API token（构建侧已配）或 admin JWT |
| 英文课程页 404 | 英文是默认语言，走**无前缀根路径** | 中文在 `/zh/…`，按语言换路径验 |
| 内容已发布但客户 agent 查不到 | 尚未到下一轮摄取 / 未同步到供给面 | 手动 `POST /internal/xingyan/sync?force=true`，再跑 `xingyan_reconcile.py` |

---

## 写作要点速记（§0 的浓缩版）

读者=客户决策者与从业者，**外加三类 AI 消费面**。每节自足（标题自带语境、无跨节指代）、术语唯一、结论先行、表格/列表优先；每条数字与因果断言对应 `sources` 可查证来源（做不到就删或明写「待验证」）；宁短勿虚；不写 H1；步骤可复现、不依赖未公开环境；课程六段结构顺序固定。
