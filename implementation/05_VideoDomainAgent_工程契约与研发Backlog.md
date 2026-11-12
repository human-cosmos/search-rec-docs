# Video Domain Agent 工程契约与研发 Backlog

> **状态：** Mock-first 工程基线，2026-11-12。
> **范围：** 只交付通用 Video Domain Agent。
> **模型：** `Video -> Clip`，计划侧使用 `ClipPlan / ClipRequirement`。
> **依据：** [交付范围与模型基线](00_交付范围与VideoClip模型.md)、[详细设计](04_VideoDomainAgent_详细设计与实施手册.md)。

## 1. 工程目标

本契约回答：

1. 代码模块和依赖方向。
2. Video、Clip、CandidateSet、ClipPlan、Assignment 和 Agent 执行的数据合同。
3. Mock 检索推荐与未来真实 Adapter 的共同 Port。
4. Task/Artifact/Tool/Recovery 的持久化结构。
5. 本次交付的 Ticket、完成标准和验收证据。

## 2. 交付边界

### 2.1 必须实现

- Video Domain Agent 与 Runtime SDK Adapter。
- Project、Task、Plan、Step、Checkpoint、Artifact。
- Video/Clip 数据模型。
- Search、Recommendation、Similar、Evidence Mock。
- Storyboard、ClipPlan、ClipRequirement、MaterialAssignment。
- Tool Registry、Policy Gateway、幂等和审计。
- Agent Eval 与 Mock 端到端验收。

### 2.2 不实现

- 真实 Ingest、Embedding、ES/Qdrant、Kafka 搜索链路。
- 推荐训练、真实 Ranker 和线上实验。
- Timeline、Render、Export、NLE、视频生成和媒体处理。
- 视频版权、许可、商业用途、地域可用性和署名过滤。
- 前端工作台、商品、广告、投放、跟品和跨领域业务。
- 个人资产、公共素材库和保护期。

## 3. Monorepo 与模块

```text
video-domain-agent/
├── contracts/
│   ├── openapi/video-api.yaml
│   ├── openapi/retrieval-api.yaml
│   ├── schemas/
│   │   ├── video.v1.schema.json
│   │   ├── clip.v1.schema.json
│   │   ├── task-brief.v1.schema.json
│   │   ├── creative-brief.v1.schema.json
│   │   ├── storyboard.v1.schema.json
│   │   ├── clip-plan.v1.schema.json
│   │   ├── search-plan.v1.schema.json
│   │   ├── candidate-set.v1.schema.json
│   │   ├── material-assignment.v1.schema.json
│   │   └── agent-event.v1.schema.json
│   └── tools/video-tools.v1.yaml
├── app/
│   ├── application-api/
│   ├── application-service/
│   ├── security/
│   └── bootstrap/
├── agent-runtime/
│   ├── runtime-sdk-adapter/
│   ├── local-tool-coordinator/
│   ├── stream-coordinator/
│   ├── workflow-engine/
│   ├── policy-gateway/
│   └── tool-registry/
├── video-domain/
│   ├── video-domain-core/
│   ├── video-agent/
│   ├── video-agent-tools/
│   ├── video-workflows/
│   ├── video-composition/
│   └── video-adapters/
├── mocks/
│   ├── fixture-catalog/
│   ├── fake-retrieval/
│   ├── fake-recommendation/
│   └── fake-evidence/
├── test-support/
└── docs/
```

### 3.1 依赖

```text
application-api
  → application-service
  → video-workflows
  → video-agent
  → video-domain-core
  → contracts

video-agent
  → runtime-sdk-adapter
  → video-agent-tools
  → contracts

video-agent-tools
  → retrieval-client
  → project-client
  → contracts

mocks
  → contracts
  → retrieval-client
```

禁止：

- `video-domain-core` 依赖 SDK 或 Mock。
- Mock Adapter 直接调用 Agent 或写项目数据库。
- Agent 直接连接数据库、Fixture 或文件系统。
- Retrieval 反向依赖视频 Workflow。

## 4. 配置基线

```yaml
app:
  api_prefix: /api/v1
  sse_heartbeat_seconds: 15
runtime:
  sdk_version: 0.2.0
  max_turns: 12
  timeout_seconds: 900
workflow:
  max_tool_calls: 40
  max_replans: 1
  max_tool_error_streak: 2
retrieval:
  adapter: mock
  candidate_budget: 100
  result_limit: 20
  agent_view_limit_per_clip: 10
  max_sub_queries: 5
composition:
  shortlist_per_clip: 10
  max_alternatives_per_clip: 3
mock:
  fixture_version: video-clip-v1
  timeout_query: "mock-timeout"
  empty_query: "mock-empty"
```

`adapter` 只允许在启动配置中切换，Agent 和领域代码不得感知具体实现。

## 5. 通用 API

### 5.1 Header

