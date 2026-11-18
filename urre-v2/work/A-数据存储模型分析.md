# A 组：URRE 数据与存储模型设计精读分析

- **精读对象**：`~/workspace/search-rec-docs/urre/URRE数据与存储模型设计.md`（全文 2395 行，§1–§21）
- **对照对象**：`~/workspace/search-rec-docs/02_URRE架构设计.md`（全文 498 行；下文简称“02”；数据模型文档下文简称“05”，沿用 02 文首所称的编号 `05_URRE数据与存储模型设计.md`）
- **任务边界**：只做要点提炼 + 与 02 的重复 / 冲突 / 缺口清单，不修改源文档，不写最终版文档，不做图片。
- **引用规则**：每条结论都标注来源章节号；凡写“未定义 / 未出现”，均指在两份文档全文检索后无定义（检索词见各条），不是凭印象。
- **版本说明**：05 自称“真实 URRE 2.0 的数据加工、控制面、检索投影和存储模型基线”，02 §10 明确“本次交付不实现 Ingest、Processing、Embedding、Indexing、ES、Qdrant 或 Kafka”，05 的内容全部属于未来真实 URRE，不构成 Mock 交付门禁（05 §1 前言、§2.2、§20.1；02 §10 开头）。

---

## 1. 文档地图：05 各章讲了什么

| 章 | 内容 | 关键结论（提炼） |
|---|---|---|
| §1 设计目标 | 8 个待回答问题 | 事实源归属、版本链、接入 API、ES/Qdrant/Redis 分工、一致索引快照、增量/重建/原子切换、反馈归因 |
| §2 范围与非目标 | 覆盖 / 不覆盖 / 存储职责 / 与现有文档缺口对照 | 明确五类存储权威性：PG 权威、对象存储内容权威、ES/Qdrant 可重建派生、Redis 非权威可全丢（§2.3）；§2.4 缺口对照表是本文的立项依据 |
| §3 总体数据架构 | Mermaid 架构 + 四个工作区 | 接入区 → 加工区 → 索引区 → 发布区；在线查询只读 Active Manifest（§2.3 末条、§3） |
| §4 命名、主键与版本规则 | snake_case、UTC、`_at/_ms/_version/_id`、UUIDv7/v5、逻辑键、版本链、幂等键、Hash 规范 | 版本链 7 环（§4.3）；幂等键 5 个（§4.4）；Hash 全部小写十六进制 SHA-256、JSON 稳定键排序（§4.5） |
| §5 核心数据实体 | §5.1 ER 图；§5.2 Source；§5.3 Snapshot；§5.4 Raw Object；§5.5 Input Artifact；§5.6 Processing Profile；§5.7 Job/Item；§5.8 Run/Artifact/SearchProjection；§5.9 Embedding；§5.10 Index Profile/Manifest/Target/Build；§5.11 Active Manifest；§5.12 CandidateSet/Feedback | 实体模型最完整的章节；SearchProjection 是 Indexing Worker 唯一接受的跨存储输入（§5.8）；Manifest 是唯一发布单元（§5.10） |
| §6 状态机 | §6.1 Ingestion Item；§6.2 Index Manifest | 全文仅有的两张状态机图；无 Job/Batch、ProcessingRun、IndexBuild、EmbeddingRecord 状态机（见 §7.4） |
| §7 上游数据接入 API | 前缀 `/open/v1/urre`；公共约束；Source 注册、Snapshot 提交、Input Artifact 登记、Job 创建、Job/Manifest 查询、索引重建 | 冲突处理：同 Snapshot 重放返原结果、同版本不同 payload hash 返 `409 SNAPSHOT_CONFLICT`、Schema 失败返 `422`（§7.3） |
| §8 检索 API 参数模型 | Search / Recommendation / Similar / Explore 请求、CandidateSet 响应（schema 1.1）、Feedback 请求 | 检索接口沿用 `POST /api/v1/retrieval/*`（§8 开头）；Explore 只预留模型（§8.4） |
| §9 PostgreSQL DDL | §9.1 Source/RawObject；§9.2 Snapshot/InputArtifact；§9.3 Profile；§9.4 Job/Item；§9.5 Run/Artifact/Embedding；§9.6 Pool/Manifest/Active Pointer；§9.7 CandidateSet/Feedback/Outbox；§9.8 配额/死信；§9.9 删除与失效 | 逻辑基线 DDL，非正式迁移文件（§9 开头）；Active Pointer 切换给出了 CAS SQL（§9.6） |
| §10 对象存储 | 目录约定、对象规则、保留与清理 | 原始对象按内容 hash 寻址禁覆盖；派生产物路径必须含 Profile 版本（§10.1–§10.2） |
| §11 Elasticsearch | §11.1 索引粒度；§11.2 通用字段；§11.3 Video 字段；§11.4 Clip 字段；§11.5 Mapping 约束 | Video 与 Clip 分物理索引；`dynamic: strict`（§11.5） |
| §12 Qdrant | §12.1 Collection 粒度；§12.2 Point ID；§12.3 Payload；§12.4 配置；§12.5 检索流程 | Collection 按“向量空间 + 模型主版本”拆分；Point ID 用 UUIDv5（§12.2） |
| §13 Redis | Key 命名、类型与 TTL、缓存规则、锁与任务协调 | Redis 只做缓存/幂等/限流/锁；Manifest 切换靠 Outbox 推失效，TTL 只是兜底（§13.3） |
| §14 跨存储一致性 | 写入链路 12 步、一致性不变量、增量更新、查询链路、重建与回滚 | 核心不变量：ES 与 Qdrant 文档数不必相等，但须覆盖同一逻辑对象集合；任一 target 失败 Manifest 不激活（§14.2） |
| §15 权限与安全 | 身份与租户、内容安全、三层权限过滤 | `visibility_scope` 只做粗过滤，最终授权由在线服务复核；撤销权限不能只等重建（§15.3、§9.9） |
| §16 可观测性 | 关联键、加工/索引/在线三类指标 | 关联键清单 14 个（§16.1） |
| §17 验收基线 | §17.1 数据模型；§17.2 幂等与重试；§17.3 索引一致性；§17.4 Redis 与故障；§17.5 权限与安全；§17.6 可重建性 | 共 6 组、约 25 条可执行验收（§17 全文） |
| §18 实施顺序 | 阶段 A–F | A 控制面与接入 → B 文本加工与 ES → C Embedding 与 Qdrant → D Redis 与反馈 → E 增量/回填/重建 → F 排序与实验 |
| §19 架构决策 | URRE-DM-ADR-01–12 | 12 条决策，核心是 ADR-01（PG 权威）、ADR-04（Manifest 唯一原子发布单元）、ADR-05（查询固定 manifest + epoch） |
| §20 与当前 Video Domain Agent 实施的关系 | 当前 Mock、未来替换路径、不得回流的内容 | CandidateSet 补齐字段应先作为可选字段加入，避免破坏 Mock 路径（§20.2） |
| §21 待基准验证的技术决策 | 10 项（全文抄录见 §8） | 全部是“不影响逻辑模型、实现前必须基准测试确定”的项（§21 开头） |

