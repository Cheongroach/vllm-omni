# 分支与交接

日期：2026-10-24。目标 fork：`https://github.com/Cheongroach/vllm-omni`。

## 已完成

| 分支 | 基线 | 内容 |
| --- | --- | --- |
| `main` | 上游 `9bc166cd5` | 本地已同步；旧 head 备份为 `backup/main-20261024` |
| `longcat-next/code` | #5299 `c90ebc1d07ba` | `b56c2a94b` 视觉正确性；`53785219b` 存储共享；只有模型与两份测试变更 |
| `longcat-next/docs` | 上游 `9bc166cd5` | 研究、审查、手稿、会话摘要、验证与本交接 |
| `longcat-next/roadmap` | 旧本地 `9f5521351` | TODO、验收、分支/issue/PR、草稿、简历 |
| `longcat-next/improvements` | 旧 PR head | 保留原四项改进，未重新推送或盲目叠加 |

三个新分支各在 `.worktrees/longcat-next-{code,docs,roadmap}`。无关实验目录保持原状，未加入这些提交。所有提交均有 DCO sign-off。

代码 diff 为 3 文件、+148/-18；16 项新用例在基线 10 失败/6 通过，修复后连同既有 talker 用例共 72 通过。详见 [验证](VALIDATION.md)。

## 远端尚未完成

GitHub 拒绝 fork `main` 同步，原错误：

> refusing to allow an OAuth App to create or update workflow `.github/workflows/build_wheel.yml` without `workflow` scope

当前令牌 scopes 包含 `repo`，不包含 `workflow`。本次本地成果已提交，但 fork main 与三个新分支没有成功推送；不能将“本地 commit”称作“已提交到 GitHub”。

用户在自己的终端为 GitHub 补充授权：

```bash
gh auth refresh -h github.com -s workflow
```

完成后重新检查身份和 scope；如果使用不同客户端管理 GitHub 授权，也可在该客户端完成等效授权。不要在会话粘贴 token。

授权后剩余步骤：

```bash
gh api -X POST repos/Cheongroach/vllm-omni/merge-upstream -f branch=main
git push origin \
  longcat-next/code \
  longcat-next/docs \
  longcat-next/roadmap
git ls-remote origin \
  refs/heads/main \
  refs/heads/longcat-next/code \
  refs/heads/longcat-next/docs \
  refs/heads/longcat-next/roadmap
```

如出现分支冲突先查明远端更新，不强推。成功后核对四条 remote OID 与本地，并给三个分支设 origin tracking。推送 fork 已获用户授权；不需要另开上游 issue/PR 或给作者发消息。

## 历史整理限制

`docs` 的 rebase 已完成。对 `roadmap` 的同类 rebase 被自动审批拒绝，理由是没有明确授权该分支的历史改写。保留其旧基线；这不影响读取材料或推送现有分支。后续没有必要仅为文档基线一致重写历史。

main/当前 PR 快照通过官方 GitHub API/tarball 导入，并核对 commit/tree SHA。浅历史边界不能当作全量 history；正常网络下可补齐。

## 阅读顺序与贡献策略

1. [审查](review.md)：仍成立的缺陷、已被作者吸收的旧改动，以及反证。
2. [源码手稿](manuscript.md)：输入、主干、逐级 RVQ、状态、CFG、内存。
3. [验证](VALIDATION.md)：实际通过项、未执行项、可复制命令。
4. `longcat-next/roadmap` 中的 `planning/longcat-next/README.md`：后续计划、草稿与简历。

先让 #5299 作者吸收两个小修复；模型合并后，再从新 upstream/main 建独立修复分支。CFG 成对调度先 RFC，质量、在线能力、profiling/graph、NPU 依次分开验收。不要把此代码分支直接向 upstream/main 开重复的整模型 PR。
