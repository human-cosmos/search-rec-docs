# Video Domain Agent 与 PRD 原型覆盖分析

> 评审日期：2026-11-16  
> 评审口径：**PRD 是 Source of Truth**。只要 PRD 描述了原型中的用户行为或 Agent 能力，就视为需求；现有设计文档中的“本期不交付”“另立范围”或“待确认”不能自行将该能力从 PRD 中删除。  
> 评审材料：[PRD v1.6](./prd/index.md)、[PRD HTML 页面](./prd/index.html)及 `prd/figures/` 下 10 张交互图。

## 1. 结论

**当前 Video Domain Agent 的设计不能完全满足 PRD 原型中的设计和 Agent 功能。**

更准确的判断是：

- 当前方案能够支撑“视频检索、相似检索、创作规划、小候选集比较和素材分配”的视频领域内核。
- 当前方案不能完整支撑 PRD 中“万镜魔方 / 乘风智能体”的视频找片、二创、生成、爆款复刻、全链路跟品、六项技能、会话画布、个人资产和反馈闭环。
- 这些差距不是少量接口遗漏，而是任务入口、媒体能力、数据对象、交互投影、资产治理和验收体系共同缺失。

现有 `final-v1.0` 的 PASS 只能说明其缩窄后的后端 Mock 切片内部基本一致，不能说明该切片满足 PRD 完整产品。设计文档自己也明确写明 PRD Q4 MVP 不在当前排期覆盖范围内，见 [实施路线图 §7](./final-v1.0/05_实施路线图_Backlog与验收_最终版.md)。

## 2. PRD 原型刻画出的完整能力范围

### 2.1 产品主路径

PRD 把产品组织为一个统一工作入口：

```text
首页 / 统一输入
  → 意图识别与任务分流
  → 对话结果 / 右画布
  → 选片、槽位修改、生成、复刻或落地页处理
  → 用户确认
  → 结果留在当前会话或进入个人资产
  → 导出、分享和后续二创
```

关键交互约束：

- 找片、看片、二创和生成尽量留在同一任务内，不频繁换页。
- 结果先在对话中显示，完整结果和视频操作在右画布展开。
- 生成前必须确认，生成中可继续浏览，失败可重试，任务可以恢复。
- 点击卡片、槽位和自然语言应落到同一套任务和对象状态上。
- 行为反馈不仅用于分析，还应影响当次会话和后续推荐。

这些要求来自 PRD 主流程、时序图和生成生命周期图，以及 [PRD §11 跨页面交互规则](./prd/index.md)。

### 2.2 四个智能体入口

PRD 首页有四个智能体入口：

1. 全链路跟品
2. 视频二创
3. 找爆款
4. 爆款复刻

它们不必一一对应四个后端自治 Agent，但必须对应四类可识别的任务入口、必需参数、执行策略和结果契约。

### 2.3 六项单点技能

PRD 还定义六项技能：

| 技能 | 必需能力 | 期望结果 |
|---|---|---|
| 提取字幕 | 视频理解、ASR/字幕提取 | 可复制文本 |
| 配口播 | 文本、语言、音色到语音 | 可试听、下载音频 |
| 擦除元素 | 指定对象识别与视频处理 | 返回处理后的视频 |
| 调整画幅 | 识别并转换 9:16、1:1、16:9 | 返回对应画幅视频 |
| 片段生成 | 镜头描述、时长等参数 | 返回生成视频 |
| 卖点浮层 | 视频、卖点文案、版式 | 返回带浮层视频 |

六项技能需要独立的任务 Schema、追问规则、异步状态、结果卡和失败重试，不能只当作 Agent 的普通文本回复。

### 2.4 完整创作与跟品闭环

PRD 中至少存在以下用户闭环：

```text
找片
→ 打开成片
→ 查看槽位、提示词、口播和指标
→ 搜相似 / 做同款 / 去生成
→ 采用结果
→ 合成新成片
→ 进入会话、画布或资产
```

```text
商品
→ 创建跟品任务
→ 确认市场和平台
→ 克隆并获取原页
→ 页面诊断
→ 落地页、口播、广告文案和视频准备
→ 视频裂变和二创
→ 下载资产包
```

