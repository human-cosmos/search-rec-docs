# 04 API、数据契约与存储（最终版 v1.0）

> **v1.1 修订注记（2026-11-16）：** 依据覆盖分析《VideoDomainAgent_与PRD原型覆盖分析.md》+ PRD v1.6；改动摘要：新增 §9–§13，补齐覆盖分析 §10.2 的 10 个新对象、六项技能 Schema、MediaActionPlan 与 Media Capability Workflow API、槽位与跟品契约、反馈扩展及 REQ-E01/E07 契约落点；§1–§8 冻结内容（CandidateSet Schema、状态机 18 条边、预算、5 个检索类 POST、14 类错误）一字未改。
> **v1.2 修订注记（2026-11-16）：** §9.3 新增 `active` / `pending_slot` / `supplementary_inputs` 字段与 `input_media_ref.source`、`result.partial` / `missing_items`；§9.4 计划 `status` 改为聚合规则；新增 §10.1 媒体 Adapter 接口契约；§13.2 对照表补 §11 行；§13.3 第 6、10 项更新（OI-07 拆分，v1.3 已移除、ADR-19–21 立项）。§1–§8 冻结内容一字未改。

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

> **同名不同义（v1.2 复核 N1-04）：** 本节 `category` 是 14 类错误分类（`validation` / `authentication` / …），`retryable` 是其一列；§9.3/§9.4/§10.1 的 `error.category` 是二值 `retryable` / `non_retryable`（只决定是否可重试），两者同名不同义，不得混用——任务/动作级 error 对象中的 `category` 一律指二值，不指本节 14 类。

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

## 9. PRD v1.6 新增对象契约（v1.1 新增）

> 来源：覆盖分析 §6.1、§6.2、§6.3、§10.2。设计原则（覆盖分析 §6.1、§7.1）：Video / Clip 本体不塞爆——语义加工、投放表现、编辑决策、资产投影拆成独立对象挂引用；Video Domain Agent 只输出声明式媒体动作意图，不直接执行渲染/转码/导出（执行归 Media Capability Workflow，见 §10）。本节对象均为 **v1.1 新增、未冻结**：字段名与枚举值须经 ADR 立项冻结后方可进入 Backlog（`07` §5 第 20 项资源 API 延期口径同样适用）；新增数字全部引自 PRD，无 PRD 出处的数值一律标“待确认”。
>
> 存储落点（提议，未冻结；§5.1 的 V1–V4 共 51 张表与业务表 26 张计数不变）：新增对象持久化复用现有表（`video_task`、`video_artifact`、`video_asset`、`video_feedback_event`，见 §5.1）+ 提议新增表 `video_entry_task`、`video_recommended_scenario`、`video_skill_task`、`video_media_action_plan`、`video_edit_decision`、`video_derived_video`、`video_performance_snapshot`、`video_personal_asset`、`video_user_preference`、`video_user_memory`、`video_session_canvas`；表名与 DDL 随 ADR 立项时冻结。Mock Fixture 不变（§7 的 4 Video / 9 Clip）；新对象暂无 Mock Fixture，Mock 方案见各节“待确认”行与 §13。
>
> JSON Schema 正文见 `08` A-9–A-21；`04` §9–§13 与 `08` §9–§10 双向一一对应（对照表见 §13）。

### 9.1 EntryTask（入口任务模板）

来源：PRD §5（四个智能体入口：全链路跟品、视频二创、找爆款、爆款复刻；六项技能）；覆盖分析 §2.2、§6.3、§10.2。`entry_type` 区分入口，必填参数与结果去向按入口模板定义；参数缺失时追问（BR-01 技能追问、BR-02 跟品补参、BR-10 直接开始条件）。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `entry_task_id` | string | 是 | 唯一 ID | 覆盖分析 §6.3 |
| `tenant_id` | string | 是 | 租户隔离（§1） | §1 |
| `session_id` | string | 是 | 所属会话 | PRD §12 |
| `entry_type` | string | 是 | 枚举：`find_hot`（找爆款）/`video_remix`（视频二创）/`hot_remake`（爆款复刻）/`follow_product`（全链路跟品）/`skill`（六项技能） | PRD §5；覆盖分析 §2.2 |
| `skill_type` | string | 条件必填 | `entry_type=skill` 时必填，枚举见 §9.3 | PRD §5 |
| `task_template_id` | string | 是 | 版本化入口模板 ID（如 `find_hot@v1`） | 覆盖分析 §6.3 |
| `required_params` | object | 是 | 本入口必填参数（见下表）；缺失项进 `missing_params` | PRD §5；BR-01/BR-02/BR-10 |
| `missing_params` | string[] | 否 | 缺失参数名清单；非空时须追问，不得静默执行 | BR-01、BR-10 |
| `clarification_question` | string | 否 | 追问文案 | BR-01 |
| `allowed_actions` | string[] | 是 | 本入口允许的动作（MediaActionPlan 动作子集，见 §10） | 覆盖分析 §6.3 |
| `result_destination` | string | 是 | 枚举：`session_dialog`（对话）/`canvas`（右画布）/`asset`（个人资产）；找片结果先在对话显示，完整结果与视频操作在右画布展开 | PRD §11；覆盖分析 §2.1 |
| `source_refs` | object | 否 | 入口来源引用：`product_id` / `video_id` / `clip_id` / `reference_video_id`，按入口取用 | PRD §4、§5 |
| `status` | string | 是 | **复用 Task 状态机（`03` §3，18 条边冻结），不另设状态机** | `03` §3 |
| `task_id` | string | 否 | 绑定后填入的 Task ID | `03` §2 |

各入口必填参数（PRD §5、跟品节 BR-08–BR-10）：`find_hot` 须 `query | product_id | reference_media` 三选一；`video_remix` 须 `video_id`（带槽位成片，PRD §6）；`hot_remake` 须 `reference_video_id`；`follow_product` 须商品输入（可空时用演示商品，BR-08）+ 国家/平台（缺一则停在“待开始”补参，BR-10）；`skill` 须 `skill_type` + 各技能必填输入（见 §9.3）。入口路由映射（四入口→必需上下文→主要输出）见 `03` §4.3（03 组负责；本文件只定任务契约）。

### 9.2 RecommendedScenario（推荐场景）

来源：PRD §17.2 DR-07、DR-08；覆盖分析 §8、§10.2。推荐场景是独立对象，不塞进 ClipRequirement（§4.3 冻结 8 字段不动）。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `scenario_id` | string | 是 | 唯一 ID | DR-07 |
| `tenant_id` | string | 是 | 租户隔离（§1） | §1 |
| `category` | string | 是 | 品类 | DR-07 |
| `slot_type` | string | 是 | 适配的槽位类型；**枚举值待确认**（PRD 只定 DR-02“槽位类型”，未给枚举；见 OI-02） | PRD §17.2 DR-02；OI-02 |
| `title` | string | 是 | 场景标题 | DR-07 |
| `prompt_text` | string | 是 | 每个场景一段可提交的提示词 | DR-08 |
| `source_evidence` | object | 否 | 历史较好画面引用 + 偏好来源（DR-13 显式偏好优先） | DR-07、DR-13 |
| `rank` | integer | 否 | 同槽位类型内排序 | DR-07 |

