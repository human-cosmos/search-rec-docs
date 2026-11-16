# 通用检索推荐系统与 Agent 架构设计：最终可实施版 v1.0

> 版本：v1.3（2026-11-16 修订：移除三项待决策内容，见 `06` §V1.3）｜初版日期：2026-11-14｜状态：**评审通过（初版 PASS，修订复核见 `06`）**
> **v1.1（2026-11-16）：依据覆盖分析（`mac-copy-20261116/VideoDomainAgent_与PRD原型覆盖分析.md`）+ PRD v1.6 修订本文件。改动摘要：新增 §5（v1.1 修订说明：改动范围、PRD 对齐目标、9 文件分工、阅读路径、Mac 01 滞后注记），§1 验收数值行改为 AC-01～AC-18 为主、A01–A31 为后端切片子集，§4 补 C-13；冻结值未变。**
> **v1.2（2026-11-16）：依据用户对六项技能设计的合理性质疑（三项指摘）重新设计。改动摘要：状态投影契约化（`03` §4.5.3 投影表 + `08` §11 T-SM 契约测试）、追问状态机画全（`03` §4.7 + SkillTask 新字段 + T-CM 契约测试）、技能执行层落地路径（`04` §10.1 Adapter 契约 + 演示视频来源标记 + OI-07 拆分为 OI-07a–g（v1.3 已移除该拆分） + AC-03R 占位）；修正 v1.1“每项独立的任务 Schema”措辞失实；新增 ADR-19–21；Ticket 总数 44、状态机 18 边、CandidateSet Schema、预算、9–13 周排期冻结不动。**
> **v1.3（2026-11-16）：依据用户决定，三项待决策内容不再写入文档：(1) OI-07a–g 服务选型决策跟踪删除，父项 OI-07 保留，状态改为“不再逐项跟踪，具体服务接入时冻结”；(2) 演示视频资产选择（V12-03）取消，不再登记资产 ID；(3) product_id 精确过滤待办取消（02 §3 注记、03 §9.3 尾句、03 §12 登记行删除）。已定设计保留：04 §10.1 Adapter 契约、`input_media_ref.source`、§2.4 冻结清单（4 项）。冻结值未变，详见 `06` §V1.3 与 `work/v1.3-changelog.md`。**
> 原始材料：`/Users/zed-mac/Documents/search-rec-docs/`（15 篇设计文档，约 47 万字节、12,436 行）+ PRD《万镜魔方·产品需求文档 v1.6》（2026-11-13，文本版，535 行；v1.4 图片版 37 页保留为历史，冲突时以 v1.6 为准）+ `/Users/zed-mac/Documents/java-examples/`（Acore Runtime Java SDK 0.2.0 示例）
> 本目录位置（本机）：`/Users/zed-mac/Documents/search-rec-docs/final-v1.0/`
> 工作区副本：`~/workspace/search-rec-analysis/final-v1.0/`（与本机版内容一致，以本机版为准）
> **原则：原始文档一字不改。本目录是裁决层 + 冻结值层（评审 R-02 后的降级宣称）：它冻结范围、Schema、数值、排期与验收，冲突时以本目录为准；但它不是全文重写——25 张表的 DDL 全文、JSON Schema 全文、A01–A31 的逐项用例、42 个 Ticket 的完整 DoD 仍在原始文档中，核心正文已移入 `08_附录_核心契约正文.md`，其余以原始文档为准（25 张 urre 表 + 26 张业务表 DDL 全文仍在原始文档中，指针见 `04` §5.1；其余未逐项指明的内容见 `07` §5 第 12–21 项的分组指引）。工程师开工时须同时备有本目录与原始文档。**

## 0. 先说清三件事（读之前必读）

### 0.1 这不是 PRD 的全部产品，这是其中一个后端 Mock-first 切片

原始材料中最严重的 P0 问题是：**PRD 与设计文档不是同一产品的同一阶段。**

- PRD 是面向优化师的端到端产品「万镜魔方」（原型界面名；对话问候用「乘风智能体」。v1.6，2026-11-13，文本版）：找片、看片、拆段、复刻、二创、全链路跟品，带前端画布、个人资产、约 500 名优化师同时在线（评估 500–1000 峰值）、Q4 上线 MVP。v1.6 沿用 v1.4 的 17 节结构，REQ/OI/DR/NFR 编号与 v1.4 §17 一致；两者冲突时以 v1.6 为准。v1.4 的逐步审批、按卖点手动查投放视频、按线路创建预算广告草稿属于旧流程，已废止（v1.6 OI-11），不进入 v1.0。
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

