#!/usr/bin/env python3
# URRE architecture diagram v2 — program-drawn, Noto Sans CJK SC (layout fixed)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BOLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

W, H = 100, 148
fig = plt.figure(figsize=(20, 29.6), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
ax.add_patch(FancyBboxPatch((0.5, 0.5), 99, 147, boxstyle="round,pad=0.6,rounding_size=1.2",
                             fc="#F7F9FB", ec="#D5DDE6", lw=2))

TEAL = "#0F766E"; TEAL_L = "#CCFBF1"; NAVY = "#1E3A5F"; NAVY_L = "#DBEAFE"
AMBER = "#B45309"; AMBER_L = "#FEF3C7"; GREY = "#64748B"; GREY_L = "#F1F5F9"
GREEN_L = "#DCFCE7"; PURPLE_L = "#EDE9FE"; ROSE_L = "#FFE4E6"

def box(x, y, w, h, text, sub="", fc="white", ec=TEAL, lw=1.8, fs=12.5, sub_fs=10,
        bold=False, style="-", title_c="#0F172A", sub_c="#475569"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.0",
                                fc=fc, ec=ec, lw=lw, linestyle=style))
    cx = x + w / 2
    if sub:
        ax.text(cx, y + h - 0.9, text, ha="center", va="top",
                fontproperties=BOLD if bold else REG, fontsize=fs, color=title_c)
        ax.text(cx, y + 0.9, sub, ha="center", va="bottom",
                fontproperties=REG, fontsize=sub_fs, color=sub_c)
    else:
        ax.text(cx, y + h / 2, text, ha="center", va="center",
                fontproperties=BOLD if bold else REG, fontsize=fs, color=title_c)

def section(x, y, w, h, label, fc="#E0F2F1"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.8",
                                fc=fc, ec="none"))
    ax.text(x + 1.2, y + h - 0.8, label, ha="left", va="top",
            fontproperties=BOLD, fontsize=12.5, color="#0F766E")

def arrow(x, y1, y2, color=TEAL, lw=2.2):
    ax.add_patch(FancyArrowPatch((x, y1), (x, y2), arrowstyle="-|>",
                                 mutation_scale=22, lw=lw, color=color))

def label(x, y, s, fs=11, c="#334155", bold=False):
    ax.text(x, y, s, ha="center", va="center", fontproperties=BOLD if bold else REG,
            fontsize=fs, color=c)

# ---------- header ----------
ax.add_patch(FancyBboxPatch((2, 139), 96, 7.5, boxstyle="round,pad=0.4,rounding_size=1.0",
                            fc=NAVY, ec=NAVY))
ax.text(50, 144.6, "URRE 通用检索推荐引擎 · 架构设计方案 v2", ha="center", va="center",
        fontproperties=BOLD, fontsize=21, color="white")
ax.text(50, 140.8, "Universal Retrieval & Recommendation Engine  |  A篇 本次交付 Mock  ·  B篇 未来真实 URRE 2.0  |  2026-11-16",
        ha="center", va="center", fontproperties=REG, fontsize=11.5, color="#BFDBFE")
label(50, 137.2, "■ 实线 = 本次交付（A篇）      ┄ 虚线框 = 未来参考设计（B篇，不进本次门禁）      漏斗数字 = 每级候选规模", fs=11, c="#475569")

# ---------- 1 callers ----------
section(2, 126.5, 96, 8.5, "①  调用方 · 谁来用 URRE")
box(4, 127.6, 29, 4.6, "业务应用 / Agent", "Video Domain Agent · 跨域编排", fc="white", ec=NAVY)
box(35.5, 127.6, 29, 4.6, "Domain Pack", "领域策略 · Schema · 过滤规则", fc="white", ec=NAVY)
box(67, 127.6, 29, 4.6, "直接调用方", "简单搜索 / 推荐直调 Port", fc="white", ec=NAVY)
arrow(50, 126.5, 125.3)

# ---------- 2 capabilities ----------
section(2, 115, 96, 10.5, "②  四类一等业务能力 · 路由后进入同一条流水线")
box(4, 117.2, 21.5, 5.4, "Search 搜索", "Query + Filters\n关键词 / 语义 / 视觉", fc=TEAL_L, ec=TEAL, bold=True)
box(27.5, 117.2, 21.5, 5.4, "Recommendation 推荐", "用户 / 任务 / 项目上下文", fc=TEAL_L, ec=TEAL, bold=True)
box(51, 117.2, 21.5, 5.4, "Similarity 相似", "语义 / 视觉 / 属性 / 行为 / 关系", fc=TEAL_L, ec=TEAL, bold=True)
box(74.5, 117.2, 21.5, 5.4, "Explore 探索（远期）", "新颖性 / 长尾发现\n本次不交付", fc=GREY_L, ec=GREY, style=(0, (4, 3)), bold=True)
label(50, 115.9, "统一 API Gateway → 能力路由与请求规范化 · 硬约束由服务端注入，不得被调用方覆盖", fs=10.5, c="#475569")
arrow(50, 115, 113.8)

