# B 组分析：URRE 调用侧与排序精读

> 分析组：B（检索调用侧与排序）
> 精读范围：
> - `03_Agent架构设计.md`：§5.2 八个 Tool、§5.3 阶段五 Retrieval Planning 与阶段六 Candidate Retrieval、§5.4 Prompt、§9 数据事件与可观测性、§10 端到端示例的检索步骤（grep 定位，未通读 2485 行全文）
> - `04_开源项目源码解析与设计指南.md`：§4.5 Recommendation Strategy、§4.4 Search Planner、§9 评估指标体系（另核对 §2.6 VideoRecommender、§5.5 API 举例、§7.3 质量门槛）
> - `urre/Query 语义理解.md` 全文、`urre/搜推排序.md` 全文
> - `02_URRE架构设计.md`：§4 四类能力、§5 流水线、§7 结果契约、§8 反馈、§9 指标（另核对 §6 Domain Strategy Contract、§12 验收）
> 约定：`02` = `02_URRE架构设计.md`；`03` = `03_Agent架构设计.md`；`04` = `04_开源项目源码解析与设计指南.md`；`QU` = `urre/Query 语义理解.md`；`排序` = `urre/搜推排序.md`。
> 重要前提：03 §7 / 04 §5.5 多次把 CandidateSet、API 详细设计、字段级权威指向工作区外的 `implementation/01`，但工作区内**没有 `implementation/` 目录**，因此 CandidateSet 的权威定义在本组精读范围内**无法核验**，下文所有“提炼出的契约”均为从五份材料中拼合的最小公共部分，并逐项标出缺口。

---

## 1. URRE 对外调用契约提炼

### 1.1 四类能力的输入输出（拼合版）

| 能力 | 02 定义的输入（02 §4） | 03 的调用入口（03 §5.2） | 04 的补充 | 输出（拼合） |
|---|---|---|---|---|
| Search | Domain、Query、Filters、Scope、User/Tenant Context、Pagination（02 §4.1） | `search_video_materials`，输入 SearchPlan，输出 CandidateSet Ref，Scope `video.material.search` / L0 | Search Planner（04 §4.4）：解析意图→识别主体/动作/场景/Clip 类型/情绪/时间/地域/技术约束→生成多子查询→选通道→混合召回；简单查询直调 Search API | CandidateSet（02 §7 结果 JSON：`request_id / domain / capability / strategy_version / items[] / trace`） |
| Recommendation | Domain、User、Scene、Task Context、Project Context、Current State、Constraints（02 §4.2） | `recommend_video_materials`，输入 Recommendation Context（未定义 Schema），输出 CandidateSet Ref，Scope `video.material.recommend` / L0 | 三种策略 A 搜索增强 / B 任务驱动 / C 主动推荐（04 §4.5）；调用示例 JSON（04 §2.6.3）：`scene_id / query / project_id / user_id / constraints / strategy{content_relevance, project_fit, user_preference, diversity, freshness} / top_k` | CandidateSet；但 02 §4.2 明确“排序不能简单等于预测点击率”，须兼顾采用率、任务帮助程度、内容质量、多样性、新颖性、业务价值、长期满意度 |
| Similarity | 未给输入清单，只定性“支持语义/视觉/属性/行为/关系相似，调用方应声明相似目标，避免把画面相似误解为主题相似”（02 §4.3） | `find_similar_materials`，输入 Seed + `similarity_targets`，输出 CandidateSet Ref，Scope `video.material.similar` / L0 | 无独立章节；QU §五 以图搜图（YOLOv8/Grounding DINO + SAM 2 主体检测、去水印/黑边）可视为图 Seed 的输入处理 | CandidateSet；相似目标枚举、阈值、top-k 均未定义（见 §3 B-07） |
| Explore | 未给输入清单，只定性“主动扩展候选空间，强调新颖性、覆盖度、长尾发现和潜在机会；探索结果应与常规相关性结果区分标记，避免把低相关候选伪装成高相关结果”（02 §4.4） | **03 八个 Tool 中没有 Explore 入口**（见 §3 A-02） | 仅在 VideoRecommender 链路末端出现“Diversity / Explore”阶段（04 §2.6.2）与主动推荐策略中的“新素材探索”（04 §4.5 C），无 API、无标记契约 | 未定义；且 02 §12.1 明确 Explore **不进入本次交付门槛** |

**共性约束（四类能力共享，02 §3 / §5 / §11）：**

- 四类能力路由后进入**同一条流水线**：请求规范化 → Query/Context 理解 → 召回策略选择 → 多路召回 → 合并/去重 → 权限与硬约束过滤 → 主排序 → 重排 → 证据组装 → 结果（02 §5 流程图）。
- 硬约束（租户、对象状态、项目权限、用户必选条件、领域硬规则）**必须在排序与重排之前生效**，且不能被高相关性分数抵消（02 §5.2；02 §3）。
- 高频链路尽量短，离线训练、索引构建、复杂内容理解不进入在线关键路径；高频 Search/Recommend **不依赖 LLM** 才能完成（02 §3、§11）。
- 对象层级只有 Video / Clip 两级，Clip 是唯一片段层级；计划侧 `storyboard_clip_id` 与素材侧 `clip_id` 是不同 ID 命名空间，不得混用（02 §6.1；03 §5.3 阶段三、§5.4）。

### 1.2 CandidateSet：提炼出的最小契约与缺口

03 在三处以不同措辞反复要求统一契约，但**没有任何一份材料给出 CandidateSet 的字段定义**：

- “Direct 检索与 Agent 检索必须经过同一 Retrieval Port 和 CandidateSet 契约”（03 §2.4 边界清单）；
- “简单检索不启动 Agent。Direct Search、Direct Similar、Direct Recommendation 与 Agent 路径必须返回相同 CandidateSet 契约”（03 §3.1）；
- “Direct API 与 Agent 路径返回统一 CandidateSet”（03 §5.3 阶段六）；
- 02 §7 的结果 JSON 是最接近的定义，但该节自述“该结构是概念契约，具体字段由 API 详细设计进一步规范”，且字段级权威指向工作区缺失的 `implementation/01`。

从 02 §7 + 03 各处拼合，CandidateSet 至少应包含：