规则：每个试点槽位类型至少 3 个推荐场景（PRD §17.2 DR-07 原文）；场景提示词可编辑、可提交（DR-08）。推荐场景的计算与数据源待确认（OI-02）。

### 9.3 SkillTask / SkillResult（六项技能）

来源：PRD §5 六项技能表、BR-01；PRD §8、§12（任务恢复）；PRD §17.2 DR-17、§17.3 NFR-04；覆盖分析 §2.3、§10.2。六项技能共用同一任务/结果信封 + 各技能独立的 `task_params` / `result` 结构；简单技能可走确定性模板，不必启动 Agent（覆盖分析 §7.2）。

> **v1.2（2026-11-16）：** 状态说明由注记升级为投影表（`03` §4.5.3）+ 契约测试（`08` §11）；新增 `active` / `pending_slot` / `supplementary_inputs` 字段（追问状态机，`03` §4.7）；`input_media_ref` 新增 `source`（演示视频来源标记）；`result` 新增 `partial` / `missing_items`（部分完成）。

**SkillTask 通用字段：**

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `skill_task_id` | string | 是 | 唯一 ID | PRD §5 |
| `skill_type` | string | 是 | 枚举：`subtitle_extract`（提取字幕）/`voiceover`（配口播）/`erase_element`（擦除元素）/`aspect_ratio`（调整画幅）/`clip_generate`（片段生成）/`selling_overlay`（卖点浮层） | PRD §5 |
| `tenant_id` / `session_id` / `task_id` | string | 是/是/否 | 租户/会话必填；绑定 Task 后填 `task_id` | §1；PRD §12 |
| `input_media_ref` | object | 条件必填 | `{video_id, clip_id?, source}`；**条件（R12-25）：** 需视频的四项技能（`subtitle_extract` / `erase_element` / `aspect_ratio` / `selling_overlay`）必填；`voiceover` / `clip_generate` 不需要输入视频，不必填。`source` 枚举 `user` / `demo`（v1.2 新增，`input_media_ref` 存在时必填，不得默认 `user`）：需视频的技能无指定素材时采用演示视频，此时 `source=demo` 必须显式标记；演示视频为具名版本化资产，资产 ID 不再登记（v1.3 已取消 V12-03 待确认项）；`source=demo` 的产物不得进入个人资产（§9.8）、回流与分享（§12.2） | PRD §5 |
| `task_params` | object | 是 | 各技能参数，见下表 | PRD §5；BR-01 |
| `status` | string | 是 | 枚举：`submitted` / `running` / `waiting_input`（追问等待）/ `succeeded` / `failed` / `cancelled`；**Workflow 执行状态的任务级投影（唯一事实源与投影表见 `03` §4.5.3；契约测试见 `08` §11）；只由状态投影器写，Agent 与 Workflow 不直接写本字段**（例外：创建时 `submitted`、用户取消时 `cancelled`，均经投影器落盘）；`waiting_input` 对应两类等待（R12-13）：执行前追问（`ask`，尚未提交 plan）与执行侧 NeedsUserAction；慢任务可查询状态；**非 Task 状态机（`03` §3，9 态）的投影** | PRD §8；DR-17；NFR-04 |
| `active` | boolean | 是 | 会话内同一时间仅一个 SkillTask 为 `true`（v1.2 新增，`03` §4.7）：切走时置 `false`——冻结的是**交互态**（不再向该任务路由新输入、不再追问），**执行态仍由投影推进**（Running 中的任务完成时 `status` 可经投影变为 `succeeded` / `failed`，结果回写后不抢焦点）；切回时置 `true`，状态不变继续；取消时置 `false`（`03` §4.7）；切换是原子操作 | BR-01；`03` §4.7 |
| `pending_slot` | string \| null | 否 | 当前追问的待决项（v1.2 新增，`03` §4.7）：槽位名，或 `confirm:<动作>` 形式的执行确认项（如 `confirm:resume`）；不在追问中为 `null`；多槽位缺失时一次只记一个，按提问顺序逐个追问 | BR-01；`03` §4.7 |
| `supplementary_inputs` | array | 否 | 追问中未命中待填槽位的输入，以及命中输入中超出当前槽位的多余内容（v1.2 新增，`03` §4.7 回答判定）：append-only，元素 `{text, at}`；不清除 `pending_slot`，不改变状态；受会话快照 30 条上限约束（PRD §12，见 `07` §7 V12-08） | BR-01；`03` §4.7 |
| `retry_count` | integer | 是 | 已重试次数，初始 0；仅 `error.category=retryable` 时显示重试入口并允许重试（`03` §4.7） | PRD §13；OI-07 |
| `max_retries` | integer | 否 | 配置值，接入时冻结（不得编造数值）；重试策略形状（指数退避 + 配置项次数）见 §10.1 | OI-07 |
| `error` | object | 否 | 失败时必填：`{code, category, message, raw_error?}`；`category` 枚举 `retryable` / `non_retryable`（v1.2 整改 R12-08，与 `04` §10.1 Adapter 返回一致）；原始异常须记录（BR-13 同款口径） | PRD §13；BR-13 |
| `created_at` / `updated_at` | string | 是 | RFC 3339 | §1 |

**各技能 `task_params` / `result`（`result` 挂在 SkillResult 对象上，`skill_task_id` 外键）：**

| 技能 | `task_params`（必填/约束） | `result` | 来源 |
|---|---|---|---|
| 提取字幕 `subtitle_extract` | `video_ref`（是） | `{subtitle_text: string}`——对话返回可复制文字 | PRD §5；AC-03 |
| 配口播 `voiceover` | `text`（是）、`language`（是，目标语种）、`voice`（否，缺音色或文本时试听禁用） | `{audio_ref: string, language: string}`——可原生试听、下载的示例音频 | PRD §5；BR-18；AC-03 |
| 擦除元素 `erase_element` | `video_ref`（是）、`target_description`（是，处理对象） | `{video_ref: string}`——返回处理后视频样例 | PRD §5 |
| 调整画幅 `aspect_ratio` | `video_ref`（是）、`target_ratio`（是，枚举 `9:16` / `1:1` / `16:9`；缺画幅时追问） | `{video_ref: string, ratio: string}`——返回对应画幅样例 | PRD §5 |
| 片段生成 `clip_generate` | `shot_description`（是，需要镜头描述）、`aspect_ratio`（否，默认 `9:16`）、`duration_seconds`（否，默认 `8`，**限制 3–15 秒**，超限拒绝） | `{video_ref: string, duration_seconds: integer, aspect_ratio: string}`——返回视频样例 | PRD §5 |
| 卖点浮层 `selling_overlay` | `video_ref`（是）、`selling_copy`（是，引号中的卖点文案；缺时追问） | `{video_ref: string}`——返回带浮层示例视频 | PRD §5；BR-01 |

