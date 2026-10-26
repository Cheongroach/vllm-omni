# LongCat-Next 设计草稿：从哪里开始读

本目录保存在个人 fork，包含调查和未实施的设计。局部代码与复现脚本已上传，不代表 CFG 生命周期或组合改进已经完成。

| 想理解的问题 | 先看阅读版 | 需要进一步审阅时 |
| --- | --- | --- |
| 卡、模型、输入为什么不能分别看支持 | [组合周报](weekly-2026-10-25-combinations-friendly.md) | [技术周报、日志与源码引用](weekly-2026-10-25-combinations.md) |
| CFG 两路为什么必须一起推进 | [CFG 生命周期](cfg-lifecycle-friendly.md) | [资源公式、实施入口与验收](cfg-lifecycle.md) |

阅读版带 `-friendly`，先用例子解释原理；技术版保留细节供实现与审阅。两版使用同一组证据，阅读版没有增加新的性能或质量结论。

[组合复现脚本](combinations_probe.py) 检查生产配置与测试 helper 的卡数推导，不执行 GPU 模型。[临时代码说明](https://github.com/Cheongroach/vllm-omni/blob/longcat-next/code/planning/longcat-next/TEMPORARY_CODE.md) 解释两个旧局部修复，以及剩余整改。

## 当前证据与工作状态

| 项目 | 状态 |
| --- | --- |
| 调查与两个隔离 CPU 复现 | 已完成，验证边界见正文 |
| 组合资源计数核验 | 已确认 FLUX.2 TP2+VAE2 的 helper=4、生产 world=2 |
| 工程方案 | 草稿，待审阅 |
| 升级代码实现 | 未开始 |
| 完整运行时 / GPU 验收 | 未完成 |
| 上游 issue / RFC / PR | 未提交 |
