# LongCat-Next 研究材料索引

本分支 `longcat-next/docs` 解释模型怎样接入推理框架、发现了哪些问题，以及当前证据支持什么结论。代码在 `longcat-next/code`，后续计划在 `longcat-next/roadmap`；它们都是个人 fork 材料。

## 从哪里开始读

第一次阅读只打开：

- [一步步认识 LongCat-Next 与 vLLM-Omni 项目](一步步认识LongCat-Next与vLLM-Omni项目-friendly.md)

它跟随一次图像生成请求，按 62 步依次解释两阶段流水线、8 级 RVQ、两项局部修复、CFG pair、四卡布局和证据边界。默认读者已理解 Embedding、Attention、KV Cache 和常见并行，不重复这些基础知识。

读完主线后，再按问题查下面的专题材料。

| 想了解什么 | 先读阅读版 | 需要源码或历史细节时 |
| --- | --- | --- |
| 模型与框架怎样对应 | [模型分析](analysis-friendly.md) | [技术原稿](analysis.md) |
| 哪些问题值得修 | [审查](review-friendly.md) | [源码位置和反证](review.md) |
| 72 项通过意味着什么 | [验证](VALIDATION-friendly.md) | [完整结果与命令](VALIDATION.md) |
| 当前交付与分支在哪里 | [交接](HANDOFF-friendly.md) | [历史核对记录](HANDOFF.md) |
| 如何讲解这项工作 | [源码讲解手稿](manuscript.md) | 分析与验证原稿 |
| 这组材料如何回答用户问题 | [会话阅读版](conversation-friendly.md) | [问题摘录](conversation.md) |
| 怎样从小修复推进为系统贡献 | [工程升级](upgrade-friendly.md) | [原调查与环境限制](upgrade.md) |

阅读版文件带 `-friendly`，为第一次接触这项工作的读者先解释术语和例子。手稿与索引直接整理并保留原名；技术原稿保存精确证据与引用。

当前两项局部修复有隔离 CPU 回归支持；CFG 生命周期和卡/模型/输入组合改进仍是设计，GPU/真实权重/多卡质量与性能尚未完成验证。后两份阅读材料位于[设计草稿分支](https://github.com/Cheongroach/vllm-omni/tree/longcat-next/draft-cfg-lifecycle/planning/longcat-next/drafts)。

## 核对过的研究版本

下面的 SHA 固定研究对象，不表示今天在线仓库的最新版本。

| 对象 | 固定版本 |
| --- | --- |
| 2026-10-24 研究时的上游 main | `9bc166cd556cdaa4e0b18543da0c2def0076275e` |
| 上游 LongCat-Next PR #5299 | `c90ebc1d07ba8c0b583586a1eddf91f531047bce` |
| 官方 LongCat-Next-inference | `70ab100beecaaa77c1f45c0cf9ec89a4faf20fd8` |
| 官方 SGLang-FluentLLM submodule | `d97603b2ac3487c733d611d0456005ba3f23602d` |
| 官方 Omni-Flow | `b11524d2fd49ef63028fe1f672879d8007bc409c` |
| 本地四项旧改进基线 | PR 旧 head `3d610baa1db580590c0c347bb8c70357a7f6accb` |

## 怎样理解历史性能与测试记录

- “代码存在”“CPU 窄逻辑验证”“作者报告旧版本 GPU E2E”“最新版本 GPU E2E”“生产负载验收”分别记录。
- PR 作者报告 `986ade20` 在 4×A100-80GB 上通过三项离线 E2E、在线文本 smoke；不能用于证明 `c90ebc1d07ba` 或本 fork 改进版本已经通过。
- `426.49s` 是三项离线测试总耗时，不是单请求延迟。
- 当前没有完整的 SGLang / Omni 框架吞吐对比或本 fork 的 nsys trace。
- 本地旧 embedding 存储实验的 882 MiB/rank 是限定配置下的分配差，不是完整模型吞吐收益。

来源：[PR #5299](https://github.com/vllm-project/vllm-omni/pull/5299)、[官方模型](https://github.com/meituan-longcat/LongCat-Next)、[官方旧推理方案](https://github.com/meituan-longcat/LongCat-Next-inference)、[Omni-Flow](https://github.com/meituan-longcat/omni-flow)。
