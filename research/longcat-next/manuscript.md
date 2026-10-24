# LongCat-Next 源码讲解手稿

## 开场

我关注的是“一个多模态模型如何进入持续批处理推理框架”。LongCat-Next 将图像和音频离散化，使同一个主干完成理解与生成；工程难点在于主干 KV cache 之外，还要维护码本深度预测、模态状态和反馈 embedding。

模型配置有 14 个复合 block、28 个 attention 模块；主干采用 MLA、Shortcut MoE 与 N-gram embedding。视觉和音频各有 4 层 depth head，每个位置预测 8 级 RVQ 码。标称约 3B 激活参数不能代表权重常驻显存，尤其存在大规模 N-gram 表。

## 第一段：输入与主干

先讲 `longcat_next_processor.py` 和音频 processor：输入媒体转换成 patch/grid 或音频特征，计算 placeholder 长度。`embed_multimodal()` 编码得到离散码，再合并码 embedding 放回主干输入位置。

接着讲 `FlashNgramModel`：Omni 复用原生 vLLM 主干、paged KV 与 TP。每请求 N-gram 短历史另由 preprocess 管理，多模态控制 token 是边界。这里要区分“模型结构对齐”和“运行时状态对齐”。

## 第二段：生成有两个方向

主干产生下一个空间/时间位置；depth head 在这个位置内部做：

`p(c0 | h), p(c1 | h,c0), …, p(c7 | h,c0,…,c6)`。

Omni 用 `talker_mtp` 接入这个循环，但它不是 speculative decoding。可以跨请求批处理同一级计算，不能删除码本层级依赖。

读取 `preprocess → talker_mtp → model.forward → make_omni_output → compute_logits`。注意该 hook 读取保存的 hidden，并构造本轮输入 embedding；讲解时按实际调用顺序解释，不能把它直接画成普通 lm_head 的替换。

## 第三段：请求正确性

模型除 KV cache 外还保存 `_ngram_ctx`、`_audio_gen`、`_visual_gen`。last_hidden、步数、past_codes、网格和输出 payload 都必须属于同一个 request。

以“同一批里一条文本、一条音频、一条图像”为例：只把有帧请求压成一个 tensor 会丢失 batch 位置。当前 PR 改成逐请求 list 和空张量占位；logits 行则使用 runner 的真实请求顺序。

单条请求成功并不覆盖重排、空帧、取消或抢占。回归必须穿过真实 payload splitter，并另外验证 scheduler 行为。

## 第四段：两个视觉修复

第一，所有视觉码级别都应满足 `0 <= c_i < codebook_size_i`。当前 PR 只屏蔽第一级额外类，高层额外类可以进入输出；它们会破坏反馈语义。真实 VQ 表有额外物理行，不能夸大成必然越界崩溃。

第二，合法 code 0 不能当作“没有图片”。当前代码保存了该帧，却反馈文本 embedding。修复依据是 `frame_kept` 和码合法性，与码值是否为零无关。

这两项适合先贡献：局部、明确、有稳定 CPU 回归，不必先重写整个 runner。

## 第五段：内存优化

rank 0 的 depth head 不能独自调用 TP embedding collective，因此 replicated 码表有必要。但码表已经缓存后再 clone 成另一份 Embedding 没必要。

共享只读 storage，并去掉 FP32 中间转换。BF16、hidden=3072 时，每份视觉码表是 `131072×3072×2 = 768 MiB`，音频是 `19456×3072×2 = 114 MiB`；合计重复存储 882 MiB/rank。

旧 H20 allocator 实验支持这项局部存储差。它没有加载完整模型，不能描述成吞吐加速；当前 fork 仍需完整 GPU 复验。测试重点是全部小表数值、dtype、storage 指针、冻结和重复访问。

## 第六段：CFG 与性能路线

CFG 公式是 `uncond + s×(cond−uncond)`。真正困难的是两路必须在同一逻辑步采样并共享反馈。容量为两条请求不等于成对调度，缺配对降级普通采样会写入无法事后修复的 KV 历史。

先持久化 pair 身份，再原子准入、同批调度、取消与恢复。随后 profiling 判断关键路径：head rank-0 等待、Python launch、broadcast、N-gram、decoder 共置。

优化顺序是正确性和质量基线 → 同一级跨请求 batch → 静态 buffer/graph → 必要的 head TP与 decoder 资源拆分。每项都同时检查质量、延迟和有效吞吐。

## 面试时的证据边界

可以说自己审查并修复了视觉码契约、保留合法 code 0，以及减少重复存储，并提供明确的回归和分支依赖。

不能说“完成 LongCat-Next 三模态生产部署”“比 SGLang 更快”“支持 Ascend”，除非对应最新版本真机、质量、并发和故障实验已经完成。简历模板与后续验收见 `longcat-next/roadmap`。
