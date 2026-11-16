# 04 API、数据契约与存储（最终版 v1.0）

> **字段级权威（唯一）。** 其它文档与本文件冲突时，以本文件为准。
> 来源：impl_01 + impl_05 + 05（存储部分），合并后冻结为 Schema v1.0。

## 1. 原则

- 公开 API 只有 5 个检索类 POST（Search / Recommend / Similar / Feedback / Evidence Resolve）+ Agent Tool + Events（见 §2）。
- SearchPlan 只作 Agent Tool 输入，**不公开第二套 Search 路径**。
- Mock 与真实 Adapter 的 Schema 版本必须一致（v1.0）；真实版新增字段先作为可选字段加入，待版本路线图明确后再变必填（05 §20.2 规则保留；v1.0→v1.1 的字段路线图在真实 URRE 立项时定，见 §8 与 `07` §5 第 5 项）。
- 所有时间用毫秒（`ms`），所有 ID 用字符串，租户隔离字段 `tenant_id` 必填。
- **不得回流到领域模型的内容（源 05 §20.3，2026-11-16 补录）：**
  - Qdrant Payload 不能改变 Video / Clip 业务语义。
  - Plan、Storyboard 和 ClipPlan 不得写入素材索引。
  - Redis 中的 CandidateSet 不替代数据库中的 Task 和 Artifact。
  - 索引版本不能替代业务对象的 `metadata_version` 与 `content_version`。

## 2. Public API（冻结）

### 2.1 Search — `POST /v1/search`

请求（冻结字段）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 查询文本，**最长 500 字符**（源 05 §8.1） |
| `domain` | string | 是 | 本期固定 `video`（源 impl_01 §4.1、05 §8.1） |
| `target_levels` | string[] | 是 | `["clip", "video"]`（源 impl_01 §4.1、05 §8.1） |
| `channels` | string[] | 是 | 枚举见 §2.4；v1.0 冻结 `keyword, semantic, visual, metadata` |
| `filters` | object | 否 | 只允许注册字段（见 §2.4） |
| `candidate_budget` | integer | 是 | **冻结值 100** |
| `deadline_ms` | integer | 是 | **冻结值 8000** |
| `ranking` | object | 是 | `{strategy_id, strategy_version}`（05 结构为准；`strategy_id` 只在此处出现一次，**不设顶层 `strategy_id` 字段**，原 impl_01 的顶层字段为冗余，现删除）；**冻结值 `strategy_id="video_mock_hybrid_v1"`、`strategy_version="1.0"`（strategy_id 源 impl_05 §6.1；strategy_version 源 05 §8.1，05 §8.1 配对的 strategy_id `video-hybrid` 未采纳）** |
| `page` | object | 否 | `{size, cursor}`；`size` 冻结默认值 **20**，`cursor` 为不透明游标（源 impl_01 §4.1、05 §8.1；游标语义见 §6） |
| `schema_version` | string | 是 | `1.0` |

响应：CandidateSet v1.0（见 §3）。

### 2.2 Recommendation — `POST /v1/recommend`

请求：`context`（项目上下文）、`strategy_id`（冻结值 `video_mock_clip_fit_v1`）、`objective`（冻结值 `task_fit_then_diversity`）、`covered_storyboard_clip_ids`、`deadline_ms=8000`。
**规则（冻结）：`selected` 与 `covered_storyboard_clip_ids` 必须一致，不一致时 Schema 拒绝。**

`context` 内字段（源 impl_01 §4.3、05 §8.2）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `project_id` | string | 是 | 项目 ID |
| `task_id` | string | 是 | 任务 ID |
| `clip_plan_id` | string | 是 | ClipPlan ID |
| `storyboard_clip_id` | string | 是 | 本次推荐对应的计划 Clip；须与 `clip_requirement.storyboard_clip_id` 一致 |
| `clip_requirement` | object | 是 | 与 §4 ClipRequirement 同一 Schema，必填字段不得削薄；展开字段：`storyboard_clip_id`、`narrative_role`、`visual_goal`、`clip_type`、`duration_target_ms`、`hard_constraints` / `soft_preferences` / `fallback_requirements` / `evidence_requirements`（注：`clip_type` 仅见于示例，未入 §4.3 冻结 8 字段） |
| `covered_storyboard_clip_ids` | string[] | 否 | 已覆盖的计划 Clip |
| `selected` | object[] | 否 | 已选条目（`storyboard_clip_id`、`entity_type`、`video_id`、`clip_id`） |
| `excluded_clip_ids` | string[] | 否 | 排除的素材 Clip |

**命名空间规则（冻结，源 impl_01 §4.3、05 §8.2）：** `covered_storyboard_clip_ids` 只允许计划侧 `sb_clip_*`，`excluded_clip_ids` 只允许素材 `clip_id`，由 Schema 校验。

**归因上下文规则（源 05 §8.2）：** 已选、已覆盖和排除条件必须出现在反馈归因上下文中。

`limit`：**冻结值 20**（源 impl_01 §4.3 示例、05 §8.2）。