| 字段/要素 | 来源 | 状态 |
|---|---|---|
| `request_id`、`domain`、`capability`（`search / recommendation / similarity / explore`）、`strategy_version` | 02 §7 结果 JSON | 已定义（概念级） |
| `candidate_set_id` | 03 §9.1 核心关联 ID 清单中有 `candidate_set_id`；02 §7 JSON 中**没有该字段** | **不一致**（见 §3 A-01） |
| `items[]`：`entity_id`、`entity_type`（`video / clip`）、`score`、`rank`、`recall_channels[]`、`matched_requirements[]`、`evidence{summary, time_range{start_ms, end_ms}, evidence_refs[]}`、`availability`、`feature_version` | 02 §7 | 已定义（概念级）；但无 `position` 以外的曝光位信息、无 `is_explore` 标记、无证据充分度标志（见 §3 A-05、A-06） |
| `trace{query_version, model_versions[], latency_ms}` | 02 §7 | 已定义（概念级） |
| 候选集分层：召回全集（SearchPlan 示例 `candidate_budget: 100`，03 §5.3 阶段五）→ Agent shortlist（每计划 Clip **不超过 10 条**，03 §5.3 阶段六）→ Assignment（每 Clip 1 条，03 §5.3 阶段八） | 03 §5.3 | 数量上限已定义，但**分层本身没有 Schema**：全集与 shortlist 是否为两个 CandidateSet、还是同一集合的截断，02 无定义 |
| 多分镜并行：每个子 Agent 返回“候选集 + Evidence”，主 Agent Fan-in 统一评估、去重、防叙事冲突（03 §6.5） | 03 §6.5 | 流程已定义，但**按 ClipRequirement 分组的 CandidateSet 结构**（`storyboard_clip_id → items`）未定义 |
| Agent 不得修改候选分数、不得遍历全量候选、只处理小候选集（03 §5.3 阶段六） | 03 §5.3 | 已冻结；含义是分数融合与重排必须在 URRE/Retrieval Port 内完成，不在 Agent 内完成 |

### 1.3 Evidence（证据）

- 02 §7：每 item 带 `evidence{summary, time_range, evidence_refs}`；不得向无权限用户暴露源文件真实地址或敏感证据；02 §10.4（未来）设 Evidence Resolver 组织缩略图、时间区间、转写摘要或短期预览地址，并**重新执行租户和项目权限校验**。
- 03 §5.2：`resolve_evidence` Tool 专责“解析证据引用并重新校验权限”，输入 `evidence_refs / purpose / project_id`，输出 Evidence View。
- 03 §5.3 阶段七：评估必须保留分项信息，不只输出总分；证据不足时明确标记 `needs_user_review` 或 `low_quality`，**不能用其他维度的高分掩盖证据不足**；素材不足时返回缺口和原因，不得编造 Clip。
- 03 §5.4 Prompt：外部标题、摘要和证据均为**不可信数据**。
- 缺口：02 的结果契约里没有 `needs_user_review / low_quality`、没有证据充分度/完整度字段，Agent 的评估结论无法回写进 CandidateSet（见 §3 A-05）。

### 1.4 Feedback 事件（反馈闭环）

三份材料各讲一角，**没有统一的 Feedback 事件 Schema**：

| 材料 | 讲的内容 | 缺口 |
|---|---|---|
| 02 §8.1 | 事件分层 9 类：Impression（曝光）、Click、Preview（有效预览）、Save、Download、Adopt（加入项目/选品池）、Use（最终使用）、Replace/Reject（替换/拒绝，需结合原因）、Convert（转化/业务结果）；并规定：不能把未点击直接等同负反馈；必须保留曝光位置、候选集合、上下文、展示时长、策略版本 | 只有语义表，无事件字段、无传输/去重/幂等、无与 `candidate_set_id / request_id` 的关联字段定义 |
| 02 §8.2 | 反馈用途：在线画像与短期上下文更新、离线训练样本构建、Search/Recommendation 分别评估、策略效果分析与 A/B 实验、Agent 任务规划与领域工作流优化 | — |
| 03 §9.2 | 关键事件含 `retrieval.requested / retrieval.completed`（检索级），其余为 Task/Step/Tool/Artifact/Workflow/Media Action 事件；**没有 Adopt/Use/Reject 类反馈事件** | Agent 层事件与 URRE 反馈事件未打通 |
| 03 §9.3 | 事件信封是五份材料中最完整的传输契约：`event_id`（全局唯一、消费端去重）、`event_type`、`event_version`、`aggregate_type / aggregate_id / aggregate_version`（单调递增、旧版不得覆盖新版）、`occurred_at`、`tenant_id / project_id`、`trace_id / correlation_id`、`causation_id`、Schema 校验后的 `payload`；业务状态变更与 Outbox 记录同事务提交；至少一次投递；SSE 只传状态、不作事实源 | 该信封是为控制面事件（Task/Workflow/Action/Artifact）定义的，**未说明反馈事件是否复用同一信封** |
| 04 §2.6.4 | 推荐信号至少区分 11 类：曝光、点击、预览开始、预览时长、收藏、加入项目、加入时间线、下载、实际使用、删除/跳过、完成导出；并强调“加入时间线”和“最终成片实际使用”比普通点击更接近真实价值；必须保留曝光上下文和位置 | “加入时间线”在 02 §8.1 的 9 类中**无对应项**（最接近 Adopt/Use，但不等价）；“删除/跳过”与 02 的 Replace/Reject **命名不一致**（见 §3 C-02） |
| 04 §5.5 | 调研用 API 举例中有 `POST /api/v1/feedback/events`，但自述“不是建议契约，实施时不得照此开工” | 只有路径，无 Schema |

### 1.5 关联 ID 与可观测性（调用侧）

- 03 §9.1 要求 15 个关联 ID 能串起“用户请求 → Task → Plan → Step → Agent Run → Tool Call → Domain Service → Artifact → Workflow → 最终结果”，其中与检索直接相关的是 `request_id / trace_id / task_id / tool_call_id / candidate_set_id`。
- 03 §9.4 存储边界：控制面唯一数据库 PostgreSQL 16，核心表含 `video_tool_call`、`creative_event_outbox` 等；Artifact 业务内容由领域 Owner 管理。
- 02 §9.3 平台指标：吞吐、P95/P99、召回通道可用率、超时率、索引延迟、特征新鲜度、模型版本分布、单位请求成本；02 §9.1/§9.2 分别列 Search 与 Recommendation 指标（见 §2.4）。
- 缺口：检索链路的**分段延迟**（QU、召回、排序、重排各段）无埋点要求；无 SLO 数值（见 §3 D-01）。

