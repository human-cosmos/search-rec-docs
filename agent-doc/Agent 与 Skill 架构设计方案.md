# Agent 与 Skill 架构设计方案

---

# 1. 设计背景与目标

## 1.1 设计背景

当前项目需要建设一套企业级 Agent 系统，为用户提供统一的 AI 对话入口，并通过 Agent 调用不同业务领域的能力，完成实际业务操作。

我们需要的是：

- 一个统一的 Agent 对话入口。
- 一套能够理解用户意图的 Agent。
- 一套明确、可复用、可通过 `@` 直接调用的 Skill 能力体系。
- 一套统一的 Tool 调用和业务服务集成机制。
- 一套简单可靠的执行、权限、状态管理机制。

因此，本方案收敛架构，采用更简单的设计。

![](C:\Users\Administrator\Desktop\search-rec-docs\images\视频素材领域 Agent 平台架构图.png)

## 1.2 核心设计原则

| 原则 | 设计要求 |
|---|---|
| 入口统一 | 用户始终通过一个 Agent 对话入口完成交互 |
| 能力独立 | 业务能力通过 Skill 独立封装，而不是全部写进 Agent |
| 明确优先 | 用户通过 @ 明确指定 Skill 时，优先执行指定 Skill |
| 智能补充 | 未明确指定 Skill 时，由 Agent 理解意图并选择能力 |
| 简单优先 | 能用 Tool 或 Workflow 解决的问题，不创建 Agent |
| 执行可靠 | Runtime 统一管理 Tool 调用、状态、权限和异常 |
| 结果可追踪 | 每次执行都有明确的输入、输出和执行记录 |
| 渐进扩展 | 只有真正需要独立智能决策的场景，才引入领域 Agent 或子 Agent |

## 1.3 核心架构结论

本系统采用：

**一个 Platform Agent + 一个 Skill Registry + 一个 Agent Runtime + 一组业务 Tools / Workflows。**

其中：

- Platform Agent：负责理解用户需求、识别能力、协调执行和组织回复。
- Skill：负责封装具有明确业务目标的专业能力。
- Tool：负责提供具体、可调用的原子操作。
- Workflow：负责执行需要固定步骤和状态控制的业务流程。
- Runtime：负责统一执行和管理。
- Business Services：负责实际业务逻辑和数据操作。

不为每一个业务功能创建 Agent，也不要求每一个 Skill 都必须拥有独立 Agent。

---

# 2. 总体架构

## 2.1 架构全景

```text
                         用户
                          │
                          ▼
                 ┌─────────────────┐
                 │  Agent Chat UI  │
                 │                 │
                 │  普通对话       │
                 │  @Skill 调用    │
                 │  文件 / 上下文  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Platform Agent │
                 │                 │
                 │  意图理解       │
                 │  Skill 选择     │
                 │  任务协调       │
                 │  结果组织       │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Skill Registry │
                 │                 │
                 │  Skill 元数据   │
                 │  Skill 定义     │
                 │  Skill 版本     │
                 │  Skill 权限     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Agent Runtime  │
                 │                 │
                 │  Skill 执行     │
                 │  Tool 调用      │
                 │  Workflow 执行  │
                 │  权限校验       │
                 │  状态管理       │
                 └────────┬────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        ┌─────────┐  ┌──────────┐  ┌──────────┐
        │  Tools  │  │Workflows │  │ External │
        │         │  │          │  │ Systems  │
        │业务操作  │  │业务流程   │  │外部系统    │
        └────┬────┘  └────┬─────┘  └────┬─────┘
             │            │             │
             └────────────┼─────────────┘
                          ▼
                 ┌─────────────────┐
                 │ Business Layer  │
                 │                 │
                 │ Domain Services │
                 │ Repositories    │
                 │ Databases       │
                 └─────────────────┘

          Shared Infrastructure:
          Conversation / Execution / Artifact / Event / Audit
```

## 2.2 各层职责

### A. Agent Chat UI

用户统一交互入口。

支持：

- 普通自然语言对话。
- @Skill 明确调用。
- 上传文件和引用上下文。
- 展示 Skill 执行过程。
- 展示结构化执行结果。
- 用户确认和后续操作。

UI 不直接调用业务 API，所有能力调用均通过 Agent Runtime。

### B. Platform Agent

系统唯一默认的用户交互 Agent。

核心职责：

1. 理解用户输入。
2. 识别用户意图。
3. 判断是否需要调用 Skill。
4. 选择适合的 Skill 或 Tool。
5. 组织调用参数。
6. 协调执行过程。
7. 根据执行结果决定下一步。
8. 向用户返回结果。

Platform Agent 不直接承担复杂业务数据操作，也不负责管理底层执行状态。

它是智能决策层，而不是业务服务层。

### C. Skill Registry

Skill 注册中心。

负责：

- Skill 注册和发现。
- Skill 元数据管理。
- Skill 版本管理。
- Skill 启用和停用。
- Skill 可见范围。
- Skill 权限配置。
- Skill 调用说明和参数定义。

### D. Agent Runtime

统一执行环境。

负责：

