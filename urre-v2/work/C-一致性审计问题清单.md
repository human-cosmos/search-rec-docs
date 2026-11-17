# C 组：跨文档一致性审计问题清单（URRE）

- **审计对象**：`~/workspace/search-rec-docs/` 下的 01、02、03、04 及 `urre/URRE数据与存储模型设计.md`（下称 DM）
- **审计日期**：2026-11-16
- **审计范围**：01 §5/§9/§13；02 全文（498 行，主审对象）；DM §2.4、§4、§5、§8、§20（及为核查所及的 §6、§12、§17、§19、§21）；03 检索边界（§1.4、§3、§5.1–§5.3、§12.4）；04 §15 与主文衔接说明
- **不改动源文档、不写最终版文档、不做图片**（按任务要求）
- **统计**：P0 8 条，P1 12 条，P2 9 条，共 29 条

## 严重度定义

- **P0 必须修**：定义冲突、互相矛盾、会误导实施——按任一文档开工都会做出与另一文档不符的东西。
- **P1 应修**：缺失定义、未定选型、无验收口径——实施时无据可依，只能靠猜。
- **P2 建议**：表述、命名、引用失效——不直接误导实施，但损害可读性与可验证性。

## 核查基线（引用存在性，2026-11-16 实测）

当前 `search-rec-docs/` 下只有 24 个文件：根目录 01–04 四篇 md，`urre/` 3 篇 md，`images/` 17 张 png；**没有 `README.md`，没有 `implementation/` 目录**。以下引用在当前目录下均不存在：`README.md`、`implementation/00_交付范围与VideoClip模型.md`、`implementation/01_API与数据契约.md`、`implementation/02_技术选型与服务部署.md`、`implementation/03_实施路线图与验收基线.md`、`implementation/05_VideoDomainAgent_工程契约与研发Backlog.md`、`implementation/07_跨域编排与领域子工作流设计.md`、`05_URRE数据与存储模型设计.md`（实际文件为 `urre/URRE数据与存储模型设计.md`，路径与文件名均不同）、`00_架构设计总纲.md`、`01_URRE架构设计.md`、`02_AgentRuntime架构设计.md`、`03_VideoDomain架构设计.md`、`runtime-sdk/java/overview.md`。本清单中凡称“引用失效”，均指在此基线下的实测结果，而非推测。

---

## P0：必须修（8 条）

### P0-1　02 “本次不交付真实 URRE”与 §10 大量未来设计混排，§3 架构图把未交付组件画成现行架构

- **问题**：02 开篇与 §5.5、§10、§12 反复声明“本次不交付真实 URRE / 不实现 Ingest、Processing、Embedding、Indexing、ES、Qdrant、Kafka”，但 §3 的 mermaid 架构图以“当前架构依据”为题，把 Search/Recommendation/Similarity/Explore 四服务、Embedding / Two-Tower / DNN Ranker / Reranker、关键词/向量/视觉/属性/关系索引、Ingest、Feedback & Attribution 全部画成并列的现行组件，无任何“未来/未交付”标记；§10（约 140 行，占全文近三成）以陈述语气详细规定未来加工与索引的责任边界、状态机、幂等键与发布流程，与可交付内容在同一文档、同一语气下混排。读者无法仅凭本文判断哪一段是“本次可实施”、哪一段是“未来参考”。
- **证据出处**：02 开篇交付约束；02 §3（“下图是当前架构依据”+ mermaid 图）；02 §10 全节（§10.1–§10.5）；02 §12.1/§12.2 对比。
- **严重度**：P0。
- **建议修法**：02 全文拆分为两部分并用显式标记隔离——A 部分“本次交付：Mock Retrieval Adapter + Port + Schema”（§1–§9 中属于 Mock 的内容），B 部分“未来真实 URRE 2.0 参考设计”（现 §10 及 §5.5），B 部分每节加统一水印式声明；§3 架构图拆成两张（本次 Mock 架构图 / 未来目标架构图），或在同一图中用虚线框标注未交付组件；§12.1 门槛改为可直接执行的检查表，不再外包给不存在的 implementation 文档。

### P0-2　Qdrant 选型自相矛盾：02 定为“默认选择”，DM 称“最终选型待定”

- **问题**：02 §5.5 以加粗标题宣布“**默认选择：Qdrant**”，并给出选型理由；DM §21“待基准验证的技术决策”第 1 条却是“Qdrant 与 Milvus / OpenSearch Vector 的最终选型”——同一选型在一处是已定默认方案，在另一处是待验证的开放问题。更甚者，DM §12.4 已给出具体配置（向量维度 1024、Cosine、HNSW m=32、ef_construct=256、segment 4），紧接着又说“最终参数必须通过数据规模、召回率和延迟基准确认”，而 DM §2.2 明确“具体 Embedding 模型、向量维度和排序模型的最终选型”不在本文覆盖范围。实施者无法判断 1024 维是决策、示例还是占位符。
- **证据出处**：02 §5.5；DM §21 第 1 条；DM §12.4；DM §2.2。
- **严重度**：P0。
- **建议修法**：二选一并全文档统一：要么冻结 Qdrant 为默认选型并删除 DM §21 第 1 条、把 §12.4 参数标注为“已冻结初值 + 变更条件”；要么把 02 §5.5 改写为“候选方案 Qdrant（待基准验证）”，删除“默认选择”的定性表述，并把 §12.4 的 1024/m=32/ef_construct=256 明确标注为“示例值，非决策”，同时补上基准测试的准入条件（数据量、召回率、延迟阈值）。

