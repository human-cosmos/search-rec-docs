# API 与数据契约

> **状态：** Video Domain Agent 与跨域编排 API 基线。
> **模型：** `Video -> Clip`。
> **范围：** [交付范围与 Video/Clip 模型](00_交付范围与VideoClip模型.md)。
> **机器契约：** 正式编码以生成的 OpenAPI、JSON Schema、DDL 和契约测试为准。

## 1. 原则

1. 素材对象只有 Video 和 Clip。
2. Clip 必须引用父 Video，并携带精确时间区间。
3. Search、Recommendation 和 Similar 使用相同 CandidateSet 结构。
4. 简单 Search、Recommendation 和 Similar 可直接调用 Mock Port，不启动 Agent。
5. 租户、用户和项目权限由服务端可信上下文注入。
6. Agent 只调用语义 Tool，不直接访问数据库、Fixture 或文件。
7. 所有写操作有幂等键和审计字段；公共头与幂等语义见 §3.0。
8. Mock 与未来真实 Adapter 使用相同 Schema。
9. 对外事件只暴露状态、摘要和引用，不暴露内部推理。
10. 跨域任务由 `CreativeProductionWorkflow` 持有，Video Agent 不调用其他领域。
11. 领域间只交换版本化 Artifact Envelope 和 `DomainInvocationResult`。
12. Ads 草稿与外部发布是不同审批范围。

## 2. Domain Pack SPI

Video Domain Pack 注册：

- Domain Schema。
- Query Parser。
- Search/Recommendation Strategy。
- Agent Tools。
- 业务 Filter。
- Processing Profile 声明。
- Evaluation Strategy。

本次只实现领域所需的最小注册项。Processing Profile 可以注册空占位，但不能引入真实数据加工依赖。

```java
public interface DomainProvider {
    String getDomainId();
    DomainPackDescriptor getDescriptor();
    DomainSchema getSchema();
    List<QueryParser> getQueryParsers();
    List<AgentToolDescriptor> getTools();
    List<AgentSkillDescriptor> getSkills();
}
```

## 3. Public API

统一前缀：`/api/v1`。Video / Clip 对象字段与不变量以 [交付范围与 Video/Clip 模型](00_交付范围与VideoClip模型.md) §2 为准，物理列与 DDL 以 [工程契约与研发 Backlog](05_VideoDomainAgent_工程契约与研发Backlog.md) §8 / §10.6 为准，本文不另抄字段表。

### 3.0 公共头

所有公开 API 使用以下公共头：

```http
Authorization: Bearer <token>
X-Tenant-Id: <trusted-gateway-injected>
X-Request-Id: <request-id>
Idempotency-Key: <required-for-mutation>
Traceparent: <w3c-trace-context>
```

写操作（`POST` / `PATCH`，含创建项目与任务、approve、assign、confirm、wait、resume、cancel 和 Feedback）必须携带 `Idempotency-Key`。相同键重放时：若请求体一致，返回首次成功结果；若请求体不一致，返回冲突，不得再执行一次副作用。工程示例见 [工程契约与研发 Backlog](05_VideoDomainAgent_工程契约与研发Backlog.md) §5.1，公共头与幂等语义以本节为准。

服务端不信任客户端自报 `user_id`、租户和项目范围。