# ---------- 3 pipeline ----------
section(2, 58, 96, 56, "③  在线处理流水线 · 漏斗 1000 → 200 → 100 → 50 → ≤10 / Clip")
box(22, 109.2, 56, 4.0, "Query 理解 QU", "快链路 <3ms（80% 头部）· 慢链路 15–40ms · 总预算 10–20ms", fc=NAVY_L, ec=NAVY, fs=12.5)
label(82, 111.2, "纠错 / 分词\nNER / 意图 / 改写", fs=10, c="#475569")
arrow(50, 109.2, 108.0)
box(10, 104.0, 80, 4.0, "多路召回 · 11 通道", "关键词 / 语义 / 视觉 / 属性 / 协同 / 上下文 / 关系 / 趋势 / 探索 / 文本转写（ASR·OCR）/ 音频", fc="white", ec=TEAL, fs=12)
label(94, 106.0, "1000", fs=13, c=TEAL, bold=True)
arrow(50, 104.0, 102.8)
box(22, 98.8, 56, 4.0, "合并 / 去重 · RRF 融合（k=60）", "去重键 (tenant, entity_type, entity_id) · 不直接比较原始分数", fc="white", ec=TEAL, fs=12.5)
arrow(50, 98.8, 97.6)
box(22, 93.6, 56, 4.0, "硬约束过滤（排序之前）", "租户 · 对象状态 · 项目权限 · 用户必选条件 —— 不可被高分抵消", fc=ROSE_L, ec="#BE123C", fs=12.5)
arrow(50, 93.6, 92.4)
box(22, 88.4, 56, 4.0, "粗排 Pre-ranking · Two-Tower 打分 + 截断", "千级 → 百级的第一道轻量排序", fc=GREEN_L, ec="#15803D", fs=12.5)
label(82, 90.4, "200", fs=13, c="#15803D", bold=True)
arrow(50, 88.4, 87.2)
box(22, 83.2, 56, 4.0, "精排 Ranking · DNN Ranker", "Cross-Encoder 归此层 · 分数相加前必须校准", fc=GREEN_L, ec="#15803D", fs=12.5)
label(82, 85.2, "100", fs=13, c="#15803D", bold=True)
arrow(50, 83.2, 82.0)
box(22, 78.0, 56, 4.0, "重排 Reranking · 多样性 / 新鲜度 / 探索 / 业务策略", "集合级公式 · MMR λ=0.7 · 探索比例 10%（新用户 20%）· 已冻结为生产值", fc=GREEN_L, ec="#15803D", fs=12)
label(82, 80.0, "50", fs=13, c="#15803D", bold=True)
arrow(50, 78.0, 76.8)
box(22, 72.8, 56, 4.0, "证据组装 Evidence", "summary + evidence_refs · 重新校验权限 · 不暴露源文件地址", fc="white", ec=TEAL, fs=12.5)
arrow(50, 72.8, 71.6)
box(14, 66.6, 72, 5.0, "CandidateSet v1.1（唯一权威）", "candidate_set_id · candidate_id · score_breakdown · index_manifest_id · is_explore · evidence_sufficiency", fc=AMBER_L, ec=AMBER, fs=13, bold=True)
label(89.5, 69.1, "≤10\n/ Clip", fs=12, c=AMBER, bold=True)
label(50, 64.6, "Agent 只处理小候选集：shortlist ≤10 / Clip，评估只产 selection_reason 与证据标记，不改相对顺序", fs=10.5, c="#475569")
label(50, 62.2, "对象层级：Video → Clip 两级，Clip 是唯一片段层级 · 计划侧 storyboard_clip_id 与素材 clip_id 是不同命名空间", fs=10.5, c="#475569")
label(50, 59.8, "LLM Listwise 仅离线评估，不进在线重排 · 高频链路不依赖 LLM", fs=10.5, c="#475569")
arrow(50, 58, 56.8)

# ---------- 4 shared services ----------
section(2, 45.5, 96, 11, "④  共享服务 · 四类能力共用，策略与模型分开")
box(4, 47.6, 21.5, 5.6, "Domain Strategy Registry", "策略 / Profile\n注册与版本化", fc=PURPLE_L, ec="#6D28D9", fs=12)
box(27.5, 47.6, 21.5, 5.6, "Feature Service", "特征版本\n存储与读取", fc=PURPLE_L, ec="#6D28D9", fs=12)
box(51, 47.6, 21.5, 5.6, "模型服务", "Embedding / Two-Tower\nDNN Ranker / Reranker", fc=PURPLE_L, ec="#6D28D9", fs=12)
box(74.5, 47.6, 21.5, 5.6, "索引（B篇）", "ES 全文 · Qdrant 向量\nPayload 硬过滤", fc=GREY_L, ec=GREY, style=(0, (4, 3)), fs=12)
label(50, 46.4, "Search 与 Recommendation 可共享基础设施，但目标函数、标签、模型版本、评估集必须独立", fs=10.5, c="#475569")
arrow(50, 45.5, 44.3)