### P0-3　CandidateSet 存在两套互不相同的 Schema，且无映射表

- **问题**：02 §7 给出一套“概念契约”JSON（字段：`request_id`、`domain`、`capability`、`strategy_version`、`items[].entity_id/entity_type/score/rank/recall_channels/matched_requirements/evidence{summary,time_range,evidence_refs}/availability/feature_version`、`trace{query_version,model_versions,latency_ms}`），无 `candidate_set_id`、`candidate_id`、Manifest、分页、警告字段；DM §5.12、§8.5、§9.7 给出另一套（`candidate_set_id`、`candidate_id`、`score_breakdown`、`candidate_origins`、`source_candidate_set_ids`、`versions{feature_version,model_versions,index_profile_version}`、`trace{query_version,latency_ms,degraded_channels,model_versions,index_manifest_id}`、`page`、`warnings`，另有 `schema_version: "1.1"`），字段名、结构、版本均不同，两处均未说明与对方的关系。01 §9 与 03 §5.3 又要求 Mock 与真实 Adapter“共用 CandidateSet Schema”，而 DM §8.5 却说“Mock 可以只实现 1.0 的必需字段，真实 URRE 在 1.x 内增加可选字段”——“共用同一 Schema”与“1.0/1.1 两个版本”直接冲突，Mock 与真实的兼容策略没有字段级对照表。
- **证据出处**：02 §7；DM §5.12、§8.5、§9.7；01 §9；03 §5.3 阶段六；DM §20.2（补齐字段清单与 §8.5 不完全一致，见 P0-3 附注）。
- **严重度**：P0。
- **建议修法**：冻结一份 CandidateSet Schema v1.x 唯一权威（建议以 DM §8.5/§9.7 为底本，因其有 DDL），02 §7 改为引用该权威并删除自立的 JSON 示例，或明确标注为“§8.5 的简化示意，非契约”；补一张字段对照表（02 §7 字段 → 权威字段，含改名/删除/新增）；明确 1.0（Mock）与 1.1（真实）的字段差集与兼容规则（哪些字段 Mock 可空、哪些真实必填）；DM §20.2 的补齐清单（`candidate_origins` 等 6 项）与 §8.5 逐字段对齐，消除两处清单差异。

### P0-4　Explore 的交付状态在 01 / 02 / 03 / DM 四处说法不一，且没有 API 端点

- **问题**：02 §1/§4.4 把 Explore 列为与 Search、Recommendation、Similarity 并列的“一等业务能力”，§3 架构图画出 Explore Service；但 02 §12.1 第 1 条又说“Explore 不进入本次交付门槛”。01 §5 请求路由表（6 行）与 §9 Mock 清单（Fake Search / Recommendation / Similar / Evidence）均无 Explore；03 的 8 个冻结 Tool 与 R0–R4 路由中无任何 Explore 入口，全文零次出现 Explore；DM §8.4 称“Explore 不属于当前交付，但数据模型预留”，给出了 ExploreRequest，却在 DM §8 开头的端点表（search / recommend / similar / feedback / evidence）中没有 `/retrieval/explore`。同一能力在四份文档中分别是“一等能力 / 不进门槛 / 不存在 / 预留无端点”。
- **证据出处**：02 §1、§4.4、§12.1；01 §5、§9；03 全文（grep Explore 零命中，8 个 Tool 见 §5.2）；DM §8、§8.4。
- **严重度**：P0。
- **建议修法**：冻结 Explore 的单一状态并全文档统一，建议表述为“Explore 为 URRE 远期能力：概念与请求模型已预留（DM §8.4），本次不交付、无 Tool、无路由、无端点、无验收”；02 §4.4 与 §3 图改为“远期能力（本次不交付）”标注；DM §8 端点表要么补上 `/retrieval/explore` 并标注“远期”，要么在 §8.4 明确“本次无端点”。

### P0-5　Item / Batch / Manifest 状态机在 02 与 DM 中分歧

- **问题**：02 §10.3 定义 Item 状态机为 `Accepted → Ingesting → Processing → Embedding → Indexing → Validating → Active`，另有 `Failed / Cancelled`，无重试边、无死信态；DM §6.1 同一状态机多了 `Failed → Accepted（retry）`、`Failed → DeadLettered（exhausted）`、`DeadLettered → Accepted（manual_retry）` 三条边。Manifest：02 §10.4 只列 5 态（Draft / Validated / Active / Failed / RolledBack），DM §6.2 为 8 态（多了 Building、Superseded，且 Active → Superseded / RolledBack）。Batch 状态机只在 02 出现（`Accepted → Running → Completed`，允许 PartiallyCompleted），DM 全文无 Batch 状态机。按任一文档实现状态流转都会与另一文档的验收（DM §17.2/§17.3）对不上。
- **证据出处**：02 §10.3、§10.4；DM §6.1、§6.2、§17.2、§17.3。
- **严重度**：P0。
- **建议修法**：以 DM §6 为唯一状态机权威（因其有完整转移边与规则），02 §10.3/§10.4 改为引用 DM §6 并删除自立的状态枚举；补上 Batch 状态机（或明确声明 Batch 不持久化、仅为 Job 聚合视图）；DM §17 验收逐条对应到状态机转移边。

### P0-6　幂等键公式在 02 与 DM 中定义不同，`content_version` 的分配权威只在一处出现

