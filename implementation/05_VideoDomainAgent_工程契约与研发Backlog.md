# Video Domain Agent 工程契约与研发 Backlog

> **文档层级：** 工程实施契约  
> **对应设计：** [Video Domain Agent 详细设计与实施手册](04_VideoDomainAgent_详细设计与实施手册.md)  
> **验证脚本：** [纵向切片与验收脚本](06_VideoDomainAgent_纵向切片与验收脚本.md)  
> **状态：** Schema、表结构和 Ticket 是可开发基线；正式实现需生成 OpenAPI、JSON Schema、DDL 迁移和自动化契约测试。

---

## 1. 使用方式

本文件回答四个工程问题：

1. 代码放在哪里，模块允许怎样依赖。
2. 服务之间和 Agent Tool 之间用什么数据契约。
3. 状态写入哪些表，如何恢复和保证幂等。
4. 团队按什么 Ticket 顺序完成可验收的纵向切片。

规则：

- 本文的 Java/JSON/DDL 是基线，不绑定尚未冻结的框架细微 API。
- 所有 JSON 必须同时有 JSON Schema 和反序列化测试。
- 所有写操作必须有 `Idempotency-Key`。
- 所有表必须有 `tenant_id`、`created_at`、`updated_at` 和 `row_version`，下文不重复强调。
- 时间统一使用 UTC RFC 3339 存储；视频时间统一使用整数毫秒。
- ID 使用带类型前缀的字符串或 UUID，不用可猜测的连续数字暴露业务规模。

---

## 2. Monorepo 与模块

```text
video-domain-agent/
├── build.gradle.kts
├── settings.gradle.kts
├── contracts/
│   ├── openapi/
│   │   ├── video-api.yaml
│   │   └── retrieval-api.yaml
│   ├── schemas/
│   │   ├── task-brief.v1.schema.json
│   │   ├── creative-brief.v1.schema.json
│   │   ├── storyboard.v1.schema.json
│   │   ├── shot-plan.v1.schema.json
│   │   ├── search-plan.v1.schema.json
│   │   ├── candidate-set.v1.schema.json
│   │   ├── material-assignment.v1.schema.json
│   │   ├── edit-decision.v1.schema.json
│   │   ├── timeline-ir.v1.schema.json
│   │   ├── quality-report.v1.schema.json
│   │   └── agent-event.v1.schema.json
│   ├── events/
│   │   └── event-catalog.yaml
│   └── tools/
│       └── video-tools.v1.yaml
├── app/
│   ├── application-api/
│   ├── application-service/
│   ├── security/
│   └── bootstrap/
├── agent-runtime/
│   ├── runtime-core/
│   ├── workflow-engine/
│   ├── policy-gateway/
│   ├── tool-registry/
│   ├── checkpoint/
│   └── tracing/
├── video-domain/
│   ├── video-domain-core/
│   ├── video-agent/
│   ├── video-agent-tools/
│   ├── video-workflows/
│   ├── video-composition/
│   ├── video-timeline/
│   ├── video-quality/
│   └── video-adapters/
├── retrieval/
│   ├── retrieval-api/
│   ├── retrieval-core/
│   ├── query-planner/
│   ├── recall/
│   ├── ranking/
│   ├── recommendation/
│   ├── feedback/
│   └── retrieval-client/
├── data-platform/
│   └── data-control-plane/
├── workers/
│   ├── ingest-worker/
│   ├── content-processing-worker/
│   ├── indexing-worker/
│   ├── media-worker/
│   └── event-worker/
├── test-support/
│   ├── fixtures/
│   ├── fake-urre/
│   ├── fake-render/
│   └── security-testkit/
├── deploy/
│   ├── compose/
│   ├── k8s/
│   └── observability/
└── docs/
    ├── adr/
    ├── runbooks/
    └── evals/
```

### 2.1 模块依赖

```text
application-api
  → application-service
  → video-agent
  → video-workflows
  → contracts

video-workflows
  → video-domain-core
  → video-agent-tools
  → agent-runtime
  → contracts

video-agent
  → agent-runtime
  → video-agent-tools
  → contracts

video-agent-tools
  → retrieval-client
  → video-domain-core
  → contracts
  ×→ recall-engine
  ×→ media-worker
  ×→ database

retrieval-api
  → retrieval-core
  → contracts
  ×→ video-agent
  ×→ application-service

video-timeline
  → video-domain-core
  → contracts
  ×→ llm client

video-quality
  → video-domain-core
  → contracts
  → quality adapters
  ×→ video-workflows
```

### 2.2 模块所有权

| 模块 | Owner 建议 | 不能越过的边界 |
|---|---|---|
| Contracts | 平台架构/领域 | 只有经过版本化审阅才能改 |
| Runtime/Workflow | Agent 平台 | 不实现视频检索和媒体逻辑 |
| Video Agent | 视频领域 | 不访问底层索引和媒体命令 |
| Retrieval | 检索推荐 | 不启动 Agent，不保存项目创作流程 |
| Composition | 视频领域/算法 | 不渲染，不写 NLE 文件 |
| Timeline/Media | 媒体平台 | 不解释自然语言，不调用 LLM 生成命令 |
| Quality | 独立 QA | 不调用生产工作流修改自身输入 |

---

## 3. 配置基线

```yaml
app:
  timezone: UTC
  api_prefix: /api/v1
  max_upload_size_mb: 2048
  sse_heartbeat_seconds: 15

security:
  tenant_header_trusted_only_from_gateway: true
  require_idempotency_for_mutations: true
  signed_url_ttl_seconds: 300

runtime:
  max_model_calls: 12
  max_tool_calls: 40
  max_replans: 1
  max_run_minutes: 15
  max_same_failure_attempts: 2
  max_tool_error_streak: 2
  checkpoint_after_each_step: true

retrieval:
  default_candidate_budget: 200
  default_result_limit: 30
  max_candidate_budget: 500
  max_result_limit: 50
  search_timeout_ms: 8000
  recommend_timeout_ms: 8000
  channel_timeout_ms: 2500
  max_page_size: 50
  agent_view_limit_per_shot: 10
  max_agent_followup_pages: 1
  max_sub_queries: 5

composition:
  shortlist_per_shot: 10
  max_alternatives_per_shot: 3
  strategy_id: video_composition_baseline_v1

render:
  preview_profile: p720
  preview_timeout_seconds: 900
  max_preview_duration_seconds: 180
  worker_concurrency: 2

quality:
  max_revisions: 2
  retain_best_version: true
  hard_gate_failure_stops_delivery: true
```

所有配置需有环境覆盖、启动校验和审计快照。运行记录保存配置版本，不依赖部署时“大概一致”。

---

## 4. API 契约

### 4.1 通用 Header

```http
Authorization: Bearer <token>
X-Tenant-Id: <injected-by-trusted-gateway>
X-Request-Id: <client-or-generated>
Idempotency-Key: <required for mutation>
Traceparent: <W3C trace context>
```

服务端不得信任客户端自报 `user_id`、角色或 Rights 范围。

### 4.2 项目与任务

```http
POST /api/v1/video/projects
POST /api/v1/video/projects/{project_id}/tasks
GET  /api/v1/video/tasks/{task_id}
POST /api/v1/video/tasks/{task_id}/pause
POST /api/v1/video/tasks/{task_id}/resume
POST /api/v1/video/tasks/{task_id}/cancel
POST /api/v1/video/tasks/{task_id}/actions/build-timeline
POST /api/v1/video/tasks/{task_id}/approvals
GET  /api/v1/video/approvals/{approval_id}
POST /api/v1/video/tasks/{task_id}/budget-adjustments
GET  /api/v1/video/tasks/{task_id}/stream
```

创建任务请求：