```http
Authorization: Bearer <token>
X-Tenant-Id: <trusted-gateway-injected>
X-Request-Id: <request-id>
Idempotency-Key: <required-for-mutation>
Traceparent: <w3c-trace-context>
```

服务端不信任客户端自报 `user_id`、租户和项目范围。

### 5.2 Project 与 Task

```http
POST /api/v1/video/projects
GET  /api/v1/video/projects/{projectId}
PATCH /api/v1/video/projects/{projectId}
POST /api/v1/video/projects/{projectId}/tasks
GET  /api/v1/video/tasks/{taskId}
GET  /api/v1/video/tasks/{taskId}/stream
POST /api/v1/video/tasks/{taskId}/wait
POST /api/v1/video/tasks/{taskId}/resume
POST /api/v1/video/tasks/{taskId}/cancel
```

创建任务：

```json
{
  "goal": "为智能机器人项目整理一组 30 秒宣传片素材",
  "mode": "creation",
  "constraints": {
    "duration_ms": 30000,
    "aspect_ratio": "16:9",
    "language": "zh-CN"
  },
  "execution": {
    "require_material_confirmation": true
  }
}
```

响应：

```json
{
  "task_id": "task_001",
  "status": "Created",
  "stream_url": "/api/v1/video/tasks/task_001/stream",
  "resource_version": "1"
}
```

### 5.3 Artifact

```http
GET  /api/v1/video/artifacts/{artifactId}
GET  /api/v1/video/artifacts/{artifactId}/versions
POST /api/v1/video/artifacts/{artifactId}/approve
```

Artifact 下载必须校验用户、租户和项目权限。

### 5.4 Assignment

```http
POST  /api/v1/video/compositions/assign
GET   /api/v1/video/assignments/{assignmentSetId}
PATCH /api/v1/video/assignments/{assignmentSetId}
POST  /api/v1/video/assignments/{assignmentSetId}/confirm
```

### 5.5 Agent Run

```http
GET /api/v1/video/agent-runs/{runId}
GET /api/v1/video/agent-runs/{runId}/events?after_sequence=120
```

响应同时返回领域 `run_id` 和 Runtime `runtime_run_id`。

## 6. Retrieval API

### 6.1 Search

```http
POST /api/v1/retrieval/search
```

```json
{
  "domain": "video",
  "query": "工程师与机械臂协作装配",
  "target_levels": ["video", "clip"],
  "filters": {
    "duration_ms": {"gte": 2000, "lte": 10000}
  },
  "recall": {
    "channels": ["keyword", "semantic", "metadata"],
    "candidate_budget": 100
  },
  "ranking": {
    "strategy_id": "video_mock_hybrid_v1",
    "limit": 20
  },
  "page": {
    "size": 20,
    "cursor": null
  }
}
```

### 6.2 Recommendation

```http
POST /api/v1/retrieval/recommend
```

```json
{
  "domain": "video",
  "scene": "clip_candidate",
  "context": {
    "project_id": "project_001",
    "task_id": "task_001",
    "clip_plan_id": "clipplan_001",
    "storyboard_clip_id": "sb_clip_003",
    "clip_requirement": {
      "visual_goal": "人机协作完成精密装配",
      "duration_target_ms": 5000,
      "clip_type": "close_up"
    },
    "covered_clip_ids": ["sb_clip_001", "sb_clip_002"],
    "selected": [
      {
        "storyboard_clip_id": "sb_clip_001",
        "entity_type": "clip",
        "video_id": "video_001",
        "clip_id": "clip_001"
      }
    ],
    "excluded_clip_ids": ["clip_005"]
  },
  "strategy": {
    "strategy_id": "video_mock_clip_fit_v1",
    "objective": "task_fit_then_diversity"
  },
  "limit": 20
}
```

### 6.3 Similar

```http
POST /api/v1/retrieval/similar
```

```json
{
  "seed": {
    "entity_type": "clip",
    "video_id": "video_001",
    "clip_id": "clip_002"
  },
  "similarity_targets": ["semantic", "visual"],
  "filters": {},
  "limit": 20
}
```

### 6.4 Evidence

```http
POST /api/v1/evidence/resolve
```

请求只接受 `evidence_refs`，不接受宿主路径或长期对象地址。

### 6.5 Feedback

```http
POST /api/v1/retrieval/feedback
```

允许事件：

- `recommendation.impression`
- `recommendation.clicked`
- `material.rejected`
- `material.assigned`
- `material.replaced`
- `material.final_kept`

Agent 不拥有写最终采用反馈的 Tool。

`preview.started/completed` 只保留为未来 UI 遥测，不属于本次必交事件。

## 7. Core Port