- 接收 Agent 的执行请求。
- 加载 Skill 定义。
- 执行 Skill。
- 调用 Tool。
- 启动 Workflow。
- 校验用户权限。
- 管理执行状态。
- 处理超时、异常和重试。
- 记录执行日志和调用链。

### E. Tools / Workflows / External Systems

这是实际业务能力的承载层。

Tools 提供原子操作。

Workflows 提供固定流程。

External Systems 提供外部系统能力。

三者通过统一接口接入 Runtime。

---

# 3. Agent 的层级与分类

## 3.1 不再采用复杂的固定 Agent 层级

本方案不再强制采用：

```text
Platform Agent
    │
    └── Domain Agent
            │
            └── Main Agent
                    │
                    └── Sub Agent
```

这样的固定嵌套结构。

因为这容易让每个业务领域都必须配置一个 Agent，每个 Agent 又必须配置若干子 Agent。

实际业务并不需要这样的组织结构。

本方案采用更简单的模型：

```text
                  Platform Agent
                         │
               ┌─────────┼─────────┐
               ▼         ▼         ▼
             Skill A   Skill B   Skill C
               │         │         │
               ▼         ▼         ▼
             Tools     Workflow   External API
```

Platform Agent 可以直接使用所有获得授权的 Skill。

Skill 内部可以调用 Tool、Workflow 或外部服务。

## 3.2 Platform Agent

Platform Agent 是系统的统一智能入口。

它具有跨领域的能力发现和调用能力，但不需要了解每个领域的全部业务实现细节。

例如：

- 用户要求检索视频素材，调用视频检索 Skill。
- 用户要求分析商品，调用商品分析 Skill。
- 用户要求生成文案，调用文案 Skill。
- 用户要求执行广告操作，调用广告管理 Skill。

Platform Agent 主要负责判断应该使用什么能力，而不是亲自完成所有专业工作。

## 3.3 Domain Agent 是否还需要？

Domain Agent 不再作为固定的必选层级。

当某个领域业务足够复杂，存在以下特征时，可以考虑创建独立的 Domain Agent：

- 领域内有大量复杂业务规则。
- 需要较长时间的多轮专业推理。
- 需要独立维护领域上下文。
- 需要协调多个 Skill 和 Workflow。
- 需要独立的领域决策能力。

例如：

```text
Platform Agent
      │
      ├── Video Domain Agent
      │       ├── Skill A
      │       ├── Skill B
      │       └── Skill C
      │
      └── Product Domain Agent
              ├── Skill D
              └── Skill E
```

但这只是复杂业务领域的可选扩展方式。

当前 Video Domain Agent 可以先不作为独立的多 Agent 执行组织，而是将视频领域能力作为一组 Skills 提供给 Platform Agent。

这样既保留未来演进空间，也避免当前过度设计。

## 3.4 子 Agent 是否需要？

子 Agent 不是固定组件。

只有当一个任务确实需要独立的智能分析，并且能够产生独立结果时，才考虑动态创建子 Agent。

例如：

- 需要同时从多个独立专业视角进行分析。
- 任务之间可以并行执行。
- 各个任务需要不同的上下文和专业知识。
- 最终需要对多个独立结果进行汇总。

普通的 Skill 调用、Tool 调用、Workflow 执行都不需要创建子 Agent。

**Skill 是能力封装，Sub Agent 是独立智能执行者，两者不是同一个概念。**

---

# 4. Skill 体系设计

## 4.1 什么是 Skill？

Skill 是一个具有明确业务目标、能够被 Agent 发现和调用的能力单元。

例如：

- 视频素材检索。
- 视频素材推荐。
- 视频素材详情查询。
- 视频素材收藏。
- 商品分析。
- 商品利润测算。
- 广告数据分析。
- 广告计划管理。

Skill 的价值在于：

**将一个专业业务能力封装成 Agent 能够理解、选择和使用的标准化能力。**

它不是一个独立 Agent，也不一定是一个复杂的程序。

一个 Skill 可以由以下内容组成：

1. Skill 基本信息。
2. Skill 使用说明。
3. Skill 适用场景。
4. 输入参数定义。
5. 执行逻辑。
6. Tool / Workflow 绑定。
7. 输出格式定义。
8. 权限和确认要求。

## 4.2 Skill 与 Tool、Workflow 的关系

三者需要明确区分。

| 类型 | 解决的问题 | 示例 |
|---|---|---|
| Skill | 用户要完成什么专业任务？ | 视频素材检索推荐 |
| Tool | 具体能够执行什么操作？ | 调用 URRE、查询素材详情 |
| Workflow | 多个操作按照什么流程执行？ | 批量采用素材并更新项目 |

它们之间的关系：

```text
             User Intent
                  │
                  ▼
                Skill
                  │
           ┌──────┴──────┐
           ▼             ▼
          Tool        Workflow
           │             │
           └──────┬──────┘
                  ▼
            Business Service
                  │
                  ▼
                Result
```

一个 Skill 可以：

- 只调用一个 Tool。
- 调用多个 Tools。
- 启动一个 Workflow。
- 同时调用 Tools 和 Workflow。
- 在必要时通过 Agent 进行多轮推理。

Skill 是能力入口，不是执行技术的限制。