---

## 2. 排序链路应如何落到 URRE 设计中

### 2.1 漏斗全貌（五份材料拼合后的目标形态）

```
Query / Context 理解（QU，快慢双链路，§2.2）
  → 召回策略选择（SearchPlan / Recall Strategy，§2.3）
  → 多路召回（9 通道，02 §5.1）→ 合并 / 去重 / RRF 融合（§2.3）
  → 硬约束过滤（权限/状态/项目范围，排序之前，02 §5.2）
  → 粗排（缺位，见 §3 B-01）：千级 → 百级（candidate_budget=100）
  → 精排 DNN Ranker（百级 → 数十级，02 §5.4）
  → 重排 Reranker + 多样性/新鲜度/探索比例/业务策略（02 §5.3）
  → 证据组装 → CandidateSet（02 §7）
  → Agent 侧：shortlist ≤10 / Clip → 分项评估（不改分，03 §5.3 阶段六~七）→ Assignment
```

### 2.2 QU：快慢双链路是唯一有数字的链路设计，应整体落入 02 §5

QU 文档给出的工业级方案由 5 个通用模块 + 5 个视频特有模块 + 快慢双链路组成，而 02 §4.1 Search 链路第 1–2 步只写了“Query 规范化与结构化”“领域实体与属性识别”，02 §5 流程图的 UNDER 节点没有任何子步骤。落点建议：

| QU 模块（QU 文档章节） | 内容要点 | 在 02 中的落点 |
|---|---|---|
| 一、预处理与纠错 | 繁简/全半角/大小写归一化、去停用词；编辑距离 + N-gram + 拼音混淆集；MacBERT/BART 纠错 | 02 §5 NORM 节点下新增；目前 02 完全未提纠错 |
| 二、分词与词权重 | 多粒度分词（精确模式保召回 / 搜索模式保实体）；核心词 vs 修饰词权重（如“手机壳”0.9、“华为 Mate60”0.7、“硅胶”0.4）；BERT+BiLSTM+CRF 输出 Token 重要性 0~1 | 02 §5.1 Keyword Recall 的前置输入；02 无词权重概念 |
| 三、NER 与结构化解析 | 槽位抽取（价格区间/品牌/性别/功能/品类）+ 实体链接归一化（如“钩子”→ Nike、`200左右` → `[150,250]`）；BERT-CRF / GlobalPointer / 蒸馏 Qwen 输出 JSON 槽位 | 02 §4.1 步骤 2“领域实体与属性识别”的展开；对应 03 ClipRequirement 的 `hard_constraints`（如 `aspect_ratio: 9:16`）与 `soft_preferences`（03 §5.3 阶段四） |
| 四、意图识别与类目预测 | Query-to-Category Top-K 及概率；意图路由（导航型 / 问答型 / 交易型）；TextCNN/FastText + BERT 多标签 | 02 §4.1 未提意图路由；对应 03 §5.3 阶段一 Intent Understanding 与 03 §3.1 R0–R4 路由，但两处路由的衔接未定义（见 §3 B-08） |
| 五、改写与语义扩展 | 同义词/上下位词、双塔向量改写（BGE/E5）、LLM 生成式改写（复杂 Query 生成 3~5 个标准搜索词多路并发） | 02 无改写步骤；对应 03 §5.3 阶段五 SearchPlan 的 `sub_queries`（见 §3 B-06） |
| 视频一、跨模态联合向量编码 | CLIP/SigLIP/BLIP-2/InternVideo2；文搜图/文搜视频双塔；CIR（参考图 + 修改文本 → BLIP-2 Q-Former / VLM 融合编码） | 02 §5.1 Semantic/Visual Recall 的模型选型依据；02 §5.4 Embedding Service 行 |
| 视频二、视觉与时空要素拆解 | 静态槽位（主体/颜色/材质/纹理/款式/构图风格）与动态槽位（动作/事件、运镜、慢动作、BGM 意图） | 03 ClipRequirement 的 `visual_goal / soft_preferences / evidence_requirements` 的来源；02 无对应槽位表 |
| 视频三、抽象意境的视觉画面翻译 | VLM/LLM 把“氛围感/高级感/松弛感”翻译成客观视觉元素组合再编码 | 02 无；属于改写模块的视频特化，应与 SearchPlan 生成规则一并冻结 |
| 视频四、多维度索引对齐 | 按 Query 意图路由到 4 路索引：画面视觉流（关键帧）、ASR 流、OCR 流、音频指纹/BGM 流；教程类重 ASR/OCR、美学类重 Visual | 02 §5.1 召回通道中**没有 ASR/OCR/音频通道**（见 §3 B-05）；这是视频 QU 与 02 召回层最大的结构缺口 |
| 视频五、以图搜图 Query 理解 | YOLOv8/Grounding DINO + SAM 2 主体检测抠图、质量评估与去水印/黑边/摩尔纹 | 02 §4.3 Similarity 的图 Seed 输入处理；02 未定义 |
| 六、快慢双链路 | 快链路：80% 头部高频 Query，离线预计算 + Redis 缓存 + Trie + 量化 TinyBERT/FastText，**<3 ms**；慢链路：20% 长尾复杂 Query，GlobalPointer NER + 蒸馏 Qwen/BERT 实时改写解析，结果异步写回缓存，**15~40 ms**；QU 阶段总预算通常 **10~20 ms** | 02 §3 只说“高频请求链路应尽量短”，无快慢分流、无缓存设计、无 QU 预算（见 §3 D-01）；注意与 03 SearchPlan 示例 `max_latency_ms: 8000` 的量级冲突（见 §3 D-02） |

### 2.3 召回：通道对照与合并规则

02 §5.1 的 9 个通道与 03/04/QU 的通道清单**不完全重合**，拼合对照如下：