- **问题**：02 §10.3 定义 Processing Key = `tenant_id + entity_type + entity_id + content_version + metadata_version + processing_profile_version`；DM §4.4 定义 `processing_key = snapshot_hash + processing_profile_id + processing_profile_version`。两者语义有重叠（`snapshot_hash` 按 DM §4.5 覆盖版本字段），但作为键的构成与字符串形式不同，按任一公式实现都会与另一实现产生不同的键，跨文档的幂等保证无法成立。同类问题：Embedding Key 在 02 中为 `processing_artifact_hash + embedding_space + embedding_model_version`，DM §4.4 多了 `embedding_model_id`。此外，02 §10.3 称 `content_version`“由 `data-control-plane` 在 `source-uploads/finalize` 校验通过并生成不可变对象后分配”——`data-control-plane` 与 `source-uploads/finalize` 这两个术语在 01、03、DM 中均无定义、无对应章节，DM §4.3 只说“原始二进制发生合法替换时递增”，未说明由谁分配。
- **证据出处**：02 §10.3；DM §4.3、§4.4、§4.5。
- **严重度**：P0。
- **建议修法**：冻结一份幂等键规范（建议以 DM §4.4 为准，因其与 §4.5 的 hash 规则成套），02 §10.3 改为引用并删除自立公式；明确 `content_version` 的分配方与分配时点（控制面哪个接口、在哪一步），并给 `data-control-plane`、`source-uploads/finalize` 下定义或改用 DM 已定义的术语（Source / Snapshot / Ingestion Job）。

### P0-7　Qdrant Collection 命名规则在 02 与 DM 中不同

- **问题**：02 §5.5 规定 Collection 按“领域 + 向量类型 + Embedding 模型主版本”划分，示例为 `video_text_v1`、`video_visual_v1`；DM §12.1 规定命名为 `urre_{pool_id}_{domain}_{vector_space}_{model_major}`，示例为 `urre_default_video_text_v1`、`urre_default_video_visual_v1`。两者前缀与分段均不同（有无 `urre_{pool_id}_` 前缀），且 02 未提 pool 概念，DM 未提 02 的命名。同一物理资源会出现两个名字。
- **证据出处**：02 §5.5；DM §12.1。
- **严重度**：P0。
- **建议修法**：以 DM §12.1 为准（因其与 Manifest / Pool 模型成套），02 §5.5 的示例改为 `urre_default_video_text_v1` 形式，并补一句“Collection 命名以 DM §12.1 为准”；或反向冻结其一，全文档统一。

### P0-8　反馈事件命名在 02 与 DM 之间无映射，归因无法落地

- **问题**：02 §8.1 定义 9 类反馈事件（Impression / Click / Preview / Save / Download / Adopt / Use / Replace / Reject / Convert），以英文名词作事件名；DM §8.6 的 FeedbackRequest 示例却用点分式 `event_type: "recommendation.clicked"`，DM §5.12 与 §9.7 的 `urre_feedback_event` 表只规定 `event_type varchar(64)`，未给出枚举值。两处事件命名体系之间无对照表，02 的 9 类事件如何映射为 DM 的点分式事件值、是否一一对应、是否允许 02 之外的事件值，均未定义。02 §12.1 第 3 条要求“反馈事件可关联请求、候选集和后续业务结果”，在事件名本身未冻结的情况下无法验收。
- **证据出处**：02 §8.1、§8.2、§12.1；DM §5.12、§8.6、§9.7。
- **严重度**：P0。
- **建议修法**：冻结一份反馈事件枚举表（建议点分式，形如 `search.impression` / `recommendation.clicked` / `clip.adopted`），逐条对应 02 §8.1 的 9 类事件，写明每个事件的必填归因字段（`candidate_set_id`、`candidate_id`、`exposure_position`、`strategy_id/version`、`index_manifest_id`）；DM §9.7 的 `event_type` 加 CHECK 约束或引用该枚举；02 §8.1 改为引用该表。

---

## P1：应修（12 条）

### P1-1　SearchPlan 只在 03 存在，02 / DM 均无定义，且与 DM 的 SearchRequest 预算冲突

- **问题**：03 §5.3 阶段五定义了 Agent 侧的 SearchPlan（含语义查询、子查询及权重、硬过滤、软偏好、召回通道、候选预算、最大延迟），但 02 与 DM 全文零次出现 SearchPlan——URRE 侧不知道这个输入对象是什么、由谁校验、权重如何生效。数值上直接冲突：03 SearchPlan 示例 `candidate_budget: 100`，DM §8.1 SearchRequest 示例 `recall.candidate_budget: 200`；而 01 §5 与 03 §5.3 阶段六同时要求“Direct 与 Agent 路径必须返回相同 CandidateSet”——两条路径用不同的候选预算，不可能保证返回相同候选集。子查询权重（03 示例 0.5 / 0.3 / 0.2）无归一化规则、无合并公式，02 §5.1 的“召回策略选择”由谁负责（URRE 还是 Agent 的 SearchPlan）也未定。
- **证据出处**：03 §5.3 阶段五、阶段六；DM §8.1；02 §5.1；01 §5。
- **严重度**：P1。
- **建议修法**：在 02 或 DM 中补 SearchPlan 的定义（或明确声明“SearchPlan 是 Agent 内部规划对象，进入 URRE 前必须翻译为 SearchRequest，翻译规则见××”）；冻结 `candidate_budget` 的默认值与 Direct/Agent 两路径的取值规则，使“相同 CandidateSet”的断言可验证；补子查询权重的归一化与合并规则，或删除权重字段改用有序子查询。

### P1-2　召回通道与相似目标的枚举未冻结，且两处不一致

