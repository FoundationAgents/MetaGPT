/**
 * MetaGPT SCRUM Dashboard - JavaScript Application
 */

// Configuration
const API_BASE = '/v1';
let currentProjectId = 'demo_project';
let ws = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initProjectSelector();
    initWebSocket();
    loadDashboardData();
});

// Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            // Update active nav
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Switch view
            const viewName = item.dataset.view;
            switchView(viewName);
        });
    });

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadDashboardData();
    });
}

function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    // Show selected view
    const view = document.getElementById(`${viewName}-view`);
    if (view) {
        view.classList.add('active');
        document.getElementById('page-title').textContent = capitalizeFirst(viewName);

        // Load view-specific data
        switch (viewName) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'backlog':
                loadBacklog();
                break;
            case 'board':
                loadBoard();
                break;
            case 'sprints':
                loadSprints();
                break;
        }
    }
}

// Project Selector
async function initProjectSelector() {
    const select = document.getElementById('project-select');

    // Load projects from API
    try {
        const projects = await apiGet('/project'); // Calls /v1/project

        if (projects && projects.length > 0) {
            select.innerHTML = '';
            projects.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = p.name || p.id;
                select.appendChild(option);
            });

            // Set current project to first one if default
            if (currentProjectId === 'demo_project' && projects[0].id) {
                currentProjectId = projects[0].id;
            }
            select.value = currentProjectId;
        }
    } catch (e) {
        console.error("Failed to load projects", e);
    }

    select.addEventListener('change', (e) => {
        currentProjectId = e.target.value;
        loadDashboardData();
        // Update WebSocket connection for new project
        if (ws) {
            ws.close();
            initWebSocket();
        }
    });
}

// WebSocket for real-time updates
function initWebSocket() {
    const statusEl = document.getElementById('connection-status');

    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/v1/project/${currentProjectId}/board/stream`);

        ws.onopen = () => {
            statusEl.innerHTML = '<span class="status-dot connected"></span><span>Connected</span>';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };

        ws.onclose = () => {
            statusEl.innerHTML = '<span class="status-dot"></span><span>Disconnected</span>';
            // Reconnect after 3 seconds
            setTimeout(initWebSocket, 3000);
        };

        ws.onerror = () => {
            statusEl.innerHTML = '<span class="status-dot"></span><span>Offline</span>';
        };
    } catch (e) {
        statusEl.innerHTML = '<span class="status-dot"></span><span>Offline</span>';
    }
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'initial_state':
        case 'board_update':
            updateBoardFromData(data.board);
            break;
        case 'task_moved':
            loadBoard();
            loadDashboardData();
            break;
    }
}

// API Functions
async function apiGet(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error('API Error');
        return await response.json();
    } catch (e) {
        console.error('API Get Error:', e);
        return null;
    }
}

async function apiPost(endpoint, body) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error: ${endpoint}`, error);
        return null;
    }
}

// Dashboard
async function loadDashboardData() {
    showLoading('Loading dashboard...');

    // Load metrics
    const metrics = await apiGet(`/project/${currentProjectId}/metrics`);
    if (metrics) {
        updateMetrics(metrics);
    }

    // Load current sprint
    const sprintsData = await apiGet(`/project/${currentProjectId}/sprints`);
    if (sprintsData && sprintsData.current_sprint) {
        updateSprintInfo(sprintsData);
    }

    hideLoading();
}

function updateMetrics(metrics) {
    document.getElementById('progress-percent').textContent = `${metrics.progress_percent || 0}%`;
    document.getElementById('progress-bar').style.width = `${metrics.progress_percent || 0}%`;
    document.getElementById('points-completed').textContent = metrics.points_completed || 0;
    document.getElementById('points-remaining').textContent = metrics.points_remaining || 0;
    document.getElementById('blocked-count').textContent = metrics.blocked_count || 0;
}

function updateSprintInfo(data) {
    document.getElementById('sprint-badge').textContent = `Sprint ${data.current_sprint}`;

    const goalsEl = document.getElementById('sprint-goals');
    if (data.sprints && data.sprints.length > 0) {
        const currentSprint = data.sprints.find(s => s.number === data.current_sprint);
        if (currentSprint && currentSprint.goals && currentSprint.goals.length > 0) {
            goalsEl.innerHTML = `
                <h4>Sprint Goals:</h4>
                <ul>
                    ${currentSprint.goals.map(g => `<li>${g}</li>`).join('')}
                </ul>
            `;
        }
    }
}

