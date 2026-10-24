# LongCat-Next 后续工作索引

`longcat-next/roadmap` 保存后续优化、投稿策略、issue/PR 草稿与简历证据要求。它不是已完成能力清单。

| 分支 | 内容 | 基线与用途 |
| --- | --- | --- |
| `main` | 同步上游代码 | 跟随 vllm-project/vllm-omni，不放研究或实验提交 |
| `longcat-next/code` | 视觉码正确性、embedding 共享及测试 | 固定 #5299 `c90ebc1d07ba`，保留模型依赖 |
| `longcat-next/docs` | 分析、审查、讲解、会话整理 | 个人 fork 材料，不混入代码 PR |
| `longcat-next/roadmap` | 本目录 | TODO、验收、贡献和简历计划 |
| 原 `longcat-next/improvements` | 旧四项改进 | 保留历史，不盲目叠加到当前 PR |

阅读顺序：

1. [TODO 与验收](TODO.md)。
2. [分支、issue、PR 与接受度](CONTRIBUTING.md)。
3. [issue 和 PR 草稿](DRAFTS.md)。
4. [简历与面试证据](RESUME.md)。

当前范围：先做局部视觉正确性与存储共享；CFG scheduler、在线生图/TTS、depth graph/TP 和 Ascend 分开推进。上游 PR 未合并时，不能从本代码分支直接向 upstream/main 开一个重复的全模型 PR。

本次实际基线：`docs` 已基于 `9bc166cd5`；`roadmap` 保留创建时的 `9f5521351`。对 roadmap 的 rebase 被自动审批以未明确授权历史改写为由拒绝，因此保留原历史。该分支只新增本目录材料，正文里的最新模型分析仍固定 #5299 `c90ebc1d07ba`；它不用于上游代码 PR。
