# 通用检索推荐系统与 Agent 架构设计：最终可实施版 v1.0

> 版本：v1.0 FINAL｜日期：2026-11-14｜状态：**待独立评审通过后生效**（评审报告见 `06_评审与验收报告.md`）
> 原始材料：`/Users/zed-mac/Documents/search-rec-docs/`（15 篇设计文档，约 47 万字节、12,436 行）+ PRD《AI乘风引擎·产品需求文档 v1.4》（2026-11-05，37 页）+ `/Users/zed-mac/Documents/java-examples/`（Acore Runtime Java SDK 0.2.0 示例）
> 本目录位置（本机）：`/Users/zed-mac/Documents/search-rec-docs/final-v1.0/`
> 工作区副本：`~/workspace/search-rec-analysis/final-v1.0/`（与本机版内容一致，以本机版为准）
> **原则：原始文档一字不改。本目录是裁决层 + 冻结值层（评审 R-02 后的降级宣称）：它冻结范围、Schema、数值、排期与验收，冲突时以本目录为准；但它不是全文重写——25 张表的 DDL 全文、JSON Schema 全文、A01–A31 的逐项用例、42 个 Ticket 的完整 DoD 仍在原始文档中，核心正文已移入 `08_附录_核心契约正文.md`，其余以原始文档为准。工程师开工时须同时备有本目录与原始文档。**

## 0. 先说清三件事（读之前必读）

### 0.1 这不是 PRD 的全部产品，这是其中一个后端 Mock-first 切片

原始材料中最严重的 P0 问题是：**PRD 与设计文档不是同一产品的同一阶段。**

- PRD 是面向优化师的端到端产品「AI乘风引擎」：找片、看片、拆段、复刻、二创、全链路跟品，带前端画布、个人资产、500 并发、Q4 上线 MVP。
- 设计文档是后端一个 Mock-first 切片：Video Domain Agent + 跨域编排契约，明确不交付前端、真实检索、媒体执行、真实领域。

**最终版 v1.0 的裁决（冻结，不可再议）：**

| 项 | 裁决 |
|---|---|
| v1.0 交付物 | 仅后端 Mock-first 切片：Video Domain Agent + CreativeProductionWorkflow 跨域编排契约 + URRE Mock Retrieval Port（Search / Recommendation `clip_candidate` 单场景 / Similar）+ PostgreSQL 控制面 + 纵向验收脚本。见 `05_实施路线图_Backlog与验收_最终版.md` §1 |
| 不属于 v1.0 | 前端/工作台/画布、上传/下载/合成/渲染/NLE、真实入库/转码/切片/ASR/OCR/Embedding/索引（ES/Qdrant/Kafka）、真实推荐训练与 A/B、视频生成、版权与许可过滤、生产计费/SLA/容量、个人资产/15 天保护期与回流任务。完整清单见 `05` §1.2 |
| PRD 关系 | v1.0 只覆盖 PRD 需求的一个子集。每一项 PRD P0 需求的处置（覆盖 / 部分 / 排除 / 待确认）见 `07_问题清单与裁决记录.md` §1 的 REQ→Ticket 映射表。**按 v1.0 走完不等于 PRD Q4 MVP 通过；PRD MVP 需另立范围，见 `05` §7** |
| 04 号文档 | `04_开源项目源码解析与设计指南.md` §4「千万级素材系统建议」**仅作阅读材料，不得直接进入 Backlog / Ticket**。任何采纳须经 ADR 裁决并写入 `01` §8 的 ADR 表（记录于 `07` §4）。它的 SearchPlan 示例缺强制字段，照抄通不过 Schema 校验 |

### 0.2 权威顺序（冲突时按此顺序裁决）

1. 本目录 `00_README_最终版说明.md`（范围裁决与冻结值）
2. `01_架构总纲_最终版.md`（架构不变量与 ADR）
3. `02_URRE检索推荐_最终版.md`（检索语义与 Schema v1.0）
4. `03_AgentRuntime与VideoDomainAgent_最终版.md`（Runtime、Agent、跨域编排）
5. `04_API数据契约与存储_最终版.md`（API、Schema、DDL——**字段级权威**）
6. `05_实施路线图_Backlog与验收_最终版.md`（排期、Ticket、验收数值）
7. `07_问题清单与裁决记录.md`（所有 P0/P1/P2 的处置记录）
8. `08_附录_核心契约正文.md`（核心正文附录；与 `00`–`05` 冲突时以 `00`–`05` 为准）

**字段级权威只有一份：`04`。** 其它文档出现字段名、枚举、类型与 `04` 不一致时，以 `04` 为准，视为其它文档的笔误。

### 0.3 文件地图

