# 通用 Video Domain Agent：设计与实施文档

本目录当前只服务一个交付目标：实现通用 Video Domain Agent。视频领域模型冻结为 `Video -> Clip` 两级。

## 权威顺序

1. [`implementation/00_交付范围与VideoClip模型.md`](implementation/00_交付范围与VideoClip模型.md)：最终交付范围、Video/Clip 模型和 Mock-first 约束。
2. [`03_VideoDomain架构设计.md`](03_VideoDomain架构设计.md)：Video Domain 架构。
3. [`implementation/04_VideoDomainAgent_详细设计与实施手册.md`](implementation/04_VideoDomainAgent_详细设计与实施手册.md)：Agent、Workflow、工具和状态设计。
4. [`implementation/01_API与数据契约.md`](implementation/01_API与数据契约.md)、[`implementation/05_VideoDomainAgent_工程契约与研发Backlog.md`](implementation/05_VideoDomainAgent_工程契约与研发Backlog.md)：API、Schema、DDL、Port、Backlog。
5. [`implementation/02_技术选型与服务部署.md`](implementation/02_技术选型与服务部署.md)、[`implementation/03_实施路线图与验收基线.md`](implementation/03_实施路线图与验收基线.md)：本次技术基线和路线图。
6. [`implementation/06_VideoDomainAgent_纵向切片与验收脚本.md`](implementation/06_VideoDomainAgent_纵向切片与验收脚本.md)：Mock 数据的端到端验收。
7. [`04_开源项目源码解析与设计指南.md`](04_开源项目源码解析与设计指南.md)：仅调研附录，不是交付契约。

[`00_架构设计总纲.md`](00_架构设计总纲.md)、[`01_URRE架构设计.md`](01_URRE架构设计.md) 和 [`02_AgentRuntime架构设计.md`](02_AgentRuntime架构设计.md) 提供平台原则和 Runtime 边界。它们描述的其他领域及生产基础设施不进入本次交付。

真实 URRE 2.0 的数据加工、控制面、API 和存储模型见 [`05_URRE数据与存储模型设计.md`](05_URRE数据与存储模型设计.md)。该文档是未来替换 Mock Retrieval Adapter 的设计基线，不构成本次 Video Domain Agent 交付的前置依赖。