**推荐策略权重结构（5 维，源 04 §2.6.3）：** `content_relevance` 0.45、`project_fit` 0.25、`user_preference` 0.15、`diversity` 0.10、`freshness` 0.05。**登记为待验证字段（数值待 A/B），不得写成冻结值**——原文明确“权重仅为示例。生产权重应由离线实验、线上 A/B 和业务目标确定”。

### 2.3 Similar — `POST /v1/similar`

请求：`seed`（Seed 对象）、`similarity_targets`（v1.0 冻结值：`semantic` / `visual`；`attribute` / `behavior` / `relation` 为未来值，Mock 不实现）、`deadline_ms=5000`。
**规则：Similar 不返回 Seed 自身。**

Seed 对象形（源 impl_01 §4.4、05 §8.3）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `entity_type` | string | 是 | `clip` 或 `video` |
| `video_id` | string | 是 | 来源 Video ID |
| `clip_id` | string | 条件必填 | `entity_type=clip` 时必填；`entity_type=video` 时为空（该不变量与 §3 的候选规则一致，源 impl_01 §4.4） |

`strategy_id`：冻结值 `"video-similar"`；`strategy_version`：`"1.0"`（源 05 §8.3）。`limit`：**冻结值 20**（源 impl_01 §4.4 示例、05 §8.3）。

**响应必须明确记录实际生效的 `similarity_targets`**（源 05 §8.3）。

### 2.4 枚举与注册字段（冻结）

- `channels` 枚举（v1.0 冻结）：`keyword, semantic, visual, metadata`（源 05 §8.1 为 4 项；impl_01 §4.1/§4.2、impl_05 §8.3 为前 3 项）。其余值（attribute、collaborative、context、relation、trend、exploration）未冻结，属未来扩展。
- `filters` 可注册字段（v1.0 清单）：`status`（`available` / `unavailable`）、`duration_ms`（范围）、`video_id`、`tenant_id`。其余字段一律拒绝。
- `availability` 枚举：`available` / `unavailable`（完整枚举，原始文档只举例，现补齐）。
- `capability` 枚举：`search` / `recommend` / `similar` / `evidence` / `feedback`。

### 2.5 Feedback — `POST /v1/feedback`

`event_type` 冻结枚举（点分名，见 `02` §7）：

`recommendation.impression` / `recommendation.clicked` / `recommendation.preview` / `recommendation.saved` / `recommendation.downloaded` / `material.assigned` / `material.replaced` / `material.final_kept` / `recommendation.rejected`

业务名映射见 `02` §7。**未点击 ≠ 负反馈。**

请求字段表（源 impl_01 §4.6）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `event_type` | string | 冻结枚举见上 |
| `source` | string | 如 `api` |
| `occurred_at` | string | 事件发生时间（RFC 3339） |
| `request_id` | string | 来源请求 ID |
| `candidate_set_id` | string | 候选集合 ID |
| `project_id` | string | 项目 ID |
| `task_id` | string | 任务 ID（Direct 路径可为空，见 impl_05 §6.5） |
| `storyboard_clip_id` | string | 计划 Clip ID |
| `entity_type` | string | `video` / `clip` |
| `entity_id` | string | 跨能力通用标识 |
| `video_id` | string | 来源 Video ID |
| `clip_id` | string | 素材 Clip ID |
| `position` | integer | 曝光位置 |
| `strategy_version` | string | 策略版本 |
| `properties` | object | 扩展属性 |

请求必须携带 `Idempotency-Key`（源 impl_01 §4.6）。`material.assigned`、`material.replaced` 和 `material.final_kept` 由业务状态迁移通过 Outbox 产生（源 impl_01 §4.6）。

**反馈保留字段清单（源 01 §8.1）：** 曝光位置、候选集合、上下文、展示时长、策略版本——必须保留，否则无法正确解释未点击和点击行为。

**信号—事件映射表（11 类信号源 04 §2.6.4；9 个事件见本节冻结枚举）：**

| 信号 | 映射事件 | 备注 |
|---|---|---|
| 曝光 | `recommendation.impression` | 曝光上下文无位置字段（待补） |
| 点击 | `recommendation.clicked` | — |
| 预览开始 | `recommendation.preview` | `preview.started` 为未来 UI 遥测，不在 v1.0 事件枚举 |
| 预览时长 | 未映射 | 无 `duration` 字段 |
| 收藏 | `recommendation.saved` | — |
| 加入项目 | `material.assigned` | — |
| 加入时间线 | 未映射 | 与加入项目未区分 |
| 下载 | `recommendation.downloaded` | — |
| 实际使用 | `material.final_kept` | — |
| 删除 / 跳过 | 未映射 | 是否等于 `recommendation.rejected` 未定义 |
| 完成导出 | 未映射 | 无对应事件 |

注：`preview.started` / `preview.completed` 为未来 UI 遥测，不在 v1.0 事件枚举（源 impl_01 §8、impl_05 §6.5）。注：`Idempotency-Key` 同时进入 FeedbackCommand 的内部模型，真实 Adapter 重试时不得丢失（源 05 §8.6）。

