# 视频素材 Agent 与画布交互架构设计方案

**版本：V1.0**

## 一、设计目标

构建一套面向视频素材业务的 Agent–Canvas 交互架构，使视频素材 Agent 能够理解用户当前的创作任务和画布状态，围绕用户意图自主规划任务，并通过画布与用户进行协同操作。

画布不仅是素材的展示界面，也是 Agent 与用户共同完成视频创作任务的可视化工作空间。

### 1.1 核心目标

1. **画布感知**：Agent 能够理解当前项目、素材、时间轴、分镜及其状态。
2. **任务规划**：Agent 根据用户意图和当前画布上下文，规划合理的业务操作。
3. **协同操作**：Agent 能够向画布提出操作建议、展示执行计划，并在授权后推动业务操作。
4. **状态一致**：Agent、业务服务和前端画布对业务状态具有一致的认知。
5. **过程可见**：用户能够理解 Agent 正在执行什么、为什么执行，以及执行结果。
6. **人工协同**：用户可以随时介入、修改、确认或接管任务。

### 1.2 核心设计原则

- Agent 负责理解、决策和规划，不直接操作前端组件。
- 业务操作由领域 Skill 和 Workflow 承担，不允许绕过业务规则。
- 画布负责展示业务状态，并提供用户交互能力。
- 业务数据以业务服务为权威来源，画布状态是业务数据的可视化投影。
- Agent 提出的操作计划与已经提交的业务结果必须明确区分。
- 用户操作和 Agent 操作遵循统一的业务规则与状态管理机制。

---

## 二、总体架构

整体采用分层架构，将 Agent 决策、业务执行、Agent–Canvas 交互和前端画布进行职责隔离。

### 2.1 架构分层



#### 第一层：Video Agent Layer

负责理解用户意图、分析创作任务、读取画布上下文、制定任务计划和协调业务能力。

核心组成：

- **Video Agent**：视频素材领域的主 Agent，负责整体任务理解与决策。
- **Intent Understanding**：识别用户意图，理解用户希望完成的操作。
- **Context Understanding**：理解当前项目、画布、素材和创作状态。
- **Task Planner**：将用户目标拆解为可执行的任务步骤。
- **Skill Orchestrator**：选择并调用相应的领域 Skill。
- **Canvas Interaction Tools**：获取画布上下文、提交操作提案、获取执行结果等交互能力。

Agent 不直接调用前端画布组件，也不直接修改业务数据库。

#### 第二层：Video Domain Skill & Workflow Layer

负责视频素材领域的业务能力和业务流程执行。

核心组成：

- **Material Search Skill**：素材检索与筛选。
- **Material Recommendation Skill**：素材推荐与匹配。
- **Material Analysis Skill**：素材内容理解、标签和属性分析。
- **Storyboard Skill**：分镜理解与规划。
- **Timeline Planning Skill**：时间轴规划与素材编排。
- **Material Assignment Skill**：素材与分镜、镜头之间的匹配。
- **Workflow Engine**：承载需要确定性执行的业务流程。

Skill 负责封装领域能力，Workflow 负责执行具有明确规则和状态流转的业务过程。

Agent 决定调用什么能力、以什么顺序完成任务；Skill 和 Workflow 负责具体的领域操作。

#### 第三层：Agent–Canvas Interaction Layer

负责连接 Agent Runtime 与前端画布，是 Agent 和画布之间的统一交互边界。

核心组成：

- **Context Service**：提供画布上下文和状态快照。
- **Command Gateway**：接收并管理 Agent 发起的画布交互请求。
- **Event Gateway**：接收画布事件并传递给 Agent。
- **State Sync**：协调业务状态与画布状态同步。
- **Operation Manager**：管理操作提案、确认、执行状态和结果。
- **Session Manager**：管理 Agent Execution 与 Canvas Session 的关联。

该层不负责视频素材业务决策，也不直接执行领域业务操作。

#### 第四层：Frontend Canvas SDK

负责将 Agent 的交互意图和业务状态转换为前端画布行为。

核心组成：

- **Context Manager**：维护当前画布上下文。
- **Command Runtime**：处理画布展示与交互命令。
- **Event Manager**：采集用户操作和画布状态事件。
- **State Manager**：维护画布本地状态。
- **Sync Manager**：接收并应用业务状态投影。
- **Draft Manager**：管理尚未提交的操作提案和临时状态。
- **Operation Manager**：呈现操作过程、确认状态和执行结果。