---

## 2. 要点提炼：05 相对 02 新增了什么（重复度低的部分）

以下内容在 02 中只有原则性一句话或完全没有，是 05 的实质增量：

1. **事实源与版本链**：§4.3 的 7 环版本链（content → metadata → snapshot → processing_profile → embedding_model → index_profile → index_manifest）；§4.4 的 5 个幂等键；§4.5 的 Hash 规范。02 §10.3 只有版本与幂等键的文字描述，无 snapshot_key、job_idempotency_key 的构成。
2. **实体模型**：§5.2–§5.12 共 11 组实体，其中 Source、RawObject、InputArtifact、ProcessingRun、EmbeddingRecord、IndexPool、TenantIndexBinding、Outbox、Quota、DeadLetter 在 02 中无对应实体定义。
3. **状态机**：§6.1 Item 状态机（含 DeadLettered）、§6.2 Manifest 状态机（含 Building / Validating / Superseded）。02 §10.3 只有 Item/Batch 的文字状态列举，无图、无转移条件。
4. **API 参数模型**：§7 接入 API（6 组接口 + 冲突码 409/422）、§8 检索 API（4 类请求 + CandidateSet 1.1 + Feedback）。02 只有 §7 的概念性结果契约和 §8 的事件分层，无请求字段表。
5. **落地 DDL**：§9 共约 20 张表的逻辑 DDL，是 02 完全没有的层次。
6. **三类存储的字段模型**：§11 ES Mapping、§12 Qdrant Collection/Payload/Point ID、§13 Redis Key/TTL/锁。02 §5.5 只有 Qdrant 选型理由和 5 条架构边界，§10.4 只有 Manifest 原则。
7. **一致性与验收的可执行条目**：§14 的 12 步写入链路与不变量、§17 的 6 组验收。02 §10.5、§12.2 只有验收方向，无逐条可测断言。

---

## 3. 与 02 的逐项对照

### 3.1 CandidateSet Schema：两处是否一致

**结论：概念一致、字段上 05 是 02 的超集，但有 4 处实质差异与 1 处版本差异。**

| 维度 | 02 §7（概念契约） | 05 §5.12 / §8.5 / §9.7 | 判定 |
|---|---|---|---|
| 顶层标识 | `request_id, domain, capability, strategy_version, items[], trace` | §8.5：`schema_version: "1.1", candidate_set_id, request_id, domain, capability, handled_by, strategy_id, strategy_version, index_manifest_id, manifest_epoch, items[], trace, page, warnings`；§5.12 实体字段与之基本一致，另有 `project_id/task_id/storyboard_clip_id, items_json 或 content_uri, expires_at`；§9.7 DDL：`content_uri/content_json（二选一，CHECK 约束）、content_hash NOT NULL` | **超集，基本一致**；但 §5.12 写的是 `items_json`，§9.7 DDL 写的是 `content_json`，同一字段两个名字（见 §5-C1） |
| Item 标识 | `entity_id, entity_type, score, rank, recall_channels, matched_requirements, evidence{summary, time_range, evidence_refs}, availability, feature_version` | §8.5 item：`candidate_id, entity_type, entity_id, video_id, clip_id, start_ms, end_ms, rank, score, score_breakdown{keyword, semantic, visual, metadata}, score_normalization_version, candidate_origins, source_candidate_set_ids, matched_requirements, matched_similarity_targets, recall_channels, evidence{summary, evidence_refs}, availability, versions{feature_version, model_versions, index_profile_version}` | **超集**；新增 `candidate_id / score_breakdown / candidate_origins / source_candidate_set_ids / matched_similarity_targets / versions`，02 均无定义 |
| evidence.time_range | 有：`evidence.time_range{start_ms, end_ms}`（02 §7） | 无：§8.5 的 `evidence` 只有 `summary + evidence_refs`；时间区间改由 item 顶层 `start_ms/end_ms` 承载 | **结构迁移，未声明兼容规则**：02 的 `evidence.time_range` 在 05 无对应字段，Mock 与真实结果的 evidence 结构不一致（见 §5-C2） |
| trace | `query_version, model_versions, latency_ms`（02 §7） | §8.5 trace：`query_version, latency_ms, degraded_channels, model_versions, index_manifest_id` | **超集，一致**；新增的两字段合理 |
| schema_version | 02 §7 无版本字段 | §8.5 响应 `schema_version: "1.1"`，而 §8.1–§8.4 的请求一律 `"1.0"`；§8.5 兼容策略称“Mock 可只实现 1.0 必需字段，真实 URRE 在 1.x 内增加可选字段” | **版本含义未定义**：1.0 与 1.1 的字段差集没有清单，何为“必需”何为“可选”无表（见 §6-G1） |
| handled_by | 02 无此字段 | §5.12 / §8.5 / §9.7：`handled_by ∈ {fast_path, agent}`（§9.7 CHECK 约束）；`fast_path` 与 `agent` 的语义、判定规则在两份文档中均无定义 | **新增枚举无定义**（见 §6-G2） |
| 反馈归因键 | 02 §8 只列事件名，未给字段 | §5.12 Feedback：`feedback_id … candidate_set_id, candidate_id, exposure_position, strategy_id/version, index_manifest_id, idempotency_key`；§9.7 DDL 另有 `project_id/task_id/storyboard_clip_id`，§5.12 的 Feedback 字段表无此三字段 | **§5.12 实体表比 DDL 少 3 个字段**（见 §5-C3） |

### 3.2 版本链 / 幂等键：02 §10.3 与 05 §4.4 是否一致

**结论：Index Item Key 逐字一致；Processing Key 与 Embedding Key 构成不同；其余 3 个键只有 05 定义。**