### 2.6 Events（关联键权威）

`request_id`（来自 X-Request-Id）、`trace_id`（Traceparent 派生）、事件名以 §2.5 为准。关联键以本节为准（00 §7 引用 impl_01 §8，现统一为本文件 §2.6）。

统一关联键（源 impl_01 §8，按出现处填写，跨日志、SSE、审计必须可对齐）：

`request_id`、`trace_id`、`task_id`、`step_id`、`run_id`、`runtime_run_id`、`action_request_id`（Run 投影中对应 `current_action_request_id`）、`tool_call_id`、`candidate_set_id`、`artifact_id`、`workflow_plan_id`、`domain_invocation_id`、`external_domain_task_id`（共 13 个）。

事件信封另外必填（源 impl_01 §8，共 7 个）：

`event_id`、`event_type`、`event_time`、`tenant_id`、`user_id`、`project_id`、`session_id`。

必要事件名录（源 impl_01 §8 原文抄录）：

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

跨域事件（源 impl_07 §13 原文抄录，共 12 个）：

`workflow.plan.created`、`domain.invocation.started`、`domain.invocation.completed`、`domain.invocation.failed`、`domain.invocation.cancelled`、`domain.artifact.published`、`domain.artifact.staled`、`workflow.review.ready`、`creative.approval.required`、`creative.approval.decided`、`ads.draft.ready`、`publish.requested`。

### 2.7 Evidence Resolve — `POST /v1/evidence/resolve`

（新增，源 impl_01 §4.5；§1 的“5 个检索类 POST”至此与 §2 一致。）

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `evidence_refs` | string[] | 是 | 证据引用列表，如 `evidence/clip_003/frame_001`；只接受 `evidence_refs`，不接受宿主路径或长期对象地址（源 impl_05 §6.4） |
| `purpose` | string | 是 | 用途，如 `material_preview` |
| `project_id` | string | 是 | 项目 ID |

响应逐项返回允许或拒绝结果，每项含：`evidence_ref`、`status`（`available`）、`summary`、`video_id`、`clip_id`、`time_range`（`{start_ms, end_ms}`）、`preview_ref`、`expires_at`（源 impl_01 §4.5 示例）。

规则（源 impl_01 §4.5）：Evidence Resolver 必须重新校验租户和项目访问权限，不接受宿主路径；拒绝项不能泄露对象是否存在。

### 2.8 SearchPlan Schema

SearchPlan 只作为 Agent Tool / 复杂检索输入，不是独立公开 HTTP 路径（源 impl_01 §4.2）。公开 Search API（§2.1）只接受 SearchRequest；`search_video_materials` Tool 只接受 SearchPlan。由服务端将 SearchPlan 转换为内部检索请求，不得再公开第二套 Search 路径。

字段表（源 impl_01 §4.2）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schema_version` | string | 是 | 固定 `1.0` |
| `plan_id` | string | 是 | 计划 ID，maxLength 64 |
| `domain` | string | 是 | 固定 `video` |
| `target_levels` | string[] | 是 | `video`、`clip` |
| `semantic_query` | string | 是 | 语义查询，1–500 字符 |
| `sub_queries` | object[] | 否 | 最多 5 项；每项 `{role, query, weight}` |
| `hard_filters` | object | 是 | 硬过滤 |
| `soft_preferences` | object | 否 | 软偏好 |
| `recall_channels` | string[] | 是 | 如 `keyword`、`semantic`、`metadata`，最多 3 项 |
| `candidate_budget` | integer | 是 | 20–200 |
| `max_latency_ms` | integer | 否 | 500–15000 |

约束（源 impl_05 §8.3）：`plan_id` maxLength 64、`semantic_query` 1–500 字符、`sub_queries` maxItems 5、`candidate_budget` 20–200、`max_latency_ms` 500–15000；必填项为 `schema_version`、`plan_id`、`domain`、`target_levels`、`semantic_query`、`hard_filters`、`recall_channels`、`candidate_budget`。冻结值 `candidate_budget=100`、`max_latency_ms=8000` 在上述范围内。子查询权重归一化约定：权重之和为 1（源 impl_01 §4.2 示例权重 0.5 / 0.3 / 0.2 之和为 1）。

### 2.9 资源 API 去向指针

v1.0 只冻结 5 个检索类 POST（§2.1–§2.3、§2.5、§2.7）+ Agent Tool + Events；以下资源 API **不在 v1.0 公开契约内**，延期至后续版本（登记 `07` §5 第 20 项）：

| 端点组 | 精确指针 |
|---|---|
| Project 与 Task（含 `wait` / `resume` / `cancel`、SSE stream） | impl_01 §3.1 |
| Artifact（含版本、审批 `approve`） | impl_01 §3.2 |
| Assignment（含创建、锁定、替换、确认 `confirm`） | impl_01 §3.3 |
| Agent Run（含事件回放） | impl_01 §3.4 |
| Creative Production Task（含 `wait` / `resume` / `cancel`、SSE stream、`confirmations`、`publish`） | impl_01 §3.5 |
| 对外 API 摘要 | impl_04 §10.1 |
| 跨域 API | impl_07 §11 |

`wait` / `resume` / `cancel`、SSE stream、`approve` / `confirmations` / `publish` 的行为以状态机（`03` §3）与审批（`03` §8）为准，调用入口待资源 API 立项。

## 3. CandidateSet Schema v1.0（冻结）

（2026-11-16 补录：按裁决表 §0.1、源 impl_01 §5 恢复两级字段表；与 `08` §2 JSON Schema 逐字一致。）

**表一：顶层字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schema_version` | string | 是 | `1.0` |
| `candidate_set_id` | string | 是 | 候选集合 ID |
| `request_id` | string | 是 | 来源请求 ID |
| `capability` | string | 是 | 枚举见 §2.4（`search` / `recommend` / `similar` / `evidence` / `feedback`） |
| `handled_by` | string | 是 | `fast_path` \| `agent` |
| `project_id` | string | 是 | 项目 ID |
| `task_id` | string | 是 | 任务 ID（Direct 路径可为空，见 `08` A21） |
| `storyboard_clip_id` | string | 否（可为 null；Recommendation 时必填） | 计划 Clip ID |
| `strategy_version` | string | 是 | 策略版本 |
| `trace.query_version` | string | 是 | 查询版本 |
| `index_manifest_id` | string | 否（Mock 可空） | 真实版必填 |
| `manifest_epoch` | integer | 否（Mock 可空） | 真实版必填 |
| `score_normalization_version` | string | 否（Mock 可空，真实版必填） | 固定值 `rrf-v1` |
| `page` | object | 是 | `{next_cursor, has_more}` |
| `warnings` | array | 是 | 警告列表 |
| `items` | array | 是 | 候选条目（表二） |