```json
{
  "goal": "制作一条 30 秒智能机器人工业应用宣传片",
  "mode": "creation",
  "source_scope": {
    "type": "project_library",
    "library_ids": ["lib_001"]
  },
  "constraints": {
    "duration_ms": 30000,
    "aspect_ratio": "16:9",
    "language": "zh-CN",
    "commercial_use": true
  },
  "execution": {
    "quality_profile": "standard",
    "require_material_confirmation": true,
    "require_export_confirmation": true
  }
}
```

响应：

```json
{
  "task_id": "task_001",
  "status": "created",
  "stream_url": "/api/v1/video/tasks/task_001/stream",
  "resource_version": "1"
}
```

预算调整请求只允许授权管理操作，不能由 Agent Tool 调用：

```json
{
  "resource_type": "llm_token",
  "requested_delta": 20000,
  "reason": "quality review retry approved by owner",
  "scope": {"run_id": "run_001", "step_id": "quality_review"},
  "approval_id": "approval_001"
}
```

预算调整成功后，Workflow 才能把 `WaitingBudget` 转回 `Running`。

### 4.3 Search

```http
POST /api/v1/retrieval/search
```

```json
{
  "domain": "video",
  "query": "工程师与机械臂协作的近景",
  "target_levels": ["segment"],
  "context": {
    "project_id": "project_001",
    "task_id": "task_001",
    "shot_id": "shot_003"
  },
  "filters": {
    "commercial_allowed": true,
    "duration_ms": {"gte": 2000, "lte": 10000},
    "orientation": ["landscape"]
  },
  "recall": {
    "channels": ["keyword", "semantic", "metadata"],
    "candidate_budget": 200
  },
  "ranking": {
    "strategy_id": "video_hybrid_v1",
    "limit": 30
  },
  "page": {"size": 30, "cursor": null}
}
```

### 4.4 Recommendation

```http
POST /api/v1/retrieval/recommend
```

```json
{
  "domain": "video",
  "scene": "shot_candidate",
  "context": {
    "project_id": "project_001",
    "task_id": "task_001",
    "shot_id": "shot_003",
    "current_stage": "material_collection",
    "shot_intent": {
      "visual_goal": "人机协作完成精密装配",
      "shot_type": "medium_close_up",
      "duration_ms": 5000,
      "mood": "confident"
    },
    "task_context": {
      "covered_shot_ids": ["shot_001", "shot_002"],
      "selected_entity_refs": [
        {"shot_id": "shot_001", "entity_id": "segment_factory_001"}
      ],
      "diversity_targets": {
        "avoid_same_segment": true,
        "max_per_visual_cluster": 3
      }
    },
    "excluded_entity_ids": ["segment_001", "segment_002"]
  },
  "strategy": {
    "strategy_id": "video_shot_task_fit_v1",
    "objective": "task_fit_then_diversity"
  },
  "limit": 30,
  "diversity": {
    "enabled": true,
    "max_per_visual_cluster": 3
  }
}
```

### 4.5 Feedback

```http
POST /api/v1/retrieval/feedback
Idempotency-Key: feedback-ui-event-001
```

```json
{
  "event_type": "recommendation.clicked",
  "source": "video_workbench",
  "occurred_at": "2026-11-11T10:20:00Z",
  "request_id": "req_search_001",
  "candidate_set_id": "cs_001",
  "project_id": "project_001",
  "task_id": "task_001",
  "shot_id": "shot_003",
  "entity_id": "segment_009",
  "position": 2,
  "strategy_version": "video_shot_task_fit_v1",
  "properties": {
    "confirmation_id": "confirm_001"
  }
}
```

客户端只提交 UI 遥测。`material.assigned`、`material.timeline_adopted`、`material.final_kept` 等业务事实由 Assignment/Timeline/Export Service 在数据库状态迁移成功后通过 Outbox 生成，不由客户端或 Agent 伪造。

Feedback source 白名单：

| 来源 | 允许的值 | 写入路径 |
|---|---|---|
| 外部 UI | `video_workbench`、`timeline_editor`、`api_ui` | 公开 Feedback API |
| 业务服务 | `assignment_service`、`timeline_service`、`render_service`、`export_service` | Outbox |
| 平台事件 | `event_service` | Outbox / 内部 Consumer |

外部请求不能声明业务服务 source；未知 source 或 source 与 event_type 不匹配时返回 `VALIDATION_ERROR`。

### 4.6 Artifact

```http
GET  /api/v1/video/artifacts/{artifact_id}
GET  /api/v1/video/artifacts/{artifact_id}/versions
POST /api/v1/video/artifacts/{artifact_id}/approve
```

Artifact 下载必须经权限检查并返回短期签名 URL；数据库不保存长期公共 URL。

### 4.7 Composition、Timeline、Render

```http
POST /api/v1/video/compositions/assign
POST /api/v1/video/compositions/evaluate
PATCH /api/v1/video/assignments/{assignment_set_id}
POST /api/v1/video/assignments/{assignment_set_id}/confirm
POST /api/v1/video/timelines/validate
POST /api/v1/video/renders/preview
GET  /api/v1/video/renders/{render_job_id}
POST /api/v1/video/quality-reviews
POST /api/v1/video/exports
```

### 4.8 Run 与事件

```http
GET /api/v1/video/agent-runs/{run_id}
GET /api/v1/video/agent-runs/{run_id}/events?after_sequence=120
```

事件流只返回可审计摘要：

```json
{
  "event_id": "evt_001",
  "sequence": 121,
  "event_type": "tool.completed",
  "task_id": "task_001",
  "run_id": "run_001",
  "step_id": "shot_materialize_shot_003",
  "summary": "Retrieved 18 candidates; 8 passed hard filters.",
  "artifact_ref": "artifact://candidate-set/cs_003",
  "created_at": "2026-11-11T10:11:05Z"
}
```

### 4.9 错误格式

```json
{
  "request_id": "req_001",
  "trace_id": "trace_001",
  "code": "RIGHTS_FILTER_REQUIRED",
  "category": "policy",
  "message": "当前用途要求有效商业授权",
  "retryable": false,
  "details": {
    "field": "filters.commercial_allowed"
  }
}
```

错误类别固定为：

- `validation`
- `authentication`
- `authorization`
- `policy`
- `not_found`
- `conflict`
- `rate_limited`
- `dependency_timeout`
- `model_error`
- `media_error`
- `budget_exhausted`
- `internal`

---

## 4A. 核心 Port 接口

以下接口用于冻结模块边界。名称可按代码规范调整，但输入必须使用可信上下文、输出必须使用版本化 Artifact 或明确 Result，不允许返回底层 ORM 实体。

```java
public interface RetrievalGateway {
    CandidateSet search(TenantContext context, SearchRequest request);
    CandidateSet recommend(TenantContext context, RecommendationRequest request);
    CandidateSet similar(TenantContext context, SimilarRequest request);
    FeedbackReceipt recordFeedback(TenantContext context, FeedbackRequest request);
}

public interface SearchPlanner {
    PlannedSearch plan(TenantContext context, RetrievalIntent intent, PlanningBudget budget);
}

public interface RecommendationStrategyRegistry {
    RecommendationStrategy resolve(
        TenantContext context,
        String scene,
        String strategyId
    );
}

public interface ProjectArtifactStore {
    ProjectContext getProjectContext(TenantContext context, String projectId);
    ArtifactRef createDraft(TenantContext context, ArtifactDraft draft);
    Artifact getArtifact(TenantContext context, ArtifactRef ref);
    List<ArtifactRef> findStaleDependents(TenantContext context, ArtifactRef changed);
}

public interface CompositionEngine {
    AssignmentSet assign(
        TenantContext context,
        ShotPlanRef shotPlan,
        List<CandidateSetRef> candidateSets,
        CompositionPolicy policy
    );

    CompositionEvaluation evaluate(
        TenantContext context,
        AssignmentSet assignment,
        CompositionPolicy policy
    );
}

public interface EditDecisionBuilder {
    EditDecision build(
        TenantContext context,
        AssignmentSetRef confirmedAssignment,
        TimelineProfile profile
    );
}

public interface TimelineService {
    ValidationReport validate(TenantContext context, TimelineIR timeline);
    CompilePlan compile(TenantContext context, TimelineIR timeline);
}

public interface MediaExecutionGateway {
    RenderJobRef submitPreview(
        TenantContext context,
        TimelineRef timeline,
        PreviewProfile profile,
        IdempotencyKey key
    );

    RenderStatus getStatus(TenantContext context, String renderJobId);
}

public interface QualityReviewService {
    QualityReport review(
        TenantContext context,
        ReviewRequest request,
        QualityPolicy policy
    );
}

public interface AgentToolExecutor {
    ToolResult execute(
        TenantContext context,
        AgentRunContext run,
        ToolCall call
    );
}
```