// Backlog
async function loadBacklog() {
    showLoading('Loading backlog...');

    const backlog = await apiGet(`/project/${currentProjectId}/backlog`);
    if (backlog) {
        renderBacklog(backlog);
    }

    hideLoading();
}

async function addBacklogItem() {
    const titleInput = document.getElementById('new-item-input');
    const typeSelect = document.getElementById('new-item-type');
    const title = titleInput.value.trim();
    const type = typeSelect.value;

    if (!title) {
        alert('Please enter a title');
        return;
    }

    showLoading('Adding item...');

    try {
        let endpoint = `/project/${currentProjectId}/backlog/`;
        let body = {
            title: title,
            description: `Added via Dashboard at ${new Date().toLocaleTimeString()}`,
            priority: "MEDIUM"
        };

        if (type === 'story') {
            endpoint += 'story';
        } else {
            endpoint += 'task';
            body.type = type; // 'bug' or 'task'
        }

        const res = await apiPost(endpoint, body);

        if (res) {
            titleInput.value = ''; // Clear input
            await loadBacklog(); // Reload list
        }
    } catch (e) {
        console.error("Failed to add backlog item", e);
        alert('Failed to add item: ' + e.message);
    } finally {
        hideLoading();
    }
}

// Make globally available
window.addBacklogItem = addBacklogItem;

function renderBacklog(backlog) {
    const container = document.getElementById('backlog-list');
    document.getElementById('backlog-points').textContent = `${backlog.total_points} points`;

    if (!backlog.stories || backlog.stories.length === 0) {
        container.innerHTML = '<p class="empty-state">No stories in backlog. Add requirements to begin.</p>';
        return;
    }

    container.innerHTML = backlog.stories.map(story => `
        <div class="story-card" data-id="${story.id}">
            <div class="story-priority ${story.priority || 'medium'}"></div>
            <div class="story-content">
                <div class="story-title">${story.title}</div>
                <div class="story-id">${story.id}</div>
            </div>
            <div class="story-points">${story.story_points || 0} pts</div>
        </div>
    `).join('');
}

// Kanban Board
async function loadBoard() {
    showLoading('Loading board...');

    const board = await apiGet(`/project/${currentProjectId}/board`);
    if (board) {
        renderBoard(board);
    }

    hideLoading();
}

function renderBoard(board) {
    renderColumn('todo-tasks', board.todo, 'todo-count');
    renderColumn('in-progress-tasks', board.in_progress, 'in-progress-count');
    renderColumn('review-tasks', board.review, 'review-count');
    renderColumn('done-tasks', board.done, 'done-count');
    renderColumn('blocked-tasks', board.blocked, 'blocked-tasks-count');
}

function renderColumn(containerId, tasks, countId) {
    const container = document.getElementById(containerId);
    const countEl = document.getElementById(countId);

    tasks = tasks || [];
    countEl.textContent = tasks.length;

    if (tasks.length === 0) {
        container.innerHTML = '<p class="empty-state">No tasks</p>';
        return;
    }

    container.innerHTML = tasks.map(task => `
        <div class="task-card" draggable="true" data-id="${task.id}">
            <div class="task-title">${task.title}</div>
            <div class="task-meta">
                <span>${task.id}</span>
                <span class="task-points">${task.story_points || 0}</span>
            </div>
        </div>
    `).join('');

    // Add drag events
    container.querySelectorAll('.task-card').forEach(card => {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });
}

function updateBoardFromData(boardData) {
    if (document.getElementById('board-view').classList.contains('active')) {
        renderBoard(boardData);
    }
}

// Drag and Drop
function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.setData('text/plain', e.target.dataset.id);
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

// Initialize drag-drop on columns
document.querySelectorAll('.column-tasks').forEach(column => {
    column.addEventListener('dragover', (e) => {
        e.preventDefault();
        column.style.background = 'rgba(88, 166, 255, 0.1)';
    });

    column.addEventListener('dragleave', () => {
        column.style.background = '';
    });

    column.addEventListener('drop', async (e) => {
        e.preventDefault();
        column.style.background = '';

        const taskId = e.dataTransfer.getData('text/plain');
        const newStatus = column.closest('.kanban-column').dataset.status;

        await moveTask(taskId, newStatus);
    });
});

async function moveTask(taskId, newStatus) {
    showLoading('Moving task...');

    const result = await apiPost(`/project/${currentProjectId}/task/move`, {
        task_id: taskId,
        new_status: newStatus
    });

    if (result && result.updated) {
        loadBoard();
        loadDashboardData();
    }

    hideLoading();
}

