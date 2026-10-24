# 优化计划与验收

基线：#5299 `c90ebc1d07ba`。状态日期：2026-10-24。下面的性能和质量阈值是建议的验收门槛，不是实测结果；具体服务 SLO 要在目标硬件、负载和使用方需求确定后冻结。

## 先修正确性，再做并发与性能

| 阶段 | 交付与入口 | 验收 | 状态 |
| --- | --- | --- | --- |
| P0 局部正确性 | `modeling_longcat_next.py` 普通/CFG depth sampling；每级排除 sentinel，code 0 保留视觉反馈 | sentinel 为最大 logit 时所有级别仍合法；code 0/nonzero、像素/换行、普通/CFG 各分支符合契约 | 代码分支实现；隔离 CPU 验证，完整运行时待验证 |
| P0 存储 | `_ensure_*_code_embed_module` 与 replicated buffer 共用冻结 storage；取消 FP32 中间转换 | 两模态、FP32/BF16，lookup 数值不变、同 storage、重复调用幂等；GPU 对照初始化峰值和稳态显存 | 代码分支实现；CPU storage 验证，GPU 数据待采 |
| P1 CFG 生命周期 | prompt 展开时保存 pair ID/role；调度器成对 admission、prefill/decode 就绪、abort、preemption、完成 | cond/uncond 每级共用码；错步不能静默普通采样；root-only/twin-only、不同行顺序、取消一方、KV 压力、重入均覆盖 | 待 RFC；不能靠 batch 字典或 `max_num_seqs` 解决 |
| P1 请求与 payload | runner、`make_omni_output`、stage handoff；确认当前 head 已有修复并扩充集成测试 | text/audio/image 同批、行顺序交换、chunked prefill、请求取消/复用，payload 严格对应 request ID | 源码已有多项修复；真实并发待测 |
| P1 质量 | 固定权重/processor/seed/参数，与官方参考推理逐步对比 | greedy 下强制 token、保留帧数量、RVQ 范围完全一致；比较每级 logits/embedding 误差与首个分歧；采样质量另做统计 | 待完整权重与 GPU |
| P2 服务 | 已有通用 API/部署 YAML 扩展在线 T2I/TTS；不新增模型专属 Python 客户端 | 有效媒体、尺寸/采样率/格式、错误传播、取消、timeout、背压；功能声明有测试对应 | 待 API 范围确认 |
| P2 性能 | rank-0 depth head Python 循环，逐级 batch，固定形状 graph，重复历史管理 | 同一质量与负载，比较端到端 P50/P95/P99、每帧耗时、req/s、显存和失败率 | 待 profiling；逐级因果约束不可破坏 |
| P3 平台 | TP/PP 契约、Ascend 算子/通信与精度单独验证 | 完整模型加载、collective 无死锁、KV/decoder 布局正确、同平台参考质量对照 | 未完成；不宣称 NPU 生产支持 |

Depth head 的 8 级 RVQ 是逐级条件预测：第 l 级依赖前 l 级的码 embedding。可以并行不同请求、批量同一级别或捕获固定循环，不能把 8 级改成互相独立的预测。

CFG 合并 `u + s(c-u)` 只在两路 hidden 对应同一步时有意义。优先讨论成对调度；如果当前 runtime 暂不支持，应明确拒绝该配置或提供公开、可观测的降级策略。延后一步再同步计数不能修复已经不同的 KV 历史。

## 从适配走到可服务

生产支持应按能力声明；未覆盖完整功能很常见，但需要有明确边界、失败方式、测试、owner 和后续计划。

| 能力 | 最低验收 | 测试层 |
| --- | --- | --- |
| 文本/图像/音频输入 | processor、特殊 token、长度/多输入处理一致 | L1 + GPU L2 |
| 图像/音频输出 | decoder 收到合法 RVQ、图像 `(token_h, token_w)`、音频 chunk boundary | L1 + 真模型 L2 |
| 并发与状态 | request ID 唯一映射；取消/异常后清理；CFG 原子就绪 | runtime 集成 + 压力 |
| 精度与质量 | 与同权重官方参考对照，量化/TP 单列 | Accuracy |
| 性能 | 负载、模型、硬件、版本固定；统计分位数和有效吞吐 | Perf |
| 服务 | endpoint/schema、错误码、媒体、timeout、监控、回滚 | Online L2 + reliability |
| 部署 | 文档命令可执行，显存预算含 N-gram 与 replicated 表 | Doc + cold-start |

建议实验矩阵：CFG 1/3；并发 1/2/4/8；单图/多图及非方形网格；文本+音频+图像混合；短/长上下文；TP=1/2/4（资源允许时）；正常完成/主动取消/超时/KV 压力。先用少量确定性用例找契约错误，再扩大随机负载。

## 测量协议

1. 固定上游及 vLLM SHA、权重 revision、GPU/驱动、dtype、TP/PP、输入集、seed、CFG/采样参数。分别报告冷启动与预热稳态。
2. 每个性能配置至少三次独立运行，记录样本数、均值及分位数；候选方案与 baseline 交错运行，减少环境漂移。
3. 图像报告尺寸/帧数与有效输出率；音频报告采样率、时长、实时因子、chunk 延迟；统一报告失败、取消和重试比例。生成 token/s 不能替代有效媒体吞吐。
4. 显存记录实际初始化了哪些表和哪些 stage。目标 storage 少一份表；BF16 hidden=3072 时理论减少 `(131072+19456)*3072*2 = 924844032 bytes = 882 MiB/rank`。这是条件化计算，不能写成端到端实测。
5. 建议性能门槛：候选有效吞吐提高至少 10%，P95 不回退超过 5%，显存不高于 baseline，质量无统计显著退化；冻结基准后再定最终阈值。正确性必须零非法码、零串请求，不能用吞吐抵消。
6. 拿不到完整运行时/GPU 时只发布实际完成的 L1 证据，并记录未测矩阵，不把预检、启动或排队当成验收。

## 提交顺序

- 第一批：视觉码正确性，测试先复现再修复。
- 第二批：storage 共享，证明字节数/数值；完整 GPU 权重路径验证后再写显存实测。
- 第三批：CFG RFC 与测试计划，先对齐 pair 生命周期和调度职责，再实现。
- 第四批：在线能力与质量/性能套件，按独立验收拆 PR。
- 第五批：depth batching/graph、TP/PP、NPU。只有测出瓶颈和收益后推进。