## 4.3 Skill 的分类

建议将 Skill 分为三类。

### 第一类：查询型 Skill

用于获取信息和分析数据。

例如：

- 视频素材检索。
- 视频素材推荐。
- 素材详情查询。
- 商品信息查询。
- 广告数据分析。

特点：

- 通常没有副作用。
- 可以直接返回结果。
- 一般不需要人工确认。

### 第二类：操作型 Skill

用于执行明确的业务操作。

例如：

- 收藏素材。
- 将素材加入项目。
- 移除项目素材。
- 更新素材标签。
- 创建商品记录。

特点：

- 会修改业务状态。
- 必须进行权限校验。
- 重要操作可能需要用户确认。
- 应支持幂等和执行结果查询。

### 第三类：复合型 Skill

用于完成需要多个步骤的业务任务。

例如：

- 根据用户要求检索素材，并将用户选中的素材加入项目。
- 分析商品并生成分析报告。
- 批量处理素材并更新项目状态。

特点：

- 可以调用多个 Tool。
- 可以启动 Workflow。
- 可以有多个执行阶段。
- 需要记录执行状态。

---

# 5. @Skill 设计

## 5.1 为什么需要 @Skill？

Agent 具有自然语言意图理解能力，但完全依靠模型自动判断能力存在一些问题：

- 用户不一定知道系统有哪些能力。
- 模型可能选择错误的能力。
- 同一个用户表达可能对应多个业务功能。
- 某些业务功能具有明确的操作意图。
- 用户希望直接指定某项功能，而不是让 Agent 猜测。

因此需要引入 @Skill 机制。

它的核心价值是：

**用户可以直接指定希望使用的能力，Agent 不需要再次猜测用户想调用什么功能。**

例如：

```text
@视频素材检索

帮我找一些适合日本市场的便携榨汁杯使用场景视频。
```

或者：

```text
@商品分析

分析这个商品在美国市场的竞争情况。
```

## 5.2 @Skill 的基本交互方式

建议采用类似常见 AI 助手的交互方式。

用户在输入框中输入 `@`，系统展示当前用户有权使用的 Skills。

```text
┌────────────────────────────────────────────┐
│                                            │
│  @视频素材检索                              │
│  根据自然语言需求检索和推荐视频素材          │
│                                            │
│  @素材详情查询                              │
│  查询素材的详细信息和分析数据                │
│                                            │
│  @素材加入项目                              │
│  将选中的素材加入指定项目                    │
│                                            │
│  @商品分析                                  │
│  分析商品市场、竞争和利润情况                │
│                                            │
│  @广告数据分析                              │
│  分析广告投放表现和关键指标                  │
│                                            │
└────────────────────────────────────────────┘
```

Skill 选择后，输入框中出现一个 Skill 标签。

```text
┌────────────────────────────────────────────┐
│                                            │
│  [@视频素材检索 ×]                           │
│                                            │
│  帮我找一些适合日本市场的便携榨汁杯视频      │
│                                            │
│                                      [发送] │
└────────────────────────────────────────────┘
```

用户发送后，Agent 直接进入指定 Skill 的执行流程。

## 5.3 @Skill 的执行规则

建议遵循以下优先级：

### 规则一：用户明确 @Skill

如果用户明确指定 Skill：

- 不再进行宽泛的能力路由。
- 直接加载指定 Skill。
- Agent 负责补充理解必要参数。
- 参数满足要求后执行 Skill。

例如：

```text
用户：
@视频素材检索
找一些日本市场的榨汁杯视频。
```

执行：

```text
解析 @Skill
    ↓
加载视频素材检索 Skill
    ↓
获取 Skill 参数定义
    ↓
结合用户输入组织参数
    ↓
Runtime 执行 Skill
    ↓
返回检索结果
```

### 规则二：用户没有 @Skill

如果用户直接输入自然语言：

```text
帮我找一些日本市场的榨汁杯视频。
```

Platform Agent 自行理解意图。

判断需要调用视频素材检索 Skill，然后执行。

### 规则三：用户 @Skill 但参数不完整

例如：

```text
@素材加入项目
```

如果缺少项目或素材信息，Agent 只询问缺少的必要参数。

不应直接执行，也不应重新进行全局意图识别。

### 规则四：用户 @Skill，但内容与 Skill 不匹配

例如：

```text
@视频素材检索
帮我计算这个商品的利润。
```

Agent 应明确提示：

当前指定的是视频素材检索能力，但你的需求是商品利润测算。

可以建议使用对应 Skill，而不是强行执行错误的能力。

### 规则五：用户明确指定 Skill 后，不允许无故切换

如果 Skill 执行过程中发现需要其他能力：

- 可以调用该 Skill 明确允许使用的依赖能力。
- 如果需要切换到另一项独立业务能力，应向用户说明。
- 不能悄悄改变用户指定的业务目标。

## 5.4 Skill 是否需要独立 Agent？

不需要。

例如：

```text
@视频素材检索
```

这不代表创建一个 Video Search Agent。

它只是调用一个已经注册的 Skill。

Skill 的执行过程可以由 Runtime 加载对应定义，再调用业务 Tool 或 Workflow。