| 键 | 02 §10.3 | 05 §4.4 | 判定 |
|---|---|---|---|
| content_version / metadata_version | “`content_version` 由 data-control-plane 在 finalize 校验通过后分配；原始二进制合法替换时递增。`metadata_version` 由领域业务服务在权威元数据变化时递增” | §4.3：“原始二进制或上游内容合法替换时递增 / 上游权威标题、标签、属性或业务状态变化时递增” | **一致** |
| Processing Key | `tenant_id + entity_type + entity_id + content_version + metadata_version + processing_profile_version` | `snapshot_hash + processing_profile_id + processing_profile_version` | **构成不同，等价性不可验证**：05 用 `snapshot_hash` 替代了 tenant/entity/两版本；§4.5 称 `snapshot_hash` 覆盖“Snapshot 信封、业务 Payload hash、Raw Object hash、Input Artifact hashes 和版本字段”，但“信封”是否包含 `tenant_id/domain/entity_type/entity_id` 未明说；且 02 的键无 `processing_profile_id`（只有版本），05 的键无 `tenant_id/entity` 明文。两者字符串不相等，跨文档对账时无法直接比对（见 §5-C4） |
| Embedding Key | `processing_artifact_hash + embedding_space + embedding_model_version` | `processing_artifact_hash + embedding_space + embedding_model_id + embedding_model_version` | **05 多一个 `embedding_model_id`**：同一模型版本、不同模型 ID 时两键是否应区分，02 与 05 答案不同（见 §5-C5） |
| Index Item Key | `tenant_id + index_profile_version + index_target + entity_type + entity_id + metadata_version + processing_artifact_hash + index_embedding_outputs_hash` | 同左，逐字相同 | **一致** |
| Request / Job 幂等键 | “客户端重复提交同一个批处理请求时返回同一个 Job；它不能替代上述内容、加工和索引幂等键”——无构成 | `job_idempotency_key = tenant_id + operation_type + source_id + selector_hash + profile_version + index_profile_version`；另 §4.4 末条“Request 级别幂等键只用于防止重复提交，不替代版本键” | **05 补全，02 无冲突**；但 `selector_hash` 的计算规则、`operation_type` 的枚举在 05 全文无定义（见 §6-G3） |
| snapshot_key | 02 无 | `tenant_id + domain + entity_type + entity_id + content_version + metadata_version + entity_schema_version` | **05 新增**；但该键对 Clip 缺 `video_id`（见 §5-C6） |

### 3.3 Qdrant 选型：02 §5.5 与 05 的关系

| 点 | 02 §5.5 | 05 | 判定 |
|---|---|---|---|
| 选型结论 | “默认选择：Qdrant”，给 5 维理由与 5 条架构边界；并声明“本次交付不启用” | §12 全章按 Qdrant 落地（Collection 粒度、Point ID、Payload、HNSW 配置）；§21 第 1 条却是“Qdrant 与 Milvus / OpenSearch Vector 的最终选型”待基准验证 | **表面一致、决策状态冲突**：02 写的是已定默认方案，05 §21 又把它列为待验证项。若 §21 为准，则 §12 的全部 Qdrant 专属设计（Point ID、Payload Index、HNSW 参数）都是“待定选型上的设计”，需在 v2 明确：02 的“默认选择”是否等于“已决策”，§21 第 1 条的验证通过标准是什么（见 §5-C7） |
| Collection 命名 | 例 `video_text_v1`、`video_visual_v1`（02 §5.5） | `urre_{pool_id}_{domain}_{vector_space}_{model_major}`，例 `urre_default_video_text_v1`（§12.1） | **命名不一致**：02 的例子无 `urre_` 前缀和 pool 段；05 的命名含 pool 与 `urre_` 前缀。两者都自称“例如”，但 v2 只能留一种（见 §5-C8） |
| 分工 | “BM25/中文分词/聚合/复杂全文查询由 ES；Qdrant 负责文本/视觉向量与相似检索；两类结果在 URRE 内合并、去重和 RRF 融合，不直接比较原始分数” | §12.5 第 6 步“与 ES 结果进行 RRF 或校准后融合”；§12.5 末条“Qdrant 原始相似度不能跨模型直接与 ES BM25 分数相加”；§14.2 同样要求 | **一致** |
| 硬过滤下推 | `tenant_id`、权限、对象状态、项目范围作为 Qdrant 查询条件在召回阶段执行 | §12.3 Payload 含 `tenant_id/status/availability/visibility_scope/project_scope_ids`；§12.5 第 3 步同样要求 | **一致** |

### 3.4 其余重复点（两处都讲，且基本一致）

- Active Manifest 是唯一原子发布点，ES/Qdrant Alias 只是 Manifest 内资源：02 §10.4 与 05 §5.10/§5.11/§14.1/ADR-04 一致。
- 不可变新索引版本 + Draft → 校验 → Validated → Active → 灰度 → 下线旧版：02 §10.4 步骤 1–7 与 05 §14.1/§14.5 一致。
- 上游权威字段只读、派生不得反写业务事实、稳定 Input Artifact 优先复用：02 §10.1/§10.2 与 05 §5.3/§5.5/ADR-02 一致。
- 敏感原文与长期签名地址不进向量 Payload、只返受控 `evidence_ref`：02 §10.4 末段与 05 §11.5/§12.3/§15.2 一致。
- 四类能力、召回通道、硬约束先于排序：02 §4–§5 与 05 无重复（05 未重述流水线），无冲突。

---

## 4. 05 文档内部的要点与自洽性检查

### 4.1 实体与 DDL 的对应关系

| 实体（§5） | DDL（§9） | 对应情况 |
|---|---|---|
| Source §5.2 | `urre_source` §9.1 | 字段基本对应；但 §5.2 的 `status`、`supported_operations` 枚举值全文未定义 |
| RawObject §5.4 | `urre_raw_object` §9.1 | 对应；UNIQUE(tenant, source, content_sha256) 落实了“按内容 hash 去重” |
| Snapshot §5.3 | `urre_canonical_snapshot` §9.2 | 对应；UNIQUE(tenant, domain, entity_type, entity_id, content_version, metadata_version, entity_schema_version) 落实了 snapshot_key；CHECK 约束落实了“Video 的 video_id 为空、Clip 必填” |
| InputArtifact §5.5 | `urre_input_artifact` §9.2 | 对应 |
| ProcessingProfile §5.6 | `urre_processing_profile` §9.3 | 对应 |
| Job §5.7 / Item §5.7 | `urre_ingestion_job` / `urre_ingestion_item` §9.4 | Job DDL 有 `total/succeeded/failed` 三个计数，无 `dead_lettered` 计数（见 §5-C9）；Item 的 `item_key` 在 §4.4 无定义（见 §6-G4） |
| ProcessingRun/Artifact §5.8 | `urre_processing_run` / `urre_processing_artifact` §9.5 | 对应 |
| Embedding §5.9 | `urre_embedding_profile` §9.3、`urre_embedding_record` §9.5 | 对应 |
| IndexProfile/Manifest/Target/Build §5.10 | `urre_index_profile` §9.3、`urre_index_manifest` / `urre_index_target` / `urre_index_build` / `urre_index_build_item` §9.6 | 对应；但 `urre_index_pool` 与 `urre_tenant_index_binding` 只有 DDL、§5 无实体节（见 §6-G5） |
| Active Manifest §5.11 | `urre_active_manifest` §9.6 | 对应；CAS SQL 只更新指针表（见 §5-C10） |
| CandidateSet/Feedback §5.12 | `urre_candidate_set` / `urre_feedback_event` §9.7 | 字段名、字段数均有出入（见 §5-C1、§5-C3） |
| （§5 无）Outbox / Quota / DeadLetter | `urre_outbox_event` / `urre_quota_policy` / `urre_quota_usage` / `urre_dead_letter` §9.7–§9.8 | **§5 实体章缺失**：Outbox 只在 §13.3、§14.1 被提及，Quota 只在 §9.8 与 02 §10.3 末段被提及，DeadLetter 只在 §6.1 规则与 §9.8 出现；三者均无 §5 级别的实体定义（字段、状态枚举、归属关系） |