### 3.1 Project 与 Task

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/video/projects` | 创建项目 |
| `GET` | `/video/projects/{projectId}` | 查询项目 |
| `PATCH` | `/video/projects/{projectId}` | 修改目标或约束 |
| `POST` | `/video/projects/{projectId}/tasks` | 创建任务 |
| `GET` | `/video/tasks/{taskId}` | 查询状态 |
| `GET` | `/video/tasks/{taskId}/stream` | 订阅 SSE；数据帧使用 §8 事件信封 |
| `POST` | `/video/tasks/{taskId}/wait` | 进入 Waiting |
| `POST` | `/video/tasks/{taskId}/resume` | 恢复任务 |
| `POST` | `/video/tasks/{taskId}/cancel` | 取消任务 |

创建任务：

```json
{
  "goal": "为智能机器人整理一组 30 秒宣传片 Clip",
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

Task 状态：

- `Created`
- `Planned`
- `AwaitingApproval`
- `Running`
- `Waiting`
- `Reviewing`
- `Completed`
- `Failed`
- `Cancelled`

`Waiting` 必须带 `waiting_reason`：

- `awaiting_user`
- `budget_exhausted`
- `awaiting_domain`
- `awaiting_approval`

Video-only Task 只启用前两项；`awaiting_domain` 和 `awaiting_approval` 仅用于 Creative Production Task 或跨域子工作流。

Task 合法状态迁移以 [详细设计与实施手册](04_VideoDomainAgent_详细设计与实施手册.md) §3.1 为准。`POST /video/tasks/{taskId}/wait` 请求体必须带已启用的 `waiting_reason`，且仅允许从 `Running` 进入 `Waiting`；禁止客户端把任意状态的任务直接打成 `Waiting`。

```json
{
  "waiting_reason": "awaiting_user"
}
```

### 3.2 Artifact

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/video/artifacts/{artifactId}` | 读取 Artifact |
| `GET` | `/video/artifacts/{artifactId}/versions` | 读取版本 |
| `POST` | `/video/artifacts/{artifactId}/approve` | 审批或确认 |

### 3.3 Assignment

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/video/compositions/assign` | 创建 Assignment |
| `GET` | `/video/assignments/{assignmentSetId}` | 查询 Assignment |
| `PATCH` | `/video/assignments/{assignmentSetId}` | 锁定或替换 |
| `POST` | `/video/assignments/{assignmentSetId}/confirm` | 用户确认 |

Assignment `status` 枚举为 `proposed`、`confirmed`、`locked`、`superseded`，与 `implementation/05` §10.6 DDL CHECK 一致，本文不再另造状态名。`POST .../confirm` 将对应 Assignment 迁为 `confirmed`；`PATCH` 用于锁定（迁为 `locked`）或替换（被替换项迁为 `superseded`）。

### 3.4 Agent Run

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/video/agent-runs/{runId}` | 查询领域 Run |
| `GET` | `/video/agent-runs/{runId}/events` | 按 sequence 回放事件 |

响应保存：

- `run_id`
- `runtime_run_id`
- `agent_id`
- `spec_version`
- `session_id`
- `request_id`
- `current_action_request_id`
- `runtime_last_event_id`
- `usage`

### 3.5 Creative Production Task

跨域任务使用独立资源，避免把 Product、Landing Page、Copy 和 Ads 塞入 Video Task。

```http
POST /api/v1/creative/projects
GET  /api/v1/creative/projects/{projectId}
POST /api/v1/creative/projects/{projectId}/tasks
GET  /api/v1/creative/tasks/{taskId}
GET  /api/v1/creative/tasks/{taskId}/stream
GET  /api/v1/creative/tasks/{taskId}/domains
GET  /api/v1/creative/tasks/{taskId}/domains/{invocationId}
GET  /api/v1/creative/artifacts/{artifactId}
GET  /api/v1/creative/artifacts/{artifactId}/versions
POST /api/v1/creative/tasks/{taskId}/wait
POST /api/v1/creative/tasks/{taskId}/resume
POST /api/v1/creative/tasks/{taskId}/cancel
POST /api/v1/creative/tasks/{taskId}/confirmations
POST /api/v1/creative/tasks/{taskId}/publish
```

创建任务：

```json
{
  "goal": "把商品 1044535 跟到韩国 TikTok，生成口播、落地页方案和视频广告草稿，不自动发布",
  "mode": "cross_domain_campaign",
  "target": {
    "market": "KR",
    "platform": "TikTok",
    "locale": "ko-KR"
  },
  "requested_outputs": [
    "product-context",
    "video-creative-artifact",
    "copy-package",
    "landing-page-plan",
    "ads-draft"
  ],
  "constraints": {
    "duration_ms": 28000,
    "aspect_ratio": "9:16"
  },
  "execution": {
    "allow_partial": true,
    "require_publish_approval": true
  }
}
```

Video-only 请求继续使用 §3.1 的 `mode=creation` Video Task。跨域领域调用和状态细节以 [跨域编排设计](07_跨域编排与领域子工作流设计.md) §8 / §9 为准。

## 4. Retrieval API

### 4.1 Search

`POST /api/v1/retrieval/search`

```json
{
  "domain": "video",
  "query": "工程师与机械臂协作",
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

### 4.2 Complex SearchPlan

```json
{
  "schema_version": "1.0",
  "plan_id": "sp_001",
  "domain": "video",
  "target_levels": ["video", "clip"],
  "semantic_query": "工程师与机械臂协作完成精密装配",
  "sub_queries": [
    {
      "role": "subject_action",
      "query": "engineer collaborating with robotic arm",
      "weight": 0.5
    },
    {
      "role": "scene",
      "query": "modern factory",
      "weight": 0.3
    },
    {
      "role": "clip_type",
      "query": "close up",
      "weight": 0.2
    }
  ],
  "hard_filters": {
    "duration_ms": {"gte": 2000, "lte": 10000}
  },
  "soft_preferences": {
    "orientation": "landscape"
  },
  "recall_channels": ["keyword", "semantic", "metadata"],
  "candidate_budget": 100,
  "max_latency_ms": 8000
}
```

`SearchPlan` 只作为 Agent Tool / 复杂检索输入，不是独立公开 HTTP 路径。公开 Search API（§4.1）只接受 `SearchRequest`；`search_video_materials` Tool 只接受 `SearchPlan`。由服务端将 `SearchPlan` 转换为内部检索请求，不得再公开第二套 Search 路径。

### 4.3 Recommendation

`POST /api/v1/retrieval/recommend`

本次 `scene` 枚举只允许 `clip_candidate`。其余推荐场景见 `03`，列为未来扩展，不进入本次契约。`covered_storyboard_clip_ids` 只允许计划侧 `sb_clip_*`，`excluded_clip_ids` 只允许素材 `clip_id`，由 Schema 校验。这里的 `clip_requirement` 使用与 §6.2 相同的 `ClipRequirement` Schema，必填字段不得削薄；其中 `storyboard_clip_id` 必须与同级 context 字段一致。

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
      "storyboard_clip_id": "sb_clip_003",
      "narrative_role": "proof",
      "visual_goal": "人机协作完成精密装配",
      "clip_type": "close_up",
      "duration_target_ms": 5000,
      "hard_constraints": {},
      "soft_preferences": {},
      "fallback_requirements": {},
      "evidence_requirements": []
    },
    "covered_storyboard_clip_ids": ["sb_clip_001", "sb_clip_002"],
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

### 4.4 Similar

`POST /api/v1/retrieval/similar`

```json
{
  "seed": {
    "entity_type": "clip",
    "video_id": "video_002",
    "clip_id": "clip_003"
  },
  "domain": "video",
  "similarity_targets": ["semantic", "visual"],
  "filters": {},
  "limit": 20
}
```

`entity_type=clip` 时 `video_id` 与 `clip_id` 必填；`entity_type=video` 时 `video_id` 必填、`clip_id` 为空。该不变量与 §5 的候选规则一致。

### 4.5 Evidence

`POST /api/v1/evidence/resolve`

```json
{
  "evidence_refs": [
    "evidence/clip_003/frame_001"
  ],
  "purpose": "material_preview",
  "project_id": "project_001"
}
```

响应逐项返回允许或拒绝结果：

```json
{
  "items": [
    {
      "evidence_ref": "evidence/clip_003/frame_001",
      "status": "available",
      "summary": "工程师与机械臂协作装配",
      "video_id": "video_002",
      "clip_id": "clip_003",
      "time_range": {"start_ms": 2000, "end_ms": 9000},
      "preview_ref": "preview/clip_003",
      "expires_at": "2026-11-12T10:10:00Z"
    }
  ]
}
```

Evidence Resolver 必须重新校验租户和项目访问权限，不接受宿主路径；拒绝项不能泄露对象是否存在。

### 4.6 Feedback

`POST /api/v1/retrieval/feedback`

```json
{
  "event_type": "recommendation.clicked",
  "source": "api",
  "occurred_at": "2026-11-12T10:00:00Z",
  "request_id": "req_001",
  "candidate_set_id": "cs_001",
  "project_id": "project_001",
  "task_id": "task_001",
  "storyboard_clip_id": "sb_clip_003",
  "entity_type": "clip",
  "entity_id": "clip_003",
  "video_id": "video_002",
  "clip_id": "clip_003",
  "position": 1,
  "strategy_version": "video_mock_clip_fit_v1",
  "properties": {}
}
```

请求必须携带 `Idempotency-Key`。本次无前端，反馈示例如上来自 API 或 Agent；`material.assigned`、`material.replaced` 和 `material.final_kept` 由业务状态迁移通过 Outbox 产生。

## 5. CandidateSet

```json
{
  "schema_version": "1.0",
  "candidate_set_id": "cs_001",
  "request_id": "req_001",
  "capability": "search",
  "handled_by": "fast_path",
  "project_id": "project_001",
  "task_id": "task_001",
  "storyboard_clip_id": null,
  "strategy_version": "video_mock_hybrid_v1",
  "items": [
    {
      "candidate_id": "cand_001",
      "entity_type": "clip",
      "entity_id": "clip_003",
      "video_id": "video_002",
      "clip_id": "clip_003",
      "start_ms": 2000,
      "end_ms": 9000,
      "rank": 1,
      "score": 0.92,
      "score_breakdown": {
        "keyword": 0.86,
        "semantic": 0.94,
        "metadata": 0.91
      },
      "recall_channels": ["keyword", "semantic"],
      "candidate_origin": "search",
      "evidence": {
        "summary": "工程师与机械臂协作装配",
        "evidence_refs": ["evidence/clip_003/frame_001"]
      },
      "availability": "available",
      "versions": {
        "feature_version": "fixture-v1",
        "model_versions": ["fixture-v1"]
      }
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  },
  "warnings": []
}
```

Video 候选：

- `entity_type=video`
- `video_id` 必填
- `clip_id/start_ms/end_ms` 为空

`entity_id` 是跨能力通用标识，但与类型化字段必须完全一致：Video 候选要求 `entity_id == video_id`，Clip 候选要求 `entity_id == clip_id`。该不变量同时由 Schema 校验、DDL CHECK 和契约测试保证。

Clip 候选：

- `entity_type=clip`
- `video_id/clip_id/start_ms/end_ms` 必填

## 6. Core Artifact

### 6.1 Storyboard

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
          "duration_target_ms": 5000,
          "hard_constraints": {},
          "soft_preferences": {},
          "fallback_requirements": {},
          "evidence_requirements": []
        }
      ]
    }
  ]
}
```

### 6.2 ClipPlan

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
      "clip_type": "medium_close_up",
      "duration_target_ms": 6000,
      "hard_constraints": {},
      "soft_preferences": {"orientation": "landscape"},
      "fallback_requirements": {"allow_cutaway": true},
      "evidence_requirements": ["human_robot_collaboration"]
    }
  ]
}
```