- **问题**：02 §5.1 列出 9 个召回通道（keyword / semantic / visual / attribute / collaborative / context / relation / trend / exploration），DM §8.1 示例的 `recall.channels` 却出现第 10 个值 `metadata`（02 中无此通道名，与 attribute 通道的关系不明）。相似目标：02 §4.3 列 5 类（语义 / 视觉 / 属性 / 行为 / 关系），DM §8.3 示例只用 `["semantic", "visual"]`，03 §5.2 的 `find_similar_materials` 接受 `similarity_targets` 但未给枚举。没有任何一处是“通道/目标枚举的唯一权威”。
- **证据出处**：02 §4.3、§5.1；DM §8.1、§8.3；03 §5.2。
- **严重度**：P1。
- **建议修法**：冻结两张枚举表（召回通道、相似目标）并指定唯一权威位置（建议 DM §8）；`metadata` 通道要么并入 attribute 并注明别名，要么作为独立通道补定义；DM §8.1/§8.3 的示例值改为枚举内的值。

### P1-3　RRF 融合与分数校准只有原则，没有方法

- **问题**：02 §5.5 与 DM §12.5、§14、§18 阶段 C 均称“RRF 融合”或“RRF 或校准后融合”，但全文档无 RRF 的 k 参数、无归一化公式、无“校准后”指何种校准方法；02 §5.4 只禁令式地要求“将现有分数直接相加前必须完成校准”“Two-Tower 分数不能未经校准直接作为最终分数”，却不给校准方法。DM §8.5 示例中的 `score_normalization_version: "rrf-v1"` 引用了一个从未定义的版本。融合是 URRE 的核心计算，当前状态不可实施。
- **证据出处**：02 §5.4、§5.5；DM §12.5、§14、§18、§8.5。
- **严重度**：P1。
- **建议修法**：冻结融合方案二选一（RRF with k=××，或分数校准 + 加权），给出公式、参数与版本命名规则（`rrf-v1` 的定义）；校准方法至少定性为“分通道单调映射 + 离线标定”，并列入 DM §21 待验证清单时给出验证方法。

### P1-4　指标只有名字，没有阈值；延迟预算在各处取不同值

- **问题**：02 §9 列出 Recall@K、NDCG@K、MRR、P95/P99 等十余项指标，但 K 未取值、P95/P99 无目标值；DM §17 验收基线 20 余条全部是定性断言（“可追溯”“一致”“不新增事件”），无一条含数字阈值。延迟预算：DM §8.1 Search `deadline_ms: 8000`、§8.2 Recommendation 8000、§8.3 Similar 5000、03 SearchPlan `max_latency_ms: 8000`——这些数字只出现在示例 JSON 中，正文无一处声明其为 SLO、默认值还是示例占位。03 §12.4 明确“本节不虚构统一数值”，但所列的“冻结位置”（容量配置与 SLO、预算与超时配置等）指向的文档均不存在（见 P2-1），数值责任空悬。
- **证据出处**：02 §9、§12；DM §8.1–§8.3、§17；03 §12.4。
- **严重度**：P1。
- **建议修法**：补一张 SLO 表（分能力：Search / Recommendation / Similar 的 P95 延迟目标、Recall@K 的 K 与目标值、零结果率上限、索引延迟上限），并注明每项的生效阶段（Mock 阶段 / 真实 URRE 阶段）；示例 JSON 中的 deadline 值要么标注“示例值”，要么与 SLO 表一致；03 §12.4 的“冻结位置”改为真实存在的位置或标注待建文档。

### P1-5　规模与成本论证缺失；“现有 Java 服务 / Kafka 链路”无依据

- **问题**：02 §1 称“大规模对象的低延迟候选发现”，§5.5 称 Qdrant 的风险是“超大规模、高写入和高并发下的成本与延迟”——全文档无任何数量级（对象数、QPS、向量总数、存储量、成本估算），“大规模”“超大规模”无法证伪。DM §12.4 的向量维度 1024、HNSW 参数、segment 数均无模型依据（未点名任何 Embedding 模型，DM §2.2 亦称模型选型不在覆盖范围）。02 §5.5 称 Qdrant“与现有 Java 服务、Kafka 索引链路和 Elasticsearch 全文检索组合”——“现有”二字暗示这些链路已存在，但 01/03/DM 中均无 Java 服务与 Kafka 链路的现状描述，该前提未经证实。
- **证据出处**：02 §1、§5.5；DM §12.4、§2.2、§21。
- **严重度**：P1。
- **建议修法**：补一节“规模假设”（对象量级、QPS 峰值、向量维度来源模型、存储估算），并注明假设失效时选型复审的触发条件；删除或修正“现有 Java 服务、Kafka 索引链路”的表述，改为“规划中的 Java 服务与 Kafka 链路”并给出出处；DM §21 的基准验证清单补上每项的通过标准。

### P1-6　Agent 的候选评估与 URRE 重排的边界模糊，存在二次排序