**@Skill 是能力选择机制，不是 Agent 创建机制。**

---

# 6. Skill 定义与注册机制

## 6.1 Skill 基本结构

每个 Skill 建议由一个独立定义文件描述。

例如：

```yaml
id: video.material.search

name: 视频素材检索

description: >
  根据用户的自然语言需求，
  调用通用检索推荐系统检索和推荐视频素材。

category: video

version: 1.0.0

invocation:
  mention: true
  auto_route: true

input_schema:
  type: object
  properties:
    query:
      type: string
      description: 用户原始检索需求

    project_id:
      type: string
      description: 当前项目 ID

    context:
      type: object
      description: 用户明确提供的业务上下文

  required:
    - query

execution:
  type: tool
  handler: urr.recommend

output:
  type: candidate_set

permission:
  action: video.material.search

confirmation:
  required: false
```

说明：

Skill 定义主要是元数据和执行配置。

它不应该成为一个新的复杂脚本语言。

对于简单 Skill，定义文件就足够。

对于复杂 Skill，可以绑定专门的 Workflow。

## 6.2 Skill Registry

Skill Registry 负责管理所有 Skill。

建议核心数据字段：

| 字段 | 说明 |
|---|---|
| skill_id | Skill 唯一标识 |
| name | Skill 名称 |
| description | Skill 功能说明 |
| category | 所属业务分类 |
| version | 版本 |
| input_schema | 输入参数定义 |
| execution_type | tool / workflow |
| handler | 绑定的执行入口 |
| permission | 权限要求 |
| enabled | 是否启用 |
| mention_enabled | 是否允许 @ 调用 |
| auto_route_enabled | 是否允许 Agent 自动路由 |

Skill Registry 不负责执行 Skill，只负责发现、描述和管理 Skill。

## 6.3 Skill 如何让 Agent 理解？

Agent 不需要每次加载所有 Skill 的完整执行逻辑。

建议采用两级信息加载：

**第一层：Skill 摘要**

提供：

- Skill 名称。
- 描述。
- 适用场景。
- 触发关键词。
- 是否支持 @。

供 Agent 进行能力选择。

**第二层：Skill 完整定义**

当 Agent 决定使用某个 Skill 后，再加载：

- 详细说明。
- 参数定义。
- 执行入口。
- 约束条件。
- 输出定义。

这样可以减少上下文占用，也方便 Skill 数量增长。

对于用户明确 @ 的 Skill，直接加载完整定义。

---

# 7. Tool 体系设计

## 7.1 Tool 的定位

Tool 是 Agent 和 Skill 实际执行业务操作的接口。

例如：

```text
video.search_materials
video.get_material_detail
video.add_material_to_project
video.remove_material_from_project
video.get_project_context
video.update_material_feedback
```

Tool 不直接暴露底层数据库操作，而是调用业务服务。

## 7.2 Tool 的分类

| 类型 | 示例 | 特点 |
|---|---|---|
| Query Tool | 查询素材详情 | 只读 |
| Search Tool | 调用 URRE | 查询外部系统 |
| Command Tool | 添加素材到项目 | 修改业务状态 |
| Integration Tool | 调用第三方 API | 外部系统交互 |

## 7.3 Tool 标准接口

每个 Tool 需要有：

- 唯一 ID。
- 描述。
- 输入 Schema。
- 输出 Schema。
- 权限要求。
- 超时设置。
- 幂等策略。
- 错误码定义。

示例：

```json
{
  "tool_id": "video.add_material_to_project",
  "description": "将素材加入指定视频项目",
  "input_schema": {
    "type": "object",
    "properties": {
      "project_id": {
        "type": "string"
      },
      "material_ids": {
        "type": "array",
        "items": {
          "type": "string"
        }
      }
    },
    "required": [
      "project_id",
      "material_ids"
    ]
  }
}
```

## 7.4 Tool 的调用边界

Tool 调用必须经过 Runtime。

禁止 Agent 直接：

- 访问数据库。
- 修改业务数据。
- 调用未注册的外部 API。
- 绕过权限校验。
- 执行任意系统命令。

---

# 8. Workflow 体系设计

## 8.1 Workflow 的定位

Workflow 用于执行固定步骤、具有明确状态和业务约束的流程。

例如：

```text
批量添加素材到项目：

1. 检查项目是否存在。
2. 检查素材是否存在。
3. 检查用户权限。
4. 检查素材是否允许采用。
5. 执行素材关联。
6. 写入操作记录。
7. 返回执行结果。
```

这些步骤不需要 Agent 每次重新规划。

应该由 Workflow 按确定性规则执行。

## 8.2 Skill 与 Workflow 的关系

```text
用户请求
    │
    ▼
Platform Agent
    │
    ▼
@素材加入项目
    │
    ▼
Material Assignment Skill
    │
    ▼
Material Assignment Workflow
    │
    ├── 权限检查
    ├── 数据检查
    ├── 执行关联
    └── 返回结果
```

Skill 提供用户能够理解和调用的能力入口。

Workflow 负责可靠执行。

## 8.3 什么时候使用 Workflow？

符合以下任意条件时，可以考虑使用 Workflow：