#### 第五层：Video Canvas & Business Services

包含视频素材业务服务以及前端画布。

主要业务服务：

- Project Service
- Material Service
- URRE Retrieval & Recommendation
- Storyboard Service
- Timeline Service
- Video Processing Service

主要画布：

- **Material Board**：素材浏览、检索和推荐。
- **Storyboard Canvas**：分镜结构和镜头规划。
- **Timeline Canvas**：素材编排、时间轴和剪辑关系。

业务服务负责权威业务数据，画布负责业务数据的可视化呈现和用户交互。

### 2.2 总体架构关系

整体交互链路：

**用户 → Video Agent → Domain Skill / Workflow → Business Services**

**Video Agent ↔ Agent–Canvas Interaction ↔ Canvas SDK ↔ Video Canvas**

**Business Services → State Sync → Canvas SDK → Video Canvas**

三条链路分别承担：

1. Agent 决策与业务能力调用。
2. Agent 与画布之间的双向交互。
3. 业务状态向画布的同步和投影。

三条链路共同构成完整的 Agent–Canvas 协同体系。

---

## 三、Agent 与画布的交互模型

Agent 与画布之间采用四种核心交互机制：

**Context、Command、Event、State Sync。**

四种机制分别解决上下文理解、交互意图表达、用户行为感知和状态一致性问题。

### 3.1 Context：上下文感知

Context 是 Agent 理解当前画布和创作任务的基础。

Agent 在执行任务之前，需要获取与当前意图相关的上下文，而不是无差别读取整个画布。

Context 主要包含：

| 上下文类型 | 内容 |
|---|---|
| Project Context | 项目基本信息、创作目标、项目配置 |
| Canvas Context | 当前画布类型、视图状态、画布版本 |
| Material Context | 当前素材、素材属性、素材来源 |
| Storyboard Context | 分镜结构、镜头信息、镜头之间的关系 |
| Timeline Context | 时间轴结构、轨道、素材位置和时间信息 |
| Selection Context | 当前选中对象、选中范围 |
| Operation Context | 正在执行的任务、待确认操作和历史结果 |
| User Context | 当前用户操作意图及必要的业务偏好 |

Context 需要支持两种获取方式：

- **主动获取**：Agent 根据当前任务主动查询所需上下文。
- **事件触发**：用户选中素材、修改分镜或调整时间轴后，画布向 Agent 发送相关事件。

Context 的核心作用是让 Agent 理解：

- 当前正在处理哪个项目？
- 当前画布处于什么状态？
- 用户正在关注什么对象？
- 当前任务已经完成到什么程度？
- 下一步操作受到哪些业务条件约束？

Context 是 Agent 的决策依据，但不是业务数据的权威存储。

### 3.2 Command：交互意图与操作表达

Command 用于表达 Agent 希望画布发生什么变化。

这里必须区分三种不同性质的操作。

#### A. Business Action：业务操作

用于改变真实的业务数据和业务关系。

例如：

- 将素材添加到当前项目。
- 将素材分配给指定分镜。
- 调整时间轴上的素材顺序。
- 修改镜头时长。
- 删除项目中的素材。
- 更新分镜与素材之间的关联。

业务操作必须经过 Video Skill 和 Workflow，由业务服务完成数据写入。

画布不能因为收到一个业务 Command 就自行修改权威业务数据。

#### B. Canvas Projection：业务状态投影

用于将已经完成的业务操作同步到画布。

例如：

- 展示新增的素材。
- 更新分镜中的素材关联。
- 更新时间轴上的素材位置。
- 展示修改后的镜头时长。
- 移除已经删除的素材。

Projection 的数据来源是业务服务确认后的业务状态。

它是业务事实在画布上的表现，不是一次新的业务操作。

#### C. Presentation Command：画布呈现操作

用于改变画布的交互和视觉状态，不改变业务事实。

例如：

- 选中某个素材。
- 高亮指定镜头。
- 滚动到某个时间轴位置。
- 展开素材详情面板。
- 定位到指定分镜。
- 聚焦某个画布区域。

此类操作可以由 Canvas SDK 直接执行。

#### 三类操作的职责边界

