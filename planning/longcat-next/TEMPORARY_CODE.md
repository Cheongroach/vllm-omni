# LongCat-Next 临时代码说明

这条分支是临时代码，保存在个人 fork 供审阅。两项局部修复已经实现，但 CFG 配对调度与完整模型验证尚未完成，不能据此视为生产可用。

说明更新：2026-10-26。代码分支：`longcat-next/code`。

## 已经改了什么

代码基于模型适配 PR #5299 的 `c90ebc1d07ba8c0b583586a1eddf91f531047bce`。它包含该模型的前置实现，因此不是可以直接独立合入当前 main 的两个小补丁。

| 提交 | 解决的问题 | 当前证据 |
| --- | --- | --- |
| `b56c2a94b` | 图像每个位置逐级生成 8 个离散码；每级排除特殊编号，合法编号 0 的保留帧继续使用视觉反馈 | 隔离 CPU 采样与反馈验证 |
| `53785219b` | 深度预测网络与已有缓存读取同一份只读码表，避免再复制一张表 | 隔离 CPU 查值与存储验证 |

16 项新用例在原代码上 10 项失败、6 项通过；修复后连同 56 项已有用例，共 72 项通过。这些测试用替身代替了部分运行时和深度网络，不覆盖完整 vLLM 初始化、GPU、多卡通信或媒体质量。

## 为什么还需要整改

CFG 生图需要组合有条件与无条件两路预测，两路各有历史缓存，却服务同一个用户请求。当前局部修复没有保证它们从创建到结束始终一起推进；缺少一方或处于不同生成步时，不应继续组合。

后续需要显式记录配对身份、同时满足两路资源、同步生成，并在结束、取消或出错时一起清理缓存与模型状态。通用 CFG 调度器与 LongCat 的 64K 上下文和每轮计算预算存在兼容性限制，不能只换一个类名或缩短上下文来代替验证。

原理与观察先看[CFG 阅读版](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/draft-cfg-lifecycle/planning/longcat-next/drafts/cfg-lifecycle-friendly.md)；实施入口、资源公式和验收条件在[技术草稿](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/draft-cfg-lifecycle/planning/longcat-next/drafts/cfg-lifecycle.md)。

这些代码与材料由 AI 辅助完成。目前尚未完成 CFG 生命周期升级，也未向上游作为正式贡献提交；后续状态应按真实运行时与真机证据更新。