- 多个步骤有固定顺序。
- 中间步骤需要持久化。
- 存在失败补偿或重试。
- 需要等待外部系统结果。
- 需要用户确认。
- 执行过程可能持续较长时间。

单一、简单、快速的业务操作，不必强行包装 Workflow。

---

# 9. Agent Runtime 设计

## 9.1 Runtime 的核心职责

Runtime 是整个系统的统一执行引擎。

它不负责理解业务目标，而是负责将 Agent 的执行决策安全、可靠地落地。

主要职责：

1. 接收执行请求。
2. 加载 Skill。
3. 校验参数。
4. 校验权限。
5. 调用 Tool 或 Workflow。
6. 处理执行结果。
7. 记录状态和日志。
8. 处理异常和重试。
9. 返回结构化结果。

## 9.2 执行模型

建议统一采用一个简单的执行模型：

```text
Execution
    │
    ├── execution_id
    ├── conversation_id
    ├── user_id
    ├── skill_id
    ├── status
    ├── input
    ├── output
    ├── error
    ├── started_at
    └── finished_at
```

每次 Skill 调用创建一个 Execution。

一个用户请求可以：

- 不创建 Execution：纯对话。
- 创建一个 Execution：调用一个 Skill。
- 创建多个 Execution：需要多个独立能力。
- 创建一个 Workflow Execution：需要固定流程。

不需要为每一次简单调用创建一套复杂的 Task / Ticket / Assignment 对象。

## 9.3 Execution 状态

建议统一使用：

```text
PENDING
   │
   ▼
RUNNING
   │
   ├── SUCCEEDED
   ├── FAILED
   ├── WAITING_CONFIRMATION
   └── CANCELLED
```

对于需要异步执行的 Workflow，可以增加：

- WAITING_EXTERNAL
- RETRYING

状态由 Runtime 和 Workflow Engine 管理，不由 Agent 自行维护。

## 9.4 异常处理

| 异常类型 | 处理方式 |
|---|---|
| 参数缺失 | Agent 询问用户 |
| 参数格式错误 | Schema 校验失败，返回错误 |
| 权限不足 | 拒绝执行并说明原因 |
| Tool 超时 | 按策略重试 |
| 外部系统不可用 | 返回可恢复错误 |
| 业务规则冲突 | 返回明确业务错误 |
| 用户取消 | 停止后续执行 |
| 执行结果不确定 | 查询执行状态，避免重复操作 |

重要：有副作用的 Tool 必须支持幂等键，不能因为超时就盲目重复执行。

---

# 10. Video Domain 业务架构

## 10.1 视频业务的正确定位

当前项目不负责完整端到端视频创作。

视频 Agent 主要负责：

- 理解用户意图。
- 判断用户需要什么视频业务能力。
- 调用通用检索推荐系统。
- 接收检索推荐结果。
- 处理用户后续的业务操作。

不负责：

- 故事板规划。
- 镜头规划。
- ClipRequirement 生成。
- 检索策略制定。
- 自主检索算法。
- 完整视频剪辑规划。
- 自动生成完整视频。

## 10.2 视频 Skill 体系

建议当前建设以下 Skill：

| Skill ID | Skill 名称 | 功能 |
|---|---|---|
| video.material.search | 视频素材检索 | 调用 URRE 检索素材 |
| video.material.recommend | 视频素材推荐 | 调用 URRE 推荐素材 |
| video.material.detail | 素材详情查询 | 查询素材详情 |
| video.material.similar | 相似素材查询 | 查询相似素材 |
| video.material.add | 素材加入项目 | 将选中素材加入项目 |
| video.material.remove | 移除项目素材 | 从项目中移除素材 |
| video.material.favorite | 收藏素材 | 收藏或取消收藏 |
| video.material.feedback | 素材反馈 | 记录用户反馈 |
| video.project.context | 项目上下文查询 | 获取当前项目相关信息 |

这些是业务能力入口，不是九个 Agent。

其中部分 Skill 可以共享同一个底层 Tool，也可以组合成一个 Workflow。

## 10.3 视频检索推荐链路

```text
用户
 │
 ▼
Platform Agent
 │
 ▼
识别视频检索 / 推荐意图
 │
 ▼
Video Material Search Skill
 │
 ▼
URRE Adapter
 │
 ▼
通用检索推荐系统
 │
 ├── Query 理解
 ├── 检索策略
 ├── Recall
 ├── Filtering
 ├── Ranking
 └── Recommendation
 │
 ▼
CandidateSet + Evidence
 │
 ▼
本系统接收结果
 │
 ▼
展示给用户
```

重要原则：

**本系统不重复实现 URRE 内部的检索推荐能力。**

用户原始检索输入应尽可能完整地传递给 URRE。

本系统可以附带：

- 当前用户。
- 当前项目。
- 市场等明确上下文。
- 已有业务约束。
- 用户主动提供的过滤条件。

但不能在本系统自行生成复杂 SearchPlan，再替代 URRE 的检索决策。

## 10.4 用户选择后的业务链路

