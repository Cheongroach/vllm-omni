# issue / PR 草稿

以下正文供人工审核后复制到独立 Markdown 文件。没有发布，也不代表上游 CI 或贡献意图 gate 已通过。发布时先确认 #5299 最新 head，套用最新 PR template，填写人类贡献者的四个意图问题与 AI 披露。不要用 agent 的动机猜测代填。

## 给 #5299 作者的简短说明

建议内容（需要单独授权才发送）：

> I checked head `c90ebc1d07ba` and prepared two small follow-up commits:
>
> 1. Mask the extra visual class at every RVQ level, and use visual feedback for kept frames whose level-0 code is zero.
> 2. Share frozen storage between replicated code rows and the depth-head embedding.
>
> The CPU regression cases fail on the baseline and pass with the changes. The tests run through production methods with unrelated vLLM imports stubbed; they do not establish GPU/TP or generation-quality parity. Would you prefer to cherry-pick the commits into #5299?

附个人 fork 分支链接、具体 commit SHA、测试命令即可。不要再完整贴一份模型适配或指责当前 head 已修复的问题。

## PR A：视觉正确性

标题：`[Bugfix] Keep LongCat-Next visual RVQ codes valid`

> LongCat-Next visual sampling at `c90ebc1d07ba` masks the extra class only at level zero. A higher-level extra class can therefore enter the emitted RVQ codes and alias another level's embedding through cumulative offsets. In addition, kept frames with a valid level-zero code of zero receive text feedback instead of visual feedback.
>
> Mask each level's extra class in both ordinary and CFG sampling, and select visual feedback whenever the frame is kept. New regressions cover greedy and sampled sentinel exclusion, code zero/nonzero, and pixel/newline feedback in ordinary and CFG paths.
>
> Validation: the six new failing visual cases reproduce on the baseline; all 12 new visual cases and the 56 existing talker tests pass after the change in an isolated CPU harness. Ruff checks and formatting pass. These results do not cover full vLLM initialization, TP collectives, real depth-head weights, scheduler behavior, or media quality.
>
> Dependency: the model implementation in #5299 must be present. This change does not fix CFG pair scheduling.
>
> AI assistance: implementation and analysis were prepared with an AI assistant. Human review and matching-head runtime validation are still required before requesting upstream review.

“高层 sentinel 导致必然 VQ 越界”不成立，不写。若先合并 #5299，需重新验证数量及 commit，再更新上述正文。

## PR B：存储共享

标题：`[Model] Share LongCat-Next depth embedding storage`

> The depth-head embedding currently clones the already replicated audio/visual code rows. Both inference consumers are read-only, so the clone retains an unnecessary second table on each rank that initializes it.
>
> Construct frozen embeddings from the cached rows and remove the intermediate FP32 conversion. Leave the all-rank table materialization in place so TP collective participation is unchanged.
>
> Validation: all four storage regressions fail on the baseline and pass after the change. They check FP32/BF16 lookup equality, frozen weights, shared storage, allocation size, and idempotent access for audio and visual. The 68 visual/talker cases also pass in the isolated CPU harness.
>
> At BF16, hidden size 3072, with both tables initialized, one duplicate copy is `(131072 + 19456) * 3072 * 2 = 882 MiB/rank`. This is a storage calculation, not an end-to-end GPU measurement or a throughput claim. Full checkpoint loading, TP, and device/offload behavior remain to be tested.
>
> AI assistance: prepared with an AI assistant; human review and matching-head runtime validation are pending.

## RFC issue：CFG 配对与调度

标题：`[RFC] Preserve LongCat-Next CFG pairs across scheduling`

> LongCat-Next image CFG requires conditional and unconditional streams at the same logical step to combine `u + scale * (c-u)` and share sampled codes and feedback.
>
> At #5299 head `c90ebc1d07ba`, the pair is discovered from twins in the current batch. A root-only batch cannot identify the absent twin and may sample independently without a warning. Identified but unavailable pairs can also fall back to ordinary sampling. Later counter synchronization cannot restore KV histories that have already diverged.
>
> Source-level evidence establishes these branches. We have not reproduced the scheduler trigger under a real GPU load. The existing same-batch CFG tests do not cover admission, preemption, or cancellation.
>
> Proposed scope:
>
> - Persist pair identity and role at request expansion, excluding requests that did not expand CFG.
> - Admit/schedule paired steps together, including chunked prefill readiness.
> - Define cancellation, terminal state, preemption, recovery, and cleanup for the pair.
> - Prevent silent fallback: either wait for the mate, explicitly reject unsupported scheduling, or expose a documented opt-in downgrade.
>
> Acceptance: cover root-only/twin-only eligibility, batch reordering, unequal progress, cancellation of one mate, and KV pressure. Assert shared codes/feedback at every kept step and no independent KV mutation while waiting.
>
> Design question: should pair admission and readiness be owned by the generic scheduler, or by an explicit grouped-request API used by the model adapter?

先确认上游通用 grouped request 是否已有方案；不要把 LongCat 专属 suffix 判断继续散落到每个 runtime 层。扩大 runtime 范围前先取得职责共识。

## 人工提交前核对

- 本次私有实验路径、其他项目会话、凭据和内部资源信息不进入正文。
- PR base 已含模型，或原作者明确接收 dependent PR；diff 只含目标修复。
- 四个贡献意图问题由人明确回答，AI 参与如实披露。
- 新 head 的完整本地/CI 结果、质量限制准确；DCO sign-off 与真实贡献者对应。
- 新 issue 先去重；未经授权不发送消息、评论或创建 PR。