- **问题**：03 §5.1 明确禁止 Agent“修改 Retrieval Port 返回的候选分数”“遍历全部候选素材”，但 03 §5.3 阶段七要求 Agent 对 shortlist 内候选逐条综合判断（是否符合需求、叙事角色、画面、商品、时长、证据、质量、重复、替代），阶段八据此选出首选 1 条与替代最多 3 条——这实质上是在 URRE 排序/重排（02 §5.3）之上又做了一次 Agent 侧排序，且 03 未规定 Agent 的评估结论能否推翻 URRE 的 rank 顺序、首选是否必须为 URRE rank 1。04 §15.1/§2.6 保留的原则“不要把每个候选素材交给 LLM 打分”（04 行 605、2116）与 03 阶段七“逐候选综合判断”之间的关系也未裁决：阶段七的分项评估是否算“打分”？此外，03 SearchPlan 的硬过滤（示例 `aspect_ratio: 9:16`）与 DM §8.1“filters 只允许 Domain Schema 注册的字段和操作符”之间无校验规则，Agent 能否写入未注册的硬过滤字段未定。
- **证据出处**：03 §5.1、§5.3 阶段七、阶段八；02 §5.2、§5.3；DM §8.1；04 §2.6、§15.1。
- **严重度**：P1。
- **建议修法**：冻结一条边界规则，例如“Agent 评估只产生 `selection_reason` 与 `needs_user_review / low_quality` 标记，不得改变候选相对顺序；首选默认为 URRE rank 1，偏离时必须在 Assignment 中写明理由并引用证据”；明确阶段七的分项评估与“不逐候选打分”原则的关系（评估≠打分，或限定 shortlist ≤10 时例外）；规定 SearchPlan 的硬过滤字段必须在 Domain Schema 注册，否则 Retrieval Port 拒绝。

### P1-7　文档编号体系错位：04 与 DM 沿用旧 00–03 编号，实际文件为 01–04

- **问题**：04 文首称“与 `00` 架构设计总纲、`01` URRE、`02` Agent Runtime、`03` Video Domain Pack”冲突时以后者为准——按实际文件名，总纲是 01、URRE 是 02、Agent 是 03、开源解析是 04，04 的编号整体偏移一位。DM §2.4 同样用旧编号，称“`01` 已定义能力、召回流水线和发布原则”“`01` 已选择 ES/Qdrant 分工”——实际指 02_URRE架构设计.md。04 §15 引用的 `02 Agent Runtime`（02_AgentRuntime架构设计.md）、`03_VideoDomain架构设计.md`、`implementation/02` 在当前目录均不存在。没有任何一处定义新旧编号的映射关系，“以后者为准”在当前目录下无锚点。
- **证据出处**：04 行 3、行 703、§15 全节；DM §2.4；01 行 3（01 自称总纲，但 04 称其为 00）。
- **严重度**：P1。
- **建议修法**：全文档统一使用实际文件名编号（01 总纲、02 URRE、03 Agent、04 开源解析），并附一张“旧编号 → 现文件名”对照表；04 §15 与 DM §2.4 中的旧编号引用逐条改写为现文件名；删除对不存在的 `02_AgentRuntime架构设计.md` 的引用，改为 03 中的对应章节（Runtime 内容在 03 §4）。

### P1-8　02 的关键决策没有 ADR 编号

- **问题**：01 §13 已建立 ADR 命名空间规则（`ADR-*` 属总纲，`IMPL-ADR-*`、`VDA-ADR-*` 各属其文档，引用须写明所属空间），DM §19 自建 `URRE-DM-ADR-01–12`，03 自建 `ADR-ART/SDK/MEDIA/API-001`。但 02 作为主审的 URRE 架构文档，全文没有任何 ADR 条目：Qdrant 默认选择（§5.5）、ES/Qdrant 分工、RRF 融合、Active Manifest 唯一发布点、Mock-first 边界等关键决策均无决策编号、无备选方案记录、无决策日期。按 01 §13 的规则，02 的决策无法被引用、无法被复审。
- **证据出处**：02 全文（无 ADR）；01 §13；DM §19；03 §1.4。
- **严重度**：P1。
- **建议修法**：为 02 补 ADR 表（建议编号空间 `URRE-ADR-*`，与 DM 的 `URRE-DM-ADR-*` 明确区分层级：前者是架构选型，后者是数据模型决策），至少覆盖 Qdrant 选型、ES/Qdrant 分工、融合策略、Manifest 发布、Mock-first 边界五项，每项写明备选方案与否决理由。

### P1-9　Mock 边界有缺口：无 Fake Feedback，且 MVP 向量召回的实现路径自相矛盾

- **问题**：01 §9 的 Mock 清单只有 Fake Catalog / Search / Recommendation / Similar / Evidence 五项，无 Fake Feedback；但 02 §12.1 门槛第 3 条要求“反馈事件可关联请求、候选集和后续业务结果”，01 §9 又要求 Mock 与真实共用“事件关联键”——没有 Fake Feedback，门槛第 3 条在 Mock 阶段无法验收。另，02 §5.4 称“MVP 可以先使用关键词、向量召回和轻量排序”，02 §5.5 又称“本次交付不启用”Qdrant、ES、Kafka——MVP 的向量召回若不用 Qdrant，靠什么实现未说明（Mock 向量？内存暴力检索？未定义）。
- **证据出处**：01 §9；02 §5.4、§5.5、§12.1。
- **严重度**：P1。
- **建议修法**：01 §9 补 Fake Feedback（或明确声明反馈在 Mock 阶段只记事件、不做归因计算）；02 §5.4 的 MVP 描述改为“MVP 的向量召回由 Mock Adapter 以固定 Fixture 模拟，不代表真实向量检索能力”，并与 §5.5 的“不启用”表述统一。

### P1-10　04 §15.2 声称“已写入 03”的三项设计，经核查在 03 中不存在或不成立

