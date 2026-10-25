# [DRAFT / 非正式] LongCat-Next CFG 生命周期升级方案

> **状态：草稿，待仓库所有者审阅。仅上传个人 fork；不是正式 RFC、上游 PR、实施承诺或已完成能力声明。**
>
> 本轮完成调查和两个隔离 CPU 复现，尚未开始升级代码。优先指标、服务对象、实施范围和验收条件待审阅确定。

日期：2026-10-25。方案来源：LongCat-Next 适配审查与工程提升调查。此文不提交给上游维护者，不请求上游 CI admission 或合并。

## 当前结论

从两项局部补丁提升到较完整的主流工程贡献，建议交付 LongCat-Next CFG 请求生命周期：身份传递 → 成对准入 → 同步生成 → 整对终止 → 资源清理，并取得对应运行时和真模型证据。单独增加错误断言或测试数量不足以证明达到这一层次。

代码基线：个人 fork `longcat-next/code`，`53785219b3c087f9e498ca2ed07088c9407fe037`；模型依赖上游 #5299 `c90ebc1d07ba8c0b583586a1eddf91f531047bce`。草稿分支基于 main `dca119877bd420ee0abc117e637eeac7aa28e4dd`，与代码基线分开保存。

## 已执行的复现

使用隔离 CPU harness，直接调用生产 `LongcatNextForCausalLM.talker_mtp`，复用现有 fixture，确定性 head 输出合法码 7。运行时导入、TP 和 head 用 stub；不覆盖真实 scheduler/GPU/权重。

| 输入 | 应有行为 | 实际行为 |
| --- | --- | --- |
| `_visual_gen` 中父/伴随流都存活，只调度父请求；两者 step=4 | 等待或对该请求明确失败，不能独立推进 CFG | 输出 `[[7,7,7,7,7,7,7,7]]`；父历史增加一帧，伴随历史仍为空 |
| 同批父 step=9、伴随 step=2 | 检出逻辑步不一致，禁止组合这两路 hidden | 输出两份共享码，并将伴随 step 覆盖成 9 |

这证明模型 hook 的分支存在错误行为；没有证明真实 GPU scheduler 在特定负载下触发该路径的概率。同步计数不能修复已经不同的 KV 和反馈历史。

## 已有能力应复用

代码基线已存在 `vllm_omni/core/sched/omni_cfg_ar_scheduler.py::OmniCFGARScheduler`，Breeze-TTS 使用它。它提供成对准入、按真实 prompt 长度比较生成进度，以及显式取消时扩展到整对请求。

LongCat-Next 的 pipeline 目前未选择该 scheduler，扩展 prompt 返回裸字符串，父/伴随请求没有 `cfg_group` 元数据。模型通过 batch 中的 `__cfg_visual` suffix 推断配对，因此父请求单独出现时无法识别缺配对。

通用 scheduler 当前要求 FCFS、同步调度、完整 prefill、关闭 prefix cache、无 speculative decoding/KV connector，以及一个 KV group。不能把“一个 group”等同于已经核验该 group 的 full-attention/MLA 契约。

不能只增加 `scheduler_cls`：

- LongCat 默认 `max_model_len=65536`、`max_num_batched_tokens=8192`；现有 scheduler 要求后者至少为前者的两倍，直接接入会启动失败。
- constructor 按两个最大上下文预留容量，可能拒绝可以容纳实际短 prompt + 生成预算的配置。
- 现有单元测试替换了父类 `schedule`，不能证明真实 vLLM 调度与块分配行为。
- 常规 EOS/length/error 通过 `update_from_output → _free_request` 清理；只覆写 `finish_requests` 不能证明这些终止路径也整对清理。
- companion 构建、父 admission、replica affinity、模型 request ID 与引擎 UUID，需要沿生产路径核验。

## 工程难点与具体落点

| 难点 | 必须解决的契约 | 实施入口 |
| --- | --- | --- |
| 请求身份 | parent/uncond 角色显式传递；外部 ID、内部 UUID 和 pair 身份保持一致；metadata 丢失及时发现 | LongCat stage input processor、pipeline prompt transform、engine request upgrade |
| 数值时序 | 保留每一路真实 position；对齐 `computed - prompt_length`，避免回滚或改写计数掩盖不同历史 | scheduler；model preprocess/talker validation |
| KV 资源与公平性 | 两路准入要同时满足 slot、token、page；已接纳对有足够生成容量；不让后来的单请求反复挤占导致饥饿 | 通用 CFG scheduler，真实 KVCacheManager/BlockPool |
| 终止与取消 | 任一路取消、EOS、length、超时或错误都必须形成一致终态；不向客户端伪报成功；无残留 KV/registry | finish_requests、update_from_output、orchestrator cleanup |
| 失败隔离 | 丢配对/错步不得静默普通采样；请求错误应传给客户端，不能无意崩溃整个 engine | admission 验证、request-local terminal outputs、模型最后一道 invariant |
| 性能与质量 | 逐级 RVQ 因果关系不变；调度改进不能只用 token/s 评估；比较有效媒体吞吐和尾延迟 | reference parity、并发 workload、profiling |

## 建议实施方案

