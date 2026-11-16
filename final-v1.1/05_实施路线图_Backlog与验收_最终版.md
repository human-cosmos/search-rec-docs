# 05 实施路线图、Backlog 与验收（最终版 v1.0）

> **v1.1 · 2026-11-16**，依据：覆盖分析《VideoDomainAgent_与PRD原型覆盖分析.md》（2026-11-16）+ PRD v1.6。改动摘要：补 PRD 追溯链与 AC-01～AC-18 主验收，补录 REQ-E01/E07 契约落点，OI-01–13 逐项设验收占位，增补 v1.1 新增工作挂接表与性能容量锚点；Ticket 总数 44 与 9–13 周排期冻结不动。
> 权威顺序第 6 位。排期、Ticket、验收数值以本文件为准。
> 来源：impl_00 + impl_02 + impl_03 + impl_06。

## 1. 交付范围（冻结）

### 1.1 交付

通用 Video Domain Agent（意图、检索规划、Storyboard、ClipPlan、素材分配）+ CreativeProductionWorkflow 跨域编排（Product / Landing Page / Copy / Ads 契约 + Mock / Adapter）；对象模型冻结为 Video→Clip 两级；Mock-first，Fake Catalog / Search / Recommendation / Similar / Evidence（检索网关名 `FakeRetrievalGateway`，源 05 §20.1）+ 跨域 Fake（Product / Landing / Copy / Ads）。

### 1.2 不交付（冻结清单，三处统一版）

前端/工作台/对话页面/画布/上传与前端交互；真实领域实现与外部平台；真实入库/转码/切片/ASR/OCR/Embedding/索引（ES/Qdrant/Kafka）；真实推荐训练与 A/B；视频生成/渲染/导出/NLE；版权、许可、商业用途、地域可用性、署名、**Provenance**过滤；生产多租户计费、SLA、容量规划与大规模运维；个人资产/公共素材库/15 天保护期与回流任务；跟品工作台、落地页对照编辑、资产包 ZIP 导出（产品侧）；互联网素材来源（04 §4.1 提及的设计目标，v1.0 明确排除）。
（修正 00 §1 漏 Provenance、漏画布/上传的问题；以本清单为准。）
**v1.4 旧流程已废止，不进入 v1.0：** 逐步审批、按卖点手动查投放视频、按线路创建预算广告草稿（v1.6 OI-11）。

> **v1.1 说明（覆盖分析 §9/§10.3）：** 本清单是 v1.0 Mock 切片的交付边界，不是 PRD 能力的删除清单。凡 PRD 列为 P0 但本清单排除的项，其原型行为、待决策问题、Mock 方案、Adapter 边界与验收占位见本文件 §8（OI-01–13 逐项），裁决记录见 `07` §6（V11-27）。“待确认”（OI）表示生产细节未定，不表示对应的原型能力和工作流可以不存在。REQ-E02（个人资产/回流）与 E01/E07 一样走占位机制：`07` §1 的“排除”仅指 v1.0 交付范围，契约占位见 `04` §9.8，实施待 OI-05 另立范围（评审 C-1）。

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

### 5.1 v1.1 新增工作挂接表（Ticket 总数 44 冻结）

> **冻结声明：** Ticket 总数 **44** 不变（VDA-001–032 + CDO-001–012，见 §5）。下表新增工作以两种方式挂接：（a）挂在现有 Ticket 下的子任务/扩展验收，不新增 Ticket 编号；（b）无现有 Ticket 可挂的，明确标注为 **v1.1 新增待编号项**，不计入 44，待另立范围与排期后编号登记。凡涉及数字变动必须引 PRD 出处；本表无新增数字（OI 项的数字见 §8，均为 PRD 原文或待确认）。