追问规则（BR-01）：技能追问未回答时，后续输入补到该任务；切换技能保留正文与附件，当前技能状态只保留一项。追问状态机全文见 `03` §4.7（v1.2 新增，含回答判定、切换、取消、重试与无超时规则）。

**部分完成（v1.2 新增）：** Workflow 终态为 Partial 时 SkillTask 为 `succeeded`，`result.partial=true`，`result.missing_items`（字符串数组）列出缺失项；结果卡须显式标注“部分完成”；`error` 留空（partial 不是失败）。`result` 各技能结构同上表，另加 `partial: boolean`（默认 `false`）、`missing_items: string[]`（`partial=true` 时必填）两个通用字段。

结果呈现（PRD §5）：视频结果完成后保持对话，点击才在右侧打开对应视频，历史结果仍能各自打开；无分段的技能结果保持单视频视图（PRD §8）。状态投影表见 `03` §4.5.3；契约测试见 `08` §11。

### 9.4 MediaActionPlan（声明式媒体动作计划）

来源：覆盖分析 §7.2、§10.1；PRD §8、§17.3 NFR-04。Video Agent 只选择动作、参数和候选，不直接持有媒体执行凭证（覆盖分析 §10.1）；执行由 Media Capability Workflow 完成（API 见 §10）。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `plan_id` | string | 是 | 唯一 ID | 覆盖分析 §10.1 |
| `task_id` / `entry_task_id` | string | 是/否 | 所属 Task；入口任务可溯源 | `03` §2 |
| `actions` | object[] | 是 | 动作列表，见下表；按 `order` 执行 | 覆盖分析 §7.2 |
| `status` | string | 是 | 枚举：`pending` / `running` / `partial` / `succeeded` / `failed` / `cancelled`；**计划级聚合状态，只由聚合器写（v1.2 新增，聚合规则见 `03` §4.5.3 状态投影表；契约测试见 `08` §11）**。聚合产生式（v1.2 整改 R12-12；复核 N2-02 补全，优先级自上而下，穷举全部动作状态组合）：(1) 任一动作 `running` → `running`；Workflow 处于 NeedsUserAction 期间保持 `running`（计划未终结）。(2) 全部动作 `pending` → `pending`（计划已提交未开始）。(3) 任一动作 `pending`（其余动作已终结，无 `running`）→ `running`（执行中混合态：有动作已终结、有动作待执行）。(4) 全部动作 `succeeded` → `succeeded`。(5) 全部动作 `cancelled` → `cancelled`。(6) ≥1 动作 `succeeded` 且 ≥1 动作 `failed` / `skipped` / `cancelled` → `partial`（BR-13 同款口径：失败动作的后续步骤跳过，未开始且无依赖的动作可继续；`missing_items` 列出失败、跳过与取消项）。(7) 0 动作 `succeeded` 且 ≥1 动作 `failed`、其余动作已终结 → `failed`（零产出：计划未交付任何可用结果）。(8) 不可达组合：全 `skipped` 或 `skipped` + `cancelled`（无 `failed`）——`skipped` 须有失败依赖，依赖本身为 `failed`，故不可达；如实现中出现，聚合器须报错而非静默归类。 | BR-13 |
| `progress` | object | 否 | `{completed_actions, total_actions}` | NFR-04 |
| `cancel_reason` | string | 否 | 取消原因 | `03` §3 |

**动作（`actions[]` 单项）：**

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `action_id` | string | 是 | 唯一 ID | 覆盖分析 §7.2 |
| `action_type` | string | 是 | 枚举：`generate_clip`（生成）/`erase_object`（擦除）/`subtitle`（字幕）/`voiceover`（口播）/`change_aspect_ratio`（画幅）/`overlay_selling_point`（浮层）/`bgm`（BGM）/`upload`（上传）/`compose_timeline`（合成）/`export_asset`（导出） | 覆盖分析 §7.2 |
| `params` | object | 是 | 每动作参数（如 `generate_clip` 复用 §9.3 片段生成参数；`compose_timeline` 须 `slot_order`；`export_asset` 须 `asset_refs`） | 覆盖分析 §7.2 |
| `order` | integer | 是 | 执行顺序（从 0 起） | 覆盖分析 §7.2 |
| `depends_on` | string[] | 否 | 依赖的 `action_id` 清单；依赖未成功不得执行 | 覆盖分析 §7.2 |
| `status` | string | 是 | 枚举：`pending` / `running` / `succeeded` / `failed` / `skipped` / `cancelled` | NFR-04 |
| `retry_count` / `max_retries` | integer | 是/否 | 已重试次数；上限为配置值，接入时冻结 | OI-07 |
| `error` | object | 否 | `{code, category, message, raw_error?}`；`category` 枚举 `retryable` / `non_retryable`（v1.2 整改 R12-08，与 `04` §10.1 Adapter 返回一致） | BR-13 |
| `idempotency_key` | string | 是 | 写操作幂等键（`03` §5.4 三层键口径） | `03` §5.4 |
| `result_ref` | object | 否 | 执行结果引用（`video_id` / `clip_id` / `asset_id` / 文件引用） | PRD §8 |

副作用分级：L2 预览、L3 修改、L4 发布继续按 `03` §5 / `03` §8 审批分级控制（覆盖分析 §10.1）；`export_asset` 与外部发布类动作须显式用户确认后方可执行。

### 9.5 EditDecision（槽位编辑决策）