PRD 的 [功能需求清单](./prd/index.md) 将这些能力列为 P0，除少部分能力为 P1 或待定外，不能通过“v1.0 排除”直接视为不重要。

## 3. 当前 Video Domain Agent 的实际设计

### 3.1 角色职责

当前方案的角色分工是：

```text
Intent Router
  ├─ 简单 Search / Recommendation / Similar → Retrieval Port
  ├─ Video-only 复杂任务 → Video Workflow → Video Domain Agent
  └─ 跨域任务 → CreativeProductionWorkflow → 各领域子工作流
```

- **Intent Router**：判断直接检索、视频工作流或跨域工作流。
- **Video Workflow**：管理 Video-only 任务状态。
- **Video Domain Agent**：理解目标、澄清、生成创作计划和素材分配。
- **CreativeProductionWorkflow**：管理 Product、Landing Page、Copy、Ads、Video 的跨域依赖。
- **Retrieval Port**：确定性执行 Search、Recommendation 和 Similar。
- **Runtime SDK**：承载 Agent、Session、Run、Action、文件产物等执行原语。

### 3.2 Agent 的冻结职责

当前 Video Domain Agent 只负责：

- 抽取目标、时长、画幅、语言、风格和硬约束。
- 判断信息是否充分并请求澄清。
- 生成 CreativeBrief、Storyboard 和 ClipPlan。
- 调用 Search、Recommendation 和 Similar。
- 比较少量候选并生成 MaterialAssignment。
- 处理零结果、工具失败、冲突和局部修改。
- 在需要时请求用户确认。

### 3.3 当前 8 个 Agent Tool

| Tool | 能力 |
|---|---|
| `get_project_context` | 读取项目上下文 |
| `search_video_materials` | 按 SearchPlan 检索视频或 Clip |
| `recommend_video_materials` | 基于 ClipRequirement 推荐候选 |
| `find_similar_materials` | 以 Video/Clip 为种子找相似 |
| `resolve_evidence` | 解析证据和预览引用 |
| `create_artifact_draft` | 创建 Storyboard、ClipPlan 等草稿 |
| `assign_materials` | 将候选绑定到计划槽位 |
| `request_user_confirmation` | 创建用户确认停点 |

当前没有 Render、Export、Media、生成、擦除、字幕、画幅、配音或外部发布 Tool。

### 3.4 当前数据模型

素材侧只有两级对象：

```text
Video → Clip
```

计划侧使用：

```text
TaskBrief
→ CreativeBrief
→ Storyboard
→ ClipPlan
→ ClipRequirement
→ CandidateSet
→ MaterialAssignment
```

`MaterialAssignment` 支持 `proposed / confirmed / locked / superseded` 等状态，能够表达推荐、确认、锁定和局部替换。

## 4. 覆盖情况总览

| 状态 | 判断 |
|---|---|
| 完整满足 | 核心 Search/Similar、Video 规划、局部候选替换等后端语义 |
| 部分满足 | 找爆款、推荐、会话恢复、跟品骨架、反馈事件、外部视频表示 |
| 未满足 | 槽位生成、爆款复刻、做同款、六项媒体技能、合成、上传下载、资产回流 |
| 与 PRD 冲突 | 当前将大量 P0 媒体能力与个人资产能力直接排除；跟品默认流程仍偏向 Ads 草稿和发布 |

## 5. 逐项能力覆盖矩阵