1. 审阅后从 `longcat-next/code` 创建 `longcat-next/cfg-lifecycle`，保留两项旧补丁。新增提交按身份/配置、调度生命周期、集成验证拆分；本草稿分支只保存文档。
2. 父/伴随提示都使用结构化 metadata，携带 `cfg_group`、role、网格和 CFG scale；CFG=1 或无需展开的请求保持单流。明确 prompt transform 与 original prompt 的边界，不能依赖修改调用者对象才能生效。
3. 复用并修正通用原子 CFG scheduler 的必要契约。按请求的实际终止预算计算页数：

   `L_i = min(max_model_len, prompt_length_i + max_tokens_i)`

   `R_pair = ceil(L_cond / block_size) + ceil(L_uncond / block_size)`

   单个 group 的可用页须扣除 null block、watermark 和实际尚占用的页。不能把此公式直接推广到 hybrid/sliding-window/cache offload；这些配置需明确拒绝或单独适配。

4. 保留 LongCat 原有 max context，不把 64K 静默降成 4K 来规避约束。完整 prefill 的两路 token 总量超过配置预算、单对永远不可能放入 KV/slot 时，给明确错误；不永久留队。是否进一步支持 chunked prefill，应作为有独立验收的后续能力。
5. 等待 companion 期间禁止父独立 decode；等待有明确 deadline。错误路径在请求层处理，model 检查作为最后一道防线。已经独立推进的 KV 不尝试只靠计数同步恢复。
6. 覆盖常规输出终止与显式取消，而不只覆写 `finish_requests`。终止后模型 N-gram/视觉状态、scheduler pair registry、orchestrator companion registry、KV 页面和输出路由应一致清理。
7. 部署与文档声明同步调度、FCFS、prefix cache、KV group 等当前限制。Breeze 已有消费者，通用 scheduler 修改必须回归它。

以上需结合最新运行时接口和审阅意见落实，不能直接把设计当作已实现能力。

## 验收矩阵

| 层次 | 场景 | 必须有的证据 |
| --- | --- | --- |
| L1 模型契约 | root-only/twin-only、行顺序交换、step/grid 不一致、code 0、新行/末尾 | 基线失败/候选通过；调用实际生产方法 |
| L1 metadata | 字符串/字典输入、CFG=1/3、父/伴随 UUID、网格传递、malformed prompt | 穿过生产序列化、request upgrade 与扩展路径 |
| CPU runtime | 多对 + 普通请求、slot/token/KV 压力、不同 prompt 长度、EOS/length/cancel/超时、ID 重用 | 实际 vLLM Request、scheduler、KV manager/BlockPool；不能替换 base schedule |
| GPU 结构验证 | 实际 runner、页表/collective、同级逐级 head、取消与后续请求 | terminal artifacts；小模型只能证明 runtime 部分 |
| LongCat 真模型 | 单对/多对、非方形 grid、混合请求；官方同权重参考对照 | 合法帧数、每级 logits/反馈误差、首个分歧与媒体结果 |
| 性能 | 相同质量/负载、冷启动和稳态、至少三次对照 | 成功率、有效 req/s、P95/P99、显存、取消恢复时间 |

正确性门槛：零独立 CFG 推进、零串请求、整对终止可解释、资源回收无残留。性能门槛需在选定工作负载后冻结，不能编造通用绝对 SLO。

满足模型契约 + 真实 runtime 闭环，可称“更完整的系统原型”；加上 LongCat 真机质量、并发和可复现性能证据以及上游吸收，才能较有把握称“主流工程贡献”。SOTA 仍需要明确任务上的领先结果。

## 当前验证边界

- 本地测试环境包含 vLLM 0.29.0、torch 2.9.1，CUDA 不可用。
- 直接运行 `tests/core/sched/test_omni_cfg_ar_scheduler.py` 在收集时失败：`ImportError: cannot import name 'ALLOWED_LAYER_TYPES' from 'transformers.configuration_utils'`。没有进入测试，不能记录为通过或 scheduler 根因。
- 尚无可复用的 GPU Worker；当前完整部署需要 4×80GB 级别资源。小 GPU runtime 实验可另做，但不能替代 LongCat 真机验证。
- 尚未开始本方案的代码实现、部署修改或真机验收。本文由 AI 辅助调查和起草，待人类审阅。

## 待审阅的问题

| 问题 | 草稿建议 | 审阅状态 |
| --- | --- | --- |
| 希望达到什么结果？ | 从局部修复推进可验证的 CFG 并发生命周期 | 待明确可交付范围 |
| 最优先改善哪个指标？ | CFG 并发正确性与故障后资源回收 | 待审阅 |
| 通过什么机制改善？ | 显式配对身份、原子准入/推进、整对终止和清理 | 待审阅 |
| 服务谁的什么需求？ | 使用 LongCat 生图的部署与推理用户，希望并发时质量稳定、取消可恢复 | 待审阅 |

这些是草稿建议，不是已由人类贡献者确认的答案。正式实施或上游投稿前，应按当时的 `CONTRIBUTING.md`、`precheck-pr` 和 PR template 核对贡献意图、AI 披露与验证要求。

欢迎逐条指出范围过大、遗漏场景、容量预算问题或验收门槛不合理之处。收到审阅反馈后先更新文档，再确定是否开始实施。