| 操作类型 | 执行主体 | 是否修改业务数据 |
|---|---|---|
| Business Action | Skill / Workflow / Business Service | 是 |
| Canvas Projection | State Sync / Canvas SDK | 否，反映已确认的业务事实 |
| Presentation Command | Canvas SDK | 否 |

这是整个架构中最重要的职责边界。

### 3.3 Event：画布事件感知

Event 用于将画布上的用户行为和状态变化反馈给 Agent。

主要分为三类：

**用户交互事件**

- 用户选中素材。
- 用户切换画布。
- 用户修改分镜。
- 用户调整时间轴。
- 用户确认或拒绝操作提案。

**画布状态事件**

- 画布初始化完成。
- 画布状态发生变化。
- 画布对象加载完成。
- 画布同步完成。
- 画布发生异常。

**业务操作反馈事件**

- 操作提案已创建。
- 操作等待确认。
- 业务操作执行成功。
- 业务操作执行失败。
- 业务状态投影已应用。

Agent 根据事件更新任务上下文，判断是否需要继续执行、重新规划或等待用户操作。

Event 不等同于业务数据本身。涉及业务事实的事件，应以业务服务确认的结果为准。

### 3.4 State Sync：状态同步

State Sync 负责保证业务服务与前端画布之间的状态一致性。

整体关系：

**Business Service → Business Event / Snapshot → State Sync → Canvas SDK → Canvas State**

其核心职责包括：

1. 接收业务服务产生的业务状态变化。
2. 将业务变化转换为画布能够理解的状态投影。
3. 将投影推送给对应的 Canvas Session。
4. 由 Canvas SDK 应用投影并更新画布。
5. 接收画布同步确认。
6. 在同步失败时支持后续恢复。

需要明确两个独立状态：

| 状态 | 含义 |
|---|---|
| Business Status | 业务操作是否成功提交 |
| Canvas Sync Status | 业务结果是否成功同步到画布 |

例如，Agent 成功添加三个素材到项目，但用户浏览器断开连接：

- Business Status：SUCCESS
- Canvas Sync Status：PENDING

这意味着业务操作已经完成，只是前端尚未同步。

画布重新连接后，应根据最新业务状态恢复，而不是重新执行一次添加素材的业务操作。

---

## 四、Agent 与画布的协同执行流程

整体采用：

**理解任务 → 获取上下文 → 规划操作 → 展示提案 → 用户确认 → 业务执行 → 状态同步 → 结果反馈**

### 4.1 标准交互流程

1. 用户向 Video Agent 提出任务。
2. Agent 理解用户意图，识别任务涉及的业务对象。
3. Agent 通过 Context Service 获取当前项目和画布上下文。
4. Agent 结合上下文制定任务计划。
5. Agent 调用相应的 Video Domain Skill。
6. Skill 完成必要的检索、推荐、分析和规划。
7. Agent 生成结构化操作提案。
8. 操作提案通过交互层发送给画布，以 Draft 形式展示。
9. 用户确认、修改或拒绝提案。
10. 确认后，由 Workflow 执行业务操作。
11. 业务服务完成数据写入并产生新的业务状态。
12. State Sync 将业务状态转换为 Canvas Projection。
13. Canvas SDK 应用投影并更新画布。
14. Agent 获取业务执行结果和画布同步状态。
15. Agent 向用户反馈最终结果。

### 4.2 以“推荐素材并添加到视频项目”为例

用户提出：

“帮我为这个视频项目推荐一些适合的城市夜景素材，并添加到对应镜头中。”

执行过程：

**第一阶段：理解与分析**

- Agent 获取当前项目和分镜上下文。
- 理解项目的创作主题、风格和镜头需求。
- 确定需要检索和推荐的素材类型。

**第二阶段：素材检索与规划**

- 调用 Material Search Skill。
- 调用 Material Recommendation Skill。
- 获取候选素材及其相关属性。
- 分析素材与目标镜头的匹配关系。
- 生成素材分配计划。

**第三阶段：画布提案**

- Agent 将素材分配计划组织为结构化 Artifact。
- 通过 Canvas Interaction 将提案发送给画布。
- 画布展示候选素材、目标镜头和分配关系。
- 用户可以查看、调整和确认。

**第四阶段：业务执行**