来源：覆盖分析 §6.2、§10.2；PRD §6、§7（BR-21–BR-24）、§12；原始设计 impl_04 §2.1.6 / §15.2.3（EditDecision 指回，见 `07` §5 处置 D10-3——本节为 v1.1 首次落契约，计划侧 Artifact，v1.0 链路止于 MaterialAssignment，见 §4.4）。本对象是 Timeline/EditDecision 投影，与计划侧 ClipRequirement（§4.3）与 Assignment（§4.4）互补，不替代二者。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `edit_decision_id` | string | 是 | 唯一 ID | 覆盖分析 §6.2 |
| `video_id` | string | 是 | 所属成片 | PRD §6 |
| `slot_id` | string | 是 | 槽位 ID（对应 `storyboard_clip_id` 命名空间外的槽位标识；与素材 `clip_id` 不同命名空间，见 §4.2 不变量） | PRD §6；§4.2 |
| `start_ms` / `end_ms` | integer | 是 | 槽位起止时间；`0 <= start_ms < end_ms <= Video.duration_ms` | PRD §17.2 DR-02；§4.2 |
| `slot_type` | string | 否 | 槽位类型；枚举待确认（同 §9.2，OI-02） | DR-02；OI-02 |
| `current_clip` | object | 是 | 当前采用的 Clip：`{entity_type: clip, video_id, clip_id}`；只有点“替换原片段”才写入采用状态（BR-21） | BR-21 |
| `generating` | boolean | 是 | 是否处于生成中；生成结果记录所属成片和槽位，采用后才写入（BR-22） | BR-22 |
| `locked` | boolean | 是 | 用户是否锁定；锁定的 Assignment 不得自动替换（§4.4 规则） | 覆盖分析 §6.2；§4.4 |
| `last_replacement` | object | 否 | 最近一次替换：`{clip_ref, replaced_at, replaced_by}` | 覆盖分析 §6.2 |
| `batch_operation` | object | 否 | 所属批量操作 `{batch_id, slot_ids}`（BR-23） | BR-23 |
| `undo_entries` | object[] | 否 | 撤销栈，**最多 8 条**（BR-23 最近八次批量替换）；每条 `{batch_id, slot_ids, previous_refs, created_at}` | BR-23 |
| `source_slot_id` | string | 否 | 原槽位 ID（衍生关系溯源） | 覆盖分析 §6.2 |
| `slot_prompt` | string | 否 | 槽位级反推提示词（DR-04 槽位各一段） | DR-04 |
| `slot_voiceover` | string | 否 | 槽位级口播文案（DR-05 槽位都有文案） | DR-05 |

批量规则（BR-23）：按当前槽位顺序应用，镜头自身时长不变；候选不可播放时无法采用；提交时重新比对所选镜头，期间有其他修改则提示重新选择；可撤销最近八次批量替换并还原相应槽位。

### 9.6 DerivedVideo（衍生视频）

来源：PRD §7（BR-22、BR-24）、§8、§9、§12；覆盖分析 §6.1、§10.2。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `derived_video_id` | string | 是 | 唯一 ID | PRD §7 |
| `base_video_id` | string | 是 | 基础成片 ID | BR-22 |
| `derivation_type` | string | 是 | 枚举：`slot_compose`（按槽位顺序合成）/`remake`（爆款复刻）/`clip_generate`（片段生成）/`skill_result`（技能结果）/`fission`（视频裂变，BR-19） | BR-24；BR-19；PRD §5 |
| `slot_mapping` | object[] | 条件必填 | `derivation_type=slot_compose` 时必填：`[{slot_id, source_clip_ref}]`，按当前槽位顺序 | BR-24 |
| `status` | string | 是 | 枚举：`generating` / `ready` / `failed`；独立衍生卡仍在生成时不阻塞当前成片的合成判断（BR-24） | BR-24 |
| `compose_check` | object | 否 | 合成前校验快照：`{at_least_one_replaced: boolean, no_slot_generating: boolean, already_composed: boolean}`（见 §11.2） | BR-24 |
| `source_task_id` / `session_id` | string | 是/是 | 来源任务/会话；结果在当前会话和支持的资产任务中显示 | BR-24；PRD §8 |
| `asset_id` | string | 否 | 归档后的 PersonalAsset ID（§9.8） | PRD §8 |

### 9.7 VideoPerformanceSnapshot（投放表现快照）

来源：PRD §6、§17.2 DR-06、§12、§16；覆盖分析 §6.1、§10.2。成片级与槽位级同一结构，`clip_id` 为空表示整片。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `snapshot_id` | string | 是 | 唯一 ID | DR-06 |
| `video_id` | string | 是 | 所属成片 | DR-06 |
| `clip_id` | string | 否 | 为空表示整片；有值表示槽位级 | DR-06 |
| `orders` | integer | 否 | 订单；成片级必填口径见 DR-06（成片有订单和转化） | DR-06 |
| `conversions` | integer | 否 | 转化 | DR-06 |
| `impressions` | integer | 否 | 展示次数 | PRD §5 |
| `clicks` | integer | 否 | 点击次数 | PRD §5 |
| `ctr` | number | 否 | 点击率 | PRD §5 |
| `cost_per_click` | number | 否 | 点击成本 | PRD §5 |
| `cost_per_conversion` | number | 否 | 转化成本 | PRD §5 |
| `conversion_rate` | number | 否 | 转化率 | PRD §5 |
| `retention` | object | 否 | 留存（按秒/分段，口径待确认 OI-02） | PRD §6；OI-02 |
| `window` | object | 否 | `{start, end}` 统计窗口；生产统计周期与归因待确认（OI-06） | PRD §5；OI-06 |
| `source_label` | string | 是 | 来源标识：`sample`（样例）/`simulated`（模拟）/`real`（真实）；报告须保留来源/模拟标识 | PRD §12 |
| `captured_at` | string | 是 | 快照时间 | DR-06 |

规则：槽位级缺失时显示“暂无”，仍可二创（DR-06 原文）；投放满 15 天是广告成片的入库加工门槛（PRD §16）。

### 9.8 PersonalAsset（个人资产）

来源：PRD §10、§16、§17.2 DR-16、§17.3 NFR-10、§17.4 OI-05；PRD §1 G4；覆盖分析 §10.2。本节只定契约落点；v1.0 映射表 `07` §1 中 REQ-E02 仍为“直接冲突→排除”，其处置不变——本对象为 v1.1 新增契约，实施排期与回流生产接入仍待产品方确认（OI-05），见 §13。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `asset_id` | string | 是 | 唯一 ID | DR-16 |
| `owner_user_id` | string | 是 | 创建者；资产按账号隔离 | PRD §16；NFR-06 |
| `task_id` | string | 是 | 来源任务 | PRD §8 |
| `asset_kind` | string | 是 | 枚举：`generated_video` / `derived_video` / `audio` / `copy_text` / `landing_snapshot` | PRD §10 |
| `status` | string | 是 | 枚举：`queued`（排队）/ `generating`（生成中）/ `completed`（完成）/ `failed`（失败） | DR-16 |
| `source_video_id` / `result_video_id` | string | 否 | 原视频 / 结果视频引用（资产详情含原视频、结果视频、分镜与生成提示词） | PRD §10 |
| `prompt_text` | string | 否 | 生成提示词（详情底栏可复制提示词） | PRD §10 |
| `protection_until` | string | 是 | 保护期截止 = 创建时间 + **15 天**；保护期内仅创建者可见、可分享 | PRD §16；NFR-10 |
| `visibility` | string | 是 | 枚举：`owner_only` / `shared`；回流后为 `public`（见下） | NFR-10 |
| `reflow_status` | string | 是 | 枚举：`protected` / `reflowed` / `pending`；15 天保护期后回流公共库 | PRD §16；G4 |
| `source_product_id` | string | 否 | 产出绑定目标商品 ID；生产绑定待确认（OI-11） | REQ-E06；OI-11 |
| `source` | string | 是 | 入库来源标记（v1.2 整改 R12-09）：枚举 `user` / `demo`，取自 `input_media_ref.source`（`04` §9.3）；`source=demo` 的产物**不得入库**——入库校验在持久化前执行，`demo` 请求被拒绝且不产生 PersonalAsset 记录（拒绝记入审计日志，不在 PersonalAsset 表中）；因此 PersonalAsset 表中 `source` 恒为 `user`，枚举保留 `demo` 仅用于拒绝审计记录的来源标注（复核 N1-05） | `04` §9.3；`07` V12-03 |

