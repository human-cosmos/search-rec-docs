# API 与数据契约

> **文档层级：** 实施规范  
> **上位文档：** [00 平台总体架构](../00_架构设计总纲.md)  
> **领域契约：** [03 Video Domain Pack 与创作执行](../03_VideoDomain架构设计.md)  
> **状态：** 概念契约，研发启动时以 OpenAPI、JSON Schema 和代码定义为准

## 1. 契约原则

1. Search、Recommendation、Similarity、Explore 使用独立语义和独立接口。
2. Agent 只调用语义化 Tool/API，不直接访问 Elasticsearch、Qdrant 或其他向量库、Redis 或数据库。
3. 租户、用户和项目权限由服务端可信上下文注入，请求体不能覆盖。
4. 所有写操作声明幂等键、风险等级、审批要求和审计字段。
5. 所有结果返回策略版本、证据和可追溯标识。
6. 对外事件返回阶段状态和简短决策摘要，不暴露内部推理链、敏感 Prompt 或凭据。
7. 契约变更必须兼容版本管理；破坏性变更使用新版本，不静默改变字段语义。
8. 上游业务服务拥有业务事实与 Canonicalization；数据加工平面只消费带版本的权威快照并生成可重建的 Search Projection；URRE 核心只负责召回、过滤和排序。

### 1.1 Domain Pack SPI 契约

每个领域通过一个 `DomainProvider` 向平台注册能力。它是平台内部 SPI，不是面向终端用户的业务 API，也不是 AgentScope 的扩展点。`domainId` 在运行实例内必须唯一。

```java
public interface DomainProvider {

    String getDomainId();

    DomainPackDescriptor getDescriptor();

    DomainSchema getSchema();

    List<QueryParser> getQueryParsers();

    List<RecallStrategy> getRecallStrategies();

    RankingStrategy getRankingStrategy();

    List<RerankPolicy> getRerankPolicies();

    List<AgentToolDescriptor> getTools();

    List<AgentSkillDescriptor> getSkills();

    List<FilterPolicy> getFilters();

    RightsPolicy getRightsPolicy();

    List<BusinessRule> getBusinessRules();

    List<ProcessingProfileDescriptor> getProcessingProfiles();

    EvaluationStrategy getEvaluationStrategy();
}

public record DomainPackDescriptor(
    String version,
    List<String> dependencies,
    List<String> compatiblePlatformVersions
) {}
```

接口约束：

- `getSchema()` 返回的 Schema 必须通过注册时的兼容性与版本校验。
- 召回、排序、重排和评估只能返回已注册、已审核的策略或模型 ID；不得接受请求方动态传入的代码、表达式或查询 DSL。
- `getProcessingProfiles()` 声明领域需要的 Search Projection / Understanding 步骤、上游输入 Artifact 契约及已发布版本。Profile 定义属于 Domain Pack，实际 Job 执行和产物持久化属于数据加工平面。
- `getTools()` 与 `getSkills()` 只声明语义能力及其输入输出契约，实际执行仍经过 Tool Registry 和 Policy Gateway。
- `getDescriptor()` 必须声明领域包版本、依赖和平台兼容范围，以支持升级、回滚与依赖检查。
- 同一个 `domainId` 只能存在一个有效 Provider；重复注册、版本冲突或兼容性校验失败时必须拒绝启动该领域包，不影响其他领域。
- Provider 返回的定义应为不可变描述；运行时不得通过修改 Provider 返回值静默改变已审核的策略或 Schema。
- 下列能力**必须注册，但允许先以空实现或显式“后补”占位通过注册校验**：Filter、Rights、Business Rules、Evaluation。不得只把 Rights 做成排序特征或可选重排因子。组成清单仍以 `00` §3 为准；上述 Java 类型名称在研发启动时以正式 SPI 模块为准。

`DomainProvider` 的具体 Java 类型、SPI 加载方式和包名在研发启动时以正式的 SPI 模块、JSON Schema 和集成测试为准。

## 2. URRE API

