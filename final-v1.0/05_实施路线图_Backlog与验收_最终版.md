# 05 实施路线图、Backlog 与验收（最终版 v1.0）

> 权威顺序第 6 位。排期、Ticket、验收数值以本文件为准。
> 来源：impl_00 + impl_02 + impl_03 + impl_06。

## 1. 交付范围（冻结）

### 1.1 交付

通用 Video Domain Agent（意图、检索规划、Storyboard、ClipPlan、素材分配）+ CreativeProductionWorkflow 跨域编排（Product / Landing Page / Copy / Ads 契约 + Mock / Adapter）；对象模型冻结为 Video→Clip 两级；Mock-first，Fake Catalog / Search / Recommendation / Similar / Evidence（检索网关名 `FakeRetrievalGateway`，源 05 §20.1）+ 跨域 Fake（Product / Landing / Copy / Ads）。

### 1.2 不交付（冻结清单，三处统一版）

前端/工作台/对话页面/画布/上传与前端交互；真实领域实现与外部平台；真实入库/转码/切片/ASR/OCR/Embedding/索引（ES/Qdrant/Kafka）；真实推荐训练与 A/B；视频生成/渲染/导出/NLE；版权、许可、商业用途、地域可用性、署名、**Provenance**过滤；生产多租户计费、SLA、容量规划与大规模运维；个人资产/公共素材库/15 天保护期与回流任务；跟品工作台、落地页对照编辑、资产包 ZIP 导出（产品侧）；互联网素材来源（04 §4.1 提及的设计目标，v1.0 明确排除）。
（修正 00 §1 漏 Provenance、漏画布/上传的问题；以本清单为准。）
**v1.4 旧流程已废止，不进入 v1.0：** 逐步审批、按卖点手动查投放视频、按线路创建预算广告草稿（v1.6 OI-11）。

### 1.3 完成定义（15 条，原 impl_00 §6 原文）

完整 15 条见 `08_附录_核心契约正文.md` §4。完成定义的判定以 §6 验收表为准。

## 2. 实施路线图（唯一排期，冻结）

> 原始文档两套排期冲突：§2 各阶段合计 **9–13 周**，§4 Day 计划合计 **20 个工作日≈4 周**，且 Day 9–10 要求的事与阶段 3+4（3 周）相同。**最终版裁决：保留 9–13 周，Day 1–10 总计划作废，不再另设 Day 清单（与 `00` §1 一致）；Day 计划的日粒度排序内容（Day 1–10 与跨域 Day 1–10，源 impl_03 §4）仅作参考，不作为排期依据。**

| 阶段 | 内容 | 周期 | 退出标准（数值版，见 §6） |
|---|---|---|---|
| 0 | 契约 + DB + Mock Catalog | 1 周 | §6 S0 |
| 1 | Mock 检索（Search / Recommend / Similar） | 1–2 周 | §6 S1 |
| 2 | Runtime + Agent | 1–2 周 | §6 S2 |
| 3 | Creative Workflow 与 Assignment | 2 周 | §6 S3 |
| 4 | Video Baseline Eval 与交付 | 1 周 | §6 S4 |
| 5 | 跨域契约与 Mock 领域 | 1–2 周 | §6 S5 |
| 6 | 主 Workflow 与跨域验收 | 2 周 | §6 S6 |
| **合计** | | **9–13 周** | |

- 无日历锚点：开始日期由项目启动时填入（T0），各阶段按 T0+周数推算；PRD 里程碑（11 月内测、12 月小范围、Q4 交付）**无法对应到本排期**，因为 PRD 是另一产品阶段的产品里程碑（见 `00` §0.1 与 `07` §1）。
- 阶段依赖：阶段 4 的 Eval 在跨域之前，阶段 6 须重跑阶段 4 的固定集（回归责任：阶段 6 退出时，Video-only 回归全部通过 + 跨域用例全部通过；触发条件：每次共享契约变更 + 每阶段退出时）。

## 3. 工作包（WP1–WP12，依赖补齐）

