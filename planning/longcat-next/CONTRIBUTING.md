# 分支、issue、PR 与接受度

先读[贡献流程阅读版](CONTRIBUTING-friendly.md)理解 fork、依赖与投稿路径。本文件保留命令和历史操作记录。

## 本次布局

`origin` 是 `Cheongroach/vllm-omni`，`upstream` 是 `vllm-project/vllm-omni`。`main` 跟踪上游，默认推送目标是个人 fork。代码、研究、计划分别在独立 worktree，避免频繁切分支时带入实验目录。

```bash
git remote -v
git branch -vv
git worktree list
git config remote.pushDefault origin
git config branch.main.pushRemote origin
```

研究时的上游 `main` 为 `9bc166cd556cdaa4e0b18543da0c2def0076275e`，代码基线固定 #5299 `c90ebc1d07ba8c0b583586a1eddf91f531047bce`。2026-10-25 fork main 已同步到 `dca119877bd420ee0abc117e637eeac7aa28e4dd`，三个 LongCat-Next 分支已推送。研究和计划分支保留原基线，不改写历史。普通 Git 拉取曾超时，因此此前通过 GitHub 官方快照/API 核对 tree 与 commit SHA 后导入；本地采用浅历史边界，并保留 `backup/main-20261024`。完整历史仍需在网络正常时补齐。

以后正常同步：

```bash
git fetch upstream
git switch main
git merge --ff-only upstream/main
git push origin main
```

若提示 shallow history，先 `git fetch --unshallow upstream`，不要为省事把 main 强推覆盖。若 fork 已有自己的 main 提交，先检查 divergence，另开分支保留，再决定同步；不要擅自删除历史。

OAuth 曾因缺 `workflow` scope 拒绝 fork 同步；用户补充授权后，本次同步已成功。如果以后遇到同类权限错误，可执行 `gh auth refresh -h github.com -s workflow`。不要删 workflow 或绕过授权以强行同步。

## 代码如何送到上游

当前模型尚未合并。`longcat-next/code` 依赖整个 #5299，因此直接以 upstream/main 为 base 会带出完整模型适配差异。推荐先给原作者提供两项独立 commit/patch，让其吸收或指明合适的目标分支。

作者需要接收时，先获取 fork 分支再 cherry-pick 具体提交；在双方明确授权后才向作者仓库开 PR。对上游应等模型合并，再从最新 main 新建两条小分支，重新验证后分别开 PR。不要用 `Closes #5299`：这个编号是原适配 PR，并非两个小修复对应的 bug issue。

```bash
git fetch upstream
git worktree add -b fix/longcat-next-visual ../longcat-next-visual upstream/main
# 用本次交接中的视觉修复 SHA 替换占位符。
git -C ../longcat-next-visual cherry-pick -s <visual-fix-sha>
git -C ../longcat-next-visual push -u origin fix/longcat-next-visual
```

研究与 roadmap 留在个人 fork；不要 merge 它们进代码分支或上游代码 PR。旧 `longcat-next/improvements` 用作历史参考，其中尺寸和请求对齐已被作者部分吸收，不能整串 cherry-pick。

## issue 与 PR 的分工

| 类型 | 适合内容 | 最小可审核信息 |
| --- | --- | --- |
| Bug issue | 可复现行为错误或不满足已声明能力 | 基线、预期/实际、最小复现、影响、证据边界 |
| RFC issue | CFG 原子调度、graph/batching、API 新契约 | 用户需求、职责划分、替代方案、验收、迁移风险 |
| 小修复 PR | 狭窄改动与回归测试 | 为什么发生、最终行为、测试结果、未覆盖路径 |
| 新能力 PR | 一项完整声明的能力 | 实现、测试、部署配置/文档、支持矩阵 |

先搜索现有 issue、PR 与作者回复，确认问题仍存在且无人重复推进。使用路径 CODEOWNERS 找最小相关 owner；机器人 mention 不是已接受任务。邀请维护者只问一个具体设计问题，不要求没有权限的贡献者自行启动全部 Buildkite。

本目录 `DRAFTS.md` 是草稿，不是已发布 issue/PR。发布示例（需先准备正文文件并人工核对）：

```bash
gh issue list -R vllm-project/vllm-omni --search 'LongCat-Next CFG'
gh pr list -R vllm-project/vllm-omni --search 'LongCat-Next'
gh issue create -R vllm-project/vllm-omni \
  --title '[RFC] Preserve LongCat-Next CFG pairs across scheduling' \
  --body-file ./cfg-issue.md
gh pr create -R vllm-project/vllm-omni \
  --base main --head Cheongroach:fix/longcat-next-visual --draft \
  --title '[Bugfix] Keep LongCat-Next visual RVQ codes valid' \
  --body-file ./visual-pr.md
```

`--body-file` 保留真实换行，避免复杂 shell 转义。以上命令只说明操作，不代表当前满足发布条件。

## 提高接受度

1. 问题来自用户需求并可复现，提交前明确目标用户、关键变量与收益。不为了简历堆功能或扩大 diff。
2. 一条 PR 解决一个主问题；视觉正确性与 storage 分开。不要随修复重构整个 runtime。
3. 基线和结论对应同一 head。旧 CI/尺寸/请求错误已修复就从批评中删除；当前 GPU 状态以最新结果为准。
4. 测试要先失败再通过，断言契约而非代码实现。标记 `core_model` + `cpu`，现有 Simple Unit Test 已收集新路径，不增 YAML 作业。
5. 对 AI 辅助如实披露，人工复核、DCO sign-off、必要验证；签名代表贡献者同意，不把 AI 生成当作个人实测。
6. 遵守上游 PR template、precheck skill 和 AI policy；提交时重新读取最新规则。特别是贡献意图四问必须由人明确回答，不能把这里的 agent 草稿当作人的答案。当前只完成个人 fork 的代码和材料，不宣称上游 ready。
7. 真实 GPU 测试资源不足时提供窄逻辑证据和待测矩阵，让维护者决定 CI admission；不编造 benchmark，也不以 “CI skip” 代替本地 lint。
8. 回复 review 时描述修复内容、对应 SHA 和测试，少写辩解；不以“已经合并”证明所有原验收条件完成。

## 验证命令

从 `longcat-next/code` worktree 根目录执行。前提：匹配该 PR 的 vLLM/vllm-omni 开发安装与 pytest 依赖；这两份 L1 测试不需要 GPU/HF 权重，但模块导入仍需要完整依赖。

```bash
pytest -q tests/model_executor/models/test_longcat_next_visual_codes.py
pytest -q tests/model_executor/models/test_longcat_next_embedding_storage.py
pytest -sv tests/model_executor/models/ \
  -m 'core_model and cpu' --run-level=core_model -k longcat_next
pre-commit run --files \
  vllm_omni/model_executor/models/longcat_next/modeling_longcat_next.py \
  tests/model_executor/models/test_longcat_next_visual_codes.py \
  tests/model_executor/models/test_longcat_next_embedding_storage.py
```

本机隔离 harness 跳过 unrelated runtime imports 和 conftest；它用于复现窄逻辑，不替代上述完整命令。实际通过数量和未执行项见 `longcat-next/docs` 分支的 `research/longcat-next/VALIDATION.md`。
