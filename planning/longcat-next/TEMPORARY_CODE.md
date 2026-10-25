# LongCat-Next 临时代码说明

> **TEMPORARY / 临时代码：仅保存在个人 fork，供仓库所有者审阅。需要后续整改与完整验证，不是正式上游提交，也不是生产可用性声明。**

更新日期：2026-10-25。代码分支：`longcat-next/code`。

## 已上传范围

基于上游 LongCat-Next 适配 PR #5299 的 `c90ebc1d07ba8c0b583586a1eddf91f531047bce`，保留两项局部修复：

| 提交 | 内容 | 证据边界 |
| --- | --- | --- |
| `b56c2a94b` | 视觉 RVQ 每级屏蔽特殊码，保留合法 code 0 的反馈 | 隔离 CPU 模型逻辑验证 |
| `53785219b` | 共享 depth embedding 存储，减少重复权重存储 | 隔离 CPU 存储与行为验证 |

既有隔离 CPU 回归共 72 项通过；完整 vLLM runtime、真实权重、GPU、TP 和媒体质量尚未验收。此分支包含 PR #5299 的前置代码，不是从当前 main 可直接独立合入的两个补丁。

## 后续整改

1. 补齐 LongCat-Next CFG 显式配对身份、原子准入和同步推进，禁止缺伴随流或不同逻辑步的两路 hidden 被组合。
2. 核验 EOS、length、cancel、error 等整对终止路径，以及 KV、模型状态、输出路由和引擎注册表清理。
3. 解决通用 CFG scheduler 与 LongCat 64K 上下文、token 预算、KV group 的兼容性，不能只加 scheduler 类或静默缩短上下文。
4. 在真实 runtime 和 GPU/TP 下验证，再与同权重参考实现比较媒体质量及并发性能。

详细设计位于个人 fork 的 `longcat-next/draft-cfg-lifecycle` 分支：
[CFG 生命周期草稿](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/draft-cfg-lifecycle/planning/longcat-next/drafts/cfg-lifecycle.md)。

**CFG 生命周期升级尚未实现。** 两项局部修复与设计草稿进入个人 Git 历史，不代表升级完成或允许上游发布。本说明按仓库所有者要求添加；代码与文档由 AI 辅助完成，后续整改和验收状态应随实际证据更新。
