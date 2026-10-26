# [非正式小周报] vLLM-Omni 的硬件、模型与输入组合

首次阅读可从[组合周报阅读版](weekly-2026-10-25-combinations-friendly.md)开始。本文件保留调查日志、完整设计和固定源码引用。

> 记录日期：2026-10-25。状态：个人 fork 调查记录与改进设计，待审阅；不是正式 RFC、上游 PR 或已实现能力声明。本文由 AI 辅助调查和起草。
>
> 本次核对 main `dca119877bd420ee0abc117e637eeac7aa28e4dd`。LongCat-Next 的旧局部修复另在 `longcat-next/code`，其模型前置来自 #5299；不能把该分支能力算作当前 main 已支持。

## 本次产出

梳理了平台选择、模型流水线、并行配置、请求输入和 CI 选择五个入口；通过隔离 CPU 调用确认一处测试资源计数差异：FLUX.2 的 TP=2、VAE patch=2 被测试 helper 算成 4 卡，而生产配置得到 2 个 worker。形成“复用现有配置入口，补组合约束与实际生效证据”的方案。尚未修改生产调度或测试资源推导，没有 GPU 性能结论。

这里的“乘法组合”指硬件后端/SKU/显存/互联/软件栈 × 模型版本与执行路径 × 并行与部署配置 × 输入模态/形状 × 并发、缓存、流式及终止行为。各维度之间有约束，可行组合只是笛卡尔积的一个子集；卡数本身也不能把所有并行参数直接相乘。

## 现在如何处理