- **问题**：04 §15.2 标题为“已写入 `03` 的设计”，列出三项：（1）Video / Clip 两级检索体系——实际定义在 01 §4，03 全文零次出现 `entity_type`，无对象模型章节；（2）创作型推荐与“Creative Composition / Material Assignment Service”——03 只有 MaterialAssignment Artifact 与阶段八的分配步骤，无名为 Creative Composition 的服务，无“Composition Evaluator”（03 全文零命中）；（3）结构化创作中间表示 IR 链（CreativeBrief → Storyboard → ClipPlan → MaterialAssignment → EditDecision → TimelineIR → Timeline Compiler）——03 中 EditDecision、TimelineIR、Timeline Compiler 均为零命中，03 实际只有 MediaActionPlan（§5.5）。§15.2 自身用“已经（或应核对后视为已经）”的 hedging 表述，承认未经核对。三项“已写入”均不成立，会让读者误以为 03 已包含这些设计。
- **证据出处**：04 §15.2；01 §4；03 全文（`entity_type`、`EditDecision`、`TimelineIR`、`Composition Evaluator` 均为零命中；MaterialAssignment 见 §5.3 阶段八）。
- **严重度**：P1。
- **建议修法**：§15.2 改标题为“建议对照 03 核查的设计（尚未确认写入）”，三项逐条标注实际状态：（1）两级体系已写入 01 §4，03 未重复定义；（2）Creative Composition Service 未立项，仅有 MaterialAssignment 步骤，Composition Evaluator 待决策；（3）IR 链中 EditDecision / TimelineIR / Timeline Compiler 均未写入 03，是否引入需另立 ADR。

### P1-11　04 §15.1 把 Agent 能力映射到 AgentScope，与 03 的 Runtime 选型冲突

- **问题**：04 §15.1 的 VEA 映射表把 Agent Loop、Tool Executor、Agent Session 分别映射为“AgentScope ReAct Agent / Harness”“AgentScope Toolkit / Tool”“AgentScope Session”，并称“可以学习 VideoAgent 的动态任务图思想，再使用 AgentScope 2.0 的 Agent、Workflow、Harness 等能力实现”；但 03 §2.3 明确写道“AgentScope Java 2.0 只是尚未验证的服务端实现可能，不应成为业务依赖”，业务接入契约是 Acore Runtime SDK 0.2.0（03 §1.4 ADR-SDK-001 待验证）。04 一面声明“不建议再把 LangGraph 作为第二套核心 Agent Runtime 引入”（§15.1），一面用 AgentScope 作实现映射，却从未裁决 Acore Runtime SDK 与 AgentScope 2.0 的关系——AgentScope 若作为实现，本身就是第二套 Runtime。04 文首与 §15 的多处免责声明（“不是第二套目标架构”）缓解了此问题，但映射表的陈述语气仍会被误读为选型结论。
- **证据出处**：04 §15.1；03 §2.3、§1.4；04 行 1979。
- **严重度**：P1。
- **建议修法**：04 §15.1 的映射表改写为“调研对照（非实现映射）”，把“AgentScope ReAct Agent / Harness”等单元格改为“对应能力在 Acore Runtime SDK 中的位置（待 Spike 确认），AgentScope 仅作对照”；或立 ADR 裁决 Acore vs AgentScope，二选一，另一方从映射表中删除。

### P1-12　Search 与 Recommendation 的独立目标函数与评估集只有要求，没有定义

- **问题**：02 §5.3 要求“Search 与 Recommendation 必须有独立目标函数与评估集。即使底层共享模型服务，也不代表共享同一套训练标签和损失函数”；DM §8 开头重复“不得共享同一套目标函数和评估集”。但四份文档中没有任何一处给出任一目标函数的定义、标签来源、损失函数或评估集的构成（规模、标注方法、更新周期）。DM §2.2 更明确把“推荐训练、排序模型训练和 A/B 实验平台”列为不覆盖范围——要求提了，责任方却被排除在外，目标函数与评估集无主。
- **证据出处**：02 §5.3；DM §8、§2.2；02 §9（指标名无评估集定义）。
- **严重度**：P1。
- **建议修法**：在 02 §5.3 或 DM §8 补一节“目标函数与评估集占位规范”：至少定义 Search 与 Recommendation 各自的目标变量（点击/采用/任务满足度）、标签来源（反馈事件映射）、评估集规模与更新机制；或明确声明“目标函数与评估集为后续专项设计，本文不定义”，并将其列入实施 Backlog 而非写成已完成的要求。

---

## P2：建议（9 条）

### P2-1　引用失效清单（已逐条实测，当前目录下均不存在）

- **问题**：以下引用在当前 `search-rec-docs/` 目录下全部失效，按出现位置列出：01 行 3 `README.md`、01 行 3 `implementation/00_交付范围与VideoClip模型.md`、01 行 3 `implementation/07_跨域编排与领域子工作流设计.md`、01 §11 `implementation/01_API与数据契约.md` §8；02 行 9 `05_URRE数据与存储模型设计.md`（实际文件为 `urre/URRE数据与存储模型设计.md`）、02 §10.5 与 §12.1 `implementation/00…`、`implementation/03_实施路线图与验收基线.md`；04 文首与 §15 多处 `00/01/02/03` 旧编号、`02_AgentRuntime架构设计.md`、`03_VideoDomain架构设计.md`、`implementation/01_API与数据契约.md`、`implementation/02_技术选型与服务部署.md`、`runtime-sdk/java/overview.md`；DM 行 9 `implementation/00…`、DM §2.4 `implementation/05_VideoDomainAgent_工程契约与研发Backlog.md`。其中 02 §12.1 把“本次门槛”外包给两个不存在的文档（见 P2-4），已超出单纯引用失效的影响。
- **证据出处**：各文档行号如上；基线见本文开头“核查基线”。
- **严重度**：P2（但 P2-4 单列其验收层面的后果）。
- **建议修法**：建立“引用登记表”，逐条改写为现存文件的现存章节，或标注“外部文档，未收录”；02 §7 的“字段级权威见 implementation/01”在 implementation 缺失期间改为“字段级权威见 DM §8.5”。

