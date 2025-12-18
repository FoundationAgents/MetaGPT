# Meta-Org Agent 实现计划

## 一、当前架构分析

### 现有编排机制

```
┌─────────────────────────────────────────────────────┐
│                     Team                            │
│  ┌───────────────────────────────────────────────┐  │
│  │ hire(roles) → 静态添加                        │  │
│  │ run(n_round) → 固定轮次循环                   │  │
│  └───────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   Environment                        │
│  ┌───────────────────────────────────────────────┐  │
│  │ roles: Dict[str, Role]  ← 静态角色池          │  │
│  │ run() → for role in roles: role.run()        │  │
│  └───────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                      Role                            │
│  ┌───────────────────────────────────────────────┐  │
│  │ _watch() → 固定订阅                           │  │
│  │ _think() → 选择预设 Action                    │  │
│  │ _act() → 执行 Action                          │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 核心局限性

| 局限性 | 现状 | 问题 |
|--------|------|------|
| **静态角色** | `Team.hire()` 一次性配置 | 无法根据任务动态调整 |
| **固定 SOP** | 角色订阅关系硬编码 | 无法适应新领域 |
| **无反馈** | 执行完即结束 | 无法从失败中学习 |
| **无仲裁** | Review 分歧无解决机制 | 可能陷入死循环 |
| **无优化** | 成本/质量无自动平衡 | 过度 Review 或质量不足 |

### 代码证据

```python
# team.py - 静态配置
def hire(self, roles: list[Role]):
    """Hire roles to cooperate"""
    self.env.add_roles(roles)  # 一次性添加，无法动态调整

# base_env.py - 简单轮询
async def run(self, k=1):
    for _ in range(k):
        for role in self.roles:  # 固定顺序遍历
            if role.is_idle:
                continue
            await role.run()  # 无条件执行
```

---

## 二、Meta-Org Agent 设计

### 核心理念

> **元组织 Agent 不做任务，而是负责"设计和进化做任务的组织"**

```
                    ┌─────────────────────┐
                    │   Meta-Org Agent    │
                    └─────────┬───────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    Signal Observer    Org Analyzer       SOP Designer
          │                   │                   │
          └─────────────┬─────┴─────┬─────────────┘
                        │           │
                Agent Lifecycle Manager
                        │
                 Active Agent Pool
```

---

## 三、信号系统

### 输入信号定义

```python
class OrgSignal(BaseModel):
    """组织健康信号"""
    signal_type: SignalType
    severity: float  # 0.0 - 1.0
    source: str  # 信号来源（角色/动作）
    details: Dict[str, Any]
    timestamp: datetime

class SignalType(str, Enum):
    # 结果信号
    FAILURE = "failure"              # 任务失败
    RETRY = "retry"                  # 重试发生
    ROLLBACK = "rollback"            # 回滚发生
    REVIEW_BLOCK = "review_block"    # Review 阻塞
    
    # 过程信号
    LOOP_DETECTED = "loop"           # 循环拉扯
    SLOW_DECISION = "slow"           # 决策过慢
    CONFLICT = "conflict"            # 意见冲突
    
    # 认知信号
    UNCERTAINTY = "uncertainty"      # 不确定性高
    ASSUMPTION_GAP = "assumption"    # 假设未验证
    BLIND_SPOT = "blind_spot"        # 盲区检测
```

### 信号收集时机

| 时机 | 信号类型 | 触发条件 |
|------|----------|----------|
| Action 失败 | FAILURE | Exception 或结果不符合预期 |
| HITL 驳回 | REVIEW_BLOCK | ReviewDecision.REJECT |
| 多次迭代 | LOOP_DETECTED | 同一 Action 执行 > 3 次 |
| 执行超时 | SLOW_DECISION | duration_ms > threshold |
| LLM 输出 | UNCERTAINTY | 包含"可能/也许/不确定" |

---

## 四、Agent 生命周期

```python
class AgentLifecycleState(str, Enum):
    PROPOSED = "proposed"       # 新提议的角色
    EXPERIMENTAL = "experimental"  # 试验中
    ACTIVE = "active"           # 正式激活
    DEPRECATED = "deprecated"   # 已弃用
    REMOVED = "removed"         # 已移除