回流后加工待确认（OI-05：回流后的槽位与提示词补加工待确认）；共享交接待确认（OI-05）。**回流仅处理 `source=user` 的资产**（v1.2 整改 R12-09）：`source=demo` 的产物不进入回流（`reflow_status` 恒为 `protected`，不参与 15 天回流）。

### 9.9 UserPreference / UserMemory（偏好与记忆）

来源：PRD §10、§17.2 DR-13、DR-14；覆盖分析 §8、§10.2；`07` §5 第 17 项（User/Episodic Memory 对象此前无落点，本节补齐）。

**UserPreference：**

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `preference_id` | string | 是 | 唯一 ID | DR-13 |
| `user_id` | string | 是 | 按用户隔离 | DR-13 |
| `scope` | string | 是 | 适用范围（如品类/槽位类型/市场） | DR-13 |
| `key` / `value` | string / object | 是 | 偏好键值 | DR-13 |
| `source` | string | 是 | 枚举：`explicit`（显式设置）/ `implicit`（探针沉淀）；**显式设置优先** | DR-13 |
| `updated_at` | string | 是 | 更新时间 | DR-13 |

**UserMemory：**

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `memory_id` | string | 是 | 唯一 ID | DR-14 |
| `user_id` | string | 是 | 按用户隔离 | DR-14 |
| `content` | string | 是 | 记忆内容（对话写入） | DR-14 |
| `source_ref` | string | 否 | 来源（会话/消息引用） | DR-14 |
| `version` | integer | 是 | 版本号，更新递增 | `07` §5-17 引 04 §6.3 原则 |
| `created_at` / `updated_at` | string | 是 | 时间 | DR-14 |

规则：记忆可改、可删（DR-14 原文）；写入须遵循 `01` §9 的记忆写入六原则（只有经过验证的事实才写入长期记忆；用户显式纠正优先级高于模型推断；记忆要有来源/时间/置信度/版本；更新可审计）。

### 9.10 SessionCanvasProjection（会话画布投影）

来源：PRD §6、§11、§12；覆盖分析 §10.2。**投影不是第二事实源**：会话/任务/Artifact 的权威状态仍在 Task（`03` §2，ADR-07：Task 状态为业务权威）；本投影只读派生，供画布与结果卡渲染；点选与自然语言使用同一套槽位和同一条任务状态（NFR-08）。

| 字段 | 类型 | 必填 | 约束 | 来源 |
|---|---|---|---|---|
| `session_id` | string | 是 | 所属会话 | PRD §12 |
| `canvas_mode` | string | 是 | 枚举：`search_results` / `video` / `follow_landing` / `follow_media`（找片结果/视频画布/跟品落地页/跟品广告素材） | PRD §6；跟品节 |
| `current_video_id` | string | 否 | 当前视频 | PRD §12 |
| `videos` | object[] | 否 | 每视频 `{video_id, slot_states: EditDecision[], result_cards: []}` | PRD §6、§12 |
| `result_cards` | object[] | 否 | 结果卡 `{card_id, video_id, slot_id?, card_type, status}`；卡片操作更新当前会话；切换视频或槽位，已有结果继续挂在对应视频和槽位 | PRD §8、§11 |
| `view_state` | object | 否 | 视图状态（数据概览收起/展开、缩略导航、滚动位置等前端状态；后端只存恢复所需的最小集） | PRD §6 |
| `snapshot_seq` | integer | 是 | 快照序号；会话快照最多 30 条（PRD §12，见 §11.9） | PRD §12 |

恢复规则见 §11.9（BR-26）。

## 10. Media Capability Workflow API（v1.1 新增）

> 来源：覆盖分析 §7.2、§10.1；PRD §8、§17.2 DR-17、§17.3 NFR-04。**未冻结**：本节 4 个端点不在 §2 冻结的 5 个检索类 POST 之列，属 v1.1 新增 API 组，须走资源 API 立项（`07` §5 第 20 项）后冻结；端点命名沿用 §2 风格。执行前按副作用等级确认（`03` §5、§8）；Agent 只提交声明式计划，不直接持有媒体执行凭证。

| 端点 | 方法与路径 | 说明 | 来源 |
|---|---|---|---|
| 提交动作计划 | `POST /v1/media-actions` | 提交 MediaActionPlan（§9.4），异步执行 | NFR-04；DR-17 |
| 查询进度 | `GET /v1/media-actions/{plan_id}` | 返回计划与各动作状态/进度/重试/错误 | DR-17 |
| 取消 | `POST /v1/media-actions/{plan_id}/cancel` | 取消未完成动作；已完成动作保留 | 覆盖分析 §7.2 |
| 重试 | `POST /v1/media-actions/{plan_id}/retry` | 重试失败动作；只清理选中分项的失败标记，成功步骤保留（BR-13 同款口径） | BR-13 |

提交请求字段：`plan_id`（是）、`task_id`（是）、`entry_task_id`（否）、`actions`（是，§9.4 结构）、`Idempotency-Key` 请求头（是，写操作必填，`03` §5.4）。响应：`202 Accepted` + `{plan_id, status, progress}`；查询返回完整计划（含各动作 `status` / `retry_count` / `error` / `result_ref`）。错误映射沿用 §6 的 14 类；耗时任务异步执行（NFR-04），生成中可继续浏览、结果可找回（PRD §1 G3）；刷新后仍能从资产和会话打开（NFR-09，恢复见 §11.9）。Mock：真实媒体服务（调画幅、合成、口播、图像修改）及失败重试契约接入时冻结（不再逐项跟踪，v1.3），Mock 方案为计时器模拟 + 固定样例结果，须在资源 API 立项时冻结，v1.1 不编造 Mock 触发词。

### 10.1 媒体 Adapter 接口契约（v1.2 新增）

> 依据：覆盖分析 §7.2/§10.1；PRD §5、§13、OI-07。本节只定接口形状与错误分类口径，不定服务选型与任何数值；`max_retries`、超时、配额为配置值，接入时冻结，不得编造。Mock 与真实服务共用同一接口（ADR-04 同款口径：Mock 与真实 Adapter 共用 Port / 错误码）。

