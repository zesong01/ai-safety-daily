# AI 研究日报

网站：https://zesong01.github.io/ai-safety-daily/

手机优先，历史归档、主题筛选、浏览器本地收藏和原文链接。网页及所有前端资源均由 GitHub Pages 提供，无 ChatGPT 登录、Sites 域名或外部字体依赖。

## 自动更新

GitHub Actions 以北京时间 **09:00（UTC 01:00）** 为每日归档边界，全天每小时读取官方 RSS。GitHub 的计划任务可能排队延迟，不保证精确到分钟；公开仓库长期无人活动时 GitHub 可能暂停定时任务，请查看 Actions 状态。

每小时第 17 分钟同步来源。前一次检查不足 50 分钟且已上线时才跳过，空列表不会终止当天后续同步。读取范围为近 7 天至实际执行时刻：截止时间后的条目写入 `public/data/feed-cache.json`，下一期再归档，避免下午执行时 RSS 已换批而旧批次丢失；迟到条目补入原来的 09:00 窗口，不冒充今日新发布。暂存与历史在同一提交中保存。所有触发仍由 GitHub 调度，不能保证准点或绝不漏跑；手动 Run workflow 不受此跳过规则影响。

RSS 请求成功只代表读到了数据，不代表其中有当天公告。采集状态记录来源条目数、最新条目日期、被窗口排除数量，以及待下期归档数量。arXiv 官方说明周末通常没有新公告，合法空期保留并继续检查。

- 来源：METR、OpenAI、Google DeepMind、Cisco AI、arXiv cs.AI / cs.CR / cs.MA / cs.LG / stat.ML / cs.CL。
- 仅自动采集原文标题、短摘要和链接；不调用任何模型、不产生 API 费用、不生成新的中文分析。
- 原有两期中文简报保留。自动条目显式标记“未人工核验”。RSS 日期不等于事件日期；arXiv 公告日期不等于首次投稿时间。
- 按链接跨期去重；不将 arXiv replacement 当作新论文。各板块按时间轮流选取，目标每板块 30 条，单期总上限 120 条；跨板块文章只保存一次，因此某板块可能因交叉归类超过 30 条。截断数量在采集状态中记录。
- 部分来源失败会显示成功来源数；不足两个来源成功时任务失败，保留线上旧数据，不伪装成“没有新闻”。
- 历史数据提交在 `public/data/briefs.json`；先构建验证，再提交更新，在同一 workflow 中直接部署，避免 bot 推送不能触发后续 workflow 的问题。

手动刷新采集：**Actions → Collect and publish → Run workflow**，保持 collect 勾选。网页“刷新”只重新读取已发布数据，不会触发采集。

## 研究板块

网页可切换全部、Safety、Deep Learning、RL、基座模型研究，默认 Safety 并记住本浏览器的选择。板块筛选同时应用于当期列表、历史归档和收藏；研究/工程/政策仍是独立的内容类型筛选。

`scripts/topics.py` 对 RSS 原标题和完整摘要做关键词匹配，一篇文章可属于多个板块，不调用模型。Safety 覆盖安全/对齐/可控性；Deep Learning 覆盖神经网络/表征学习/扩散模型；RL 覆盖强化学习/策略优化/奖励模型；基座模型研究覆盖 LLM/VLM、预训练/后训练与规模规律。关键词分类可能误判或遗漏，不代表研究质量评价。旧简报保留 Safety 归属，新板块不会凭空补造历史内容。

更新流程：`.github/workflows/pages.yml` 定时启动 GitHub 的运行环境 → `scripts/collect.py` 读取 RSS、分类去重 → 写入 `public/data/briefs.json` 并提交历史 → 构建网页并部署到 GitHub Pages。GitHub 提供执行与托管，实际采集逻辑来自仓库代码。

## 本地开发

Node 24，Python 3.12（采集器仅用标准库）。

```sh
npm ci
npm run dev
python -m unittest discover -s tests
python scripts/collect.py --dry-run
npm run build
```

站点路径配置在 `vite.config.ts`，默认 `/ai-safety-daily/`。不要把任何 API key 或 GitHub token 提交到仓库。本项目不需要额外 Secrets。

## 验证范围

包含时间窗口边界、未知日期、危险链接、arXiv 修订和重复采集测试。部署成功以 GitHub Actions 和公开网址实际返回为准；本地验证不能证明所有中国网络运营商或地区均可访问 GitHub Pages。


## 2026-10-20 采集修复与历史补采

此前下午运行时，只读取截至当天 09:00 的条目；arXiv RSS 已切换到当天美东午夜公告（10 月为北京时间 12:00），新批次全部被排除，旧批次也已消失。仅根据“空期已发布”跳过后续运行进一步掩盖了问题。现在用上述暂存、回查和周期复查处理。

`python scripts/recover_arxiv.py --announcement-date 2026-10-16` 可从 arXiv 官方 recent 列表补采仍可查证的标题及公告日期，归入下一天 09:00 截止的简报。该恢复不假造摘要或原 RSS 时间，条目明确标注资料边界。recent 列表会滚动消失，无法保证任意久远日期可恢复。