| # | v1.1 新增工作 | 来源 | 挂接方式 | 依赖 | 验收挂钩 |
|---|---|---|---|---|---|
| 1 | Media Capability Workflow：独立媒体能力层，执行片段生成、擦除、画幅、字幕、口播、卖点浮层、BGM、上传、合成、导出；Video Agent 只输出声明式 MediaActionPlan，不直接持有媒体执行凭证 | 覆盖分析 §7.2/§10.2；PRD REQ-C04/C05/C06/D02/D03、BR-22/24、NFR-04 | **v1.1 新增待编号项**（`03` §4.2 已明文：v1.0 不注册 Render/Export/Media Tool，无现有 Ticket 可挂） | 04 对象契约 MediaActionPlan（`04` §9.4）与 Workflow API（`04` §10，合稿已落定）；03 Agent 声明式计划输出 | AC-03、AC-10、AC-13、AC-17（§6.2） |
| 2 | 六项技能：提取字幕、配口播、擦除元素、调整画幅、片段生成、卖点浮层；每项独立的任务 Schema、追问规则、异步状态、结果卡与失败重试 | PRD §5 六项技能表；REQ-D03；OI-10；覆盖分析 §2.3/§5 | **v1.1 新增待编号项**（技能非 Agent 普通文本回复，无现有 Ticket 可挂） | #1 Media Capability Workflow；04 SkillTask/SkillResult 契约（`04` §9.3，合稿已落定） | AC-03（§6.2） |
| 3 | RecommendedScenario 与反馈闭环：推荐场景对象（适配槽位类型 + 场景提示词，DR-07/08：每个试点槽位类型至少 3 个场景、每个场景一段可提交的提示词）；反馈回写规则（会话内重排、跳过/重搜负向权重、长期偏好更新，显式偏好优先） | PRD §17.2 DR-07/08；REQ-B02/C04；OI-02；覆盖分析 §8/§10.2 | 子任务挂 VDA-014（推荐场景对象，`clip_candidate` 之外的推荐场景扩展）+ VDA-015 扩展验收（反馈回写规则；VDA-015 原 DoD 只覆盖事件归因写入，见 impl_05 §13） | 04 RecommendedScenario 对象契约（`04` §9.2）与反馈事件 Schema（`04` §12.1，合稿已落定）；02 推荐范围裁决（现仅 `clip_candidate`，见 `07` §4 C P1-1） | AC-04、AC-10（§6.2） |
| 4 | 新对象契约：EntryTask/任务模板、MediaActionPlan、SkillTask/SkillResult、EditDecision、DerivedVideo、VideoPerformanceSnapshot、PersonalAsset、UserPreference/UserMemory、SessionCanvasProjection | 覆盖分析 §10.2；PRD §12 对象表、DR-04–08/13–16/19 | 挂 04 组，已落定：`04` §9.1 EntryTask、§9.2 RecommendedScenario、§9.3 SkillTask/SkillResult、§9.4 MediaActionPlan、§9.5 EditDecision、§9.6 DerivedVideo、§9.7 VideoPerformanceSnapshot、§9.8 PersonalAsset、§9.9 UserPreference/UserMemory、§9.10 SessionCanvasProjection；JSON Schema 正文见 `08` §9（A-9–A-21） | 02/03 对象定义先行；PersonalAsset 依赖 OI-05 决策（见 §8） | AC-09、AC-10、AC-11（投影类，§6.2） |
| 5 | 跟品末端改为 ZIP 下载：跟品主路径末端由 Ads 草稿/发布改为“下载资产包（ZIP）”；Ads 保留为可选通用能力，不作为跟品主路径必需末端 | PRD 跟品 BR-20（资产包交付）、REQ-F07；覆盖分析 §7.4 | 子任务挂 CDO-008–012（交付状态已有 Workflow 底；ZIP 打包为新增子任务） | 落地页/口播/文案/视频各分项就绪（BR-13 分项失败规则）；OI-11 旧广告草稿入口待确认（见 §8） | AC-08、AC-13（§6.2） |
| 6 | 槽位交互：多选镜头、批量替换、最近八次批量撤销、并发修改校验、槽位生成中状态、结果卡自动避让与手动位置/来源连线保留 | PRD BR-21/22/23、§7/§8；OI-13；覆盖分析 §5 | 子任务挂 VDA-025–026（Assignment 扩展：批量操作与撤销状态）+ VDA-013/VDA-032（Similar 候选绑定发起槽位） | 04 EditDecision（`04` §9.5）与槽位/跟品契约（`04` §11，合稿已落定）；#1 媒体能力层（生成中状态） | AC-10、AC-14、AC-17（§6.2） |

- 阶段归属：上表 #1/#2/#4 的排期**不在 v1.0 9–13 周排期内**（§2 冻结排期只覆盖 VDA/CDO 44 Ticket）；#3/#5/#6 的子任务随其父 Ticket 所在阶段（#3 随 S2、#5 随 S8、#6 随 S5），但其 AC 验收（§6.2）须待前端/真实 Adapter 立项后执行，当前为验收占位。

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