### 4A.1 Port 约束

- `TenantContext` 由鉴权层创建，不是可反序列化的请求字段。
- `RetrievalGateway` 只能返回 CandidateSet，不返回内部召回通道客户端。
- `SearchPlanner` 不能执行检索，只生成通过 Schema 校验的 `PlannedSearch`。
- `RecommendationStrategyRegistry` 只解析已发布策略，不能即时创建权重。
- `CompositionEngine` 返回评分和理由，不直接修改 Timeline。
- `TimelineService` 不调用 LLM，不执行 Shell。
- `MediaExecutionGateway` 异步提交，不返回宿主路径。
- `QualityReviewService` 不依赖执行 Workflow，只消费冻结输入。
- `AgentToolExecutor` 必须先 Registry 校验，再 Policy 鉴权，再调用 Port。

### 4A.2 Adapter 清单

| Port | MVP Adapter | 生产 Adapter |
|---|---|---|
| `RetrievalGateway` | Fake URRE / in-memory index | URRE HTTP/gRPC |
| `RecommendationStrategyRegistry` | YAML 注册表 | Domain Strategy Service |
| `ProjectArtifactStore` | PostgreSQL + local object store | PostgreSQL/MySQL + S3/MinIO |
| `CompositionEngine` | 规则与线性加权 | 约束优化/学习型组合 |
| `TimelineService` | Java compiler + ffprobe | FFmpeg/NLE Adapter |
| `MediaExecutionGateway` | Fake Render | Queue + isolated Worker |
| `QualityReviewService` | 规则门禁 | Rules + independent model/human |

Adapter 测试使用同一套 Port Contract Test；切换 Adapter 不得改变上层业务代码。

---

## 5. JSON Schema 基线

### 5.1 通用约束

每个 Artifact Schema：

- 必须声明 `schema_version`。
- `additionalProperties` 默认 `false`。
- 枚举变化按兼容性处理。
- 删除或修改字段语义必须提升 Major 版本。
- 时间区间必须满足 `start_ms < end_ms`。
- ID 和 URI 有长度上限。
- 数组有 `maxItems`，防止 Agent 输出失控。
- 文本字段有长度上限，并在进入 Prompt 前标记为不可信数据。

### 5.2 SearchPlan

关键字段：

```json
{
  "$id": "urn:video:search-plan:v1",
  "type": "object",
  "required": [
    "schema_version",
    "plan_id",
    "domain",
    "target_levels",
    "semantic_query",
    "hard_filters",
    "recall_channels",
    "candidate_budget"
  ],
  "properties": {
    "schema_version": {"const": "1.0"},
    "plan_id": {"type": "string", "maxLength": 64},
    "domain": {"const": "video"},
    "target_levels": {
      "type": "array",
      "items": {"enum": ["video", "shot", "segment"]},
      "minItems": 1,
      "maxItems": 3
    },
    "semantic_query": {"type": "string", "minLength": 1, "maxLength": 500},
    "sub_queries": {"type": "array", "maxItems": 5},
    "hard_filters": {"type": "object"},
    "soft_preferences": {"type": "object"},
    "recall_channels": {"type": "array", "maxItems": 6},
    "candidate_budget": {"type": "integer", "minimum": 20, "maximum": 500},
    "max_latency_ms": {"type": "integer", "minimum": 500, "maximum": 15000}
  },
  "additionalProperties": false
}
```

### 5.3 CandidateSet

```json
{
  "schema_version": "1.0",
  "candidate_set_id": "cs_001",
  "request_id": "req_001",
  "capability": "search",
  "handled_by": "agent",
  "project_id": "project_001",
  "task_id": "task_001",
  "shot_id": "shot_003",
  "strategy_version": "video_hybrid_v1",
  "created_at": "2026-11-11T10:11:05Z",
  "items": [
    {
      "candidate_id": "cand_001",
      "entity_type": "segment",
      "entity_id": "segment_009",
      "video_id": "video_100",
      "source_shot_id": "source_shot_008",
      "time_range": {"start_ms": 12500, "end_ms": 18800},
      "rank": 1,
      "score": 0.923,
      "score_breakdown": {
        "keyword": 0.84,
        "semantic": 0.94,
        "metadata": 0.90
      },
      "recall_channels": ["keyword", "semantic"],
      "candidate_origin": "search",
      "matched_requirements": ["human_robot_collaboration", "factory"],
      "evidence": {
        "summary": "工程师与机械臂协作完成装配",
        "time_range": {"start_ms": 12500, "end_ms": 18800},
        "evidence_refs": ["artifact://evidence/ev_001"],
        "keyframes": ["artifact://frame/f_001"]
      },
      "rights": {
        "status": "verified",
        "commercial_allowed": true,
        "territory": ["CN"],
        "attribution_required": false
      },
      "technical": {
        "width": 1920,
        "height": 1080,
        "fps": 25,
        "duration_ms": 6300
      },
      "versions": {
        "feature_version": "vf_3",
        "model_versions": ["embed_4", "ranker_1"],
        "index_version": "idx_10"
      }
    }
  ],
  "page": {"next_cursor": null, "has_more": false},
  "warnings": []
}
```

### 5.4 Storyboard

```json
{
  "schema_version": "1.0",
  "storyboard_id": "sb_001",
  "project_id": "project_001",
  "creative_brief_id": "cb_001",
  "duration_ms": 30000,
  "scenes": [
    {
      "scene_id": "scene_01",
      "narrative_role": "opening",
      "summary": "未来工厂全景建立科技感",
      "shots": [
        {
          "shot_id": "shot_001",
          "narrative_role": "establishing",
          "visual_goal": "智能工厂全景，机械臂生产线有序运转",
          "target_duration_ms": 5000,
          "transition_out": "cut"
        }
      ]
    }
  ]
}
```

### 5.5 ShotPlan

```json
{
  "schema_version": "1.0",
  "shot_plan_id": "shotplan_001",
  "storyboard_id": "sb_001",
  "storyboard_version": 1,
  "shots": [
    {
      "shot_id": "shot_003",
      "narrative_role": "proof",
      "visual_goal": "工程师与机械臂协作完成精密装配",
      "subject": ["engineer", "industrial_robot_arm"],
      "action": ["collaborative_assembly"],
      "scene": ["modern_factory"],
      "shot_type": "medium_close_up",
      "camera_motion": "slow_push_in",
      "mood": ["confident", "precise"],
      "duration_target_ms": 6000,
      "hard_constraints": {
        "commercial_allowed": true,
        "min_duration_ms": 3000
      },
      "soft_preferences": {
        "orientation": "landscape",
        "min_resolution": "1080p"
      },
      "fallback_requirements": {
        "allow_cutaway": true,
        "allow_texture_b_roll": false
      },
      "evidence_requirements": [
        "show_human_and_robot_interaction",
        "include_valid_time_range"
      ]
    }
  ]
}
```