| PRD 原型能力 | 当前 Video Agent / 系统设计 | 判断 | 主要缺口 |
|---|---|---|---|
| 按文字描述找视频或片段 | SearchPlan、CandidateSet、Video/Clip 两级结果 | 部分满足 | 结果页、搜索卡片和完整画布未建模 |
| 按产品 ID 精确找片 | Search 支持文本 Query 和少量硬过滤 | 部分满足 | 没有 `product_id` 精确过滤和商品绑定 |
| 按图片或视频参考找片 | Similar 支持 Video/Clip Seed | 部分满足 | 用户上传媒体、视觉理解、附件到 Seed 的链路缺失 |
| 内部视频、外部视频、AI 片段混排 | Video/CandidateSet 可表达视频和片段 | 部分满足 | 外部召回、行业参考、AI 片段生成和来源治理不完整 |
| 对话最多 9 条结果，仍有“查看全部” | CandidateSet 支持分页 | 部分满足 | 后端分页不等于 PRD 的 9 卡预览和全部结果交互 |
| 打开视频、时间轴和槽位 | Video/Clip/ClipRequirement | 部分满足 | 画布、播放器、时间轴和卡片状态没有服务契约 |
| 搜相似并替换原槽位 | Similar + Assignment 局部重算 | 基本满足 | 产品级结果卡、来源连线和操作投影仍需补充 |
| 整片搜相似 | Similar 支持 Video Seed | 基本满足 | 整片参考的呈现和“查看整片”未定义 |
| 推荐下一段或下一批候选 | Recommendation 仅支持 `clip_candidate` | 部分满足 | 其余推荐场景、动机解释和会话内重排不完整 |
| 推荐场景和场景提示词 | ClipRequirement 可承载基础目标 | 不满足 | 没有独立推荐场景对象、场景提示词和 DR-07/08 数据 |
| 槽位“去生成” | 没有生成 Tool 或生成任务 | 不满足 | 提示词输入、生成进度、结果归属和原槽位绑定缺失 |
| 做同款 | 无工作流、无生成能力 | 不满足 | 参考结构保持、换要素、参数确认和结果预览缺失 |
| 整片爆款复刻 | 只有参考视频和规划对象的概念 | 不满足 | 产品、人物、场景、模型、比例、时长、分辨率及参考图校验缺失 |
| 多选镜头、批量替换、撤销 | 有局部 Assignment 和 Artifact 版本思想 | 部分满足 | 批量操作、最近八次撤销和并发修改校验缺失 |
| 上传视频替换槽位 | 无上传/媒体素材接口 | 不满足 | 文件校验、媒体入库、预览引用和结果替换缺失 |
| 按当前槽位顺序合成成片 | 无合成/渲染服务 | 不满足 | 合成前校验、转码、拼接、衍生成片和新会话映射缺失 |
| 下载槽位或衍生视频 | 无导出能力 | 不满足 | 下载权限、文件命名、失败降级和资产可见性缺失 |
| 六项技能 | 当前 Tool 白名单没有对应 Skill | 不满足 | 输入、追问、结果、音频/视频媒体和恢复规则均缺失 |
| 外部视频和无槽位视频 | Video 可表示外部视频 | 部分满足 | 外部视频实时理解、自动切片和深度二创仍无生产方案 |
| 全链路跟品任务 | 主 Workflow、DomainInvocationPort 和 Mock Adapter 骨架 | 部分满足 | 真实商品、页面、文案、视频和交付服务均未形成闭环 |
| 落地页诊断与编辑 | Landing Page 领域契约 | 部分满足 | 图片级诊断、人工编辑保护、撤销和页面快照仍未实现 |
| 多视频共享口播与文案 | CopyPackage 可表达 | 部分满足 | 多视频共享、单侧编辑同步、试听和版本恢复未定义 |
| 视频裂变和 BGM | 无对应能力 | 不满足 | 参考成片派生子版本、BGM 上传、选择和预览缺失 |
| 跟品资产包 ZIP | Workflow 可以表达交付状态 | 不满足 | 页面、视频、文案、音频、BGM 和素材清单打包未实现 |
| 会话保存与恢复 | Session、Task、Checkpoint、Artifact 基础较好 | 部分满足 | 画布模式、当前视频、结果卡、上传引用和跨端恢复不完整 |
| 用户偏好与记忆 | Session 和有限项目上下文 | 部分满足 | 没有 User Memory、Episodic Memory 和可修改/删除的偏好对象 |
| 收藏与分享 | 未纳入需求映射 | 不满足 | 收藏、只读分享、访问权限和有效期缺失 |
| 反馈影响当次检索 | Feedback 事件和 CandidateSet 关联 | 部分满足 | 只有事件记录，没有曝光/点击/跳过/重搜对下一轮排序的回写规则 |
| 个人资产、15 天保护期和回流 | 当前设计明确排除 | 不满足 | 与 PRD G4、REQ-E02、NFR-10 直接冲突 |
| 生成中并行浏览和恢复 | Task/Waiting/Resume 基础存在 | 部分满足 | 检索任务有状态，媒体生成、合成与技能任务没有完整生命周期 |
| 产品级异常处理 | 零结果、预算、重试和部分成功有定义 | 部分满足 | 媒体读取、上传、导出、素材失效和结果卡级错误未覆盖 |