### 6.2 PRD 验收 AC-01～AC-18（主验收，v1.1 新增）

> **地位裁决（覆盖分析 §9/§10.3）：** A01–A31（§6.1）保留作**后端切片验收子集**，只证明 Mock 切片内部一致；**AC-01～AC-18（PRD §14）成为主验收**，是 PRD 原型可用的最终验收依据。A01–A31 全部通过不等于 AC 通过；AC 未通过不得宣布 PRD 原型验收通过。

**追溯链（覆盖分析 §10.3 原文结构）：**

```text
PRD G / REQ / BR / DR / NFR / OI
  → 设计对象
  → API 或 Workflow
  → Ticket
  → Mock 或真实 Adapter
  → PRD AC-01～AC-18
  → 证据
```

每项 AC 须沿此链逐环可追溯；任一环缺失（如对象无契约、Ticket 无挂接、Adapter 无 Mock 方案）即记为验收缺口，登记 `07` §6，不得以“前端/媒体不在 v1.0”跳过该环——不在 v1.0 的环写明“验收占位”，见下表“证据”列。

| AC | PRD 验收要点（§14） | 追溯：REQ / BR / DR / NFR | Ticket / 挂接 | Mock / 真实 Adapter 与证据 |
|---|---|---|---|---|
| AC-01 首页案例 | 悬浮只预览、移开保留原内容、采用后只出现一份 | REQ-A02；PRD §5 | 前端，**v1.1 新增待编号项**（不在 44 内） | 证据：E2E 原型验收占位（待前端立项）；后端无对应环 |
| AC-02 库筛选 | 默认最多订单，条件生效，两种布局可切换 | REQ-A04；BR-05/06；OI-06 | VDA-011–014（检索口）+ 前端筛选/排序/布局为 v1.1 新增待编号项 | Mock：Fake 检索候选；E2E 占位（生产字段待确认，OI-06） |
| AC-03 技能交付 | 六种技能结果：字幕可复制，口播可试听/下载，四种视频点开才进对应画布，历史仍可打开 | REQ-D03；PRD §5 六项技能表；OI-10 | **v1.1 新增待编号项**（§5.1 #2） | Mock：六项技能固定模板；真实 Adapter：媒体服务待接入（OI-07）；证据占位 |
| AC-04 找片展示 | 对话最多 9 张，少于 9 条仍保留「…」，单条与全部结果分别打开，再搜索一次仍同规则 | REQ-B01；BR-05；PRD §5 | VDA-011–014 + 前端 9 卡呈现为 v1.1 新增待编号项 | Mock：CandidateSet 分页（`04` §3）+ A07；E2E 占位（9 卡预览交互） |
| AC-05 跟品开始 | 完整信息直达双栏，缺参显示补充控件，空 ID 用已提示样例，当前版用新商品 ID | REQ-F01/F02；BR-08/09/10/11；OI-11 | VDA-009–010 + CDO-004–007 | Mock：跟品 Task/Workflow；证据：A22/A24（跨域路径）+ E2E 占位（补参交互） |
| AC-06 诊断定位 | 右侧报告展示依据与修改状态，问题入口定位正确，能返回对应图片，处理更新保留展开和滚动 | REQ-F03；BR-16；OI-12 | CDO-004–007 | Mock：诊断报告 Artifact；真实证据待确认（OI-12）；E2E 占位 |
| AC-07 快跟与手工改页 | 可按报告优化，人工修改与原版快照保留，可查看变化或撤销 | REQ-F05；BR-14/16；PRD §跟品 | CDO-004–007 | Mock：原版快照 + 当前版 Artifact；撤销八步为产品规则（BR-16），后端 Checkpoint 只类比，不替代（`07` §1 REQ-F05 行） |
| AC-08 跟品交付 | 未读提示按页签处理，共享文案更新，ZIP 含可用文件与清单；试听无文件时有口播稿及说明 | REQ-F07（P1）；BR-17/18/20；PRD §跟品 | CDO-008–012 子任务（§5.1 #5） | Mock：交付状态（A27 部分成功）；ZIP 打包 E2E 占位（待媒体/导出 Adapter） |
| AC-09 视频与导航 | 生成/检索操作正确，工具栏可恢复数据，缩略导航不占画布列，历史结果随对应视频恢复 | REQ-C01/C07；PRD §6/§11 | VDA-025–026 + 前端画布为 v1.1 新增待编号项 | Mock：Assignment/Checkpoint（A11/A13）；画布投影 E2E 占位 |
| AC-10 槽位结果 | 候选与生成卡独立保留，生成面板聚焦，自动卡避让，手动位置和来源连线保留；OI-13 尺寸稳定性见 §8 | REQ-C02/C04；BR-21/22；OI-13 | VDA-013/VDA-032 + VDA-025–026 子任务（§5.1 #6） | Mock：A09/A11；生成卡 E2E 占位（待 #1 媒体能力层）；OI-13 为纯前端验收 |
| AC-11 会话恢复 | 可恢复的流程接续，已暂停的跟品等待继续 | REQ-E04；NFR-09；BR-26；OI-09 | VDA-009–010 | Mock：Checkpoint + A13（等待与恢复）；跨端恢复占位（OI-09，旧版 7 天为暂拟值） |
| AC-12 复刻与成片 | 缺人像参考时提示，确认后留在对话播放样例 | REQ-D01；BR-25；OI-01 | **v1.1 新增待编号项**（复刻工作流，§5.1 #1 媒体层） | Mock：固定复刻方案 + 样例结果；人像校验规则见 §8 OI-01 |
| AC-13 无槽位与异常 | 无分段仍可播放和拖进度；素材清单记录读取失败，已读文件保留 | REQ-C05；BR-20；OI-04；PRD §9/§13 | CDO-008–012（ZIP 失败降级）+ 媒体读取为 v1.1 新增待编号项 | Mock：A27 部分成功；ZIP 失败清单 E2E 占位 |
| AC-14 多选镜头 | 保留槽位时长和顺序，采用后更新替换引用，撤销还原 | REQ-C02；BR-23；PRD §7 | VDA-025–026 子任务（§5.1 #6） | Mock：Assignment 版本（A11 局部重算）；批量撤销 E2E 占位 |
| AC-15 输入冲突与回退 | 跟品保留参数区已选值；普通找片可出现样例回退，不视为真实同商品匹配 | REQ-F01/B01；BR-03/09 | VDA-009–010 + CDO-004–007 | Mock：Task 参数状态；证据：固定用例（参数区已选值优先） |
| AC-16 分项失败与恢复 | 记录原始错误，其他分项继续，重试保留已就绪产物和人工编辑 | REQ-F01–F06；BR-13；PRD §跟品 | CDO-008–012 | Mock：A27 部分成功 + A30 跨域恢复；证据：失败分项重试固定用例 |
| AC-17 镜头合成前校验 | 首次提示先替换，采用后生成衍生结果，重复提交提示已有结果 | REQ-C06；BR-24；PRD §7 | 校验规则 Mock 占位挂 VDA-025–026 子任务；真实合成**为 v1.1 新增待编号项** | Mock：校验前置检查（至少一段已替换且无槽位生成中）；转码/拼接待真实 Adapter（`07` §1 REQ-C06 行） |
| AC-18 兼容与反馈 | 1280×800、深色主题下关键控件可达，局部滚动可用，反馈与发送可分别操作 | PRD §10 反馈（最多 12 条、最多 3 张截图）；PRD §14 | 前端为 v1.1 新增待编号项；反馈事件挂 VDA-015 | Mock：Feedback 写入 A21；E2E 占位（兼容与反馈交互） |