### 4.2 字段模型的三处“表”与一处“JSON”对不齐

1. **ES §11.5 的 Mapping JSON 是 §11.2–§11.4 字段表的子集**：全文检索确认，Mapping JSON（§11.5）中缺失 §11.2 的 `source_type`、`freshness_ts`，§11.3 的 `fps`、`clip_count`、`quality_flags`、`preview_ref`，§11.4 的 `subjects`、`actions`、`scenes`、`clip_type`、`camera_motion`、`mood`、`quality_flags`、`keyframe_ref`、`preview_ref`。`dynamic: strict` 下这些字段写入即失败，§11.2–§11.4 与 §11.5 不能同时成立（见 §5-C11）。
2. **Qdrant Payload（§12.3）比 ES 多 `chunk_id / projection_id / sample_ms / evidence_ref（单数）`**：`evidence_ref`（单数）与 §5.8 的 `evidence_refs`（复数）、§8.5 的 `evidence.evidence_refs` 不一致；`chunk_id` 的来源（分块规则）在 §5.6 只有 `text_chunking_config` 字段名，无结构定义（见 §6-G6）。
3. **ES 无文档 `_id` 定义**：§11 全章未定义 ES 文档的 `_id` 构成，而 §12.2 定义了 Qdrant Point ID。§14.2 要求“每条 ES 文档和 Qdrant Point 必须包含相同的 manifest_id、tenant_id 和逻辑对象键”，但无 `_id` 规则时无法逐条对账主键集合差异（§16.3 要求监控“ES/Qdrant 主键集合差异”却无主键定义）（见 §6-G7）。

---

## 5. 冲突清单（C：两处说法不一致，或同一文档内自相矛盾）

