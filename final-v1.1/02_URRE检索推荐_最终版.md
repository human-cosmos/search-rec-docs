# 02 URRE 检索推荐（最终版 v1.0）

> **v1.1 修订注记（2026-11-16）**：依据覆盖分析（2026-11-16）+ PRD v1.6；本次新增推荐场景与反馈闭环（§11）、记忆读写与遗忘（§12）、行为探针采集（§13）、检索侧补齐（§3 增补 + §14）、资产/收藏/会话在检索侧的落点（§15）；§§1–10 冻结值不动。
> 权威顺序第 3 位。字段级权威见 `04`。本文件只定语义与冻结值；字段、类型、枚举以 `04` 为准。
> 来源：01 URRE + 05 数据模型（检索部分）。

## 1. 定位

URRE = Universal Retrieval & Recommendation Engine（通用检索推荐引擎）。
**v1.0 只交付 Mock Retrieval Port**（Search / Recommendation `clip_candidate` / Similar），真实 URRE 2.0（05 号文档的完整数据加工与索引）是未来基线，**不是 v1.0 的前提**。真实 Adapter 的门禁见 §8。

## 2. 四类能力（冻结）

| 能力 | 定义 | v1.0 状态 |
|---|---|---|
| Search | 按查询返回候选 + 证据 | 交付（Mock） |
| Recommendation | 按上下文/项目返回候选 + 证据；本次仅 `clip_candidate` 场景 | 交付（Mock，单场景） |
| Similarity | 按 Seed 返回相似候选；目标枚举见 `04` §2.3（`semantic` / `visual` 为 v1.0 冻结值；`attribute` / `behavior` / `relation` 为未来值，Schema 中保留但 Mock 不实现） | 交付（Mock，semantic/visual） |
| Explore | 探索性返回新颖候选 | **不在 v1.0**（延期）。01 §4.4 称其与 Search 并列一等，但无接口、无度量——最终版裁决为延期，`novelty_weight` / `max_distance` 字段不进入 Schema v1.0 |

推荐场景对象 `RecommendedScenario`（每个试点槽位类型至少 3 个场景、每场景一段提示词）见 §11.1；Schema 本体见 `04` §9.2。

Explore 结果必须在 CandidateSet 中显式标记探索原因，不能伪装成高相关性 Search 结果（源 05 §8.4；Explore 本身仍延期）。

## 3. 流水线（10 步，冻结顺序）

规范化 → 理解 → 策略 → 多路召回 → 合并 → **硬过滤（在排序之前）** → 排序 → 重排 → 证据 → 响应。

- 硬过滤必须在排序之前；过滤条件只允许注册字段（注册字段清单见 `04` §2.4，v1.0 冻结清单）。注（v1.1）：`product_id` 尚不在 `04` §2.4 注册字段清单内（清单仅 `status` / `duration_ms` / `video_id` / `tenant_id`）；精确商品检索的 ID 相等匹配在意图层执行（见下），02 不改 Schema v1.0。合稿裁决：`04` §2.4 为 v1.0 冻结清单，v1.1 未补 `product_id`；注册字段扩展待 ADR/后续版本。入口层 `product_id` 见 `04` §9.1（`find_hot` 须 `query | product_id | reference_media` 三选一）。
- 商品 ID 检索语义（v1.6 BR-03）：查询含连续至少五位数字、或明确写商品 ID／产品 ID 时，意图层优先判为精确商品检索，先按 ID 相等匹配；无匹配时可展示默认样例。真实同商品纯净结果与零召回待接入，Mock 阶段按 Fixture 行为。商品对象以 PRD §17.2 DR-12 为准（输入 ID 能查到名称和图片）；检索侧只消费 ID 相等结果，不自造商品解析。
- 每路召回独立超时、独立上限、独立监控、可降级。通道超时与上限见 §4。
- 融合用 RRF（Reciprocal Rank Fusion），**不得直接比较跨库原始分数**。RRF 参数冻结：`k=60`（标准 RRF 常数，v1.0 冻结值；原始文档只提名字无数值，现补齐）。

**合并（冻结，源 impl_04 §7.3）：** Search 与 Recommendation 的候选按以下顺序裁决：

1. Clip 时间证据完整。
2. 硬要求覆盖更多者优先。
3. 校准后的任务适配分更高者优先。
4. 与已选 Clip 重复度更低者优先。
5. `clip_id` 稳定排序。

保留全部 `candidate_origins` 和来源 CandidateSet。注：此处 `candidate_origins` 指来源记录概念，字段名冻结为单数 `candidate_origin`，见 `04` §3。

**零结果：** 放宽软条件、调整 Query、请求用户确认，最多执行一次自动 fallback（源 03 §7）。