**引用规范（2026-11-16 补录，源 `04` §1.2）：** 阅读开源项目与外部资料时，必须区分三级证据——（1）代码已实现：可在仓库具体文件、函数、接口或测试中找到；（2）项目文档声明：README、架构文档或论文描述，但尚未逐项核对实现；（3）本文设计建议：为适配目标业务而提出的方案，不代表参考项目已经实现。正式选型前应固定 commit SHA，并对关键路径做本地源码复核；不把 GitHub Star 数当成技术成熟度或生产可用性的证明。

### 0.3 文件地图

| 文件 | 内容 | 来源（合并） |
|---|---|---|
| `00_README_最终版说明.md` | 本文件：范围裁决、权威顺序、冻结值总表 | 新增 |
| `01_架构总纲_最终版.md` | 架构不变量、对象模型、路由、Artifact、Tool 治理、安全、ADR（单套编号） | 00 总纲 + 03 VideoDomain |
| `02_URRE检索推荐_最终版.md` | URRE 四类能力、流水线、模型分工、反馈、指标（冻结 Schema v1.0 引用 `04`） | 01 URRE + 05 数据模型（检索部分） |
| `03_AgentRuntime与VideoDomainAgent_最终版.md` | Runtime、Session/Plan/Task/Checkpoint/Artifact、Router、预算、质量门、多 Agent、Video Agent、跨域编排；v1.2：§4.5.3 状态投影表、§4.7 追问状态机 | 02 Runtime + 03 + impl_04 + impl_07 |
| `04_API数据契约与存储_最终版.md` | 全部 API、JSON Schema、枚举、错误码、DDL、索引、迁移、Mock Fixture；v1.2：§9.3 SkillTask 新字段、§10.1 Adapter 契约 | impl_01 + impl_05 + 05（存储部分） |
| `05_实施路线图_Backlog与验收_最终版.md` | 唯一排期（9–13 周）、44 Ticket 修订版、验收数值表、纵向切片 | impl_00 + impl_02 + impl_03 + impl_06 |
| `06_评审与验收报告.md` | 独立评审 BOT 的评审结论与验收勾选表（评审后填写） | 新增，评审 BOT 填写 |
| `07_问题清单与裁决记录.md` | A/B/C 三组全部 P0/P1/P2 问题、处置、REQ 映射、ADR 映射 | 新增 |
| `08_附录_核心契约正文.md` | 状态机、CandidateSet JSON Schema、请求示例、错误码表、完成定义 15 条、A01–A31、Ticket/Sprint 对照、ADR 映射 50 行、索引清单 | 新增（评审 R-02/R-07/R-09 后补写） |

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
| CandidateSet v1.0 | 顶层与条目两级字段表见 `04` §3（2026-11-16 补录，按 impl_01 §5 恢复；Video 候选与 Clip 候选均可表示） | `04` §3；impl_01 §5 |
| Artifact Envelope 8 类 | `campaign-brief`、`workflow-plan`、`product-context`、`landing-page-plan`、`copy-package`、`video-creative-artifact`、`ads-draft`、`review-package`（2026-11-16 补录，按 impl_07 §6.2 恢复；初版的 `product-brief`、`landing-page-package`、`video-plan`、`clip-assignment` 为无来源改写，现废止） | impl_07 §6.2；`01` §6 |
| Agent Tool 8 个 | `get_project_context`、`search_video_materials`、`recommend_video_materials`、`find_similar_materials`、`resolve_evidence`、`create_artifact_draft`、`assign_materials`、`request_user_confirmation`（2026-11-16 补录，按 impl_01 §7 恢复；初版的 `search_clips`/`recommend_clips`/`similar_clips`/`get_clip_detail`/`create_storyboard`/`create_clip_plan`/`assign_material` 为无来源改名/拆分，现废止） | impl_01 §7（= impl_04 §10.2 = impl_05 §9.2）；`03` §4.2 |
| 验收数值 | 见 `05` §6 验收数值表（Mock 阶段：确定性、隔离、恢复、延迟均有数值；生产 SLO 不承诺）；**v1.1 验收口径：A01–A31 保留作后端切片验收子集（`05` §6.1），AC-01～AC-18（PRD §14）成为主验收，AC 细节见 `05` §6.2** | `05` §6 |
| 覆盖率 80–85%→约 95% | 评测目标（v1.6 §16 原文核实；v1.4 图片版时未核实，现以 v1.6 文本为准）。真实检索指标，**不在 v1.0 验收范围** | `02` §9 |
| 排期 | **唯一排期：9–13 周，阶段 0–6**（见 `05` §2）。impl_03 §4 的 Day 1–10 总计划作废，不再另设 Day 清单 | `05` §2（解决 C 组 P0-3） |