**表二：条目字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `candidate_id` | string | 是 | 候选唯一 ID |
| `entity_type` | string | 是 | `video` \| `clip` |
| `entity_id` | string | 是 | 跨能力通用标识，须与类型化字段完全一致（见不变量） |
| `video_id` | string | 是 | 来源 Video ID（Video 候选必填；Clip 候选必填） |
| `clip_id` | string | 条件必填 | Clip 候选必填；Video 候选为空 |
| `start_ms` | integer | 条件必填 | Clip 候选必填；Video 候选为空 |
| `end_ms` | integer | 条件必填 | Clip 候选必填；Video 候选为空 |
| `rank` | integer | 是 | 排名 |
| `score` | number | 是 | RRF 融合分（`score_normalization_version=rrf-v1`） |
| `score_breakdown` | object | 是 | 各通道分；`visual` 可为 null |
| `recall_channels` | string[] | 是 | 召回通道 |
| `candidate_origin` | string（单数） | 是 | 候选来源（冻结为单数；05 的复数 `candidate_origins` 不采用） |
| `evidence` | object | 是 | 候选证据（匹配字段、片段位置） |
| `availability` | string | 是 | `available` \| `unavailable` |
| `versions` | object | 是 | `{feature_version, model_versions}` |

**必填性说明：** impl_01 §5 原文无显式 `required` 清单；本表必填性按 §5 示例出现情况判定——示例中出现的字段为必填（`storyboard_clip_id` 示例值为 null，Recommendation 时必填）；`index_manifest_id`、`manifest_epoch`、`score_normalization_version` 在 impl_01 §5 示例中未出现，按裁决表 §0.1 记为可选（Mock 可空，真实版必填）。

**不变量（源 impl_01 §5、impl_00 §2.2）：**

- `entity_type` 只能是 `video` 或 `clip`。
- Video 候选 `entity_id == video_id`，Clip 候选 `entity_id == clip_id`，由 Schema 校验、DDL CHECK 和契约测试保证。
- Clip 级候选必须携带来源 `video_id` 和精确时间区间（`start_ms` / `end_ms`）。
- 预览走 `preview_ref` / `keyframe_ref`；证据引用挂在候选或分配结果上，由 Evidence Port 解析，不是 Clip 的落列字段。

RRF 参数冻结：`k=60`。

**不进入 v1.0 的字段（`02` §6 已裁决）：** `candidate_origins`（复数）、`source_candidate_set_ids`、`matched_similarity_targets`、`matched_requirements`、`trace` 的 `latency_ms` / `degraded_channels` / `model_versions`——待真实 URRE 时再议。

## 4. Core Artifact（Storyboard / ClipPlan / MaterialAssignment）

- Storyboard：`storyboard_id`、`clips`（`clip_requirements`，**不用 `shots`**）、`duration_target_ms`。
- ClipPlan：`plan_id`、`domain`（`video`）、`hard_filters`、`candidate_budget`（100）、`storyboard_clip_id`。
- **注意：** Assignment 只有 `project_id`，无产品 ID。PRD REQ-E06（产出归属目标产品 ID）为待确认项（PRD OI-11；**更正：** v1.0 初版误写 OI-05，v1.6 §17.4 的 OI-05 影响 REQ-E02，E06 的待确认项是 OI-11），v1.0 不加产品 ID 字段；若 PRD 确认，须走 ADR 加字段。