- **接口（单个动作一次调用）：** `invoke(action, params, idempotency_key, deadline)` → 成功返回 `{artifact_ref}`；失败返回 `{error: {code, category, message, raw_error}}`。`action` 枚举 10 项（§9.4）；`params` 按 §9.3/§9.4 各动作参数；`idempotency_key` 复用 `03` §5.4 公式；`deadline` 由调用方传入，超时为部署配置项，非冻结常量。
- **错误分类（冻结分类，不冻结具体 code 值）：** `retryable`（可重试：超时、429、5xx、瞬时网络）与 `non_retryable`（不可重试：参数校验 4xx、策略拦截、配额耗尽、不支持的动作）。每个 Adapter 实现须在接入时声明其 code → category 映射表并冻结（该映射表为各 Adapter 接入时冻结的附表，不在本文件内——`05` §6.2 AC-03R 所称“映射表”即指此附表）；未声明的 code 默认 `non_retryable`（就高不就低：宁可少重试，不可无限重试）。
- **重试策略形状（冻结形状，不冻结次数）：** 指数退避（首 500ms → 1000ms，形状与 `03` §5.3 相同，次数不同——§5.3 的 2 次是跨域调用口径，不适用于媒体层）；次数为配置项 `max_retries`（接入时冻结）；重试复用原 `invocation_id`，不产生重复 Artifact；重试只清理选中分项的失败标记，成功步骤与人工编辑保留（BR-13 同款口径）；`retryable` 耗尽次数后转 `failed`，`non_retryable` 直接转 `failed` 不重试。
- **按动作逐项迁移（ADR-21）：** 10 个动作各自独立切换 Mock / 真实服务（feature flag 按动作，不搞一次性大切换）；切换不改 MediaActionPlan Schema；切换门禁见下表——有对应技能的动作须通过该技能的 AC-03R 验收，无对应技能的动作按其主验收（`05` §6.2）；切换后 Mock 结果不得再返回。

| 动作 | 切换门禁（验收） | 决策归属 |
|---|---|---|
| `subtitle` / `voiceover` / `erase_object` / `change_aspect_ratio` / `generate_clip` / `overlay_selling_point` | 该技能的 AC-03R（`05` §6.2） | 接入时冻结（按技能） |
| `compose_timeline` / `bgm` | AC-17（合成前校验，`05` §6.2） | 接入时冻结 |
| `export_asset` | AC-13（ZIP 失败降级，`05` §6.2） | 接入时冻结 |
| `upload` | §11.7 上传契约（30 MB 上限、校验失败保留原选用项）+ AC-13 异常证据（上传失败记录与重试） | 接入时冻结 |
- **演示视频不走 Adapter：** `input_media_ref.source=demo` 的输入不调用真实服务，演示视频资产由平台直接提供（§9.3、V12-03）。

## 11. 槽位与跟品契约（v1.1 新增）

### 11.1 槽位状态

槽位的可操作状态由 §9.5 EditDecision 承载；时间轴、提示词、口播入口与数据栏读取关系：槽位数量与时长取素材数据（PRD §6）；跟品三条内置样例各为四个 2 秒槽位（PRD §6 原文）；无槽位的视频保留播放、时间与进度条（PRD §6）；首页技能视频不展示分段轨道和数据概览（PRD §6）。槽位操作菜单：点时间轴镜头选槽位，菜单为“搜相似”“去生成”（PRD §7）；整片搜相似独立于当前时间轴选中项，按本地样例商品、品类、语种和视频类型匹配至多 4 条整片参考（PRD §7 原文）。

### 11.2 合成前校验（BR-24）

点击“合成成片”时校验（PRD §7 BR-24 原文）：(1) 当前成片至少一段已替换；(2) 没有槽位本身处于生成中状态。两者同时满足才创建衍生成片（§9.6 `derivation_type=slot_compose`）。独立衍生卡仍在生成时，当前判断没有统一阻塞合成。同一成片已有合成结果时，当前入口提示已合成。结果在当前会话和支持的资产任务中显示。实际转码、媒体拼接和二次合成策略待接入（BR-24 原文）。验收占位：AC-17（首次提示先替换，采用后生成衍生结果，重复提交提示已有结果）。

### 11.3 做同款 / 爆款复刻参数与人像校验（BR-25、OI-01）

复刻配置（PRD §7）：参考视频与产品、线路/语言、比例、人物、场景、模型、时长、分辨率；换产品或换场景时可补相应参考图；换人物时须从人像库选择或使用上传图。硬性校验（BR-25 原文）：**人像库最多选四位**；当前对话入口的硬性校验集中在人像；共用旧表单分支还有按换项检查参考图的代码，生产统一校验见 OI-01。模型能力、生产配额、各入口参数统一口径待确认（PRD §7、OI-01）。做同款（REQ-C03）与整片复刻（REQ-D01）的生产模型、参数、参考素材校验和配额待确认（OI-01）；本节只定参数与校验契约，不定模型选型。验收占位：AC-12（缺人像参考时提示，确认后留在对话播放样例）。

### 11.4 跟品任务：对象归属 / 任务状态 / 分项失败（BR-11、BR-12、BR-13）

- **对象归属（BR-11）：** 一次确认建立独立会话与任务 ID；来源商品提供原页、口播及诊断资料；任务生成的演示克隆 ID 写入当前版落地页；ZIP 清单的商品 ID 取任务商品，目标国家与平台另存；跨线路或换商品后的真实归属见 OI-11。
- **任务状态（BR-12）：** 待开始尚未创建执行任务；运行中按顺序完成步骤；暂停保存剩余等待时长，继续从未完成步骤恢复；已完成步骤保留；已保存的运行中任务可在重开时接续，暂停的任务等待手动继续。状态复用 Task 状态机（`03` §3）。
- **分项失败（BR-13）：** 落地页、口播、广告文案或视频的某个步骤抛错时，将该分项标为失败、记录原始异常，跳过该分项未完成步骤，其他分项继续；整轮结束若仍有失败，显示对应重试入口；重试只清理选中分项的失败标记，成功步骤和人工编辑保留。`error.raw_error` 字段见 §9.3/§9.4。
- 快跟与定向优化（BR-14）：选择“原素材快跟”时落地页可在诊断后按沿用状态就绪，问题条目标记待优化；点击“按报告优化落地页”后切换落地页处理方式，排入待处理步骤，已完成的口播和视频步骤保留。
- 诊断依据（BR-15）：匹配时使用该商品内置广告、评论与区域行为；未知商品使用模拟来源并标明参考口径；模拟点击率按点击/曝光，模拟转化率按订单/点击；报告按区域呈现点击率和停留时长，区域点击率不相加，修改效果以同条件对照验证。