### 6.3 映射表补遗：REQ-E01、REQ-E07（v1.1 新增）

> 覆盖分析 §9 指出的追溯缺口：v1.0 `07` §1 映射表缺 REQ-E01 与 REQ-E07 两行。本节给出它们在 04/08 的契约落点（2026-11-16 核对 v1.1 版 04/08 全文所得）；对应行已同步补入 `07` §1（v1.1 补录）。

| PRD 需求 | 处置 | 对应 Ticket / 阶段 | 04/08 契约落点（已核对存在）与待对齐项 |
|---|---|---|---|
| REQ-E01 收藏与分享（P0；PRD §10、OI-08） | 部分（v1.1 补录） | 收藏事件挂 VDA-015（`recommendation.saved` 已入 `04` §2.5 冻结枚举）；收藏对象/分享权限/有效期为 **v1.1 新增待编号项** | 已落定：`04` §2.5 `recommendation.saved` 事件；`04` §2.5 信号—事件映射表“收藏 → `recommendation.saved`”；收藏对象与只读分享契约见 `04` §12.2、`08` §9 A-21（合稿已落定，原“04 中无对象契约”已作废）。生产口径待确认（OI-08） |
| REQ-E07 行为探针与片段预生成（P0；PRD §16 行为探针行、§17.2 DR-15/19） | 部分（v1.1 补录） | VDA-015（反馈事件写入）+ 反馈回写规则挂 VDA-015 扩展验收（§5.1 #3） | 已落定：`04` §2.5 Feedback 事件枚举与请求字段（含 `position` 曝光位置、`candidate_set_id`、`strategy_version`）；`04` §5.1 `video_feedback_event`、`urre_feedback_event` 表；`08` §6 A21（Feedback 写入）；反馈事件 Schema 与归因上下文见 `04` §12.1、反馈回写规则见 `02` §11.2（合稿已落定）。仍待确认：会话内重排权重数值、跳过/重搜负向权重数值、预生成片段触发规则（OI-02）；探针实时作用于当次会话为生产依赖（PRD §17.2 DR-15） |