// Sprints
async function loadSprints() {
    showLoading('Loading sprints...');

    const data = await apiGet(`/project/${currentProjectId}/sprints`);
    if (data) {
        renderSprints(data);
    }

    hideLoading();
}

function renderSprints(data) {
    const container = document.getElementById('sprints-timeline');

    if (!data.sprints || data.sprints.length === 0) {
        container.innerHTML = '<p class="empty-state">No sprints created yet. Run Sprint Planning to create your first sprint.</p>';
        return;
    }

    container.innerHTML = data.sprints.map(sprint => `
        <div class="sprint-card">
            <div class="sprint-header">
                <span class="sprint-name">${sprint.name}</span>
                <span class="sprint-status ${sprint.number === data.current_sprint ? 'active' : 'completed'}">
                    ${sprint.number === data.current_sprint ? 'Active' : 'Completed'}
                </span>
            </div>
            <div class="sprint-progress-bar">
                <div class="sprint-progress-fill" style="width: ${sprint.progress_percent || 0}%"></div>
            </div>
            <div class="sprint-goals">
                <strong>Goals:</strong>
                <ul>
                    ${(sprint.goals || []).map(g => `<li>${g}</li>`).join('') || '<li>No goals defined</li>'}
                </ul>
            </div>
        </div>
    `).join('');
}

// Ceremonies
async function runCeremony(type) {
    showLoading(`Running ${type.replace('-', ' ')}...`);

    const result = await apiPost(`/scrum/${currentProjectId}/ceremony/${type}`, {
        sprint_number: 1,
        velocity: 20,
        sprint_duration: 7
    });

    hideLoading();

    if (result) {
        showCeremonyOutput(result);
    } else {
        showModal('Error', 'Failed to run ceremony. Please check if the backend is running.');
    }
}

function showCeremonyOutput(result) {
    const outputCard = document.getElementById('ceremony-output-card');
    const titleEl = document.getElementById('ceremony-output-title');
    const outputEl = document.getElementById('ceremony-output');

    titleEl.textContent = `${result.ceremony} - ${new Date(result.timestamp).toLocaleString()}`;
    outputEl.textContent = result.report;
    outputCard.style.display = 'block';

    // Switch to ceremonies view if not there
    switchView('ceremonies');

    // Scroll to output
    outputCard.scrollIntoView({ behavior: 'smooth' });
}

function closeCeremonyOutput() {
    document.getElementById('ceremony-output-card').style.display = 'none';
}

async function prioritizeBacklog() {
    showLoading('AI is prioritizing backlog...');

    const result = await apiPost(`/scrum/${currentProjectId}/backlog/prioritize`);

    hideLoading();

    if (result) {
        showModal('Backlog Prioritized', result.result);
        loadBacklog();
    }
}

// Modal
function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = `<p>${content}</p>`;
    document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

// Loading
function showLoading(text = 'Loading...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

// Utilities
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'modal-overlay') {
        closeModal();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// ============================================
// CHAT & REQUIREMENTS SUBMISSION
// ============================================

let currentConversationId = null;
let activityWebSocket = null;

// Send chat message to AI Product Manager
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    // Update status
    document.getElementById('chat-status').textContent = 'Thinking...';
    document.getElementById('chat-status').style.background = 'rgba(210, 153, 34, 0.15)';
    document.getElementById('chat-status').style.color = 'var(--accent-warning)';

    try {
        let response;

        if (!currentConversationId) {
            // Start new conversation
            response = await apiPost('/conversation/start', { initial_idea: message });
            if (response) {
                currentConversationId = response.conversation_id;
                addChatMessage(response.first_question, 'ai');
                // Show Skip button after first message
                document.getElementById('skip-btn').style.display = 'inline-flex';
            }
        } else {
            // Continue conversation
            response = await apiPost('/conversation/message', {
                conversation_id: currentConversationId,
                message: message
            });
            if (response) {
                addChatMessage(response.ai_response, 'ai');

                // Show approve button if ready
                if (response.requires_approval) {
                    document.getElementById('approve-btn').style.display = 'inline-flex';
                    document.getElementById('chat-status').textContent = 'Ready to Approve';
                    document.getElementById('chat-status').style.background = 'rgba(63, 185, 80, 0.15)';
                    document.getElementById('chat-status').style.color = 'var(--accent-success)';
                }
            }
        }

        if (!response || !response.requires_approval) {
            document.getElementById('chat-status').textContent = 'Active';
            document.getElementById('chat-status').style.background = 'rgba(88, 166, 255, 0.15)';
            document.getElementById('chat-status').style.color = 'var(--accent-primary)';
        }
    } catch (error) {
        console.error('Chat error:', error);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
        document.getElementById('chat-status').textContent = 'Error';
        alert('Chat Error: ' + error.message);
    }
}