## 2. 术语表（冻结）

| 术语 | 定义 | 不得混用 |
|---|---|---|
| Video | 完整视频资产；字段见 `04` §4 | — |
| Clip | Video 内可独立发现和引用的连续片段，唯一片段层级；字段（13 个，与 `04` §4 逐字一致）：`clip_id`、`video_id`、`start_ms`、`end_ms`、`duration_ms`、`preview_ref`、`keyframe_ref`、`semantic_summary`、`tags`、`quality_flags`、`availability`、`feature_version`、`model_versions` | Shot、Segment、切片（对照表外不得再用） |
| Storyboard | 叙事结构（计划侧） | — |
| ClipPlan | 执行计划（计划侧） | — |
| ClipRequirement | 计划中的一条目标；字段（8 个，与 `04` §4 逐字一致）：`storyboard_clip_id`（如 `sb_clip_001`）、`narrative_role`、`visual_goal`、`duration_target_ms`、`hard_constraints`、`soft_preferences`、`fallback_requirements`、`evidence_requirements` | 槽位（PRD 术语；映射见 `07` §1，计划侧 ClipRequirement 无起止时间／封面字段，属缺口；资产侧 Clip 已有 `start_ms`／`end_ms`／`preview_ref`，见 `04` §7） |
| MaterialAssignment | 素材候选到计划 Clip 的绑定；字段见 `04` §4（含 `entity_ref` 与 `status` 枚举） | — |
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
| C-08 | ADR 四套并一套，50 行（ADR/IMPL-ADR/VDA-ADR 各 14 行 + XDA-ADR 8 行，`07` §4）；`VDA-ADR-01–14` 真实存在于 impl_04 §16，并入单套编号（非删除） | C P1-5 |
| C-12 | **2026-11-16 覆盖核查补录修订（见 `work/coverage-audit-2026-11-16.md` 与 `work/remediation-dispositions.md`）：**（1）CandidateSet 字段恢复（impl_01 §5，字段表见 `04` §3）；（2）Artifact Envelope 8 类恢复（impl_07 §6.2）；（3）Agent Tool 8 个恢复（impl_01 §7）；（4）评分 13 项与子权重（impl_04 §9，顶层权重仍冻结 `clip_fit` 0.7 / `collection_fit` 0.3）；（5）MaterialAssignment `entity_ref` 与 `status` 枚举（impl_00 §3.3 / impl_01 §3.3，见 `04` §4）；（6）Search `strategy_id` 冻结为 `video_mock_hybrid_v1`、`strategy_version` 为 `1.0`（strategy_id 源 impl_05 §6.1；strategy_version 源 05 §8.1，05 §8.1 的 `video-hybrid` 未采纳）；（7）XDA-ADR-01–08 并入 ADR 映射，共 50 行（impl_07 §2）；（8）V1–V4 迁移分配表（新增裁决，见 `04` §5.1：V1 业务核心表 17 张、V2 URRE 表 23 张、V3 Task/Workflow 表 8 张、V4 反馈/Outbox 3 张，合计 51 张）；（9）Sprint 错位修正：VDA-032（阶段 1）→S2、VDA-031（阶段 5）→S7、S5 只留 VDA-025–026；（10）阻断项 12→15（impl_06 §11 实测 15 条）；（11）状态机边数 17→18；（12）公开 API“5 个检索类 POST”修正，新增 Evidence Resolve（`POST /v1/evidence/resolve`，源 impl_01 §4.5，见 `04` §2.7）；（13）Plan Schema 补 `constraints`、`steps`、`acceptance_criteria` 字段（02 §4.1，见 `04` §5.2）；（14）SearchPlan Schema（impl_01 §4.2 / impl_05 §8.3，见 `04` §2.8）；（15）Intent Schema 最小字段集（源 04 §4.3，见 `01` §4）；（16）`00` §0.2 新增“引用规范”（三级证据 + 固定 commit SHA + 不把 Star 数当成熟度，源 04 §1.2）；（17）`availability` 枚举补齐 `unavailable`（最终版新增冻结值，原始文档只举例 `available`）。**本轮补录/恢复原文已有内容并修正事实错误；新增冻结值仅（6）与（17）两项。** | 覆盖核查 |
| C-09 | Explore 延期；04 §4 隔离；推荐仅 `clip_candidate` 全文档统一 | A P0-6；C P1-1、P1-2 |
| C-10 | 全部交叉引用改为相对路径，删除 Windows 绝对路径 | A §4；C P0-5 |
| C-11 | **2026-11-16 修订，对齐 PRD v1.6（2026-11-13 文本版）：** PRD 引用从 v1.4 图片版改为 v1.6；`07` §1 补 REQ-A02–A05、C07、F01–F07 与 NFR-03/04/07–11，`07` §5 关闭第 7 项（覆盖率引用已核实）并补 OI-02–04/06–08/10–13；`04` §4 REQ-E06 待确认项由 OI-05 更正为 OI-11；`03` §3/§8 补 BR-12/BR-13 映射，`02` §3 补 BR-03 语义规则；`05` §7 里程碑按 v1.6 §17.5 核实。**Schema、预算、状态机、排期、ADR、Mock Fixture 均未变。** 独立评审 R2-01–R2-13（1 P1 + 9 P2 + 3 P3）已按清单整改，均为单行文字修正（见 `06` 修订记录）。 | PRD v1.6 |
| C-13 | **2026-11-16 v1.1 修订（依据覆盖分析 + PRD v1.6；本文件与 `01` 由 00/01 组修订，其余文件由各组修订）：**（1）`00` 新增 §5（v1.1 修订说明：改动范围、PRD 对齐目标、9 文件分工、阅读路径、Mac 01 滞后注记）；（2）`00` §1 验收数值行与 `01` §1 验收口径改为 AC-01～AC-18 为主、A01–A31 为后端切片子集（AC 细节见 `05` §6.2）；（3）`01` 新增 §10（Video Agent 窄边界与 Media Capability Workflow，覆盖分析 §7.1/§7.2/§10/§10.1；8 Tool 不变，新增声明式 MediaActionPlan，Agent 不持媒体执行凭证，L2/L3/L4 分级不变）、§11（四入口显式路由映射，覆盖分析 §7.3；R0–R4 判定条件不变）、§12（六项技能一等公民，PRD §5 BR-01；片段生成默认 9:16、8 秒、3–15 秒）、§13（性能与容量锚点，PRD §16/§17.3/§17.5，数字原样引入）；（4）`01` INV-07 释义补 MediaActionPlan 交接。**冻结值（状态机 18 条边、CandidateSet Schema、预算、Ticket 总数 44、ADR-01–ADR-18）未变；新增数字全部引 PRD 章节，无编造。** | 覆盖分析 |

