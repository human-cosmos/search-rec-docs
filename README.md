# 检索推荐与 Agent 平台：2.0 架构文档

本目录是 2.0 架构文档的阅读入口。权威顺序如下；冲突时按此顺序取用，不得把后位文档当作开工依据去覆盖前位结论。

## 权威顺序

1. [`00_架构设计总纲.md`](00_架构设计总纲.md)：已冻结原则、边界、能力里程碑 A–D、架构 ADR（`ADR-01`–`ADR-12`）。
2. [`01_URRE架构设计.md`](01_URRE架构设计.md)、[`02_AgentRuntime架构设计.md`](02_AgentRuntime架构设计.md)、[`03_VideoDomain架构设计.md`](03_VideoDomain架构设计.md)：专项架构。Task 状态机以 `02` §4.2 为准。
3. [`implementation/01_API与数据契约.md`](implementation/01_API与数据契约.md)：字段级契约。
4. [`implementation/02_技术选型与服务部署.md`](implementation/02_技术选型与服务部署.md)、[`implementation/03_实施路线图与验收基线.md`](implementation/03_实施路线图与验收基线.md)：选型、工程阶段 0–5、实施决策（`IMPL-ADR-01`–`IMPL-ADR-11`）。
5. [`04_开源项目源码解析与设计指南.md`](04_开源项目源码解析与设计指南.md)：**仅调研附录**，不是目标架构、阶段计划、API 或技术选型权威。

实施材料的目录说明见 [`implementation/README.md`](implementation/README.md)。

## 图的身份

| 图 | 身份 |
|---|---|
| `00` / `01` / `02` / `03` 中被正文引用的 mermaid（含 `00` §1.1 总图） | 正式逻辑图 |
| [`images/通用检索推荐系统架构图.png`](images/通用检索推荐系统架构图.png) | 可继续被 `01` 引用，但须加注：Similarity / Explore 与 Search、Recommendation 并列；Rights 硬过滤先于排序。若与注不符，以正文 mermaid 为准 |
| [`images/整体架构图.png`](images/整体架构图.png)、[`images/视频检索推荐 Agent 架构图.png`](images/视频检索推荐%20Agent%20架构图.png) | **不作开工总图**。与正文冲突，不得读成「所有请求经 Runtime 才能到 URRE」或「以 Agent 为核心」。待重绘前禁止当作平台目标架构 |
| [`images/推荐链路.png`](images/推荐链路.png)、[`images/动态任务路由.png`](images/动态任务路由.png)、[`images/人工确认与生产闭环.png`](images/人工确认与生产闭环.png) | 调研/流程示意；若引用须标明非本平台目标架构，建议由 `04` 引用 |
| [`images/shared-chat/`](images/shared-chat/) | 仅服务 `04` 调研叙述 |
