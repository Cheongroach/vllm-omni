# [DRAFT / 非正式] LongCat-Next 审阅草稿

> **DRAFT / 非正式：仅供仓库所有者审阅。不是正式 RFC、上游 PR 或已完成能力声明。**

本目录位于个人 fork 的 `longcat-next/draft-cfg-lifecycle` 分支。包含设计文档、小周报和隔离调查脚本，生产代码与部署配置未改动。

- [CFG 生命周期升级方案](cfg-lifecycle.md)：实际复现、工程难点、拟实施范围和验收矩阵。
- [2026-10-25 小周报：硬件、模型与输入组合](weekly-2026-10-25-combinations.md)：当前机制、已确认问题、处理日志和改进顺序。
- [组合配置复现脚本](combinations_probe.py)：临时调查代码，仅验证源码配置和测试 helper，不代表 runtime/GPU 验收。
- [既有 LongCat 临时代码说明](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/code/planning/longcat-next/TEMPORARY_CODE.md)：局部修复已上传，CFG 升级和完整验收待完成。

请审阅优先目标、实现范围、兼容性取舍和验收条件，并反馈修改意见。草稿或调查脚本进入 Git 历史不代表生产能力已经完成。

草稿状态：

| 项目 | 状态 |
| --- | --- |
| 调查与两个隔离 CPU 复现 | 已完成，验证边界见正文 |
| 组合资源计数核验 | 已确认 FLUX.2 TP2+VAE2 的 helper=4、生产 world=2 |
| 工程方案 | 草稿，待审阅 |
| 升级代码实现 | 未开始 |
| 完整运行时 / GPU 验收 | 未完成 |
| 上游 issue / RFC / PR | 未提交 |