| 02 §5.1 通道 | 03 SearchPlan 示例（03 §5.3 阶段五） | 04 §4.4 通道 | QU 视频四路 | 备注 |
|---|---|---|---|---|
| Keyword Recall | `keyword` | BM25/倒排 | — | 一致 |
| Semantic Recall | `semantic` | 文本 Embedding | — | 一致 |
| Visual Recall | —（示例未列） | 图像/视频 Embedding | 画面视觉流 | 03 示例缺 visual，应补 |
| Attribute Recall | `metadata`（命名不一致） | 标签和元数据过滤 | — | **命名冲突**：02 叫 Attribute，03 叫 metadata（见 §3 B-04） |
| Collaborative Recall | — | —（04 §2.6 有协同召回） | — | 03 检索计划不体现协同信号 |
| Context Recall | —（隐含在 Recommendation Context） | — | — | 只在推荐侧出现 |
| Relation Recall | — | — | — | 三处均未展开 |
| Trend Recall | — | — | — | 只在 02 出现，无定义 |
| Exploration Recall | — | —（04 §2.6 链路末端有 Explore 阶段） | — | 见 §3 A-02 |
| —（02 无） | — | OCR/ASR 文本检索 | ASR 流、OCR 流 | 04 与 QU 有，02 无（见 §3 B-05） |
| —（02 无） | — | 外部互联网搜索 | — | 04 独有；02 的 Domain Pack 与租户边界是否允许外网召回未定 |
| —（02 无） | — | 用户指定素材库或项目范围 | — | 实为 Scope/过滤条件，不应与召回通道并列 |
| —（02 无） | — | Clip 级/时间片段级检索 | — | 02 以 Clip 为对象层级已隐含，但未列为通道 |

合并规则（已达成一致的部分）：

- 关键词与向量**分开召回**：BM25/中文分词/聚合/复杂全文由 Elasticsearch 承担；Qdrant 负责文本向量、视觉向量与相似检索；两类结果在 URRE 内合并、去重和 **RRF 融合**，不在不同存储之间直接比较原始分数（02 §5.5）。
- 每个召回通道应有独立的超时、候选上限、覆盖监控和版本号；通道失败可降级，不导致整条链路不可用（02 §5.1）。
- RRF 公式（排序 §“多 score 融合公式”之 3）：`Score_RRF(d) = Σ_i w_i / (k + rank_i(d))`，`k = 60` 为工业界标准经验值；适用场景正是“分数不在同一量纲时只看排名”，即 BM25（0~35）+ 向量余弦（-1~1）+ 精排 Logit（-10~+10）的合并。
- 去重：02 只在 §4.1 步骤 4 与 §5 MERGE 节点提到“合并/去重”，**去重键未定义**（同一 Video 的多个 Clip、同一 Clip 的不同时间区间是否算重复，见 §3 B-03）。

### 2.4 精排与重排：模型分工与多分数融合的裁决

**模型分工（02 §5.4，已明确，可直接落入 v2）：**

| 模型 | 阶段 | 输入 | 输出与边界 |
|---|---|---|---|
| Embedding Service | 语义索引、召回、相似发现 | Query、Video/Clip 文本、图像、多模态特征 | 向量表示；**不直接决定最终业务排序** |
| Two-Tower | 大规模候选召回 | 用户/上下文塔、对象塔及特征 | 低维匹配表示；用于高效候选发现，**不代替重排**；其召回分数**不能未经校准直接作为最终业务分数** |
| DNN Ranker | 主排序/精排 | Query/Context、候选特征、交叉特征、业务约束特征 | 相关性或任务适配分数；**不改变权限硬过滤结果** |
| Reranker | 小候选集重排 | 排序后的候选、证据、多样性与业务目标 | 最终重排结果；**不负责全量召回** |

**排序 § 的漏斗与 02 的对应（需裁决，见 §3 B-01/B-02）：**

| 排序 § 阶段 | 代表模型 | 耗时（排序 § 对比表） | 对应到 02 |
|---|---|---|---|
| 召回 | BM25（<5 ms）、BGE/E5 双塔（<10 ms）、SPLADE/ColBERT（20~50 ms） | 极快~中等 | 02 §5.1 召回层；ColBERT 的 Token 级延迟交互在 02 中无位置 |
| 粗排 | **排序 § 自称四阶段却无独立章节**（第二节标题为“精排/重排”，粗排内容缺失） | — | 02 §5 同样无粗排节点：千级 → 百级的轻量排序无 owner、无模型（见 §3 B-01） |
| 精排 | Cross-Encoder（BGE-Reranker，百毫秒级）、LambdaMART/XGBoost/LightGBM、DeepFM/DIN/DCN | 10~30 ms（树/深度模型）~百毫秒级（Cross-Encoder） | 02 的 DNN Ranker；但注意术语冲突：排序 § 的 Cross-Encoder 叫 Reranker，与 02 §5.4 的 Reranker（小候选集重排）**不是同一层**（见 §3 B-02） |
| 重排 | LLM Listwise（RankGPT/RankZephyr，前 20 候选）、生成式检索（DSI/TIGER） | 慢 | 02 的 Reranker 只定义了多样性/新鲜度/业务策略，未提 LLM Listwise；且 02 §11 要求高频链路不依赖 LLM，二者需划界 |
| 特征融合 | 两阶段解耦（语义提分 + DCN-v2/DIN，主流、最稳健、10~20 ms）vs 端到端（特征文本化 + DeBERTa/Qwen，50~200 ms）；防“统计特征霸占”：Feature Dropout、多任务 MMoE/PLE（相关性头 + CTR/CVR 头） | — | 02 §5.4 只规定“分数直接相加前必须完成校准；模型缺失/超时/降级时回退规则或轻量排序基线”，**校准方法未定义**（见 §3 B-09） |

**多分数融合公式的裁决（排序 §“多 score 融合公式”共 4 式，均须改造后才能用于 URRE）：**

1. **乘性幂次加权**（排序 § 式 1，主流）：`Score = (S_rel)^α × (p_CTR)^β × (p_CVR)^γ × (Price)^δ`，α/β/γ 通常 0.5~2.0，搜索场景 α 宜大（如 1.5/1.0/0.8），加平滑偏置防极小值崩盘。**URR
...[truncated 17904 chars]
---

## 3. 不一致与缺失清单（逐条，带来源章节）

严重度：🔴 阻塞 v2 冻结（无此定义则无法写契约）；🟡 影响一致性（两处说法不同，需裁决其一）；⚪ 待补（有方向、无细节，可进 v2 附录或后续议题）。

### A. 调用契约类

