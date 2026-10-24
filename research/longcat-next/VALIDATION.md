# 本次代码验证

日期：2026-10-24。基线：#5299 `c90ebc1d07ba8c0b583586a1eddf91f531047bce`。代码分支：`longcat-next/code`。

## 提交

| Commit | 内容 | 范围 |
| --- | --- | --- |
| `b56c2a94b` | `[Bugfix] Keep LongCat-Next visual RVQ codes valid` | 每级视觉 sentinel、code 0 反馈；12 项新回归 |
| `53785219b` | `[Model] Share LongCat-Next depth embedding storage` | 两模态冻结 storage 共享，去掉 FP32 中转；4 项新回归 |

相对固定 PR 基线：3 个文件，148 行增加、18 行删除；模型代码 16 行增加、18 行删除，测试增加 132 行。两个提交均有 DCO `Signed-off-by`，不代表密码学签名或上游已接收。

## 结果

| 验证 | 结果 | 证明范围 |
| --- | --- | --- |
| 原代码 + 16 项新用例 | 10 failed / 6 passed | 4 项 sentinel、2 项 code 0、4 项 storage 可复现 |
| 视觉修复 + 新视觉/既有 talker 测试 | 68 passed | 12 新视觉 + 56 既有 talker |
| 两项修复 + 两份新测试/既有 talker | 72 passed | 同上 + 4 storage |
| Ruff lint / format check | 通过 | 三个变更 Python 文件 |
| 仓库 check-mark | 通过 | 新测试 `core_model` + `cpu`，无直接 SKU 标记 |
| SPDX | 通过 | 新测试 Omni copyright |
| forbidden imports / torch.cuda gate | 通过 | 变更文件，无新增禁用导入或 CUDA 调用 |
| `git diff --check` | 通过 | 相对固定基线的空白检查 |
| 完整 `pre-commit` | 未执行 | 本机没有 pre-commit；运行了上述适用脚本，不等于全 hook 集通过 |
| 完整 vLLM runtime / TP / GPU / 质量 | 未执行 | 本机缺匹配运行时、完整权重和 GPU |

CPU harness 直接导入生产模型模块、调用原方法，替换无关 vLLM imports，使用现有测试的 head/TP stub，并关闭 conftest。没有替换被测采样、反馈或 storage 方法。配置以 `-o addopts=''` 取消本机未安装的 xdist 参数；禁用插件自动加载及 bytecode 写入。出现一项 `asyncio_mode` 未知配置警告，原因是隔离模式没有加载 asyncio plugin。

首次尝试因缺 xdist plugin 而未进入测试，不能计入基线复现；上表记录的是随后实际执行的 16 项断言结果。

## 完整环境复验

从代码 worktree 根目录执行。需要匹配该 head 的 vLLM、vllm-omni 开发依赖、pytest/pytest-xdist/pytest-asyncio；两份 L1 新测试本身不需要 GPU 或 HF 模型缓存。

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

现有 `.buildkite/cuda/test-ready.yml` Simple Unit Test 已执行 `tests/model_executor -m 'core_model and cpu'`，无需为这两份新测试加重复作业。

后续 GPU 验证必须使用此 fork 实际代码 SHA，不能引用作者旧 `986ade20` E2E 代替。检查 remote-code head 是否移动/修改共享 embedding；若将 module 移到另一设备，会重新分配 storage，当前优化保证仅适用于缓存与 head 同设备同 dtype 的初始化路径。完整 offload/device 迁移不在此次验证范围。

## 上游就绪状态

局部修复和独立测试已完成。当前不是上游 ready：模型前置 PR 尚未合并，完整运行时/真机未测；提交上游时还需人工复核、贡献意图四问、最新模板及 AI 披露。个人研究与计划材料不进入这两个代码提交。
