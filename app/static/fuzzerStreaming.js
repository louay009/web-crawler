const resultsByStatus = {};
let totalTested = 0;
let successfulResponses = 0;
let currentTaskId = null;

function createStatusGroup(statusCode) {
    const statusText = statusCode === 200 ? 'Success' :
                     statusCode === 404 ? 'Not Found' :
                     statusCode === 500 ? 'Server Error' : 'Unknown Status';

    const group = document.createElement('div');
    group.className = 'status-group';
    group.dataset.status = statusCode;
    group.innerHTML = `
        <div class="status-header" onclick="toggleGroup(${statusCode})">
            <div style="display: flex; align-items: center;">
                <span class="status-badge status-${statusCode}">
                    ${statusCode} - ${statusText}
                </span>
                <span class="count-badge">0 URLs</span>
            </div>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="status-content">
            <ul class="url-list"></ul>
        </div>
    `;
    return group;
}

function toggleGroup(statusCode) {
    const group = document.querySelector(`[data-status="${statusCode}"]`);
    const content = group.querySelector('.status-content');
    const header = group.querySelector('.status-header');
    content.classList.toggle('expanded');
    header.classList.toggle('expanded');
}

function updateStats() {
    document.getElementById('totalTested').textContent = totalTested;
    document.getElementById('successfulResponses').textContent = successfulResponses;
}

function addResult(result) {
    totalTested++;
    if (result.status_code === 200) {
        successfulResponses++;
    }

    const statusCode = result.status_code || 'error';
    if (!resultsByStatus[statusCode]) {
        resultsByStatus[statusCode] = [];
        const statusGroup = createStatusGroup(statusCode);
        document.getElementById('status-groups').appendChild(statusGroup);
    }

    resultsByStatus[statusCode].push(result);

    const group = document.querySelector(`[data-status="${statusCode}"]`);
    const countBadge = group.querySelector('.count-badge');
    countBadge.textContent = `${resultsByStatus[statusCode].length} URLs`;

    const urlList = group.querySelector('.url-list');
    const listItem = document.createElement('li');
    if (result.error) {
        listItem.innerHTML = `
            <span class="url-text">${result.url}</span>
            <div style="color: #991b1b; margin-top: 0.25rem">${result.error}</div>
        `;
    } else {
        listItem.innerHTML = `
            <a href="${result.url}" class="url-text" target="_blank">${result.url}</a>
        `;
    }
    urlList.appendChild(listItem);

    updateStats();
}

const stopButton = document.getElementById('stopButton');
const statusMessage = document.getElementById('statusMessage');

async function stopFuzzing() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/stop_fuzz/${currentTaskId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            statusMessage.textContent = 'Fuzzing stopped';
            stopButton.disabled = true;
        } else {
            statusMessage.textContent = 'Error stopping fuzzing';
        }
    } catch (error) {
        console.error('Error stopping fuzzing:', error);
        statusMessage.textContent = 'Error stopping fuzzing';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const baseUrl = document.getElementById('baseUrl').textContent;
    stopButton.addEventListener('click', stopFuzzing);
    
    const eventSource = new EventSource(`/stream_fuzz?base_url=${encodeURIComponent(baseUrl)}`);
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.task_id) {
            currentTaskId = data.task_id;
            stopButton.disabled = false;
            statusMessage.textContent = 'Fuzzing in progress...';
            return;
        }
        
        addResult(data);
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        stopButton.disabled = true;
        statusMessage.textContent = 'Fuzzing completed or connection lost';
    };
});