## 5. v1.1 修订说明（2026-11-16）

> 依据：覆盖分析（`mac-copy-20261116/VideoDomainAgent_与PRD原型覆盖分析.md`，2026-11-16）+ PRD v1.6（2026-11-13，535 行）。v1.1 只做增量修订：保持 9 文件结构与编号体系，不删除 v1.0 已有内容；冻结值（状态机 18 条边、CandidateSet Schema v1.0、预算、Ticket 总数 44、ADR-01–ADR-18 单套编号）一律保留，未动；新增数字全部引 PRD 章节，无编造。

### 5.1 改动范围（本文件，00/01 组）

- `00`：文件头 v1.1 版本注记、§1 验收数值行（验收口径）、§4 补 C-13、本 §5。
- `01`：文件头 v1.1 版本注记、§1 验收口径与 v1.1 架构层新增说明、INV-07 释义补 MediaActionPlan 交接、新增 §10–§13。
- 本组只改上述两个文件，不碰 `final-v1.0/`、不碰 Mac 上的任何文件、不写回 Mac。

### 5.2 PRD 对齐目标

- 把覆盖分析的缺口补进总纲：Video Agent 窄边界与 Media Capability Workflow（覆盖分析 §7.1/§7.2/§10/§10.1，`01` §10）、四入口显式路由映射（覆盖分析 §7.3，`01` §11）、六项技能一等公民（覆盖分析 §2.3，`01` §12）、性能与容量锚点原样引入（PRD §16/§17.3/§17.5，`01` §13）。
- 验收以 PRD AC-01～AC-18 为主（PRD §14；覆盖分析 §9、§10.3），A01–A31 保留作后端切片验收子集。
- 明确边界：Media Capability Workflow 与技能任务是 v1.1 架构层新增的设计对象，不改变 v1.0 Mock-first 交付范围（§0.1、`05` §1.2 仍有效）；其实现 Ticket 与排期由 05 组裁决。PRD Q4 MVP 仍不在本排期覆盖范围（`05` §7）。