class AgentLifecycle(BaseModel):
    """Agent 生命周期管理"""
    role_name: str
    role_class: str
    state: AgentLifecycleState
    
    # 试验期配置
    evaluation_window: int = 5  # 评估周期（项目数）
    success_criteria: Dict[str, float]  # 成功指标
    
    # 统计
    projects_participated: int = 0
    success_rate: float = 0.0
    value_score: float = 0.0
    
    # 状态转换历史
    state_history: List[tuple[AgentLifecycleState, datetime]]
```

### 状态转换规则

```
PROPOSED → EXPERIMENTAL: Meta-Org Agent 批准
EXPERIMENTAL → ACTIVE: 达到成功标准
EXPERIMENTAL → REMOVED: 未达标准
ACTIVE → DEPRECATED: 价值持续低
DEPRECATED → REMOVED: 确认无用
DEPRECATED → ACTIVE: 重新激活（条件变化）
```

---

## 五、新增/删除 Agent 触发模式

### 模式 A：盲区型失败 → 新增 Agent

**信号**：同类问题反复出现，无 Agent 负责发现

**示例**：
```yaml
Signal: BLIND_SPOT
Details:
  pattern: "Security vulnerability in generated code"
  occurrences: 3
  
Action:
  type: ADD_AGENT
  role:
    name: SecurityReviewer
    profile: "Security Threat Analyst"
    actions: [ThreatModeling, VulnerabilityScan]
    watch: [WriteCode]
```

### 模式 B：认知过载 → 拆分 Agent

**信号**：单一 Agent 输出过长，质量波动大

**示例**：
```yaml
Signal: COGNITIVE_OVERLOAD
Details:
  role: Architect
  avg_output_length: 15000
  quality_variance: 0.35
  
Action:
  type: SPLIT_AGENT
  from: Architect
  to:
    - name: SystemArchitect
      focus: "High-level design"
    - name: ScalabilityAnalyst
      focus: "Performance and scaling"
```

### 模式 C：决策冲突 → 新增仲裁 Agent

**信号**：Review 循环无法收敛

**示例**：
```yaml
Signal: CONFLICT
Details:
  between: [Architect, QAEngineer]
  iterations: 5
  unresolved: true
  
Action:
  type: ADD_ARBITER
  role:
    name: DesignArbiter
    profile: "Technical Decision Maker"
    authority_over: [Architect, QAEngineer]
```

### 模式 D：无价值输出 → 合并/移除 Agent

**信号**：Agent 输出长期未被引用

**示例**：
```yaml
Signal: LOW_VALUE
Details:
  role: DocumentationWriter
  output_referenced_rate: 0.05
  last_useful_output: "2024-01-01"
  
Action:
  type: MERGE_AGENT
  merge: DocumentationWriter
  into: Engineer
  as_action: WriteDocumentation
```

---

## 六、实现计划

### Phase 1: 信号基础设施

#### [NEW] metagpt/meta_org/signals.py

信号定义和收集器。

```python
class SignalCollector:
    """收集组织健康信号"""
    
    def __init__(self):
        self.signals: List[OrgSignal] = []
    
    def record_failure(self, role: str, action: str, error: str):
        self.signals.append(OrgSignal(
            signal_type=SignalType.FAILURE,
            source=f"{role}.{action}",
            details={"error": error}
        ))
    
    def record_loop(self, role: str, action: str, count: int):
        self.signals.append(OrgSignal(
            signal_type=SignalType.LOOP_DETECTED,
            source=f"{role}.{action}",
            details={"iterations": count}
        ))
    
    def analyze_patterns(self) -> List[OrgPattern]:
        """分析信号模式"""
        # 检测盲区
        blind_spots = self._detect_blind_spots()
        # 检测过载
        overloads = self._detect_overloads()
        # 检测冲突
        conflicts = self._detect_conflicts()
        return blind_spots + overloads + conflicts
```

---

### Phase 2: Meta-Org Agent 核心

#### [NEW] metagpt/meta_org/agent.py

```python
META_ORG_SYSTEM_PROMPT = """
You are the Meta-Organization Agent.

Mission:
- Optimize the organization structure to achieve goals with minimal irreversible errors

You do NOT:
- Implement features
- Review content directly

You DO:
- Observe organizational signals
- Modify the agent graph and SOP dynamically

Inputs:
- Outcome metrics
- Process logs
- Agent interaction traces

Responsibilities:
- Decide when to add, remove, split, or merge agents
- Adjust review strictness and decision gates
- Propose new agent roles with clear responsibilities

Rules:
- Prefer adding agents only when failure is systemic
- Prefer removing agents only when value is consistently low
- Every organizational change must include a rationale

Output Format:
1. Organizational Diagnosis
2. Identified Bottlenecks
3. Proposed Changes (Add / Remove / Modify Agent)
4. Expected Impact
5. Rollback Plan
"""