**A-01 🔴 CandidateSet 无字段定义，且 `candidate_set_id` 两处不一致**
- 02 §7 给出结果 JSON 但自述只是概念契约，字段级权威指向工作区缺失的 `implementation/01`；02 §7 JSON 中**没有 `candidate_set_id`**。
- 03 §9.1 把 `candidate_set_id` 列为 15 个核心关联 ID 之一，要求能串起全链路；03 §5.2 三个检索 Tool 的输出均为 “CandidateSet Ref”。
- 03 §2.4 / §3.1 / §5.3 阶段六三处要求 Direct 与 Agent 返回“同一/统一 CandidateSet 契约”，但契约本身在五份材料中不存在。
- 影响：反馈事件无法关联候选集（02 §8.1 要求保留候选集合、02 §12.1 要求“反馈事件可关联请求、候选集和后续业务结果”无字段可挂）；多分镜 Fan-in（03 §6.5）无法表达 `storyboard_clip_id → items` 分组。
- 落点：v2 必须冻结 CandidateSet Schema（含 `candidate_set_id`、分层、按 ClipRequirement 分组、分页/total、is_explore 标记、证据充分度标志），并补齐工作区缺失的 `implementation/01` 或声明其替代位置。

**A-02 🔴 Explore 是一等能力（02 §4.4），但无入口、无 API、无交付归属**
- 02 §4.4 定义 Explore；02 §5.1 有 Exploration Recall 通道；02 §5.3 要求重排负责“探索比例”。
- 03 八个 Tool（03 §5.2）无 Explore 入口；03 §10 端到端示例全程无探索步骤。
- 04 仅在 VideoRecommender 链路末端（04 §2.6.2）与主动推荐策略“新素材探索”（04 §4.5 C）中顺带提及。
- 02 §12.1 明确 Explore 不进入本次交付门槛。
- 影响：Explore 在 02 §4 是“四类一等业务能力”之一，在交付上又被排除——v2 必须明确裁决：Explore 是 v2 交付、v2 延期、还是仅保留接口占位；同时冻结探索结果的区分标记格式（02 §4.4 只要求“区分标记”，未给字段）。
- 关联缺失：探索比例数值（§3 B-10）、新颖性度量定义（02 §9.2 列出“新颖性”但无定义）。

**A-03 🟡 SearchPlan 两个示例形状不同，且与 02 的 Search 输入不对齐**
- 03 §5.3 阶段五示例：`schema_version / plan_id / domain / target_levels / semantic_query / sub_queries[{role, query, weight}] / hard_filters / recall_channels / candidate_budget: 100 / max_latency_ms: 8000`。
- 04 §4.4 示例：只有 `query / sub_queries[{query, clip_type, weight}] / filters{orientation}`，无 budget、无 latency、无通道、无 `schema_version`。
- 02 §4.1 Search 输入：Domain、Query、Filters、Scope、User/Tenant Context、Pagination——**无 sub_queries、无 candidate_budget、无 max_latency_ms**。
- 03 §5.3 明确“SearchPlan 只作为 Agent Tool 输入，不是独立公开的第二套 Search API”，但 04 §4.4 称“Search Service 并行处理子查询、合并候选、去重和重排”，即子查询的执行方在 URRE 内——那么 SearchPlan 如何进入 URRE（是 Tool 参数直传、还是 Agent 侧展开成多次 Search 调用）未定义。
- 子查询权重示例也不同：03 为 0.5/0.3/0.2（按 role：visual/semantic/scene），04 为 0.35/0.35/0.30（按 clip_type：close_up/wide/medium）——权重语义（role vs clip_type）与归一化方式均未冻结。

**A-04 🟡 召回通道命名不一致：`metadata` vs `Attribute Recall`**
- 03 §5.3 阶段五示例 `recall_channels: ["keyword", "semantic", "metadata"]`。
- 02 §5.1 对应通道叫 Attribute Recall；04 §4.4 叫“标签和元数据过滤”（且放在过滤语境而非召回通道）。
- 影响：通道名是 Domain Strategy Contract（02 §6）的 Recall Strategy IDs 与监控口径（02 §5.1 要求每通道独立超时/上限/覆盖监控/版本号）的键，必须先统一枚举。

**A-05 🟡 证据充分度信号只在 Agent 侧存在，进不了 CandidateSet**
- 03 §5.3 阶段七：证据不足标记 `needs_user_review` / `low_quality`，不得用其他维度高分掩盖；03 §5.3 阶段九 Preflight Gate 检查 Evidence。
- 02 §7 结果契约每 item 只有 `evidence{summary, time_range, evidence_refs}`，无充分度/完整度字段，无上述两个标记。
- 影响：Agent 的评估结论无法以结构化字段回流给 URRE/评估集；02 §9 的指标也无法统计“证据不足率”。

**A-06 🟡 Recommendation Context 无 Schema；04 的调用示例与 02 的输入清单未对齐**
- 03 §5.2 `recommend_video_materials` 输入只写 “Recommendation Context”，无字段。
- 02 §4.2 输入：Domain、User、Scene、Task Context、Project Context、Current State、Constraints。
- 04 §2.6.3 示例 JSON：`scene_id / query / project_id / user_id / constraints{duration_min/max, orientation} / strategy{content_relevance, project_fit, user_preference, diversity, freshness} / top_k: 100`，但自述“权重仅为示例”。
- 三处字段名互不相同（如 02 的 Scene vs 04 的 `scene_id`；02 的 Task/Project Context vs 04 的 `project_id`），且 04 示例把策略权重放进请求体——权重是调用方参数还是 Domain Pack 注册策略（02 §6），未裁决。

**A-07 🟡 Similarity 输入只有“Seed + similarity_targets”，五类相似目标无枚举**
- 02 §4.3：语义/视觉/属性/行为/关系相似，调用方应声明相似目标。
- 03 §5.2：`find_similar_materials` 输入 Seed、`similarity_targets`。
- 两处均未给出枚举值、阈值、top-k、Seed 类型（Video/Clip/图片/文本是否都可作 Seed）；QU §五的图 Seed 处理（主体检测、抠图、去水印）未挂到任何一处。
- 04 无 Similarity 独立章节。

**A-08 ⚪ 意图路由有两套：03 的 R0–R4 与 QU 的意图路由未衔接**
- 03 §3.1：R0–R4 路由（Direct/单 Agent/并行 Agent/跨域 Workflow）；03 §5.3 阶段一 Intent Understanding 解析 task_type（`search / recommend / create / edit / project_qa`）。
- QU §四：意图路由（导航型/问答型/交易型）+ 类目预测 Top-K 及概率。
- 04 §4.5 的三种推荐策略（A/B/C）与上述两套路由均无映射规则：`task_type=recommend` 时走 A、B 还是 C，由什么字段决定，未定义。
- 02 §4.1 Search 链路无意图路由步骤。

