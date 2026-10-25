# LongCat-Next 研究材料索引

本分支 `longcat-next/docs` 保存分析、审查、讲解手稿和本次会话的整理记录；生产代码位于 `longcat-next/code`，后续任务及上游投稿材料位于 `longcat-next/roadmap`。这些研究材料供个人 fork 使用，不作为上游模型支持声明。

研究基线：

| 对象 | 固定版本 |
| --- | --- |
| 2026-10-24 研究时的上游 main | `9bc166cd556cdaa4e0b18543da0c2def0076275e` |
| 上游 LongCat-Next PR #5299 | `c90ebc1d07ba8c0b583586a1eddf91f531047bce` |
| 官方 LongCat-Next-inference | `70ab100beecaaa77c1f45c0cf9ec89a4faf20fd8` |
| 官方 SGLang-FluentLLM submodule | `d97603b2ac3487c733d611d0456005ba3f23602d` |
| 官方 Omni-Flow | `b11524d2fd49ef63028fe1f672879d8007bc409c` |
| 本地四项旧改进基线 | PR 旧 head `3d610baa1db580590c0c347bb8c70357a7f6accb` |

材料：

- [模型和推理框架对比](analysis.md)：模块映射、请求状态、CFG、性能与 Ascend 边界。
- [已有提交审查](review.md)：最新 PR 与旧四项改进的去重、确定问题、反证和改进优先级。
- [讲解手稿](manuscript.md)：适合源码讲解与面试的叙述顺序。
- [会话整理](conversation.md)：用户问题原文摘录与回答摘要；不是原始工具日志或逐字全量导出。
- [代码验证](VALIDATION.md)：两个提交、基线失败/修复通过、实际验证边界与复验命令。
- [分支与交接](HANDOFF.md)：实际分支基线、推送结果和远端核对命令。

证据口径：

- “代码存在”“CPU 窄逻辑验证”“作者报告旧版本 GPU E2E”“最新版本 GPU E2E”“生产负载验收”分别记录。
- PR 作者报告 `986ade20` 在 4×A100-80GB 上通过三项离线 E2E、在线文本 smoke；不能用于证明 `c90ebc1d07ba` 或本 fork 改进版本已经通过。
- `426.49s` 是三项离线测试总耗时，不是单请求延迟。
- 当前没有完整的 SGLang / Omni 框架吞吐对比或本 fork 的 nsys trace。
- 本地旧 embedding 存储实验的 882 MiB/rank 是限定配置下的分配差，不是完整模型吞吐收益。

来源：[PR #5299](https://github.com/vllm-project/vllm-omni/pull/5299)、[官方模型](https://github.com/meituan-longcat/LongCat-Next)、[官方旧推理方案](https://github.com/meituan-longcat/LongCat-Next-inference)、[Omni-Flow](https://github.com/meituan-longcat/omni-flow)。