### 5.6 MaterialAssignment

```json
{
  "schema_version": "1.0",
  "assignment_set_id": "mas_001",
  "project_id": "project_001",
  "shot_plan_id": "shotplan_001",
  "strategy_version": "video_composition_baseline_v1",
  "status": "proposed",
  "assignments": [
    {
      "assignment_id": "ma_001",
      "shot_id": "shot_003",
      "selected_candidate_id": "cand_001",
      "entity_ref": {
        "entity_type": "segment",
        "entity_id": "segment_009",
        "video_id": "video_100",
        "start_ms": 12500,
        "end_ms": 18800
      },
      "trim": {"source_in_ms": 13000, "source_out_ms": 18400},
      "score": 0.89,
      "score_breakdown": {
        "shot_fit": 0.91,
        "collection_fit": 0.84
      },
      "selection_reason": "动作和景别匹配，时长可裁剪，且不与相邻镜头重复",
      "alternatives": [
        {
          "candidate_id": "cand_002",
          "score": 0.86,
          "reason": "景别略宽，可作为更完整的建立镜头"
        }
      ],
      "rights_status": "verified",
      "locked_by_user": false
    }
  ],
  "coverage": {
    "required_shots": 5,
    "covered_shots": 5,
    "missing_shot_ids": []
  }
}
```

### 5.7 EditDecision

