# 02 URRE 检索推荐（最终版 v1.0）

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

## 3. 流水线（10 步，冻结顺序）

规范化 → 理解 → 策略 → 多路召回 → 合并 → **硬过滤（在排序之前）** → 排序 → 重排 → 证据 → 响应。

- 硬过滤必须在排序之前；过滤条件只允许注册字段（注册字段清单见 `04` §2.4，v1.0 冻结清单）。
- 每路召回独立超时、独立上限、独立监控、可降级。通道超时与上限见 §4。
- 融合用 RRF（Reciprocal Rank Fusion），**不得直接比较跨库原始分数**。RRF 参数冻结：`k=60`（标准 RRF 常数，v1.0 冻结值；原始文档只提名字无数值，现补齐）。

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

## 5. 模型分工（语义冻结，v1.0 不训练、不部署模型）

| 模型 | 职责 | v1.0 状态 |
|---|---|---|
| Embedding | 文本/视觉向量化 | 不部署；Mock 返回固定向量/固定分数 |
| Two-Tower | 候选召回打分 | 不部署；分数**不得直接作最终分**（无校准流程，v1.0 不设校准） |
| DNN Ranker | 排序 | 不部署；Mock 返回固定排序 |
| Reranker | 重排 | 不部署；Mock 返回固定重排 |

**诚实声明：** 05 §21 列出的 Embedding 维度、距离度量、HNSW 参数、中文分析器、分块长度、视觉采样密度，全部为**待验证项**，v1.0 不冻结、不承诺。真实 URRE 选型须另立基准（数据集、基准方法、通过标准），见 §8。

## 6. CandidateSet Schema v1.0（唯一权威版）

> 原始文档有三版 CandidateSet（01 §7、05 §8.5 v1.1、impl_01 §5 v1.0），字段名、必填性、版本号各说各话。本最终版冻结为 **Schema v1.0（`04` §3）**，以 impl_01 §5 为底，吸纳 05 §8.5 的 `index_manifest_id` / `manifest_epoch` / `score_normalization_version` 为**可选字段**（Mock 版可为空，真实版必填）。其余 05 特有字段（`candidate_origins` 复数、`source_candidate_set_ids`、`matched_similarity_targets`）**不进入 v1.0**，待真实 URRE 时再议。
>
> 字段表、类型、必填性见 `04` §3。此处只记裁决：`candidate_origin` 用**单数**（impl_01）；`score_breakdown` 含 `visual`（可为 null）；`trace.query_version` 保留；`index_manifest_id` + `manifest_epoch` + `score_normalization_version` 均为**可选（Mock 版可为空，真实版必填）**，`score_normalization_version` 的固定值为 `rrf-v1`。

Search 请求 v1.0 冻结值：`candidate_budget=100`、`deadline_ms=8000`、channels 含 visual、`ranking={strategy_id, strategy_version}`（05 结构为准；impl_01 的 `{strategy_id, limit}` 作废）。

Recommendation v1.0 冻结值：`strategy_id=video_mock_clip_fit_v1`（impl_01 值；05 的 `video-clip-fit` 为真实 URRE 草案值，不采用）；**`selected` 与 `covered_storyboard_clip_ids` 必须一致，不一致时 Schema 拒绝**（05 §8.2 规则为准；impl_01 §4.3 的反例 `covered=[sb_001, sb_002]` / `selected` 仅 sb_001 作废，见 `07` §2 A P0-3）。

## 7. 反馈事件（单一枚举，冻结）

> 原始文档两套命名（业务名 vs 点分名）无映射。本最终版冻结为**点分名为主、业务名为别名**，映射表见 `04` §2.5。

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

## 8. 真实 URRE 2.0 门禁（6 项，全部满足方可启动）

1. Embedding 模型选型 + 维度 + 距离度量冻结（基准通过）
2. HNSW 参数 + 中文分析器版本冻结
3. 分块长度 / 重叠 / 视觉采样密度冻结
4. 评测集 + 标注规范 + 离线评估流程就绪
5. A/B 实验平台就绪（05 §2.2 明确不覆盖，须另立）
6. Active Index Manifest 发布流程在 staging 验证通过

**在门禁满足之前，任何真实索引、真实模型、真实训练工作不得进入 Backlog。**

## 9. 指标（v1.0 数值表）

> 原始文档只列指标名无数值，验收不可执行。本表为 Mock 阶段的冻结数值（**不是生产 SLO**）。

| 指标 | v1.0 目标 | 测量方法 |
|---|---|---|
| Mock 检索 P95 延迟 | <500ms（进程内 Mock） | 固定 Fixture，100 次重复，取 P95 |
| SearchPlan 总预算 | ≤8000ms（deadline） | 见 `04` §2.1 |
| 同一输入 + 同一 Fixture 版本返回稳定排序 | 100% 一致（100 次重复） | 排序结果逐项比对 |
| 零结果率（Mock） | 按 Fixture 预期：空查询返回空集，不返回随机候选 | 固定用例 |
| 跨租户泄漏 | 0 | 隔离测试（见 `05` §6） |
| 覆盖率（PRD §16.3 的 80–85%→95%） | **不在 v1.0 验收范围**（真实检索指标，Mock 无真实语料，无法测量） | 延期至真实 URRE |

## 10. 存储模型（v1.0 冻结）

- 控制面：PostgreSQL 16（唯一数据库）。
- 内容权威：对象存储（Mock 阶段为本地 Fixture 目录，见 `04` §7）。
- 派生可重建：ES / Qdrant / Redis **不在 v1.0**（见 `00` §1）。
- 跨存储一致性：Active Index Manifest 为唯一原子发布点（真实 URRE 时）；v1.0 Mock 无 Manifest，`index_manifest_id` 为可选空值。
- 版本链、幂等键：Processing Key 冻结为 `snapshot_hash + profile_id + profile_version`（05 §4.4 为准；01 §10.3 的另一公式作废）。`data-control-plane` / `source-uploads/finalize` 为悬空引用，v1.0 删除，不采用。