class MetaOrgAgent:
    """元组织 Agent - 管理组织进化"""
    
    def __init__(self, team: Team, llm: BaseLLM):
        self.team = team
        self.llm = llm
        self.signal_collector = SignalCollector()
        self.lifecycle_manager = AgentLifecycleManager()
    
    async def analyze_and_adapt(self):
        """分析信号并调整组织"""
        # 1. 收集信号
        signals = self.signal_collector.get_recent_signals()
        
        # 2. 分析模式
        patterns = self.signal_collector.analyze_patterns()
        
        # 3. 生成诊断
        diagnosis = await self._generate_diagnosis(signals, patterns)
        
        # 4. 提出变更
        changes = await self._propose_changes(diagnosis)
        
        # 5. 执行变更（需要 HITL 审批）
        await self._execute_changes(changes)
    
    async def _propose_changes(self, diagnosis: str) -> List[OrgChange]:
        """基于诊断提出组织变更"""
        prompt = f"""
{META_ORG_SYSTEM_PROMPT}

## Current Diagnosis
{diagnosis}

## Current Team Structure
{self._describe_team()}

Based on the diagnosis, propose organizational changes.
"""
        response = await self.llm.aask(prompt)
        return self._parse_changes(response)
```

---

### Phase 3: 集成到 Team

#### [MODIFY] team.py

```python
class Team(BaseModel):
    meta_org_enabled: bool = False
    meta_org_agent: Optional[MetaOrgAgent] = None
    
    async def run(self, ...):
        # 初始化 Meta-Org
        if self.meta_org_enabled:
            self.meta_org_agent = MetaOrgAgent(self, self.llm)
        
        try:
            # 正常执行
            while n_round > 0:
                await self.env.run()
                n_round -= 1
                
                # 周期性组织分析
                if self.meta_org_enabled and n_round % 5 == 0:
                    await self.meta_org_agent.analyze_and_adapt()
        finally:
            # 项目结束后复盘
            if self.meta_org_enabled:
                await self.meta_org_agent.postmortem()
```

---

## 七、预期效果

### Before vs After

| 场景 | Before | After |
|------|--------|-------|
| 新领域任务 | 原 SOP 失败 | Meta-Org 检测盲区，新增专家角色 |
| 质量下降 | 不知道哪里出问题 | 信号系统定位到具体 Agent/Action |
| 成本过高 | 人工优化 | 自动弱化低价值 Review |
| 创新停滞 | 角色分工固化 | 动态拆分/合并角色 |

### 组织进化示例

```
项目 1: 贪吃蛇游戏
├── 初始团队: PM, Architect, Engineer
├── 信号: 无安全 Review
├── 变更: 无（简单项目）

项目 2: 支付系统
├── 初始团队: PM, Architect, Engineer
├── 信号: 安全漏洞反复出现
├── 变更: + SecurityReviewer（试验期）

项目 3: 交易平台
├── 团队: PM, Architect, Engineer, SecurityReviewer
├── 信号: SecurityReviewer 发现 3 个关键漏洞
├── 变更: SecurityReviewer → ACTIVE

项目 4: 内部工具
├── 团队: PM, Architect, Engineer, SecurityReviewer
├── 信号: SecurityReviewer 输出未被引用
├── 变更: SecurityReviewer 降权（简单项目跳过）
```

---

## 八、实现优先级

| 优先级 | 功能 | 复杂度 | 价值 |
|--------|------|--------|------|
| P0 | 信号收集基础设施 | 中 | 高 |
| P0 | Agent 生命周期模型 | 中 | 高 |
| P1 | 模式检测算法 | 高 | 高 |
| P1 | Meta-Org Prompt 设计 | 中 | 高 |
| P2 | 自动化变更执行 | 高 | 中 |
| P2 | SOP 动态调整 | 高 | 中 |

---

## 九、风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 过度调整组织 | 设置变更冷却期，HITL 审批 |
| 误判信号 | 多信号交叉验证，置信度阈值 |
| 组织混乱 | Agent 试验期机制，可回滚 |
| 成本增加 | 预算限制，成本感知决策 |