| 文件 | 内容 | 来源（合并） |
|---|---|---|
| `00_README_最终版说明.md` | 本文件：范围裁决、权威顺序、冻结值总表 | 新增 |
| `01_架构总纲_最终版.md` | 架构不变量、对象模型、路由、Artifact、Tool 治理、安全、ADR（单套编号） | 00 总纲 + 03 VideoDomain |
| `02_URRE检索推荐_最终版.md` | URRE 四类能力、流水线、模型分工、反馈、指标（冻结 Schema v1.0 引用 `04`） | 01 URRE + 05 数据模型（检索部分） |
| `03_AgentRuntime与VideoDomainAgent_最终版.md` | Runtime、Session/Plan/Task/Checkpoint/Artifact、Router、预算、质量门、多 Agent、Video Agent、跨域编排 | 02 Runtime + 03 + impl_04 + impl_07 |
| `04_API数据契约与存储_最终版.md` | 全部 API、JSON Schema、枚举、错误码、DDL、索引、迁移、Mock Fixture | impl_01 + impl_05 + 05（存储部分） |
| `05_实施路线图_Backlog与验收_最终版.md` | 唯一排期（9–13 周）、42 Ticket 修订版、验收数值表、纵向切片 | impl_00 + impl_02 + impl_03 + impl_06 |
| `06_评审与验收报告.md` | 独立评审 BOT 的评审结论与验收勾选表（评审后填写） | 新增，评审 BOT 填写 |
| `07_问题清单与裁决记录.md` | A/B/C 三组全部 P0/P1/P2 问题、处置、REQ 映射、ADR 映射 | 新增 |
| `08_附录_核心契约正文.md` | 状态机、CandidateSet JSON Schema、请求示例、错误码表、完成定义 15 条、A01–A31、Ticket/Sprint 对照、ADR 映射 42 行、索引清单 | 新增（评审 R-02/R-07/R-09 后补写） |

原始文档的交叉引用（`implementation/…`、`C:\Users\Administrator\…`）在本目录中**全部改为相对路径**（`./01_…` 等）或删除。`implementation/` 前缀不再使用。

## 1. 冻结值总表（v1.0 全局冻结，改动须走 ADR）

| 维度 | 冻结值 | 来源/说明 |
|---|---|---|
| 语言与框架 | Java 17 + Spring Boot 3.x；Acore Runtime Java SDK **0.2.0**（`/open/v1`）；PostgreSQL **16** | impl_02 §2；PG 大版本原先未定，现冻结为 16 |
| 不引入（v1.0） | ES / Qdrant / Kafka / Embedding 服务 / Ranker 训练 / FFmpeg / NLE | impl_02 §1–2；真实 URRE 见 `02` §8（门禁） |
| 视频对象 | 只有两级：`Video -> Clip`；`Shot`/`Segment` 一律映射为 Clip，不得再引入 | 00 §4；impl_00 §2 |
| 检索能力 | Search、Recommendation（仅 `clip_candidate` 单场景）、Similar；**Explore 不在 v1.0**（延期，见 `02` §7） | 01 §4；impl_00 §1.1 |
| 检索总预算 | Search / Recommendation `deadline_ms = 8000`；Similar `5000`；SearchPlan `max_latency_ms = 8000` | 05 §8；impl_01 §4.2 |
| 候选预算 | Search `candidate_budget = 100`（v1.0 冻结值；05 的 200 是真实 URRE 草案值，不采用） | `04` §2.1（以此为准，解决 A 组 P0-2） |
| 检索 Top-K（Agent 侧） | 每计划 Clip 保留 shortlist **最多 10** | impl_04 §9（**纠正评审 R-05：** 草稿的“检索侧每节拍 Top-K 默认 5”在 impl_04 全文无依据，现删除；如需该值，须另立设计决策并给出理由） |
| Task 状态 | 9 态：Created / Planned / AwaitingApproval / Running / Waiting / Reviewing / Completed / Failed / Cancelled；**Waiting→Running 恢复边存在**（02 §4.2 原图已有） | `03` §3 |
| waiting_reason | 冻结 4 个：`awaiting_user` / `budget_exhausted` / `awaiting_domain` / `awaiting_approval`；`video_task` 与 `creative_task` 均允许 4 个（修正 DDL CHECK） | `03` §3 |
| 单 Run 预算（默认） | `max_turns=12`、`timeout_seconds=900`、`max_tool_calls=40`、`max_replans=1`、`max_tool_error_streak=2` | impl_04 §6.5（v1.0 唯一单 Run 默认值） |
| 任务级预算 | Planner 调用 ≤20 / 任务；检索工具调用 ≤120 / 任务（按最多 3 个 Run 计）；Critic 修订 ≤2 轮；子 Agent ≤3 / 任务 | `03` §5.2–§5.3 |
| 重试 | 领域调用最多 **2 次**（含首次共 3 次尝试，指数退避 500ms→1000ms）；Critic 修订最多 **2 轮**；三处“2”的口径：重试 2 次、修订 2 轮、连续工具错误 2 轮即停——**三者分别计数，不累计** | `03` §5.3 |
| 质量门阈值 | 80 分（满分 100），换算公式见 `03` §6；低于 80 分进入修订，最多 2 轮，保留最佳版本 | `03` §6 |
| 副作用等级 | L0 只读 / L1 分析 / L2 预览 / L3 修改 / L4 外部副作用；L3 须明确确认，L4 须强审批 + 明确授权 | 02 §7.3 |
| Mock Fixture | 固定：4 Video / 9 Clip（video_001: clip_001–003, clip_008；video_002: clip_003–004；video_003: clip_005–006；video_004: clip_007, clip_009）；**语义相似视觉不同的一对冻结为 clip_003 / clip_004**（补 C 组 P2-2 缺口） | impl_05 §11；`04` §7 |
| 验收数值 | 见 `05` §6 验收数值表（Mock 阶段：确定性、隔离、恢复、延迟均有数值；生产 SLO 不承诺） | `05` §6 |
| 排期 | **唯一排期：9–13 周，阶段 0–6**（见 `05` §2）。impl_03 §4 的 Day 1–10 总计划作废，不再另设 Day 清单 | `05` §2（解决 C 组 P0-3） |

