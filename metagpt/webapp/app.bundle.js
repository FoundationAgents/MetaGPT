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

    // Update status (if element exists)
    const chatStatus = document.getElementById('chat-status');
    if (chatStatus) {
        chatStatus.textContent = 'Thinking...';
        chatStatus.style.background = 'rgba(210, 153, 34, 0.15)';
        chatStatus.style.color = 'var(--accent-warning)';
    }

    console.log('Sending chat message:', message);

    try {
        let response;

        if (!currentConversationId) {
            // Start new conversation
            console.log('Starting new conversation...');
            response = await apiPost('/conversation/start', { initial_idea: message });
            console.log('Conversation start response:', response);

            if (response) {
                currentConversationId = response.conversation_id;
                addChatMessage(response.first_question, 'ai');
                // Show Skip button after first message
                const skipBtn = document.getElementById('skip-btn');
                if (skipBtn) skipBtn.style.display = 'inline-flex';
            }
        } else {
            // Continue conversation
            console.log('Continuing conversation:', currentConversationId);
            response = await apiPost('/conversation/message', {
                conversation_id: currentConversationId,
                message: message
            });
            console.log('Conversation message response:', response);

            if (response) {
                addChatMessage(response.ai_response, 'ai');

                // Show approve button if ready
                if (response.requires_approval) {
                    const approveBtn = document.getElementById('approve-btn');
                    if (approveBtn) approveBtn.style.display = 'inline-flex';
                    if (chatStatus) {
                        chatStatus.textContent = 'Ready to Approve';
                        chatStatus.style.background = 'rgba(63, 185, 80, 0.15)';
                        chatStatus.style.color = 'var(--accent-success)';
                    }
                }
            }
        }

        if (chatStatus && (!response || !response.requires_approval)) {
            chatStatus.textContent = 'Active';
            chatStatus.style.background = 'rgba(88, 166, 255, 0.15)';
            chatStatus.style.color = 'var(--accent-primary)';
        }
    } catch (error) {
        console.error('Chat error:', error);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
        if (chatStatus) chatStatus.textContent = 'Error';
        showModal('Chat Error', 'Failed to communicate with AI: ' + (error.message || 'Unknown error'));
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
            'monitoring': 'Live Monitoring',
            'backlog': 'Product Backlog',
            'board': 'Kanban Board',
            'sprints': 'Sprints',
            'artifacts': 'Project Artifacts',
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
            case 'monitoring':
                if (!activityWebSocket || activityWebSocket.readyState !== WebSocket.OPEN) {
                    startActivityStream();
                }
                break;
            case 'artifacts':
                loadArtifacts();
                break;
        }
    }
};

// ============================================
// EXECUTION MODE HANDLING
// ============================================

let executionMode = 'interactive'; // 'interactive' or 'autonomous'

// Initialize mode selection
document.querySelectorAll('.mode-option')?.forEach(option => {
    option.addEventListener('click', () => {
        const mode = option.dataset.mode;
        setExecutionMode(mode);
    });
});

function setExecutionMode(mode) {
    executionMode = mode;

    // Update UI
    document.querySelectorAll('.mode-option').forEach(opt => {
        opt.classList.remove('selected');
        if (opt.dataset.mode === mode) {
            opt.classList.add('selected');
        }
    });

    // Update header display
    const modeDisplay = document.getElementById('current-mode');
    if (modeDisplay) {
        modeDisplay.textContent = mode === 'interactive' ? 'Interactive' : 'Autonomous';
    }

    console.log('Execution mode set to:', mode);
}

// ============================================
// FILE EXPLORER / ARTIFACTS
// ============================================