### 4.1 Video（12 字段，源 03 §3.1）

| 字段 | 类型 | 说明 |
|---|---|---|
| `video_id` | string | Video 唯一 ID |
| `title` | string | 标题 |
| `source_type` | string | 来源类型，如 `library` |
| `duration_ms` | integer | 总时长（毫秒） |
| `width` | integer | 宽（像素） |
| `height` | integer | 高（像素） |
| `fps` | integer | 帧率 |
| `preview_ref` | string | 预览引用 |
| `availability` | string | `available` / `unavailable` |
| `tags` | string[] | 标签 |
| `feature_version` | string | 特征版本 |
| `created_at` | string | 创建时间 |

注：impl_05 §8.1 示例另含 `schema_version`（`"1.0"`）作为信封版本，不计入上述 12 个业务字段。

### 4.2 Clip（13 字段，源 03 §3.2）

| 字段 | 类型 | 说明 |
|---|---|---|
| `clip_id` | string | Clip 唯一 ID |
| `video_id` | string | 父 Video ID |
| `start_ms` | integer | 起始毫秒 |
| `end_ms` | integer | 结束毫秒 |
| `duration_ms` | integer | 时长（毫秒），落列字段 |
| `preview_ref` | string | 预览引用 |
| `keyframe_ref` | string | 关键帧引用 |
| `semantic_summary` | string | 语义摘要 |
| `tags` | string[] | 标签 |
| `quality_flags` | string[] | 质量标记 |
| `availability` | string | `available` / `unavailable` |
| `feature_version` | string | 特征版本 |
| `model_versions` | string[] | 模型版本列表 |

**三条不变量表述（源 03 §3.2、impl_00 §2.2）：**

- `duration_ms` 是落列字段，必须等于 `end_ms - start_ms`，不是仅在示例中出现的派生值；且 `0 <= start_ms < end_ms <= Video.duration_ms`。
- Clip 可跨语义切点，不要求对应内部剪辑切点。
- `clip_id` 与 `storyboard_clip_id` 不同 ID 命名空间（计划侧 `storyboard_clip_id` 与素材侧 `clip_id` 必须使用不同 ID 命名空间或明确字段名，避免混淆，源 03 §3.3）。

### 4.3 ClipRequirement（8 字段，源 03 §6.4）

| 字段 | 类型 | 说明 |
|---|---|---|
| `storyboard_clip_id` | string | 计划 Clip ID |
| `narrative_role` | string | 叙事角色 |
| `visual_goal` | string | 视觉目标 |
| `duration_target_ms` | integer | 目标时长（毫秒） |
| `hard_constraints` | object | 硬约束 |
| `soft_preferences` | object | 软偏好 |
| `fallback_requirements` | object | 兜底要求 |
| `evidence_requirements` | array | 证据要求 |

### 4.4 MaterialAssignment（源 impl_01 §6.3、03 §6.5；两份原文的字段集并集）

| 字段 | 类型 | 说明 |
|---|---|---|
| `assignment_id` | string | Assignment 唯一 ID |
| `project_id` | string | 项目 ID |
| `clip_plan_id` | string | ClipPlan ID |
| `storyboard_clip_id` | string | 计划 Clip ID |
| `entity_ref` | object | 绑定实体：`entity_type: video \| clip`，含 `video_id` / `clip_id`——恢复被静默删除的 Video 绑定能力（`entity_type=clip` 时 `video_id` 与 `clip_id` 必填；`entity_type=video` 时 `video_id` 必填、`clip_id` 为空，与 §3 不变量一致） |
| `match_evidence` | object | 匹配证据（`summary`、`evidence_refs`） |
| `alternatives` | object[] | 替代候选（同 `entity_ref` 形） |
| `selection_reason` | string | 选择理由 |
| `user_confirmed` | boolean | 用户是否确认 |
| `scores` | object | 13 项分，见 §5.4 |
| `status` | string | 枚举见下 |

`status` 枚举（源 impl_01 §3.3）：`proposed` / `confirmed` / `locked` / `superseded`。迁移规则：`confirm` → `confirmed`，锁定 → `locked`，替换 → `superseded`。

**规则（源 impl_04 §9、impl_06 §6.4）：**

- 每计划 Clip 首选 1 + 替代最多 3（另：每个计划 Clip 保留最多 10 个 shortlist，源 impl_04 §9）。
- 不允许同一 Clip 在相邻计划位置重复（除非用户明确允许）。
- 用户锁定的 Assignment 不得自动替换。
- 证据不足标记 `needs_user_review` / `low_quality`；自动 Assignment 必须显式标记待审核，不得用其他维度高分掩盖证据或质量问题。
- 素材不足返回缺口（与原因），不编造 Clip。

### 4.5 TaskBrief（9 项）与 CreativeBrief（6 项）

源 03 §6.1 / §6.2 原文为描述性条目，未给出 snake_case 字段名；以下逐条抄录原文条目，**不自造字段名**：