```json
{
  "schema_version": "1.0",
  "edit_decision_id": "ed_001",
  "project_id": "project_001",
  "assignment_set_id": "mas_001",
  "timeline_settings": {
    "fps_num": 25,
    "fps_den": 1,
    "width": 1920,
    "height": 1080,
    "audio_sample_rate": 48000
  },
  "clips": [
    {
      "clip_id": "clip_001",
      "shot_id": "shot_001",
      "source_video_id": "video_100",
      "source_segment_id": "segment_001",
      "source_in_ms": 2000,
      "source_out_ms": 7000,
      "sequence_order": 1,
      "duration_target_ms": 5000,
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

`sequence_order`、`duration_target_ms` 和 `position_intent` 是创意意图。绝对 `timeline_start_ms`、最终 `track_id` 和发生裁剪后的实际帧区间由 Timeline Resolver 计算，只写入 TimelineIR。

### 5.8 Timeline IR

```json
{
  "schema_version": "1.0",
  "timeline_id": "tl_001",
  "project_id": "project_001",
  "edit_decision_id": "ed_001",
  "timeline_settings": {
    "fps_num": 25,
    "fps_den": 1,
    "width": 1920,
    "height": 1080,
    "duration_ms": 30000
  },
  "asset_manifest_version": "am_001",
  "tracks": [
    {
      "track_id": "V1",
      "track_type": "video",
      "clips": [
        {
          "timeline_clip_id": "tc_001",
          "asset_id": "asset_100",
          "segment_id": "segment_001",
          "source_in_ms": 2000,
          "source_out_ms": 7000,
          "timeline_start_ms": 0,
          "speed": 1.0
        }
      ]
    }
  ]
}
```

### 5.9 QualityReport

QualityReport Schema 的强制项：

- `evaluation_inputs[]`
- `dimensions{}`
- `hard_gate_failures[]`
- `issues[]`
- `decision: pass|revise|reject|human_review`
- `policy_version`
- `evaluator_version`

`pass` 不能在 `hard_gate_failures` 非空时出现，契约测试必须拒绝。

### 5.9.1 QualityPolicy

```json
{
  "policy_id": "video_standard_v1",
  "policy_version": "1.0",
  "hard_gates": {
    "schema": true,
    "contract_required": true,
    "evidence_required_for_key_shots": true,
    "technical_decodable": true,
    "rights_verified": true
  },
  "dimensions": {
    "contract": {"weight": 0.25, "threshold": 80},
    "evidence": {"weight": 0.20, "threshold": 80},
    "technical": {"weight": 0.15, "threshold": 90},
    "semantic": {"weight": 0.20, "threshold": 75},
    "aesthetic": {"weight": 0.10, "threshold": 70},
    "rights": {"weight": 0.10, "threshold": 100}
  },
  "overall_threshold": 80,
  "max_revisions": 2,
  "retain_best": true,
  "human_review_on": [
    "hard_gate_failure",
    "same_issue_repeated",
    "revision_budget_exhausted"
  ]
}
```

权重之和必须为 1。Quality Policy 由 Registry 发布，任务只引用 `policy_id + version`；硬门由规则引擎执行，不能由加权总分覆盖。

---

## 6. Agent Tool 注册契约

### 6.1 Descriptor

```json
{
  "name": "search_video_materials",
  "version": "1.0",
  "domain": "video",
  "description": "Search authorized video segments using a validated SearchPlan.",
  "input_schema_ref": "urn:video:tool:search-video-materials:input:1.0",
  "output_schema_ref": "urn:video:candidate-set:1.0",
  "side_effect_level": "L0",
  "permission": {
    "scopes": ["video.material.search"],
    "project_scope_required": true,
    "rights_filter_required": true
  },
  "timeout_ms": 8000,
  "retry": {
    "max_attempts": 2,
    "backoff_ms": [200, 800],
    "retry_on": ["dependency_timeout", "rate_limited"]
  },
  "idempotency": {
    "mode": "not_required_for_read"
  },
  "observability": {
    "record_input_summary": true,
    "record_result_ref": true,
    "record_sensitive_payload": false
  }
}
```

### 6.2 Tool 白名单与能力目录

| Tool | Scope | 副作用 | 超时 |
|---|---|---|---|
| `get_project_context` | `video.project.read` | L0 | 2s |
| `search_video_materials` | `video.material.search` | L0 | 8s |
| `recommend_video_materials` | `video.material.recommend` | L0 | 8s |
| `find_similar_materials` | `video.material.similar` | L0 | 5s |
| `explore_video_materials` | `video.material.explore` | L0 | 8s |
| `explain_candidates` | `video.retrieval.explain` | L0 | 5s |
| `create_artifact_draft` | `video.artifact.write` | L1 | 5s |
| `assign_materials` | `video.composition.assign` | L1 | 20s |
| `validate_timeline` | `video.timeline.validate` | L0 | 10s |
| `render_preview` | `video.render.preview` | L2 | 30s enqueue |
| `request_user_confirmation` | `video.task.wait` | L1 | 2s |
| `export_video` | `video.export.create` | L4 | 30s enqueue |

Agent 不拥有高价值反馈写 Tool。采用、替换、最终保留和导出转化由服务端状态迁移确定性发出。

### 6.2.1 Tool 幂等模式

| Tool | 幂等模式 | 幂等键组成 |
|---|---|---|
| Search/Recommend/Similar/Explore/Explain | `read_only` | 不需要；用 `request_id` 关联结果 |
| `get_project_context` / `get_artifact` | `read_only` | 不需要 |
| `create_artifact_draft` | `content_dedup` | `tenant + task + step + artifact_type + content_hash` |
| `assign_materials` | `operation_dedup` | `tenant + task + shot_plan_hash + candidate_set_hashes + strategy_version` |
| `validate_timeline` | `read_only` | 不需要；相同输入可缓存 ValidationReport |
| `request_user_confirmation` | `operation_dedup` | `tenant + task + step + question_hash + scope_hash` |
| `render_preview` | `job_dedup` | `tenant + timeline_hash + profile + purpose` |
| `export_video` | `job_dedup` | `tenant + render_hash + output_profile + usage_context_hash + approval_id` |

`content_dedup` 可以复用内容相同的草稿，但用户确认产生的版本不能去重覆盖。`job_dedup` 必须保存原有 Job 并返回其状态，不能因客户端重试创建第二条计费任务。

### 6.3 Action Schema

模型输出只能采用以下 Action：

```json
{
  "action_type": "tool_call",
  "tool_name": "search_video_materials",
  "arguments": {},
  "reason_summary": "shot_003 needs visual evidence for human-robot collaboration",
  "expected_result": "candidate_set"
}
```

```json
{
  "action_type": "ask_user",
  "question": "需要保留旁白吗？",
  "options": ["保留", "仅背景音乐", "无音频"],
  "required": true
}
```

```json
{
  "action_type": "complete_node",
  "output": {
    "artifact_type": "shot_plan",
    "schema_version": "1.0"
  }
}
```

不允许自由文本 JSON、未知 Tool、超出节点白名单的 Tool 或隐式副作用。

---

## 7. 持久化 Schema

以下为 PostgreSQL 参考 DDL。正式迁移需补充租户索引、分区策略和保留期限。

租户隔离不能只依赖应用层比较：

- 所有查询必须显式带 `tenant_id`，Repository 接口不得提供仅按全局 ID 查询的业务方法。
- 生产实现建议使用行级安全策略，或为父子表增加 `(tenant_id, id)` 复合唯一键与复合外键。
- 下文为便于阅读保留单列外键；若同 ID 可能跨租户生成，必须使用全局不可碰撞 ID，并由数据库约束测试证明跨租户引用不可写入。
- 任何跨租户管理查询只能通过独立、强审计的内部工具完成。

### 7.1 Project

```sql
CREATE TABLE video_project (
  project_id           varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  owner_user_id        varchar(64) NOT NULL,
  name                 varchar(200) NOT NULL,
  status               varchar(32) NOT NULL,
  goal                 text NOT NULL,
  constraints_json     jsonb NOT NULL DEFAULT '{}'::jsonb,
  current_version      integer NOT NULL DEFAULT 1,
  row_version          integer NOT NULL DEFAULT 1,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_video_project_tenant_updated
  ON video_project (tenant_id, updated_at DESC);
```

### 7.2 Task

```sql
CREATE TABLE video_task (
  task_id              varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL REFERENCES video_project(project_id),
  created_by           varchar(64) NOT NULL,
  task_type            varchar(32) NOT NULL,
  status               varchar(32) NOT NULL,
  current_step_id      varchar(80),
  plan_version         integer,
  parent_task_id       varchar(64),
  deadline_at          timestamptz,
  constraints_json     jsonb NOT NULL DEFAULT '{}'::jsonb,
  execution_json       jsonb NOT NULL DEFAULT '{}'::jsonb,
  cancel_reason        varchar(500),
  row_version          integer NOT NULL DEFAULT 1,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_video_task_project_status
  ON video_task (tenant_id, project_id, status, updated_at DESC);
```

### 7.3 Task Status History

```sql
CREATE TABLE video_task_status_history (
  history_id           bigserial PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL REFERENCES video_task(task_id),
  from_status          varchar(32),
  to_status            varchar(32) NOT NULL,
  actor_type           varchar(32) NOT NULL,
  actor_id             varchar(64),
  reason_code          varchar(64),
  related_entity_id    varchar(64),
  created_at           timestamptz NOT NULL DEFAULT now()
);
```

### 7.4 Plan

```sql
CREATE TABLE video_plan (
  plan_id              varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL REFERENCES video_task(task_id),
  version              integer NOT NULL,
  status               varchar(32) NOT NULL,
  plan_json            jsonb NOT NULL,
  acceptance_json      jsonb NOT NULL,
  tool_allowlist_json  jsonb NOT NULL,
  budget_json          jsonb NOT NULL,
  approved_by          varchar(64),
  approved_at          timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, task_id, version)
);
```

### 7.5 Agent Run

```sql
CREATE TABLE video_agent_run (
  run_id               varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL REFERENCES video_task(task_id),
  plan_id              varchar(64) NOT NULL REFERENCES video_plan(plan_id),
  status               varchar(32) NOT NULL,
  current_step_id      varchar(80),
  model_profile        varchar(64) NOT NULL,
  budget_json          jsonb NOT NULL,
  usage_json           jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_code           varchar(64),
  started_at           timestamptz,
  ended_at             timestamptz,
  heartbeat_at         timestamptz,
  row_version          integer NOT NULL DEFAULT 1,
  created_at           timestamptz NOT NULL DEFAULT now()
);
```

### 7.6 Task Step

```sql
CREATE TABLE video_task_step (
  step_id              varchar(80) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL REFERENCES video_task(task_id),
  parent_step_id       varchar(80),
  step_type            varchar(64) NOT NULL,
  step_key             varchar(120) NOT NULL,
  status               varchar(32) NOT NULL,
  attempt              integer NOT NULL DEFAULT 0,
  max_attempts         integer NOT NULL DEFAULT 2,
  idempotency_key      varchar(200) NOT NULL,
  input_refs_json      jsonb NOT NULL DEFAULT '[]'::jsonb,
  output_refs_json     jsonb NOT NULL DEFAULT '[]'::jsonb,
  error_code           varchar(64),
  error_detail_json    jsonb,
  timeout_ms           integer NOT NULL,
  started_at           timestamptz,
  ended_at             timestamptz,
  row_version          integer NOT NULL DEFAULT 1,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, task_id, step_key)
);
```

### 7.6.1 Tool Call Ledger

```sql
CREATE TABLE video_tool_call (
  tool_call_id         varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL,
  run_id               varchar(64) NOT NULL,
  step_id              varchar(80) NOT NULL,
  tool_name            varchar(100) NOT NULL,
  tool_version         varchar(32) NOT NULL,
  input_hash           char(64) NOT NULL,
  idempotency_key      varchar(200) NOT NULL,
  status               varchar(32) NOT NULL,
  attempt              integer NOT NULL DEFAULT 0,
  result_ref           varchar(1000),
  error_code           varchar(64),
  error_detail_json    jsonb,
  started_at           timestamptz,
  ended_at             timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX idx_video_tool_call_step
  ON video_tool_call (tenant_id, task_id, step_id, created_at);
```

同一 ToolCall 重放返回既有结果；只有策略允许且输入 hash 未变化时才可增加 `attempt`。

### 7.6.2 Budget Ledger

```sql
CREATE TABLE video_budget_ledger (
  budget_entry_id      varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL,
  run_id               varchar(64),
  step_id              varchar(80),
  reservation_id       varchar(64),
  resource_type        varchar(32) NOT NULL,
  state                varchar(32) NOT NULL,
  amount               numeric(18,6) NOT NULL,
  currency             varchar(8) NOT NULL DEFAULT 'USD',
  units                numeric(18,6),
  related_ref          varchar(500),
  idempotency_key      varchar(200) NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (amount >= 0),
  UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX idx_video_budget_task
  ON video_budget_ledger (tenant_id, task_id, state, created_at);
```

状态为 `reserved / consumed / released / failed`。调用前先预留，完成后转为实际消耗或释放；预算不足时禁止开始新的模型、工具、渲染或导出调用。

### 7.7 Checkpoint

```sql
CREATE TABLE video_checkpoint (
  checkpoint_id        varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL REFERENCES video_task(task_id),
  run_id               varchar(64) REFERENCES video_agent_run(run_id),
  step_id              varchar(80),
  checkpoint_type      varchar(32) NOT NULL,
  state_ref            varchar(500) NOT NULL,
  state_hash           char(64) NOT NULL,
  remaining_budget_json jsonb NOT NULL,
  resume_token_hash    char(64),
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_video_checkpoint_task_created
  ON video_checkpoint (tenant_id, task_id, created_at DESC);
```

### 7.8 Artifact

```sql
CREATE TABLE video_artifact (
  artifact_id          varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL REFERENCES video_project(project_id),
  task_id              varchar(64) REFERENCES video_task(task_id),
  artifact_type        varchar(64) NOT NULL,
  schema_version       varchar(16) NOT NULL,
  version              integer NOT NULL,
  status               varchar(32) NOT NULL,
  parent_ids_json      jsonb NOT NULL DEFAULT '[]'::jsonb,
  content_uri          varchar(1000) NOT NULL,
  content_hash         char(64) NOT NULL,
  producer_tool        varchar(100),
  producer_version     varchar(64),
  validation_status    varchar(32) NOT NULL,
  permission_scope_json jsonb NOT NULL,
  created_by           varchar(64) NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  staled_at            timestamptz,
  UNIQUE (tenant_id, project_id, artifact_type, version)
);

CREATE INDEX idx_video_artifact_task_type
  ON video_artifact (tenant_id, task_id, artifact_type, created_at DESC);
```

### 7.9 CandidateSet 与 Candidate

```sql
CREATE TABLE video_candidate_set (
  candidate_set_id     varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL,
  task_id              varchar(64),
  shot_id              varchar(64),
  capability           varchar(32) NOT NULL,
  request_id           varchar(64) NOT NULL,
  strategy_version     varchar(64) NOT NULL,
  content_uri          varchar(1000) NOT NULL,
  item_count           integer NOT NULL,
  warnings_json        jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE video_candidate (
  candidate_id         varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  candidate_set_id     varchar(64) NOT NULL REFERENCES video_candidate_set(candidate_set_id),
  entity_type          varchar(32) NOT NULL,
  entity_id            varchar(64) NOT NULL,
  video_id             varchar(64) NOT NULL,
  start_ms             bigint NOT NULL,
  end_ms               bigint NOT NULL,
  rank                 integer NOT NULL,
  score                numeric(10,6) NOT NULL,
  candidate_origin     varchar(32) NOT NULL,
  rights_status        varchar(32) NOT NULL,
  evidence_ref         varchar(500),
  feature_version      varchar(64),
  model_version        varchar(64),
  created_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (start_ms >= 0 AND end_ms > start_ms)
);

CREATE INDEX idx_video_candidate_set_rank
  ON video_candidate (tenant_id, candidate_set_id, rank);
```

### 7.9.1 ShotPlan 与 ShotRequirement

ShotPlan 既保存为 Artifact，也建立关系表用于并行 Step、局部重算、Assignment Join 和用户锁定。

```sql
CREATE TABLE video_shot_plan (
  shot_plan_id         varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL,
  storyboard_id        varchar(64) NOT NULL,
  version              integer NOT NULL,
  status               varchar(32) NOT NULL,
  content_hash         char(64) NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, project_id, storyboard_id, version)
);

CREATE TABLE video_shot_requirement (
  tenant_id            varchar(64) NOT NULL,
  shot_plan_id         varchar(64) NOT NULL REFERENCES video_shot_plan(shot_plan_id),
  shot_id              varchar(64) NOT NULL,
  sequence_order       integer NOT NULL,
  narrative_role       varchar(64),
  visual_goal          text NOT NULL,
  duration_target_ms   bigint NOT NULL,
  hard_constraints_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  soft_preferences_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  fallback_json        jsonb NOT NULL DEFAULT '{}'::jsonb,
  status               varchar(32) NOT NULL,
  row_version          integer NOT NULL DEFAULT 1,
  updated_at           timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, shot_plan_id, shot_id),
  CHECK (sequence_order >= 0 AND duration_target_ms > 0)
);
```

### 7.10 Material Assignment

```sql
CREATE TABLE video_assignment_set (
  assignment_set_id    varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL,
  shot_plan_id         varchar(64) NOT NULL,
  version              integer NOT NULL,
  status               varchar(32) NOT NULL,
  strategy_version     varchar(64) NOT NULL,
  content_uri          varchar(1000) NOT NULL,
  content_hash         char(64) NOT NULL,
  confirmed_by         varchar(64),
  confirmed_at         timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, project_id, shot_plan_id, version)
);

CREATE TABLE video_material_assignment (
  assignment_id        varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  assignment_set_id    varchar(64) NOT NULL REFERENCES video_assignment_set(assignment_set_id),
  shot_id              varchar(64) NOT NULL,
  selected_candidate_id varchar(64) NOT NULL,
  entity_id            varchar(64) NOT NULL,
  source_in_ms         bigint,
  source_out_ms        bigint,
  score                numeric(10,6) NOT NULL,
  rights_status        varchar(32) NOT NULL,
  locked_by_user       boolean NOT NULL DEFAULT false,
  status               varchar(32) NOT NULL
                       CHECK (status IN ('proposed','confirmed','locked','superseded')),
  reason               text,
  created_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (source_in_ms IS NULL OR source_out_ms IS NULL OR source_in_ms < source_out_ms)
);
```

### 7.11 Timeline 与 Render

```sql
CREATE TABLE video_timeline (
  timeline_id          varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL,
  edit_decision_id     varchar(64) NOT NULL,
  version              integer NOT NULL,
  schema_version       varchar(16) NOT NULL,
  content_uri          varchar(1000) NOT NULL,
  content_hash         char(64) NOT NULL,
  validation_status    varchar(32) NOT NULL,
  validation_report_ref varchar(500),
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, project_id, version)
);

