# 04 API、数据契约与存储（最终版 v1.0）

> **字段级权威（唯一）。** 其它文档与本文件冲突时，以本文件为准。
> 来源：impl_01 + impl_05 + 05（存储部分），合并后冻结为 Schema v1.0。

## 1. 原则

- 公开 API 只有 5 个检索类 POST + Agent Tool + Events（见 §2）。
- SearchPlan 只作 Agent Tool 输入，**不公开第二套 Search 路径**。
- Mock 与真实 Adapter 的 Schema 版本必须一致（v1.0）；真实版新增字段先作为可选字段加入，待版本路线图明确后再变必填（05 §20.2 规则保留；v1.0→v1.1 的字段路线图在真实 URRE 立项时定，见 §8 与 `07` §5 第 5 项）。
- 所有时间用毫秒（`ms`），所有 ID 用字符串，租户隔离字段 `tenant_id` 必填。

## 2. Public API（冻结）

### 2.1 Search — `POST /v1/search`

请求（冻结字段）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `query` | string | 是 | 查询文本 |
| `channels` | string[] | 是 | 枚举见 §2.4；v1.0 含 `keyword, semantic, visual, attribute, context` |
| `filters` | object | 否 | 只允许注册字段（见 §2.4） |
| `candidate_budget` | integer | 是 | **冻结值 100** |
| `deadline_ms` | integer | 是 | **冻结值 8000** |
| `ranking` | object | 是 | `{strategy_id, strategy_version}`（05 结构为准；`strategy_id` 只在此处出现一次，**不设顶层 `strategy_id` 字段**，原 impl_01 的顶层字段为冗余，现删除） |
| `schema_version` | string | 是 | `1.0` |

响应：CandidateSet v1.0（见 §3）。

### 2.2 Recommendation — `POST /v1/recommend`

请求：`context`（项目上下文）、`strategy_id`（冻结值 `video_mock_clip_fit_v1`）、`objective`（冻结值 `task_fit_then_diversity`）、`covered_storyboard_clip_ids`、`deadline_ms=8000`。
**规则（冻结）：`selected` 与 `covered_storyboard_clip_ids` 必须一致，不一致时 Schema 拒绝。**

### 2.3 Similar — `POST /v1/similar`

请求：`seed_clip_id`、`similarity_targets`（v1.0 冻结值：`semantic` / `visual`；`attribute` / `behavior` / `relation` 为未来值，Mock 不实现）、`deadline_ms=5000`。
**规则：Similar 不返回 Seed 自身。**

### 2.4 枚举与注册字段（冻结）

- `channels` 枚举：`keyword, semantic, visual, attribute, collaborative, context, relation, trend, exploration`（其中 `exploration` 在 v1.0 不返回候选）。
- `filters` 可注册字段（v1.0 清单）：`status`（`available` / `unavailable`）、`duration_ms`（范围）、`video_id`、`tenant_id`。其余字段一律拒绝。
- `availability` 枚举：`available` / `unavailable`（完整枚举，原始文档只举例，现补齐）。
- `capability` 枚举：`search` / `recommend` / `similar` / `evidence` / `feedback`。

### 2.5 Feedback — `POST /v1/feedback`

`event_type` 冻结枚举（点分名，见 `02` §7）：

`recommendation.impression` / `recommendation.clicked` / `recommendation.preview` / `recommendation.saved` / `recommendation.downloaded` / `material.assigned` / `material.replaced` / `material.final_kept` / `recommendation.rejected`

业务名映射见 `02` §7。**未点击 ≠ 负反馈。**

### 2.6 Events（关联键权威）

`request_id`（来自 X-Request-Id）、`trace_id`（Traceparent 派生）、事件名以 §2.5 为准。关联键以本节为准（00 §7 引用 impl_01 §8，现统一为本文件 §2.6）。

## 3. CandidateSet Schema v1.0（冻结）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `candidate_id` | string | 是 | 候选唯一 ID |
| `clip_id` | string | 是 | 素材 Clip ID |
| `candidate_origin` | string（单数） | 是 | 候选来源（冻结为单数；05 的复数 `candidate_origins` 不采用） |
| `score` | number | 是 | RRF 融合分（`score_normalization_version=rrf-v1`） |
| `score_breakdown` | object | 是 | 各通道分；`visual` 可为 null |
| `evidence` | object | 是 | 候选证据（匹配字段、片段位置） |
| `trace.query_version` | string | 是 | 查询版本 |
| `index_manifest_id` | string | 否（Mock 可空） | 真实版必填 |
| `manifest_epoch` | integer | 否（Mock 可空） | 真实版必填 |
| `score_normalization_version` | string | 否（Mock 可空，真实版必填） | 固定值 `rrf-v1` |

