# MetaGPT-Pro SCRUM Dashboard - Implementation Plan

## Overview
Complete implementation of the SCRUM Dashboard with Interactive/Autonomous modes, real-time updates, file management, and iterative development workflow.

---

## Phase 1: Core Infrastructure (Priority: HIGH)

### Task 1.1: Persist Agent Outputs to Files
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/roles/scrum/*.py` - Add file saving logic
- `metagpt/project/workspace.py` - Create workspace manager (new file)

**Details**:
- Create a `WorkspaceManager` class to handle file operations
- Save PRD documents to `workspace/{project_id}/docs/PRD.md`
- Save system designs to `workspace/{project_id}/docs/SYSTEM_DESIGN.md`
- Save code files to `workspace/{project_id}/src/`
- Save test files to `workspace/{project_id}/tests/`
- Save sprint/backlog data to `workspace/{project_id}/project.json`

### Task 1.2: Add Execution Mode Support
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/api/orchestrator.py` - Add mode handling
- `metagpt/project/project_manager.py` - Modify existing or create new
- `metagpt/api/routes/project.py` - Add mode endpoints

**Details**:
- Add `ExecutionMode` enum: `INTERACTIVE`, `AUTONOMOUS`
- Store mode in project configuration
- Implement pause points for Interactive mode
- Implement automatic progression for Autonomous mode

---

## Phase 2: Frontend Restructuring (Priority: HIGH)

### Task 2.1: Redesign New Project Page
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html` - Restructure HTML
- `metagpt/webapp/styles.css` - Update styles
- `metagpt/webapp/app.bundle.js` - Update JavaScript

**Changes**:
- Remove "Agent Activity" and "Live Status" widgets from New Project page
- Show only:
  - Project description input
  - Mode selection (Interactive / Autonomous)
  - AI conversation for requirements
  - Formatted PRD preview with "Accept" button
- After acceptance, redirect to Live Monitoring page

### Task 2.2: Create Live Monitoring Page
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html` - Add new view
- `metagpt/webapp/styles.css` - Add styles
- `metagpt/webapp/app.bundle.js` - Add page logic

**Features**:
- Agent Activity Feed (moved from New Project)
- Live Status Panel (moved from New Project)
- Current Sprint Progress
- Real-time task updates
- Agent collaboration visualization

### Task 2.3: Update Dashboard Page
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html`
- `metagpt/webapp/app.bundle.js`

**Changes**:
- Connect metrics to real project data
- Show accurate Sprint Progress, Points Completed, etc.
- Add Quick Actions that trigger real operations
- Show recent activity summary

### Task 2.4: Update Backlog Page
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html`
- `metagpt/webapp/app.bundle.js`
- `metagpt/api/routes/project.py` - Ensure API returns proper data

**Features**:
- Show all user stories with acceptance criteria
- Priority ordering
- Status indicators
- Interactive mode: Allow user to approve/modify backlog

### Task 2.5: Update Kanban Board
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html`
- `metagpt/webapp/app.bundle.js`

**Features**:
- Drag-and-drop support
- Real-time updates via WebSocket
- Task cards with agent assignments
- Column filtering by sprint

### Task 2.6: Update Sprints Page
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html`
- `metagpt/webapp/app.bundle.js`

**Features**:
- Sprint list with status
- Current sprint details
- Sprint goals and completion %
- Burndown chart (if time permits)

---

## Phase 3: File Explorer & Artifacts (Priority: MEDIUM)

### Task 3.1: Create Project Artifacts Page
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html` - Add Artifacts view
- `metagpt/webapp/styles.css` - File explorer styles
- `metagpt/webapp/app.bundle.js` - File explorer logic
- `metagpt/api/routes/files.py` - Ensure file list API works

**Features**:
- Tree view file explorer
- File preview (code highlighting for source files)
- Download individual files
- Download entire project as ZIP
- Show file generation timestamps

---

## Phase 4: Project Completion & Iteration (Priority: MEDIUM)

### Task 4.1: Add Project Review Flow
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/webapp/index.html` - Add Review section
- `metagpt/api/routes/project.py` - Add review endpoints

**Features**:
- Project completion summary
- User comment submission
- Change request creation
- Bug report creation
- Enhancement request creation
- "Project Complete" action

### Task 4.2: Implement Iteration Workflow
**Status**: 🔴 Not Started
**Files to Modify**:
- `metagpt/api/orchestrator.py` - Add iteration handling
- `metagpt/api/routes/project.py` - Add iteration endpoints

**Features**:
- Create new sprint from change requests
- Assign tasks to agents
- Track iteration history
- Support maintenance mode

---

## Phase 5: Real-time Event System (Priority: HIGH)

### Task 5.1: Enhance Event Broadcasting
**Status**: 🟡 Partially Done
**Files to Modify**:
- `metagpt/project/event_system.py` - Already done
- `metagpt/webapp/app.bundle.js` - Add listeners for all pages

**Features**:
- Events update all pages, not just Activity Feed
- Backlog page updates when stories added
- Kanban updates when tasks move
- Sprint page updates on completion
- Dashboard metrics update in real-time

---

## Implementation Order

### Sprint 1 (Current Priority)
1. ✅ Task 1.1: Persist Agent Outputs to Files
2. ✅ Task 2.1: Redesign New Project Page
3. ✅ Task 2.2: Create Live Monitoring Page
4. ✅ Task 5.1: Enhance Event Broadcasting

### Sprint 2
5. Task 2.3: Update Dashboard Page
6. Task 2.4: Update Backlog Page
7. Task 2.5: Update Kanban Board
8. Task 2.6: Update Sprints Page

### Sprint 3
9. Task 1.2: Add Execution Mode Support
10. Task 3.1: Create Project Artifacts Page

### Sprint 4
11. Task 4.1: Add Project Review Flow
12. Task 4.2: Implement Iteration Workflow

---

## Current Progress Tracker

| Phase | Task | Status | Notes |
|-------|------|--------|-------|
| 1 | 1.1 Persist Outputs | ✅ | WorkspaceManager + Agent integrations complete |
| 1 | 1.2 Execution Modes | 🟡 | Frontend ready, backend API in progress |
| 2 | 2.1 New Project Page | ✅ | Simplified with mode selection |
| 2 | 2.2 Live Monitoring | ✅ | Agent Activity + Live Status + Sprint Progress |
| 2 | 2.3 Dashboard | ✅ | Connected to real APIs |
| 2 | 2.4 Backlog | ✅ | Real data + approval button ready |
| 2 | 2.5 Kanban Board | ✅ | Drag-drop + real-time updates |
| 2 | 2.6 Sprints | ✅ | Real data + approval button ready |
| 3 | 3.1 Artifacts Page | ✅ | File explorer + download ZIP |
| 4 | 4.1 Review Flow | ✅ | Modal with feedback options |
| 4 | 4.2 Iteration | 🔴 | Backend iteration endpoints needed |
| 5 | 5.1 Events | ✅ | Enhanced event handling for all pages |

---

## Technical Notes

### Execution Modes

**Interactive Mode Flow**:
1. User submits requirements → Show PRD → User approves
2. Generate Backlog → Show to user → User approves
3. Generate Sprint Plan → Show tasks → User approves
4. Agents start working → User monitors
5. Sprint complete → Show results → User reviews
6. Next sprint or project complete

**Autonomous Mode Flow**:
1. User submits requirements → Auto-approve PRD
2. Auto-generate and approve backlog
3. Auto-plan sprints
4. Agents work continuously
5. Project completes → User reviews final output
6. User submits feedback → New iteration or close

### File Structure
```
workspace/
└── {project_id}/
    ├── project.json          # Project metadata, sprints, backlog
    ├── docs/
    │   ├── PRD.md
    │   ├── SYSTEM_DESIGN.md
    │   └── API_SPEC.md
    ├── src/
    │   ├── main.py
    │   └── ...
    ├── tests/
    │   ├── test_main.py
    │   └── ...
    └── artifacts/
        ├── sprint_1_review.md
        └── ...
```