// Skip questions and force approval
async function skipQuestionsAndApprove() {
    if (!currentConversationId) {
        showModal('Error', 'Please start a conversation first by describing your project.');
        return;
    }

    // Send a proceed message to trigger approval
    addChatMessage("Let's proceed with development based on what I've described.", 'user');

    showLoading('Processing requirements...');

    try {
        const response = await apiPost('/conversation/message', {
            conversation_id: currentConversationId,
            message: "Yes, let's start development. I'm ready to proceed."
        });

        if (response) {
            addChatMessage(response.ai_response, 'ai');
        }

        hideLoading();

        // Now approve
        document.getElementById('approve-btn').style.display = 'inline-flex';
        document.getElementById('skip-btn').style.display = 'none';

        addChatMessage('✅ Ready for approval! Click "Approve & Start Development" to begin.', 'ai');
    } catch (error) {
        hideLoading();
        console.error('Skip error:', error);
        // Still show approve button
        document.getElementById('approve-btn').style.display = 'inline-flex';
    }
}

function addChatMessage(text, sender) {
    const container = document.getElementById('chat-messages');
    const isUser = sender === 'user';

    const messageHtml = `
        <div class="chat-message ${sender}">
            <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
            <div class="message-content">
                <strong>${isUser ? 'You' : 'AI Product Manager'}</strong>
                <p>${text}</p>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', messageHtml);
    container.scrollTop = container.scrollHeight;
}

// Approve requirements and start development
async function approveRequirements() {
    if (!currentConversationId) {
        showModal('Error', 'No active conversation to approve.');
        return;
    }

    showLoading('Approving requirements and starting agents...');

    try {
        const result = await apiPost('/conversation/approve', {
            conversation_id: currentConversationId
        });

        if (result && result.project_id) {
            currentProjectId = result.project_id;

            // Update project selector
            const select = document.getElementById('project-select');
            const option = document.createElement('option');
            option.value = result.project_id;
            option.textContent = result.project_id;
            option.selected = true;
            select.appendChild(option);

            // Start agent activity stream
            startActivityStream();

            // Update UI
            document.getElementById('chat-actions').style.display = 'none';
            document.getElementById('agents-status').textContent = 'Running';
            document.getElementById('agents-status').style.background = 'rgba(63, 185, 80, 0.15)';
            document.getElementById('agents-status').style.color = 'var(--accent-success)';

            addChatMessage('✅ Requirements approved! AI agents are now working on your project. Watch the activity feed to monitor progress.', 'ai');

            hideLoading();
        }
    } catch (error) {
        hideLoading();
        showModal('Error', 'Failed to approve requirements. Please try again.');
    }
}

// ============================================
// AGENT ACTIVITY MONITORING
// ============================================

function startActivityStream() {
    const feedEl = document.getElementById('agent-activity-feed');
    feedEl.innerHTML = ''; // Clear empty state

    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        activityWebSocket = new WebSocket(`${protocol}//${window.location.host}/v1/stream/events`);

        activityWebSocket.onopen = () => {
            addActivityItem('System', 'Connected to activity stream', '🔌');
        };

        activityWebSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleActivityEvent(data);
        };

        activityWebSocket.onerror = () => {
            addActivityItem('System', 'Activity stream connection error', '⚠️');
        };

        activityWebSocket.onclose = () => {
            addActivityItem('System', 'Activity stream disconnected', '🔌');
        };
    } catch (e) {
        // Fallback: poll for status
        pollAgentStatus();
    }
}