TaskBrief（源 03 §6.1）：用户目标、受众、平台、目标时长、画幅、语言、硬约束、软偏好、验收标准（共 9 项）。

CreativeBrief（源 03 §6.2）：主题、叙事方向、情绪、风格、节奏、创作约束（共 6 项）。

## 5. 存储（PostgreSQL 16，冻结）

### 5.1 基础表（业务表 26 张 DDL 全文以 impl_05 §10 为准）

- PostgreSQL **16**（冻结；原始文档未定大版本）。
- 迁移顺序与版本号：`V1__core_tables` → `V2__urre_tables` → `V3__task_workflow_tables` → `V4__feedback_outbox`；每个迁移可重复执行须幂等。迁移文件名为最终版约定，非原文值。
- **业务表 26 张（impl_05 §10，表名逐一核对）：** `video_project`、`video_task`、`video_task_step`、`video_agent_run`、`video_artifact`、`video_asset`、`video_clip`、`video_candidate_set`、`video_candidate`、`video_clip_plan`、`video_clip_requirement`、`video_assignment_set`、`video_material_assignment`、`video_tool_call`、`video_budget_ledger`、`video_checkpoint`、`video_agent_event`、`video_feedback_event`、`creative_project`、`creative_task`、`creative_task_step`、`domain_invocation`、`creative_artifact_index`、`creative_artifact_edge`、`creative_approval`、`creative_task_event`。
- **V1–V4 分配表（2026-11-16 新增裁决，见裁决表 §0.4）：**

| 迁移 | 表 | 张数 | 来源 |
|---|---|---|---|
| V1 业务核心表 | `video_project`、`video_task`、`video_task_step`、`video_agent_run`、`video_artifact`、`video_asset`、`video_clip`、`video_candidate_set`、`video_candidate`、`video_clip_plan`、`video_clip_requirement`、`video_assignment_set`、`video_material_assignment`、`video_tool_call`、`video_budget_ledger`、`video_checkpoint`、`video_agent_event` | 17 | impl_05 §10 |
| V2 URRE 表 | 05 §9 的 25 张中除反馈 / Outbox 外的 23 张（`urre_source`、`urre_raw_object`、`urre_canonical_snapshot`、`urre_input_artifact`、`urre_processing_profile`、`urre_index_profile`、`urre_embedding_profile`、`urre_ingestion_job`、`urre_ingestion_item`、`urre_processing_run`、`urre_processing_artifact`、`urre_embedding_record`、`urre_index_pool`、`urre_tenant_index_binding`、`urre_index_manifest`、`urre_index_target`、`urre_index_build`、`urre_index_build_item`、`urre_active_manifest`、`urre_candidate_set`、`urre_quota_policy`、`urre_quota_usage`、`urre_dead_letter`） | 23 | 05 §9 |
| V3 Task / Workflow 表 | `creative_project`、`creative_task`、`creative_task_step`、`domain_invocation`、`creative_artifact_index`、`creative_artifact_edge`、`creative_approval`、`creative_task_event` | 8 | impl_05 §10 |
| V4 反馈 / Outbox | `video_feedback_event`、`urre_feedback_event`、`urre_outbox_event` | 3 | impl_05 §10、05 §9 |
| 合计 | — | 51 | — |

- **索引意向清单（未指定落表与索引名，完整清单随 DDL 交付，见 `07` §5 第 4 项）：** 租户+实体（`tenant_id, entity_id`）、`manifest_id`、反馈归因（`tenant_id, event_type, created_at`）、`video_task(waiting_reason, status)`、`creative_task(waiting_reason, status)`。原始 05 DDL 全库仅 1 个 `CREATE INDEX`，上述为意向清单而非已落表索引。
- 上游快照 `business_payload_json` 最小内容清单见 05 §5.3（Video 至少含 `video_id`、`title`、`source_type`、`duration_ms`、`width` / `height` / `fps`、`preview_ref`、`availability`、`tags`、`status`、`created_at`；Clip 至少含 `clip_id`、`video_id`、`start_ms` / `end_ms` / `duration_ms`、`preview_ref`、`keyframe_ref`、`semantic_summary`、`tags`、`quality_flags`、`availability`、`feature_version`、`model_versions`）。
- `event_type` 加 CHECK 约束（枚举见 §2.5）。

### 5.2 Plan Schema（平台自建，新增定义）

`plan_id`、`plan_version`、`task_id`、`goal`、`budget`（见 `03` §5）、`tool_scope`（允许的 Tool 列表）、`side_effect_level`（最高等级）、`status`（`draft` / `approved` / `frozen` / `superseded`）、`created_at`、`approved_by`。

新增字段：

- `constraints`（对象，含 `duration_seconds` / `aspect_ratio` / `style` 等，见 `01` §4 Intent）。
- `steps`（Step 清单，字段见 `03` §8）。
- `acceptance_criteria`（验收条件清单）。

注：Risk 只有 `budget`，不新增独立 Risk 项——原文 02 §4.1 的 Risk & Budget 在 v1.0 只有 budget 有字段，写明。