## 6. 数据与契约差距

### 6.1 Video / Clip 不足以承载原型信息

当前 `Video` 主要包含：

- ID、标题、来源类型、时长、宽高、帧率、预览、可用性、标签、版本和时间。

当前 `Clip` 主要包含：

- 父 Video、起止时间、时长、预览、关键帧、语义摘要、标签、质量、可用性和模型版本。

PRD 还需要：

- 整片和槽位反推提示词。
- 整片和槽位口播文本及音频引用。
- 成片订单、转化、点击率、留存和成本。
- 槽位类型、状态和业务语义。
- 原版与当前版引用。
- 衍生视频和生成来源。
- BGM 选择与音频引用。
- 个人资产归属、可见性和保护期。

这些字段不能全部塞入 `Video` 或 `Clip` 本身。建议拆成独立的语义加工、投放表现、编辑决策和资产投影对象，再通过引用挂回 Video/Clip。

### 6.2 ClipRequirement 不能完整表达交互槽位

当前 ClipRequirement 主要表达创作需求：

- 叙事角色。
- 视觉目标。
- 目标时长。
- 硬约束、软偏好、兜底和证据要求。

PRD 的“槽位”还是用户可操作对象，需要额外表达：

- 当前采用的 Clip。
- 是否处于生成中。
- 用户是否锁定。
- 最近一次替换。
- 批量操作和撤销状态。
- 原槽位与衍生结果关系。
- 槽位级提示词和口播。

这些状态应属于 Timeline/EditDecision/Assignment 投影，不能只是计划文字。

### 6.3 缺少入口级任务 Schema

当前 Video Task 主要只有：

```json
{
  "goal": "自然语言目标",
  "mode": "creation",
  "constraints": {},
  "execution": {}
}
```

这不足以区分：

- 这是找爆款、视频二创、爆款复刻还是技能任务。
- 入口要求的必填参数是什么。
- 应执行哪些动作、禁止哪些动作。
- 结果应进入会话、画布还是资产。
- 哪个参数缺失时需要追问。

建议增加明确的 `entry_type` 或 `task_type`，并把各入口的必填输入和允许输出定义成版本化模板。

## 7. 工作流与 Agent 边界问题

### 7.1 保持 Video Agent 的窄边界是正确的

不应为了满足 PRD 而让 Video Domain Agent 直接执行 FFmpeg、渲染、转码、导出或外部投放。这样会破坏当前设计最重要的优点：

- 领域职责清晰。
- 媒体执行和规划解耦。
- Tool 权限和副作用可控。
- 检索与规划结果可审计、可复用。

### 7.2 缺少与 Video Agent 相邻的媒体能力层

当前架构的问题不是 Agent 不够“全能”，而是没有一个独立的媒体能力 Workflow：

```text
Video Domain Agent
  理解、规划、选片、分配、声明媒体动作意图

Video Action / Media Capability Workflow
  执行生成、擦除、字幕、口播、画幅、浮层、BGM、合成和导出

Canvas / Asset Projection
  维护结果卡、槽位操作、任务进度、资产和会话视图
```

推荐让 Video Agent 输出声明式 Action Plan，例如：

```text
generate_clip
replace_slot
apply_voiceover
erase_object
change_aspect_ratio
overlay_selling_point
compose_timeline
export_asset
```

由工作流调用对应媒体能力 Port，执行前按副作用等级进行确认。简单技能可以走确定性模板，不必启动 Agent。

### 7.3 四入口缺少显式路由映射

当前 Router 只按复杂度、领域数、副作用和审批判断 R0–R4，但没有把 PRD 的四个智能体入口映射到固定参数和固定结果。