## 4. 召回通道（9 路，v1.0 实际清单）

| 通道 | v1.0 |
|---|---|
| keyword（关键词） | Mock 实现 |
| semantic（语义） | Mock 实现 |
| visual（视觉） | Mock 实现（Search 请求 channels 含 visual；见 `04` §2.1） |
| attribute（属性） | Mock 实现（硬过滤字段） |
| collaborative（协同） | Mock 返回空路（声明存在，不返回候选） |
| context（上下文） | Mock 实现（项目上下文） |
| relation（关系） | Mock 返回空路 |
| trend（趋势） | Mock 返回空路 |
| exploration（探索） | 不在 v1.0 |

每通道超时：单通道 `≤2000ms`；每通道候选上限冻结为 **100**（= `candidate_budget`），合并后截断至 100；通道降级顺序（冻结）：exploration → trend → relation → collaborative → visual → semantic → keyword → attribute（后者为硬过滤，不得降级）。

每个召回通道应有独立的超时、候选上限、覆盖监控和版本号（源 01 §5.1）。

`metadata` 通道不在 v1.0 9 路清单（impl_04 §7.1 示例值，不采用）。

高频 Search / Recommend 不依赖 LLM 才能完成（源 01 §11）。

## 5. 模型分工（语义冻结，v1.0 不训练、不部署模型）

| 模型 | 职责 | v1.0 状态 |
|---|---|---|
| Embedding | 文本/视觉向量化 | 不部署；Mock 返回固定向量/固定分数 |
| Two-Tower | 候选召回打分 | 不部署；分数**不得直接作最终分**（无校准流程，v1.0 不设校准） |
| DNN Ranker | 排序 | 不部署；Mock 返回固定排序 |
| Reranker | 重排 | 不部署；Mock 返回固定重排 |

**诚实声明：** 05 §21 列出的 Embedding 维度、距离度量、HNSW 参数、中文分析器、分块长度、视觉采样密度，全部为**待验证项**，v1.0 不冻结、不承诺。真实 URRE 选型须另立基准（数据集、基准方法、通过标准），见 §8。

05 §12.4 的具体数值（1024/Cosine/m=32/`ef_construct`=256）未被采纳，仅类别列为待验证（见 §8）。

## 6. CandidateSet Schema v1.0（唯一权威版）

> 原始文档有三版 CandidateSet（01 §7、05 §8.5 v1.1、impl_01 §5 v1.0），字段名、必填性、版本号各说各话。本最终版冻结为 **Schema v1.0（`04` §3）**，以 impl_01 §5 为底，吸纳 05 §8.5 的 `index_manifest_id` / `manifest_epoch` / `score_normalization_version` 为**可选字段**（Mock 版可为空，真实版必填）。其余 05 特有字段（`candidate_origins` 复数、`source_candidate_set_ids`、`matched_similarity_targets`）**不进入 v1.0**，待真实 URRE 时再议。
>
> 字段表、类型、必填性见 `04` §3。此处只记裁决：`candidate_origin` 用**单数**（impl_01）；`score_breakdown` 含 `visual`（可为 null）；`trace.query_version` 保留；`index_manifest_id` + `manifest_epoch` + `score_normalization_version` 均为**可选（Mock 版可为空，真实版必填）**，`score_normalization_version` 的固定值为 `rrf-v1`。

其余 05 特有字段（`matched_requirements`、`trace` 的 `latency_ms`/`degraded_channels`/`model_versions` 等）同样不进入 v1.0，待真实 URRE 时再议。

Search 请求 v1.0 冻结值：`candidate_budget=100`、`deadline_ms=8000`、channels 含 visual、`ranking={strategy_id, strategy_version}`（05 结构为准；impl_01 的 `{strategy_id, limit}` 作废）。

Recommendation v1.0 冻结值：`strategy_id=video_mock_clip_fit_v1`（impl_01 值；05 的 `video-clip-fit` 为真实 URRE 草案值，不采用）；**`selected` 与 `covered_storyboard_clip_ids` 必须一致，不一致时 Schema 拒绝**（05 §8.2 规则为准；impl_01 §4.3 的反例 `covered=[sb_001, sb_002]` / `selected` 仅 sb_001 作废，见 `07` §2 A P0-3）。

## 7. 反馈事件（单一枚举，冻结）

> 原始文档两套命名（业务名 vs 点分名）无映射。本最终版冻结为**点分名为主、业务名为别名**，映射表见 `04` §2.5。注：`recommendation.preview` / `recommendation.saved` / `recommendation.downloaded` / `recommendation.rejected` 四个点分名在 15 篇原文中无出处，为最终版冻结的自造命名；impl_01 §8 的 `material.rejected` 与 `recommendation.rejected` 是否等同未定义。

