---
name: "xingyan-publish"
description: "把文章/教程发布到寻数·星研内容平台：星研 canonical 起草（双语成对）→ 脱敏机检 → CMS（Strapi）学院/内参/研究模块录入发布 → 官网构建链自动拉取 → 滚版与缓存验证。含三条发布腿的取舍与全部已踩坑。"
---

# xingyan-publish — 发布文章到寻数·星研

星研 = FindData 对外内容线，**两个承载面**：

| 面 | 地址 | 角色 |
| --- | --- | --- |
| 星研 CMS（Strapi v5，真源） | `https://cms.finddatatech.cloud/admin` | 三集合托管：`briefing`（内参）/ `course`（学院）/ `research-article`（研究）；官网构建期经 REST 拉取 |
| 官网（fd-official-web，Astro 静态） | `https://www.finddatatech.cloud` | 消费面：`/zh/research/academy/<slug>` 等路径；构建第一步 `strapi:fetch` 从 CMS 拉 md |

**canonical 起草目录**：`~/finddata/docs/xingyan/`（三分区 `briefings/` `academy/` `research/`，双语 `zh/`+`en/` 成对，slug 必须相同）。README 与模板在该目录。

## 硬规矩（发布 gate，逐条都会被机器拦）

1. **双语成对**：zh/en 缺一侧不得发布（官网构建门 + CMS 导入预检都拦）。
2. **脱敏机检**：`python3 ~/finddata/docs/xingyan/scripts/sanitize_check.py` 必须 0 命中。规则清单 `scripts/internal-identifiers.txt`（内部节点名/私有仓/集群/凭据形制）。CMS 侧发布闸还打包了同源副本，双保险。
3. **use 层语言门**（官网 `check-content-integrity.mjs`，仅 `level: use` 的课程）：正文不得含 `finddatatech.cloud` 等 URL/域名、控制台深链、错误码；错误码与代码块只能进「如果没成功」小节。**pack 链接放 frontmatter `pack_url`，不进正文**（正文提功能集名字即可）。
4. **终审留痕**：正式发布需人工终审；agent 代发时在交付说明里明示待终审项。
5. **凭据红线**：任何凭据不进内容、不进正文、不进提交。

## 发布流程（四腿）

### 腿 1 · 起草（canonical）

- 课程 → `academy/{zh,en}/<slug>.md`（slug 定后不改）；内参 → `briefings/{zh,en}/<YYYY-MM-DD>-<短名>.md`；研究 → `research/{zh,en}/<slug>.md`。
- frontmatter 按类型套 `templates/`（course: `title/summary/level('use'|'build')/order/source_material/updated/pack_url`；briefing 加 `date/tags/sources`；research 加 `kind(paper|casestudy|note)`）。
- 正文不写 H1（标题由 frontmatter 承载）；读者是客户决策者与从业者，不是工程师。
- 跑机检 → 0 命中。

### 腿 2 · CMS 录入（推荐主路径：CMS 是真源）

凭据：应急本地账号 `xingyan-admin@finddatatech.cloud`（Editor，可发布）——密码在 cheap-1 `/opt/fd-strapi/.admin-credentials`（`ssh cheap1` 读取；`ssh fd-deploy` 上**没有**；或用浏览器 SSO `aloadtree@gmail.com` 走 UI）。**程序化 REST 配方（实测可用）**：

```python
# POST {BASE}/admin/login {"email","password"} → data.token
# 建 zh 草稿：POST {BASE}/content-manager/collection-types/api::course.course?locale=zh
#   body: {slug,title,summary,order,level,updated,pack_url,source_material,body}
#   ⚠️ 字段值存裸文本（不带引号）；body=正文源文本，【不带 frontmatter】——
#      官网 fetch-strapi 的 serializeAcademy 会从字段重新生成 frontmatter
# 发布：POST .../api::course.course/{documentId}/actions/publish?locale=zh
# 建 en 变体：POST 同端点?locale=en，data 里【必须】显式带 documentId=zh的documentId
#   + 全部非本地化字段（slug/order/level/pack_url 等，document service 不自动复制）→ 发布同款
# 幂等：先 GET ?locale=*&filters[$and][0][slug][$eq]=<slug> 判存在
# 验发布态：集合列表接口看 `status` 字段（publishedAt 恒为 null，别用它判）
```