- 其余 v1.1 新增对象（§5.1 #4 清单）的 04 落点：已全部落定，见 §5.1 #4（`04` §9.1–§9.10；JSON Schema 正文见 `08` §9 A-9–A-21）。

## 7. PRD MVP 与本排期的关系（新增）

PRD Q4 MVP（11 月内测、12 月小范围、Q4 交付全环节）**不在本排期覆盖范围**。里程碑按 v1.6 §17.5 核实：内测 2026 年 11 月（5–10 名优化师、1–2 个市场或品类，走完主路径）、小范围试用 2026 年 12 月、Q4 浅版交付 2026 年 Q4。若要推进 PRD MVP，须另立范围与排期，至少包括：前端工作台/画布、真实检索（或外采）、个人资产/保护期、媒体执行（上传/合成/渲染）、约 500 名优化师同时在线容量。本文件不承诺 PRD 里程碑。

> **v1.1 补充：** 本节裁决不变（v1.1 不把 PRD MVP 拉入 9–13 周排期）。v1.1 只补齐通向 MVP 的追溯与占位：主验收 AC-01～AC-18（§6.2）、OI-01–13 逐项占位（§8）、性能与容量锚点（§9）、v1.1 新增工作挂接表（§5.1）。另立范围时以 §5.1 #1/#2/#4 的“新增待编号项”为立项输入。

## 8. 待确认项 OI-01–13：原型行为、Mock 方案与验收占位（v1.1 新增）

> **规则（覆盖分析 §10.3）：** P0 不得直接标排除。每项 OI 保留五要素：原型行为说明 + 待决策问题 + Mock 方案 + Adapter 边界 + 验收占位。原型行为引 PRD 原文；待决策问题引 PRD §17.4；Mock 方案只复用 v1.0 已有 Mock 手段（Fake Catalog/Search/Recommendation/Similar/Evidence + 跨域 Fake），不虚构新 Mock 能力；验收占位挂 AC-xx（§6.2）。