### 6.3 MaterialAssignment

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
    "clip_id": "clip_003"
  },
  "match_evidence": {
    "summary": "人机协作装配近景",
    "evidence_refs": ["evidence/clip_003/frame_001"]
  },
  "alternatives": [
    {
      "entity_type": "clip",
      "video_id": "video_002",
      "clip_id": "clip_004"
    }
  ],
  "selection_reason": "满足主体、动作和时长要求",
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

`status` 枚举为 `proposed`、`confirmed`、`locked`、`superseded`，与 `implementation/05` §10.6 DDL CHECK 一致；迁移规则见 §3.3。

### 6.4 Artifact Metadata

所有 Artifact 至少包含：

- `artifact_id`
- `artifact_type`
- `schema_version`
- `project_id`
- `task_id`
- `owner_domain`
- `producer_invocation_id`
- `parent_artifact_ids`
- `content_schema`
- `content_ref`
- `content_hash`
- `producer_tool`
- `model_version`
- `validation_status`
- `permission_scope`
- `created_at`

### 6.5 Domain Invocation

```json
{
  "schema_version": "1.0",
  "invocation_id": "di_001",
  "task_id": "task_001",
  "step_key": "copy.generate_package",
  "domain": "copy",
  "operation": "generate_copy_package",
  "status": "succeeded",
  "input_refs": [
    "artifact://product-context/pc_001/v1"
  ],
  "output_refs": [
    "artifact://copy-package/copy_001/v1"
  ],
  "warnings": [],
  "error": null,
  "usage": {
    "units": 2
  },
  "external_task_ref": null
}
```