### 11.5 落地页更新顺序（BR-16）

原版快照始终用于对照；自动优化只更新命中且未手改的当前版图片字段，未命中项沿用，已改价格和图片保留；上传先验证图片与位置，成功后再回填；**撤销可回退最近八步内的页面快照**，恢复图、顺序、状态和价格；同市场沿用来源价格，换市场时试投价格默认待确认，人工已改价格优先（BR-16 原文）。落地页快照对象复用 Artifact Envelope（`03` §8，`landing-page-plan` 类）+ Checkpoint 语义（§5.3）；页面快照撤销栈不在 Checkpoint Schema 内（`07` §1 REQ-F05 行已记），本节只定业务规则，不扩展 Checkpoint 字段。

### 11.6 共享口播与广告文案（BR-17、BR-18）

- **共享（BR-17）：** 沿用模式的中文稿取历史样例；同市场沿用时目标语口播取原稿；跨市场沿用或整套优化时分别取目标语言对应样例；广告标题与广告语从商品卖点和目标市场 CTA 组装；**多个成片读取任务内同一份口播和文案**。
- **更新与试听（BR-18）：** 单侧编辑原文/译文时提示另一侧待同步，口播版本变化会停止旧试听；可恢复上一版或重新生成成对样例；系统语音按文本、目标语种和设备音色试听，缺音色或文本时禁用；试听与文案编辑不会重写视频音轨。
- 共享口播/文案对象复用 `copy-package` Envelope（`03` §8）；版本恢复复用 Artifact 版本语义，不另设版本对象。

### 11.7 成片与 BGM / 音频上传（BR-19）

标准任务装入本地成片样例；裂变新增一个版本，沿用参考片媒体及镜头数据，可独立编辑（§9.6 `derivation_type=fission`）；BGM 可用于全部或指定视频的预览；**音频上传上限 30 MB**，校验失败保留原选用项，实际混音导出待接入（BR-19 原文）。音频文件引用复用 Evidence 引用口径（§2.7：只接受引用，不接受宿主路径）。

### 11.8 跟品资产包 ZIP 下载（BR-20）

会话至少有一项可交付素材且用户点击下载时触发（BR-20）。打包内容：当前版页面、成片、文案、可用音频和其他已就绪素材；同源文件读取复用，重名文件加序号；未就绪、读取失败及槽位替换映射写入清单；失败项不阻止其他素材打包；跟品交付停在下载，真实发布或投放走待确认的生产接口。ZIP 清单 `素材清单.json` 结构见 `08` A-20。验收占位：AC-08（ZIP 含可用文件与清单；试听无文件时有口播稿及说明）。

### 11.9 会话快照与恢复（BR-26、PRD §12）

- **容量（PRD §12 原文）：会话快照最多 30 条；跟品商品/任务各最多 40 条；反馈最多 12 条**（反馈截图长边压至 1000px、JPEG 质量 0.6）。
- **恢复（BR-26）：** 已完成的会话快照可在同一浏览器恢复；首页技能的临时视频引用失效时可回到示例素材；跟品上传按文件引用从本机恢复，未完成的编辑或上传可报中断并允许重试；分享链接要求访问侧已有对应会话快照。
- 生成中的任务刷新后仍能从资产和会话打开（NFR-09）；首页技能未完成的流式任务可接续，过期 blob 视频可退回演示素材；运行中的跟品重开会话时继续；暂停状态等待继续操作（PRD §12）。保留期与跨端恢复待确认（OI-09：旧版 7 天为暂拟值）。

## 12. 反馈扩展、收藏与分享（v1.1 新增）

### 12.1 反馈事件 Schema 与归因上下文

来源：PRD §10、§16、§17.2 DR-15、DR-19、§17.3 NFR-11；覆盖分析 §8。**§2.5 的 9 个反馈事件枚举为冻结值，本节不增删枚举**；下表把 PRD 探针事件映射到冻结枚举或标为“未映射”，与 §2.5 信号—事件映射表同款口径。

| PRD 探针事件 | 映射到冻结枚举（§2.5） | 备注 |
|---|---|---|
| 曝光 | `recommendation.impression` | 曝光上下文无位置字段（待补，见 §2.5） |
| 点击 | `recommendation.clicked` | — |
| 打开 | `recommendation.preview` | 预览开始；`preview.started` 为未来 UI 遥测，不在 v1.0 枚举（见 §2.5） |
| 停留 | 未映射 | 无 `duration` 字段（见 §2.5 预览时长行） |
| 跳过 | 未映射 | 是否等于 `recommendation.rejected` 未定义（见 §2.5） |
| 重搜 | 未映射 | 无对应事件；重搜行为进 DR-19 探针日志 |
| 槽位替换 | `material.replaced` | 由业务状态迁移通过 Outbox 产生（见 §2.5） |
| 采用 | `material.assigned` / `material.final_kept` | 加入项目/实际使用（见 §2.5） |
| 合成 | 未映射 | 无对应事件（见 §2.5 完成导出行）；进 DR-19 探针日志 |
| 下载 | `recommendation.downloaded` | — |
| 分享 | 未映射 | 无对应事件；进 DR-19 探针日志 |

**归因上下文（FeedbackAttributionContext，`08` A-19）：** 每次反馈事件须携带 `{candidate_set_id, position?, strategy_version, session_id, entry_type?, slot_id?, exposure_context}`；已选、已覆盖和排除条件必须出现在反馈归因上下文中（§2.2 规则）；曝光位置、候选集合、上下文、展示时长、策略版本必须保留（§2.5 反馈保留字段清单）。反馈的实时作用（DR-15：实时作用于当次会话）与长期偏好更新（DR-13、DR-19：支撑漏斗、偏好沉淀、热搜词统计）为生产管线依赖：v1.1 只定事件与归因契约，**不规定重排权重数值**（无 PRD 出处，不得编造；权重待 A/B，口径同 §2.2 推荐策略权重“登记为待验证字段”）。

反馈提交（PRD §10）：类型包含功能、数据、体验和新需求；正文必填，可附最多 3 张截图与选填联系方式；附带页面和时间，最多保存 12 条。

### 12.2 收藏与只读分享链接（REQ-E01 契约落点）

来源：PRD §10、§17.4 OI-08；覆盖分析 §9（REQ-E01 未出现在 v1.0 映射表中的缺口，本节补契约落点；映射表本身由 05 组负责）。