async function loadArtifacts() {
    const fileTree = document.getElementById('file-tree');
    const filePreview = document.getElementById('file-preview');

    fileTree.innerHTML = '<p style="color: var(--text-muted); padding: 20px;">Loading files...</p>';
    filePreview.innerHTML = '<p class="empty-state">Select a file to preview</p>';

    try {
        const data = await apiGet(`/files/project/${currentProjectId}/tree`);

        if (data && data.items && data.items.length > 0) {
            fileTree.innerHTML = renderFileTree(data.items);

            // Add click handlers for files
            fileTree.querySelectorAll('.file-item[data-type="file"]').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    loadFilePreview(item.dataset.path);
                });
            });

            // Add click handlers for folders (simple toggle)
            fileTree.querySelectorAll('.file-item[data-type="directory"]').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    item.classList.toggle('expanded');
                    const children = item.nextElementSibling;
                    if (children && children.classList.contains('folder-children')) {
                        children.classList.toggle('visible');
                    }
                });
            });
        } else {
            fileTree.innerHTML = '<p class="empty-state">No artifacts generated yet.</p>';
        }
    } catch (e) {
        console.error('Failed to load artifacts:', e);
        fileTree.innerHTML = '<p class="empty-state">Failed to load artifacts.</p>';
    }
}

function renderFileTree(items, prefix = '') {
    let html = '';

    // Sort: directories first, then files
    const sortedItems = items.sort((a, b) => {
        if (a.type === b.type) return a.name.localeCompare(b.name);
        return a.type === 'directory' ? -1 : 1;
    });

    sortedItems.forEach(item => {
        const icon = item.type === 'directory' ? '📁' : getFileIcon(item.extension);
        const sizeStr = item.type === 'file' ? formatFileSize(item.size) : '';
        const arrow = item.type === 'directory' ? '<span class="arrow">▶</span>' : '';

        html += `
            <div class="file-item ${item.type}" data-path="${item.path}" data-type="${item.type}">
                ${arrow}
                <span class="file-icon">${icon}</span>
                <span class="file-name">${item.name}</span>
                ${sizeStr ? `<span class="file-size">${sizeStr}</span>` : ''}
            </div>
        `;

        // Always render children container, but hidden by default
        if (item.type === 'directory') {
            const childrenHtml = item.children ? renderFileTree(item.children) : '';
            html += `<div class="folder-children">${childrenHtml}</div>`;
        }
    });

    return html;
}

function getFileIcon(ext) {
    const icons = {
        '.py': '🐍',
        '.js': '📜',
        '.ts': '📘',
        '.html': '🌐',
        '.css': '🎨',
        '.json': '📋',
        '.md': '📄',
        '.yaml': '⚙️',
        '.yml': '⚙️',
        '.txt': '📝',
        '.sh': '🐚',
        '.dockerfile': '🐳',
        '.png': '🖼️',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.svg': '🖼️'
    };
    // Handle special cases
    if (ext === '.gitignore') return '👁️';

    return icons[ext] || '📄';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function loadFilePreview(path) {
    const preview = document.getElementById('file-preview');
    preview.innerHTML = '<p style="color: var(--text-muted); padding: 20px;">Loading...</p>';

    // Update selection
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.path === path) {
            item.classList.add('selected');
        }
    });

    try {
        const data = await apiGet(`/files/project/${currentProjectId}/content?path=${encodeURIComponent(path)}`);

        if (data && data.content !== undefined) {
            const ext = path.split('.').pop().toLowerCase();
            const languageMap = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'typescript',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'md': 'markdown',
                'sh': 'bash',
                'yaml': 'yaml',
                'yml': 'yaml'
            };
            const lang = languageMap[ext] || 'clike';

            preview.innerHTML = `
                <div class="code-preview-container">
                    <pre><code class="language-${lang}">${escapeHtml(data.content)}</code></pre>
                </div>
            `;

            // Apply syntax highlighting
            if (window.Prism) {
                try {
                    Prism.highlightAllUnder(preview);
                } catch (e) {
                    console.warn('Prism highlighting failed:', e);
                }
            }
        } else {
            preview.innerHTML = '<p class="empty-state">Cannot preview this file</p>';
        }
    } catch (e) {
        console.error('File preview error:', e);
        preview.innerHTML = '<p class="empty-state">Failed to load file</p>';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function (m) { return map[m]; });
}

async function downloadProject() {
    showLoading('Preparing download...');

    try {
        const response = await fetch(`${API_BASE}/files/project/${currentProjectId}/download`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentProjectId}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            throw new Error('Download failed');
        }
    } catch (e) {
        showModal('Error', 'Failed to download project files.');
    }

    hideLoading();
}

// ============================================
// PROJECT REVIEW MODAL
// ============================================

let feedbackType = null;

