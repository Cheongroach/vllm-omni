# 分支与交接

更新：2026-10-25。目标 fork：`https://github.com/Cheongroach/vllm-omni`。

## 已完成

| 分支 | 基线 | 内容 |
| --- | --- | --- |
| `main` | 当前上游 `dca119877b` | fork 与本地均已同步；旧 head 备份为 `backup/main-20261024` 和 `backup/main-20261025` |
| `longcat-next/code` | #5299 `c90ebc1d07ba` | `b56c2a94b` 视觉正确性；`53785219b` 存储共享；只有模型与两份测试变更 |
| `longcat-next/docs` | 上游 `9bc166cd5` | 研究、审查、手稿、会话摘要、验证与本交接 |
| `longcat-next/roadmap` | 旧本地 `9f5521351` | TODO、验收、分支/issue/PR、草稿、简历 |
| `longcat-next/improvements` | 旧 PR head | 保留原四项改进，未重新推送或盲目叠加 |

三个新分支各在 `.worktrees/longcat-next-{code,docs,roadmap}`。无关实验目录保持原状，未加入这些提交。所有提交均有 DCO sign-off。

代码 diff 为 3 文件、+148/-18；16 项新用例在基线 10 失败/6 通过，修复后连同既有 talker 用例共 72 通过。详见 [验证](VALIDATION.md)。

## 远端推送已完成

用户补充 `workflow` 授权后，GitHub 已成功 fast-forward fork main 到 `dca119877bd420ee0abc117e637eeac7aa28e4dd`。三个分支已推送并通过 GitHub Git refs API 核对：代码分支 `53785219b3c087f9e498ca2ed07088c9407fe037`，研究和计划分支与各自本地提交一致。文档状态更新会追加普通提交，不改写既有历史。

三个 LongCat-Next 分支均跟踪 `origin` 下的同名分支；main 继续跟踪 `upstream/main`。完整最终 SHA 清单与核对时间保存在交付包 `manifest.json`。

重新核对远端：

```bash
git ls-remote origin \
  refs/heads/main \
  refs/heads/longcat-next/code \
  refs/heads/longcat-next/docs \
  refs/heads/longcat-next/roadmap
gh api repos/Cheongroach/vllm-omni/git/matching-refs/heads \
  --jq '.[] | select(.ref == "refs/heads/main" or (.ref | startswith("refs/heads/longcat-next/"))) | [.ref,.object.sha] | @tsv'
```

代码、研究和计划分支继续保持原始基线。此次没有向上游或作者发送消息、评论，也没有创建 issue/PR。后续推送如出现冲突先核查，不强推。

## 历史整理限制

`docs` 的 rebase 已完成。对 `roadmap` 的同类 rebase 被自动审批拒绝，理由是没有明确授权该分支的历史改写。保留其旧基线；这不影响读取材料或推送现有分支。后续没有必要仅为文档基线一致重写历史。

原 main/当前 PR 快照通过官方 GitHub API/tarball 导入，并核对 commit/tree SHA。本次 Git 拉取和 tarball 下载均超时，本地同步改用 GitHub Git objects API，只下载缺失对象并核对所有 blob/tree 和原签名 commit SHA。浅历史边界不能当作全量 history；正常网络下可补齐。

## 阅读顺序与贡献策略

1. [审查](review.md)：仍成立的缺陷、已被作者吸收的旧改动，以及反证。
2. [源码手稿](manuscript.md)：输入、主干、逐级 RVQ、状态、CFG、内存。
3. [验证](VALIDATION.md)：实际通过项、未执行项、可复制命令。
4. `longcat-next/roadmap` 中的 `planning/longcat-next/README.md`：后续计划、草稿与简历。

先让 #5299 作者吸收两个小修复；模型合并后，再从新 upstream/main 建独立修复分支。CFG 成对调度先 RFC，质量、在线能力、profiling/graph、NPU 依次分开验收。不要把此代码分支直接向 upstream/main 开重复的整模型 PR。