| ID | 问题 | 依据 A | 依据 B | 影响与建议方向 |
|---|---|---|---|---|
| C1 | CandidateSet 内容字段名不一致：`items_json` vs `content_json` | 05 §5.12：“`items_json` 或 `content_uri`” | 05 §9.7 DDL：`content_uri varchar(1000), content_json jsonb`，CHECK(`content_uri IS NOT NULL OR content_json IS NOT NULL`)；§5.12 无 `content_hash`，§9.7 有 `content_hash char(64) NOT NULL` | 二选一并统一；`content_hash` 的计算对象（`content_json` 还是 `content_uri` 指向的对象）需定义 |
| C2 | `evidence.time_range` 在 05 消失 | 02 §7：`evidence: {summary, time_range: {start_ms, end_ms}, evidence_refs}` | 05 §8.5：`evidence: {summary, evidence_refs}`，时间区间只在 item 顶层 `start_ms/end_ms` | 明确 05 为准并声明 02 §7 的 `evidence.time_range` 废弃，或在 05 恢复该字段；否则 Mock（按 02）与真实（按 05）证据结构不兼容 |
| C3 | Feedback 实体字段表比 DDL 少 3 个字段 | 05 §5.12 Feedback 字段表：无 `project_id / task_id / storyboard_clip_id` | 05 §9.7 `urre_feedback_event` DDL：有 `project_id, task_id, storyboard_clip_id`；§8.6 FeedbackRequest 示例也有此三字段 | 以 DDL + §8.6 为准，补 §5.12 的字段表 |
| C4 | Processing Key 构成不同（02 vs 05） | 02 §10.3：`tenant_id + entity_type + entity_id + content_version + metadata_version + processing_profile_version` | 05 §4.4：`snapshot_hash + processing_profile_id + processing_profile_version` | 见 §3.2：明确以 05 为准，并补写 `snapshot_hash` 是否覆盖 tenant/domain/entity 的断言；或恢复 02 的显式构成，二者只能留一种字符串形式 |
| C5 | Embedding Key 多一个 `embedding_model_id` | 02 §10.3：`processing_artifact_hash + embedding_space + embedding_model_version` | 05 §4.4：`processing_artifact_hash + embedding_space + embedding_model_id + embedding_model_version` | 以 05 为准（模型 ID 不同即不同空间是合理设计），并在 02 §10.3 加注修订 |
| C6 | Clip 的 snapshot_key / DDL 唯一约束缺 `video_id`，与 §4.2 的 Clip 逻辑键矛盾 | 05 §4.2：Clip 逻辑键必须同时保留父 Video 关系，`clip_logical_key = tenant_id + domain=video + entity_type=clip + video_id + clip_id` | 05 §4.4 `snapshot_key`：`tenant_id + domain + entity_type + entity_id + content_version + metadata_version + entity_schema_version`（无 video_id）；§9.2 DDL UNIQUE 约束同样无 `video_id` | 若 `clip_id` 全局唯一则无实际冲突，但文档未声明该假设；若 `clip_id` 只在 Video 内唯一，则同一 `clip_id` 属于不同 Video 时 snapshot_key 与唯一约束都会碰撞。v2 必须二选一：声明 `clip_id` 全局唯一，或把 `video_id` 加入 snapshot_key 与唯一约束 |
| C7 | Qdrant 选型状态冲突：02 已定默认 vs 05 §21 待验证 | 02 §5.5：“默认选择：Qdrant”，并列 5 条架构边界 | 05 §21 第 1 条：“Qdrant 与 Milvus / OpenSearch Vector 的最终选型”待基准验证 | 明确决策状态：若 02 的“默认选择”即决策，则 §21 第 1 条应改为“Qdrant 部署参数验证”；若未决策，则 §12 不应以 Qdrant 专属细节（Point ID、HNSW）作为基线 |
| C8 | Qdrant Collection 命名示例不一致 | 02 §5.5：`video_text_v1`、`video_visual_v1` | 05 §12.1：`urre_{pool_id}_{domain}_{vector_space}_{model_major}`，例 `urre_default_video_text_v1` | 以 05 §12.1 为准，02 的例子作废；或在 05 注明 02 的例子是省略 pool 前缀的简写 |
| C9 | Job 的死信计数：响应有、DDL 与实体表无 | 05 §7.6 Job 状态响应示例：`counts: {total, succeeded, failed, dead_lettered: 0}` | 05 §5.7 Job 关键字段：只有 `total_item_count / succeeded_item_count / failed_item_count`；§9.4 `urre_ingestion_job` DDL 同样只有三列 | 补 `dead_lettered_item_count` 列，或把 §7.6 的 `dead_lettered` 改为由 `urre_dead_letter` 表聚合得出并注明 |
| C10 | Manifest 激活是否“一个事务”：§6.2/§9.6 与 §17.3.3 说法不一致 | 05 §6.2 规则：“只有控制面通过 CAS 更新 Active Pointer 后，Manifest 才可标记为 `Active`”（两步：先 CAS 指针，后标状态）；§9.6 的 CAS SQL 只 `UPDATE urre_active_manifest`，不更新 `urre_index_manifest.status` | 05 §17.3.3 验收：“Active Pointer 切换在数据库事务中完成” | 明确原子单元：指针切换与 Manifest 状态置 `Active` 是否在同一事务；若是，补写包含两张表的事务 SQL；若否，§17.3.3 应改为“指针切换本身是单条 CAS 语句，状态标记随后进行，失败时指针已切但状态未标的补偿流程是……” |
| C11 | ES Mapping JSON 是字段表的子集，`dynamic: strict` 下不能共存 | 05 §11.2–§11.4 字段表：含 `source_type, freshness_ts, fps, clip_count, quality_flags, preview_ref, subjects, actions, scenes, clip_type, camera_motion, mood, keyframe_ref` 等 | 05 §11.5 Mapping JSON：全文检索确认上述字段均未出现在 `properties` 中；§11.5 同时规定 `dynamic: strict`、“未知字段写入应失败” | 以 §11.5 的 JSON 为准补全字段，或以 §11.2–§11.4 的表为准重写 JSON；二者必须逐字段对齐后才能作为基线 |
| C12 | Clip `business_payload` 含派生字段，与“只保存上游事实”冲突 | 05 §5.3 规则：“业务 Payload 只保存上游事实和必要元数据。ES 文档、Qdrant Payload 和 Search Projection 都是其检索侧投影，不得反向成为业务事实” | 05 §5.3 Clip 的 `business_payload_json` “至少包含”清单含 `feature_version`、`model_versions`——两者是加工/模型派生版本，不是上游事实 | 把 `feature_version / model_versions` 移出 Clip 业务 Payload 清单（改由 SearchProjection/EmbeddingRecord 承载），或修正 §5.3 的规则，说明此二字段为例外及其来源 |
| C13 | Clip `business_payload` 的 `title`：§5.3 清单无，§7.3 示例与 §11.4 有 | 05 §5.3：Video 清单有 `title`，Clip 清单无 `title`（只有 `clip_id, video_id, start_ms/end_ms/duration_ms, preview_ref, keyframe_ref, semantic_summary, tags …`） | 05 §7.3 Snapshot 提交示例：Clip 的 `business_payload` 含 `"title": "人机协作装配"`；§11.4 Clip 字段表：`title text + keyword` | 明确 Clip 是否有 `title` 及其来源（上游提供还是加工生成）；若由加工生成，则它不应出现在 §7.3 的上游提交示例中 |
| C14 | §7.3 示例的 Clip Payload 不满足 §5.3“至少包含”清单 | 05 §5.3 Clip 清单：`preview_ref, keyframe_ref, semantic_summary, quality_flags, availability, feature_version, model_versions` 等为必填（“至少包含”） | 05 §7.3 示例的 Clip `business_payload` 只有 `video_id, clip_id, title, start_ms, end_ms, duration_ms, availability, tags`，缺 `preview_ref, keyframe_ref, semantic_summary, quality_flags, feature_version, model_versions` | 补全示例，或把 §5.3 的“至少包含”改为分“上游提交时必填”与“加工后补全”两档 |
| C15 | Job/Batch 状态值大小写不一致 | 02 §10.3 Batch：`Accepted → Running → Completed`，`PartiallyCompleted / Failed / Cancelled`（首字母大写） | 05 §7.6 Job 状态响应示例：`"status": "running"`（全小写）；§6.1 Item 状态机用首字母大写（`Accepted` 等），§9 DDL 的 `status` 全是无 CHECK 的 `varchar(32)`，大小写无约束 | 统一状态枚举的大小写规范（建议与 §6 状态机一致的首字母大写，或全小写 snake_case，二选一并写入 §4.1 命名规则） |
| C16 | 02 §10.4 的 Manifest 状态枚举缺 3 个状态 | 02 §10.4：“状态 `Draft / Validated / Active / Failed / RolledBack`” | 05 §6.2 状态机：`Draft → Building → Validating → Validated → Active → Superseded / RolledBack`，另有 `Failed` | 以 05 §6.2 为准，02 §10.4 的枚举应补 `Building / Validating / Superseded` |

---

## 6. 缺口清单（G：某处引用、依赖或承诺了，但全文无定义）