```java
public interface VideoCatalogPort {
    VideoPage listVideos(TenantContext context, VideoQuery query);
    Optional<Video> getVideo(TenantContext context, String videoId);
    ClipPage listClips(TenantContext context, ClipQuery query);
    Optional<Clip> getClip(TenantContext context, String clipId);
}

public interface RetrievalGateway {
    CandidateSet search(TenantContext context, SearchRequest request);
    CandidateSet recommend(TenantContext context, RecommendationRequest request);
    CandidateSet similar(TenantContext context, SimilarRequest request);
}

public interface EvidenceGateway {
    EvidenceViewSet resolve(TenantContext context, EvidenceRequest request);
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
        ClipPlanRef clipPlan,
        List<CandidateSetRef> candidateSets,
        CompositionPolicy policy
    );
}

public interface AgentRuntimePort {
    RuntimeRunRef start(
        TenantContext context,
        AgentExecutionRequest request,
        PlatformLocalToolset toolset
    );

    RuntimeRunSnapshot getRun(TenantContext context, String runtimeRunId);
    RuntimeEventStream attach(
        TenantContext context,
        String runtimeRunId,
        String lastEventId
    );
    List<ActionRequestRef> listOpenActions(
        TenantContext context,
        String runtimeRunId
    );
    void decideAction(
        TenantContext context,
        String runtimeRunId,
        String actionRequestId,
        PlatformActionDecision decision
    );
}
```

### 7.1 Adapter

| Port | 本次 Adapter | 未来 Adapter |
|---|---|---|
| VideoCatalogPort | `FakeVideoCatalogPort` | Video service |
| RetrievalGateway | `FakeRetrievalGateway` | URRE HTTP/gRPC |
| EvidenceGateway | `FakeEvidenceGateway` | Evidence Resolver |
| ProjectArtifactStore | PostgreSQL | unchanged |
| CompositionEngine | deterministic rules | learned composition |
| AgentRuntimePort | SDK + Fake Runtime | target Runtime |

所有 Adapter 运行同一 Port Contract Test。

## 8. Schema

### 8.1 Video

```json
{
  "schema_version": "1.0",
  "video_id": "video_001",
  "title": "未来工厂",
  "source_type": "library",
  "duration_ms": 42000,
  "width": 1920,
  "height": 1080,
  "fps": 25,
  "preview_ref": "preview/video_001",
  "availability": "available",
  "tags": ["factory", "technology"],
  "feature_version": "fixture-v1"
}
```

### 8.2 Clip

```json
{
  "schema_version": "1.0",
  "clip_id": "clip_001",
  "video_id": "video_001",
  "start_ms": 2000,
  "end_ms": 8000,
  "duration_ms": 6000,
  "preview_ref": "preview/clip_001",
  "keyframe_ref": "keyframe/clip_001",
  "semantic_summary": "工程师与机械臂协作完成装配",
  "tags": ["human_robot_collaboration", "assembly"],
  "quality_flags": [],
  "availability": "available",
  "feature_version": "fixture-v1",
  "model_versions": ["fixture-v1"]
}
```

### 8.3 SearchPlan

```json
{
  "$schema": "urn:video:search-plan:v1",
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
      "items": {"enum": ["video", "clip"]},
      "minItems": 1,
      "maxItems": 2
    },
    "semantic_query": {"type": "string", "minLength": 1, "maxLength": 500},
    "sub_queries": {"type": "array", "maxItems": 5},
    "hard_filters": {"type": "object"},
    "soft_preferences": {"type": "object"},
    "recall_channels": {
      "type": "array",
      "items": {"enum": ["keyword", "semantic", "metadata"]},
      "maxItems": 3
    },
    "candidate_budget": {"type": "integer", "minimum": 20, "maximum": 200},
    "max_latency_ms": {"type": "integer", "minimum": 500, "maximum": 15000}
  },
  "additionalProperties": false
}
```

### 8.4 CandidateSet

```json
{
  "schema_version": "1.0",
  "candidate_set_id": "cs_001",
  "request_id": "req_001",
  "capability": "search",
  "handled_by": "agent",
  "project_id": "project_001",
  "task_id": "task_001",
  "storyboard_clip_id": "sb_clip_003",
  "strategy_version": "video_mock_hybrid_v1",
  "items": [
    {
      "candidate_id": "cand_001",
      "entity_type": "clip",
      "entity_id": "clip_009",
      "video_id": "video_002",
      "clip_id": "clip_009",
      "start_ms": 12500,
      "end_ms": 18800,
      "rank": 1,
      "score": 0.923,
      "score_breakdown": {
        "keyword": 0.84,
        "semantic": 0.94,
        "metadata": 0.90
      },
      "candidate_origin": "search",
      "recall_channels": ["keyword", "semantic"],
      "evidence": {
        "summary": "工程师与机械臂协作装配",
        "evidence_refs": ["evidence/clip_009/frame_001"]
      },
      "availability": "available",
      "versions": {
        "feature_version": "fixture-v1",
        "model_versions": ["fixture-v1"]
      }
    }
  ],
  "page": {"next_cursor": null, "has_more": false},
  "warnings": []
}
```