### P2-2　02 §7“与 03 对象层级对齐”指错文档

- **问题**：02 §7 称“`entity_type` 与 `03` 对象层级对齐，枚举为 `video` / `clip`”——但 03 是 Agent 架构文档，全文零次出现 `entity_type`，无对象层级定义；对象层级实际在 01 §4（Video / Clip 两级）与 DM §4.2。读者按引用去 03 查不到任何对象定义。
- **证据出处**：02 §7；01 §4；03 全文 grep `entity_type` 零命中。
- **严重度**：P2。
- **建议修法**：改为“`entity_type` 与 01 §4 对象层级对齐，枚举为 `video` / `clip`，字段级权威见 DM §8.5”。

### P2-3　三处图片引用使用 Windows 绝对路径，在仓库内失效

- **问题**：01 §1、02 §3、02 §10 的图片引用均为 `C:\Users\Administrator\Desktop\search-rec-docs\images\…` 绝对路径，在任何其他机器与仓库内均无法解析；而对应图片实际存在于当前目录的 `images/` 下（`视频全链路智能创作架构图.png`、`URRE 与 Agent Runtime 统一架构图.png`、`原材料智能处理与检索全链路流程.png`）。04 的图片引用使用相对路径 `images/shared-chat/…`，是正确做法。
- **证据出处**：01 行 5；02 行 45、行 323；`images/` 目录实测。
- **严重度**：P2。
- **建议修法**：三处改为相对路径 `images/…`，与 04 的做法统一；顺带检查 04 的 10 张 `images/shared-chat/` 配图是否均为当前目录所有（实测 10 张均存在）。

### P2-4　02 的“本次门槛”无法在当前目录内验证

- **问题**：02 §10.5 称“本次门槛以 implementation/00 与 implementation/03 为准”，§12.1 同样以这两个不存在的文档为准——即 02 自身的验收标准指向目录外。DM §17 虽有验收基线，但 DM 文首声明“不构成本次 Mock 交付的门禁”，且 §17 全部是真实 URRE 的验收，与本次门槛无关。结果是：当前目录内没有任何一份文档能独立回答“本次 Mock 交付通过的标准是什么”。
- **证据出处**：02 §10.5、§12.1；DM 行 9、§17。
- **严重度**：P2（若计入验收可执行性则接近 P1；此处按任务口径列为引用类问题，但修法须按 P1 处理）。
- **建议修法**：在 02 §12.1 内直接写出本次门槛的可执行检查表（Mock Search / Recommendation / Similar 各至少一个可重复用例、零结果/超时/非法参数/重复候选四种异常、反馈关联键），不再外包给不存在的文档；或补收 implementation/00 与 implementation/03 两个文件。

### P2-5　术语不统一，无术语表

- **问题**：`data-control-plane`、`source-uploads/finalize`、`Search Projection`、`Canonicalization`、`Index Manifest`、`manifest_epoch` 等术语只在 02 §10 密集出现，DM 用 Source / Snapshot / Ingestion Job / Index Manifest 等另一套表述，两处术语无对照；“URRE 2.0”（02）、“真实 URRE”（DM）、“真实检索”（01）指同一概念却有三种叫法；“Mock-first”（01 §13 ADR-04）、“Mock Adapter”（02）、“FakeRetrievalGateway”（DM §20.1）三者关系未说明。
- **证据出处**：02 §10；DM §4–§5、§20.1；01 §13。
- **严重度**：P2。
- **建议修法**：补一页术语表（建议放在 01 或 02 文首），统一“真实 URRE 2.0”一名，明确 Mock Adapter = FakeRetrievalGateway 的同一实现、不同叫法，并给出 `data-control-plane` 的定义或删除该词。

### P2-6　04 §15.1 的 ViMax 与 Director 映射存在以偏概全的表述

- **问题**：04 §15.1 的 ViMax 映射表把“Video Generation”映射为“真实素材检索或生成”，将生成式视频与检索素材并列为同一格，掩盖了两者在版权、成本、延迟上的本质差异；Director 一节称“不要把 VideoDB 作为我们的基础设施前提。我们需要自建 URRE”，但自建 URRE 与 VideoDB 的取舍无任何选型记录（成本、功能、许可均未比较），该句只是立场声明。两者均为调研附录内的表述，不直接决定实施，但会被误读为已论证的结论。
- **证据出处**：04 §15.1（ViMax 映射表、Director 一节）。
- **严重度**：P2。
- **建议修法**：ViMax 映射表拆分为“真实素材检索”与“生成式视频”两行，生成式一行标注“本次不交付”；Director 一节补一句“自建 URRE 的选型依据见 02 §5.5（待补量化论证，见 P1-5）”，或删除选型式断言。

### P2-7　`chunk_id` 是否为第三级对象未澄清，与“Clip 是唯一片段层级”需对照