| 点分名（API 值） | 业务名 | 说明 |
|---|---|---|
| `recommendation.impression` | Impression | 曝光 |
| `recommendation.clicked` | Click | 点击 |
| `recommendation.preview` | Preview | 预览 |
| `recommendation.saved` | Save | 保存 |
| `recommendation.downloaded` | Download | 下载 |
| `material.assigned` | Adopt / Use | 素材被分配（Outbox 产生） |
| `material.replaced` | Replace | 素材被替换（Outbox 产生） |
| `material.final_kept` | Convert（终态保留） | 最终保留（Outbox 产生） |
| `recommendation.rejected` | Reject | 拒绝（显式负反馈；**未点击 ≠ 负反馈**） |

`event_type` 在 DDL 中加 CHECK 约束（枚举见上表；原始 05 DDL `varchar(64)` 无 CHECK，现补齐）。

> v1.1 补充：本节只冻结事件枚举与映射；事件如何作用于下一轮排序、会话内重排与长期偏好，见 §11。跳过/重搜的事件映射在 `04` §2.5 未定义（删除/跳过是否等于 `recommendation.rejected` 未定义），在 04 明确前不得把跳过记为 `recommendation.rejected`；本节冻结规则“未点击 ≠ 负反馈”不变（排序层弱负向信号 ≠ 事件层显式拒绝，见 §11.2）。

## 8. 真实 URRE 2.0 门禁（6 项，全部满足方可启动）

1. Embedding 模型选型 + 维度 + 距离度量冻结（基准通过）
2. HNSW 参数 + 中文分析器版本冻结
3. 分块长度 / 重叠 / 视觉采样密度冻结
4. 评测集 + 标注规范 + 离线评估流程就绪
5. A/B 实验平台就绪（05 §2.2 明确不覆盖，须另立）
6. Active Index Manifest 发布流程在 staging 验证通过

**在门禁满足之前，任何真实索引、真实模型、真实训练工作不得进入 Backlog。**

真实 Adapter 替换门禁与保持清单见 impl_02 §11。

## 9. 指标

### 9.1 Mock 阶段冻结数值表（v1.0）

> 原始文档只列指标名无数值，验收不可执行。本表为 Mock 阶段的冻结数值（**不是生产 SLO**）。

| 指标 | v1.0 目标 | 测量方法 |
|---|---|---|
| Mock 检索 P95 延迟 | <500ms（进程内 Mock） | 固定 Fixture，100 次重复，取 P95 |
| SearchPlan 总预算 | ≤8000ms（deadline） | 见 `04` §2.1 |
| 同一输入 + 同一 Fixture 版本返回稳定排序 | 100% 一致（100 次重复） | 排序结果逐项比对 |
| 零结果率（Mock） | 按 Fixture 预期：空查询返回空集，不返回随机候选 | 固定用例 |
| 跨租户泄漏 | 0 | 隔离测试（见 `05` §6） |
| 覆盖率（PRD §16 召回与推荐行的 80–85%→95%） | **不在 v1.0 验收范围**（真实检索指标，Mock 无真实语料，无法测量）。引用已核实：v1.6 §16 原文「覆盖率从 80–85% 提升至约 95% 是评测目标」（v1.4 图片版时未核实，现以 v1.6 文本为准；07 §5 第 7 项已关闭） | 延期至真实 URRE |

### 9.2 真实 URRE 评估指标名录（定义，无阈值）

> 源 04 §9.1–§9.4 原文抄录。**只登记定义，不补阈值。** 其中 04 §9.2–§9.4 原文只列指标名、未给逐项定义，此处只登记名称，不补定义。

**Agent 任务质量（源 04 §9.1）：**

| 指标 | 定义 |
|---|---|
| Task Completion Rate | 成功完成任务比例 |
| Plan Validity | 计划结构和依赖是否合法 |
| Tool Success Rate | 工具调用成功比例 |
| Tool Recovery Rate | 失败后恢复成功比例 |
| Human Intervention Rate | 需要人工介入比例 |
| Cost per Completed Task | 每个成功任务的模型和工具成本 |
| P50/P95 Latency | 任务耗时分位数 |

**搜索质量（源 04 §9.2，原文只列名，无逐项定义）：** Recall@K、Precision@K、NDCG@K、MRR、Clip Boundary Accuracy、Query Reformulation Success、Search Zero-result Rate。

**推荐质量（源 04 §9.3，原文只列名，无逐项定义）：** CTR、Preview Rate、Preview Completion、Add-to-Project Rate、Download Rate、Actual Usage Rate、Diversity、Coverage、Novelty、Long-term User Satisfaction。附注：点击率不能单独代表推荐质量。曝光位置、素材质量、用户任务和实际使用情况都要纳入分析。