| 层次 | 当前机制 | 能保证什么、仍有什么边界 |
| --- | --- | --- |
| 硬件 | CUDA、ROCm、NPU、XPU、MUSA 插件检测；选择 worker、attention backend、平台补丁 | 同一进程选择一个 OmniPlatform；backend 还检查 SM、head size 和依赖包。不是自动把 CUDA+NPU 编成一个异构 mesh。[cite:1](#source-1) |
| 模型 | `OMNI_PIPELINES` / diffusion registry 解析模型，`PipelineConfig` 固定 stage 拓扑 | 定义 thinker/talker/decoder、输入来源、最终输出和转换 hook；注册成功不证明任意卡、任意输入、任意并行都有效。[cite:2](#source-2) |
| 部署 | deploy YAML 的平台覆盖，再合并用户配置、strategy 和 CLI | 同一个模型在不同平台可以有不同卡布局和 eager/graph 设置；Qwen2.5-Omni 默认 stages 使用卡 `0,1,0`，NPU 覆盖为 `0,1,2`。三个 stage 不等于三张独占卡。[cite:3](#source-3) |
| 并行 | `composable_parallel` 叠加 TP/DP/PP/EP/stage replica；diffusion 有独立 `DiffusionParallelConfig` | 前者目前仅翻译五类轴，SP/CFG/HSDP 等仍是保留轴；扩散运行时能走自己的相关配置。两者不能混称已统一接通。[cite:4](#source-4) |
| 输入与生命周期 | 服务端 metadata、模型 processor、stage 输入转换、request affinity | diffusion metadata 声明参考图上限、混合参考和输出类型；StagePool 保存 request→replica，并允许 companion 继承 affinity。形状与状态约束仍分布在具体实现中。[cite:5](#source-5) |
| 验证 | 人工定义模型/加速组、任务 subtests、硬件/card markers、L1–L5 与源码依赖过滤 | 复用实例减少启动成本；没有穷举全部组合。CI 配置存在、被选中、实际执行、质量合格是不同状态。[cite:6](#source-6) |

AR 通用策略中的单 engine world 为 `TP × DP × PP`，stage replica 是独立 engine 数，EP 复用 TP×DP rank。`check_device_layout` 接受单副本模板或整个副本池的卡数，但这项检查不证明物理卡可见、显存充足或跨 stage 放置安全。[cite:4](#source-4)

扩散的常规 world 为 `PP × DP × TP × SP × CFG`，其中 `SP = Ulysses × Ring × AllGather`。EP、VAE patch 和 text encoder TP 不再分别增加 world；HSDP 单独使用时决定 world，组合时覆盖已有 rank，并要求维度一致。HSDP 当前不兼容 TP、DP>1、PP>1 或 EP；Ring>1 与 AllGather>1 也被明确拒绝。[cite:7](#source-7)

支持模型表主要表达“模型×后端”，部分勾选来自已审计 recipe，其他保留实现支持 metadata；它没有穷举 SKU、软件栈、输入形状和所有加速开关。表中空白表示未列为支持，不能直接推导成已证实不支持。[cite:8](#source-8)

## 遇到的问题与处理日志

本表记录本次调查及明确引用的前序观察，不虚构一周内的逐日实验。

| 问题/触发 | 证据与影响 | 本次处理、剩余状态 |
| --- | --- | --- |
| 并行参数全相乘会错算资源 | `Flux2Pipeline` 配置 `[TP, VAE_PATCH]`；helper 算 4，生产 config 算 2。VAE 文档及 wrapper 明确复用 DiT rank。[cite:7](#source-7)[cite:9](#source-9) | 隔离执行原源码定义确认差异，保留复现脚本；生产修复待做。可能多占测试卡、让 2 卡 lane 未选择该用例；本次未测实际队列浪费。 |
| 功能开关存在，未必生效 | SP hook 没有 plan 或安装异常时会 warning 后继续；部分模型 cache 会被关闭，compile 失败也可回退。[cite:10](#source-10) | 记录 requested/effective 不一致的入口；未据此声称所有 fallback 都错或已复现媒体错误。建议明确必需能力与可选加速。 |
| 同名 CFG 隐藏不同契约 | 扩散 CFG 是卡间 guidance 分工；LongCat AR CFG 是两个带独立 KV 的请求流。前序隔离 hook 调用中，父单独推进、两路 step=9/2 被组合并覆盖计数。[cite:11](#source-11) | 已形成显式身份→原子准入/推进→整对终止设计；尚未实现。StagePool affinity 只能保证落点，不能替代 engine 内成对调度。 |
| 测试等级与权重等级混淆 | 当前 `case_filtering` 多卡组标 `full_model`，nightly 却传 `--run-level core_model`，因此仍用 tiny weights。[cite:6](#source-6) | 区分 job 等级、资源、权重种类；本次统计 16 个模型、51 个离线配置组、16 个默认在线基础组，只是参数表数量。 |
| 基础输出通过会漏交互 | common tests 用 eager；determinism/multi-output 默认仅基础组；online 默认不跑额外加速组。[cite:6](#source-6) | 确认这是控制实例启动成本的既有取舍；建议补少量形状、排序、缓存与取消交互，而非重复全部在线组合。 |
| 本地完整导入受依赖阻塞 | 前序完整 pytest 收集报 `ALLOWED_LAYER_TYPES` 导入失败；本次 harness 初稿也因 AST 提取的 decorator namespace 绑定错误而失败。[cite:11](#source-11) | harness 改为分别保留 vLLM config decorator 与生产 class 的 namespace 后运行成功。仅验证配置关系及 helper，不替代完整 runtime/GPU 验证。 |

隔离执行结果如下，使用 Python 3.11.2、Pydantic 2.11.7，保留生产 `DiffusionParallelConfig`、validator、测试 helper 原定义；从本地 vLLM 0.29.0 源码提取真实 `config` decorator，避开其他 runtime import：

| 配置 | 测试 helper 要求 | 生产配置结果 | 结论范围 |
| --- | --- | --- | --- |
| FLUX.2 现有 TP=2、VAE patch=2 用例 | 4 卡 | world=2 | 资源估算与生产配置不一致；未运行 VAE collective |
| TP=2、CFG=2 | — | 接受，world=4 | 配置合法；未证明任意模型支持 |
| Ulysses=2、HSDP shard=2 | — | 接受，world=2 | HSDP 覆盖已有 rank |
| TP=2、HSDP shard=2 | — | 拒绝：不兼容 TP | 现有校验工作，不需要新增同义规则 |
| Ring=2、AllGather=2 | — | 拒绝：不支持该组合 | 现有校验工作，不需要新增同义规则 |

复现支持文件：[combinations_probe.py](combinations_probe.py)。其统计范围仅 `DIFFUSION_TEST_SETTINGS`，不代表全仓库模型数、pytest 收集数、已执行数或已通过数。运行命令：

```bash
python3 planning/longcat-next/drafts/combinations_probe.py \
  --repo-root /path/to/current-main-checkout \
  --vllm-utils /path/to/site-packages/vllm/config/utils.py
```

## 从组合问题出发的改进设计

### 1. 共用资源推导，先交付一个可验证的小改动

第一步收敛到 diffusion 测试资源估算：将 acceleration→config 的现有映射交给生产 `DiffusionParallelConfig` 推导 worker world，分别描述新建 rank 的轴与复用 rank 的轴。VAE 是已有 DiT group 的需求，不能独立相乘；HSDP 也不能再乘一次。仅拿 `max(所有并行度)` 同样错误：TP=2、CFG=2 仍需要 4 个 worker。

资源计划应分别输出 `worker_world`、`component_group_requirements`、`stage_replica_count` 和物理 `placement`。共享卡多 stage 的显存预算另算；world_size 只是进程/rank 数，不能保证显存 fit。VAE 独立 degree=2 而 world=1 的配置，应显示无法达到请求的并行度或明确 fallback，不能靠测试多申请一张卡掩盖生产没有创建 worker。

验收：FLUX.2 TP2+VAE2 归入 2 卡测试；TP2+CFG2 保持 4 卡；HSDP overlay 不重复计数；现有非法组合仍被拒绝。真正使用了两路 VAE、结果排序及误差需后续 GPU 用例证明。当前仅有发现与方案，未提交此修复。

### 2. 在现有 resolver 上增加分阶段能力检查

复用 `config.resolver`、`StageConfigFactory` 和轻量 model metadata，不另建一套平行的模型注册体系。给约束增加稳定 rule ID、适用范围、执行阶段和理由；实现支持声明与实测证据分开存。[cite:2](#source-2)[cite:4](#source-4)[cite:5](#source-5)

| 阶段 | 可取得的信息 | 检查与输出 |
| --- | --- | --- |
| 解析后、spawn 前 | 最终 CLI/deploy/strategy、模型 metadata、声明能力 | 轴关系、stage 布局、scheduler/缓存/stream 开关；错误注明 rule ID、stage、冲突字段来源。必须在 CLI 覆盖后检查。 |
| worker probe / 初始化 | 实际 SKU/SM、可见设备、依赖包、HF geometry、组件 plan | 校验 kernel、head、dtype、collective、SP/VAE hooks；已知信息尽量在加载权重前检查；安装后的有效状态要确认。 |
| 请求准入 | 模态、图数、网格、帧数、prompt 长度、生成预算 | 检查模型与并行对该形状的要求，计算 KV/内存需求；明确可排队与永远不能满足的请求。 |
| 执行与终止 | request/group ID、逻辑 step、页表、实际 backend 与状态 | 保持 request 身份、成对进度和清理不变量；输入错误局部失败，非法 collective 拓扑在启动时拒绝。 |

建议形成可解释的 effective plan：`requested → effective → reason → evidence`。可选 compile/cache 回退可继续，但必须展示实际生效状态；被配置为必需的 SP/后端等无法生效时明确失败。历史用户可能依赖 fallback，需保持兼容默认或显式模式迁移，不能全局强改为报错。

实现状态用 `declared_supported / rejected / unverified`，运行状态另用 `effective / fallback / not_active`；缺证据不自动等于不支持。验证记录带 Omni/vLLM commit、模型 revision、SKU、driver/toolkit、dtype、输入、并行、测试 ID、权重种类与 artifact，避免换版本后继续沿用一个绿勾。

### 3. 用约束和风险选择组合，保留高阶正确性测试

沿用 `model_settings → case_filtering → hardware marks → Buildkite`。从声明约束生成可行候选，再按受影响模块和启动成本选择；测试 skip 要区分 unsupported、缺资源、缺依赖、未入选，不能算作通过。源码依赖过滤已存在，新增公共契约路径须接入 registry，验证最终选中的 job。[cite:6](#source-6)

普通低风险开关可用受约束的两两交互覆盖减少组合；以下高阶场景必须定点保留，两两覆盖不能证明调度或数值正确：

- `SP方式 × padding/mask × 不整除的输入形状`：核对单卡参考、pad 隔离和每路 shape，不能只有成功返回。
- `CFG请求对 × KV/token压力 × cancel/EOS/length`：检查整对准入、推进、终态和零残留，覆盖多对与普通请求混合。
- `VAE/TP × 多输出 × 请求排序/非方形网格`：检查 Request ID、图尺寸、输出顺序和分块拼接误差。
- `精度/attention kernel × SKU/软件栈 × head/长度`：确认实际 backend，不能仅检查 Python 包可导入。

L1 跑资源推导和契约；L2 用 tiny weights 跑真实 runner/collective/输入链路；L3/L4 在代表性可行组合上做真权重质量和同质量性能；L5 跑压力及失败后恢复。对不同模态使用不同质量判据，不把随机权重的非空媒体当作质量验收。测试选择的改进不能以降低维护者现有 CI gate 为代价。

## 下一周期的执行顺序与验收口径

| 顺序 | 具体落点 | 验收口径 | 当前状态 |
| --- | --- | --- | --- |
| 1 | diffusion 资源推导 + test helper | 修正已确认的 4→2 计数；真实 2 卡执行并核对有效 VAE group | 已定位，未实施 |
| 2 | resolver/worker 的 requested/effective 记录 | 人为缺失 SP plan/不支持 kernel 时明确说明；必需能力及时拒绝 | 设计完成，未实施 |
| 3 | 代表性组合与覆盖记录 | 稳定记录 selected/executed/passed/skipped 及原因、版本和权重种类 | 设计完成，未实施 |
| 4 | LongCat CFG 生命周期 | 原子准入/推进、整对终止和资源回收；真实 runtime 后再做真机媒体对照 | 独立草稿，未实施 |

工程难点集中在跨层一致性：CLI 会覆盖策略；stage 可共享卡；HSDP/VAE/EP 的 rank 关系不同；输入形状到请求准入时才完整；取消时 KV 与模型状态都要清理；tiny 测试成本低但不证明质量。范围应按上述顺序逐步扩展。

跟踪指标：可行且要求覆盖的交互中实际执行比例、执行通过率、skip 原因、测试启动次数与 GPU 工时、错误发生阶段、实际生效能力与声明的差异；性能另跟踪同质量有效 req/s、P95/P99、峰值显存和取消恢复时间。本次没有 CI/GPU artifact，不能给覆盖提升、成本降低或吞吐改善数字。

代码状态：两项既有 LongCat 局部修复已在个人 fork，并追加 [临时代码说明](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/code/planning/longcat-next/TEMPORARY_CODE.md)，标注“需要后续整改”。前序隔离 CPU 72 项通过不扩展为本方案已验证；CFG 生命周期升级和本篇组合契约设计均未实现。

## 证据索引

以下为同一仓库的一手源码与文档交叉核对，以及范围明确的隔离 CPU 结果；没有独立外部验证或新的线上故障报告。main 引用固定到调查 SHA，LongCat 引用固定到其前序草稿 SHA。

<a id="source-1"></a>
[cite:1] [平台插件检测](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/platforms/__init__.py)、[平台接口](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/platforms/interface.py)、[CUDA backend 选择](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/platforms/cuda/platform.py)。

<a id="source-2"></a>
[cite:2] [Pipeline registry](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/config/pipeline_registry.py)、[Stage/PipelineConfig](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/config/stage_config.py)、[统一 resolver](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/config/resolver.py)。

<a id="source-3"></a>
[cite:3] [Qwen2.5-Omni pipeline](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/model_executor/models/qwen2_5_omni/pipeline.py)、[部署与平台覆盖](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/deploy/qwen2_5_omni.yaml)。

<a id="source-4"></a>
[cite:4] [策略 translator](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/config/composable_parallel/translator.py)、[apply/device check](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/config/composable_parallel/apply.py)、[factory 覆盖顺序](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/config/config_factory.py)。

<a id="source-5"></a>
[cite:5] [Diffusion input metadata](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/diffusion/model_metadata.py)、[StagePool affinity](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/engine/stage_pool.py)。

<a id="source-6"></a>
[cite:6] [模型参数表](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/tests/model_tests/diffusion/model_settings.py)、[case_filtering](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/tests/model_tests/diffusion/case_filtering.py)、[common offline](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/tests/model_tests/diffusion/test_common_offline.py)、[common online](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/tests/model_tests/diffusion/test_common_online.py)、[nightly job](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/.buildkite/cuda/test-nightly.yml)、[CI 分层与选择](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/docs/contributing/ci/ci_settings.md)。

<a id="source-7"></a>
[cite:7] [生产 DiffusionParallelConfig](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/diffusion/data.py#L241-L484)、[测试资源推导](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/tests/model_tests/diffusion/config_types.py#L102-L173)；本次隔离结果由随附脚本复现。

<a id="source-8"></a>
[cite:8] [Supported Models 及勾选说明](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/docs/models/supported_models.md)。

<a id="source-9"></a>
[cite:9] [VAE 复用 rank 文档](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/docs/user_guide/diffusion/parallelism/vae_parallelism.md#L37-L62)、[VAE patch wrapper](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/diffusion/distributed/vae_patch_parallel.py#L348-L400)。

<a id="source-10"></a>
[cite:10] [SP hook 警告后继续](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/diffusion/registry.py#L619-L693)、[runner 的 compile/cache 降级及 step 限制](https://github.com/vllm-project/vllm-omni/blob/dca119877bd420ee0abc117e637eeac7aa28e4dd/vllm_omni/diffusion/worker/diffusion_model_runner.py#L375-L435)。

<a id="source-11"></a>
[cite:11] [前序 CFG 生命周期调查、两个局部复现及验证边界](https://github.com/Cheongroach/vllm-omni/blob/8270df2daa1970089deb6282e6da1e1d00ff938a/planning/longcat-next/drafts/cfg-lifecycle.md)。