- 三集合端点：`api::briefing.briefing` / `api::course.course` / `api::research-article.research-article`。
- 非本地化共享字段：`slug`/`date`/`kind`/`order`/`pack_url`；随语言变：`title/summary/tags/sources/source_material/body`。
- 发布闸会拦内部标识（400 + 命中行报文）；发布前自己先跑过 xingyan 机检就不会撞。
- 验证：admin `GET /content-manager/collection-types/api::course.course/{documentId}?locale=*`（单文档路径不接 `*`，逐 locale 查或用集合列表）。

**图文课程的图片上传（2026-10-25 实测）**：这台 Strapi 5 的媒体库 admin 路由挂在 **`/upload`**，不是
`/admin/upload`（后者 405——`/admin/*` 全是 admin SPA 兜底，GET 200 是假象）：

```python
# POST {BASE}/upload  multipart 字段名 files, 头 Authorization: Bearer <admin JWT>
# → 返回文件对象数组，url 形如 /uploads/<名>_<hash>.png（公网可直接 GET 200）
# CMS 正文引图用绝对 URL https://cms.finddatatech.cloud/uploads/<file>；
# canonical 仓内用相对路径 media/<slug>/<file>，发布时再替换成 CMS 绝对 URL。
```

- 图文课程已获官网门支持：`check-content-integrity.mjs` 对**纯图片定义行**（`![alt](url)` 独占一行）
  整行豁免 use 层规则（prose+图同行仍拦）——官网仓 6ae73a3；CMS 托管截图不再触发 tech-identifier。

### 腿 3 · 官网站内呈现

**先说清一件事（2026-10-26 实测更正，此前的"自动拉取"说法不成立）**：官网**镜像构建不拉 CMS**——`Dockerfile` 的 build 阶段没有传 `STRAPI_URL`/`STRAPI_READ_TOKEN`，`strapi:fetch` 见 `STRAPI_URL` 未设置就走「仓内快照」分支。所以 **CMS 发布完，官网不会自动出现**：必须把同一份 md 落到官网仓 `src/content/<分区>/{zh,en}/`，再走腿 4。（本机想验「在线拉取能拿到」可手动 `STRAPI_URL=https://cms.finddatatech.cloud npm run strapi:fetch`，但公开读默认 403——生产未开公开 find，是正确姿态；别把 403 当"内容没发布"。）

| 情况 | 做法 |
| --- | --- |
| 日常发内容 | CMS 发布（腿 2）→ **把同一份 md 复制到官网仓 `src/content/<分区>/{zh,en}/`** → 腿 4 |
| 改站点代码/样式 | 直接改官网仓 |
| 官网页面 404 / 列表没新条目 | 检查快照有没有落（最常见原因就是这个） |

官网仓提交纪律：
- **只 add 自己的文件**——树上常有并行会话的改动（`src/data/*.json` 抓取产物等），勿 `-A`。
- **两个远端：`origin`=GitHub，`gitee`=gitee**。image workflow 只监听 GitHub 的 `push: [main]`——**只推 gitee 不会出片**，两个都得推。
- 远端有并行提交：`git stash -u` → `git rebase github/main` → 推 github → `git push gitee HEAD:main --force`（rebase 改写历史，gitee 落后需 force）。

### 腿 4 · 出片滚版与验证

1. 官网镜像：`gh run list -R FindDataTechnology/fd-official-web` 看 `image` workflow（push **GitHub** main 触发；tag=commit 7 位短 sha）。
2. relay：`ssh cheap3 '/usr/local/bin/tcr-relay-sync.sh'`，日志 grep `fd-web/official-web:sha-<tag>` OK。
3. bump：官网仓 `deploy/k8s/fd-web.yaml` 的 image 行 → 新 sha，commit 推 gitee（ArgoCD 源）。
4. 滚：生产=chengsi k3s（`kubectl --context tencent -n fd-web`，别去 cheap 集群找）；ArgoCD 应用名 `fd-web`：`kubectl --context tencent -n argocd annotate application fd-web argocd.argoproj.io/refresh=hard --overwrite`，等 `status.sync.revision` == 新 commit（首刷常不拾取），再 `rollout status deploy/official-web`。
5. 验证（防假阴性三层）：pod 内产物 `exec ... grep <内容标记> /usr/share/nginx/html/<分区>/<路径>/index.html`（**英文页在无语言前缀的根路径**，中文在 `/zh/…`）→ 源站直查 `ssh fd-deploy 'curl -s http://127.0.0.1:30442/<路径>/'` → 公网（EdgeOne 缓存 max-age=300 起，可能更久；`curl -sI` 看 `eo-cache-status`，MISS=刚回源）。