### B. 排序链路类

**B-01 🔴 粗排缺位：千级 → 百级没有 owner、没有模型**
- 排序 § 开篇自称四阶段（召回/粗排/精排/重排），但第二节标题即为“精排/重排”，**粗排无独立章节、无模型**。
- 02 §5 流水线同样无粗排节点：RECALL → MERGE → FILTER → RANK → RERANK；02 §5.4 的 Two-Tower 负责“大规模候选召回”，DNN Ranker 负责主排序，中间千级 → 百级（对应 03 SearchPlan `candidate_budget: 100`）的轻量排序无人负责。
- 影响：漏斗在数量级上断档；Agent 的 shortlist ≤10（03 §5.3 阶段六）建立在未定义的 100 条输入之上。
- 落点：v2 须明确粗排是否存在（可声明“Two-Tower 打分 + 截断即粗排”，或新增轻量预排模型），并冻结每级候选规模（如召回 1000 → 粗排 200 → 精排 100 → 重排 50 → shortlist 10）。

**B-02 🔴 “Reranker”一词三义，必须先统一术语再写 v2**
- 02 §5.4 Reranker：小候选集重排，输入排序后候选+证据+多样性与业务目标，**不负责全量召回**（近似重排层）。
- 排序 § 的 BGE-Reranker/Cross-Encoder：Query 与文档拼串做深度交叉，**是精排模型**，只能用于前几十~几百条（百毫秒级）。
- 排序 § 的 LLM Listwise（RankGPT/RankZephyr）：前 20 候选重排；04 §7.3 的 Evaluator 打分亦属事后评估而非在线重排。
- 02 §11 另要求高频链路不依赖 LLM——LLM Listwise 能否进在线重排、还是仅离线评估，三处未划界。

**B-03 🟡 去重规则未定义：去重键是什么**
- 02 §4.1 步骤 4、§5 MERGE 节点、§5.5 均提“合并/去重”，04 §4.4 亦提“合并候选、去重和重排”，但去重键在五份材料中均未定义。
- 待裁决：同一 Video 的多个 Clip 是否算重复；同一 Clip 的不同时间区间（`time_range` 重叠）是否算重复；跨通道同一 entity 的分数/证据如何合并（RRF 只解决分数合并，不解决证据合并）。

**B-04 🟡 召回通道清单三处不重合（见 §2.3 对照表）**
- 02 独有：Collaborative、Context、Relation、Trend、Exploration Recall（04 §2.6 链路有协同召回，但 04 §4.4 通道清单无协同）。
- 04 与 QU 共有、02 缺失：OCR/ASR 文本检索、音频指纹/BGM 流（QU §四的 4 路索引对齐）。
- 04 独有：外部互联网搜索（02 的租户/Domain Pack 边界是否允许外网召回未定）、用户指定素材库或项目范围（实为 Scope，应移出通道清单）。
- 03 示例缺 Visual 通道（见 §2.3 表）。

**B-05 🔴 视频 QU 的多路索引对齐（ASR/OCR/音频）在 02 召回层无落点**
- QU §四：教程/口播类 Query 应重 ASR 与 OCR 索引权重，美学类 Query 走 Visual 向量索引；4 路索引（画面视觉流、ASR 流、OCR 流、音频指纹流）+ 意图路由策略。
- 02 §5.1 的 9 通道中没有任何一路对应 ASR/OCR/音频；02 §10.2 的 Search Projection 虽提及 ASR/OCR/视觉理解是加工产物，但未说明它们如何成为在线召回通道。
- 影响：视频素材“搜台词、搜字幕、搜 BGM”这一核心能力在 URRE 召回层没有接口。

**B-06 🟡 子查询合并规则未定义**
- 03 §5.3 阶段五与 04 §4.4 均要求多子查询（03 按 role、04 按 clip_type），04 §4.4 称 Search Service 并行处理子查询再合并、去重、重排。
- 但子查询结果如何合并（RRF？加权求和？权重即 `sub_queries[].weight` 吗？）在五份材料中均未定义；02 的 Search 输入根本没有 sub_queries 字段（见 A-03）。
- 另：QU §五的 LLM 生成式改写（复杂 Query 生成 3~5 个标准搜索词多路并发）与 SearchPlan 子查询是同一机制还是两套机制，未说明。

**B-07 🟡 推荐目标函数三处都是“建议/示例”，无一有权威值**
- 02 §4.2：定性要求（7 个维度），无公式、无权重。
- 04 §4.5：集合级公式 `Score(S) = αR(S) + βP(S) + γC(S) + δD(S) + εQ(S)`，自述“调研用示意公式（非正式生产门槛，也不是实施指标权威）”，权重“必须通过数据和实验确定”。
- 04 §2.6.3：策略权重示例 0.45/0.25/0.15/0.10/0.05，自述“权重仅为示例……不应由 LLM 任意编造”。
- 02 §5.3 另要求 Search 与 Recommendation 必须有**独立目标函数与评估集**，即使共享模型服务也不共享训练标签与损失函数——该要求正确，但两个目标函数本身均未定义。
- 关联：04 §4.5 的集合级目标（覆盖度 C、互补性 D）与 02 §7 的单 item 打分（`score` 字段）之间缺一座桥：集合优化在哪个阶段发生（Reranker？Agent Assignment？），未定义；03 §5.3 阶段八 Assignment 做跨槽位分配时，是否复用该集合分数，未说明。

**B-08 ⚪ 特征融合：排序 § 的两方案与 02 的校准要求未接线**
- 排序 § 推荐“两阶段特征解耦”（语义提分 + DCN-v2/DIN，10~20 ms）为主流，端到端（特征文本化 + LLM）为低并发备选；并给出防“统计特征霸占”的手段（Feature Dropout、多任务 MMoE/PLE：相关性头 + CTR/CVR 头）。
- 02 §5.4 只规定“分数直接相加前必须完成校准；模型缺失/超时/降级时回退规则或轻量排序基线”，校准方法（Platt/Isotonic/分桶映射？）、回退基线的具体形态均未定义。
- 02 §5.4 另规定 Two-Tower 分数不得未经校准直接作最终分——与排序 § 的 RRF（只看排名、不看分数）结合，可作为冷启动期默认方案，但 v2 须明说。