function handleActivityEvent(data) {
    // Handle standard events
    switch (data.type) {
        case 'connected':
            addActivityItem('System', data.message || 'Connected', '🔌');
            break;
        case 'pong':
            // Heartbeat response, ignore
            break;
        case 'agent_started':
            const startPayload = data.payload || {};
            addActivityItem(
                startPayload.name || startPayload.profile || 'Agent',
                startPayload.action || 'Started',
                getAgentIcon(startPayload.profile || 'Agent')
            );
            updateAgentStatus(startPayload.name || 'Agent', 'active', 'Starting...');
            break;
        case 'agent_thinking':
            const thinkPayload = data.payload || {};
            addActivityItem(
                thinkPayload.name || thinkPayload.profile || 'Agent',
                thinkPayload.action || 'Thinking...',
                '🤔'
            );
            updateAgentStatus(thinkPayload.name || 'Agent', 'thinking', thinkPayload.action || 'Analyzing...');
            break;
        case 'agent_acting':
            const actPayload = data.payload || {};
            const actionText = actPayload.action || actPayload.todo || 'Working';
            addActivityItem(
                actPayload.name || actPayload.profile || 'Agent',
                actionText,
                getAgentIcon(actPayload.profile || 'Agent')
            );
            updateAgentStatus(actPayload.name || 'Agent', 'active', actionText);

            // If message communication
            if (actPayload.message_to) {
                addActivityItem(
                    actPayload.name,
                    `→ ${actPayload.message_to}: ${actPayload.message_preview || 'message'}`,
                    '💬'
                );
            }
            if (actPayload.message_from) {
                addActivityItem(
                    actPayload.name,
                    `← From ${actPayload.message_from}: ${actPayload.message_preview || 'message'}`,
                    '📨'
                );
            }
            break;
        case 'agent_waiting':
            const waitPayload = data.payload || {};
            updateAgentStatus(waitPayload.name || 'Agent', 'idle', 'Waiting');
            break;
        case 'agent_completed':
            const completePayload = data.payload || {};
            addActivityItem(
                completePayload.name || completePayload.profile || 'Agent',
                completePayload.action || 'Completed',
                '✅'
            );
            updateAgentStatus(completePayload.name || 'Agent', 'idle', 'Done');
            break;
        case 'agent_error':
            const errorPayload = data.payload || {};
            addActivityItem(
                errorPayload.name || 'Agent',
                `Error: ${errorPayload.error || 'Unknown error'}`,
                '❌'
            );
            updateAgentStatus(errorPayload.name || 'Agent', 'error', 'Error');
            break;
        case 'task_started':
            const taskStartPayload = data.payload || {};
            addActivityItem(
                taskStartPayload.assigned_to || 'Agent',
                `📋 Started: ${taskStartPayload.task_title || taskStartPayload.task_id}`,
                '▶️'
            );
            break;
        case 'task_completed':
            const taskDonePayload = data.payload || {};
            addActivityItem(
                taskDonePayload.completed_by || 'Agent',
                `✅ Completed: ${taskDonePayload.task_id}`,
                '✅'
            );
            loadDashboardData(); // Refresh metrics
            break;
        case 'task_blocked':
            const blockedPayload = data.payload || {};
            addActivityItem(
                blockedPayload.reported_by || 'Agent',
                `🚫 Blocked: ${blockedPayload.blocker}`,
                '🚫'
            );
            break;
        case 'task_assigned':
            const assignPayload = data.payload || {};
            addActivityItem(
                'System',
                `Task ${assignPayload.task_id} → ${assignPayload.assigned_to}`,
                '📋'
            );
            break;
        case 'project_completed':
            addActivityItem('System', '🎉 Project completed!', '🎉');
            document.getElementById('agents-status').textContent = 'Complete';
            document.getElementById('agents-status').style.background = 'rgba(63, 185, 80, 0.15)';
            updateAllAgentStatus('idle', 'Done');
            loadDashboardData();
            break;
        case 'system_error':
            const sysErrorPayload = data.payload || {};
            addActivityItem('System', `Error: ${sysErrorPayload.error}`, '⚠️');
            break;
        // Legacy event types for compatibility
        case 'agent_action':
            addActivityItem(data.agent, data.action, getAgentIcon(data.agent));
            updateAgentStatus(data.agent, 'active', data.action);
            break;
        case 'task_update':
            addActivityItem(data.agent || 'System', `Task: ${data.task_id} → ${data.status}`, '📋');
            break;
        case 'message':
            addActivityItem(data.from || 'Agent', data.content, '💬');
            break;
        case 'complete':
            document.getElementById('agents-status').textContent = 'Complete';
            updateAllAgentStatus('idle', 'Done');
            break;
    }
}