至少要明确：

| 入口 | 必需上下文 | 主要输出 |
|---|---|---|
| 找爆款 | 产品/画面/素材、市场、平台、来源 | 视频/Clip 候选和证据 |
| 视频二创 | 成片、槽位、修改动作 | 替换方案、衍生成片或资产 |
| 爆款复刻 | 参考片、产品、人物、场景、比例、时长等 | 复刻 Artifact 和生成结果 |
| 全链路跟品 | 商品、目标市场、平台、处理组合 | 页面方案、文案、视频及资产包 |

### 7.4 跟品默认流程与最新 PRD 不完全一致

当前跨域默认链路仍以 Ads 草稿和发布作为末端：

```text
Product
→ Video / Landing Page
→ Copy
→ Video Plan / Landing Plan
→ Ads
→ Review
→ Publish 门禁
```

PRD 最新版跟品工作台则停在：

```text
商品
→ 克隆/获取原页
→ 诊断
→ 页面、口播、文案、视频
→ 下载资产包
```

PRD 明确说明逐步审批、按线路创建预算广告草稿属于旧流程，真实发布入口仍需确认。因此跨域能力可以保留 Ads 作为可选通用能力，但不能把 Ads 默认视为跟品主路径的必需末端。

## 8. 推荐与反馈差距

当前 Recommendation 只有 `clip_candidate`。PRD 还要求：

- 品类和槽位类型对应的历史较好画面。
- 每个试点槽位类型至少 3 个推荐场景。
- 每个推荐场景对应可编辑、可提交的提示词。
- 搜索曝光、点击、跳过、重搜和槽位替换影响下一轮结果。
- 显式用户偏好和隐式行为偏好共存，显式偏好优先。

当前 Feedback 事件覆盖曝光、点击、采用、替换和保留，但缺少：

- 当次会话内重排策略。
- 曝光位置和归因上下文。
- 跳过和重搜的负向权重规则。
- 长期偏好更新。
- User/Episodic Memory 的读写与遗忘策略。

因此反馈目前只能“记录”，尚不能形成 PRD 要求的推荐闭环。

## 9. 验收体系差距

PRD 的正式验收是 `AC-01～AC-18`，覆盖：

- 首页案例和技能。
- 广告库排序与筛选。
- 找片结果展示。
- 跟品补参、诊断和交付。
- 槽位搜索、生成、多选、替换和撤销。
- 会话恢复。
- 复刻与人像参考校验。
- 无槽位视频和导出异常。
- 窄屏和深色主题。

当前 v1.0 主要使用后端切片 `A01–A31`。它能验证：

- Schema 和 Mock 稳定性。
- Direct/Agent 路由。
- Waiting、恢复和预算。
- CandidateSet、Assignment 和跨域 Artifact。

但它不能证明 PRD 原型可用，也不能覆盖大量媒体和 UI 行为。

此外，现有 [PRD 需求映射](./final-v1.0/07_问题清单与裁决记录.md) 仍存在追溯缺口：

- `REQ-E01 收藏与分享`未出现在映射表中。
- `REQ-E07 行为探针与片段预生成`未出现在映射表中。
- 部分 P0 被直接标为排除，但仍保留在 PRD 原型和功能需求中。
- PRD 的待确认项表示生产细节未定，不表示对应的原型能力和工作流可以不存在。

## 10. 建议的目标架构

建议保持一个明确的领域 Agent，同时补齐产品编排和媒体能力：