| OI | 原型行为说明（PRD 出处） | 待决策问题（PRD §17.4） | Mock 方案 | Adapter 边界 | 验收占位 |
|---|---|---|---|---|---|
| OI-01 | 做同款与整片复刻：换人物必须从人像库选人物或提交参考图，人像库最多选四位；产品与场景可提供参考图，当前对话入口硬性校验集中在人像；确认后在原对话看样例结果（PRD §7、BR-25） | 生产中的模型、参数、参考素材校验和配额 | 固定复刻方案 + 对话内样例结果；缺人像参考时固定提示 | 真实生成服务接入时替换样例结果；校验规则以 BR-25 为准，生产统一校验另行冻结 | AC-12 |
| OI-02 | 槽位归因与推荐场景：槽位级指标缺失时显示「暂无」，仍可二创（DR-06）；每个试点槽位类型至少 3 个推荐场景，每个场景一段可提交的提示词（DR-07/08） | 槽位点击、跳出、转化按秒归因，及推荐场景的计算与数据源 | 每槽位类型固定 3 个场景 + 固定提示词；归因字段固定值 | 真实归因与场景计算服务接入时替换；DR-07/08 数据须试点抽检（PRD §17.5 前置数据） | AC-10 |
| OI-03 | 外部视频：带来源、默认无槽位（DR-10）；外部视频实时理解、自动切片与深度二创为待确认的生产能力（PRD §9） | 外部视频是否允许二创，何时触发深度理解和缓存 | 外部 Video 无 Clip；理解/切片一律返回“未触发”固定状态 | 深度理解与缓存 Adapter 接入时，触发条件以 OI-03 决策为准，不得默认全量理解 | AC-09、AC-13 |
| OI-04 | 动作矩阵与下载：独立片段菜单随入口变化（PRD §9：tldraw 片段菜单提供搜相似、做同款、去生成与下载）；下载排在对应菜单最后（PRD §7） | 独立片段、整片、切片和衍生结果的生产动作矩阵及下载口径 | 固定动作矩阵（按卡片类型）；下载固定返回样例文件 | 真实导出 Adapter 接入时按矩阵逐项替换；失败降级见 BR-20 | AC-09、AC-13 |
| OI-05 | 个人资产与回流：资产筛选全部/进行中/已完成/失败，详情含原视频、结果视频、分镜与生成提示词（PRD §10）；产出 15 天保护期后回流公共库（PRD §16）；回流后槽位与提示词补加工待确认 | 资产保护期、公共回流、回流后加工以及共享交接 | `video_asset` 状态字段（`04` §5.1 已有表）；回流一律返回“未回流”固定状态 | 回流服务接入时以 OI-05 决策为准；保护期内仅创建者可见、可分享（NFR-10） | **AC 暂无直接对应，占位**：待产品确认后补 AC 或纳入 AC-18 扩展 |
| OI-06 | 库字段与统计口径：广告视频库支持优化师、时间范围、部门、语种、平台、线路和品类筛选（PRD §5）；订单和转化用素材字段，其他库指标可由样例属性和序号推算（BR-06） | 优化师、部门、加购成本、投放统计周期与商品来源字段 | 样例属性推算的固定指标；筛选条件取交集 | 真实统计服务接入时替换推算口径；生产统计周期、归因和缺失值见 PRD §16–17 | AC-02 |
| OI-07 | 真实媒体服务：调画幅、合成、口播、图像修改等原型均为样例交付（PRD §5、§7）；耗时任务异步执行（NFR-04） | 调画幅、合成、口播、图像修改等真实服务及失败重试契约 | 固定成功/固定失败两档 Mock 结果；重试固定 2 次（`05` §4 配置示例 `max_domain_retries=2` 为跨域重试，不直接等同媒体重试，媒体重试次数待确认） | 真实服务 Adapter 接入时以 OI-07 契约替换；失败重试契约须先冻结再接入 | AC-03、AC-17 |
| OI-08 | 收藏与分享：库卡和视频收藏在本机，可在收藏页或收藏车查看；分享弹窗可复制带会话 ID 的链接，当前只打开已有本地快照（PRD §10） | 收藏/会话链接的跨账号访问、只读权限和有效期 | `recommendation.saved` 事件（`04` §2.5）；分享链接固定返回已有快照 | 跨账号/只读/有效期 Adapter 接入时以 OI-08 决策为准；跨端可访问性当前不承诺 | **AC 暂无直接对应，占位**：待产品确认后补 AC |
| OI-09 | 会话保留与恢复：会话快照最多 30 条（PRD §12）；已完成的会话快照可在同一浏览器恢复；运行中的跟品重开会话时继续（BR-26） | 会话和任务保留期、跨端恢复及资源续存。旧版 7 天为暂拟值 | Checkpoint 恢复（A13）；保留期不设 TTL（`07` §1 REQ-E04 行） | 跨端恢复 Adapter 接入时以 OI-09 决策为准；保留期冻结前不得承诺 7 天 | AC-11 |
| OI-10 | 技能目录与市场：六项技能交付见 PRD §5；Skills 提供能力条目、启停和本地导入入口（PRD §10）；技能市场另行确认（PRD §1） | 技能目录、技能市场、中台同步、翻译和脚本等能力的 Q4 范围 | 六项技能固定模板（§5.1 #2）；市场/同步一律返回“未接入”固定状态 | 中台同步 Adapter 接入时以 OI-10 决策为准 | AC-03 |
| OI-11 | 未匹配商品与旧流程：未知输入保留标识并复用本地样例（BR-08）；跨线路或换商品后的真实归属待确认（BR-11）；v1.4 旧流程（逐步审批/按卖点查投放视频/按线路建预算草稿）已废止（PRD §跟品） | 未匹配商品的生产校验、跨线路商品 ID 绑定，以及旧广告草稿与预算能力的交付入口 | 演示商品回落（BR-08）；旧流程入口一律返回“已废止” | 商品校验与绑定 Adapter 接入时以 OI-11 决策为准；Ads 草稿入口不得默认进入跟品主路径（§5.1 #5） | AC-05、AC-15 |
| OI-12 | 跟品诊断真实数据：样例标记首图和前三张详情图的四处问题；模拟来源明确标注；报告按区域呈现点击率和停留时长，区域点击率不相加（PRD §跟品、BR-15） | 跟品诊断接入真实广告、评论和页面行为后的证据及效果验证 | 固定诊断报告（四处问题 + 模拟标识）；效果一律标“待验证” | 真实广告/评论/页面行为 Adapter 接入时以 OI-12 决策为准；修改效果以同条件对照验证（BR-15） | AC-06、AC-07 |
| OI-13 | 布局回归：找片槽位布局回归中，生成面板聚焦、生成中及结果卡避让检查通过，重复渲染时原视频节点实测高度从 689px 变为 691px，触发尺寸稳定性断言（PRD §17.4、AC-10） | （PRD 原文即为该断言本身；无进一步待确认生产问题，属纯前端验收） | 无后端 Mock（v1.0 不跟进，`07` §5 第 11 项） | 前端验收，不设 Adapter | AC-10（前端） |

