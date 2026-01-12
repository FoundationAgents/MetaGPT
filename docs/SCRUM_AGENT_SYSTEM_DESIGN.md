# MetaGPT-Pro SCRUM Agent System
## Comprehensive Design Document v1.0

> A complete specification for building a SCRUM-based AI Agent management system with real-time updates, human interaction, and knowledge management.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Business Rules](#3-business-rules)
4. [Execution Modes](#4-execution-modes)
5. [Agent Roles & Responsibilities](#5-agent-roles--responsibilities)
6. [SCRUM Process Flows](#6-scrum-process-flows)
7. [Human-AI Interaction](#7-human-ai-interaction)
8. [Event System & Logging](#8-event-system--logging)
9. [Knowledge Management](#9-knowledge-management)
10. [Project Resources](#10-project-resources)
11. [State Persistence](#11-state-persistence)
12. [API Specifications](#12-api-specifications)
13. [Dashboard Integration](#13-dashboard-integration)
14. [Implementation Roadmap](#14-implementation-roadmap)

---

## 1. Executive Summary

### 1.1 Purpose
Build a fully-featured SCRUM-based AI Agent system that provides:
- **Real-time visibility** into agent activities
- **Human collaboration** at key decision points
- **Persistent state** that survives restarts
- **Multiple execution modes** (autonomous, hybrid, interactive)
- **Knowledge sharing** between humans and AI agents

### 1.2 Current State Issues
| Issue | Description |
|-------|-------------|
| No persistence | Project state lost on refresh/restart |
| No real-time updates | Dashboard doesn't reflect agent progress |
| Single async execution | Agents run to completion without reporting |
| No human checkpoints | No approval gates in the process |
| No knowledge management | Documents generated but not organized |

### 1.3 Target State
A system where:
- Every agent action is logged and broadcasted
- Humans can intervene at any point
- Projects persist across sessions
- SCRUM ceremonies are properly implemented
- Knowledge flows bidirectionally between humans and AI

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  SCRUM Dashboard │  │  Agent Monitor  │  │  Knowledge Portal      │  │
│  │  - Sprint Board  │  │  - Live Status  │  │  - Documents           │  │
│  │  - Kanban Board  │  │  - Activity Log │  │  - Upload/Download     │  │
│  │  - Backlog       │  │  - Interventions│  │  - Search              │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ WebSocket + REST API
┌──────────────────────────────▼──────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    SCRUM Orchestrator                            │   │
│  │  • Mode Controller (Autonomous/Hybrid/Interactive)               │   │
│  │  • Sprint Lifecycle Manager                                      │   │
│  │  • Event Broadcaster                                             │   │
│  │  • State Persistence Manager                                     │   │
│  │  • Human Interaction Queue                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                         AGENT LAYER                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ ProductOwner │ │ ScrumMaster  │ │  Architect   │ │   Engineer   │   │
│  │ Agent        │ │ Agent        │ │  Agent       │ │   Agent      │   │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤   │
│  │• PRD         │ │• Ceremonies  │ │• System Arch │ │• Code        │   │
│  │• User Stories│ │• Blockers    │ │• API Design  │ │• Tests       │   │
│  │• Backlog     │ │• Metrics     │ │• Data Model  │ │• Debug       │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │ QA Engineer  │ │  DevOps      │ │  Reviewer    │                    │
│  │ Agent        │ │  Agent       │ │  Agent       │                    │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤                    │
│  │• Test Cases  │ │• Deployment  │ │• Code Review │                    │
│  │• Bug Reports │ │• CI/CD       │ │• Quality     │                    │
│  │• Validation  │ │• Monitoring  │ │• Standards   │                    │
│  └──────────────┘ └──────────────┘ └──────────────┘                    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                         PERSISTENCE LAYER                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ Project Store   │  │  Knowledge Base │  │  Activity Log Store    │  │
│  │ • Projects      │  │  • Documents    │  │  • Events              │  │
│  │ • Sprints       │  │  • Templates    │  │  • Metrics             │  │
│  │ • Tasks         │  │  • Artifacts    │  │  • Audit Trail         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Details

#### 2.2.1 SCRUM Orchestrator
The central coordination engine that:
- Manages execution mode (autonomous/hybrid/interactive)
- Coordinates agent activities
- Handles human intervention requests
- Broadcasts all state changes
- Persists state to storage

#### 2.2.2 Agent Base Class (SCRUMRole)
All agents inherit from this base:
```python
class SCRUMRole(Role):
    """Base class for all SCRUM agents"""
    
    # Required overrides
    name: str                    # Agent name
    profile: str                 # Role description
    goal: str                    # Agent's primary goal
    
    # SCRUM-specific
    current_task: Optional[Task] # Current assigned task
    sprint_id: Optional[str]     # Current sprint
    
    # Communication
    async def broadcast_status(self, status: AgentStatus) -> None
    async def request_human_input(self, question: str) -> str
    async def update_task_status(self, task_id: str, status: TaskStatus) -> None
    
    # Lifecycle hooks
    async def on_sprint_start(self, sprint: Sprint) -> None
    async def on_sprint_end(self, sprint: Sprint) -> None
    async def on_task_assigned(self, task: Task) -> None
    async def on_task_completed(self, task: Task) -> None
```

---

## 3. Business Rules

### 3.1 Project Lifecycle Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| BR-001 | Every project MUST have a Product Owner | System blocks project creation without PO |
| BR-002 | Sprints MUST have a defined duration (1-4 weeks) | Validated on sprint creation |
| BR-003 | Tasks MUST be estimated before sprint inclusion | Blocks un-estimated tasks |
| BR-004 | Completed tasks require QA validation | Status change blocked without QA sign-off |
| BR-005 | Sprint scope CANNOT change mid-sprint (unless emergency) | Requires human approval |

### 3.2 Agent Behavior Rules

| Rule ID | Rule | Description |
|---------|------|-------------|
| AG-001 | Agents MUST broadcast status on every action | No silent actions allowed |
| AG-002 | Agents MUST update task status when working | Kanban auto-updates |
| AG-003 | Agents CAN request human assistance | Pauses execution for input |
| AG-004 | Agents MUST log all artifacts created | Knowledge base auto-populates |
| AG-005 | Agents MUST handle errors gracefully | No silent failures |

### 3.3 Human Interaction Rules

| Rule ID | Rule | Description |
|---------|------|-------------|
| HI-001 | Critical decisions require human approval | PRD approval, deployment, etc. |
| HI-002 | Humans can pause/resume execution at any time | Emergency stop available |
| HI-003 | Humans can modify task priorities | Real-time backlog editing |
| HI-004 | Humans can inject new requirements | Mid-sprint changes handled |
| HI-005 | All human decisions are logged | Audit trail maintained |

### 3.4 State Persistence Rules

| Rule ID | Rule | Description |
|---------|------|-------------|
| SP-001 | State MUST persist across restarts | File/DB storage required |
| SP-002 | State changes trigger immediate save | No data loss on crash |
| SP-003 | Historical state MUST be queryable | Sprint history preserved |
| SP-004 | Concurrent access MUST be handled | Lock mechanisms in place |

---

## 4. Execution Modes

### 4.1 Mode Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      EXECUTION MODES                                 │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│  AUTONOMOUS     │     HYBRID          │       INTERACTIVE           │
│  (Full Auto)    │  (Semi-Supervised)  │     (Pair Programming)      │
├─────────────────┼─────────────────────┼─────────────────────────────┤
│ • AI runs       │ • AI runs with      │ • Human drives each step    │
│   independently │   checkpoints       │ • AI assists/suggests       │
│ • Human reviews │ • Human approves    │ • Real-time collaboration   │
│   at end        │   key decisions     │ • Full control to human     │
│ • Best for      │ • Best for          │ • Best for learning/        │
│   trusted tasks │   most projects     │   sensitive projects        │
└─────────────────┴─────────────────────┴─────────────────────────────┘
```

### 4.2 Mode: AUTONOMOUS

**Description**: AI agents work independently to complete the entire project.

**Use Cases**:
- Well-defined, repetitive tasks
- Low-risk projects
- Proof of concept work
- Internal tooling

**Flow**:
```
User submits requirement
       │
       ▼
┌──────────────────┐
│ ProductOwner     │──▶ Creates PRD, User Stories
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Architect        │──▶ Designs system architecture
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Engineer         │──▶ Implements code
└────────┬─────────┘
         ▼
┌──────────────────┐
│ QA Engineer      │──▶ Tests and validates
└────────┬─────────┘
         ▼
┌──────────────────┐
│ DevOps           │──▶ Deploys application
└────────┬─────────┘
         ▼
  Human receives notification
  Reviews completed project
```

**Checkpoints** (notifications only, no blocking):
- PRD generated
- Architecture complete
- Code complete
- Tests passed
- Deployed

### 4.3 Mode: HYBRID (Recommended Default)

**Description**: AI agents work but pause at key decision points for human approval.

**Use Cases**:
- Production projects
- Client deliverables
- Projects with uncertain requirements
- Learning/training scenarios

**Flow**:
```
User submits requirement
       │
       ▼
┌──────────────────┐
│ ProductOwner     │──▶ Creates PRD, User Stories
└────────┬─────────┘
         ▼
   ⏸️ PAUSE: Human reviews PRD
   ✅ Approve / ❌ Request changes
         │
         ▼
┌──────────────────┐
│ Architect        │──▶ Designs system architecture
└────────┬─────────┘
         ▼
   ⏸️ PAUSE: Human reviews architecture
   ✅ Approve / ❌ Request changes
         │
         ▼
   ...continues with pauses at key points...
```

**Checkpoints** (blocking, requires approval):
- [ ] PRD Approval
- [ ] Architecture Approval
- [ ] Code Review Approval
- [ ] Deployment Approval

### 4.4 Mode: INTERACTIVE

**Description**: Human and AI work together step-by-step, like pair programming.

**Use Cases**:
- Training new team members
- Highly sensitive projects
- Regulatory/compliance projects
- Complex decision making

**Flow**:
```
┌─────────────────────────────────────────────────────────────┐
│                  INTERACTIVE SESSION                         │
│                                                              │
│  Human: "Create a login feature"                            │
│     │                                                        │
│     ▼                                                        │
│  AI: "I'll create a user story for login. Here's my draft:" │
│      [User Story Preview]                                    │
│      "Would you like to modify this?"                        │
│     │                                                        │
│     ▼                                                        │
│  Human: "Add 2FA requirement"                               │
│     │                                                        │
│     ▼                                                        │
│  AI: "Updated. Ready for next step?"                        │
│     │                                                        │
│     ▼                                                        │
│  Human: "Proceed"                                           │
│     │                                                        │
│     ▼                                                        │
│  AI: [Continues to next action...]                          │
└─────────────────────────────────────────────────────────────┘
```

### 4.5 Mode Configuration

```yaml
# config/execution_mode.yaml
execution:
  mode: "hybrid"  # autonomous | hybrid | interactive
  
  autonomous:
    notify_on_completion: true
    max_runtime_hours: 4
    
  hybrid:
    approval_required:
      - prd_complete
      - architecture_complete
      - pre_deployment
    timeout_minutes: 60  # Auto-proceed if no response
    
  interactive:
    confirmation_required_for_each_step: true
    auto_suggest_next_action: true
```

---

## 5. Agent Roles & Responsibilities

### 5.1 Agent Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT HIERARCHY                               │
│                                                                      │
│                    ┌─────────────────┐                              │
│                    │  ScrumMaster    │                              │
│                    │  (Coordinator)  │                              │
│                    └────────┬────────┘                              │
│                             │                                        │
│          ┌──────────────────┼──────────────────┐                    │
│          │                  │                  │                    │
│  ┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐           │
│  │ ProductOwner  │  │  Development  │  │    Quality    │           │
│  │ Agent         │  │  Team         │  │    Team       │           │
│  └───────────────┘  └───────┬───────┘  └───────┬───────┘           │
│                             │                  │                    │
│                    ┌────────┴────────┐  ┌──────┴──────┐             │
│                    │                 │  │             │             │
│            ┌───────▼───────┐ ┌───────▼───────┐ ┌──────▼──────┐     │
│            │  Architect    │ │   Engineer    │ │ QA Engineer │     │
│            └───────────────┘ └───────────────┘ └─────────────┘     │
│                                     │                               │
│                             ┌───────▼───────┐                       │
│                             │    DevOps     │                       │
│                             └───────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 ProductOwner Agent

**Profile**: Business requirements expert who translates ideas into actionable specs.

| Attribute | Value |
|-----------|-------|
| **Primary Goal** | Create clear, complete, prioritized requirements |
| **Input** | Raw ideas, business needs, stakeholder feedback |
| **Output** | PRD, User Stories, Acceptance Criteria, Backlog |
| **Interacts With** | Human stakeholders, ScrumMaster, Architect |

**Actions**:
```python
class ProductOwnerAgent(SCRUMRole):
    actions = [
        "analyze_requirements",      # Parse and understand input
        "create_prd",                # Generate Product Requirements Document
        "create_user_stories",       # Break down into user stories
        "define_acceptance_criteria", # Clear pass/fail criteria
        "prioritize_backlog",        # Order by business value
        "refine_stories",            # Clarify based on feedback
    ]
```

**Outputs**:
- `docs/prd.md` - Product Requirements Document
- `docs/user_stories.json` - Structured user stories
- `data/backlog.json` - Prioritized product backlog

### 5.3 ScrumMaster Agent

**Profile**: Process guardian who ensures SCRUM is followed and removes blockers.

| Attribute | Value |
|-----------|-------|
| **Primary Goal** | Facilitate smooth sprint execution |
| **Input** | Team status, blockers, metrics |
| **Output** | Daily reports, blocker resolutions, process improvements |
| **Interacts With** | All agents, Human stakeholders |

**Actions**:
```python
class ScrumMasterAgent(SCRUMRole):
    actions = [
        "facilitate_sprint_planning",  # Run planning ceremony
        "conduct_daily_standup",       # Daily sync
        "identify_blockers",           # Detect issues
        "remove_blockers",             # Resolve or escalate
        "facilitate_sprint_review",    # Demo to stakeholders
        "facilitate_retrospective",    # Process improvement
        "track_velocity",              # Measure team performance
    ]
```

**Outputs**:
- `reports/daily_standup_{date}.md` - Daily status
- `reports/sprint_review_{id}.md` - Sprint summary
- `reports/retrospective_{id}.md` - Lessons learned
- `data/metrics.json` - Velocity, burndown, etc.

### 5.4 Architect Agent

**Profile**: Technical leader who designs scalable, maintainable systems.

| Attribute | Value |
|-----------|-------|
| **Primary Goal** | Design robust system architecture |
| **Input** | PRD, Technical constraints, Best practices |
| **Output** | System design, API specs, Data models |
| **Interacts With** | ProductOwner, Engineer, Reviewer |

**Actions**:
```python
class ArchitectAgent(SCRUMRole):
    actions = [
        "analyze_technical_requirements",  # Understand needs
        "design_system_architecture",      # High-level design
        "design_api_contracts",            # API specifications
        "design_data_models",              # Database schema
        "define_tech_stack",               # Technology choices
        "create_component_diagram",        # Visual architecture
        "review_implementation",           # Validate code matches design
    ]
```

**Outputs**:
- `docs/architecture.md` - System design document
- `docs/api_spec.yaml` - OpenAPI specification
- `docs/data_model.md` - Database design
- `docs/component_diagram.mmd` - Mermaid diagram

### 5.5 Engineer Agent

**Profile**: Developer who writes clean, tested, production-ready code.

| Attribute | Value |
|-----------|-------|
| **Primary Goal** | Implement features according to specifications |
| **Input** | User stories, Architecture, Coding standards |
| **Output** | Source code, Unit tests, Documentation |
| **Interacts With** | Architect, QA Engineer, Reviewer |

**Actions**:
```python
class EngineerAgent(SCRUMRole):
    actions = [
        "analyze_story",           # Understand requirements
        "design_implementation",   # Plan approach
        "write_code",              # Implement feature
        "write_unit_tests",        # Test coverage
        "fix_bugs",                # Debug and fix
        "refactor_code",           # Improve quality
        "document_code",           # Code comments + README
        "compile_and_validate",    # Ensure it builds
    ]
```

**Outputs**:
- `src/**/*.{py,js,ts}` - Source code files
- `tests/**/*_test.{py,js,ts}` - Test files
- `docs/api_usage.md` - API documentation

### 5.6 QA Engineer Agent

**Profile**: Quality guardian who ensures software meets requirements.

| Attribute | Value |
|-----------|-------|
| **Primary Goal** | Validate software quality and functionality |
| **Input** | User stories, Acceptance criteria, Code |
| **Output** | Test plans, Bug reports, Quality metrics |
| **Interacts With** | ProductOwner, Engineer, ScrumMaster |

**Actions**:
```python
class QAEngineerAgent(SCRUMRole):
    actions = [
        "create_test_plan",         # Test strategy
        "create_test_cases",        # Specific test scenarios
        "execute_tests",            # Run manual/auto tests
        "report_bugs",              # Document issues found
        "verify_fixes",             # Confirm bugs resolved
        "regression_testing",       # Ensure no new breaks
        "generate_quality_report",  # Metrics and status
    ]
```

**Outputs**:
- `tests/test_plan.md` - Test strategy
- `tests/test_cases.json` - Test scenarios
- `reports/bugs.json` - Bug tracking
- `reports/quality_report.md` - Quality metrics

### 5.7 DevOps Agent

**Profile**: Infrastructure expert who ensures smooth deployment and operations.

| Attribute | Value |
|-----------|-------|
| **Primary Goal** | Reliable, fast, secure deployments |
| **Input** | Code, Infrastructure requirements |
| **Output** | CI/CD pipelines, Deployment configs, Monitoring |
| **Interacts With** | Engineer, Architect, ScrumMaster |

**Actions**:
```python
class DevOpsAgent(SCRUMRole):
    actions = [
        "setup_ci_pipeline",        # Automated builds
        "setup_cd_pipeline",        # Automated deployments
        "configure_infrastructure", # Cloud/server setup
        "deploy_application",       # Push to environment
        "setup_monitoring",         # Observability
        "manage_secrets",           # Security
        "rollback_deployment",      # Emergency recovery
    ]
```

**Outputs**:
- `.github/workflows/*.yml` - CI/CD definitions
- `docker-compose.yml` - Container configs
- `infrastructure/*.tf` - Terraform configs
- `monitoring/` - Dashboards and alerts

### 5.8 Reviewer Agent

**Profile**: Code quality expert who ensures standards are met.

| Attribute | Value |
|-----------|-------|
| **Primary Goal** | Maintain code quality and standards |
| **Input** | Code changes, Coding standards |
| **Output** | Review comments, Approval/rejection |
| **Interacts With** | Engineer, Architect |

**Actions**:
```python
class ReviewerAgent(SCRUMRole):
    actions = [
        "analyze_code_changes",     # Understand the change
        "check_coding_standards",   # Style compliance
        "check_security",           # Security vulnerabilities
        "check_performance",        # Performance issues
        "provide_feedback",         # Constructive comments
        "approve_or_reject",        # Final decision
    ]
```

---

## 6. SCRUM Process Flows

### 6.1 Sprint Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SPRINT LIFECYCLE                                 │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐ │
│  │   PLANNING   │──▶│  EXECUTION   │──▶│    REVIEW    │──▶│  RETRO   │ │
│  │  (Day 1)     │   │  (Days 2-N)  │   │  (Last Day)  │   │(Last Day)│ │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────┘ │
│         │                  │                  │                  │      │
│         ▼                  ▼                  ▼                  ▼      │
│  • Select stories   • Daily standups   • Demo work        • What worked │
│  • Estimate tasks   • Task updates     • Stakeholder      • What didn't │
│  • Assign work      • Code/test/fix      feedback         • Actions     │
│  • Set sprint goal  • Resolve blockers • Accept/reject                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Sprint Planning Flow

```
START Sprint Planning
       │
       ▼
┌──────────────────────────────────────┐
│ ProductOwner presents prioritized    │
│ backlog items for the sprint         │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ Team discusses and estimates         │
│ each item (story points)             │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ Team commits to sprint backlog       │
│ based on velocity                    │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ [HYBRID/INTERACTIVE MODE]            │
│ Human approves sprint plan           │
│ ⏸️ Wait for approval                 │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ Sprint starts                        │
│ Tasks moved to Kanban board          │
│ Broadcast: SPRINT_STARTED            │
└──────────────────────────────────────┘
```

### 6.3 Daily Standup Flow

```
START Daily Standup (automated daily or on-demand)
       │
       ▼
┌──────────────────────────────────────┐
│ ScrumMaster gathers agent status     │
│ • What did you complete?             │
│ • What will you work on?             │
│ • Any blockers?                      │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ Compile standup report               │
│ • Progress summary                   │
│ • Blockers list                      │
│ • Burndown update                    │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ [If blockers detected]               │
│ Escalate to human OR                 │
│ Attempt auto-resolution              │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ Broadcast: DAILY_STANDUP_COMPLETE    │
│ Update dashboard metrics             │
└──────────────────────────────────────┘
```

### 6.4 Task Execution Flow

```
START Task Execution
       │
       ▼
┌──────────────────────────────────────┐
│ Agent picks task from TODO           │
│ Broadcast: TASK_STARTED              │
│ Move task to IN_PROGRESS             │
└────────────────┬─────────────────────┘
                 ▼
┌──────────────────────────────────────┐
│ Agent works on task                  │
│ • Periodic status updates            │
│ • Artifacts created logged           │
│ • Intermediate saves                 │
└────────────────┬─────────────────────┘
                 ▼
       ┌─────────┴─────────┐
       │ Task complete?    │
       └─────────┬─────────┘
          No │         │ Yes
             ▼         ▼
      ┌──────────┐  ┌──────────────────────────┐
      │ Continue │  │ Move to REVIEW           │
      │ working  │  │ Broadcast: TASK_COMPLETED│
      └──────────┘  └────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │ [HYBRID/INTERACTIVE]     │
                    │ Wait for review approval │
                    └────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │ Move to DONE             │
                    │ Broadcast: TASK_VERIFIED │
                    └──────────────────────────┘
```

---

## 7. Human-AI Interaction

### 7.1 Interaction Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HUMAN-AI INTERACTION TYPES                            │
├─────────────────┬───────────────────────────────────────────────────────┤
│  APPROVAL       │ AI pauses and waits for human to approve/reject       │
│                 │ Examples: PRD approval, Deployment approval           │
├─────────────────┼───────────────────────────────────────────────────────┤
│  FEEDBACK       │ AI requests input to clarify requirements             │
│                 │ Examples: "Should login support SSO?"                 │
├─────────────────┼───────────────────────────────────────────────────────┤
│  INTERVENTION   │ Human proactively changes direction                   │
│                 │ Examples: "Stop current task", "Reprioritize"         │
├─────────────────┼───────────────────────────────────────────────────────┤
│  COLLABORATION  │ Human and AI work together on a task                  │
│                 │ Examples: Pair programming, Design review             │
├─────────────────┼───────────────────────────────────────────────────────┤
│  OVERRIDE       │ Human overrides AI decision                           │
│                 │ Examples: "Use REST instead of GraphQL"               │
├─────────────────┼───────────────────────────────────────────────────────┤
│  MONITORING     │ Human observes without intervening                    │
│                 │ Examples: Watching activity feed                      │
└─────────────────┴───────────────────────────────────────────────────────┘
```

### 7.2 Approval Workflow

```python
class ApprovalRequest:
    id: str
    type: ApprovalType  # PRD, ARCHITECTURE, CODE, DEPLOYMENT
    agent: str          # Requesting agent
    artifact: str       # What needs approval
    context: str        # Why approval is needed
    options: List[str]  # e.g., ["Approve", "Reject", "Request Changes"]
    deadline: datetime  # Auto-proceed after this
    status: str         # PENDING, APPROVED, REJECTED, EXPIRED
```

**UI Flow**:
```
┌─────────────────────────────────────────────────────────────────────┐
│                    APPROVAL REQUEST                                  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ 🔔 ProductOwner Agent requests approval                       │  │
│  │                                                                │  │
│  │ Artifact: Product Requirements Document                       │  │
│  │                                                                │  │
│  │ [View PRD]                                                     │  │
│  │                                                                │  │
│  │ Deadline: 2h 30m remaining (auto-approve if no response)      │  │
│  │                                                                │  │
│  │ ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │  │
│  │ │ ✅ Approve   │  │ ❌ Reject    │  │ 📝 Request Changes   │ │  │
│  │ └──────────────┘  └──────────────┘  └───────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Knowledge Input from Humans

Humans can contribute knowledge that AI agents use:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE INPUT TYPES                             │
├─────────────────┬───────────────────────────────────────────────────┤
│  DOCUMENTS      │ Upload specifications, designs, standards         │
│                 │ Formats: PDF, MD, DOCX, TXT                       │
├─────────────────┼───────────────────────────────────────────────────┤
│  CODE SAMPLES   │ Reference implementations, patterns               │
│                 │ Formats: Any code file                            │
├─────────────────┼───────────────────────────────────────────────────┤
│  CONTEXT        │ Business rules, constraints, preferences          │
│                 │ Via chat or structured forms                      │
├─────────────────┼───────────────────────────────────────────────────┤
│  FEEDBACK       │ Corrections, improvements, guidance               │
│                 │ On AI-generated content                           │
└─────────────────┴───────────────────────────────────────────────────┘
```

---

## 8. Event System & Logging

### 8.1 Event Types

```python
class EventType(Enum):
    # Project Events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_COMPLETED = "project_completed"
    PROJECT_ARCHIVED = "project_archived"
    
    # Sprint Events
    SPRINT_PLANNED = "sprint_planned"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    
    # Task Events
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_VERIFIED = "task_verified"
    TASK_BLOCKED = "task_blocked"
    
    # Agent Events
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTING = "agent_acting"
    AGENT_WAITING = "agent_waiting"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Human Events
    HUMAN_APPROVAL_REQUESTED = "human_approval_requested"
    HUMAN_APPROVAL_RECEIVED = "human_approval_received"
    HUMAN_INPUT_RECEIVED = "human_input_received"
    HUMAN_INTERVENTION = "human_intervention"
    
    # Artifact Events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    
    # System Events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
```

### 8.2 Event Structure

```python
class Event:
    id: str                     # Unique event ID
    type: EventType             # Event classification
    timestamp: datetime         # When it occurred
    project_id: str             # Related project
    sprint_id: Optional[str]    # Related sprint
    task_id: Optional[str]      # Related task
    agent_id: Optional[str]     # Acting agent
    user_id: Optional[str]      # Involved human
    payload: Dict[str, Any]     # Event-specific data
    metadata: Dict[str, Any]    # Additional context
```

### 8.3 Event Broadcasting

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EVENT FLOW                                        │
│                                                                          │
│  Agent Action                                                            │
│       │                                                                  │
│       ▼                                                                  │
│  ┌───────────────────┐                                                   │
│  │ Event Created     │                                                   │
│  └─────────┬─────────┘                                                   │
│            │                                                             │
│            ├──────────────────────┬───────────────────┐                 │
│            ▼                      ▼                   ▼                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐       │
│  │ Persist to Log  │   │ WebSocket       │   │ Update State    │       │
│  │ (file/DB)       │   │ Broadcast       │   │ (project/task)  │       │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘       │
│                                │                                        │
│                                ▼                                        │
│                        ┌─────────────────┐                              │
│                        │ Dashboard UI    │                              │
│                        │ Updates         │                              │
│                        └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Logging Levels

| Level | Description | Example |
|-------|-------------|---------|
| DEBUG | Detailed internal state | "Parsing user story #123" |
| INFO | Normal operations | "Task moved to IN_PROGRESS" |
| WARNING | Potential issues | "API rate limit approaching" |
| ERROR | Failures requiring attention | "Code compilation failed" |
| CRITICAL | System-level failures | "Database connection lost" |

### 8.5 Log Storage

```
workspace/
└── logs/
    ├── events/
    │   ├── 2026-01-12.jsonl     # Daily event log
    │   └── ...
    ├── agents/
    │   ├── product_owner.log    # Agent-specific logs
    │   ├── engineer.log
    │   └── ...
    ├── system/
    │   ├── error.log            # Error tracking
    │   └── audit.log            # Security audit
    └── metrics/
        └── performance.jsonl     # Performance data
```

---

## 9. Knowledge Management

### 9.1 Knowledge Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE CLASSIFICATION                             │
├─────────────────────┬───────────────────────────────────────────────────┤
│  INPUT KNOWLEDGE    │ Provided by humans before/during project          │
│  (Human → AI)       │ • Requirements documents                          │
│                     │ • Design guidelines                               │
│                     │ • Code standards                                  │
│                     │ • Business rules                                  │
├─────────────────────┼───────────────────────────────────────────────────┤
│  GENERATED KNOWLEDGE│ Created by AI agents during execution             │
│  (AI → Human)       │ • PRD documents                                   │
│                     │ • Architecture designs                            │
│                     │ • Source code                                     │
│                     │ • Test reports                                    │
├─────────────────────┼───────────────────────────────────────────────────┤
│  SHARED KNOWLEDGE   │ Collaborative refinement                          │
│  (Human ↔ AI)       │ • Reviewed documents                              │
│                     │ • Approved designs                                │
│                     │ • Feedback-enhanced content                       │
├─────────────────────┼───────────────────────────────────────────────────┤
│  SYSTEM KNOWLEDGE   │ Learned patterns and templates                    │
│  (Persistent)       │ • Best practices                                  │
│                     │ • Reusable components                             │
│                     │ • Historical decisions                            │
└─────────────────────┴───────────────────────────────────────────────────┘
```

### 9.2 Knowledge Directory Structure

```
workspace/{project_id}/
├── input/                     # Human-provided knowledge
│   ├── requirements/          # Input documents
│   ├── references/            # Reference materials
│   ├── constraints/           # Rules and limitations
│   └── feedback/              # Human corrections
│
├── generated/                 # AI-created artifacts
│   ├── docs/
│   │   ├── prd.md
│   │   ├── architecture.md
│   │   ├── api_spec.yaml
│   │   └── user_guide.md
│   ├── src/                   # Source code
│   ├── tests/                 # Test files
│   └── reports/               # Generated reports
│
├── shared/                    # Collaborative artifacts
│   ├── approved/              # Human-approved versions
│   └── revisions/             # Version history
│
└── metadata/
    ├── index.json             # Content catalog
    ├── versions.json          # Version tracking
    └── permissions.json       # Access control
```

### 9.3 Knowledge Operations

```python
class KnowledgeManager:
    """Manages all project knowledge"""
    
    async def upload(self, file: File, category: str) -> KnowledgeItem
    async def download(self, item_id: str) -> bytes
    async def search(self, query: str) -> List[KnowledgeItem]
    async def catalog(self, project_id: str) -> List[KnowledgeItem]
    async def share_with_agent(self, item_id: str, agent: str) -> None
    async def get_agent_context(self, agent: str) -> List[KnowledgeItem]
```

---

## 10. Project Resources

### 10.1 Resource Types

| Resource | Description | Created By |
|----------|-------------|------------|
| Documents | PRD, specs, guides | ProductOwner, Architect |
| Source Code | Implementation files | Engineer |
| Tests | Test cases and results | QA Engineer |
| Configs | Configuration files | DevOps |
| Artifacts | Build outputs | CI/CD |
| Reports | Status, quality, metrics | All agents |
| Media | Diagrams, screenshots | Various |

### 10.2 Resource Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     RESOURCE LIFECYCLE                                   │
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐│
│  │ CREATED  │──▶│ REVIEWED │──▶│ APPROVED │──▶│ PUBLISHED│──▶│ARCHIVED││
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘│
│       │              │              │              │              │     │
│       ▼              ▼              ▼              ▼              ▼     │
│   Generated      Feedback       Locked for    Made available  Historical│
│   by agent       from human     production    to all          reference │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Download/Upload Interface

```python
class ResourceManager:
    """Manages project resources"""
    
    # Upload (Human → System)
    async def upload_document(
        self, 
        file: bytes, 
        filename: str,
        category: str,
        metadata: Dict
    ) -> ResourceId
    
    # Download (System → Human)
    async def download_resource(
        self, 
        resource_id: str
    ) -> Tuple[bytes, str, Dict]
    
    # List resources
    async def list_resources(
        self, 
        project_id: str,
        category: Optional[str] = None
    ) -> List[Resource]
    
    # Export project
    async def export_project(
        self, 
        project_id: str, 
        format: str = "zip"
    ) -> bytes
```

---

## 11. State Persistence

### 11.1 What Gets Persisted

| Entity | Storage | Frequency |
|--------|---------|-----------|
| Project | JSON file or DB | On every change |
| Sprint | JSON file or DB | On every change |
| Task | JSON file or DB | On every status change |
| Backlog | JSON file | On priority change |
| Agent State | JSON file | Periodic (every 30s) |
| Events | Append-only log | Immediately |
| Knowledge | File system | On creation/update |

### 11.2 Storage Structure

```
data/
├── projects/
│   └── {project_id}/
│       ├── project.json         # Project metadata
│       ├── sprints/
│       │   └── {sprint_id}.json
│       ├── tasks/
│       │   └── {task_id}.json
│       ├── backlog.json         # Product backlog
│       ├── board.json           # Kanban state
│       └── agents/
│           └── {agent_name}.json
│
├── events/
│   └── {date}.jsonl             # Append-only event log
│
└── global/
    ├── templates/               # Reusable templates
    └── settings.json            # System configuration
```

### 11.3 State Recovery

```python
class StateManager:
    """Manages persistent state"""
    
    async def save_project(self, project: Project) -> None
    async def load_project(self, project_id: str) -> Optional[Project]
    async def list_projects(self) -> List[ProjectSummary]
    
    async def save_sprint(self, sprint: Sprint) -> None
    async def load_sprint(self, sprint_id: str) -> Optional[Sprint]
    
    async def save_task(self, task: Task) -> None
    async def load_task(self, task_id: str) -> Optional[Task]
    
    async def recover_from_crash(self, project_id: str) -> RecoveryResult
```

---

## 12. API Specifications

### 12.1 REST API Endpoints

#### Project Management
```
POST   /v1/projects                      # Create project
GET    /v1/projects                      # List projects
GET    /v1/projects/{id}                 # Get project
PUT    /v1/projects/{id}                 # Update project
DELETE /v1/projects/{id}                 # Archive project

POST   /v1/projects/{id}/start           # Start execution
POST   /v1/projects/{id}/pause           # Pause execution
POST   /v1/projects/{id}/resume          # Resume execution
POST   /v1/projects/{id}/stop            # Stop execution
```

#### Sprint Management
```
GET    /v1/projects/{id}/sprints         # List sprints
POST   /v1/projects/{id}/sprints         # Create sprint
GET    /v1/sprints/{id}                  # Get sprint
PUT    /v1/sprints/{id}                  # Update sprint
POST   /v1/sprints/{id}/start            # Start sprint
POST   /v1/sprints/{id}/complete         # Complete sprint
```

#### Task Management
```
GET    /v1/projects/{id}/backlog         # Get backlog
POST   /v1/projects/{id}/backlog         # Add to backlog
GET    /v1/projects/{id}/board           # Get Kanban board
POST   /v1/tasks/{id}/move               # Move task on board
PUT    /v1/tasks/{id}                    # Update task
```

#### Agent Management
```
GET    /v1/projects/{id}/agents          # List agents
GET    /v1/agents/{name}/status          # Get agent status
POST   /v1/agents/{name}/command         # Send command to agent
```

#### Human Interaction
```
GET    /v1/approvals/pending             # List pending approvals
POST   /v1/approvals/{id}/approve        # Approve request
POST   /v1/approvals/{id}/reject         # Reject request
POST   /v1/approvals/{id}/feedback       # Provide feedback
```

#### Knowledge Management
```
GET    /v1/projects/{id}/knowledge       # List knowledge items
POST   /v1/projects/{id}/knowledge       # Upload knowledge
GET    /v1/knowledge/{id}                # Download knowledge
DELETE /v1/knowledge/{id}                # Remove knowledge
GET    /v1/projects/{id}/export          # Export project
```

### 12.2 WebSocket Events

```
WS /v1/stream/events                     # All events stream
WS /v1/projects/{id}/events              # Project-specific events
WS /v1/agents/{name}/logs                # Agent-specific logs
```

**Event Message Format**:
```json
{
  "type": "task_updated",
  "timestamp": "2026-01-12T12:00:00Z",
  "project_id": "proj_abc123",
  "payload": {
    "task_id": "task_456",
    "from_status": "in_progress",
    "to_status": "review"
  }
}
```

---

## 13. Dashboard Integration

### 13.1 Dashboard Views

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD LAYOUT                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Navigation: Projects | New Project | Knowledge | Settings           │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Project: {name}                                    [Mode: Hybrid ▼] │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│ ┌──────────────────────┐  ┌──────────────────────────────────────────┐ │
│ │ METRICS              │  │ SPRINT PROGRESS                          │ │
│ │ ├── Tasks: 12/20     │  │ █████████████░░░░░░░░ 65%                │ │
│ │ ├── Velocity: 32     │  │ Day 5 of 10 • 8 stories completed        │ │
│ │ └── Blockers: 1      │  └──────────────────────────────────────────┘ │
│ └──────────────────────┘                                                │
│                                                                          │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ KANBAN BOARD                                                         ││
│ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         ││
│ │ │ TODO       │ │ IN PROGRESS│ │ REVIEW     │ │ DONE       │         ││
│ │ │ ┌────────┐ │ │ ┌────────┐ │ │ ┌────────┐ │ │ ┌────────┐ │         ││
│ │ │ │ Task 1 │ │ │ │ Task 3 │ │ │ │ Task 5 │ │ │ │ Task 7 │ │         ││
│ │ │ └────────┘ │ │ │ 🤖 Engr │ │ │ │ ⏳ Wait │ │ │ │ ✅      │ │         ││
│ │ │ ┌────────┐ │ │ └────────┘ │ │ └────────┘ │ │ └────────┘ │         ││
│ │ │ │ Task 2 │ │ │ ┌────────┐ │ │            │ │ ┌────────┐ │         ││
│ │ │ └────────┘ │ │ │ Task 4 │ │ │            │ │ │ Task 8 │ │         ││
│ │ │            │ │ │ 🤖 QA   │ │ │            │ │ │ ✅      │ │         ││
│ │ │            │ │ └────────┘ │ │            │ │ └────────┘ │         ││
│ │ └────────────┘ └────────────┘ └────────────┘ └────────────┘         ││
│ └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│ ┌──────────────────────┐  ┌──────────────────────────────────────────┐ │
│ │ AGENT ACTIVITY       │  │ PENDING APPROVALS                        │ │
│ │ ┌──────────────────┐ │  │ ┌──────────────────────────────────────┐ │ │
│ │ │ 🤖 Engineer      │ │  │ │ PRD requires approval      [Review] │ │ │
│ │ │    Writing code  │ │  │ └──────────────────────────────────────┘ │ │
│ │ │    Task: Login   │ │  │                                          │ │
│ │ └──────────────────┘ │  │                                          │ │
│ │ ┌──────────────────┐ │  │                                          │ │
│ │ │ 🤖 QA Engineer   │ │  │                                          │ │
│ │ │    Testing       │ │  │                                          │ │
│ │ │    Task: Auth    │ │  │                                          │ │
│ │ └──────────────────┘ │  │                                          │ │
│ └──────────────────────┘  └──────────────────────────────────────────┘ │
│                                                                          │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ ACTIVITY LOG                                           [View All →] ││
│ │ 12:05:23 | Engineer started task "Implement Login"                  ││
│ │ 12:03:45 | QA Engineer completed task "Test Authentication"         ││
│ │ 12:01:12 | ProductOwner created user story "Password Reset"         ││
│ └──────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Real-Time Updates

All dashboard components subscribe to WebSocket events:

| Component | Event Types | Update Action |
|-----------|-------------|---------------|
| Metrics | task_*, sprint_* | Recalculate counts |
| Sprint Progress | task_completed | Update progress bar |
| Kanban Board | task_moved | Move card visually |
| Agent Activity | agent_* | Update status cards |
| Activity Log | all events | Prepend to log |
| Approvals | approval_* | Add/remove items |

---

## 14. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Design document approval ← **YOU ARE HERE**
- [ ] Set up persistence layer (JSON files initially)
- [ ] Create base SCRUMRole class
- [ ] Implement event broadcasting system
- [ ] Create state management utilities

### Phase 2: Core Agents (Week 3-4)
- [ ] Implement ProductOwnerAgent
- [ ] Implement ScrumMasterAgent
- [ ] Implement ArchitectAgent
- [ ] Implement EngineerAgent
- [ ] Implement QAEngineerAgent
- [ ] Implement DevOpsAgent

### Phase 3: SCRUM Ceremonies (Week 5)
- [ ] Sprint Planning automation
- [ ] Daily Standup automation
- [ ] Sprint Review facilitation
- [ ] Retrospective generation

### Phase 4: Human Interaction (Week 6)
- [ ] Approval workflow implementation
- [ ] Feedback collection system
- [ ] Knowledge upload/download
- [ ] Mode switching (auto/hybrid/interactive)

### Phase 5: Dashboard Integration (Week 7)
- [ ] Real-time WebSocket updates on all UI components
- [ ] Agent activity visualization
- [ ] Knowledge management UI
- [ ] Approval workflow UI

### Phase 6: Testing & Polish (Week 8)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation finalization
- [ ] User acceptance testing

---

## Appendix A: Configuration Schema

```yaml
# config/scrum_agents.yaml

project:
  default_sprint_duration_days: 14
  max_concurrent_agents: 5
  workspace_path: "./workspace"
  
execution:
  default_mode: "hybrid"  # autonomous | hybrid | interactive
  approval_timeout_minutes: 60
  auto_retry_on_failure: true
  max_retries: 3
  
agents:
  product_owner:
    enabled: true
    llm_model: "gpt-4"
    temperature: 0.7
  scrum_master:
    enabled: true
    daily_standup_cron: "0 9 * * *"
  architect:
    enabled: true
    auto_diagram: true
  engineer:
    enabled: true
    code_review_required: true
  qa_engineer:
    enabled: true
    auto_test: true
  devops:
    enabled: true
    auto_deploy: false  # Requires approval
    
persistence:
  backend: "file"  # file | sqlite | postgres
  events_retention_days: 90
  
broadcasting:
  websocket_enabled: true
  heartbeat_interval_seconds: 30
  
logging:
  level: "INFO"
  format: "json"
  output: "file"  # console | file | both
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Agent** | AI entity that performs specific SCRUM role |
| **Artifact** | Deliverable produced by agents (code, docs, etc.) |
| **Backlog** | Prioritized list of work items |
| **Broadcast** | Real-time event notification to all subscribers |
| **Ceremony** | SCRUM ritual (planning, standup, review, retro) |
| **Hybrid Mode** | Execution with human approval checkpoints |
| **Knowledge** | Documents and context shared between humans and AI |
| **Sprint** | Time-boxed iteration of work |
| **Task** | Smallest unit of work, assignable to agents |
| **Velocity** | Measure of work completed per sprint |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | AI Assistant | Initial comprehensive design |

---

**Status**: DRAFT - Pending Review
**Next Step**: Human approval before implementation