| ID | 缺口 | 引用处 | 说明 |
|---|---|---|---|
| G1 | CandidateSet 1.0 与 1.1 的字段差集无清单 | 05 §8.5（`schema_version: "1.1"`；兼容策略称 Mock 实现 1.0 必需字段） | 何为 1.0 必需、何为 1.1 新增可选，无表；`score_normalization_version: "rrf-v1"` 的 `rrf-v1` 也无注册表（RRF 只在 02 §5.5、05 §12.5/§14.4 被提及，无参数与版本定义） |
| G2 | `handled_by` 的两个枚举值无语义定义 | 05 §5.12、§8.5、§9.7（CHECK `fast_path / agent`） | 何时是 `fast_path`、何时是 `agent`，判定规则、与 02 流水线的对应关系均无定义 |
| G3 | `job_idempotency_key` 的 `operation_type` 枚举与 `selector_hash` 算法无定义 | 05 §4.4 | `operation_type` 可取值？`selector_hash` 对 §7.5 的 selector 如何规范化、排序、编码？无定义则两个客户端算出的键可能不同 |
| G4 | `item_key`（IngestionItem）的构成无定义 | 05 §5.7（Item 关键字段含 `item_key`）、§9.4 DDL（`item_key varchar(200)`，UNIQUE(tenant, job, item_key)） | 它是 §4.4 的 processing_key、index_item_key，还是第三种键？§6.1“重试必须复用原 Item 和 Processing Key”也未说明 `item_key` 与 Processing Key 的关系 |
| G5 | Index Pool 实体无 §5 定义 | 05 §5.10/§5.11 大量使用 `pool_id`；§9.6 DDL 有 `urre_index_pool`（`isolation_mode`）、`urre_tenant_index_binding` | `pool_id` 的生成规则、`isolation_mode` 的枚举（共享/专用？§5.11 提到“共享 Pool”“专用 Pool”但无枚举值）、租户与 Pool 的绑定规则（一个租户能否绑多 Pool）、Pool 与 `domain` 的关系，均无 §5 级别定义 |
| G6 | `chunk_id` 与分块规则无定义 | 05 §12.2 Point ID 含 `chunk_id`；§12.3 Payload 含 `chunk_id`；§5.6 只有 `text_chunking_config` 字段名 | 文本分块长度/重叠、视觉采样密度本就是 §21 第 3 条待验证项，但 Point ID 的 `chunk_id` 生成规则（分块 ID 是否稳定、重分块后是否变）必须先于 Point ID 定义，否则 Point ID 不稳定 |
| G7 | ES 文档 `_id` 无定义 | 05 §11 全章；§14.2、§16.3 要求对账“主键集合差异” | 无 `_id` 构成则无法逐条对账；建议明确 `_id` 是否等于 Qdrant Point ID 的某种映射，或等于 `tenant + entity + content/metadata_version` 的派生键 |
| G8 | `query_parser_version` 无定义 | 05 §13.1 Redis Query Cache Key 含 `{query_parser_version}`；§13.3 要求 Key 包含它 | Query Parser 的版本由谁发布、版本号格式、与 §8 请求的 `query_version`（trace 用）是否为同一版本，均无定义 |
| G9 | 增量“同步水位”无定义 | 05 §14.3（“由控制面推进同步水位”）、§16.3、§18 阶段 E；§5.10/§9.6 有 `source_watermark_json` 但无结构 | 水位的值是时间戳、版本号还是 snapshot hash 集合？推进条件、回退规则、与 Manifest 的关系均无定义；`source_watermark_json` 的结构也未给出 |
| G10 | 反馈事件类型枚举无映射表 | 02 §8.1：`Impression / Click / Preview / Save / Download / Adopt / Use / Replace / Reject / Convert`；05 §8.6 示例：`"event_type": "recommendation.clicked"` | 02 的 10 个事件名与 05 的点分式 `event_type`（`recommendation.clicked` 之类）之间无映射表；`source` 的枚举（示例 `"api"`）也无定义；§5.12/§9.7 的 `event_type` 为自由 `varchar(64)` |
| G11 | RecommendationRequest 的 `selected` 与 `covered_storyboard_clip_ids` 一致性规则不可执行 | 05 §8.2：“`selected` 与 `covered_storyboard_clip_ids` 必须一致；如不一致，Schema 拒绝” | `selected` 数组元素的类型未定义（是 `clip_id` 还是对象？）；`covered_*` 是 `sb_clip_*`（计划侧 ID），`selected` 若是素材 `clip_id`，两者根本无法“一致”——规则的字面含义无法实现；且 `clip_requirement` 的 `hard_constraints / soft_preferences / fallback_requirements / evidence_requirements` 结构未定义 |
| G12 | `soft_preferences.orientation` 与 `recall.channels: ["metadata"]` 无字段/通道定义 | 05 §8.1 示例：`soft_preferences: {orientation: "landscape"}`；`recall.channels` 含 `"metadata"`；`score_breakdown` 含 `"metadata": 0.90` | `orientation` 在 §11 ES、§12 Qdrant 全文无此字段；`"metadata"` 通道不在 02 §5.1 的 9 个召回通道中，也不在 05 任何通道清单中；`metadata` 分数的计算方式无定义 |
| G13 | `filters.tags_any` 的操作符无定义 | 05 §8.1 示例：`filters: {tags_any: [...]}` | §8.1 称“`filters` 只允许 Domain Schema 注册的字段和操作符”，但 `tags_any` 的语义（任一命中）、与 §11.4 `tags keyword[]` 的对应关系、以及其它允许的操作符（`_all/_gte/_lte` 等）无注册表 |
| G14 | Explore 的 `max_distance` 无量纲 | 05 §8.4 示例：`"max_distance": 0.45` | 距离度量（Cosine 距离 0–2？归一化相似度？）未定义，0.45 无法解释；与 §12.4 的 `distance: Cosine` 也未挂钩 |
| G15 | 枚举值大量未定义（DDL 也无 CHECK 约束） | 05 §5.2 Source `status`；§5.5 InputArtifact `status`；§5.6 Profile `status`（仅列 `draft/published/deprecated`，DDL 无 CHECK）；§5.7 Job `status`、Item `status`；§5.9 EmbeddingRecord `status`；§5.10 Manifest/Target/Build `status`；§9 各表 `status varchar(32)` 均无 CHECK | 除 `handled_by`（§9.7）、`target_kind/entity_type`（§9.6）、`entity_type`（§9.2）有 CHECK 外，其余状态字段在 DDL 层均不受约束；§6 的两张状态机因此无法由数据库强制执行 |
| G16 | 引用目标缺失：`01_URRE架构设计.md`、`03_VideoDomain架构设计.md`、`implementation/00|05` 在工作区不存在 | 05 第 11 行（上游基线）、§2.4、§20.1；02 文首（`05_URRE数据与存储模型设计.md`） | 工作区实际文件是 `02_URRE架构设计.md`、`03_Agent架构设计.md`，无 `01_URRE…`、`03_VideoDomain…`、`implementation/` 目录（已核实：`ls implementation` 不存在）；02 文首的链接文件名 `05_URRE数据与存储模型设计.md` 与实际路径 `urre/URRE数据与存储模型设计.md` 也不符。所有跨文档链接在 v2 前需逐条核对 |
| G17 | Qdrant Point ID 的 UUIDv5 命名空间不是 UUID | 05 §12.2：`namespace = urre_{pool_id}_{vector_space}` | UUIDv5 的 namespace 按 RFC 4122 必须本身是一个 UUID；`urre_default_video_text` 这样的字符串不能直接作 namespace，需先经 UUIDv5/哈希派生或改用其它稳定派生方式，否则实现时无法直接调用标准库 |
| G18 | §9.6 CAS 示例只覆盖“已有行”的更新，首建 Active Pointer 无 SQL | 05 §9.6（CAS `UPDATE … WHERE manifest_id = :expected_old_manifest_id AND manifest_epoch = :expected_epoch`） | 第一次激活（`urre_active_manifest` 无行）需 `INSERT`，其并发语义未定义；`manifest_epoch` 初始值未定义 |
| G19 | Redis Key 的 TTL 不一致风险：Epoch 缓存 300 秒 > 指针缓存 60 秒 | 05 §13.2：Manifest 指针 TTL 60 秒，Manifest Epoch TTL 300 秒 | Epoch 缓存比指针活得久，指针已切新、Epoch 仍读旧时，Query Cache Key（§13.1 含 `manifest_epoch`）可能把新旧混用；§17.4.2 要求“切换后不会继续命中旧 epoch 查询缓存”，但 TTL 表本身留了 240 秒窗口 |
| G20 | 实体关系图（§5.1）缺 3 组关系 | 05 §5.1 ER 图 | 图中无 Outbox、Quota、DeadLetter，`urre_index_build_item` 在图中只以 `INDEX_BUILD_ITEM` 出现但 §5.10 文字未定义其字段（字段只在 §9.6 DDL 中）；`INDEX_BUILD` 与 `INDEX_BUILD_ITEM` 的关系在 §5.10 文字中未说明 |

