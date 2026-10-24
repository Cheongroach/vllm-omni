# LongCat-Next 本次会话整理

本文保留本线程的关键用户问题原文，并整理回答结论。它是“原文摘录 + 摘要”，不宣称逐字导出全部回答；不包含原始工具输出、环境变量或其他项目会话。

## 1. 官方实现、benchmark 与硬件

用户：

> 能说一下相对于官方SgLang实现，vllm-omni上的LongCat-Next有何异同，能否做一下benchmark、nsys等工具分析？是否支持Ascend机器？目前gh上的项目做了哪些适配工作？

回答摘要：

- 区分旧 NMM Infer/SGLang-FluentLLM 与官方后续 Omni-Flow。
- 模型结构基本对应，模块边界、head 计算、缓存、graph和多阶段调度不同。
- #5299 尚未合并，最新 head 未完成 GPU 复验；旧测试耗时不能作为框架 benchmark。
- 框架支持 NPU，但该 LongCat-Next 适配仍有 CUDA 依赖。
- 当前环境缺完整权重、兼容 runtime和 profiler，没有本轮端到端性能或 nsys 结果。
- 已准备文本测量、预检和 nsys wrapper；官方 HTTP 协议需要适配，准备工具不等于完成对比。

## 2. 模块如何对齐

用户：

> 简单说一下SGLang的模块以及vllm-omni如何对齐的，比如一致和有差异的地方

回答摘要：

InputProcessor 对应 multimodal processor/embedding；主干对应 FlashNgramModel；StateMachine 对应按请求维护的状态；OutputProcessor/Sample 对应 talker_mtp；PostProcessor 对应 combined decoder。

一致的是建模目标、层级码依赖和 CFG 公式；差异是计算时序、模块归属、调度和优化。数值一致仍需要相同前缀下的逐级对齐。

## 3. 成熟度与理想形态

用户：

> 现在实现的情况怎么样？不同的模型适配有什么差距，怎么到完美形态

回答摘要：

LongCat-Next 处于主要功能已接入、工程闭环不完整的阶段。不同模型的支持矩阵、流式、graph、质量测试和硬件覆盖并不一致。理想形态应以声明的任务/硬件/负载范围验收，而不是无限功能清单。

路线为最新 E2E → 质量对齐 → 请求/CFG契约 → 服务接口与流水线 → profiling驱动优化 → NPU及持续回归。

## 4. 生产条件与部分支持

用户：

> 为了达到vllm-omni的生产条件，是如何把控的？比如需要支持什么完整功能？
> 如果未能完全支持，是常态吗？要如何补充？

回答摘要：

PR 合并、版本发布和具体业务生产验收分别判断。仓库 L1/L2侧重逻辑及流程，L3/L4增加真模型质量、性能和功能，L5覆盖持续运行和故障；不能假定每个模型/平台都统一跑完。

部分支持是常态。应按任务/API/硬件/配置声明支持矩阵，未支持的路径明确拒绝；范围内的串请求、质量错误和故障挂死不能接受。graph、量化、prefix cache和 Ascend按实际承诺决定是否必需。

## 5. 同步 fork、代码、文档与后续计划

用户：

> 1. 将vllm-omni 同步一下。然后将需要的代码提交到`https://github.com/Cheongroach/vllm-omni`。这是我的fork。
> 2. LongCat-Next进一步的优化，策略，计划，提交到fork。
> 区分不同的分支，包括
> a. 修改代码
> b. 分析文档、手稿、对话历史记录
> c. 后面进一步的todo，如何将代码贡献给vllm-omni，如何提高接受度，简历完整性等。
> 3. 锐评一下，已有的longcat-next提交的问题，看看如何在这个基础上进一步修改。介绍一下怎么配置分支、提issue和pr等。

执行安排：

- `longcat-next/code`：基于当前 #5299，独立视觉正确性与 embedding 存储提交。
- `longcat-next/docs`：本目录的研究、审查、手稿与会话整理。
- `longcat-next/roadmap`：TODO、贡献流程、issue/PR 草稿、验收与简历表述。
- 原有旧改进分支保留；尺寸和请求映射等已吸收的修复不再叠加。

## 6. 审查中的重要更正

两名独立复核者确认：

1. 高层视觉 sentinel不属于有效量化码，但真实物理表有额外行，不能声称必然数组越界。
2. code 0 是合法视觉量化索引，其反馈不能替换为文本。
3. embedding clone造成的是重复常驻存储；FP32过渡影响初始化峰值，不是持续泄漏。
4. CFG正常公式不保证调度语义：root-only批次可能无告警退化普通采样。

这些更正已纳入[审查报告](review.md)，后续材料应沿用收窄后的表述。