| 对象/字段 | 约定 | 来源 |
|---|---|---|
| 收藏（Favorite） | `{favorite_id, user_id, entity_type: video\|clip, entity_id, created_at}`；库卡和视频收藏在本机，可在收藏页或收藏车查看 | PRD §10 |
| 分享链接（ShareLink） | `{share_id, session_id, created_at, expires_at?, access: read_only}`；分享弹窗可复制带会话 ID 的链接，当前只打开已有本地快照；**`source=demo` 的产物不生成分享链接**（v1.2 整改 R12-09） | PRD §10 |
| 待确认 | 跨账号、跨浏览器可访问性和只读授权待确认；有效期待确认 | OI-08 |

## 13. REQ-E01 / REQ-E07 契约落点与 04↔08 对照（v1.1 新增）

### 13.1 REQ-E01、REQ-E07 的契约落点

| REQ | 契约落点（本文件） | 附录落点 | 说明 |
|---|---|---|---|
| REQ-E01 收藏与分享 | §12.2（Favorite / ShareLink） | `08` A-21 | 跨端权限与有效期待确认（OI-08）；映射表由 05 组负责，本节只给契约落点 |
| REQ-E07 行为探针与片段预生成 | §12.1（反馈事件与归因上下文）+ §9.2（推荐场景）+ §9.7（表现快照） | `08` A-19、A-10、A-15 | 探针事件见 §12.1 映射表；预生成片段属 DR-03（成片切片 + 历史 AI 片段 + 预生成片段），以 Clip 形态进入 CandidateSet（§3 不变量不变），预生成触发策略与供给指标待确认（DR-19、G5） |

### 13.2 04↔08 引用对照表（v1.1 新增部分）

| 04 节 | 08 附录 | 对象/内容 |
|---|---|---|
| §9.1 | A-9 | EntryTask |
| §9.2 | A-10 | RecommendedScenario |
| §9.3 | A-12 | SkillTask / SkillResult（六项技能） |
| §9.3 / §9.4 | §11（v1.2 新增） | 状态投影与追问状态机契约测试（T-SM、T-CM） |
| §10.1 | §11.4（v1.2 整改 R12-16 新增） | Adapter 契约测试（T-AD-01–03：错误分类与按动作迁移） |
| §9.4 | A-11 | MediaActionPlan |
| §9.5 | A-13 | EditDecision |
| §9.6 | A-14 | DerivedVideo |
| §9.7 | A-15 | VideoPerformanceSnapshot |
| §9.8 | A-16 | PersonalAsset |
| §9.9 | A-17 | UserPreference / UserMemory |
| §9.10 | A-18 | SessionCanvasProjection |
| §10 | A-11（注） | Media Capability Workflow API（端点契约在 04 §10；A-11 给计划 Schema） |
| §11.2 | A-14 | 合成前校验（BR-24） |
| §11.3–§11.7 | —（无附录正文） | 复刻参数/人像校验（BR-25）、跟品任务（BR-11–13）、落地页更新（BR-16）、共享口播与文案（BR-17/18）、成片与 BGM（BR-19）；契约正文见 `04` §11.3–§11.7 |
| §11.8 | A-20 | 资产包 ZIP 清单 |
| §12.1 | A-19 | 反馈事件与归因上下文 |
| §12.2、§13.1 | A-21 | 收藏/分享；REQ-E01/E07 落点 |

### 13.3 未解决的待对齐项（v1.1，P0 不得直接标排除）

以下按覆盖分析 §10.3 口径保留：原型行为说明 + 待决策问题 + Mock 方案 + Adapter 边界 + 验收占位；确认前不进 Backlog（`07` §5 第 6、8、9 项口径）。

1. **OI-01（做同款/复刻生产参数）：** 原型行为见 §11.3；待决策：生产模型、参数、参考素材校验与配额；Mock：固定样例结果；Adapter 边界：复刻执行走 §10 Media Capability Workflow，不进 Video Agent Tool（`03` §4.2 冻结 8 个不变）；验收占位 AC-12。
2. **OI-02（槽位归因与推荐场景计算）：** 原型行为：槽位级缺失显示“暂无”（DR-06）；待决策：按秒归因口径、推荐场景数据源、`slot_type` 枚举值；Mock：固定样例指标；验收占位 AC-09/AC-10。
3. **OI-03（外部视频二创与深度理解）：** 原型行为：外部视频默认无槽位（DR-10），实时理解、自动切片与深度二创为待确认的生产能力（PRD §9）；待决策：是否允许二创、何时触发深度理解和缓存；Adapter 边界：外部视频以 Video 形态承载，`source_type` 区分来源（§4.1）。
4. **OI-04（动作矩阵与下载口径）：** 原型行为：独立片段/整片/切片/衍生结果的动作随卡片入口变化（PRD §7、§9）；待决策：生产动作矩阵及下载口径；验收占位 AC-13。
5. **OI-05（资产保护期与回流）：** 原型行为见 §9.8；待决策：回流后加工、共享交接；Mock：资产状态四值（DR-16）固定样例；验收占位 G4。
6. **OI-07（真实媒体服务契约，v1.2 曾拆分，v1.3 已移除该拆分）：** 原型行为：技能交付见 §9.3；真实服务及失败重试契约（含 `max_retries` 数值）接入时冻结，不再逐项跟踪；Mock：计时器模拟 + 固定样例；Adapter 边界：§10.1 媒体 Adapter 接口契约（错误分类、重试形状、按动作逐项迁移与门禁表）；验收占位 AC-03（Mock）+ AC-03R（真实服务，`05` §6.2）。
7. **OI-08（收藏/分享权限）：** 见 §12.2。
8. **OI-09（会话保留期与跨端恢复）：** 原型行为见 §11.9；待决策：保留期（旧版 7 天为暂拟值）、跨端恢复、资源续存。
9. **OI-11（商品绑定与旧广告草稿入口）：** 跟品演示 ID 见 BR-11（§11.4）；待决策：未匹配商品生产校验、跨线路商品 ID 绑定、旧广告草稿与预算能力的交付入口；跟品主路径停在下载资产包，不默认走 Ads 草稿/发布（覆盖分析 §7.4）。
10. **新对象冻结程序：** §9–§12 的对象、枚举与 §10 端点均为 v1.1 新增未冻结；字段名、枚举值、提议新增表须经 ADR 立项冻结；Ticket 总数 44（`05` §5）不动。新增 ADR 的规则（v1.2 整改 R12-19）：新增工作**默认不新增 ADR 编号**，挂在既有 ADR 下；确需新增时走新 ADR 评审（05/07 组裁决），编号顺延。**v1.2 执行：** 本条程序已执行——ADR-19–21 经 v1.2 评审立项（`01` §8、`07` §7 V12-06）。
11. **新对象 Mock Fixture（场景 Fixture，评审 C-6 新增登记）：** `04` §9 引言已明示新对象暂无 Mock Fixture（§7 的 4 Video / 9 Clip 不变）；待决策：RecommendedScenario 等新对象的 Fixture 数据集与版本管理；Mock：场景取固定样例预置；验收占位 AC-04/AC-10。