- 用户确认操作。
- Agent 触发相应的业务 Workflow。
- Workflow 校验业务条件。
- Project / Timeline 等业务服务完成数据更新。

**第五阶段：状态同步**

- 业务服务产生新的业务状态。
- State Sync 生成对应的 Canvas Projection。
- Canvas SDK 更新素材看板、分镜和时间轴。
- 画布返回同步结果。

**第六阶段：结果反馈**

Agent 根据业务执行状态和画布同步状态，向用户说明：

- 推荐了哪些素材。
- 哪些素材已经成功添加。
- 素材被分配到了哪些镜头。
- 是否存在未完成或需要处理的事项。

---

## 五、操作提案与业务执行管理

为了让 Agent 与用户能够共同完成复杂任务，需要将操作提案和业务执行结果分离。

### 5.1 Draft：操作提案

Draft 表示 Agent 已经规划、但尚未正式提交的操作。

例如：

- 推荐素材列表。
- 素材与分镜的匹配计划。
- 时间轴调整计划。
- 镜头修改建议。

Draft 的主要作用是让用户提前看到 Agent 准备做什么。

Draft 不属于已经生效的业务状态，也不能被视为业务操作成功。

用户可以：

- 确认提案。
- 修改提案。
- 部分确认。
- 拒绝提案。

### 5.2 Artifact：结构化业务产物

对于视频素材创作任务，Agent 不应只输出自然语言操作描述，而应生成结构化 Artifact。

主要包括：

| Artifact | 作用 |
|---|---|
| CreativeBrief | 创作目标和需求描述 |
| Storyboard | 分镜结构和镜头规划 |
| ShotPlan | 镜头级执行计划 |
| MaterialAssignment | 素材与镜头的匹配关系 |
| EditDecision | 剪辑决策和调整建议 |
| TimelineIR | 结构化时间轴描述 |

Artifact 是 Agent 规划和业务流程之间的结构化信息载体。

Agent 可以根据 Artifact 生成操作提案；Workflow 可以根据确认后的 Artifact 执行业务操作；画布可以根据 Artifact 展示相应内容。

需要注意：Artifact 本身不等于业务数据。只有经过业务流程确认并写入业务服务后，相关内容才成为正式业务状态。

### 5.3 Operation：操作生命周期

一次操作应具有明确的生命周期：

**CREATED → PROPOSED → WAITING_CONFIRMATION → EXECUTING → SUCCEEDED / FAILED**

其中：

- CREATED：操作已创建。
- PROPOSED：操作提案已生成。
- WAITING_CONFIRMATION：等待用户确认。
- EXECUTING：业务操作执行中。
- SUCCEEDED：业务操作成功。
- FAILED：业务操作失败。

业务执行完成后，画布同步状态独立维护：

**PENDING → SYNCING → SYNCED / SYNC_FAILED**

这样可以避免把业务执行失败、画布同步失败和用户尚未确认混为一谈。

---

## 六、用户与 Agent 的协同编辑

画布同时支持用户主动编辑和 Agent 自动操作。

两者必须遵循统一的业务规则。

### 6.1 用户操作

用户操作分为两类：

**纯交互操作**

例如选中、缩放、滚动、展开面板等。

由 Canvas SDK 本地处理，不需要触发业务写入。

**业务编辑操作**

例如添加素材、调整时间轴、修改素材归属和镜头时长等。

需要经过业务服务确认后才能成为正式业务状态。

用户可以先看到本地临时效果，但在服务端确认之前，不能将其视为已经提交的业务事实。

### 6.2 Agent 操作

Agent 不能绕过业务流程直接修改画布中的正式业务对象。

Agent 的操作过程为：

1. 获取当前画布上下文。
2. 生成操作提案。
3. 展示操作内容。
4. 根据授权和业务规则决定是否需要用户确认。
5. 调用业务 Workflow。
6. 等待业务结果。
7. 将最终业务状态同步到画布。

### 6.3 并发编辑与冲突处理

当用户和 Agent 同时编辑同一业务对象时，需要通过业务版本控制识别冲突。

例如：

- Agent 正在为镜头 A 分配素材。
- 用户同时手动修改镜头 A 的素材。
- Agent 原有操作计划所依据的业务状态已经发生变化。

此时不能直接覆盖用户最新修改。

系统应识别版本冲突，并根据业务规则选择：