function showProjectReview() {
    const modal = document.getElementById('review-modal-overlay');
    const summary = document.getElementById('review-summary');

    summary.innerHTML = `
        <h3>🎉 Project Completed!</h3>
        <p>Your AI team has finished working on the project. Review the generated artifacts and provide feedback.</p>
        <ul style="margin-top: 12px;">
            <li>📄 Documentation generated</li>
            <li>💻 Source code implemented</li>
            <li>🧪 Tests written</li>
        </ul>
    `;

    modal.style.display = 'flex';
}

function closeReviewModal() {
    document.getElementById('review-modal-overlay').style.display = 'none';
    document.getElementById('feedback-form').style.display = 'none';
}

function submitFeedback(type) {
    feedbackType = type;

    if (type === 'done') {
        // Mark project as complete
        apiPost(`/project/${currentProjectId}/complete`, { status: 'completed' })
            .then(() => {
                closeReviewModal();
                showModal('Success', 'Project marked as complete!');
            });
        return;
    }

    // Show feedback form for other types
    const titles = {
        'change': 'Describe the changes you need:',
        'bug': 'Describe the bug you found:',
        'feature': 'Describe the new feature:'
    };

    document.getElementById('feedback-title').textContent = titles[type] || 'Describe your feedback:';
    document.getElementById('feedback-form').style.display = 'block';
}

function cancelFeedback() {
    document.getElementById('feedback-form').style.display = 'none';
    feedbackType = null;
}

async function sendFeedback() {
    const text = document.getElementById('feedback-text').value.trim();

    if (!text) {
        alert('Please describe your feedback');
        return;
    }

    showLoading('Submitting feedback...');

    try {
        await apiPost(`/project/${currentProjectId}/feedback`, {
            type: feedbackType,
            description: text
        });

        hideLoading();
        closeReviewModal();
        showModal('Feedback Submitted', 'A new iteration will be started based on your feedback.');

        // Clear form
        document.getElementById('feedback-text').value = '';
        feedbackType = null;

    } catch (e) {
        hideLoading();
        showModal('Error', 'Failed to submit feedback. Please try again.');
    }
}

// ============================================
// PRD PREVIEW AND ACCEPTANCE
// ============================================

let generatedPRD = null;

function showPRDPreview(prdContent) {
    generatedPRD = prdContent;
    document.getElementById('prd-content').innerHTML = escapeHtml(prdContent);
    document.getElementById('prd-preview').style.display = 'block';
    document.getElementById('chat-actions').style.display = 'none';
}

function editPRD() {
    // Allow user to edit - switch back to chat mode
    document.getElementById('prd-preview').style.display = 'none';
    document.getElementById('chat-actions').style.display = 'flex';
    addChatMessage('I\'d like to make some changes to the PRD.', 'user');
}

async function acceptPRD() {
    showLoading('Starting project development...');

    try {
        // First approve
        await approveRequirements();

        // Then navigate to Live Monitoring
        switchView('monitoring');

        // Update nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === 'monitoring') {
                item.classList.add('active');
            }
        });

    } catch (e) {
        hideLoading();
        showModal('Error', 'Failed to start project. Please try again.');
    }
}

// ============================================
// INTERACTIVE MODE APPROVAL HANDLING
// ============================================

function showApprovalPanel(content, title) {
    const panel = document.getElementById('approval-panel');
    const contentEl = document.getElementById('approval-content');

    panel.style.display = 'block';
    contentEl.innerHTML = `<h4>${title}</h4><pre style="white-space: pre-wrap;">${content}</pre>`;
}

function hideApprovalPanel() {
    document.getElementById('approval-panel').style.display = 'none';
}

async function approveAndContinue() {
    showLoading('Processing...');
    hideApprovalPanel();

    try {
        await apiPost(`/project/${currentProjectId}/approve-step`, {
            approved: true
        });
        hideLoading();
    } catch (e) {
        hideLoading();
        showModal('Error', 'Failed to process approval.');
    }
}

async function requestChanges() {
    const changes = prompt('Describe the changes you want:');
    if (changes) {
        showLoading('Processing...');
        hideApprovalPanel();

        try {
            await apiPost(`/project/${currentProjectId}/approve-step`, {
                approved: false,
                changes: changes
            });
            hideLoading();
        } catch (e) {
            hideLoading();
            showModal('Error', 'Failed to process change request.');
        }
    }
}

