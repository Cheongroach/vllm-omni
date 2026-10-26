# LongCat-Next 后续工作索引

本目录说明两项局部修复之后应该做什么、如何验证，以及哪些成果可以用于投稿和简历。下面的计划不代表已经完成。

## 从问题进入材料

| 想解决什么 | 阅读版 | 技术细节 |
| --- | --- | --- |
| 下一步先做什么、怎样验收 | [优化计划](TODO-friendly.md) | [入口与详细矩阵](TODO.md) |
| 个人 fork 怎样贡献上游 | [贡献流程](CONTRIBUTING-friendly.md) | [命令与检查项](CONTRIBUTING.md) |
| 每份英文草稿希望审核什么 | [草稿说明](DRAFTS-friendly.md) | [英文投稿原稿](DRAFTS.md) |
| 当前成果怎样写进简历 | [简历阅读版](RESUME-friendly.md) | [证据表与追问](RESUME.md) |

当前已有视觉正确性和只读存储修复的隔离 CPU 证据；CFG 成对调度、真实模型质量、在线能力、性能和 Ascend 分别需要后续验证。最新 CFG 与组合设计见[草稿分支](https://github.com/Cheongroach/vllm-omni/tree/longcat-next/draft-cfg-lifecycle/planning/longcat-next/drafts)。

## 分支各自保存什么

| 分支 | 内容 | 基线与用途 |
| --- | --- | --- |
| `main` | 同步上游代码 | 跟随 vllm-project/vllm-omni，不放研究或实验提交 |
| `longcat-next/code` | 视觉码正确性、只读存储共享及测试 | 固定 #5299 `c90ebc1d07ba`，保留模型依赖和临时说明 |
| `longcat-next/docs` | 分析、审查、讲解、会话整理 | 个人 fork 材料，不混入代码 PR |
| `longcat-next/roadmap` | 本目录 | TODO、验收、贡献和简历计划 |
| 原 `longcat-next/improvements` | 旧四项改进 | 保留历史，不盲目叠加到当前 PR |

上游尚无模型前置时，代码分支不能作为两个小补丁直接向 main 投稿，否则差异会包含整套适配。投稿前需重新核对届时版本。

研究分支创建基线为 `9bc166cd5`，计划分支保留 `9f5521351`。前序计划分支的 rebase 被自动审批拒绝，因此没有改写历史；这不影响文档中固定 #5299 `c90ebc1d07ba` 的模型分析。文档更新继续追加提交。