## 9. 性能与容量锚点（v1.1 新增，PRD §16/§17.3，数字原文照录）

> 本节数字**全部引自 PRD 原文，不许改数字**。其中 Mock 验收已覆盖的只列对应关系；生产目标不进 Mock 验收，待真实 Adapter/容量立项后验收。

| 锚点 | PRD 数值（原文） | 出处 | v1.0/Mock 对应 |
|---|---|---|---|
| 内部检索首批 | 约 500ms 返回首批结果 | PRD §16 召回与推荐行；NFR-01 | §6 S1 Mock P95 <500ms（100 次重复）已覆盖 Mock 层 |
| 外部检索首批 | 约 4–5 秒内开始有结果，先返回的来源先展示 | PRD §16；NFR-02 | 生产目标，不进 Mock 验收（`07` §1 NFR-01/02 行） |
| 意图分流 | 200ms | PRD §16 召回与推荐行 | 未单列验收；路由判定见 §6 S2（固定用例 100% 通过，无时延阈值） |
| 传统链路 | 1 秒内 | PRD §16 召回与推荐行 | 未单列验收，记为生产目标 |
| 同时在线容量 | 按约 500 名同时在线优化师估算，评估 500–1000 峰值、多会话与低配机表现 | PRD §16 生成与隔离行；NFR-06 | 容量不在 v1.0（`07` §1 NFR-06 行排除裁决不变）；沙箱按会话隔离、资产按账号隔离为 NFR-06 原文 |
| Q4 内测规模 | 1–2 个市场、1–2 个品类、每个品类头部 50–100 条视频、5–10 名优化师 | PRD §1 Q4 规划；§17.5 内测行 | 里程碑无法对应到 9–13 周排期（§2 已裁决）；前置数据须试点成片和 DR-01–08 通过抽检（PRD §17.5） |
| 覆盖率评测目标 | 覆盖率从 80–85% 提升至约 95% | PRD §16 召回与推荐行 | 评测目标，非 Mock 验收（`07` §1 该行排除（延期）裁决不变；`07` §5 第 7 项已关闭引用核实） |

- 另两条 15 天规则不属性能锚点，仅此备录（PRD §16 原文）：广告成片投放满 15 天后进入入库加工；个人资产产出 15 天保护期后回流公共库。处置见 `07` §1 REQ-E02 行与本文件 §8 OI-05，本节不重定义。