```text
用户查看检索结果
       │
       ▼
选择素材
       │
       ▼
@素材加入项目
       │
       ▼
Platform Agent
       │
       ▼
Material Add Skill
       │
       ▼
Material Assignment Workflow
       │
       ├── 权限检查
       ├── 素材检查
       ├── 项目检查
       ├── 写入项目关系
       └── 记录操作事件
       │
       ▼
返回执行结果
```

检索和素材采用是两类独立能力。

不要将它们强制设计成一个复杂的端到端视频创作 Agent。

---

# 11. 对话与 Skill 调用机制

## 11.1 两种主要调用模式

### 模式 A：普通自然语言

用户：

```text
帮我找一些适合日本市场的榨汁杯视频。
```

流程：

```text
用户输入
   ↓
Platform Agent 意图识别
   ↓
匹配 video.material.search
   ↓
加载 Skill
   ↓
组织参数
   ↓
执行
   ↓
返回结果
```

### 模式 B：明确 @Skill

用户：

```text
@视频素材检索

帮我找一些适合日本市场的榨汁杯视频。
```

流程：

```text
用户输入
   ↓
解析 @Skill
   ↓
直接加载指定 Skill
   ↓
组织参数
   ↓
执行
   ↓
返回结果
```

两种模式最终进入同一个 Skill 执行入口。

不应该为 @ 调用和自动路由维护两套执行代码。

## 11.2 对话中的连续操作

例如：

```text
用户：
帮我找一些日本市场的榨汁杯视频。

Agent：
已经找到一批相关素材。

用户：
把第 3 个加入项目。

Agent：
已将素材加入当前项目。
```

第二轮请求需要结合对话上下文，解析“第 3 个”对应的素材 ID。

这里需要注意：

- Conversation 负责保存用户对话。
- Artifact 负责保存结构化检索结果。
- Agent 从上下文中解析引用关系。
- Skill 负责执行素材采用操作。

不要将整个 CandidateSet 只保存在模型的聊天上下文中。

## 11.3 Skill 调用结果

建议统一使用结构化输出：

```json
{
  "execution_id": "exec_123",
  "skill_id": "video.material.search",
  "status": "SUCCEEDED",
  "result": {
    "artifact_id": "artifact_456",
    "artifact_type": "CandidateSet",
    "summary": "找到 30 条相关素材",
    "data": {
      "total": 30
    }
  }
}
```

UI 根据 Skill 输出类型展示结果。

例如：

- CandidateSet：展示素材卡片。
- MaterialDetail：展示素材详情。
- OperationResult：展示操作结果。
- AnalysisReport：展示分析报告。

Agent 不应该把所有业务结果都转换成普通文本。

---

# 12. Artifact 设计

## 12.1 Artifact 的定位

Artifact 是业务执行过程中产生的结构化结果。

它不是 Agent，也不是 Skill。

例如：

- CandidateSet：检索推荐结果集合。
- MaterialDetail：素材详情。
- AnalysisReport：分析报告。
- OperationResult：操作结果。
- ProjectSnapshot：项目状态快照。

## 12.2 Artifact 的基本结构

```json
{
  "artifact_id": "artifact_001",
  "artifact_type": "CandidateSet",
  "version": 1,
  "created_by": "video.material.search",
  "execution_id": "exec_123",
  "created_at": "2026-11-17T10:00:00+08:00",
  "data": {}
}
```

Artifact 应支持：

- 持久化。
- 版本管理。
- 权限控制。
- 来源追踪。
- 生命周期管理。

对于大型素材数据，Artifact 只保存必要的元数据和对象存储引用，不需要把所有文件内容写入数据库。

## 12.3 Artifact 与 Conversation

两者职责不同：

| 对象 | 保存内容 |
|---|---|
| Conversation | 用户与 Agent 的交互记录 |
| Execution | Skill 或 Workflow 的执行记录 |
| Artifact | 结构化业务结果 |

这三个对象构成最基础的可追踪体系。

---

# 13. 数据模型

建议初期只建设必要的数据表。

| 数据表 | 用途 |
|---|---|
| agent | Agent 定义 |
| skill | Skill 定义 |
| tool | Tool 定义 |
| conversation | 对话 |
| message | 消息 |
| execution | Skill / Tool / Workflow 执行记录 |
| artifact | 结构化业务产物 |
| workflow_instance | Workflow 实例 |
| audit_log | 权限和操作审计 |

如果 Workflow Engine 已经提供可靠的实例存储，可以不重复建设 workflow_instance。

## 13.1 Agent 表

保存 Agent 的基本定义。

当前主要使用 Platform Agent。

## 13.2 Skill 表

保存：

- Skill ID。
- 名称。
- 描述。
- 分类。
- 版本。
- 输入定义。
- 执行入口。
- 权限。
- 是否允许 @。
- 是否允许自动路由。

## 13.3 Execution 表

建议字段：

```text
execution_id
conversation_id
user_id
skill_id
execution_type
status
input_json
output_json
artifact_ids
error_code
error_message
started_at
finished_at
created_at
```

## 13.4 Artifact 表

建议字段：

```text
artifact_id
artifact_type
version
execution_id
created_by
storage_uri
metadata_json
owner_id
created_at
expires_at
```

---

# 14. 权限与安全

## 14.1 权限原则