### 5.3 Checkpoint Schema（平台自建，新增定义）

`checkpoint_id`、`task_id`、`plan_version`、`step_id`、`artifact_refs`、`budget_remaining`、`created_at`。不存模型内部推理链。

### 5.4 评分公式（冻结）

13 个评分项（源 impl_04 §9，`scores` 字段与公式维度一一对应，并额外保存聚合分数）：

| `scores` 字段 | 含义 |
|---|---|
| `semantic_fit` | 语义与 ClipRequirement 的匹配度 |
| `visual_fit` | 构图、主体和画面风格匹配度 |
| `evidence_confidence` | 时间证据和关键帧证据置信度 |
| `technical_quality` | 固定 Fixture 或未来技术检测质量 |
| `duration_fit` | 目标时长适配度 |
| `freshness` | 素材新鲜度 |
| `storyboard_coverage` | 跨 Clip 叙事覆盖度 |
| `style_consistency` | 集合风格一致性 |
| `low_redundancy` | 低重复度，越高表示重复越少 |
| `temporal_rhythm_fit` | 集合节奏适配度 |
| `clip_fit` | 单 Clip 聚合分数 |
| `collection_fit` | 集合聚合分数 |
| `task_fit` | 最终总分 |

子权重（源 impl_04 §9 原文逐项核对，权重属于可配置策略示例，子字段名见上表）：

```text
clip_fit =
  0.27 * semantic_fit +
  0.15 * visual_fit +
  0.22 * evidence_confidence +
  0.16 * technical_quality +
  0.15 * duration_fit +
  0.05 * freshness

collection_fit =
  0.40 * storyboard_coverage +
  0.25 * style_consistency +
  0.20 * low_redundancy +
  0.15 * temporal_rhythm_fit
```

顶层权重仍冻结 `clip_fit` 0.7 / `collection_fit` 0.3（v1.0 冻结默认值；改动须走 ADR）。注：impl_04 §9 的 `total = 0.75 * clip_fit + 0.25 * collection_fit` 是“可配置策略示例”，已裁决不采用。

质量分 = 加权和 × 100；80 分为通过线（见 `03` §6）。

**分数不可比护栏（源 05 §8.5）：业务层不得依赖 Mock 分数与真实模型分数的绝对值可比。**

### 5.5 跨域持久化

`creative_task` 与 `video_task` 的 `waiting_reason` CHECK 均允许 4 个值（修正 impl_05 §10.2 只允许 2 个的错误）。
`video_feedback_event` 归属阶段 1（修正 impl_03 与 impl_05 的阶段归属不一致）。

Task 应记录字段（指针）：`owner`、`tenant`、`domain`、`parent_task`、`current_step`、`deadline`、`cancel_reason`、`waiting_reason`、状态版本，见 impl_05 §10 `video_task` 表与 02 §4.2。

## 6. 错误（冻结，14 类逐类映射）

> **纠正（评审 R-08）：** v1.0 草稿的错误码表用了 9 类自编 `category`，与原始 impl_01 §9 的 14 类不符。以下 14 类**以 impl_01 §9 原文为准**，逐类映射 HTTP 状态与 `retryable`（均为 v1.0 冻结值）。

错误体示例（impl_01 §9 原文）：`{request_id, trace_id, code, category, message, retryable, details}`。

| category | HTTP | retryable | 说明 |
|---|---|---|---|
| `validation` | 400 | 否 | 参数校验失败；Tool Schema 非法返回 `TOOL_SCHEMA_INVALID`（源 impl_06 §6.3），Agent 最多修正一次 |
| `authentication` | 401 | 否 | 身份认证失败 |
| `authorization` | 403 | 否 | 无权访问；**跨租户对外返回 `not_found`（404），不返回 403** |
| `policy` | 403 | 否 | 策略拒绝（Tool 权限、副作用等级） |
| `not_found` | 404 | 否 | 对象不存在 |
| `conflict` | 409 | 否 | 同键不同体（幂等冲突）；另：乐观锁冲突返回 409 `STATE_CONFLICT`（见 `03` §5.4） |
| `rate_limited` | 429 | 是 | 限流，退避后重试 |
| `dependency_timeout` | 504 | 是 | 依赖超时 |
| `domain_unavailable` | 503 | 是 | 领域不可用 |
| `dependency_failed` | 502 | 是 | 依赖失败 |
| `approval_required` | 403 | 否 | 需审批（进入 Waiting(`awaiting_approval`)，不是重试） |
| `model_error` | 500 | 是 | 模型调用失败（瞬时） |
| `budget_exhausted` | 409 | 否 | 预算耗尽（进入 Waiting(`budget_exhausted`)，不是重试） |
| `internal` | 500 | 是 | 内部错误 |

分页游标：不透明游标（opaque cursor），格式由服务端定义，客户端不得解析；限流值：v1.0 Mock 不设限流，真实版另定。

## 7. Mock Fixture（冻结）

