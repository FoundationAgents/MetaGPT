# Meta-Org Agent: 动态组织编排系统

## Goal
分析 MetaGPT 当前 Agent 编排流程的局限性，设计并实现"元组织 Agent"，使组织结构本身成为可学习、可进化的系统。

---

## Task Breakdown

### Phase 1: 现状分析
- [x] 1.1 分析 Team/Environment/Role 架构
- [x] 1.2 识别静态配置的局限性
- [ ] 1.3 文档化当前编排流程

### Phase 2: 信号系统设计
- [x] 2.1 定义组织健康信号（Outcome/Process/Cognitive）
- [x] 2.2 实现 SignalCollector 信号收集器
- [x] 2.3 集成到 Trace 系统 (via decorators)

### Phase 3: Meta-Org Agent 实现
- [x] 3.1 实现 Agent 生命周期模型
- [x] 3.2 实现组织诊断器（OrgAnalyzer embedded in Agent）
- [x] 3.3 实现 Agent 动态增删/合并 (Basic capabilities)

### Phase 4: SOP 进化
- [ ] 4.1 实现 SOP 动态调整
- [ ] 4.2 实现 Review 强度自适应
- [ ] 4.3 编写测试和文档