---

## 7. 状态机完整性核查

### 7.1 三条状态机逐条判定

| 状态机 | 02 §10.3 | 05 §6 | 完整性判定 |
|---|---|---|---|
| **Item** | 文字列举：`Accepted → Ingesting → Processing → Embedding → Indexing → Validating → Active`，另有 `Failed / Cancelled`；无图、无转移条件、无死信 | §6.1 有完整 Mermaid 图：主链 7 步；`Failed` 可从 Ingesting/Processing/Embedding/Indexing/Validating 进入；`Failed → Accepted`（retry）、`Failed → DeadLettered`（exhausted）、`DeadLettered → Accepted`（manual_retry）；`Accepted → Cancelled` | **基本完整，但有 3 个缺口**：（1）`Cancelled` 只有 `Accepted → Cancelled` 一条边，执行中的 Item（Ingesting 之后）无法取消，但 §7.6 有 `POST …/jobs/{jobId}/cancel` 接口，取消语义（是否级联到执行中 Item、已写入 Draft 索引如何处理）未定义；（2）`Active` 是终态（`Active --> [*]`），但 §6.1 规则又称“`Active` 只表示 Item 已进入一个已校验索引目标，不表示 Manifest 已全局在线”——Manifest 被 Superseded/RolledBack 后 Item 的 `Active` 是否失效、是否需要转移，无定义；（3）`Failed → Accepted` 重试时 `attempt` 如何递增、重试上限值、退避策略均无定义（只有“超过重试上限进入 DeadLettered”一句话） |
| **Batch / Job** | 文字列举：`Accepted → Running → Completed`，允许 `PartiallyCompleted`，另有 `Failed / Cancelled` | **05 §6 无 Batch/Job 状态机**；§5.7 只列 Job 字段，§7.6 只给响应示例 | **缺失**：Job 何时从 Running 到 Completed/PartiallyCompleted 的判定规则（是否按 Item 成功率阈值？）、`PartiallyCompleted` 是否终态、Job 的 `Failed / Cancelled` 转移条件、Job 取消是否级联 Item，全部未定义。这是 05 相对 02 的倒退：02 有文字版，05 连文字版都没有 |
| **Manifest** | 02 §10.4 只列状态枚举 `Draft / Validated / Active / Failed / RolledBack`（缺 Building/Validating/Superseded，见 C16）；无图 | §6.2 有完整 Mermaid 图：`Draft → Building → Validating → Validated → Active → Superseded / RolledBack`；`Building/Validating → Failed` | **基本完整，但有 2 个缺口**：（1）`Draft → Building` 的触发条件（谁创建 Build、Build 与 Job 的关系）未定义——§5.10 的 `IndexBuild` 与 §5.7 的 Job 之间无关联字段，Manifest 的构建是由 Job 驱动还是独立触发，说不清；（2）`Validated → Active` 的转移在图中是一步，但在 §6.2 规则与 §9.6 CAS SQL 中是两步（先 CAS 指针，后标状态），见 C10 |

### 7.2 05 中没有状态机的对象

- **ProcessingRun**：§5.8、§9.5 有 `status` 字段，无状态枚举、无转移图。Run 是按阶段（stage）执行的，`stage` 与 `status` 是两个维度还是同一维度的不同值，未说明。
- **IndexBuild / IndexBuildItem**：§5.10、§9.6 有 `status` 字段，无枚举、无图；Build 的 `Failed` 是否导致 Manifest `Failed`（§6.2 有 `Building/Validating → Failed`，但 Build 与 Manifest 的状态联动规则未写）。
- **EmbeddingRecord**：§5.9、§9.5 有 `status` 字段，无枚举。
- **Source / Snapshot / Profile**：Snapshot 的 `status ∈ {accepted, superseded, deleted, rejected}`（§5.3）只有枚举，无转移图（例如 `accepted → superseded` 由谁触发、`deleted` 是否经 Tombstone 事件，见 §9.9 的 5 步删除流程，但无状态转移表）。

---

## 8. §21 待验证决策清单（全文抄录）

05 §21 原文：“以下内容不影响逻辑模型，但在真实实现前必须通过基准测试确定：”

1. Qdrant 与 Milvus / OpenSearch Vector 的最终选型。
2. 中文全文分析器、词典和插件版本。
3. 文本分块长度、重叠和视觉采样密度。
4. Embedding 维度、距离度量和 HNSW 参数。
5. ES 分片、副本和 Qdrant 分段参数配置。
6. 共享索引池与租户隔离级别。
7. Redis 集群部署模式和最大缓存容量。
8. 增量更新采用 Item 级可见性还是新 Manifest 切换。
9. 旧 Manifest 的保留和回滚窗口。
10. 反馈事件的批量聚合与训练样本生成周期。

**附注**：§21 第 4 条与 §12.4 的示例配置（`vectors.size: 1024, distance: Cosine, hnsw m: 32, ef_construct: 256, default_segment_number: 4`）存在“示例值先行、决策待后”的关系——§12.4 自身注明“最终参数必须通过数据规模、召回率和延迟基准确认”，v2 应把 §12.4 的数值明确标注为“占位示例值，非基线”，否则会被误读为已定参数。同理 §11.5 的 `zh_search` 分析器（§21 第 2 条待定）与 §11.1 的索引命名中的 `{generation}`（生成规则未定义，见 §6-G9 的关联项）也需标注。

---

## 9. 给 v2（最终版文档）的修订建议（按优先级）

### P0——不修则基线自相矛盾