### 5.3 九文件分工（v1.1，按任务书）

| 文件 | v1.1 分工 | 状态 |
|---|---|---|
| `00_README_最终版说明.md` | 本文件：范围、分工、阅读路径、验收口径（本 §5） | 本组已改 |
| `01_架构总纲_最终版.md` | 总纲：窄边界、四入口、六技能、性能锚点、验收口径（§10–§13） | 本组已改 |
| `02_URRE检索推荐_最终版.md` | 02 组在该文件中说明，本文件不代述（核对时 02 v1.1 相对 v1.0 有改动，内容由 02 组负责） | — |
| `03_AgentRuntime与VideoDomainAgent_最终版.md` | MediaActionPlan 与 Media Capability Workflow 编排语义（§4.5）、四入口显式路由映射（§4.3）、六项技能 Agent 侧编排（§4.6）、槽位交互（§9）、跟品链路纠正（§10）、会话快照与恢复（§11）、待对齐引用登记（§12） | 03 组已写入（核对时 03 v1.1 为 §1–§12） |
| `04_API数据契约与存储_最终版.md` | MediaActionPlan / SkillTask / 入口任务模板的契约 Schema 与字段；MediaActionPlan 的 Envelope 归属裁决 | 已落定：新对象见 `04` §9.1–§9.10、Workflow API 见 `04` §10；03 §4.5.2→`04` §9.4、§4.6→`04` §9.3（合稿已纠正，原占位 `04` §4.6/§4.7 作废） |
| `05_实施路线图_Backlog与验收_最终版.md` | AC-01～AC-18 主验收细节与追溯链（§6.2）、v1.1 新增工作挂接表（§5.1）、REQ-E01/E07 补遗（§6.3）、性能与容量锚点（§9） | 05 组已写入 §5.1/§6.2/§6.3/§9；OI-01–13 逐项占位（§8）编写时未写入，待 05 组补齐 |
| `06_评审与验收报告.md` | 评审 BOT 填写 | — |
| `07_问题清单与裁决记录.md` | Mac 01 滞后问题正式记账 | 07 组已记账：`07` §6 V11-31 |
| `08_附录_核心契约正文.md` | 08 组在该文件中说明，本文件不代述（核对时 08 v1.1 相对 v1.0 有改动，内容由 08 组负责） | — |

### 5.4 阅读路径

1. 读本文件 §0–§2 + §5，确认范围裁决、冻结值与 v1.1 改动。
2. 读 `01` §10–§13（v1.1 新增总纲内容），再读 `01` §1–§9（不变量与 ADR）。
3. 细节：媒体执行接线见 `03` §4.5/§4.6、入口映射见 `03` §4.3、槽位与跟品见 `03` §9–§10；契约字段见 `04` §9–§13（v1.1 新增，已落定）；主验收见 `05` §6.2、挂接表见 `05` §5.1、性能锚点见 `05` §9。
4. 工程师开工时仍须同时备有本目录与原始文档（见文件头原则）。

### 5.5 Mac 01 滞后注记

Mac `final-v1.0/01_架构总纲_最终版.md`（9,222 B / 113 行）滞后于工作区 `final-v1.0/01`（13,776 B / 151 行）；v1.1 的 01 同时取代两者。该问题由 07 组正式记账（`07` §6 V11-31），本文件与 `01` 仅作注记，不写回 Mac。