`domain` 允许值：`product`、`landing_page`、`copy`、`ads`、`video`。

`status` 允许值：`started`、`succeeded`、`partial`、`needs_user_action`、`failed`、`cancelled`。

领域调用必须由主 Workflow 发起。该契约不注册为 Video Domain Agent Tool。

## 7. Agent Tool

| Tool | 输入 | 输出 | 风险 |
|---|---|---|---|
| `get_project_context` | project_id | ProjectContext | L0 |
| `search_video_materials` | SearchPlan | CandidateSetRef | L0 |
| `recommend_video_materials` | RecommendationContext | CandidateSetRef | L0 |
| `find_similar_materials` | Video/ClipRef | CandidateSetRef | L0 |
| `resolve_evidence` | evidence_refs | EvidenceViewSet | L0 |
| `create_artifact_draft` | artifact draft | ArtifactRef | L1 |
| `assign_materials` | ClipPlan + CandidateSetRefs | AssignmentSetRef | L1 |
| `request_user_confirmation` | question/scope | CheckpointRef | L1 |

每个 Tool 必须声明：

- 输入/输出 JSON Schema。
- 权限 scope。
- 风险等级。
- 超时和重试。
- 幂等模式。
- 日志脱敏策略。

## 8. Events

本节是本次交付的事件目录与统一关联键权威来源。总纲和其他文档引用本节，不再各自维护一份关联键清单。