### 8.5 Storyboard

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
      "clip_requirements": [
        {
          "storyboard_clip_id": "sb_clip_001",
          "narrative_role": "establishing",
          "visual_goal": "未来工厂全景",
          "duration_target_ms": 5000
        }
      ]
    }
  ]
}
```

### 8.6 ClipPlan

```json
{
  "schema_version": "1.0",
  "clip_plan_id": "clipplan_001",
  "storyboard_id": "sb_001",
  "storyboard_version": 1,
  "clips": [
    {
      "storyboard_clip_id": "sb_clip_003",
      "narrative_role": "proof",
      "visual_goal": "工程师与机械臂协作完成精密装配",
      "subject": ["engineer", "industrial_robot_arm"],
      "action": ["collaborative_assembly"],
      "scene": ["modern_factory"],
      "clip_type": "medium_close_up",
      "camera_motion": "slow_push_in",
      "mood": ["confident", "precise"],
      "duration_target_ms": 6000,
      "hard_constraints": {},
      "soft_preferences": {"orientation": "landscape"},
      "fallback_requirements": {"allow_cutaway": true},
      "evidence_requirements": ["human_robot_collaboration"]
    }
  ]
}
```

### 8.7 MaterialAssignment

```json
{
  "schema_version": "1.0",
  "assignment_id": "ma_001",
  "project_id": "project_001",
  "clip_plan_id": "clipplan_001",
  "storyboard_clip_id": "sb_clip_003",
  "entity_ref": {
    "entity_type": "clip",
    "video_id": "video_002",
    "clip_id": "clip_009"
  },
  "match_evidence": {
    "summary": "人机协作装配，近景，时长满足要求",
    "evidence_refs": ["evidence/clip_009/frame_001"]
  },
  "alternatives": [
    {
      "entity_type": "clip",
      "video_id": "video_003",
      "clip_id": "clip_015"
    }
  ],
  "selection_reason": "主体、动作和时长均满足目标",
  "user_confirmed": false,
  "scores": {
    "semantic_fit": 0.91,
    "visual_fit": 0.88,
    "evidence_confidence": 0.90,
    "technical_quality": 0.93,
    "duration_fit": 0.89,
    "freshness": 0.80,
    "storyboard_coverage": 0.92,
    "style_consistency": 0.86,
    "low_redundancy": 0.84,
    "temporal_rhythm_fit": 0.88,
    "clip_fit": 0.91,
    "collection_fit": 0.88,
    "task_fit": 0.90
  },
  "status": "proposed"
}
```

## 9. Tool 契约

### 9.1 Descriptor

```json
{
  "name": "search_video_materials",
  "version": "1.0",
  "description": "Search Video and Clip entities using a validated SearchPlan.",
  "input_schema_ref": "urn:video:tool:search-video-materials:input:1.0",
  "output_schema_ref": "urn:video:candidate-set:1.0",
  "side_effect_level": "L0",
  "runtime_binding": {
    "kind": "local_tool",
    "local_handler_name": "search_video_materials",
    "available_in_stream": true
  },
  "permission": {
    "scopes": ["video.material.search"],
    "project_scope_required": true
  },
  "timeout_ms": 8000,
  "idempotency": {"mode": "not_required_for_read"}
}
```

### 9.2 白名单

| Tool | Scope | 副作用 |
|---|---|---|
| `get_project_context` | `video.project.read` | L0 |
| `search_video_materials` | `video.material.search` | L0 |
| `recommend_video_materials` | `video.material.recommend` | L0 |
| `find_similar_materials` | `video.material.similar` | L0 |
| `resolve_evidence` | `video.evidence.read` | L0 |
| `create_artifact_draft` | `video.artifact.write` | L1 |
| `assign_materials` | `video.composition.assign` | L1 |
| `request_user_confirmation` | `video.task.wait` | L1 |

### 9.3 幂等

| Tool | 模式 | 键 |
|---|---|---|
| Search/Recommend/Similar | read-only | `request_id` 关联 |
| `create_artifact_draft` | content dedup | tenant + task + step + type + content hash |
| `assign_materials` | operation dedup | tenant + task + clip_plan hash + candidate hashes + strategy |
| `request_user_confirmation` | operation dedup | tenant + task + step + question hash + scope hash |

## 10. 数据库

### 10.1 Project

```sql
CREATE TABLE video_project (
  project_id      varchar(64) PRIMARY KEY,
  tenant_id       varchar(64) NOT NULL,
  owner_user_id   varchar(64) NOT NULL,
  name            varchar(200) NOT NULL,
  status          varchar(32) NOT NULL,
  goal            text NOT NULL,
  constraints_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  row_version     integer NOT NULL DEFAULT 1,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
```

### 10.2 Task

```sql
CREATE TABLE video_task (
  task_id         varchar(64) PRIMARY KEY,
  tenant_id       varchar(64) NOT NULL,
  project_id      varchar(64) NOT NULL REFERENCES video_project(project_id),
  created_by      varchar(64) NOT NULL,
  task_type       varchar(32) NOT NULL,
  status          varchar(32) NOT NULL,
  waiting_reason  varchar(32)
                  CHECK (waiting_reason IS NULL OR waiting_reason IN
                    ('awaiting_user','budget_exhausted')),
  current_step_id varchar(80),
  deadline_at     timestamptz,
  constraints_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  row_version     integer NOT NULL DEFAULT 1,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CHECK ((status = 'Waiting' AND waiting_reason IS NOT NULL)
      OR (status <> 'Waiting' AND waiting_reason IS NULL))
);
```

允许状态：`Created`、`Planned`、`AwaitingApproval`、`Running`、`Waiting`、`Reviewing`、`Completed`、`Failed`、`Cancelled`。

### 10.3 Step

```sql
CREATE TABLE video_task_step (
  step_id          varchar(80) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  task_id          varchar(64) NOT NULL REFERENCES video_task(task_id),
  step_type        varchar(64) NOT NULL,
  step_key         varchar(120) NOT NULL,
  status           varchar(32) NOT NULL,
  attempt          integer NOT NULL DEFAULT 0,
  max_attempts     integer NOT NULL DEFAULT 2,
  idempotency_key  varchar(200) NOT NULL,
  input_refs_json  jsonb NOT NULL DEFAULT '[]'::jsonb,
  output_refs_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  timeout_ms       integer NOT NULL,
  budget_json      jsonb NOT NULL DEFAULT '{}'::jsonb,
  row_version      integer NOT NULL DEFAULT 1,
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, task_id, step_key)
);
```

### 10.4 Runtime Run Projection

```sql
CREATE TABLE video_agent_run (
  run_id                varchar(64) PRIMARY KEY,
  tenant_id             varchar(64) NOT NULL,
  task_id               varchar(64) NOT NULL REFERENCES video_task(task_id),
  step_id               varchar(80) NOT NULL REFERENCES video_task_step(step_id),
  request_id            varchar(128) NOT NULL,
  session_id            varchar(128),
  runtime_run_id        varchar(128),
  agent_id              varchar(128) NOT NULL,
  spec_version          varchar(64) NOT NULL,
  runtime_status        varchar(32),
  status                varchar(32) NOT NULL,
  current_action_request_id varchar(128),
  runtime_last_event_id varchar(512),
  usage_json            jsonb NOT NULL DEFAULT '{}'::jsonb,
  budget_json           jsonb NOT NULL DEFAULT '{}'::jsonb,
  row_version           integer NOT NULL DEFAULT 1,
  created_at            timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, request_id),
  UNIQUE (tenant_id, runtime_run_id)
);
```

### 10.5 Artifact

```sql
CREATE TABLE video_artifact (
  artifact_id      varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  project_id       varchar(64) NOT NULL,
  task_id          varchar(64),
  artifact_type    varchar(64) NOT NULL,
  schema_version   varchar(16) NOT NULL,
  version          integer NOT NULL,
  status           varchar(32) NOT NULL,
  parent_ids_json  jsonb NOT NULL DEFAULT '[]'::jsonb,
  content_uri      varchar(1000),
  content_json     jsonb,
  content_hash     char(64) NOT NULL,
  producer_run_id  varchar(64),
  producer_tool    varchar(100),
  validation_status varchar(32) NOT NULL,
  created_by       varchar(64) NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  staled_at        timestamptz,
  CHECK (content_uri IS NOT NULL OR content_json IS NOT NULL),
  UNIQUE (tenant_id, project_id, artifact_type, version)
);
```

### 10.6 Video 与 Clip

```sql
CREATE TABLE video_asset (
  video_id         varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  title            varchar(500) NOT NULL,
  source_type      varchar(32) NOT NULL,
  duration_ms      bigint NOT NULL CHECK (duration_ms > 0),
  width            integer,
  height           integer,
  fps              numeric(10,3),
  preview_ref      varchar(500),
  availability     varchar(32) NOT NULL,
  tags_json        jsonb NOT NULL DEFAULT '[]'::jsonb,
  feature_version  varchar(64),
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE video_clip (
  clip_id          varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  video_id         varchar(64) NOT NULL REFERENCES video_asset(video_id),
  start_ms         bigint NOT NULL,
  end_ms           bigint NOT NULL,
  preview_ref      varchar(500),
  keyframe_ref     varchar(500),
  semantic_summary text,
  tags_json        jsonb NOT NULL DEFAULT '[]'::jsonb,
  quality_flags_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  availability     varchar(32) NOT NULL,
  feature_version  varchar(64),
  model_versions_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at       timestamptz NOT NULL DEFAULT now(),
  CHECK (start_ms >= 0 AND end_ms > start_ms)
);

CREATE INDEX idx_video_clip_video_time
  ON video_clip (tenant_id, video_id, start_ms);
```

Clip 的结束时间不能超过 Video 时长，该约束由应用服务和集成测试共同校验。

### 10.7 CandidateSet 与 Candidate

```sql
CREATE TABLE video_candidate_set (
  candidate_set_id varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  project_id       varchar(64),
  task_id          varchar(64),
  storyboard_clip_id varchar(64),
  capability       varchar(32) NOT NULL,
  handled_by       varchar(16) NOT NULL
                   CHECK (handled_by IN ('fast_path','agent')),
  request_id       varchar(64) NOT NULL,
  strategy_version varchar(64) NOT NULL,
  content_uri      varchar(1000),
  content_json     jsonb,
  item_count       integer NOT NULL,
  warnings_json    jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at       timestamptz NOT NULL DEFAULT now(),
  CHECK (content_uri IS NOT NULL OR content_json IS NOT NULL)
);

CREATE TABLE video_candidate (
  candidate_id     varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  candidate_set_id varchar(64) NOT NULL REFERENCES video_candidate_set(candidate_set_id),
  entity_type      varchar(16) NOT NULL CHECK (entity_type IN ('video','clip')),
  entity_id        varchar(64) NOT NULL,
  video_id         varchar(64) NOT NULL,
  clip_id          varchar(64),
  start_ms         bigint,
  end_ms           bigint,
  rank             integer NOT NULL,
  score            numeric(10,6) NOT NULL,
  candidate_origin varchar(32) NOT NULL,
  recall_channels_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_json    jsonb NOT NULL DEFAULT '{}'::jsonb,
  feature_version  varchar(64),
  model_version    varchar(64),
  created_at       timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (entity_type = 'video'
      AND entity_id = video_id
      AND clip_id IS NULL
      AND start_ms IS NULL
      AND end_ms IS NULL)
    OR
    (entity_type = 'clip'
      AND entity_id = clip_id
      AND clip_id IS NOT NULL
      AND start_ms >= 0
      AND end_ms > start_ms)
  )
);
```

### 10.8 ClipPlan 与 Assignment

```sql
CREATE TABLE video_clip_plan (
  clip_plan_id     varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  project_id       varchar(64) NOT NULL,
  storyboard_id    varchar(64) NOT NULL,
  version          integer NOT NULL,
  status           varchar(32) NOT NULL,
  content_hash     char(64) NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, project_id, storyboard_id, version)
);