**创作质量（源 04 §9.4，原文只列名，无逐项定义；User Edit Distance 原文附定义）：** Storyboard Coverage、Material Assignment Acceptance、Timeline Validity、Render Success Rate、Revision Count、Human Quality Score、Final Export Rate、User Edit Distance（用户对 Agent 时间线修改幅度）。

### 9.3 监控指标定义（无阈值）

> 源 impl_03 §6 原文登记。已在 05 §6 有数值的 3 项注明落点，其余 11 项注明“无阈值，待真实 URRE/后续阶段冻结”。

| 指标 | 阈值/落点 |
|---|---|
| Direct Search / Recommendation / Similar 不启动 Agent 的比例 | 无阈值，待真实 URRE/后续阶段冻结 |
| Agent Task 完成率 | 无阈值，待真实 URRE/后续阶段冻结 |
| Schema 校验通过率 | 有数值，见 05 §6 S0：全部 JSON Schema 校验 100% 通过 |
| Candidate 证据完整率 | 无阈值，待真实 URRE/后续阶段冻结 |
| ClipPlan 覆盖率 | 无阈值，待真实 URRE/后续阶段冻结 |
| Assignment 接受率和局部重算范围 | 无阈值，待真实 URRE/后续阶段冻结 |
| Tool 成功率、调用次数和耗时 | 无阈值，待真实 URRE/后续阶段冻结 |
| Waiting 恢复成功率 | 无阈值，待真实 URRE/后续阶段冻结 |
| 跨租户泄漏 | 有数值，见 05 §6 全阶段：目标为 0 |
| DomainInvocation 成功、部分成功和失败分类 | 无阈值，待真实 URRE/后续阶段冻结 |
| Fan-out 并行度、fan-in 等待时间和领域重试率 | 无阈值，待真实 URRE/后续阶段冻结 |
| Artifact stale 传播范围和误伤率 | 无阈值，待真实 URRE/后续阶段冻结 |
| 跨域审批拒绝率和未审批发布拦截次数 | 无阈值，待真实 URRE/后续阶段冻结 |
| Video-only 回归通过率 | 有数值，见 05 §6 S6：Video-only 回归全部通过（阶段 4 固定集重跑 100% 通过） |

### 9.4 离线评估集

> 源 04 §9.5 原文抄录。

建议建立四类数据集：

1. 查询—相关片段标注集；
2. 用户—素材行为序列；
3. 创作 brief—分镜—素材组合标注集；
4. EditDecision—人工审核结果集。

升级必跑规则：每次 Prompt、模型、检索策略和排序模型升级，都运行固定评估集，避免只凭 Demo 判断效果。（05 §2 的阶段 6 重跑规则是其子集：阶段 6 须重跑阶段 4 的固定集。）

## 10. 存储模型（v1.0 冻结）

- 控制面：PostgreSQL 16（唯一数据库）。
- 内容权威：对象存储（Mock 阶段为本地 Fixture 目录，见 `04` §7）。
- 派生可重建：ES / Qdrant / Redis **不在 v1.0**（见 `00` §1）。
- 跨存储一致性：Active Index Manifest 为唯一原子发布点（真实 URRE 时）；v1.0 Mock 无 Manifest，`index_manifest_id` 为可选空值。
- 版本链、幂等键：Processing Key 冻结为 `snapshot_hash + profile_id + profile_version`（05 §4.4 为准；01 §10.3 的另一公式作废）。`data-control-plane` / `source-uploads/finalize` 为悬空引用，v1.0 删除，不采用。

## 11. 推荐场景与反馈闭环（v1.1 新增）

> 依据：覆盖分析 §8、§10.2；PRD §17.2 DR-07/08/13/15/19、PRD §17.1 REQ-B02、PRD §16 行为探针行、PRD §17.3 NFR-11、PRD §17.4 OI-02。本节只定检索推荐层的流程、排序/重排规则与事件处理语义；Schema 本体在 `04`。

### 11.1 RecommendedScenario 在检索推荐层的使用