Agent 可以决定调用什么能力，但不能自行决定是否拥有执行权限。

所有执行请求必须经过 Runtime 的服务端权限校验。

## 14.2 Skill 权限

建议每个 Skill 配置独立权限。

例如：

| Skill | 权限 |
|---|---|
| video.material.search | video:material:read |
| video.material.detail | video:material:read |
| video.material.add | video:project:write |
| video.material.remove | video:project:write |
| video.material.favorite | video:material:favorite |

## 14.3 操作确认

建议按副作用划分：

| 操作类型 | 默认策略 |
|---|---|
| 查询数据 | 不需要确认 |
| 检索推荐 | 不需要确认 |
| 收藏素材 | 根据业务规则 |
| 加入项目 | 根据业务规则 |
| 删除或移除 | 重要操作可要求确认 |
| 修改重要项目配置 | 要求确认 |
| 不可逆外部操作 | 必须确认或受严格授权约束 |

确认策略应由服务端配置，而不是只依赖 Agent 提示词。

---

# 15. 前端交互设计

## 15.1 Agent Chat

统一对话页面需要支持：

- 普通文本输入。
- @Skill 搜索和选择。
- Skill 标签展示。
- 文件上传。
- 上下文引用。
- 执行状态展示。
- 结构化结果卡片。
- 用户确认操作。

## 15.2 Skill 选择器

Skill 选择器建议支持：

- 按名称搜索。
- 按业务领域分类。
- 展示 Skill 简介。
- 展示适用场景。
- 展示必要参数提示。
- 展示用户是否有权限使用。

Skill 数量较多时，不能把所有 Skill 一次性铺开。

应该支持搜索、分类和最近使用。

## 15.3 执行状态展示

建议只展示必要状态：

```text
正在理解需求
    ↓
正在执行：视频素材检索
    ↓
检索完成
    ↓
展示结果
```

对于复杂 Workflow，可以展示：

- 当前步骤。
- 已完成步骤。
- 当前等待事项。
- 失败原因。
- 用户需要进行的操作。

不要把底层 Runtime 的全部日志直接展示给用户。

## 15.4 Skill 管理界面

初期只需要一个简单的 Skill 管理页面。

展示：

- Skill 名称。
- 描述。
- 分类。
- 版本。
- 启用状态。
- 是否支持 @。
- 是否支持自动路由。
- 权限。
- 最近调用情况。

不需要为每个 Skill 建设一个独立管理后台。

---

# 16. 与 Super Agent 架构的关系

本方案吸收 Super Agent 中值得借鉴的思想，但不照搬它的完整架构。

| Super Agent 概念 | 本方案对应设计 |
|---|---|
| Main Session | Platform Agent |
| Ticket | Execution / Workflow Instance |
| Assignment | Runtime 执行绑定 |
| Executor | Agent Runtime Execution |
| Mandate | 用户身份 + Permission + Execution Scope |
| Report | Execution Result |
| Attention | 用户确认与待处理状态 |
| Subscription | 后续可扩展的事件订阅 |
| Thread | Conversation / Context |
| Event | Event / Audit |

需要注意：

本方案不再把这些概念全部设计成独立领域对象。

只保留真正需要的能力。

例如：

- 不需要一开始就实现完整 Ticket 系统。
- 不需要为每个 Execution 创建独立 Assignment 对象。
- 不需要在普通用户请求前增加独立 Eval Agent。
- 不需要让 Skill 之间通过复杂订阅关系协作。

当真实业务需要时再增加相应机制。

---

# 17. 技术实现建议

## 17.1 核心模块

建议初期只拆分为五个核心模块：

```text
agent-platform
    │
    ├── agent-core
    │     ├── Agent Orchestrator
    │     ├── Intent Router
    │     └── Context Manager
    │
    ├── skill-center
    │     ├── Skill Registry
    │     ├── Skill Loader
    │     └── Skill Resolver
    │
    ├── agent-runtime
    │     ├── Execution Manager
    │     ├── Tool Executor
    │     ├── Workflow Executor
    │     └── Policy Guard
    │
    ├── business-adapters
    │     ├── Video Adapter
    │     ├── URRE Adapter
    │     └── Other Domain Adapters
    │
    └── artifact-service
          ├── Artifact Registry
          └── Artifact Storage
```

这些是逻辑模块，不要求第一阶段就拆成五个微服务。

建议先采用模块化单体或少量服务部署，减少分布式调用和运维成本。

## 17.2 Agent Core

负责：

- Prompt 管理。
- LLM 调用。
- 意图理解。
- Skill 路由。
- 上下文构建。
- 工具选择。
- 结果组织。

## 17.3 Skill Center

负责：

- Skill 注册。
- Skill 加载。
- Skill 版本。
- Skill 搜索。
- @Skill 解析。
- Skill 权限元数据。

## 17.4 Agent Runtime

负责：

- 执行生命周期。
- Tool 调用。
- Workflow 启动。
- 参数校验。
- 权限检查。
- 异常处理。
- 执行记录。

## 17.5 Business Adapters

负责对接外部业务系统。

例如：

```text
Video Skill
    │
    ▼
Video Adapter
    │
    ├── URRE API
    ├── Material API
    └── Project API
```