统一前缀：`/api/v1/retrieval`

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/search` | 明确 Query 或约束下的候选发现 |
| `POST` | `/recommend` | 用户、场景、项目和任务上下文推荐 |
| `POST` | `/similar` | 按对象发现语义、视觉、属性或关系相似项 |
| `POST` | `/explore` | 受控扩展候选空间和机会发现 |
| `POST` | `/rerank` | 对已有候选进行重排 |
| `POST` | `/explain` | 解释已有结果或推荐依据 |
| `POST` | `/feedback` | 提交行为、采用和业务结果事件 |

### 2.1 Search 请求

```json
{
  "domain": "video",
  "query": "雨夜城市街道，电影感，霓虹灯反射",
  "filters": {
    "duration_ms": {"gte": 3000, "lte": 15000},
    "orientation": ["landscape"],
    "resolution_min": "1080p",
    "commercial_allowed": true
  },
  "context": {
    "project_id": "project_456",
    "task_id": "task_123",
    "shot_plan_id": "shotplan_003",
    "session_id": "session_789"
  },
  "recall": {
    "channels": ["keyword", "semantic", "visual"],
    "top_k": 300
  },
  "ranking": {
    "strategy_id": "video_hybrid_v1",
    "limit": 30
  },
  "page": {
    "cursor": null,
    "size": 30
  }
}
```

复杂自然语言查询可以通过 Search Planner 转换为 `SearchPlan`。它是内部或 Agent Tool 契约，不应成为简单搜索的必经链路。

```json
{
  "plan_id": "sp_001",
  "domain": "video",
  "target_level": ["shot", "segment"],
  "semantic_query": "夜晚雨后的城市街道，霓虹灯倒映在湿润路面",
  "sub_queries": [
    {"role": "scene", "query": "night city street after rain"},
    {"role": "visual", "query": "neon reflections on wet asphalt"},
    {"role": "mood", "query": "cinematic moody urban night"}
  ],
  "filters": {
    "duration_ms": {"gte": 3000, "lte": 15000},
    "commercial_allowed": true
  },
  "recall_channels": ["keyword", "semantic", "visual", "metadata"],
  "target_candidates": 300,
  "sort_intent": "relevance_then_quality"
}
```

SearchPlan 必须经过 Schema 校验。租户、Rights 和可见范围等硬约束由服务端注入，Agent 不得移除。

### 2.2 Recommendation 请求

```json
{
  "domain": "video",
  "scene": "task_material_recommendation",
  "context": {
    "session_id": "session_789",
    "project_id": "project_456",
    "task_id": "task_123",
    "current_stage": "material_collection",
    "task_description": "制作一条城市夜生活品牌短片",
    "task_context": {
      "covered_shot_ids": ["shot_001", "shot_002"],
      "selected_entity_refs": [
        {"shot_id": "shot_001", "entity_id": "segment_001"}
      ],
      "diversity_targets": {
        "avoid_same_segment": true,
        "max_per_visual_cluster": 3
      }
    }
  },
  "strategy": {
    "strategy_id": "video_project_recommend_v1",
    "objective": "task_fit_then_diversity"
  },
  "limit": 30,
  "diversity": {
    "enabled": true,
    "max_per_cluster": 5
  }
}
```

`RecommendationStrategy` 由 Domain Pack / 服务端策略注册表选择，负责确定推荐场景、目标和约束。客户端只能请求授权范围内的策略 ID；实际候选召回、排序和重排由 URRE Recommendation Service 执行。租户、用户身份由服务端可信上下文注入，请求体不得携带或覆盖 `user_id`。`session_id` 只用于交互连续性，Project、Task 和 Artifact 仍是业务权威状态。项目型推荐必须携带结构化 `task_context`；`task_description` 只能作为摘要，不能替代已覆盖 Shot、已选素材和多样性约束。

### 2.3 Explore 请求

```json
{
  "domain": "product",
  "seed_entities": ["product_123"],
  "goal": "discover_derivative_products",
  "constraints": {
    "market": ["US", "UK"],
    "price_band": {"min": 15, "max": 80}
  },
  "expansion": {
    "semantic": true,
    "audience": true,
    "category": true,
    "relation": true,
    "trend": true
  },
  "limit": 200
}
```

### 2.4 统一结果

```json
{
  "request_id": "req_001",
  "domain": "video",
  "capability": "search",
  "strategy_version": "video_hybrid_v1",
  "items": [
    {
      "entity_id": "segment_009",
      "entity_type": "segment",
      "video_id": "video_100",
      "shot_id": "shot_008",
      "score": 0.923,
      "rank": 1,
      "recall_channels": ["semantic", "visual"],
      "matched_requirements": ["night_city", "neon_reflection"],
      "evidence": {
        "summary": "雨夜街道霓虹倒影，中景推进镜头",
        "time_range": {"start_ms": 12500, "end_ms": 18800},
        "evidence_refs": ["frame_012500", "clip_preview_009"]
      },
      "availability": "available",
      "rights_status": "verified",
      "feature_version": "video_feature_v3"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  },
  "trace": {
    "query_version": "query_plan_v2",
    "model_versions": ["embed_v4", "ranker_v1"],
    "latency_ms": 86
  }
}
```

线上默认不返回详细调试字段。诊断信息仅在授权诊断和实验场景提供，并执行脱敏和访问控制。

## 3. 视频项目、任务与数据加工 API

### 3.1 项目和任务

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/v1/video/projects` | 创建创作项目 |
| `GET` | `/api/v1/video/projects/{projectId}` | 获取项目及当前上下文 |
| `PATCH` | `/api/v1/video/projects/{projectId}` | 修改项目目标或约束 |
| `POST` | `/api/v1/video/projects/{projectId}/tasks` | 创建创作任务 |
| `GET` | `/api/v1/video/tasks/{taskId}` | 查询任务状态 |
| `POST` | `/api/v1/video/tasks/{taskId}/wait` | 使任务进入 `Waiting`，请求必须带 `waiting_reason` |
| `POST` | `/api/v1/video/tasks/{taskId}/resume` | 从 `Waiting` 恢复任务 |
| `POST` | `/api/v1/video/tasks/{taskId}/cancel` | 取消任务 |

任务状态以 [02 Agent Runtime 与任务治理](../02_AgentRuntime架构设计.md) §4.2 为唯一权威，状态集为 `Created`、`Planned`、`AwaitingApproval`、`Running`、`Waiting`、`Reviewing`、`Completed`、`Failed`、`Cancelled`。不设独立 `Paused` 或 `WAITING_USER`。`Waiting` 必须带原因：`budget_exhausted` / `awaiting_user` / `awaiting_external`。历史上若使用 `/pause`，应映射为进入 `Waiting` 而不是新状态。API 只返回状态、当前步骤、待处理事项、Artifact 引用和可执行操作，不返回模型内部推理链。

### 3.2 创作产物

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/v1/video/projects/{projectId}/briefs` | 创建 CreativeBrief |
| `POST` | `/api/v1/video/projects/{projectId}/storyboards` | 创建 Storyboard |
| `POST` | `/api/v1/video/projects/{projectId}/shot-plans` | 创建 ShotPlan |
| `POST` | `/api/v1/video/projects/{projectId}/material-assignments` | 创建素材分配 |
| `POST` | `/api/v1/video/projects/{projectId}/edit-decisions` | 创建 EditDecision |
| `POST` | `/api/v1/video/projects/{projectId}/timelines` | 创建 Timeline IR |
| `GET` | `/api/v1/video/artifacts/{artifactId}` | 获取指定 Artifact |
| `POST` | `/api/v1/video/artifacts/{artifactId}/approve` | 批准需要审批的 Artifact |

### 3.3 创作型推荐与媒体执行

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/v1/video/compositions/assign` | 将候选素材分配到 ShotPlan |
| `POST` | `/api/v1/video/compositions/evaluate` | 评估素材组合 |
| `POST` | `/api/v1/video/timelines/validate` | 校验 Timeline IR |
| `POST` | `/api/v1/video/renders/preview` | 创建预览渲染任务 |
| `GET` | `/api/v1/video/renders/{renderJobId}` | 获取渲染状态 |
| `POST` | `/api/v1/video/exports` | 创建经授权的导出任务 |
| `GET` | `/api/v1/video/exports/{exportJobId}` | 获取导出状态 |

### 3.4 数据加工与索引入口

原始素材通过统一数据加工入口进入系统，业务 API 不直接向 Elasticsearch 或 Qdrant 写入。上传会话、Job、Profile、配额和 Active Manifest 指针由 `data-control-plane` 管理；Worker 只能上报处理结果和校验报告。

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/v1/data/source-uploads` | 创建受控上传会话，返回 `upload_id` 和短期有效的上传地址 |
| `GET` | `/api/v1/data/source-uploads/{uploadId}` | 查询上传状态、已接收大小和校验结果 |
| `POST` | `/api/v1/data/source-uploads/{uploadId}/finalize` | 校验上传完成、文件 hash 和大小，返回不可变 `source_ref` |
| `POST` | `/api/v1/data/ingestion-jobs` | 批量登记 `source_ref`，执行校验、加工、Embedding 和索引 |
| `GET` | `/api/v1/data/ingestion-jobs/{jobId}` | 查询批次及各阶段状态、失败项和可重试项 |
| `POST` | `/api/v1/data/ingestion-jobs/{jobId}/retry` | 重试失败或指定对象，必须幂等 |
| `POST` | `/api/v1/data/index-builds` | 基于事实源和加工产物创建全量或回填索引任务 |
| `GET` | `/api/v1/data/index-builds/{jobId}` | 查询索引构建、校验和发布状态 |

批量加工请求示例：

```json
{
  "domain": "video",
  "canonical_snapshot_id": "video_asset_snapshot_20261112_001",
  "source_refs": ["objref_001", "objref_002"],
  "input_artifact_refs": [
    {
      "artifact_type": "shot_segments",
      "artifact_ref": "artifact_shot_001",
      "schema_version": "shot_segments_v1",
      "content_hash": "sha256:..."
    }
  ],
  "processing_profile_version": "video_default_v1",
  "embedding_profile_version": "video_multimodal_v1",
  "index_profile_version": "video_hybrid_v1",
  "index_targets": ["keyword", "text_vector", "visual_vector"]
}
```

`canonical_snapshot_id` 必须引用上游业务服务发布的不可变权威快照。`input_artifact_refs` 用于登记上游已经产出的稳定 Shot、Segment、OCR 或商品结构化特征；数据加工平面必须校验 artifact 类型、Schema 版本、权限、来源和 hash，校验通过后直接复用。缺少可用产物或检索侧需要不同表示时，才按 Processing Profile 生成新的 Search Projection。

`source-uploads/finalize` 必须以服务端登记的预期大小和客户端提供的 SHA-256 校验对象；同一上传会话的重复 finalize 返回相同 `source_ref`，不得创建重复原始对象。

索引重建请求示例：

```json
{
  "domain": "video",
  "index_profile_version": "video_hybrid_v1",
  "source_snapshot_id": "snapshot_20261111_001",
  "scope": {
    "ingestion_job_ids": ["ingest_001"],
    "failed_item_refs": [],
    "updated_after": "2026-11-01T00:00:00+08:00",
    "updated_before": null
  },
  "mode": "full_rebuild",
  "publish": "activate_after_validation"
}
```

`mode` 枚举为 `full_rebuild` / `backfill` / `repair`；`publish` 枚举为 `draft_only` / `activate_after_validation`。租户与授权范围由服务端注入，客户端不能通过 `scope` 扩大可见范围。`activate_after_validation` 需要独立索引管理权限；Agent Tool 默认只能创建 Draft，不能直接激活生产索引。重建结果必须返回 `index_version` 和 `manifest_id`。

约束：

- 租户、用户和数据范围由服务端可信上下文注入，请求体不得覆盖。
- `processing_profile_version`、`embedding_profile_version` 和 `index_profile_version` 必须是已注册且已发布的版本。
- `canonical_snapshot_id` 和每个 `input_artifact_refs` 都必须绑定上游可信来源、不可变版本和内容 hash；客户端不能通过引用扩大租户、项目、Rights 或数据范围。
- 数据加工平面不得修正上游权威业务字段，也不得把 Search Projection 或 Understanding 结果反写为业务事实；字段冲突必须拒绝 Job 并返回可归因错误，由上游发布新快照。
- Processing Profile 必须声明上游输入 Schema、允许复用的 Input Artifact 类型和本 Profile 生成的 Search Projection 类型。
- `index_targets` 是当前 Index Profile 声明的枚举子集；`index_profile_version` 固定每个 target 的 Schema 版本。客户端不能传入自由字符串、底层索引名或未注册 Schema。
- 写入请求必须携带 `Idempotency-Key`。重复提交返回同一 Job，不得重复创建素材或向量。
- 客户端提交成功只表示任务已受理，不表示内容已可检索；在线可见性以索引校验和发布结果为准。
- Agent 只能通过受控 Tool 提交任务和查询状态，不能指定原始文件系统路径、FFmpeg 命令、SQL、任意模型或底层索引地址。
- 批量任务必须返回受理数、不可处理数、失败项引用、配额消耗和后续状态查询地址。
- 服务端必须按租户配置单批对象数、并发、存储和处理成本上限；超过配额时拒绝创建 Job，不能先接收再无限排队。

数据 Job 的 Item 与 Batch 状态定义为：

| 对象 | 状态 | 说明 |
|---|---|---|
| Item | `Accepted` / `Ingesting` / `Processing` / `Embedding` / `Indexing` / `Validating` / `Active` | 单个对象的加工与发布状态 |
| Item 终态 | `Failed` / `Cancelled` | 保留失败阶段、错误码和是否可重试 |
| Batch | `Accepted` / `Running` / `PartiallyCompleted` / `Completed` | 汇总 Item 成功、失败和重试数量 |
| Batch 终态 | `Failed` / `Cancelled` | 失败或取消批次仍保留逐 Item 结果 |

视频元数据中的 `ingest_status`、`analysis_status` 和 `index_status` 是兼容用粗粒度投影，不能作为独立状态机。所有 Item 与 Batch 转换发布 `data.job.status_changed` 事件，并携带 `job_kind`、`job_id`、`item_ref`、`from`、`to` 和 `stage`。

| 投影字段 | 映射 |
|---|---|
| `ingest_status` | `Accepted` → `pending`；`Ingesting` → `running`；进入 `Processing` 后为 `completed`，Ingest 阶段失败为 `failed` |
| `analysis_status` | `Accepted` / `Ingesting` → `pending`；`Processing` / `Embedding` → `running`；`Indexing` 起为 `completed`，分析或 Embedding 失败为 `failed` |
| `index_status` | `Indexing` / `Validating` → `running`；`Active` → `active`；索引阶段失败为 `failed` |

`Cancelled` 在所有投影字段中映射为 `cancelled`。这些字段不能反向触发状态转换。

### 3.5 证据解析

检索结果只返回受控 `evidence_ref`，客户端或 Agent 不能根据内部路径自行拼接媒体地址。

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/v1/evidence/resolve` | 批量解析候选证据，返回摘要、时间区间和经授权的短期预览地址 |

请求示例：

```json
{
  "evidence_refs": ["frame_012500", "clip_preview_009"],
  "purpose": "material_preview",
  "usage_context": {
    "project_id": "project_456"
  }
}
```

Evidence Resolver 必须重新校验租户、项目、Rights、用途和地域，返回逐项允许/拒绝结果和过期时间。租户、用户和地域来自服务端可信上下文，不能由客户端覆盖。不得把原始文件系统路径、长期对象存储地址或无权限源文件地址写入日志或响应。

## 4. Agent Tool 契约

Tool 只暴露语义能力，不暴露底层客户端。

| Tool | 输入 | 输出 | 风险等级 |
|---|---|---|---|
| `search_video_materials` | SearchRequest | CandidateSet | L0 只读 |
| `recommend_video_materials` | RecommendationRequest | RecommendationSet | L0 只读 |
| `find_similar_shots` | EntityRef + constraints | CandidateSet | L0 只读 |
| `explore_video_materials` | Seed + goal | ExplorationSet | L0 只读 |
| `rerank_candidates` | CandidateSet ref + authorized ranking policy | CandidateSet | L0 只读 |
| `explain_retrieval_result` | request_id / result ref + explanation scope | ExplanationReport | L0 只读 |
| `get_profile_summary` | user / context ref + purpose | ProfileSummary | L0 只读，敏感 |
| `get_project_context` | project_id | ProjectContext | L0 只读 |
| `get_artifact` | artifact_id | Artifact | L0 只读 |
| `create_artifact` | type + schema + content | ArtifactRef | L1 写草稿 |
| `submit_data_processing_job` | domain + authorized source refs + registered profile | DataJobRef | L2 资源消耗 |
| `get_data_processing_job` | job_id | DataJobStatus | L0 只读 |
| `resolve_evidence` | evidence refs + purpose + usage context | EvidenceViewSet | L0 只读，敏感 |
| `assign_materials` | ShotPlan + candidates | AssignmentSet | L1 写草稿 |
| `validate_timeline` | TimelineIR | ValidationReport | L0 只读 |
| `render_preview` | TimelineIR ref | RenderJobRef | L2 资源消耗 |
| `submit_for_approval` | artifact/action ref | ApprovalRef | L3 流程操作 |
| `export_video` | approved render ref | ExportJobRef | L4 高风险 |

每个 Tool 必须声明：

- 输入输出 JSON Schema。
- 租户、身份和权限要求。
- 风险等级与审批策略。
- 超时、重试、幂等键和调用预算。
- 审计字段、错误码和结果脱敏策略。

补充约束：

- `rerank_candidates` 只能重排调用方已经获得的候选集，不能扩大候选范围、恢复已被硬约束过滤的候选或更换未注册的排序模型。
- `explain_retrieval_result` 只能解释已有请求、候选、召回通道和证据；结果必须区分事实、模型判断与未知项。
- `get_profile_summary` 必须声明调用目的，只返回完成当前任务所需的最小字段，并受租户、用户和数据范围权限约束；不得暴露原始行为序列、敏感属性或完整画像。
- `submit_data_processing_job` 只能引用调用者有权访问的来源和已注册 Processing/Embedding/Index Profile，不得绕过租户/Rights 校验、单批上限、成本配额或直接写入 ES/Qdrant；完成状态必须由 Job 事件确认。
- `resolve_evidence` 必须携带用途和上下文，只返回调用者有权查看的最小证据；拒绝项不能泄露对象是否存在。
- 通用 Toolkit 名称与领域 Tool 可以不同，但领域 Tool 必须映射到对应的 URRE 或领域基础服务，并遵守相同的 Policy Gateway 规则。
- Agent 默认不拥有高价值反馈写入 Tool。曝光与点击等 UI 遥测由前端/Event Service 记录；`material.assigned`、`material.timeline_adopted`、`material.final_kept` 和导出转化由业务 Service 在状态迁移成功后通过 Outbox 发出。

示例：

```java
public record SearchVideoRequest(
    String projectId,
    String taskId,
    String query,
    List<String> targetLevels,
    Map<String, Object> filters,
    List<String> recallChannels,
    Integer limit
) {}

public record SearchVideoResult(
    String requestId,
    List<VideoCandidate> items,
    String nextCursor
) {}
```

示例是业务契约示意，不绑定 AgentScope 的易变注解或构造 API。

## 5. 核心数据契约

### 5.1 实体引用

Video、Shot、Segment 的权威定义见 [Video Domain Pack](../03_VideoDomain架构设计.md)。跨 API 引用时至少包含：

```json
{
  "video_id": "video_100",
  "shot_id": "shot_008",
  "segment_id": "segment_009",
  "start_ms": 12500,
  "end_ms": 18800
}
```

时间字段使用整数毫秒；需要帧精确定位时同时提供帧率或帧序号。Segment 必须能够回溯 Shot 和源 Video。

Video 元数据至少按以下类别维护：

- 标识：`video_id`、`tenant_id`、`asset_owner_id`、`source_type`、`source_uri`。
- 媒体：`duration_ms`、`width`、`height`、`fps`、`codec`、`bitrate`、`file_size`。
- 格式：`aspect_ratio`、`orientation`、`container`、`audio_tracks`。
- Rights：`license_type`、`commercial_allowed`、`territory`、`expiry_at`、`attribution_required`。
- 质量：分辨率、清晰度、稳定性、曝光和压缩质量分数。
- 内容理解：标题、描述、标签、场景、动作、主体、情绪及合法合规的敏感用途说明。
- 模型版本：ASR、OCR、视觉理解和 Embedding 版本。
- 版本：`content_version`、`metadata_version`、`rights_version`、`processing_artifact_version`、`embedding_versions`、`index_profile_version`。
- 生命周期：`ingestion_job_id`、`processing_job_id`、`index_job_id`、`ingest_status`、`analysis_status`、`index_status`、`active_index_version`、`created_at`、`updated_at`。

视频领域关系不能只使用一个 `similar_to`。至少区分视觉相似、语义相关、同场景、同实体、替代拍摄、叙事衔接、互补、项目采用和 Shot 分配，并记录关系来源、置信度、模型版本和更新时间。

### 5.2 MaterialAssignment

```json
{
  "assignment_id": "ma_001",
  "project_id": "project_001",
  "storyboard_version": 3,
  "shot_plan_id": "shotplan_002",
  "storyboard_shot_id": "sb_shot_014",
  "entity_ref": {
    "entity_type": "segment",
    "entity_id": "segment_009",
    "source_video_id": "video_100",
    "selected_time_range": {"start_ms": 12500, "end_ms": 18800}
  },
  "match_evidence": {
    "summary": "近景机械臂抓取，时长满足镜头目标",
    "evidence_refs": ["frame_012500"]
  },
  "alternatives": [
    {"entity_type": "segment", "entity_id": "segment_011"}
  ],
  "selection_reason": "画面包含机械臂精准抓取动作，近景构图符合该镜头需求",
  "user_confirmed": false,
  "rights_status": "verified",
  "scores": {
    "semantic_fit": 0.91,
    "visual_fit": 0.88,
    "technical_quality": 0.93,
    "task_fit": 0.90
  },
  "status": "proposed"
}
```

Material Assignment 字段级以此为准，概念关系见 `03` §6。最小字段集：`shot_plan_id`（必填）、`storyboard_shot_id`（必填）、`entity_ref`（含 `entity_type`、id、`selected_time_range`）、`match_evidence`、`alternatives`、`selection_reason`、`user_confirmed`、`rights_status`。`scores`、`status` 为实施扩展。不再使用 `locked_by_user`；若历史数据出现该字段，与 `user_confirmed` 同义，以 `user_confirmed` 为准。`entity_type` 枚举为 `video` / `shot` / `segment`。与 `03` §6.5 旧称的对照见 `03` 本节表格。不把 `04` 中的 `Asset` / `Clip` / `AgentRun` 作为实施契约。

### 5.3 EditDecision

```json
{
  "edit_decision_id": "ed_001",
  "project_id": "project_001",
  "source_storyboard_version": 3,
  "timeline_settings": {
    "fps_num": 25,
    "fps_den": 1,
    "width": 1920,
    "height": 1080
  },
  "clips": [
    {
      "clip_id": "clip_001",
      "source_video_id": "video_100",
      "source_segment_id": "segment_009",
      "source_in_ms": 12500,
      "source_out_ms": 18800,
      "sequence_order": 1,
      "duration_target_ms": 6300,
      "position_intent": null,
      "speed": 1.0,
      "transition_in": null,
      "transition_out": {"type": "cut"}
    }
  ],
  "audio_tracks": [],
  "text_overlays": []
}
```

EditDecision 表达顺序、入出点和编辑意图。绝对 `timeline_start_ms`、最终轨道分配和帧级落位由 Timeline Resolver 生成到 Timeline IR，不在 EditDecision 中提前固化。

### 5.4 Artifact

每个 Artifact 至少包含：

- `artifact_id`
- `artifact_type`
- `schema_version`
- `project_id`
- `task_id`
- `parent_artifact_ids`
- `content_ref`
- `content_hash`
- `producer_tool`
- `model_version`
- `validation_status`
- `permission_scope`
- `created_at`

### 5.5 IndexManifest

IndexManifest 是 ES 与 Qdrant 索引版本的发布清单。控制面只保存一个当前 Active Manifest 指针，切换该指针时使用版本号 CAS，不能分别把两个底层 Alias 当作跨系统事务。

```json
{
  "manifest_id": "manifest_20261111_001",
  "domain": "video",
  "index_profile_version": "video_hybrid_v1",
  "source_snapshot_id": "snapshot_20261111_001",
  "processing_versions": ["video_default_v1"],
  "embedding_versions": ["video_multimodal_v1"],
  "targets": [
    {
      "engine": "elasticsearch",
      "physical_name": "video_search_20261111_001",
      "alias": "video_search_active_candidate",
      "schema_version": "video_keyword_schema_v3",
      "document_count": 100000,
      "checksum": "sha256:..."
    },
    {
      "engine": "qdrant",
      "physical_name": "video_text_20261111_001",
      "alias": "video_text_active_candidate",
      "schema_version": "video_text_vector_schema_v2",
      "point_count": 100000,
      "checksum": "sha256:..."
    }
  ],
  "status": "validated",
  "parent_manifest_id": "manifest_20261110_003",
  "created_by": "data-control-plane",
  "built_by": "indexing-worker",
  "created_at": "2026-11-11T10:00:00+08:00",
  "activated_at": null
}
```

发布流程必须满足：

- 所有 target 的校验报告提交给 `data-control-plane` 并复核通过后，Manifest 才能进入 `Validated`；每个 target 使用自己的预期数量、逻辑对象主键覆盖和关键字段标准，ES 文档数不要求与多向量 Qdrant Point 数相等。
- 任一侧失败时 Manifest 进入 `Failed`，不得发布成功目标或切换 Active 指针。
- 只有 `data-control-plane` 能执行激活；激活使用 `expected_current_manifest_id + version` 的 CAS，冲突时拒绝覆盖并重新校验。
- 在线请求固定使用请求开始时读取的 Manifest；旧 Manifest 在所有引用请求和灰度窗口结束后才能回收。
- 日常增量不满足 Item 级可见性隔离时，只能进入 `Draft` 或创建新索引代际，不能声称已原子发布。

## 6. 事件契约

### 6.1 统一字段

```json
{
  "event_id": "evt_001",
  "event_type": "material.timeline_adopted",
  "event_time": "2026-11-10T10:00:00+08:00",
  "tenant_id": "tenant_001",
  "user_id": "user_001",
  "project_id": "project_001",
  "task_id": "task_001",
  "session_id": "session_001",
  "request_id": "req_001",
  "agent_run_id": "run_001",
  "domain": "video",
  "entity_type": "segment",
  "entity_id": "segment_009",
  "position": 2,
  "strategy_version": "video_project_recommend_v1",
  "properties": {
    "timeline_start_ms": 12500,
    "used_duration_ms": 6300
  }
}
```

### 6.2 关键事件

- `video.ingested`
- `video.analysis.completed`
- `video.indexed`
- `data.ingestion.accepted`
- `data.search_projection.generated`（替代 `data.asset.normalized`；旧事件名仅用于兼容过渡）
- `data.analysis.completed`
- `data.embedding.completed`
- `data.indexing.completed`
- `data.indexing.failed`
- `data.index.activated`
- `data.job.status_changed`
- `retrieval.requested`
- `retrieval.completed`
- `recommendation.impression`
- `recommendation.clicked`
- `preview.started`
- `preview.completed`
- `asset.downloaded`
- `asset.favorited`
- `material.added_to_collection`
- `material.timeline_adopted`
- `material.final_kept`
- `timeline.created`
- `render.completed`
- `export.completed`
- `agent.task.completed`
- `agent.tool.failed`
- `user.feedback.submitted`

反馈必须关联请求、候选集、位置、策略版本和后续业务结果。未点击不能直接视为明确负反馈。

## 7. 实时任务事件

前端通过 SSE 或 WebSocket 接收：

- `task.status.changed`
- `agent.thinking.summary`
- `agent.tool.started`
- `agent.tool.completed`
- `retrieval.progress`
- `composition.progress`
- `artifact.created`
- `approval.required`
- `render.progress`
- `task.completed`
- `task.failed`

`agent.thinking.summary` 只提供可审计的决策摘要、调用能力和下一步状态，不暴露 Chain-of-Thought。

## 8. 错误与幂等

统一错误结构至少包含：

```json
{
  "request_id": "req_001",
  "code": "RIGHTS_FILTER_REQUIRED",
  "message": "当前用途要求有效商业授权",
  "retryable": false,
  "details": {}
}
```

错误码需要区分：

- 请求格式或 Schema 错误。
- 鉴权、租户和项目权限错误。
- 业务硬约束或 Rights 错误。
- 超时、限流和临时依赖错误。
- 模型、检索或媒体任务失败。
- 审批缺失或计划已失效。
- 预算、步骤或资源耗尽。

有副作用的请求必须携带幂等键。重试不能重复创建渲染任务、审批记录、导出请求或其他不可逆操作。

数据加工请求的客户端幂等键只用于识别同一请求；内容、Embedding 和索引写入还必须使用服务端生成的 Processing、Embedding 和 Index Item Key。`data-control-plane` 拒绝 Worker 直接切换 Active Manifest，并把 CAS 冲突映射为可重试的版本冲突错误。