- 对象（覆盖分析 §10.2 必须补充的对象）：`RecommendedScenario`——推荐场景、适配槽位类型和提示词。Schema 本体见 `04` §9.2（字段：`scenario_id` / `category` / `slot_type` / `title` / `prompt_text` / `source_evidence` / `rank`）；`slot_type` 枚举值待确认（PRD 只定 DR-02“槽位类型”，未给枚举；见 OI-02）（`04` §9.2）。
- 数量（PRD §17.2 DR-07）：每个试点槽位类型至少 3 个场景；场景来源为品类 × 槽位的历史较好画面 + 偏好（DR-07）。
- 提示词（PRD §17.2 DR-08）：每个场景一段可提交的提示词；槽位去生成时，可选推荐方案填入提示词，也可自行输入，提交后进度与结果留在当前会话，采用时绑定原槽位（PRD §7）。
- 计算与数据源待确认（PRD §17.4 OI-02）：推荐场景的计算与数据源属 OI-02，v1.1 不定计算方法。Mock 方案：场景取 Fixture 预置（每试点槽位类型 ≥3 个场景，每场景一段提示词）；`04` §9 head 明示新对象暂无 Mock Fixture（§7 的 4 Video / 9 Clip 不变），场景 Fixture 登记见 `04` §13.3 第 11 项。
- 与 Recommendation API 的关系：不改 `04` §2.2 冻结字段（`strategy_id=video_mock_clip_fit_v1`、`limit=20`、归因上下文规则）；场景对象与 `04` §2.2 `context` 的挂接点在 `04` §9.2 未定，待对齐（04 组定）。
- 与 §2 的关系：§2 Recommendation 仍为单场景 `clip_candidate`（Mock）；DR-07/08 是推荐场景的数据准备要求，不是新增 Recommendation API 场景枚举值。

### 11.2 反馈事件的作用规则

- 适用事件：以 §7 冻结枚举为准；本节不新增事件名、不改映射（映射见 `04` §2.5）。
- 当次会话内实时重排（PRD §17.2 DR-15、PRD §16 行为探针行、PRD §17.3 NFR-11、PRD §17.1 REQ-B02）：同一会话内，下一轮 Search / Recommend 请求须携带当次会话已发生的反馈事件归因上下文（`candidate_set_id`、`position`、`strategy_version`，见 `04` §2.5 请求字段与反馈保留字段清单，源 01 §8.1）；重排发生在 §3 流水线“重排”步，不得改写硬过滤（排序之前）与 RRF 融合冻结规则（§3）。Mock 阶段：事件只记录（`04` §2.5），Mock 返回固定排序/固定重排（§5），重排规则为真实 URRE 生效条件。
- 曝光位置与归因上下文（`04` §2.5 `position` 字段；`04` §2.2 归因上下文规则：已选、已覆盖和排除条件必须出现在反馈归因上下文中；反馈保留字段清单：曝光位置、候选集合、上下文、展示时长、策略版本，源 01 §8.1；`04` §12.1 同款口径：曝光上下文无位置字段，待补）：曝光事件必须带 `position`；展示时长保留字段尚无 `duration` 字段承载（`04` §2.5：预览时长未映射），待 04 对齐；槽位点击、跳出、转化按秒归因待确认（PRD §17.4 OI-02）。
- 跳过/重搜负向权重（PRD §17.2 DR-15“未打开”、PRD §16 探针采集“重搜”、覆盖分析 §8）：方向性规则，不冻结量级——同一会话下一轮中，被跳过的候选降权、重搜前的结果集降权；量级（具体权重数值）无来源，不冻结，待 A/B 确定（数值处理类比 `04` §2.2 推荐策略权重结构：数值仅为示例，待验证）。事件层区分：排序层弱负向信号 ≠ 显式拒绝事件；`04` §2.5 未定义删除/跳过到 `recommendation.rejected` 的映射，在 04 明确前不得把跳过记为 `recommendation.rejected`（§7“未点击 ≠ 负反馈”不变）。
- 长期偏好更新（PRD §17.2 DR-13、DR-19；PRD §16 行为探针行：用于长期偏好、漏斗分析和片段预生成）：反馈事件沉淀为隐式喜好；只有经过验证的事实才写入长期记忆（源 04 §6.3，见 §12）；历史行为是证据，不应直接等同于用户永久偏好（源 04 §6.2 D）。
- 显式偏好优先于隐式（PRD §17.2 DR-13：显式设置优先；源 04 §6.3：用户显式纠正优先级高于模型推断）：显式偏好来源为工作台偏好设置（PRD §10）与对话显式纠正；冲突时显式胜出。

### 11.3 Mock 方案与验收占位

- Mock：反馈事件按 `04` §2.5 收录；场景按 Fixture 预置；重排与长期偏好更新不执行（§5 Mock 固定排序）。
- 验收占位：验收锚点为 PRD §17.1 REQ-B02（行为反馈进入下一次检索）与 PRD §17.2 DR-15（实时作用于当次会话）；权重数值、按秒归因（OI-02）关闭后补阈值与用例。

## 12. User / Episodic Memory 读写、修改、删除与遗忘（v1.1 新增）

> 依据：PRD §17.2 DR-13/14、PRD §10 工作台、PRD §17.4 OI-09；源 04 §6.2/§6.3；`01` §9；登记 `07` §5 第 17 项。本节只定检索推荐层的读写语义；Schema 本体在 `04`。