// ============================================
// ENHANCED EVENT HANDLING FOR ALL PAGES
// ============================================

// Enhanced handleActivityEvent to update all pages
const originalHandleActivityEvent = handleActivityEvent;
handleActivityEvent = function (data) {
    // Call original handler
    originalHandleActivityEvent(data);

    // Additional handling for real-time updates across pages
    switch (data.type) {
        case 'sprint_planned':
        case 'sprint_started':
        case 'sprint_completed':
            loadSprints();
            loadDashboardData();
            break;
        case 'backlog_updated':
            loadBacklog();
            break;
        case 'task_moved':
        case 'task_created':
        case 'task_updated':
            loadBoard();
            loadDashboardData();
            break;
        case 'artifact_created':
            // Refresh artifacts if on that view
            if (document.getElementById('artifacts-view')?.classList.contains('active')) {
                loadArtifacts();
            }
            break;
        case 'project_completed':
            // Show review modal in interactive mode
            if (executionMode === 'interactive') {
                setTimeout(() => showProjectReview(), 2000);
            }
            break;
        case 'approval_required':
            // Interactive mode: show approval panel
            if (executionMode === 'interactive' && data.payload) {
                showApprovalPanel(data.payload.content, data.payload.title || 'Approval Required');
            }
            break;
    }
};

// Make functions globally available
window.sendChatMessage = sendChatMessage;
window.skipQuestionsAndApprove = skipQuestionsAndApprove;
window.approveRequirements = approveRequirements;
window.runCeremony = runCeremony;
window.closeCeremonyOutput = closeCeremonyOutput;
window.prioritizeBacklog = prioritizeBacklog;
window.closeModal = closeModal;
window.downloadProject = downloadProject;
window.showProjectReview = showProjectReview;
window.closeReviewModal = closeReviewModal;
window.submitFeedback = submitFeedback;
window.cancelFeedback = cancelFeedback;
window.sendFeedback = sendFeedback;
window.editPRD = editPRD;
window.acceptPRD = acceptPRD;
window.approveAndContinue = approveAndContinue;
window.requestChanges = requestChanges;
window.approveBacklog = function () { console.log('Approve backlog'); };
window.approveSprint = function () { console.log('Approve sprint'); };

// ============================================
// FEEDBACK CHAT FOR EXISTING PROJECTS
// ============================================

let pendingFeedback = null;