- **问题**：01 §4 与 02 §1、§6.1 反复强调“Clip 是唯一的片段层级”“不引入第三层素材对象”；但 DM §12.2 的 Point ID 构成含 `chunk_id`、`projection_id`，§12.3 Payload 有 `chunk_id` 字段，DM §21 第 3 条提及“文本分块长度、重叠和视觉采样密度”。Chunk（分块）是索引内部的切分单位还是业务对象？若 Point 粒度小于 Clip，02 §7 的 `entity_type: clip` 与 Point 级 `chunk_id` 之间的聚合规则（DM §12.5 第 5 步“按 entity_type + entity_id 聚合”）是否足以保证“唯一片段层级”？文档未正面回答。
- **证据出处**：01 §4；02 §1、§6.1；DM §12.2、§12.3、§21。
- **严重度**：P2。
- **建议修法**：在 DM §12.1 补一句“Chunk / Projection 仅为索引内部分块单位，不是业务对象层级，不进入 Video / Clip 之外的枚举”，并说明 Point 到 Clip 的聚合规则已由 §12.5 第 5 步覆盖。

### P2-8　01 §5 路由表与 03 §3.1 R0–R4 两套路由表述无映射

- **问题**：01 §5 用业务语言列路由（Direct Search / Direct Similar / Direct Recommendation / Agent Workflow / CreativeProductionWorkflow），03 §3.1 用 R0–R4 分级（R0 Direct API、R1 轻量 Agent、R2 单主 Agent、R3 并行、R4 Workflow + 审批），两套表述无映射关系。例如 01 的“替换单个计划 Clip → Agent Workflow”对应 R1 还是 R2？01 的“跨域任务 → CreativeProductionWorkflow”对应 R4 是否等价？03 §3.2 的示例只覆盖 R0/R2/R3/R4，R1 无示例。
- **证据出处**：01 §5；03 §3.1、§3.2。
- **严重度**：P2。
- **建议修法**：在 03 §3.2 补一张映射表（01 §5 每一行 → R0–R4），并给 R1 补一个路由示例；或在 01 §5 注明“路由分级详见 03 §3.1”。

### P2-9　04 §15.2 的“创作型推荐”示例与 03 的分镜覆盖无对应验收

- **问题**：04 §15.2 建议“组合评估不仅看单条素材相关性，还要看 Clip 覆盖完整性、叙事逻辑、互补性、视觉风格一致性”等 6 项，但 03 的 MaterialAssignment（§5.3 阶段八）只规定首选 1 条、替代最多 3 条、shortlist 最多 10 条，无任何组合级评估指标；02 §9 的推荐指标（Adoption@K、覆盖度、多样性、新颖性）是单候选级指标，无“组合完整性”指标。示例很生动，但无一处可验收。
- **证据出处**：04 §15.2；03 §5.3 阶段八；02 §9.2。
- **严重度**：P2。
- **建议修法**：将 6 项组合评估标准降级为“待立项的评估维度”，或在 02 §9.2 补“组合级指标（覆盖完整性、风格一致性）”的占位定义与负责人。

---

## 附录 A：一致性核查通过的点（未列入问题清单，供 v2 参考）

1. **Video / Clip 两级对象**：01 §4、02 §1/§6.1、DM §4.2 三处一致，枚举均为 `video` / `clip`，Clip 含父 Video 关系。
2. **Agent 不越界检索**：03 §5.1 明确禁止 Agent 直读数据库/索引/Fixture、禁止改候选分数、只处理小候选集；01 §3、§5 与 03 §3.2 的“简单检索不启动 Agent”一致；DM §20.3 的“不得回流”条款与之一致。Agent 侧边界本身是清晰的，问题只在阶段七评估与重排的衔接（P1-6）。
3. **硬过滤在排序前生效**：02 §3/§5.2、DM §8.1、DM §12.5 三处一致；ES/Qdrant 均保存租户与权限字段（02 §10.4、DM §15.3）。
4. **Active Manifest 为唯一原子发布点**：02 §10.4 与 DM §6.2/§19 URRE-DM-ADR-04 一致；ES/Qdrant Alias 不承担跨系统发布，两处一致（状态集合分歧见 P0-5，不影响该原则本身）。
5. **04 的免责声明本身是到位的**：04 文首、§4、§5、§10、§13、§15 多处声明“不是目标架构/阶段计划/API/选型权威”“与主文冲突时以后者为准”；问题在于 §15.1 的映射表与 §15.2 的“已写入”标题在语气上越过了声明（P1-10、P1-11）。
6. **Mock 与真实共用 Port 的方向一致**：01 §9、02 §12.1、DM §20.2 三处均要求同一 Port、同一 CandidateSet 契约、可替换 Adapter；分歧只在 CandidateSet 的字段版本（P0-3）。

## 附录 B：审计方法

- 逐行通读 02 全文（498 行），按节提取交付边界、能力、流水线、选型、契约、反馈、验收主张。
- 对每项主张在 01、03、04、DM 中做反向检索（定义、枚举、数值、状态机、引用路径），记录一致/冲突/缺失。
- 引用存在性用 `ls` / 文件清单实测（基线见文首），不依赖文档自述。
- 03 全文 grep 验证：`Explore` 零命中；`entity_type`、`EditDecision`、`TimelineIR`、`Composition Evaluator` 零命中；`SearchPlan` 只在 03 出现。
- DM §8.1 示例 `recall.channels` 含 `metadata`，02 §5.1 九通道无此值；DM §8 端点表无 `/retrieval/explore`。
- 未审计：`urre/搜推排序.md`、`urre/Query 语义理解.md`（不在本次任务范围内，建议 v2 组核查其排序公式与 Query 理解定义是否与 02 §5/DM §8 一致）；图片内容本身未做像素级核对，只核对引用路径。