WP1 契约、WP2 控制面、WP3 Mock Catalog、WP4 Mock 检索、WP5 Runtime 接入、WP6 Agent、WP7 Workflow、WP8 Assignment、WP9 Eval、WP10 跨域契约、WP11 Mock 领域、WP12 主 Workflow 与验收。
依赖：WP4 依赖 WP1/WP3；WP6 依赖 WP5；WP8 依赖 WP4/WP6；WP9 依赖 WP8；WP10 依赖 WP1；WP12 依赖 WP7/WP10/WP11。
（原始文档无依赖标注，现补齐。）

### 3.1 原文 WP 与最终版 WP 映射表（2026-11-16 补录）

原文 WP 名以 impl_03 §3 为准。原文 WP 与最终版 WP 同名不同义，以本表映射为准；“原样保留”的表述作废。

| 编号 | 原文 WP（impl_03 §3） | 最终版 WP（本文件 §3） |
|---|---|---|
| WP1 | Domain Contract（Video/Clip、Creative IR、SearchPlan） | 契约 |
| WP2 | Mock Retrieval（同一 `RetrievalGateway` 上的 Search、Recommendation、Similar 与 Feedback） | 控制面 |
| WP3 | Mock Evidence（固定证据和预览引用） | Mock Catalog |
| WP4 | Runtime（AgentSpec、Run、Action、SSE） | Mock 检索 |
| WP5 | Agent（Prompt、Tool、澄清、预算） | Runtime 接入 |
| WP6 | Workflow（Task、Step、Checkpoint、Recovery） | Agent |
| WP7 | Composition（shortlist、评分、Assignment） | Workflow |
| WP8 | Evaluation（Agent Eval、故障注入） | Assignment |
| WP9 | Cross-domain Contract（DomainInvocation、Artifact Envelope、领域状态） | Eval |
| WP10 | Mock Domains（Product、Landing Page、Copy、Ads） | 跨域契约 |
| WP11 | Creative Workflow（依赖图、并行、fan-in、stale、审批和恢复） | Mock 领域 |
| WP12 | Cross-domain Eval（领域失败、部分成功、审批和双路径回归） | 主 Workflow 与验收 |

## 4. 技术选型与部署（冻结）

- Java 17 + Spring Boot 3.x + Acore SDK 0.2.0 + PostgreSQL 16；不引入 ES/Qdrant/Kafka/Embedding/Ranker/FFmpeg。
- 部署单元：app + postgres；Mock 进程内。
- 本地启动：`make compose-up / migrate / seed-mock / contract-test`；配置示例 `domain_timeout_ms=30000`、`max_domain_retries=2`。
- Java / Python 边界：本次全部 Java；Python 仅用于离线评估脚本（不进入服务）。

### 4.1 健康检查与启动（2026-11-16 补录）

- 健康检查端点：`/health/live`、`/health/ready`，不使用 `/api/v1` 前缀（源 impl_02 §7）。
- Ready 检查 5 项（源 impl_02 §7）：PostgreSQL 可连接；Migration 完整；Mock Fixture hash 正确；AgentSpec 配置存在；可选 Runtime 环境契约可读取。
- 启动完成条件（源 impl_06 §3.2）：`/health/live` 返回 200；`/health/ready` 检查 DB 和 Mock Adapter；Mock Fixture 版本为 `video-clip-v1`；Video Domain AgentSpec 版本已记录；Product、Landing Page、Copy、Ads 四个领域 Adapter 均报告 `ready`；CreativeProductionWorkflow 版本已记录。
- 其余 make 目标（源 impl_02 §7 / impl_06 §3.2）：`make integration-test`、`make eval-fast`、`make e2e-slice`（另见本文件 §4 本地启动的 `compose-up` / `migrate` / `seed-mock` / `contract-test`）。

### 4.2 工具清单与测试拓扑（2026-11-16 补录）

- 工具清单（源 impl_06 §3.1）：JDK 17+、Maven、Docker / Docker Compose、PostgreSQL Client、curl、jq；不要求 FFmpeg、Qdrant、Elasticsearch、Kafka 或前端 Node 服务。
- 测试拓扑（源 impl_06 §2）：首轮优先使用 `FakeAcoreRuntime`；第二轮在目标环境验证真实 Runtime SDK 的认证、AgentSpec、Run、Action 和 SSE。
- 技术栈明细（源 impl_02 §2）：Schema 用 JSON Schema + OpenAPI；Migration 用 Flyway 或 Liquibase；测试用 JUnit 5 + Testcontainers；Mock Runtime 用 SDK `FakeAcoreRuntime`；Mock 数据为版本化 JSON Fixture；可观测性用 OpenTelemetry + 结构化日志；本地环境用 Docker Compose。