CREATE TABLE video_render_job (
  render_job_id        varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL,
  timeline_id          varchar(64) NOT NULL REFERENCES video_timeline(timeline_id),
  idempotency_key      varchar(200) NOT NULL,
  profile              varchar(32) NOT NULL,
  status               varchar(32) NOT NULL,
  progress             integer NOT NULL DEFAULT 0,
  output_uri           varchar(1000),
  output_hash          char(64),
  error_code           varchar(64),
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key),
  CHECK (progress >= 0 AND progress <= 100)
);
```

### 7.11.1 Export Job

```sql
CREATE TABLE video_export_job (
  export_job_id        varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL,
  render_job_id        varchar(64) NOT NULL REFERENCES video_render_job(render_job_id),
  approval_id          varchar(64) NOT NULL,
  idempotency_key      varchar(200) NOT NULL,
  usage_context_json   jsonb NOT NULL,
  output_profile       varchar(64) NOT NULL,
  status               varchar(32) NOT NULL,
  output_uri           varchar(1000),
  output_hash          char(64),
  error_code           varchar(64),
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);
```

Render/Export 恢复时先按 `idempotency_key + input hash` 查询真实 Job，再决定重试或复用，禁止直接提交新 Job。

### 7.12 Quality、Approval 与 Feedback

```sql
CREATE TABLE video_quality_review (
  review_id            varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  project_id           varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL,
  target_artifact_id   varchar(64) NOT NULL,
  round                integer NOT NULL,
  decision             varchar(32) NOT NULL,
  report_uri           varchar(1000) NOT NULL,
  policy_version       varchar(64) NOT NULL,
  evaluator_version    varchar(64) NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE video_approval (
  approval_id          varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL,
  action_type          varchar(64) NOT NULL,
  target_ref           varchar(500) NOT NULL,
  target_hash          char(64),
  execution_hash       char(64) NOT NULL,
  usage_context_json   jsonb NOT NULL DEFAULT '{}'::jsonb,
  status               varchar(32) NOT NULL,
  requested_by         varchar(64) NOT NULL,
  decided_by           varchar(64),
  decision_reason      varchar(500),
  expires_at           timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now(),
  CHECK (status IN ('requested','approved','rejected','expired','revoked'))
);

CREATE TABLE video_feedback_event (
  event_id             varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  event_type           varchar(64) NOT NULL,
  source               varchar(64) NOT NULL,
  occurred_at          timestamptz NOT NULL,
  request_id           varchar(64),
  candidate_set_id     varchar(64),
  project_id           varchar(64),
  task_id              varchar(64),
  shot_id              varchar(64),
  entity_id            varchar(64),
  position             integer,
  strategy_version     varchar(64),
  properties_json      jsonb NOT NULL DEFAULT '{}'::jsonb,
  idempotency_key      varchar(200) NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);
```

### 7.13 Event Outbox

```sql
CREATE TABLE video_agent_event (
  event_id             varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL,
  sequence             bigint NOT NULL,
  event_type           varchar(64) NOT NULL,
  aggregate_type       varchar(64) NOT NULL,
  aggregate_id         varchar(64) NOT NULL,
  actor_type           varchar(32) NOT NULL,
  payload_json         jsonb NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, task_id, sequence)
);