```text
万镜魔方 / 乘风智能体
│
├─ Intent & Experience Router
│  ├─ 四类智能体入口
│  ├─ 六类技能模板
│  └─ Direct / Agent / Workflow 路由
│
├─ Video Domain Agent
│  ├─ 目标理解与澄清
│  ├─ CreativeBrief / Storyboard / ClipPlan
│  ├─ Search / Recommend / Similar
│  └─ MaterialAssignment / 局部修改
│
├─ Media Capability Workflow
│  ├─ 片段生成、擦除、画幅、字幕
│  ├─ 口播、卖点浮层、BGM
│  ├─ 上传、合成、导出
│  └─ 异步进度、重试、取消、恢复
│
├─ Product Follow Workflow
│  ├─ 商品与目标线路
│  ├─ 页面诊断与编辑保护
│  ├─ 共享口播与文案
│  ├─ 多视频裂变与二创
│  └─ 资产包交付
│
├─ Session / Canvas / Asset Projection
│  ├─ 结果卡与槽位状态
│  ├─ 原版/当前版对照
│  ├─ 收藏、分享和权限
│  └─ 资产保护期与回流
│
└─ Feedback & Memory
   ├─ 会话内实时重排
   ├─ 显式偏好
   ├─ 长期行为画像
   └─ 可修改、可删除记忆
```

### 10.1 对 Video Domain Agent 的调整

不建议把渲染、上传、导出和广告发布塞入当前 8 个 Tool。建议：

1. 保持 Video Agent 的检索、规划和分配职责。
2. 增加声明式 `MediaActionPlan` 或同等 Artifact。
3. 由独立 Media Capability Workflow 执行媒体动作。
4. Agent 只选择动作、参数和候选，不直接持有媒体执行凭证。
5. L2 预览、L3 修改、L4 发布继续按副作用分级控制。

### 10.2 必须补充的对象

- `EntryTask` 或任务模板：记录入口类型和必填参数。
- `RecommendedScenario`：推荐场景、适配槽位类型和提示词。
- `MediaActionPlan`：声明生成、编辑、合成和导出动作。
- `SkillTask / SkillResult`：六项技能的输入、追问和结果。
- `EditDecision`：槽位替换、批量操作、撤销和合成前状态。
- `DerivedVideo`：生成视频、合成视频与基础视频的关系。
- `VideoPerformanceSnapshot`：投放指标和时间窗口。
- `PersonalAsset`：归属、可见性、保护期和回流状态。
- `UserPreference / UserMemory`：显式偏好和可管理记忆。
- `SessionCanvasProjection`：当前视频、槽位、结果卡和画布状态。

### 10.3 必须补充的验收

至少建立以下追溯链：

```text
PRD G / REQ / BR / DR / NFR / OI
  → 设计对象
  → API 或 Workflow
  → Ticket
  → Mock 或真实 Adapter
  → PRD AC-01～AC-18
  → 证据
```

任何标为“待确认”的 PRD 项，都应保留：

- 原型已存在的行为说明。
- 生产实现待决策的具体问题。
- Mock 方案。
- 可回退的 Adapter 边界。
- 验收占位。

不能把“生产细节待确认”直接转化为“设计阶段不建立能力”。

## 11. 最终判定

### 11.1 Video Domain Agent 自身

**基本合理，但不能称为完整。**

它已经具备视频领域 Agent 的核心骨架，尤其是：

- 小候选集原则。
- 规划与执行分离。
- 工具白名单。
- 证据约束。
- 局部重算。
- Task 与 Run 状态分离。

当前还需要解决：

- 入口任务契约。
- PRD 用语到 Video/Clip/ClipRequirement 的提示词归一。
- 推荐场景和提示词对象。
- 视频表现、口播和编辑状态的数据模型。
- 反馈闭环。

### 11.2 PRD 完整原型

**不能完全满足。**

主要阻塞项包括：

1. 六项媒体技能没有能力层。
2. 槽位生成、做同款和爆款复刻没有工作流。
3. 合成、上传、下载和资产包没有交付链路。
4. 全链路跟品只有领域骨架，没有产品闭环。
5. 画布、结果卡和会话恢复缺少交互投影。
6. 个人资产、收藏、分享、保护期和回流未覆盖。
7. 反馈尚未真正影响推荐。
8. PRD 验收用例没有进入当前主验收体系。

### 11.3 建议的正式结论

> 当前方案是“可扩展的 Video Domain Agent 检索与规划内核”，但还不是“完整支撑万镜魔方原型”的 Agent 与媒体创作架构。应保留其领域边界，在外部补齐入口模板、媒体能力 Workflow、会话画布投影、资产治理和推荐反馈闭环，再以 PRD AC-01～AC-18、REQ、DR 和 NFR 作为最终验收依据。