**B-09 🟡 多分数融合公式须改造后才能用于 URRE（排序 § 4 式逐一批注）**
- 式 1 乘性幂次：含 `(Price)^δ`——视频素材无价格因子，应删除；含 `p_CTR / p_CVR`——02 §4.2 明确推荐排序不能简单等于预测点击率，CTR/CVR 只能作为分量之一，且 04 §9.3 本身警告“点击率不能单独代表推荐质量”；其“一票否决”特性（相关性极低则总分趋近 0）与 03 §5.3 阶段七“不得用其他维度高分掩盖证据不足”方向一致，值得保留为 URRE 融合式的骨架。
- 式 2 对数线性：与式 1 数学等价，数值稳定性更好，适合离线网格搜索/贝叶斯优化调参；可作为式 1 的工程实现形式。
- 式 3 RRF：02 §5.5 已采纳用于 ES+Qdrant 召回合并且 k=60 有据可查；适用边界是“分数不在同一量纲时”，不应推广为精排融合的默认公式（会丢失分数的绝对信息，如相关性是否过线）。
- 式 4 线性加权 + Min-Max/Z-Score 归一化：与 02 §5.4“相加前必须校准”相呼应，但归一化方式（Min-Max 对异常值敏感、Z-Score 抗异常值）与权重求解方式（网格搜索/贝叶斯优化/CEM 进化算法/Meta-Ranker，排序 § 之五）均未冻结。
- 排序 § 之五的权重求解三法（离线贝叶斯优化、线上小流量 CEM/遗传算法、端到端 Meta-Ranker）与 02 §9 的“离线指标与线上业务结果需要对应；不得只通过离线 NDCG 提升宣称产品推荐效果必然提升”原则一致，但 v2 须指定哪一种是默认方法。

**B-10 ⚪ 多样性算法与探索比例：五份材料零算法、零数字**
- 全文 grep：`MMR` 命中 0 次；`多样性`在 02 §4.1/§5.3/§6、03 §5.3 阶段七、04 §2.6/§4.5/§7.3/§9.3 多处被要求，但**没有任何一处给出算法**（MMR、DPP、类目轮询、去重阈值均未出现）；04 §11.5 阅读清单中 `src/recommendation/diversity.py` 只列为待读文件，04 §7.3 的 Evaluator 示例只给了一个多样性反例（“前 5 个候选中 4 个为相同景别的机械臂特写”），未给判定规则。
- 探索比例：02 §5.3 只把“探索比例”列为重排职责，无数值、无按场景区分（如新用户/新项目是否提高探索比）。
- 冷启动：04 §11.5 阅读问题第 2 条“冷启动如何处理？”**以问题形式挂起、未回答**；排序 § 仅在 RRF 适用场景中提及“快速上线冷启动”；02 的 Trend Recall 与热门/趋势内容（02 §4.2 召回来源）可作为隐含的冷启动回退，但未明说；新用户、新素材、新项目三类冷启动均无策略。

### C. 反馈与评估类

**C-01 🟡 指标口径三处不完全一致**
- 02 §9.1 Search：Recall@K、NDCG@K、MRR、零结果率、查询改写率、有效预览率、下载率、任务满足度、P95/P99 延迟。
- 04 §9.2 Search：Recall@K、Precision@K、NDCG@K、MRR、Clip Boundary Accuracy、Query Reformulation Success、Search Zero-result Rate——多出 Precision@K 与 **Clip Boundary Accuracy**（02 的 `time_range` 证据精度在 02 指标中无对应度量）。
- 02 §9.2 Recommendation：Adoption@K、NDCG@K、覆盖度、多样性、新颖性、重复率、任务完成贡献、长期留存/业务价值。
- 04 §9.3 Recommendation：CTR、Preview Rate、Preview Completion、Add-to-Project Rate、Download Rate、Actual Usage Rate、Diversity、Coverage、Novelty、Long-term User Satisfaction——04 保留 CTR 作为指标之一，与 02 §4.2“排序不能简单等于预测点击率”并无字面冲突，但 v2 须明确 CTR 的地位（观测指标而非优化目标），否则易被误读为目标函数。
- 02 §9 未定义离线评估集；04 §9.5 建议四类数据集（查询–相关片段标注集、用户–素材行为序列、brief–分镜–素材组合标注集、EditDecision–人工审核结果集），并要求每次 Prompt/模型/检索策略/排序模型升级都跑固定评估集——该要求应落入 02 §6 Domain Strategy Contract 的 Evaluation Dataset/Metrics 注册项。

**C-02 🟡 反馈事件命名不一致（见 §1.4 表）**
- 02 §8.1：Adopt（加入项目/选品池）、Use（最终使用）、Replace/Reject。
- 04 §2.6.4：加入项目、**加入时间线**、实际使用、删除/跳过、完成导出。
- “加入时间线”无 02 对应项；“删除/跳过” vs “Replace/Reject”命名不同；“完成导出” vs 02 的 Convert 对应关系未说明。
- 03 §9.2 无反馈事件，Agent 侧的采用/拒绝行为无法进入反馈闭环。

**C-03 ⚪ 评估阈值与重试策略只有调研级描述**
- 04 §7.3：生产 Agent 生成 → 独立 Evaluator 分项打分 → 达阈值通过 → 未通过输出失败维度 → 有限次重试 → 保留历史最佳 → 仍未达标交用户确认；分数阈值“应通过人工标注集和线上效果校准，不要直接把示例分数当作生产标准”。
- 02 §9 无阈值、无重试策略；03 §5.3 阶段九/十的 Preflight/Final Quality Gate 检查项（Schema/Contract/Evidence/Technical；版本/血缘/Policy/Human）与 04 的 Evaluator 分项（语义相关性/Clip 覆盖/视觉质量/多样性）未映射。

### D. 性能、降级与可靠性类

**D-01 🟡 延迟预算：QU 有数字，URRE 全链路无 SLO**
- QU §六：快链路 <3 ms、慢链路 15~40 ms、QU 总预算 10~20 ms。
- 排序 § 对比表：BM25 <5 ms、BGE/E5 <10 ms、ColBERT 20~50 ms、Cross-Encoder 百毫秒级、LambdaMART/DeepFM 10~30 ms、特征文本化+LLM 50~200 ms（均为通用参考值，非 URRE 预算）。
- 02 §9 只把 P95/P99 列为指标，无数值目标；02 §11 只要求“支持限流、超时、熔断、缓存和候选上限”。
- 03 §5.2 要求每个 Tool 声明超时、重试、幂等、日志脱敏策略（原则 P12，03 §1.4），但检索类 Tool 的具体超时值未给。
- 04 §9.1 只有 P50/P95 Latency 指标名，无数值。