# ---------- 5 data plane (B) ----------
section(2, 30.5, 96, 13.5, "⑤  数据加工与索引发布（B篇 · 未来真实 URRE 2.0）", fc="#E2E8F0")
for i, (t, s) in enumerate([
        ("Ingest 接入", "登记 · 校验\n不可变原件"),
        ("Processing 加工", "转码 · 抽帧\nClip 切分 · ASR/OCR"),
        ("Embedding", "文本 / 视觉\n多模态向量"),
        ("Indexing 索引构建", "ES 文档\nQdrant Point"),
        ("Manifest 校验发布", "Draft → Validated\n→ Active（唯一原子点）")]):
    x = 4 + i * 19
    box(x, 33.6, 17, 7.6, t, s, fc="white", ec=GREY, style=(0, (4, 3)), fs=12, sub_fs=10)
    if i < 4:
        ax.add_patch(FancyArrowPatch((x + 17, 37.4), (x + 19, 37.4), arrowstyle="-|>",
                                     mutation_scale=18, lw=2, color=GREY))
label(50, 32.0, "版本链：content → metadata → snapshot → processing_profile → embedding_model → index_profile → index_manifest · 幂等键以 DM §4.4 为准",
      fs=10.5, c="#475569")
arrow(50, 30.5, 29.3)

# ---------- 6 feedback ----------
section(2, 18.5, 96, 10.5, "⑥  反馈闭环 · 事件 → 画像 / 训练 / 评估 / 实验")
box(4, 20.6, 21.5, 5.6, "反馈事件（点分式）", "impression / clicked\nadopted / timeline_added", fc=TEAL_L, ec=TEAL, fs=11.5)
box(27.5, 20.6, 21.5, 5.6, "在线画像", "短期上下文更新\n不把未点击当负反馈", fc="white", ec=TEAL, fs=11.5)
box(51, 20.6, 21.5, 5.6, "离线训练样本", "Search / Rec 分别评估\n四类评估集", fc="white", ec=TEAL, fs=11.5)
box(74.5, 20.6, 21.5, 5.6, "策略与 A/B 实验", "离线 NDCG ≠ 线上效果\n须对应验证", fc="white", ec=TEAL, fs=11.5)
label(50, 19.4, "必填归因：candidate_set_id · candidate_id · exposure_position · strategy_id/version · index_manifest_id", fs=10.5, c="#475569")
arrow(50, 18.5, 17.3)

# ---------- footer frozen ----------
section(2, 1.5, 96, 15.5, "⑦  v2 冻结要点 · 与源文档冲突时以 v2 文档为准", fc="#FEF3C7")
items = [
    ("CandidateSet v1.1", "DM §8.5/§9.7 唯一权威；02 §7 降格示意"),
    ("Qdrant 默认选型", "冻结；部署参数待验证；命名 urre_{pool}_{domain}_{space}_{major}"),
    ("融合", "召回 RRF k=60；精排乘性幂次 1.5 / 1.0 / 0.8（初始值）"),
    ("多样性 / 探索", "MMR λ=0.7；探索 10% / 新用户 20%（生产值，Phase F 验证）"),
    ("延迟 SLO（提案值）", "在线 P95 ≤500ms · P99 ≤1000ms；QU / 召回 / 精排 / 重排分段预算"),
    ("Explore", "远期能力：本次无 Tool / 路由 / 端点 / 验收"),
]
for i, (t, s) in enumerate(items):
    r, c = divmod(i, 2)
    x = 4 + c * 48
    y = 12.6 - r * 3.4
    ax.text(x, y + 1.2, "◆ " + t, ha="left", va="center", fontproperties=BOLD, fontsize=11.5, color="#0F172A")
    ax.text(x + 1.5, y - 0.9, s, ha="left", va="center", fontproperties=REG, fontsize=10.5, color="#475569")
label(50, 3.0, "三项决策已冻结（2026-11-16）：U-1 重试上限 3 次 · 指数退避 2s→4s→8s  ·  U-2 直接基于 Acore Runtime SDK 0.2.0（内部封装 AgentScope Java 2.0）  ·  U-3 探索 10%/20% · MMR λ=0.7 已冻结为生产值",
      fs=10.5, c="#92400E", bold=True)

out = "/home/hatch/workspace/search-rec-docs/urre-v2/output/URRE架构设计方案图_v2.png"
plt.savefig(out, dpi=150, facecolor="white")
print("saved", out)