- 重新获取最新上下文。
- 重新生成操作计划。
- 请求用户确认。
- 中止当前操作。

核心原则：**任何一方都不能在不知情的情况下覆盖另一方已经提交的业务修改。**

---

## 七、核心状态与一致性模型

整个系统存在三个不同层面的状态。

### 7.1 Agent Execution State

表示 Agent 当前任务的执行状态。

例如：

- 理解用户意图。
- 获取上下文。
- 规划任务。
- 调用 Skill。
- 等待用户确认。
- 执行业务操作。
- 汇总结果。

### 7.2 Business State

表示视频项目的真实业务状态。

例如：

- 项目包含哪些素材。
- 素材与镜头之间的关联。
- 分镜结构。
- 时间轴轨道和素材位置。
- 镜头时长和剪辑关系。

Business State 以业务服务为唯一权威来源。

### 7.3 Canvas State

表示前端画布当前的展示和交互状态。

例如：

- 当前选中对象。
- 画布布局。
- 视口位置。
- 展开的面板。
- 已经应用的业务状态投影。
- 尚未提交的 Draft。

Canvas State 不应成为业务数据的第二个权威来源。

### 7.4 状态关系

三种状态之间的关系：

- Agent Execution State 决定任务当前执行到哪一步。
- Business State 决定业务操作是否真正生效。
- Canvas State 决定业务结果是否已经在画布上正确呈现。

三者彼此关联，但不能合并成一个状态模型。

### 7.5 版本控制

至少需要区分：

| 版本 | 作用 |
|---|---|
| Business Version | 业务对象或项目的权威版本 |
| Canvas Revision | 画布当前应用的状态版本 |
| Event Sequence | 画布事件和状态同步的顺序标识 |
| Object Version | 单个业务对象的版本 |

业务操作以 Business Version 作为并发控制依据。

Canvas Revision 用于判断画布是否已经应用最新状态。

Event Sequence 用于识别事件顺序和同步进度。

---

## 八、核心组件职责与边界

| 组件 | 核心职责 | 不负责的内容 |
|---|---|---|
| Video Agent | 意图理解、任务规划、Skill 编排 | 直接修改业务数据库 |
| Video Domain Skill | 视频素材领域能力封装 | 前端画布状态管理 |
| Workflow | 确定性业务流程执行 | Agent 意图决策 |
| Context Service | 获取和组织画布上下文 | 业务决策 |
| Command Gateway | 管理画布交互请求 | 执行领域业务操作 |
| Event Gateway | 接收和分发画布事件 | 维护业务权威状态 |
| State Sync | 业务状态向画布投影 | 业务规则和业务决策 |
| Operation Manager | 管理操作提案和执行状态 | 直接修改业务数据 |
| Canvas SDK | 管理画布状态、事件和呈现 | 作为业务数据权威来源 |
| Video Business Services | 维护视频项目权威业务数据 | Agent 任务规划 |

---

## 九、整体架构总结

本方案的核心不是让 Agent 直接控制画布，而是建立一套明确的 Agent–Business–Canvas 协同机制。

三条核心原则：

**1. Agent 决策，Skill 承载能力，Workflow 执行业务。**

Agent 理解用户目标并决定如何完成任务；Skill 封装视频素材领域能力；Workflow 负责可靠地执行业务操作。

**2. 业务服务负责事实，画布负责呈现，交互层负责协调。**

业务数据只能由业务服务确认和维护。画布通过状态投影展示业务事实，交互层负责 Agent 与画布之间的上下文、命令、事件和状态同步。

**3. Draft 是提案，Artifact 是结构化产物，Business State 才是正式业务结果。**

Agent 可以先规划和展示操作，再由用户确认和业务流程执行。画布不能把提案误认为已经生效的业务状态。

最终形成：

**用户提出创作目标 → Video Agent 理解任务 → 获取画布上下文 → 调用领域 Skill → 生成结构化 Artifact → 画布展示操作提案 → 用户确认 → Workflow 执行业务 → State Sync 同步状态 → 画布呈现结果 → Agent 反馈完成情况。**

这套架构使视频素材 Agent 不再只是一个能够调用工具的聊天机器人，而是一个能够理解创作上下文、规划业务任务、与用户协同操作并持续感知执行结果的智能创作 Agent。