## 已踩坑速查

| 现象 | 真因 | 处置 |
| --- | --- | --- |
| use 层正文被 gate 拦 `tech-identifier` | 正文含 `finddatatech.cloud`/MCP/A2A/Logto/控制台路径 | 链接移 `pack_url`；正文用名字与「本课页配套链接」话术 |
| curl 公网 URL 得到首页壳 | 站点是 SPA 兜底（未知路径 200 壳）+ EdgeOne 缓存 | **curl 公网=假阴性**；验 pod 内文件与源站 30442，等缓存过期或看 `eo-cache-status` |
| 官网列表没显示新条目 | 镜像没滚完 / EdgeOne 缓存 / 分组按 `level`（use/build/undeclared） | 先验 pod 内 index.html 含 slug，再等缓存 |
| CMS `GET .../{documentId}?locale=*` 返回空 | 单文档路径不吃 `*` | 逐 locale 查或用集合列表 filters |
| 建 en 变体成了独立新文档 | data 里没带 zh 的 `documentId` | en 载荷显式带 `documentId` + 全部非本地化字段 |
| 发布 400 带命中行 | CMS 发布闸机检（fail-closed） | 按行改写重发；与 xingyan 机检同源 |
| 找不到官网部署在哪 | 生产=chengsi k3s `fd-web/official-web`（NodePort 30442←宿主 nginx←EdgeOne），**不在** cheap 集群 | `kubectl --context tencent -n fd-web`；ssh 别名 `fd-deploy`（124.220.7.175，ubuntu） |
| 公开读 CMS API 403 | 生产未开公开 find（正确姿态） | 走只读 API token（官网构建侧已配）或 admin JWT |
| `POST /admin/upload` 405 | 这台 Strapi 5 媒体库路由在 **`/upload`**；`/admin/*` 全是 SPA 兜底 | `POST {BASE}/upload` multipart 字段 `files` + admin JWT；见腿 2 |
| 字段里出现 `\"…\"` 双引号壳 | frontmatter 解析时没剥引号就入库 | 字段值一律裸文本入库（官网序列化器会自己加引号） |
| 页面顶部出现第二块 frontmatter | `body` 字段里带了 frontmatter | body 只放正文；frontmatter 由官网 fetch 从字段生成 |
| CMS 发布了但官网没新课程 | **镜像构建不拉 CMS**（Dockerfile 未传 `STRAPI_URL`）→ 走仓内快照 | 把同一份 md 复制进官网仓 `src/content/<分区>/{zh,en}/` 再出片（见腿 3） |
| `git push` 成功但 image workflow 没跑 | 只推了 gitee；该仓 `origin`=GitHub，workflow 只监听 GitHub 的 push | 两个远端都推；`git ls-remote origin main` 对拍 commit |
| 本机 `strapi:fetch` 报 403 | 生产未开公开 find（正确姿态） | 不是内容问题；验内容用 admin JWT 或直接看 CMS 后台 |
| CMS 集合视图 `locale=*` 里 en 显示 `modified` | 跨语言聚合视图的展示差异，非真实草稿态 | 判发布态用**单 locale** 视图（`?locale=en`），那里 status 才是真值 |
| 英文课程页 404 | 英文是默认语言，**走无前缀根路径**（`/research/academy/<slug>/`），中文在 `/zh/…` | 按语言换路径验；别以为没生成 |

## 写作纪律速记（详见 xingyan/README.md）

读者=客户决策者与从业者；每条数字与断言对应 `sources` 可查证来源（做不到就删或标「待验证」）；宁短勿虚；不写 H1；步骤可复现、不依赖未公开环境；课程结构建议：学完能做什么 / 前置条件 / 步骤 / 自检练习 / 常见问题 / 下一步。