async function sendFeedbackChat() {
    const input = document.getElementById('feedback-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to feedback chat
    addFeedbackMessage(message, 'user');
    input.value = '';

    // Update status
    const statusEl = document.getElementById('feedback-status');
    if (statusEl) {
        statusEl.textContent = 'Analyzing...';
    }

    console.log('Sending feedback request:', message);

    try {
        // Call the AI to analyze and classify the feedback
        const response = await apiPost('/feedback/analyze', {
            project_id: currentProjectId,
            description: message
        });

        console.log('Feedback analysis response:', response);

        if (response && response.classification) {
            // Store the pending feedback
            pendingFeedback = {
                type: response.classification,
                title: response.suggested_title || 'User Request',
                description: message,
                priority: response.priority || 'medium',
                aiSummary: response.summary || message
            };

            // Show AI classification response
            const icons = {
                'bug': '🐛',
                'feature': '✨',
                'enhancement': '📈',
                'change': '🔄'
            };
            const icon = icons[response.classification] || '📋';

            addFeedbackMessage(`I've analyzed your request. This looks like a **${response.classification.toUpperCase()}**.\n\n` +
                `**Summary:** ${response.summary || message}\n\n` +
                `**Suggested Title:** ${response.suggested_title || 'User Request'}\n\n` +
                `If this looks correct, click "Confirm & Create Task" to add it to the backlog.`, 'ai');

            // Show the result UI
            showFeedbackResult(response);

            if (statusEl) {
                statusEl.textContent = 'Classified';
            }
        } else {
            addFeedbackMessage('I understood your request. Let me create a task for the team.', 'ai');

            // Default to a change request if no classification
            pendingFeedback = {
                type: 'change',
                title: 'User Request',
                description: message,
                priority: 'medium',
                aiSummary: message
            };

            showFeedbackResult({ classification: 'change', summary: message });
        }
    } catch (error) {
        console.error('Feedback analysis error:', error);
        addFeedbackMessage('I\'ll create a task for this request. The team will review it.', 'ai');

        // Still allow submission even if analysis fails
        pendingFeedback = {
            type: 'change',
            title: 'User Request',
            description: message,
            priority: 'medium',
            aiSummary: message
        };

        showFeedbackResult({ classification: 'change', summary: message });

        if (statusEl) {
            statusEl.textContent = 'Ready';
        }
    }
}

function addFeedbackMessage(text, sender) {
    const container = document.getElementById('feedback-messages');
    if (!container) return;

    const isUser = sender === 'user';

    // Format markdown-like text (basic)
    const formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    const messageHtml = `
        <div class="chat-message ${sender}">
            <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
            <div class="message-content">
                <strong>${isUser ? 'You' : 'AI Assistant'}</strong>
                <p>${formattedText}</p>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', messageHtml);
    container.scrollTop = container.scrollHeight;
}

function showFeedbackResult(response) {
    const resultEl = document.getElementById('feedback-result');
    const classificationEl = document.getElementById('feedback-classification');

    if (!resultEl || !classificationEl) return;

    const icons = {
        'bug': '🐛 Bug Report',
        'feature': '✨ New Feature',
        'enhancement': '📈 Enhancement',
        'change': '🔄 Change Request'
    };

    classificationEl.innerHTML = `
        <div class="classification-badge ${response.classification}">
            ${icons[response.classification] || '📋 Request'}
        </div>
        <div class="classification-summary">
            ${response.summary || pendingFeedback?.description || 'Your request has been analyzed.'}
        </div>
    `;

    resultEl.style.display = 'block';
}

function editFeedbackRequest() {
    // Hide result, show input
    const resultEl = document.getElementById('feedback-result');
    if (resultEl) resultEl.style.display = 'none';

    // Put the description back in the input
    const input = document.getElementById('feedback-input');
    if (input && pendingFeedback) {
        input.value = pendingFeedback.description;
    }

    pendingFeedback = null;
}

async function submitFeedbackRequest() {
    if (!pendingFeedback) {
        showModal('Error', 'No pending feedback to submit.');
        return;
    }

    showLoading('Creating task...');

    try {
        // Add to backlog as a task/bug
        const result = await apiPost(`/project/${currentProjectId}/backlog/task`, {
            title: pendingFeedback.title,
            description: pendingFeedback.description + '\n\n---\n*AI Analysis: ' + pendingFeedback.aiSummary + '*',
            priority: pendingFeedback.priority,
            type: pendingFeedback.type === 'bug' ? 'bug' : 'task'
        });

        hideLoading();

        if (result) {
            // Clear the feedback chat
            const container = document.getElementById('feedback-messages');
            if (container) {
                container.innerHTML = `
                    <div class="chat-message ai">
                        <div class="message-avatar">🤖</div>
                        <div class="message-content">
                            <strong>AI Assistant</strong>
                            <p>✅ Task created successfully! The team will work on it in the next sprint.</p>
                        </div>
                    </div>
                `;
            }

            // Hide result
            const resultEl = document.getElementById('feedback-result');
            if (resultEl) resultEl.style.display = 'none';

            // Update status
            const statusEl = document.getElementById('feedback-status');
            if (statusEl) statusEl.textContent = 'Task Created';

            // Refresh backlog
            loadBacklog();

            showModal('Success', `${pendingFeedback.type === 'bug' ? 'Bug' : 'Task'} "${pendingFeedback.title}" has been added to the backlog.`);

            pendingFeedback = null;
        }
    } catch (error) {
        hideLoading();
        console.error('Submit feedback error:', error);
        showModal('Error', 'Failed to create task. Please try again.');
    }
}

// Make feedback functions globally available
window.sendFeedbackChat = sendFeedbackChat;
window.editFeedbackRequest = editFeedbackRequest;
window.submitFeedbackRequest = submitFeedbackRequest;