CREATE TABLE video_clip_requirement (
  tenant_id        varchar(64) NOT NULL,
  clip_plan_id     varchar(64) NOT NULL REFERENCES video_clip_plan(clip_plan_id),
  storyboard_clip_id varchar(64) NOT NULL,
  sequence_order   integer NOT NULL,
  narrative_role   varchar(64),
  visual_goal      text NOT NULL,
  subject_json     jsonb NOT NULL DEFAULT '[]'::jsonb,
  action_json      jsonb NOT NULL DEFAULT '[]'::jsonb,
  scene_json       jsonb NOT NULL DEFAULT '[]'::jsonb,
  clip_type        varchar(64),
  camera_motion    varchar(64),
  mood_json        jsonb NOT NULL DEFAULT '[]'::jsonb,
  duration_target_ms bigint NOT NULL,
  hard_constraints_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  soft_preferences_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  fallback_json    jsonb NOT NULL DEFAULT '{}'::jsonb,
  evidence_requirements_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  content_json     jsonb NOT NULL,
  content_hash     char(64) NOT NULL,
  status           varchar(32) NOT NULL,
  row_version      integer NOT NULL DEFAULT 1,
  PRIMARY KEY (tenant_id, clip_plan_id, storyboard_clip_id)
);

CREATE TABLE video_assignment_set (
  assignment_set_id varchar(64) PRIMARY KEY,
  tenant_id         varchar(64) NOT NULL,
  project_id        varchar(64) NOT NULL,
  clip_plan_id      varchar(64) NOT NULL REFERENCES video_clip_plan(clip_plan_id),
  version           integer NOT NULL,
  status            varchar(32) NOT NULL,
  strategy_version  varchar(64) NOT NULL,
  content_uri       varchar(1000),
  content_json      jsonb,
  content_hash      char(64) NOT NULL,
  confirmed_by      varchar(64),
  confirmed_at      timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CHECK (content_uri IS NOT NULL OR content_json IS NOT NULL),
  UNIQUE (tenant_id, project_id, clip_plan_id, version)
);