- 对象（覆盖分析 §10.2）：`UserPreference` / `UserMemory`（显式偏好与可管理记忆）。Schema 本体见 `04` §9.9（UserPreference：`preference_id` / `user_id` / `scope` / `key` / `value` / `source` explicit/implicit，显式设置优先 / `updated_at`；UserMemory：`memory_id` / `user_id` / `content` / `source_ref` / `version` / `created_at` / `updated_at`；规则：记忆可改、可删，写入遵循 `01` §9 六原则）。Episodic Memory（历史任务事实分层，源 04 §6.2 D）在 `04` 中无独立对象节，仍为语义分层，节号待对齐；登记出处仍为 `07` §5 第 17 项（User/Episodic 对象此前无落点，`04` §9.9 现补 UserPreference/UserMemory，Episodic 仍待后续阶段）。
- 分层（源 04 §6.2）：User Memory（长期偏好：喜欢的视觉风格、常用画幅/分辨率/节奏、偏好的素材类型、常用创作模板）；Project Memory（项目范围：当前目标、受众、风格、脚本、分镜、素材选择、用户确认过的约束）；Working Memory（当前 Agent Run：当前计划、已完成节点、当前工具结果摘要、下一步、重试次数、预算消耗）；Episodic Memory / Event Memory（历史任务事实：用户曾选择哪些素材、哪些推荐被跳过、哪个版本被导出、用户提出过哪些修改）。
- 写入触发（PRD §17.2 DR-14：用户记忆，对话写入；源 04 §6.3）：对话写入；只有经过验证的事实才写入长期记忆；临时意图只保存在项目或当前任务（源 04 §6.3）；用户显式纠正优先级高于模型推断（源 04 §6.3）。写入六原则全文见 `01` §9。
- 读取范围：检索推荐层读取 User Memory（长期偏好）与 Project Memory（当前项目约束）参与排序/重排（§11.2）；Working Memory 只在当前 Run 内使用；Episodic Memory 只作历史证据读取，不直接等同于用户永久偏好（源 04 §6.2 D）。读取须按用户隔离（PRD §17.2 DR-13：按用户隔离）。完整聊天记录不得反复注入 Prompt（源 04 §6.3）。
- 用户修改/删除入口（PRD §17.2 DR-14：可改、可删；源 04 §6.2 A：用户可以查看、修改和删除；PRD §10：工作台显示偏好和可修改／删除的记忆）：入口为工作台偏好与记忆管理；自用户操作起，后续检索请求不得再使用被删除的记忆条目；已发生的隐式沉淀是否回滚，待确认（无对应 OI 编号，须产品方新增确认项）。记忆要有来源、时间、置信度和版本；记忆更新必须可审计（源 04 §6.3）。
- 遗忘/过期策略：PRD 未定，一律标待确认——记忆遗忘规则（是否按时间衰减、是否按条目过期、除用户手动清理外是否自动遗忘）无 PRD 条款、无对应 OI 编号，须产品方新增确认项；会话与任务保留期属 OI-09（旧版 7 天为暂拟值，PRD §17.4 OI-09），只覆盖会话/任务，不覆盖记忆遗忘，不得混用。Mock 方案：Mock 阶段不删除、不设过期，以 Fixture 行为为准。验收占位：遗忘策略确认后补验收用例（删除后不可见、过期后不可见）。
- 与 §11 的关系：长期偏好更新（§11.2）写入长期记忆时，遵守本节写入触发与审计规则。

## 13. 行为探针 DR-15 / DR-19 采集（v1.1 新增）

> 依据：PRD §16 行为探针行、PRD §17.2 DR-15/19、PRD §17.3 NFR-11；映射见 `04` §2.5。

- 采集项清单（PRD §16 行为探针行 + PRD §17.2 DR-15 并集）：搜索、曝光、打开、未打开、停留、重搜、槽位替换、合成、下载、分享；另 DR-15 的“替换”即槽位替换（采用/替换，见 §7 `material.replaced`）。
- 采集时点：前端探针 SDK 全链路采集（PRD §17.2 DR-19）；非侵入采集，异步批量上报，不阻塞渲染（PRD §17.3 NFR-11）；事件发生时采集（`occurred_at`，`04` §2.5）。
- 与反馈事件的关系（映射见 `04` §2.5 信号—事件映射表与 `04` §12.1 探针映射表，两者口径一致）：