### 4.3 模块边界与 Monorepo 依赖禁令（2026-11-16 补录）

模块边界 8 条（源 impl_02 §4）：

1. `video-domain-core` 不依赖 Spring、SDK 或 Mock。
2. `runtime-sdk-adapter` 不依赖视频领域对象。
3. `creative-workflows` 只依赖 `DomainInvocationPort` 和跨域 Artifact 契约，不依赖领域内部 DTO。
4. `video-agent` 不依赖 Product、Landing Page、Copy 或 Ads 模块。
5. Video Workflow 可被主 Workflow 调用，不能反向调用主 Workflow。
6. `video-agent-tools` 只通过已注册 Port（可经 `retrieval-client` / `project-client` 封装）和 contracts 访问，不得直连 SDK、Fixture 或数据库。
7. `mocks` 只实现 Port，不调用 Agent。
8. Tool handler 必须经过 Registry 和 Policy。

Monorepo 依赖禁令 7 条（源 impl_05 §3.1；与上述边界部分重叠者为同一规则在两处原文的表述）：

1. 禁止 `video-domain-core` 依赖 SDK 或 Mock。
2. 禁止 Mock Adapter 直接调用 Agent 或写项目数据库。
3. 禁止 Agent 直接连接数据库、Fixture 或文件系统。
4. 禁止 Retrieval 反向依赖视频 Workflow。
5. 禁止 `video-agent` 依赖 Product、Landing Page、Copy 或 Ads 模块。
6. 禁止领域 Adapter 依赖主 Workflow 状态或读取其他领域数据库。
7. 禁止跨域领域把内部 DTO 返回到主 Workflow。

## 5. 研发 Backlog（44 Ticket，修订版）

VDA-001–030（P0 契约基建 8 个、P1 检索 Mock 7 个、P2 Agent/Workflow 9 个、P3 Composition/交付 6 个）+ CDO-001–012（跨域 12 个）+ 新增 VDA-031/032，共 **44 个**（评审 R-04 纠正：草稿称 42 个又新增 2 个，总数未更新）。
**修订（相对原始 impl_05 §13–14）：**

1. **补依赖与估算占位：** 每个 Ticket 须在开工前补依赖（前置 Ticket）与估算（人日），DoR 增加“依赖已明确、估算已填”两项；本文件不编造估算数值（原始文档无估算，现不虚构）。DoR 9 条与 DoD 12 条原文见 impl_05 §15–§16；本文件新增 DoR 两项（依赖已明确、估算已填）。
2. **补缺失 Ticket：** 新增 VDA-031「阶段 5 退出检查：Video Agent 无任何跨域 Tool 或依赖」（认领 impl_03 阶段 5 的检查项，原无 Ticket）；新增 VDA-032「Similar 不返回 Seed 自身」（认领阶段 1 退出标准，原 VDA-013 的 DoD 是另一验收）。
3. **Sprint 修正：** 原 S5 横跨阶段 3–4，现拆分。Sprint 数由 7 改为 8，**阶段 3 拆为两个 Sprint（S4/S5），其余阶段各一个 Sprint**（评审 R-04 纠正：7 个阶段对应 8 个 Sprint，不是“一一对应”）。完整对照表：

| Sprint | 阶段 | Ticket 段 | 内容 |
|---|---|---|---|
| S1 | 0 | VDA-001–010 | 契约、DB、Mock Catalog |
| S2 | 1 | VDA-011–015、VDA-032 | Search / Recommend / Similar |
| S3 | 2 | VDA-016–020 | Runtime、Agent、Tool |
| S4 | 3 | VDA-021–024 | Creative Workflow |
| S5 | 3 | VDA-025–026 | Composition |
| S6 | 4 | VDA-027–030 | Eval、Video Demo |
| S7 | 5 | CDO-001–007、VDA-031 | Cross-domain 契约、Mock 领域 |
| S8 | 6 | CDO-008–012 | Workflow、审批、跨域 Eval |