1. **统一 CandidateSet**：以 05 §8.5 为准定稿，废弃 02 §7 的 `evidence.time_range`（或恢复），统一 §5.12 的 `items_json` 与 §9.7 的 `content_json`，补 §5.12 Feedback 的 3 个字段，发布 1.0→1.1 字段差集表（C1/C2/C3、G1）。
2. **统一幂等键**：以 05 §4.4 为准，补写 `snapshot_hash` 对 tenant/domain/entity 的覆盖断言，明确 Embedding Key 含 `embedding_model_id`，并在 02 §10.3 加注修订（C4/C5）；补 `item_key` 构成（G4）与 `selector_hash` 算法（G3）。
3. **补全 ES Mapping**：§11.5 的 JSON 必须与 §11.2–§11.4 的字段表逐字段对齐，否则 `dynamic: strict` 下基线不可写（C11）。
4. **补 Job/Batch 状态机**：在 05 §6 增加 §6.3 Job 状态机（含 PartiallyCompleted 判定、取消级联），与 02 §10.3 对齐（§7.1）；统一状态值大小写（C15）。
5. **明确 Qdrant 决策状态**：02 §5.5 与 05 §21 第 1 条二选一，并统一 Collection 命名示例（C7/C8）。

### P1——不修则实现时无法落地

6. **Clip 主键**：声明 `clip_id` 全局唯一，或把 `video_id` 加入 snapshot_key 与 DDL 唯一约束（C6）。
7. **Clip Payload**：`title` 有无、`feature_version/model_versions` 是否属于上游事实、§7.3 示例补全，三者一并定稿（C12/C13/C14）。
8. **补状态枚举与 DDL CHECK**：所有 `status` 字段补枚举值并在 DDL 加 CHECK 约束，使 §6 状态机可由数据库执行（G15）；补 ProcessingRun/IndexBuild/EmbeddingRecord 的状态机或枚举（§7.2）。
9. **补 Pool 实体**：§5 增加 Pool / TenantIndexBinding 定义，明确 `isolation_mode` 枚举与租户绑定规则（G5）；补 `source_watermark_json` 结构与“同步水位”定义（G9）。
10. **补 ES `_id` 与 Qdrant Point ID 的 namespace 问题**：定义 ES `_id` 构成；把 §12.2 的 UUIDv5 namespace 改为合法 UUID 或其它稳定派生方式；定义 `chunk_id` 生成规则（G6/G7/G17）。

### P2——不修则联调时才暴露

11. 明确 Manifest 激活的事务边界（C10），补首次激活的 INSERT 语义（G18），修正 Redis Epoch TTL > 指针 TTL 的窗口（G19）。
12. 补 Job 响应与 DDL 的 `dead_lettered` 计数（C9）、`handled_by` 语义（G2）、反馈事件类型映射表（G10）、`filters` 操作符注册表与 `tags_any` 语义（G13）、`orientation / metadata 通道` 的字段与通道定义（G12）、Explore `max_distance` 量纲（G14）。
13. 修复全部跨文档引用：05 的 `01_URRE…`/`03_VideoDomain…`/`implementation/…` 与 02 文首的 `05_URRE…` 链接，按工作区实际文件名逐条更正（G16）；§5.1 ER 图补 Outbox/Quota/DeadLetter（G20）。

---

## 10. 核心结论（10 条）

1. **05 是 02 的实质性下钻，不是重述**：版本链、幂等键、11 组实体、两张状态机、§7–§8 API、§9 约 20 张表 DDL、ES/Qdrant/Redis 字段模型、§14 一致性与 §17 验收，均为 02 没有的层次；两者在发布原则（Manifest 唯一原子发布点）、只读上游事实、ES/Qdrant 分工上一致。
2. **CandidateSet 总体是 02 的超集**：05 §8.5 新增 `candidate_id / score_breakdown / candidate_origins / source_candidate_set_ids / matched_similarity_targets / versions` 等字段；但 02 的 `evidence.time_range` 在 05 消失，§5.12 的 `items_json` 与 §9.7 的 `content_json` 同字段两名，§5.12 Feedback 比 DDL 少 3 个字段。
3. **幂等键只有 Index Item Key 逐字一致**：Processing Key（02 显式 6 元组 vs 05 `snapshot_hash + profile`）与 Embedding Key（05 多 `embedding_model_id`）构成不同；`snapshot_hash` 是否覆盖 tenant/entity 未明说，等价性不可验证。
4. **Qdrant 选型状态冲突**：02 §5.5 写“默认选择 Qdrant”，05 §21 第 1 条又列为待基准验证的最终选型；Collection 命名示例也不一致（`video_text_v1` vs `urre_default_video_text_v1`）。
5. **Item 与 Manifest 两张状态机基本完整，Batch/Job 状态机缺失**：05 §6 有 Item（含 DeadLettered）与 Manifest（含 Building/Validating/Superseded）两图，但 02 §10.3 有文字版的 Batch 状态机在 05 全文无对应章节；Item 的 `Cancelled` 仅 `Accepted` 可出、`Active` 终态后 Manifest 回滚的影响、重试上限均未定义。
6. **ES Mapping JSON 与字段表对不齐**：§11.5 的 Mapping JSON 缺失 §11.2–§11.4 的 13 个字段（`source_type / freshness_ts / fps / clip_count / subjects / actions / scenes / clip_type / camera_motion / mood / quality_flags / preview_ref / keyframe_ref` 等），而 `dynamic: strict` 规定未知字段写入失败，两者不能同时成立。
7. **Clip 主键有碰撞风险**：§4.2 要求 Clip 逻辑键保留父 Video，但 §4.4 的 snapshot_key 与 §9.2 的唯一约束均无 `video_id`；除非声明 `clip_id` 全局唯一，否则同一 `clip_id` 归属不同 Video 时会碰撞。
8. **Clip 业务 Payload 自相矛盾**：§5.3 一面规定“只保存上游事实”，一面把派生的 `feature_version / model_versions` 列入 Clip 清单；`title` 在 §5.3 Clip 清单中无、在 §7.3 示例与 §11.4 中有；§7.3 示例也不满足 §5.3 的“至少包含”清单。
9. **大量被引用的字段与枚举无定义**：`query_parser_version`（Redis Key）、`chunk_id`（Point ID）、`item_key`、`selector_hash`、`operation_type`、`handled_by` 的语义、反馈事件类型映射、`filters` 操作符注册表、`orientation / metadata` 通道、增量“同步水位”、ES 文档 `_id`、Pool 的 `isolation_mode`，以及除 3 处外所有 `status` 字段的枚举与 DDL CHECK 约束。
10. **跨文档引用已失效**：05 引用的 `01_URRE架构设计.md`、`03_VideoDomain架构设计.md`、`implementation/00|05` 在工作区均不存在（实际文件是 `02_URRE架构设计.md`、`03_Agent架构设计.md`，无 `implementation/` 目录）；02 文首引用的 `05_URRE数据与存储模型设计.md` 与实际路径 `urre/URRE数据与存储模型设计.md` 也不符；§21 的 10 项待验证决策中，第 1、2、4 条直接影响 §12 的 Qdrant 专属设计能否作为基线。