RRF 参数冻结：`k=60`。

## 4. Core Artifact（Storyboard / ClipPlan / MaterialAssignment）

- Storyboard：`storyboard_id`、`clips`（`clip_requirements`，**不用 `shots`**）、`duration_target_ms`。
- ClipPlan：`plan_id`、`domain`（`video`）、`hard_filters`、`candidate_budget`（100）、`storyboard_clip_id`。
- MaterialAssignment：`assignment_id`、`project_id`、`storyboard_clip_id`、`clip_id`、`scores`（13 个分项，含 `clip_fit`、`collection_fit`，见 §5.4）、`status`。
- **注意：** Assignment 只有 `project_id`，无产品 ID。PRD REQ-E06（产出归属目标产品 ID）为待确认项（PRD OI-05），v1.0 不加产品 ID 字段；若 PRD 确认，须走 ADR 加字段。

## 5. 存储（PostgreSQL 16，冻结）

### 5.1 基础表（05 §9 的 25 张表，原样保留，补索引与版本）

- PostgreSQL **16**（冻结；原始文档未定大版本）。
- 迁移顺序与版本号：`V1__core_tables` → `V2__urre_tables` → `V3__task_workflow_tables` → `V4__feedback_outbox`；每个迁移可重复执行须幂等。
- **索引补齐（新增）：** 原始 05 DDL 全库仅 1 个 `CREATE INDEX`，现补：租户+实体（`tenant_id, entity_id`）、`manifest_id`、`feedback` 归因（`tenant_id, event_type, created_at`）、`video_task(waiting_reason, status)`、`creative_task(waiting_reason, status)`。完整索引清单见 `08_附录_核心契约正文.md` §5。
- `event_type` 加 CHECK 约束（枚举见 §2.5）。

### 5.2 Plan Schema（平台自建，新增定义）

`plan_id`、`plan_version`、`task_id`、`goal`、`budget`（见 `03` §5）、`tool_scope`（允许的 Tool 列表）、`side_effect_level`（最高等级）、`status`（`draft` / `approved` / `frozen` / `superseded`）、`created_at`、`approved_by`。

### 5.3 Checkpoint Schema（平台自建，新增定义）

`checkpoint_id`、`task_id`、`plan_version`、`step_id`、`artifact_refs`、`budget_remaining`、`created_at`。不存模型内部推理链。

### 5.4 评分公式（冻结）

`clip_fit` 与 `collection_fit` 加权和，权重和为 1；默认值：`clip_fit` 权重 0.7、`collection_fit` 权重 0.3（v1.0 冻结默认值；改动须走 ADR）。
质量分 = 加权和 × 100；80 分为通过线（见 `03` §6）。

### 5.5 跨域持久化

`creative_task` 与 `video_task` 的 `waiting_reason` CHECK 均允许 4 个值（修正 impl_05 §10.2 只允许 2 个的错误）。
`video_feedback_event` 归属阶段 1（修正 impl_03 与 impl_05 的阶段归属不一致）。

## 6. 错误（冻结，14 类逐类映射）

> **纠正（评审 R-08）：** v1.0 草稿的错误码表用了 9 类自编 `category`，与原始 impl_01 §9 的 14 类不符。以下 14 类**以 impl_01 §9 原文为准**，逐类映射 HTTP 状态与 `retryable`（均为 v1.0 冻结值）。

错误体示例（impl_01 §9 原文）：`{request_id, trace_id, code, category, message, retryable, details}`。

| category | HTTP | retryable | 说明 |
|---|---|---|---|
| `validation` | 400 | 否 | 参数校验失败 |
| `authentication` | 401 | 否 | 身份认证失败 |
| `authorization` | 403 | 否 | 无权访问；**跨租户对外返回 `not_found`（404），不返回 403** |
| `policy` | 403 | 否 | 策略拒绝（Tool 权限、副作用等级） |
| `not_found` | 404 | 否 | 对象不存在 |
| `conflict` | 409 | 否 | 同键不同体（幂等冲突） |
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
- Mock 部署：进程内 Mock（impl_02 §3），Fixture 目录与启动校验见 impl_02 §6；启动命令 `make compose-up / migrate / seed-mock / contract-test`（impl_02 §7）。
- 配置示例：`domain_timeout_ms=30000`（领域超时，与检索 8000 分属不同层：8000 约束检索总预算，30000 约束领域调用；前者更严）。

## 8. 版本与兼容

- Schema v1.0；Mock 与真实 Adapter 的 Schema 版本必须一致。
- 新增字段先作为可选字段加入，待版本路线图明确后再变必填；v1.0→v1.1 的字段路线图在真实 URRE 立项时定，见 `07` §5 第 5 项。