CREATE INDEX idx_video_agent_event_task_sequence
  ON video_agent_event (tenant_id, task_id, sequence);
```

SSE 通过 `Last-Event-ID` 或 `after_sequence` 从该表读取。事件表是交互重放的持久事实；进程内队列和 Kafka 都不能单独承担重放。事件超过保留期或出现不可补齐的 sequence 缺口时，返回 `resync_required` 与最新 Task/Artifact 快照。

```sql
CREATE TABLE video_event_outbox (
  outbox_id            bigserial PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  aggregate_type       varchar(64) NOT NULL,
  aggregate_id         varchar(64) NOT NULL,
  event_type           varchar(64) NOT NULL,
  event_payload_json   jsonb NOT NULL,
  status               varchar(32) NOT NULL DEFAULT 'pending',
  attempt              integer NOT NULL DEFAULT 0,
  available_at         timestamptz NOT NULL DEFAULT now(),
  published_at         timestamptz,
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_video_outbox_pending
  ON video_event_outbox (status, available_at, outbox_id);
```

业务事务只写业务表和 Outbox；异步发布器负责投递事件。禁止先写业务表再“尽力发事件”。

Outbox 采用至少一次投递。消费者必须以 `event_id` 幂等；持久化事件和 SSE 重放不能驱动新的业务副作用。

---

## 8. 状态与幂等实现

### 8.1 乐观锁更新

```sql
UPDATE video_task
SET status = :new_status,
    row_version = row_version + 1,
    updated_at = now()
WHERE task_id = :task_id
  AND tenant_id = :tenant_id
  AND row_version = :expected_version
  AND status = :expected_status;
```

影响行数为 0 时返回 `409 STATE_CONFLICT` 或 `TASK_VERSION_CONFLICT`。

### 8.2 Step 幂等

`idempotency_key = hash(tenant_id, task_id, step_key, input_artifact_hashes, action_version)`。

执行前：

1. `INSERT ... ON CONFLICT` 尝试创建 Step。
2. `succeeded` 直接返回已有输出。
3. `running` 且未超时：返回当前状态，不重复执行。
4. `running` 且租约超时：比较 `attempt`，按策略接管。
5. `failed` 且可重试：增加 attempt 后执行。

### 8.3 对外副作用幂等

- Render/Export 使用独立幂等键，包含 Timeline hash、profile 和授权 ID。
- 反馈事件使用 UI 事件 ID。
- Artifact 写入按 content hash 去重，但用户确认版本必须保留。
- 外部回调先查实际任务状态，再更新本地状态。

---

## 9. 契约版本与兼容性

| 变更 | 兼容策略 |
|---|---|
| 增加可选字段 | Minor 版本，旧消费者可忽略 |
| 增加枚举值 | 消费者必须有 unknown 处理 |
| 修改字段含义 | Major 版本 |
| 删除/重命名字段 | Major 版本 |
| 新增 Tool | 新 descriptor 版本和权限评审 |
| 新增策略 | 注册新 strategy_id，不改历史 Run |
| Prompt/模型修改 | 新 profile/version，重新跑 Eval |

Artifact 读取器必须按 `schema_version` 路由，不得默认用最新 Schema 解析历史 Artifact。

---

## 10. 测试夹具与本地开发

### 10.1 样本素材

至少准备：

- 3 个来源视频，总时长超过 5 分钟。
- 20 个 Shot。
- 5 个 Rights 已验证 Segment。
- 2 个 Rights 受限 Segment。
- 2 个时长短于 2 秒的 Segment。
- 2 个重复画面。
- 1 个缺音轨视频。
- 1 个损坏媒体或探测失败样例。

### 10.2 Fake Adapters

`FakeUrreAdapter`：

- 按 Shot 返回 10 个稳定候选。
- 支持模拟零结果、超时、单通道失败和 Rights 冲突。
- 所有候选 ID 和证据固定。

`FakeRenderAdapter`：

- 生成固定测试媒体或返回可验证的 mock output manifest。
- 支持进度、超时和失败分类。
- 不读取任意宿主路径。

### 10.3 本地验收

最小命令应覆盖：

```bash
make test
make contract-test
make integration-test
make eval-fast
make compose-up
```

正式脚本在 [纵向切片与验收脚本](06_VideoDomainAgent_纵向切片与验收脚本.md) 中定义。

---

## 11. 研发 Ticket 与依赖

### 11.1 P0：契约和基础设施

| ID | Ticket | 交付 | 依赖 | Definition of Done |
|---|---|---|---|---|
| VDA-001 | 建立 Monorepo 与模块边界 | 模块、依赖检查 | 无 | 非法依赖在 CI 失败 |
| VDA-002 | 实现统一可信上下文 | Tenant/User/Project scope | 001 | Header 伪造和跨租户测试通过 |
| VDA-003 | 建立 Error/Idempotency 框架 | 错误码、幂等表/接口 | 001 | 重放不重复副作用 |
| VDA-004 | 建立 Artifact Registry | 版本、对象存储、hash | 001 | 同类型多版本和 lineage 测试通过 |
| VDA-005 | 建立 Project/Task/Run/Step/ToolCall/Budget/Event 表 | 迁移和 Repository | 003,004 | 状态机、乐观锁与账本事务测试通过 |
| VDA-006 | 建立 Checkpoint 与 Resume | 恢复 API、Step 接管 | 005 | 暂停/重启后不重复 Step |
| VDA-007 | 建立 SSE/Event/Outbox | 持久事件、顺序和重连游标 | 003,005 | 断连重放无丢失、无重复业务写入 |
| VDA-008 | 建立 Schema/OpenAPI 生成与校验 | contracts 管线和 CI | 001 | 文档、生成代码和 Schema 一致 |

### 11.2 P1：检索与推荐

| ID | Ticket | 交付 | 依赖 | Definition of Done |
|---|---|---|---|---|
| VDA-009 | Video/Shot/Segment 数据模型 | 数据表与 Schema | 004,008 | 时间区间与层级引用测试通过 |
| VDA-010 | 批量入库与内容加工 | Ingest/Content Worker、IngestionJob | 008,009 | 固定样本可重复生成 Shot 和加工产物；内容/元数据/Rights 版本与幂等键测试通过 |
| VDA-011 | BM25 索引与元数据过滤 | ES Index Writer、Index Manifest | 010 | Active Manifest 为唯一发布指针；单侧失败不发布，Active 指针回滚通过 |
| VDA-012 | Qdrant 文本向量与 RRF | Embedding/Indexing Worker、Hybrid Search | 010,011 | Point 带模型、Rights 与索引版本；仅 Rights 更新不重跑 Embedding |
| VDA-013 | CandidateSet API | SearchResult Contract | 012 | 证据引用、Rights、版本完整；Evidence Resolver 权限测试通过 |
| VDA-014 | 项目上下文推荐 | Recommendation API | 009,013 | Shot/Project context 生效 |
| VDA-015 | Recommendation Strategy Registry | 策略 ID 与校验 | 014 | Agent 无法提供未注册权重 |
| VDA-016 | Feedback + Attribution | 事件与幂等 | 007,013,014 | 采用事件可追溯到请求/候选/位置 |

### 11.3 P2：Agent 与 Workflow

| ID | Ticket | 交付 | 依赖 | Definition of Done |
|---|---|---|---|---|
| VDA-017 | Tool Registry 与 Policy Gateway | 工具调用治理 | 002,008 | 未授权、超预算、非法 Schema 被拒 |
| VDA-018 | Director Tool Loop 与 Runtime 准入 | Action Schema、Runtime SPI、准入 ADR | 017 | Mock 完成多轮工具调用；准入结论明确 |
| VDA-019 | Intent/Complexity Router | fast path 与 Agent 路由 | 018 | 简单 Search/Recommend 不启 Agent |
| VDA-020 | Creation Workflow 骨架 | Brief/Storyboard/ShotPlan 节点 | 018,005 | 固定任务生成三个 Artifact |
| VDA-021 | Search/Recommend Tool 接入 | 两个 Tool adapter | 013,014,018 | 同一 Shot 可合并两类候选 |
| VDA-022 | Shot 并行与局部重算 | 并行 Step 调度 | 020,021 | 一个 Shot 失败不阻塞无关 Shot |
| VDA-023 | WaitingUser 与恢复 | 确认 Checkpoint | 006,020 | 重复确认不重复执行 |
| VDA-024 | 预算、重试和失败分类 | WaitingBudget、预算预留与停机 | 018 | 故障注入符合预期且预算可对账 |

### 11.4 P3：组合、时间线和媒体

| ID | Ticket | 交付 | 依赖 | Definition of Done |
|---|---|---|---|---|
| VDA-025 | Composition 基线 | shortlist 与评分 | 021 | 每个 Shot 生成首选与替代 |
| VDA-026 | 跨 Shot 集合评分 | 覆盖/重复/风格 | 025 | 固定样本结果可重复 |
| VDA-027 | Assignment 用户操作 | 锁定/替换/确认 | 023,025 | 修改产生新版本，旧版本可读 |
| VDA-028 | EditDecision 生成 | Schema 与 serializer | 027 | 不由 LLM 拼接媒体命令 |
| VDA-029 | Timeline IR 与 Validator | 校验和 issue 列表 | 028 | 时间/轨道/Rights 错误被拦截 |
| VDA-030 | CompilePlan 与 FFmpeg Preview | 媒体 Worker | 029 | 输出可探测、可播放 |
| VDA-031 | Media Inspector | 技术质量检测 | 030 | 时长、编码、音轨有事实结果 |
| VDA-032 | 导出审批 | L4 审批与导出 Job | 031 | 无审批无法导出，重复请求幂等 |

### 11.5 P4：质量与产品化

| ID | Ticket | 交付 | 依赖 | Definition of Done |
|---|---|---|---|---|
| VDA-033 | Quality Gate 规则 | Contract/Evidence/Technical | 029,031 | 硬失败不能 pass |
| VDA-034 | 独立 Quality Reviewer | 模型/人工审核接口 | 033 | 不读取生产者自述作为唯一依据 |
| VDA-035 | 有限修订 Workflow | repair scope、最佳版本 | 034 | 两次后停止并转人工 |
| VDA-036 | 可观测性和成本账本 | Trace、metrics、cost | 018,030 | 能按任务拆解模型/工具/渲染成本 |
| VDA-037 | Eval 固定集与回归 | 检索/推荐/Agent/成片 | P1—P4 | 每次策略或 Prompt 变更自动跑 |
| VDA-038 | 工作台最小页面 | 对话、候选、时间线、审核 | P1—P3 | 用户可完成纵向切片 |
| VDA-039 | 故障演练 | 超时、断连、恢复、权限 | P0—P4 | 故障场景脚本全部通过 |
| VDA-040 | Runbook 与交付评审 | 启停、回滚、排障 | 全部 | 新工程师按文档可独立运行 |

---

## 12. 建议 Sprint 切分

| Sprint | 目标 | 主要 Ticket | 演示 |
|---|---|---|---|
| S1 | 契约、DB、可信上下文 | VDA-001—008 | 创建项目/任务，暂停恢复 |
| S2 | Search MVP | VDA-009—013 | 自然语言搜到镜头并返回证据 |
| S3 | Recommendation + Feedback | VDA-014—016 | 项目上下文推荐，采用事件回流 |
| S4 | Director + Creation | VDA-017—024 | Brief → Storyboard → ShotPlan |
| S5 | Composition + Timeline | VDA-025—031 | 素材组合、时间线校验与预览 |
| S6 | Quality + Product Slice | VDA-032—040 | 完整 30 秒短片、审核和审计 |

S2 和 S3 可与 S1 后半段并行；Timeline Mock 开发可从 S2 开始，但真实集成必须等待 Assignment 契约稳定。

---

## 13. Definition of Ready

一个 Ticket 进入开发前必须满足：

- 输入输出契约明确。
- 状态迁移和失败路径明确。
- 租户、权限、Rights 和副作用等级明确。
- 幂等与恢复方式明确。
- 依赖 Ticket 已完成或有稳定 Mock。
- 有至少一个成功用例和三个失败用例。
- 验收指标可自动或人工验证。

---

## 14. Definition of Done

每个 Ticket 完成必须：

- 代码通过格式、静态检查、单元和契约测试。
- 新 Schema 有兼容性检查和示例。
- 新 Tool 有 Policy Gateway 测试。
- 新状态迁移有非法迁移测试。
- 新外部调用有超时、重试、熔断和 trace。
- 新事件有 event catalog 和关联键。
- 不新增跨租户、裸路径或任意命令执行能力。
- 更新相关 Runbook 和验收脚本。
- 涉及策略、Prompt、模型、索引的变更跑固定 Eval。

### 14.1 PR 硬门禁

- 构建失败禁止合并。
- Schema 破坏性变更无新版本禁止合并。
- 无权限测试禁止合并。
- 无 Idempotency 的写操作禁止合并。
- Agent 直连索引或数据库禁止合并。
- LLM 生成 Shell/FFmpeg 参数禁止合并。
- 无证据候选进入交付路径禁止合并。
- Rights 硬失败允许交付禁止合并。

---

## 15. 团队分工与接口冻结

| 团队 | 负责 | 必须共同冻结 |
|---|---|---|
| Agent 平台 | Runtime、Workflow、Tool Registry、Policy | AgentAction、Tool Envelope、Task/Checkpoint |
| 视频领域 | Director、Composition、Creative IR | ShotPlan、Assignment、Artifact |
| 检索推荐 | Search、Recommend、Ranking、Feedback | SearchPlan、CandidateSet、Feedback |
| 媒体工程 | Timeline、Compiler、Worker、Inspector | TimelineIR、RenderJob、MediaReport |
| QA/安全 | Quality Gate、权限、Rights、Eval | QualityReport、Policy codes、Eval set |

每个接口由唯一 Owner 维护，但消费者必须参与契约评审。契约先合并，再并行实现。

---

## 16. 交付物清单

进入纵向切片验收前，仓库至少包含：

- 可启动的本地 Compose 环境。
- 数据库迁移和回滚脚本。
- OpenAPI 与 JSON Schema。
- Fake URRE/Render Adapter。
- 固定样本项目与素材。
- Director/Workflow 配置。
- E2E 验收脚本。
- Trace Dashboard 或结构化日志查询示例。
- 权限、Rights、幂等和故障恢复测试。
- 运行、暂停、恢复、取消和审计 Runbook。
