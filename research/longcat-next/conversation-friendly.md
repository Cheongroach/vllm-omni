# 这组材料在回答哪些问题

这是会话材料的阅读版，按问题之间的关系整理。完整用户问题摘录与前序回答摘要保留在 [conversation.md](conversation.md)，它本身也不是全量逐字日志。

## 同一个模型换框架后，为什么还需要核对

最初的问题是：

> 能说一下相对于官方SgLang实现，vllm-omni上的LongCat-Next有何异同，能否做一下benchmark、nsys等工具分析？是否支持Ascend机器？目前gh上的项目做了哪些适配工作？

需要分别核对模型计算规则、请求调度和性能。两边都处理图片与声音，不代表逐级采样、反馈、缓存和输出编号已经一致；配置里存在并行或计算图路径，也不代表已经测出性能优势。Ascend 的框架支持还要与具体 LongCat-Next 模型的验证分开。

这部分先读[模型与框架分析](analysis-friendly.md)。目前没有完成相同条件的框架吞吐对照或本 fork 的完整 nsys 分析。

## 已有适配哪些地方还需要改

用户继续询问模块对齐、当前成熟度，以及如何达到生产条件。为回答这些问题，前序工作核查了固定适配版本，并把“作者已修复的问题”与“仍成立的问题”分开。

仍成立的局部问题包括：高层视觉特殊码进入输出，合法 code 0 得到错误反馈，以及只读码表重复复制。个人 fork 已有两个提交处理它们，并获得隔离 CPU 回归支持。CFG 两路的完整生命周期仍待解决。

先读[审查阅读版](review-friendly.md)，再读[验证阅读版](VALIDATION-friendly.md)。后者解释 72 项通过的构成，以及为何这不能替代 GPU、真实权重和生成质量证据。

## 怎样把这项工作变成可审核的贡献

用户要求将代码、研究材料和后续计划分别保存在个人 fork：

> 区分不同的分支，包括
> a. 修改代码
> b. 分析文档、手稿、对话历史记录
> c. 后面进一步的todo，如何将代码贡献给vllm-omni，如何提高接受度，简历完整性等。

分支因此分成代码、研究、计划和设计草稿。代码依赖尚未吸收至调查 main 的模型前置；不应把整套适配作为两个局部修复重复投稿。后续贡献与简历表述需要对应实际已完成范围。

阅读[分支与交接](HANDOFF.md)，以及计划分支的[贡献阅读版](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/roadmap/planning/longcat-next/CONTRIBUTING-friendly.md)。

## 从局部修复怎样再提高工程完整性

后续问题转向 CFG 生命周期和“卡、模型、输入”的组合。它们有一个共同点：单个步骤正确，还不足以保证多个条件叠加后整体正确。

CFG 需要两个内部请求一直保持配对；资源组合需要区分真正新增的计算进程和复用进程。前序观察分别找到错步/缺配对行为，以及 FLUX.2 的 TP2+VAE2 计数差异。两者均已有问题证据和设计，尚未完成生产修复。

这两部分先读草稿分支的[组合周报](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/draft-cfg-lifecycle/planning/longcat-next/drafts/weekly-2026-10-25-combinations-friendly.md)与[CFG 阅读版](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/draft-cfg-lifecycle/planning/longcat-next/drafts/cfg-lifecycle-friendly.md)。