CREATE TABLE video_material_assignment (
  assignment_id     varchar(64) PRIMARY KEY,
  tenant_id         varchar(64) NOT NULL,
  assignment_set_id varchar(64) NOT NULL REFERENCES video_assignment_set(assignment_set_id),
  storyboard_clip_id varchar(64) NOT NULL,
  entity_type       varchar(16) NOT NULL CHECK (entity_type IN ('video','clip')),
  video_id          varchar(64) NOT NULL,
  clip_id           varchar(64),
  score             numeric(10,6) NOT NULL,
  user_confirmed    boolean NOT NULL DEFAULT false,
  status            varchar(32) NOT NULL
                    CHECK (status IN ('proposed','confirmed','locked','superseded')),
  reason            text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (entity_type = 'video' AND clip_id IS NULL)
    OR
    (entity_type = 'clip' AND clip_id IS NOT NULL)
  )
);
```

### 10.9 Tool、Budget、Checkpoint、Event

```sql
CREATE TABLE video_tool_call (
  tool_call_id     varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  task_id          varchar(64) NOT NULL,
  run_id           varchar(64) NOT NULL,
  step_id          varchar(80) NOT NULL,
  tool_name        varchar(100) NOT NULL,
  input_hash       char(64) NOT NULL,
  idempotency_key  varchar(200) NOT NULL,
  status           varchar(32) NOT NULL,
  attempt          integer NOT NULL DEFAULT 0,
  result_ref       varchar(1000),
  error_code       varchar(64),
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE video_budget_ledger (
  budget_entry_id  varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  task_id          varchar(64) NOT NULL,
  resource_type    varchar(32) NOT NULL,
  state            varchar(32) NOT NULL,
  amount           numeric(18,6) NOT NULL,
  idempotency_key  varchar(200) NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE video_checkpoint (
  checkpoint_id        varchar(64) PRIMARY KEY,
  tenant_id            varchar(64) NOT NULL,
  task_id              varchar(64) NOT NULL,
  run_id               varchar(64),
  runtime_run_id       varchar(128),
  step_id              varchar(80),
  checkpoint_type      varchar(32) NOT NULL,
  state_ref            varchar(500) NOT NULL,
  state_hash           char(64) NOT NULL,
  remaining_budget_json jsonb NOT NULL,
  runtime_last_event_id varchar(512),
  action_request_id    varchar(128),
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE video_agent_event (
  event_id         varchar(64) PRIMARY KEY,
  tenant_id        varchar(64) NOT NULL,
  task_id          varchar(64) NOT NULL,
  sequence         bigint NOT NULL,
  run_id           varchar(64),
  step_id          varchar(80),
  runtime_run_id   varchar(128),
  runtime_event_id varchar(512),
  event_type       varchar(64) NOT NULL,
  payload_json     jsonb NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, task_id, sequence)
);
```

## 11. Mock 契约

固定 Fixture：

- `video_001`: 未来工厂，2 个 Clip。
- `video_002`: 人机协作，2 个 Clip。
- `video_003`: 产品展示，2 个 Clip。
- `video_004`: 低质量和缺失证据测试，2 个 Clip。

Mock 行为：

| 输入 | 行为 |
|---|---|
| `mock-empty` | 返回零结果和 `NO_MATCH` warning |
| `mock-timeout` | 抛出可重试超时 |
| `mock-duplicate` | 返回相同 `clip_id` 的多路来源 |
| 默认 Query | 固定排序，结果可重复 |

Mock 约束：

- 不读取文件系统。
- 不生成随机 ID。
- 时间区间固定。
- 同一输入和 `fixture_version` 返回同一排序。
- Evidence 和 Candidate 使用正式 Schema。

## 12. 状态与幂等

### 12.1 乐观锁

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

影响行数为 0 时返回 `409 STATE_CONFLICT`。

### 12.2 Step 幂等

`idempotency_key = hash(tenant_id, task_id, step_key, input_artifact_hashes, action_version)`。

- `succeeded` 返回已有输出。
- `running` 未超时返回当前状态。
- 超时后按 attempt 和租约策略接管。
- `failed` 仅在可重试时增加 attempt。

### 12.3 Runtime 恢复

- 重试复用原 `requestId`。
- 先回读原 `runtime_run_id`。
- 活动 Run 使用 `attach(runId, lastEventId)`。
- 重复 Action 决议不得重复执行业务副作用。
- EOF 不等于 Run 完成。

## 13. 研发 Ticket

### 13.1 P0：契约与基础设施

| ID | Ticket | 交付 | DoD |
|---|---|---|---|
| VDA-001 | Monorepo 与依赖检查 | 模块骨架 | 非法依赖 CI 失败 |
| VDA-002 | 可信上下文 | Tenant/User/Project | 伪造身份测试通过 |
| VDA-003 | Error + Idempotency | 错误码和幂等拦截 | 重放无重复副作用 |
| VDA-004 | Artifact Registry | 版本、hash、lineage | 多版本和失效测试通过 |
| VDA-005 | Task/Step/Run/Event 表 | Migration + Repository | 状态与关联测试通过 |
| VDA-006 | Checkpoint 与 Resume | Waiting/Resume | 重启后无重复 Step |
| VDA-007 | SSE 与事件重放 | sequence/resync | 断线重连无丢失 |
| VDA-008 | Schema/OpenAPI 生成 | 契约管线 | 文档与代码一致 |

### 13.2 P1：Video/Clip 与 Mock

| ID | Ticket | 交付 | DoD |
|---|---|---|---|
| VDA-009 | Video/Clip Schema | JSON Schema + Java DTO | 时间区间合法 |
| VDA-010 | VideoCatalogPort | Port + Fake Catalog | 固定 Video/Clip 可查询 |
| VDA-011 | Fake Search | Search + 零结果/超时 | 输出 CandidateSet Schema |
| VDA-012 | Fake Recommendation | clip_candidate 场景 | 上下文影响排序 |
| VDA-013 | Fake Similar | Seed Clip → 候选 | 不返回超权限 Clip |
| VDA-014 | Fake Evidence | 固定证据与预览 | 证据和预览引用可解析 |
| VDA-015 | Feedback Attribution | 事件与 Power | request/candidate 链可追 |

### 13.3 P2：Agent 与 Workflow

| ID | Ticket | 交付 | DoD |
|---|---|---|---|
| VDA-016 | Tool Registry + Policy | Tool 白名单 | 非法 Tool 被拒 |
| VDA-017 | Runtime SDK Adapter | Run/Action/SSE | Fake Runtime 通过 |
| VDA-018 | Intent Router | Direct/Agent 分流 | 简单 Query 不建 Run |
| VDA-019 | Video Domain AgentSpec | Prompt + Output Schema | 固定版本可发布 |
| VDA-020 | Search/Recommend Tools | LocalToolset handler | 工具结果可回读 |
| VDA-021 | Creation Workflow | Brief/Storyboard/ClipPlan | 三个 Artifact 生成 |
| VDA-022 | Clip 并行与局部重算 | Step 调度 | 单 Clip 失败不阻塞其他 |
| VDA-023 | Waiting/Action/Approval | 用户确认和恢复 | 重复确认幂等 |
| VDA-024 | Budget/Retry/Failure | 预算和失败分类 | 故障注入通过 |

### 13.4 P3：Composition 与交付

| ID | Ticket | 交付 | DoD |
|---|---|---|---|
| VDA-025 | Composition 基线 | shortlist + scoring | 每 Clip 有首选/替代 |
| VDA-026 | Assignment 版本 | lock/replace/confirm | 旧版本可读 |
| VDA-027 | Storyboard/ClipPlan API | CRUD + validation | lineage 完整 |
| VDA-028 | Agent Eval | 固定任务集 | 回归可自动运行 |
| VDA-029 | 故障演练 | 超时/断连/权限 | 脚本全部通过 |
| VDA-030 | Demo 与 Runbook | 启动、重启、演示 | 新工程师可独立运行 |

## 14. Sprint

| Sprint | 目标 | Ticket |
|---|---|---|
| S1 | 契约、DB、Mock Catalog | 001–010 |
| S2 | Search/Recommend/Similar | 011–015 |
| S3 | Runtime、Agent、Tool | 016–020 |
| S4 | Creative Workflow | 021–024 |
| S5 | Composition、Eval、Demo | 025–030 |

## 15. Definition of Ready

- 输入输出 Schema 已冻结。
- 状态和失败路径明确。
- 租户、项目权限和 Tool 风险明确。
- 幂等和恢复方式明确。
- Agent 版本、Tool binding 和 Action 处理明确。
- 成功、零结果、超时、非法参数和权限失败用例齐备。

## 16. Definition of Done

- 格式、静态检查、单元和契约测试通过。
- 所有写操作有幂等测试。
- 所有 Tool 有 Registry 和 Policy 测试。
- Runtime Adapter 有版本、Run、Action、SSE 和 Tool 批次测试。
- 所有 Artifact 可校验 Schema 和 lineage。
- 新事件进入 Event Catalog。
- 不出现 Shot、Segment 或其他视频层级。
- 不引入真实检索、媒体渲染、前端或跨领域依赖。

## 17. 交付物

- 可启动的本地 Mock Compose。
- OpenAPI、JSON Schema 和数据库迁移。
- Fake Video/Clip Catalog。
- Fake Search/Recommend/Similar/Evidence。
- Video Domain AgentSpec 和 Prompt。
- Workflow、Artifact、Assignment 和 SSE。
- 契约、集成、Eval、故障注入测试。
- 启动、恢复、取消和演示 Runbook。