4. DoD 数值化：每个 Ticket 的 DoD 须含数值（见 §6 的阶段验收表）；定性短语（“测试通过”“可查询”）须在开工前改为数值。

## 6. 验收数值表（冻结，Mock 阶段）

> 原始文档验收基线几乎无数值（14 项“必须监控”无一有阈值）。本表为 v1.0 唯一验收依据。

| 阶段 | 验收项 | 数值 / 判定方法 |
|---|---|---|
| S0 | 契约 Schema 校验通过 | 全部 JSON Schema 校验 100% 通过 |
| S0 | DB 迁移可重复执行 | 迁移幂等，重复执行 0 报错 |
| S1 | 同一输入 + 同一 Fixture 版本返回稳定排序 | 100 次重复，100% 一致 |
| S1 | Similar 不返回 Seed 自身 | 固定用例 100% 通过 |
| S1 | Mock 检索 P95 | <500ms（100 次重复） |
| S2 | 路由 R0–R4 判定 | 固定用例集（每层 ≥5 例）100% 通过 |
| S2 | 预算耗尽进入 Waiting(`budget_exhausted`) | 固定用例 100% 通过 |
| S3 | 修改 `sb_clip_003` 不重算其他 Assignment | 通用规则：修改任一 Assignment 只重算该条，其余不变（原退出标准写死单个 Fixture ID，现改为通用规则） |
| S3 | 每计划 Clip shortlist ≤10 | 固定用例 100% 通过 |
| S3 | 每个 ClipRequirement 至少一条候选路径 | 固定用例 100% 通过（源 03 §11 #5） |
| S4 | 纵向验收脚本（impl_06 的 A01–A31） | 31 项全部通过（见 §6.1）；Runbook 以 impl_03 §2 阶段 4 为准 |
| S4 | Agent Eval 固定集 | 固定集内容见 `08_附录_核心契约正文.md` §6（A18）；用例数与通过线须在阶段 4 开始前冻结并写入 `08` 附录，本文件不虚构用例数 |
| S5 | Video Agent 无任何跨域 Tool 或依赖 | 静态检查 0 命中（VDA-031） |
| S5 | 跨域 Artifact Envelope 8 类 Schema 齐全 | 8/8 齐全（含 `video-creative-artifact`） |
| S6 | Video-only 回归全部通过 | 阶段 4 固定集重跑 100% 通过 |
| S6 | 跨域用例全部通过 | 跨域固定用例集 100% 通过 |
| 全阶段 | 跨租户泄漏 | 0 |
| 全阶段 | 旧层级词禁入 | CI 禁止关键字（Shot/Segment 等），0 命中（源 impl_03 §7） |
| 全阶段 | SSE 重连游标 | `Last-Event-ID`，重连后无丢事件、无重复（固定用例） |

### 6.1 纵向切片验收（A01–A31）

31 项验收表 A01–A31 全文见 `08_附录_核心契约正文.md` §6（源 impl_06），+ 15 项阻断项（impl_06 §11 实测 15 条，2026-11-16 复数核实），原样保留为 v1.0 纵向验收表；Demo 脚本原样保留（源 impl_06 §12）。**修正两处：** 跨租户返回冻结为 `not_found`；SSE 重连游标冻结为 `Last-Event-ID`。
全部基于 Mock Fixture（4 Video / 9 Clip）。
**注意 A13：** 原文“Video-only 使用原有原因”中的“原有原因”从未定义；本最终版冻结为：Video-only 与跨域均使用同一 4 个 `waiting_reason`（见 `01` §5）。

## 7. PRD MVP 与本排期的关系（新增）

PRD Q4 MVP（11 月内测、12 月小范围、Q4 交付全环节）**不在本排期覆盖范围**。里程碑按 v1.6 §17.5 核实：内测 2026 年 11 月（5–10 名优化师、1–2 个市场或品类，走完主路径）、小范围试用 2026 年 12 月、Q4 浅版交付 2026 年 Q4。若要推进 PRD MVP，须另立范围与排期，至少包括：前端工作台/画布、真实检索（或外采）、个人资产/保护期、媒体执行（上传/合成/渲染）、约 500 名优化师同时在线容量。本文件不承诺 PRD 里程碑。
