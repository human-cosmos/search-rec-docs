# API 与数据契约

> **文档层级：** 实施规范  
> **上位文档：** [00 平台总体架构](../00_检索推荐与Agent平台_架构设计2.0.md)  
> **领域契约：** [03 Video Domain Pack 与创作执行](../03_Video_Domain_Pack与创作执行_架构设计2.0.md)  
> **状态：** 概念契约，研发启动时以 OpenAPI、JSON Schema 和代码定义为准

## 1. 契约原则

1. Search、Recommendation、Similarity、Explore 使用独立语义和独立接口。
2. Agent 只调用语义化 Tool/API，不直接访问 Elasticsearch、Milvus、Redis 或数据库。
3. 租户、用户和项目权限由服务端可信上下文注入，请求体不能覆盖。
4. 所有写操作声明幂等键、风险等级、审批要求和审计字段。
5. 所有结果返回策略版本、证据和可追溯标识。
6. 对外事件返回阶段状态和简短决策摘要，不暴露内部推理链、敏感 Prompt 或凭据。
7. 契约变更必须兼容版本管理；破坏性变更使用新版本，不静默改变字段语义。

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
    "shot_plan_id": "shotplan_003"
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
    "user_id": "user_123",
    "project_id": "project_456",
    "task_id": "task_123",
    "current_stage": "material_collection",
    "task_description": "制作一条城市夜生活品牌短片"
  },
  "limit": 30,
  "diversity": {
    "enabled": true,
    "max_per_cluster": 5
  }
}
```

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

## 3. 视频项目与任务 API

### 3.1 项目和任务

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/api/v1/video/projects` | 创建创作项目 |
| `GET` | `/api/v1/video/projects/{projectId}` | 获取项目及当前上下文 |
| `PATCH` | `/api/v1/video/projects/{projectId}` | 修改项目目标或约束 |
| `POST` | `/api/v1/video/projects/{projectId}/tasks` | 创建创作任务 |
| `GET` | `/api/v1/video/tasks/{taskId}` | 查询任务状态 |
| `POST` | `/api/v1/video/tasks/{taskId}/pause` | 暂停任务 |
| `POST` | `/api/v1/video/tasks/{taskId}/resume` | 恢复任务 |
| `POST` | `/api/v1/video/tasks/{taskId}/cancel` | 取消任务 |

任务状态以 [02 Agent Runtime 与任务治理](../02_Agent_Runtime与任务治理_架构设计2.0.md) 的定义为准。API 只返回状态、当前步骤、待处理事项、Artifact 引用和可执行操作，不返回模型内部推理链。

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

## 4. Agent Tool 契约

Tool 只暴露语义能力，不暴露底层客户端。

| Tool | 输入 | 输出 | 风险等级 |
|---|---|---|---|
| `search_video_materials` | SearchRequest | CandidateSet | L0 只读 |
| `recommend_video_materials` | RecommendationRequest | RecommendationSet | L0 只读 |
| `find_similar_shots` | EntityRef + constraints | CandidateSet | L0 只读 |
| `explore_video_materials` | Seed + goal | ExplorationSet | L0 只读 |
| `get_project_context` | project_id | ProjectContext | L0 只读 |
| `get_artifact` | artifact_id | Artifact | L0 只读 |
| `create_artifact` | type + schema + content | ArtifactRef | L1 写草稿 |
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

Video、Shot、Segment 的权威定义见 [Video Domain Pack](../03_Video_Domain_Pack与创作执行_架构设计2.0.md)。跨 API 引用时至少包含：

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
- 生命周期：`ingest_status`、`analysis_status`、`index_status`、`created_at`、`updated_at`。

视频领域关系不能只使用一个 `similar_to`。至少区分视觉相似、语义相关、同场景、同实体、替代拍摄、叙事衔接、互补、项目采用和 Shot 分配，并记录关系来源、置信度、模型版本和更新时间。

### 5.2 MaterialAssignment

```json
{
  "assignment_id": "ma_001",
  "project_id": "project_001",
  "storyboard_version": 3,
  "shot_plan_id": "shotplan_002",
  "entity_ref": {
    "entity_type": "segment",
    "entity_id": "segment_009",
    "source_video_id": "video_100",
    "start_ms": 12500,
    "end_ms": 18800
  },
  "scores": {
    "semantic_fit": 0.91,
    "visual_fit": 0.88,
    "technical_quality": 0.93,
    "task_fit": 0.90
  },
  "reasons": [
    "画面包含机械臂精准抓取动作",
    "近景构图符合该镜头需求",
    "片段长度满足目标时长"
  ],
  "rights_status": "verified",
  "status": "proposed",
  "locked_by_user": false
}
```

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
      "timeline_start_ms": 0,
      "track": "V1",
      "speed": 1.0,
      "transition_in": null,
      "transition_out": {"type": "cut"}
    }
  ],
  "audio_tracks": [],
  "text_overlays": []
}
```

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