**D-02 🟡 延迟量级冲突：SearchPlan 示例 `max_latency_ms: 8000` vs QU 10~20 ms**
- 03 §5.3 阶段五示例 `max_latency_ms: 8000`（8 秒）是整个检索计划的预算，与 QU 的 10~20 ms 并不直接冲突（QU 只是其中一段），但五份材料均未给出 8 秒如何分配到 QU/召回/排序/重排/Agent 评估各段，也未说明 8 秒是示例值还是上限。
- 若 8 秒为上限，则与 02 §3“高频请求链路应尽量短”及 02 §11 的高频不依赖 LLM 要求之间缺一张分段预算表。

**D-03 ⚪ 降级策略只有原则，无触发条件与回退形态**
- 02 §5.1：通道独立超时/上限/覆盖监控/版本号，失败可降级；02 §5.4：模型缺失/超时/降级时回退规则或轻量排序基线；02 §11：召回通道可独立降级，模型可替换；02 §12.2（未来验收）：各模型有独立版本、接口边界、降级策略、可归因指标。
- 但“回退到规则或轻量排序基线”的基线是什么（BM25 only？热门回退？）、触发阈值（超时多少毫秒、覆盖率低于多少）、降级期间是否标记结果（与 Explore 的区分标记类似）均未定义。
- 03 的 Tool 治理管线（03 §5.2：Registry → Identity → Policy Gateway → 幂等 → Domain Service → Schema 校验 → Audit/Outbox）与 02 的降级未打通：降级是否走同一管线、是否写 Audit 事件，未说明。

---

## 4. v2 应冻结的清单（建议，不含最终措辞）

按“无此则 v2 无法写成可实施文档”排序，前 6 项为冻结前置：

1. **CandidateSet Schema**（A-01）：字段、 `candidate_set_id`、分层（全集/shortlist）、按 `storyboard_clip_id` 分组、分页与 total、is_explore 标记、证据充分度标志；并补齐 `implementation/01` 的缺失或指定替代权威位置。
2. **四类能力的输入输出表**（§1.1）：补齐 Similarity（枚举、阈值、Seed 类型）与 Explore（入口、标记、交付状态裁决，A-02/A-07）。
3. **漏斗级数与每级规模、模型**（B-01/B-02）：明确粗排是否存在；统一 Reranker 术语；冻结召回→粗排→精排→重排每级的候选规模与模型（含 ColBERT 与 LLM Listwise 的位置）。
4. **融合公式与校准方法**（B-08/B-09）：召回合用 RRF（k=60）；精排融合用乘性幂次骨架（去价格因子、CTR/CVR 降格为分量之一、相关性一票否决）或其对数线性等价形式；冻结校准方法与权重求解方法（离线贝叶斯优化默认）。
5. **QU 落点**（§2.2）：5 通用模块 + 5 视频模块 + 快慢双链路（<3 ms / 15~40 ms / 总 10~20 ms）写入 02 §5；ASR/OCR/音频通道写入 02 §5.1（B-05）。
6. **推荐目标函数**（B-07）：Search 与 Recommendation 的独立目标函数各一；集合级公式 `Score(S)` 的落点（Reranker 还是 Assignment）与权重确定方法。
7. **多样性算法、探索比例、冷启动策略**（B-10）：至少冻结一种多样性算法（建议 MMR 为默认）与探索比例默认值及分场景值；三类冷启动各给一条回退链。
8. **子查询与 SearchPlan 对齐**（A-03/B-06）：统一 SearchPlan 字段、子查询权重语义、子查询合并规则、SearchPlan 进入 URRE 的方式。
9. **Feedback 事件 Schema**（§1.4、C-02）：统一 9 类事件命名（补“加入时间线”“完成导出”的映射），复用 03 §9.3 事件信封，冻结 `request_id / candidate_set_id / position / strategy_version / dwell` 关联字段。
10. **指标口径与评估集**（C-01）：统一 Search/Recommendation 指标清单（含 Clip Boundary Accuracy 的归属、CTR 的地位），冻结 04 §9.5 的四类离线评估集。
11. **分段延迟预算与降级表**（D-01/D-02/D-03）：QU/召回/精排/重排/Agent 评估的分段预算、超时值、降级触发条件与回退基线形态。

## 附录：术语冲突速查

| 术语 | 02 的含义 | 其他材料的含义 | 裁决建议 |
|---|---|---|---|
| Reranker | 小候选集重排（多样性/业务策略），不负责全量召回（02 §5.4） | Cross-Encoder 精排模型（排序 §）；LLM Listwise 重排（排序 §） | v2 统一：Cross-Encoder 归精排；02 的 Reranker 改称“重排层”或保留但加注 |
| 粗排 Pre-ranking | 无此节点（02 §5） | 排序 § 自称四阶段之一但无内容 | v2 明确有无（见 B-01） |
| metadata / Attribute | Attribute Recall（02 §5.1） | `recall_channels: ["metadata"]`（03 §5.3）；“标签和元数据过滤”（04 §4.4） | 统一枚举名 |
| Recommendation | 四类能力之一，输入含 Task/Project Context（02 §4.2） | 三种策略 A/B/C（04 §4.5）；创作型推荐 = 跨 Clip 集合优化（04 §4.5） | v2 明确：能力 vs 策略 vs 集合优化三层关系 |
| 证据 Evidence | 每 item 的 `evidence{summary, time_range, evidence_refs}`（02 §7） | 需 `resolve_evidence` 重校验权限的 Evidence View（03 §5.2）；不可信数据（03 §5.4） | v2 明确：证据引用（ref）与证据视图（view）是两层对象 |
| 反馈 Adopt/Use | Adopt=加入项目/选品池，Use=最终使用（02 §8.1） | 加入项目、加入时间线、实际使用、完成导出（04 §2.6.4） | 统一事件枚举（见 C-02） |
| Explore | 一等能力（02 §4.4），但不进本次交付（02 §12.1） | 推荐链路末端阶段（04 §2.6.2）；主动推荐中的新素材探索（04 §4.5 C） | v2 裁决交付状态（见 A-02） |