| 探针采集项 | 反馈事件映射（`04` §2.5 / §12.1） |
|---|---|
| 搜索 | 无对应反馈事件；为检索请求本身 |
| 曝光 | `recommendation.impression` |
| 打开 | `recommendation.preview`（`04` §12.1：预览开始；`preview.started` 为未来 UI 遥测，不在 v1.0 枚举） |
| 停留 | 未映射（预览时长无 `duration` 字段） |
| 未打开 / 跳过 | 未映射（是否等于 `recommendation.rejected` 未定义） |
| 重搜 | 未映射（无事件；检索层按 §11.2 作负向信号处理；重搜行为进 DR-19 探针日志） |
| 槽位替换 | `material.replaced` |
| 合成 | 未映射（无事件；进 DR-19 探针日志） |
| 下载 | `recommendation.downloaded` |
| 分享 | 未映射（无事件；进 DR-19 探针日志） |

`04` §12.1 另有两行与本表口径一致：点击 → `recommendation.clicked`；采用 → `material.assigned` / `material.final_kept`（加入项目/实际使用）。

- 用途（PRD §16；PRD §17.3 NFR-11）：本轮检索纠偏（实时重排，见 §11.2）、长期偏好（见 §11.2/§12）、漏斗分析与片段预生成（DR-19：支撑漏斗、偏好沉淀、热搜词统计；DR-03 片段含预生成片段）。
- 区分：本节“探针采集项”是原始信号；`04` §2.5 的反馈事件是 API 层映射；PRD §10 的用户反馈表单（类型功能/数据/体验/新需求，正文必填，最多保存 12 条）是另一对象，不进入检索排序。
- Mock 方案：Mock 阶段探针事件按 `04` §2.5 收录，未映射项只记录不映射；反馈事件的批量聚合与训练样本生成周期属真实 URRE 待验证项（源 05 §21，登记见 `07` §5 第 5 项补记）。

## 14. 检索侧补齐：上传 Seed、整片相似与结果呈现（v1.1 新增）

> 依据：PRD §5 BR-03/05、PRD §7 BR-21/22、PRD §14 AC-04、PRD §17.4 OI-03、PRD §9；覆盖分析 §5。

### 14.1 上传媒体到 Similar Seed 的链路

- 入口（PRD §5）：输入区支持文字、上传或粘贴图／视频；上传入口只在相应卡片上展示（PRD §7）；支持上传的入口接受视频文件，本地播放引用与原片分别保留（PRD §7 BR-22）。
- 链路：上传媒体 → 成为可引用的媒体对象（本地播放引用与原片分别保留，BR-22）→ 以 Seed 参与 Similar（`04` §2.3：Seed 形 `entity_type` clip/video、`video_id` 必填、`clip_id` 条件必填；Similar 不返回 Seed 自身）。上传媒体的视觉理解深度属外部视频实时理解范围，待确认（PRD §17.4 OI-03；PRD §9：外部视频实时理解、自动切片与深度二创为待确认的生产能力）。
- 待对齐：未入库上传媒体尚无 `video_id` / `clip_id` 分配规则，`04` §2.3 现只定义已有 Video/Clip 的 Seed 形；上传媒体如何变成 Seed（临时 ID、入库条件、引用有效期）待 `04` §2.3 对齐。上传动作本身见 `04` §9.4（`action_type=upload`）与 `04` §10，但那是媒体执行动作，不是 Seed 表达。Mock 阶段：只接受已有 `video_id` / `clip_id` 的 Seed。
- 覆盖分析 §5 对应缺口：用户上传媒体、视觉理解、附件到 Seed 的链路缺失——本节补链路语义，字段与 ID 分配待 04。

### 14.2 整片搜相似

- 规则（PRD §7 BR-21）：整片相似只提供整片预览，候选排除自身，按商品、品类、语种、视频类型匹配数排序；至多 4 条整片参考，可查看整片（PRD §7 整片搜相似行）。
- 与槽位 Similar 的区分（PRD §7 BR-21）：槽位候选绑定发起时的槽位 ID，只有点「替换原片段」才写入采用状态，原片、其他槽位和已打开候选保留。
- 与 API 限额的关系：`04` §2.3 Similar `limit` 冻结值 20 不动；BR-21 的“至多 4 条”是整片搜相似的业务呈现上限，呈现层取前 4 条，不是 API 限额变更。

### 14.3 9 卡预览 + 查看全部

- 规则（PRD §5 BR-05；PRD §14 AC-04）：搜索结果对话预览最多 9 张缩略图；少于 9 条也保留「…／查看全部」；再次搜索遵循同一规则；完整结果画布保持收起，点「…」才打开完整列表；点单条缩略图直达对应视频。
- 与检索结果呈现的关系：后端分页（`04` §2.1 `page.size` 默认 20）是 CandidateSet 分页机制，9 卡是对话呈现截断——呈现层取 CandidateSet 前 9 条展示，完整结果数量按当前样例列表计算（PRD §5 BR-05）；完整结果按当前入口与检索条件呈现（PRD §5 找视频结果行）。9 卡规则不改 `candidate_budget=100`（§6）与 `page.size=20`（`04` §2.1）冻结值。
- 验收锚点：PRD AC-04（找片展示）。