## 2. 术语表（冻结）

| 术语 | 定义 | 不得混用 |
|---|---|---|
| Video | 完整视频资产 | — |
| Clip | Video 内可独立发现和引用的连续片段，唯一片段层级；字段 `clip_id`、`video_id`、`start_ms`/`end_ms`、`preview_ref`、`semantic_summary`、`quality_flags` | Shot、Segment、切片（对照表外不得再用） |
| Storyboard | 叙事结构（计划侧） | — |
| ClipPlan | 执行计划（计划侧） | — |
| ClipRequirement | 计划中的一条目标；字段含 `storyboard_clip_id`（如 `sb_clip_001`）、`duration_target_ms` | 槽位（PRD 术语；映射见 `07` §1，槽位的起止时间/封面在 v1.0 无对应字段，属缺口） |
| MaterialAssignment | 素材候选到计划 Clip 的绑定 | — |
| CandidateSet | 检索返回的候选集合 + 证据；Schema v1.0 见 `04` §3 | — |
| Artifact | 可引用、可版本化的阶段成果；跨域用统一 Envelope，8 类（见 `01` §6） | — |
| Task / Run | Task 是平台侧业务任务聚合；Run 是 Runtime 侧单次执行实例；Task 与 Run 是投影关系，不是同一枚举 | 不得用 Run 状态替代 Task 状态 |
| Plan / Checkpoint | Plan 是任务执行方案（平台自建，无 SDK 原生 API）；Checkpoint 是最小充分恢复状态（平台自建） | 不得说成 SDK 原生能力 |

## 3. 如何用这套文档开工（5 步）

1. 读本文件 §0–§2，确认范围裁决与冻结值。
2. 读 `01`（不变量）+ `04`（字段级权威），再读 `03`（Agent 怎么做）。
3. 按 `05` §2 的阶段 0 开工：契约 + DB + Mock Catalog（1 周），先跑通 `05` §6 的阶段 0 验收表。
4. 每个阶段退出时，按 `05` §6 的数值表逐项勾选，不过不进入下一阶段。
5. 任何对冻结值的改动，先写 ADR（单套编号，见 `01` §8），再改代码与文档；冻结值与代码不一致时，以冻结值为准，代码须改。

## 4. 变更记录（相对原始文档）

| # | 变更 | 原因（问题编号见 `07`） |
|---|---|---|
| C-01 | 新增本文件与 `07`，确立唯一权威顺序与 REQ 映射 | C P0-1、P0-5 |
| C-02 | 冻结 CandidateSet / Search / Recommendation / Feedback 为 Schema v1.0 单一版本（`04`） | A P0-1、P0-2、P0-3、P0-4 |
| C-03 | `waiting_reason` 4 值两表统一；`video_task` CHECK 补齐；Task 状态机按 02 §4.2 原图完整复现（**纠正评审 R-01：** 草稿称“修正 02 图缺失”是误读，02 原图已有恢复边） | B P0-2；C P1-6 |
| C-04 | 冻结预算与质量门数值（单 Run + 任务级 + 重试口径） | B P0-3 |
| C-05 | 降级 java-examples 误引（CallerToolContinuation 等）为“待对源码核验” | B P0-4 |
| C-06 | 排期二选一：保留 9–13 周，作废 Day 1–10 总计划 | C P0-3 |
| C-07 | 验收基线补数值表 | A P0-5；C P0-4 |
| C-08 | ADR 三套并一套，42 个旧编号逐行映射（`07` §4）；`VDA-ADR-01–14` 真实存在于 impl_04 §16，并入单套编号（非删除） | C P1-5 |
| C-09 | Explore 延期；04 §4 隔离；推荐仅 `clip_candidate` 全文档统一 | A P0-6；C P1-1、P1-2 |
| C-10 | 全部交叉引用改为相对路径，删除 Windows 绝对路径 | A §4；C P0-5 |
