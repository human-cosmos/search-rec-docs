# 实施材料

本目录承载通用 Video Domain Agent 及跨域创作编排的实施契约。交付范围与领域模型以 [00 交付范围与 Video/Clip 模型基线](00_交付范围与VideoClip模型.md)为准。

本次交付跨域编排契约，以及 Product、Landing Page、Copy、Ads 的 Mock/Adapter。不交付这些领域的真实业务实现、外部平台接入、真实检索推荐、媒体渲染或前端。Video Domain Agent 继续只负责视频领域，不承担跨域编排。

## 文档

| 文档 | 内容 |
|---|---|
| [00 交付范围与 Video/Clip 模型](00_交付范围与VideoClip模型.md) | 最终范围、对象层级、旧概念映射和 Mock 约束 |
| [01 API 与数据契约](01_API与数据契约.md) | Video、Clip、Search、Recommendation、任务和 Tool 契约 |
| [02 技术选型与服务部署](02_技术选型与服务部署.md) | 本次最小技术栈、Mock 服务和测试部署 |
| [03 实施路线图与验收基线](03_实施路线图与验收基线.md) | 阶段计划、工作包、指标和交付顺序 |
| [04 Video Domain Agent 详细设计与实施手册](04_VideoDomainAgent_详细设计与实施手册.md) | Agent、Workflow、ClipPlan、Assignment、恢复和评测 |
| [05 工程契约与研发 Backlog](05_VideoDomainAgent_工程契约与研发Backlog.md) | 模块、Port、Schema、DDL、Ticket 和完成标准 |
| [06 纵向切片与验收脚本](06_VideoDomainAgent_纵向切片与验收脚本.md) | Video-only 与跨域 Mock、端到端演练和故障注入 |
| [07 跨域编排与领域子工作流设计](07_跨域编排与领域子工作流设计.md) | 主 Workflow、领域调用、Artifact 交换、审批和恢复 |

## 使用顺序

1. 阅读 [交付范围与模型基线](00_交付范围与VideoClip模型.md)。
2. 阅读 [跨域编排设计](07_跨域编排与领域子工作流设计.md)和 [Video Domain 架构](../03_VideoDomain架构设计.md)。
3. 阅读 [Video Domain Agent 详细设计](04_VideoDomainAgent_详细设计与实施手册.md)。
4. 按 [API 契约](01_API与数据契约.md)和 [工程契约](05_VideoDomainAgent_工程契约与研发Backlog.md)编码。
5. 按 [实施路线图](03_实施路线图与验收基线.md)排期。
6. 使用 [验收脚本](06_VideoDomainAgent_纵向切片与验收脚本.md)完成 Video-only 与跨域 Mock 验收。

Runtime 接入以 Acore Runtime Java SDK 文档和示例为**外部基线**，本仓库不收录 `runtime-sdk/` 或 `java-examples/`。SDK 制品和目标环境仍需在开发环境单独验收。

## 维护原则

- 新设计不得重新引入 Shot、Segment 或第三层视频对象。
- 跨域编排只能由主 Workflow 负责，Video Domain Agent 不得直接调用其他领域服务。
- Mock 与真实 Adapter 共用 Port、Schema、事件和错误码。
- Agent 只使用注册 Tool，不直接访问 Mock 数据、数据库或文件系统。
- 机器契约以 OpenAPI、JSON Schema、DDL 迁移和契约测试为准。
- 跨域领域真实实现、媒体渲染、真实索引和前端不在本次范围。
