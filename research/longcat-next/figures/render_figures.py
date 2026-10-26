# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM-Omni project
"""Render the three explanatory figures; requires Matplotlib and a CJK font.

The resource counts and CFG steps are observations recorded in the source
documents. The RVQ and paired-lifecycle layouts are explanatory diagrams,
not timing measurements or new experiments.
"""

from pathlib import Path
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

TEXT = "#202B38"
MUTED = "#526171"
BLUE = "#285F91"
PURPLE = "#725B98"
SURFACE = "#F5F7FA"
BORDER = "#C5CED8"


def box(ax, x, y, w, h, label, *, edge=BORDER, size=12):
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
        facecolor=SURFACE, edgecolor=edge, linewidth=1.4,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=size, color=TEXT, linespacing=1.6)


def arrow(ax, start, end, *, color=MUTED):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=13,
        linewidth=1.3, color=color, shrinkA=3, shrinkB=3,
    ))


def canvas(title, height=4.3):
    fig, ax = plt.subplots(figsize=(10, height), dpi=180)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, height)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(0.3, height - 0.3, title, color=TEXT, fontsize=16, va="top")
    fig.subplots_adjust(left=0.025, right=0.975, top=0.98, bottom=0.04)
    return fig, ax


def save(fig, output, name):
    fig.savefig(output / f"{name}.png", facecolor="white")
    fig.savefig(output / f"{name}.svg", facecolor="white")
    plt.close(fig)


def rvq(output):
    fig, ax = canvas("一个图像位置内部：8 级离散码需要依次生成")
    box(ax, 0.4, 2.2, 2.0, 0.85, "主干生成\n当前位置的表示", edge=BLUE)
    box(ax, 3.1, 2.2, 2.3, 0.85, "深度预测网络\n依次生成 c0 … c7", edge=BLUE)
    box(ax, 6.1, 2.2, 3.4, 0.85, "一组码有两种用途\n反馈给主干 · 交给图像解码器")
    arrow(ax, (2.4, 2.63), (3.1, 2.63))
    arrow(ax, (5.4, 2.63), (6.1, 2.63))
    for i in range(8):
        x = 0.7 + i * 1.1
        box(ax, x, 0.95, 0.65, 0.65, f"c{i}", edge=BLUE)
        if i < 7:
            arrow(ax, (x + 0.65, 1.28), (x + 1.1, 1.28), color=BLUE)
    ax.text(5, 0.42, "后一级读取前面已经采样的码；跨请求批处理也必须保留这个顺序。",
            ha="center", color=MUTED, fontsize=11)
    save(fig, output, "rvq-order")


def cfg(output):
    fig, ax = canvas("CFG 配对：两个内部请求共同完成一个用户请求", height=5.1)
    ax.text(0.45, 4.28, "已有隔离 CPU 观察", color=MUTED, fontsize=12)
    box(ax, 0.45, 3.12, 2.1, 0.85, "有条件请求\n生成第 9 步", edge=BLUE)
    box(ax, 0.45, 1.88, 2.1, 0.85, "无条件请求\n生成第 2 步", edge=PURPLE)
    box(ax, 3.3, 2.5, 2.5, 0.85, "仍被合并采样\n并把计数改为 9")
    box(ax, 6.6, 2.5, 2.9, 0.85, "计数看似一致\n历史内容没有被修复")
    arrow(ax, (2.55, 3.54), (3.3, 3.08), color=BLUE)
    arrow(ax, (2.55, 2.3), (3.3, 2.73), color=PURPLE)
    arrow(ax, (5.8, 2.92), (6.6, 2.92))
    ax.text(0.45, 1.33, "建议的处理规则（尚未实现）", color=MUTED, fontsize=12)
    labels = ["标记为同一对", "资源一起满足", "同一步共同推进", "一起结束并清理"]
    for i, label in enumerate(labels):
        x = 0.45 + i * 2.4
        box(ax, x, 0.42, 1.9, 0.58, label, edge=BLUE, size=11)
        if i < 3:
            arrow(ax, (x + 1.9, 0.71), (x + 2.4, 0.71))
    save(fig, output, "cfg-pair")


def resources(output):
    fig, ax = canvas("TP=2 与 VAE=2 在这个配置中复用同两张卡", height=4.7)
    ax.text(0.5, 3.77, "运行时配置：2 个 worker", color=BLUE, fontsize=13)
    ax.text(6.1, 3.77, "测试估算：2 × 2 = 4", color=MUTED, fontsize=13)
    for x, label in [(0.65, "GPU 0"), (2.95, "GPU 1")]:
        box(ax, x, 2.65, 1.85, 0.68, label, edge=BLUE)
    box(ax, 0.65, 1.56, 4.15, 0.6, "TP=2：把模型计算分给这两张卡", edge=BLUE)
    box(ax, 0.65, 0.65, 4.15, 0.6, "VAE=2：解码时继续使用这两张卡", edge=BLUE)
    for x in [1.58, 3.88]:
        arrow(ax, (x, 2.16), (x, 2.65), color=BLUE)
    box(ax, 6.1, 1.65, 3.2, 1.4, "测试 helper 又乘了 VAE 度数\n因此把同一个用例算到 4 卡")
    ax.text(6.1, 0.88, "证据：生产配置 + 测试 helper 的\n隔离 CPU 调用，以及 VAE 复用说明。\n未测实际 GPU 执行或队列成本。",
            color=MUTED, fontsize=11, linespacing=1.6)
    save(fig, output, "shared-ranks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    font_manager.fontManager.addfont(str(args.font))
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=args.font).get_name()
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["svg.fonttype"] = "path"
    args.output.mkdir(parents=True, exist_ok=True)
    assert (131072 + 19456) * 3072 * 2 / 1024**2 == 882
    rvq(args.output)
    cfg(args.output)
    resources(args.output)