## 15. 资产、收藏、会话在检索侧的落点（v1.1 新增）

> 依据：PRD §1 G4、PRD §10、PRD §12、PRD §16、PRD §17.1 REQ-E02、PRD §17.2 DR-16、PRD §17.3 NFR-06/10、PRD §17.4 OI-05/08/09、PRD §7 BR-26、PRD §14 AC-11；覆盖分析 §10.2。

### 15.1 PersonalAsset 状态与检索可见性

- 状态（PRD §17.2 DR-16）：排队、生成中、完成、失败；资产筛选：全部、进行中、已完成、失败（PRD §10）。
- 可见性规则：只有完成态资产进入检索候选池（可检索、可引用）；排队/生成中态尚无结果视频（PRD §10 资产详情含原视频、结果视频、分镜与生成提示词），仅在资产页可见进度，不进入候选；失败态不进入候选。
- 失败态重试：重试契约待确认（PRD §17.4 OI-07：调画幅、合成、口播、图像修改等真实服务及失败重试契约）。
- 隔离与保护期：资产按账号隔离（PRD §16；PRD §17.3 NFR-06）；保护期内仅创建者可见、可分享（PRD §17.3 NFR-10）；产出 15 天保护期后回流公共库（PRD §16；PRD §1 G4；PRD §17.1 REQ-E02）；回流后进入公共检索池，回流后的槽位与提示词补加工待确认（PRD §17.4 OI-05；PRD §16：回流后的槽位与提示词补加工待确认）——回流后是否立即全量可检索，待 OI-05 关闭后定，v1.1 不预设。
- 对象：`PersonalAsset` Schema 本体见 `04` §9.8（字段：`asset_id` / `owner_user_id` / `task_id` / `asset_kind` / `status` queued/generating/completed/failed / `protection_until` 创建时间 + 15 天 / `visibility` owner_only/shared，回流后 public / `reflow_status` protected/reflowed/pending / `source_product_id`；回流后加工与共享交接待确认，OI-05）。

### 15.2 收藏与只读分享链接

- 收藏（PRD §10）：库卡和视频收藏在本机，可在收藏页或收藏车查看；对象见 `04` §12.2（Favorite：`favorite_id` / `user_id` / `entity_type` video|clip / `entity_id` / `created_at`）。检索侧：收藏映射为反馈事件 `recommendation.saved`（`04` §2.5），作为显式偏好信号进入长期偏好沉淀（§11.2/§12），不直接改写当次排序。
- 分享链接（PRD §10；PRD §7 BR-26）：分享弹窗可复制带会话 ID 的链接，当前只打开已有本地快照；对象见 `04` §12.2（ShareLink：`share_id` / `session_id` / `created_at` / `expires_at?` / `access: read_only`）；分享链接要求访问侧已有对应会话快照（BR-26）；跨账号、跨浏览器可访问性和只读授权待确认（PRD §17.4 OI-08）。检索侧：链接本身不携带检索权限；无快照的访问侧不得经链接获得检索结果。
- 待确认：只读权限与有效期待 OI-08 关闭后定；Mock 方案：按原型行为（只打开已有本地快照）。

### 15.3 会话快照与恢复在检索上下文中的含义

- 上限（PRD §12）：会话快照最多 30 条，跟品商品／任务各最多 40 条；反馈（表单）最多 12 条。
- 恢复（PRD §7 BR-26；PRD §14 AC-11）：已完成的会话快照可在同一浏览器恢复；恢复后检索上下文按快照恢复——会话包含消息、画布模式、当前视频和各视频的工作区状态，槽位保存时间、替换引用及操作（PRD §12）；已打开的相似与生成结果按视频/槽位保留（PRD §7 多个结果行：切换操作或槽位保留已打开的相似与生成结果）；运行中的跟品重开会话时继续，暂停状态等待继续操作（PRD §12）；首页技能未完成的流式任务可接续，过期 blob 视频可退回演示素材（PRD §12）。
- 跨端与保留期待确认（PRD §17.4 OI-09）：会话和任务保留期、跨端恢复及资源续存；旧版 7 天为暂拟值。恢复机制见 `03` §2（Session / Checkpoint）与 `04` §5.3（Checkpoint Schema）；会话画布投影见 `04` §9.10，恢复规则见 `04` §11.9（BR-26、PRD §12）。
- 验收锚点：PRD AC-11（会话恢复）。