- 4 Video / 9 Clip：video_001（clip_001–003、clip_008）、video_002（clip_003–004）、video_003（clip_005–006）、video_004（clip_007、clip_009）。
- **语义相似视觉不同的一对冻结为 clip_003 / clip_004**（补 C 组 P2-2 缺口）。
- Mock 场景（冻结清单）：稳定成功、零结果、超时、非法参数、重复候选、非法 Tool 参数。触发方式见 `08_附录_核心契约正文.md` §7（`mock-illegal-param` 为**新增设计决策**，无原始依据，触发词在阶段 0 冻结）。
- 槽位字段（v1.6 DR-02）：每条试点成片须有槽位、起止时间、类型、封面。Mock Fixture 中起止时间与封面分别由 Clip 的 `start_ms`/`end_ms` 与 `preview_ref` 承载；「类型」在 v1.0 无独立字段，Mock 阶段不校验。
- Mock 部署：进程内 Mock（impl_02 §3），Fixture 目录与启动校验见 impl_02 §6；启动命令 `make compose-up / migrate / seed-mock / contract-test`（impl_02 §7）。
- 配置示例：`domain_timeout_ms=30000`（领域超时，与检索 8000 分属不同层：8000 约束检索总预算，30000 约束领域调用；前者更严）。

### 7.1 Fixture 数据明细（源 impl_06 §4.1–§4.2 原文抄录）

Fixture 数据见 impl_06 §4（本节此前只引用 impl_02 §6）。

Video：

| Video | 标题 | `duration_ms` |
|---|---|---:|
| `video_001` | 未来工厂 | 42000 |
| `video_002` | 人机协作 | 58000 |
| `video_003` | 产品展示 | 20000 |
| `video_004` | 研究素材 | 15000 |

Clip：

| Clip | Video | `start_ms`–`end_ms` | `duration_ms` | 语义 |
|---|---|---:|---:|---|
| `clip_001` | `video_001` | 0–7000 | 7000 | 工厂全景 |
| `clip_002` | `video_001` | 7000–16000 | 9000 | 机械臂生产线 |
| `clip_003` | `video_002` | 2000–9000 | 7000 | 人机协作 |
| `clip_004` | `video_002` | 9000–15000 | 6000 | 精密装配近景 |
| `clip_005` | `video_003` | 1000–8000 | 7000 | 产品英雄画面 |
| `clip_006` | `video_003` | 8000–14000 | 6000 | 产品细节 |
| `clip_007` | `video_004` | 3000–10000 | 7000 | 语义相似但视觉不同 |
| `clip_008` | `video_001` | 14000–25000 | 11000 | 跨内部切点的连续 Clip |
| `clip_009` | `video_004` | 10000–14000 | 4000 | 低清且证据不足的背景素材 |

`duration_ms` 必须等于 `end_ms - start_ms`，且 `end_ms <= Video.duration_ms`（源 impl_06 §4.2）。其中 `clip_008` 为跨内部切点的连续 Clip（11000ms），`clip_009` 为低清且证据不足的背景素材。

**Mock 与评测数据分离原则（源 03 §8）：** 固定 Fixture 保证集成测试稳定，评测集允许独立版本。

**`needs_user_action` 场景（源 impl_00 §4）：** 至少 1 个领域要求 `needs_user_action` 的场景。

**跨域 Mock 故障场景（源 impl_07 §14，共 7 项）：**

- Product 成功 / 缺失 / Claim 冲突。
- Landing Page 成功 / 超时 / stale 输入。
- Copy 成功 / 敏感 Claim 拒绝 / 部分候选。
- Ads 成功 / 预算不足 / 审批缺失。
- Video 零结果 / 局部替换 / Tool 超时。
- 一个领域失败时，无依赖分支继续完成。
- 重试复用 `invocation_id`，不产生重复 Artifact。

**Mock 超时可控**（源 impl_02 §9；超时触发见 `08` §7）。

### 7.2 运行配置（源 impl_02 §8）

```yaml
runtime:
  agent_name: video-domain-agent
  spec_version: 1.0.0
evidence:
  adapter: mock
orchestration:
  max_parallel_domains: 4
  domain_timeout_ms: 30000
  max_domain_retries: 2
  partial_result_policy: allow_with_gaps
domains:
  product: mock
  landing_page: mock
  copy: mock
  ads: mock
  video: internal
```

目标 Runtime 环境还需：`ACORE_BASE_URL`、`ACORE_TOKEN_URL`、应用凭证、允许调用的 Agent 资源权限。密钥仅由环境注入，不写入文档和版本库。

## 8. 版本与兼容

- Schema v1.0；Mock 与真实 Adapter 的 Schema 版本必须一致。
- 新增字段先作为可选字段加入，待版本路线图明确后再变必填；v1.0→v1.1 的字段路线图在真实 URRE 立项时定，见 `07` §5 第 5 项。
- 增加可选字段使用 Minor（源 impl_01 §10）。
- 修改语义、删除字段或重命名使用 Major（源 impl_01 §10）。
- 消费者必须能处理未知枚举值（源 impl_01 §10）。
- Artifact 按 `schema_version` 路由解析（源 impl_01 §10）。