Adapter 不应该把外部系统的内部数据结构直接暴露给 Agent。

应转换成统一业务契约。

---

# 18. 实施路线

建议分三个阶段实施。

## Phase 1：最小可用 Agent Platform

目标：跑通统一 Agent 和 Skill 调用。

实施内容：

1. Platform Agent。
2. Conversation / Message。
3. Skill Registry。
4. @Skill 选择器。
5. Skill 自动路由。
6. Agent Runtime。
7. Tool Registry。
8. Execution 状态管理。
9. 基础权限校验。
10. 执行结果展示。

验收标准：

- 用户可以直接与 Agent 对话。
- 用户可以 @ 指定 Skill。
- Agent 可以自动选择 Skill。
- Skill 可以调用 Tool。
- Runtime 能够记录执行过程。
- 用户可以看到执行结果。

## Phase 2：业务能力接入

目标：完成 Video Domain 的实际业务能力。

实施内容：

1. URRE Adapter。
2. 视频检索 Skill。
3. 视频推荐 Skill。
4. 素材详情 Skill。
5. 素材加入项目 Skill。
6. 素材移除 Skill。
7. 素材收藏 Skill。
8. CandidateSet Artifact。
9. 用户行为反馈。
10. 必要的 Workflow。

验收标准：

- Agent 可以调用 URRE。
- URRE 返回结果能够正确展示。
- 用户能够选择素材。
- 用户能够通过自然语言或 @Skill 执行业务操作。
- 业务操作具有权限校验和审计记录。

## Phase 3：能力扩展

目标：支持更多业务领域和复杂流程。

实施内容：

1. Skill 分类和推荐。
2. Skill 版本管理。
3. Skill 可见范围。
4. 复杂 Workflow。
5. 异步执行。
6. 用户确认和恢复。
7. Execution Analytics。
8. 可选 Domain Agent。
9. 必要时引入并行 Sub Agent。

验收标准：

- 新增一个 Skill 不需要修改 Agent 核心代码。
- 新增一个业务领域不需要重建平台架构。
- 复杂 Workflow 能够持久化和恢复。
- Agent 能够在权限范围内选择和调用能力。
- 不同业务能力能够独立开发和迭代。

---

# 19. 架构设计中的关键决策

| 问题 | 最终决策 |
|---|---|
| 是否需要多个平台级 Agent？ | 当前只需要一个统一 Platform Agent |
| 是否需要固定 Domain Agent 层级？ | 不需要，按实际复杂度选择 |
| 是否每个 Skill 都需要 Agent？ | 不需要 |
| @Skill 是否直接创建 Agent？ | 不会，直接调用已注册 Skill |
| Skill 和 Tool 是否相同？ | 不同，Skill 是业务能力入口，Tool 是执行接口 |
| 是否需要 Workflow？ | 需要，但只用于确定性多步骤业务流程 |
| 是否需要子 Agent？ | 当前不需要，复杂并行推理时再引入 |
| Agent 是否直接访问数据库？ | 不允许 |
| Agent 是否直接执行外部业务操作？ | 必须通过 Runtime 和受控 Tool |
| 检索推荐是否由 Video Agent 自己完成？ | 不需要，交给 URRE |
| 是否需要复杂 Ticket / Mandate / Assignment？ | 当前不需要独立完整体系 |
| 是否需要 Artifact？ | 需要，保存结构化业务结果 |
| 是否需要 Event？ | 需要基础事件记录，复杂订阅机制后续再扩展 |

---

# 20. 最终架构总结

整个系统最终只需要理解五个核心概念：

## 1. Agent：负责理解和决策

理解用户想做什么，判断应该使用什么能力。

## 2. Skill：负责定义专业能力

将专业业务能力封装成 Agent 可以发现、理解和调用的标准单元。

用户可以通过 @ 明确指定 Skill，也可以由 Agent 自动选择。

## 3. Tool：负责具体操作

通过标准接口调用业务服务或外部系统。

## 4. Workflow：负责固定流程

将有明确顺序、状态和约束的业务过程可靠地执行。

## 5. Runtime：负责统一执行

管理执行过程、权限、状态、异常、日志和结果。

它们之间的关系：

```text
                User
                 │
                 ▼
              Agent
                 │
          理解意图 / 选择能力
                 │
                 ▼
               Skill
                 │
          组织业务执行过程
                 │
          ┌──────┴──────┐
          ▼             ▼
         Tool        Workflow
          │             │
          └──────┬──────┘
                 ▼
              Runtime
                 │
                 ▼
         Business Services
                 │
                 ▼
               Result
                 │
                 ▼
               Agent
                 │
                 ▼
                User
```

**最终设计理念：**

不要把所有业务能力都变成 Agent。

不要把所有操作都变成 Workflow。

不要把所有 Skill 都设计成复杂的程序。

不要为了多 Agent 而多 Agent。

一个优秀的 Agent Platform，应该让用户只需要表达目标，让 Agent 找到正确的能力，让 Skill 组织执行，让 Runtime 保证执行可靠。

**架构越简单，职责越清晰，能力越容易扩展，系统越容易真正落地。**