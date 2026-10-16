# AI Safety / Agent 每日资讯

网站：https://zesong01.github.io/ai-safety-daily/

手机优先，历史归档、主题筛选、浏览器本地收藏和原文链接。网页及所有前端资源均由 GitHub Pages 提供，无 ChatGPT 登录、Sites 域名或外部字体依赖。

## 自动更新

GitHub Actions 每天北京时间 **09:00（UTC 01:00）** 收录此前 24 小时官方 RSS 中与 AI Safety / Agent 相关的内容。GitHub 的计划任务可能排队延迟，不保证精确到分钟；公开仓库长期无人活动时 GitHub 可能暂停定时任务，请查看 Actions 状态。

每天 **09:17 至 18:17，每小时**额外检查公开网站。只有当天对应窗口的数据和至少两个成功来源已实际上线，才跳过；否则补跑采集并部署。检查网站超时也会尝试补跑。这样既能补偿漏掉的单次触发，也能恢复数据已提交但发布失败的情况。所有触发仍由 GitHub 调度，不能保证准点或绝不漏跑；手动 Run workflow 不受此跳过规则影响。

- 来源：METR、OpenAI、Google DeepMind、Cisco AI、arXiv cs.AI / cs.CR / cs.MA。
- 仅自动采集原文标题、短摘要和链接；不调用任何模型、不产生 API 费用、不生成新的中文分析。
- 原有两期中文简报保留。自动条目显式标记“未人工核验”。RSS 日期不等于事件日期；arXiv 公告日期不等于首次投稿时间。
- 按链接跨期去重；不将 arXiv replacement 当作新论文。当前单期最多保留 30 条，截断数量在采集状态中记录。
- 部分来源失败会显示成功来源数；不足两个来源成功时任务失败，保留线上旧数据，不伪装成“没有新闻”。
- 历史数据提交在 `public/data/briefs.json`；先构建验证，再提交更新，在同一 workflow 中直接部署，避免 bot 推送不能触发后续 workflow 的问题。

手动刷新采集：**Actions → Collect and publish → Run workflow**，保持 collect 勾选。网页“刷新”只重新读取已发布数据，不会触发采集。

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