统一关联键（按出现处填写，跨日志、SSE、审计必须可对齐）：

- `request_id`
- `trace_id`
- `task_id`
- `step_id`
- `run_id`
- `runtime_run_id`
- `action_request_id`（Run 投影中对应 `current_action_request_id`）
- `tool_call_id`
- `candidate_set_id`
- `artifact_id`
- `workflow_plan_id`
- `domain_invocation_id`
- `external_domain_task_id`

事件信封另外必填：

- `event_id`
- `event_type`
- `event_time`
- `tenant_id`
- `user_id`
- `project_id`
- `session_id`

必要事件：

- `task.created`
- `task.status.changed`
- `plan.created`
- `step.started/completed/failed`
- `tool.started/completed/failed`
- `action.required/decided`
- `artifact.created/staled`
- `retrieval.requested/completed`
- `recommendation.impression`
- `recommendation.clicked`
- `material.rejected`
- `material.assigned/replaced/final_kept`
- `workflow.plan.created`
- `domain.invocation.started/completed/failed/cancelled`
- `domain.artifact.published/staled`
- `workflow.review.ready`
- `creative.approval.required/decided`
- `ads.draft.ready`
- `publish.requested`

`preview.started/completed` 属于未来 UI 遥测，本次没有预览 Tool 和前端，不列为必要事件。

## 9. Error

```json
{
  "request_id": "req_001",
  "trace_id": "trace_001",
  "code": "FORBIDDEN",
  "category": "authorization",
  "message": "当前身份无权访问该对象",
  "retryable": false,
  "details": {}
}
```

错误类别：

- `validation`
- `authentication`
- `authorization`
- `policy`
- `not_found`
- `conflict`
- `rate_limited`
- `dependency_timeout`
- `domain_unavailable`
- `dependency_failed`
- `approval_required`
- `model_error`
- `budget_exhausted`
- `internal`

## 10. 版本与兼容

- 增加可选字段使用 Minor。
- 修改语义、删除字段或重命名使用 Major。
- 消费者必须能处理未知枚举值。
- Artifact 按 `schema_version` 路由解析。
- Mock 和真实 Adapter 的 Schema 版本必须一致。