function addActivityItem(agent, task, icon) {
    const feedEl = document.getElementById('agent-activity-feed');
    const time = new Date().toLocaleTimeString();

    const itemHtml = `
        <div class="activity-item">
            <div class="activity-icon">${icon}</div>
            <div class="activity-content">
                <div class="activity-agent">${agent}</div>
                <div class="activity-task">${task}</div>
            </div>
            <span class="activity-time">${time}</span>
        </div>
    `;

    feedEl.insertAdjacentHTML('afterbegin', itemHtml);

    // Limit items
    while (feedEl.children.length > 50) {
        feedEl.removeChild(feedEl.lastChild);
    }
}

function getAgentIcon(agent) {
    const icons = {
        // By Profile
        'Product Owner': '📋',
        'ProductOwner': '📋',
        'Scrum Master': '🏃',
        'ScrumMaster': '🏃',
        'Architect': '🏗️',
        'Engineer': '💻',
        'QA Engineer': '🧪',
        'QAEngineer': '🧪',
        'QA': '🧪',
        // By Name (from our SCRUM agents)
        'Alice': '📋',    // Product Owner
        'Bob': '🏃',      // Scrum Master  
        'Alex': '💻',     // Engineer
        'Charlie': '🧪',  // QA Engineer
        // Legacy names
        'Paula': '📋',
        'Eve': '💻',
        'Sam': '🏃',
        // System
        'System': '⚙️'
    };
    return icons[agent] || '🤖';
}

function updateAgentStatus(agentName, status, task) {
    const statusItems = document.querySelectorAll('.agent-status-item');
    statusItems.forEach(item => {
        const name = item.querySelector('.agent-name').textContent;
        if (name.toLowerCase().includes(agentName.toLowerCase()) ||
            agentName.toLowerCase().includes(name.toLowerCase())) {
            const dot = item.querySelector('.agent-dot');
            const taskEl = item.querySelector('.agent-task');

            dot.className = `agent-dot ${status}`;
            taskEl.textContent = task || 'Working...';
        }
    });
}

function updateAllAgentStatus(status, task) {
    document.querySelectorAll('.agent-status-item').forEach(item => {
        const dot = item.querySelector('.agent-dot');
        const taskEl = item.querySelector('.agent-task');
        dot.className = `agent-dot ${status}`;
        taskEl.textContent = task;
    });
}

// Fallback polling for agent status
async function pollAgentStatus() {
    try {
        // Use the new activity endpoint for detailed info
        const activity = await apiGet('/company/activity');
        if (activity && activity.agents) {
            activity.agents.forEach(agent => {
                const status = agent.is_idle ? 'idle' : 'active';
                const action = agent.current_action || (agent.is_idle ? 'Waiting' : 'Working');
                updateAgentStatus(agent.name, status, action);

                // Add activity item if agent is working
                if (!agent.is_idle) {
                    addActivityItem(agent.name, action, getAgentIcon(agent.profile || agent.name));
                }
            });

            // Update overall status
            if (activity.is_running) {
                document.getElementById('agents-status').textContent = 'Running';
            } else if (activity.status === 'idle') {
                document.getElementById('agents-status').textContent = 'Idle';
            }
        }
    } catch (e) {
        // Fallback to old status endpoint
        try {
            const status = await apiGet('/company/status');
            if (status && status.roles) {
                status.roles.forEach(role => {
                    if (!role.is_idle) {
                        updateAgentStatus(role.name, 'active', role.current_todo || 'Working');
                        addActivityItem(role.name, role.current_todo || 'Processing', getAgentIcon(role.name));
                    }
                });
            }
        } catch (e2) {
            console.log('Could not poll status');
        }
    }

    // Continue polling if agents are running
    if (document.getElementById('agents-status').textContent === 'Running') {
        setTimeout(pollAgentStatus, 2000);
    }
}

// Handle Enter key in chat
document.getElementById('chat-input')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

// Update switchView to handle newproject
const originalSwitchView = switchView;
switchView = function (viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    // Show selected view
    const view = document.getElementById(`${viewName}-view`);
    if (view) {
        view.classList.add('active');

        // Set page title
        const titles = {
            'newproject': 'New Project',
            'dashboard': 'Dashboard',
            'backlog': 'Product Backlog',
            'board': 'Kanban Board',
            'sprints': 'Sprints',
            'ceremonies': 'SCRUM Ceremonies',
            'team': 'AI Team'
        };
        document.getElementById('page-title').textContent = titles[viewName] || capitalizeFirst(viewName);

        // Load view-specific data
        switch (viewName) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'backlog':
                loadBacklog();
                break;
            case 'board':
                loadBoard();
                break;
            case 'sprints':
                loadSprints();
                break;
        }
    }
};
