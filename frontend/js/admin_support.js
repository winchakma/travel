// admin_support.js
// Handles the admin/trainer side of the WebSocket Support Chat

let adminSupportWs = null;
let currentSupportSessionId = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only init if we are on a page that has the support section
    if (document.getElementById('view-support')) {
        initAdminSupport();
    }
});

function initAdminSupport() {
    const token = localStorage.getItem('gotrip_token');
    if (!token) return;

    // Use the same API host logic
    const activeAPI = window.ELITE_API_URL || "https://travel-xyyl.onrender.com";
    let wsUrl = activeAPI.replace(/^http/, 'ws') + `/api/support-ws/chat?token=${encodeURIComponent(token)}`;

    // Fallback to local if on localhost and no ELITE_API_URL
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        if (!window.ELITE_API_URL) {
            wsUrl = `ws://localhost:8000/api/support-ws/chat?token=${encodeURIComponent(token)}`;
        }
    }

    adminSupportWs = new WebSocket(wsUrl);

    adminSupportWs.onopen = () => {
        console.log("Admin Support WebSocket connected");
        document.getElementById('admin-support-status').textContent = 'Live';
        document.getElementById('admin-support-status').className = 'text-[10px] text-green-500 font-bold uppercase tracking-widest';
        
        // Fetch open sessions
        adminSupportWs.send(JSON.stringify({ action: 'fetch_sessions' }));
    };

    adminSupportWs.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.event === 'sessions_list') {
            renderAdminSessions(data.sessions);
        } else if (data.event === 'chat_history') {
            currentSupportSessionId = data.session_id;
            renderAdminChatHistory(data.messages);
            document.getElementById('admin-support-chat-form').classList.remove('hidden');
            // Remove unread badge if we are viewing it
            const badge = document.getElementById('support-unread-badge');
            if (badge) badge.classList.add('hidden');
        } else if (data.event === 'new_message') {
            // Update UI if this session is currently active
            if (currentSupportSessionId === data.session_id) {
                appendAdminMessage(data);
                const historyEl = document.getElementById('admin-support-chat-history');
                historyEl.scrollTop = historyEl.scrollHeight;
            } else {
                // Show badge on sidebar if it's a new message for another session
                const badge = document.getElementById('support-unread-badge');
                if (badge) badge.classList.remove('hidden');
                
                // Refresh sessions to show the updated thread
                adminSupportWs.send(JSON.stringify({ action: 'fetch_sessions' }));
            }
        }
    };

    adminSupportWs.onclose = () => {
        console.log("Admin Support WebSocket disconnected");
        clearInterval(adminSupportWs.pingInterval);
        document.getElementById('admin-support-status').textContent = 'Disconnected';
        document.getElementById('admin-support-status').className = 'text-[10px] text-red-500 font-bold uppercase tracking-widest';
        
        // Reconnect after 5 seconds
        setTimeout(initAdminSupport, 5000);
    };

    // Keepalive to prevent Render timeout
    adminSupportWs.pingInterval = setInterval(() => {
        if (adminSupportWs && adminSupportWs.readyState === WebSocket.OPEN) {
            adminSupportWs.send(JSON.stringify({ action: "ping" }));
        }
    }, 20000);

    // Handle Send
    document.getElementById('admin-support-send').addEventListener('click', sendAdminReply);
    document.getElementById('admin-support-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendAdminReply();
    });
}

function renderAdminSessions(sessions) {
    const listEl = document.getElementById('admin-support-sessions');
    if (sessions.length === 0) {
        listEl.innerHTML = '<div class="p-6 text-center text-[#555] text-xs italic font-bold">No active support threads</div>';
        return;
    }

    listEl.innerHTML = sessions.map(session => `
        <div class="p-4 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors" onclick="loadSupportSession('${session.id}', '${session.userName}')">
            <div class="flex justify-between items-start mb-1">
                <span class="text-xs font-bold text-yellow-400 uppercase tracking-widest">${session.userName}</span>
                <span class="text-[9px] text-[#666]">${new Date(session.updated_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
            <div class="text-[10px] text-[#888] truncate">${session.userEmail}</div>
        </div>
    `).join('');
}

window.loadSupportSession = function(sessionId, userName) {
    document.getElementById('admin-support-chat-title').textContent = 'Chat with ' + userName;
    document.getElementById('admin-support-chat-history').innerHTML = '<div class="text-center text-[#555] text-xs italic mt-4">Loading history...</div>';
    
    if (adminSupportWs && adminSupportWs.readyState === WebSocket.OPEN) {
        adminSupportWs.send(JSON.stringify({
            action: 'fetch_history',
            session_id: sessionId
        }));
    }
};

function renderAdminChatHistory(messages) {
    const historyEl = document.getElementById('admin-support-chat-history');
    if (!messages || messages.length === 0) {
        historyEl.innerHTML = '<div class="text-center text-[#555] text-xs italic mt-4">No messages yet.</div>';
        return;
    }

    historyEl.innerHTML = '';
    messages.forEach(msg => appendAdminMessage(msg));
    historyEl.scrollTop = historyEl.scrollHeight;
}

function appendAdminMessage(msg) {
    const historyEl = document.getElementById('admin-support-chat-history');
    
    // In admin panel, admin is 'me', user is 'them'
    const isMe = msg.sender_type === 'admin';
    const alignClass = isMe ? 'self-end' : 'self-start';
    const bgClass = isMe ? 'bg-yellow-400 text-black' : 'bg-[#1a1a1a] text-white border border-white/10';
    const nameStr = isMe ? 'You' : msg.sender_name;

    let contentHtml = '';
    if (msg.message_type === 'image') {
        contentHtml = `<img src="${msg.content}" class="max-w-[200px] rounded-lg mt-1 cursor-pointer" onclick="openMediaModal('${msg.content}', 'image')">`;
    } else {
        contentHtml = `<div>${msg.content.replace(/\n/g, '<br>')}</div>`;
    }

    const msgHtml = `
        <div class="flex flex-col max-w-[80%] ${alignClass}">
            <span class="text-[9px] text-[#666] font-bold uppercase tracking-widest mb-1 ${isMe ? 'text-right' : 'text-left'}">${nameStr}</span>
            <div class="p-3 rounded-2xl text-xs ${bgClass}">
                ${contentHtml}
            </div>
            <span class="text-[8px] text-[#444] mt-1 ${isMe ? 'text-right' : 'text-left'}">
                ${new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </span>
        </div>
    `;

    historyEl.insertAdjacentHTML('beforeend', msgHtml);
}

function sendAdminReply() {
    const input = document.getElementById('admin-support-input');
    const content = input.value.trim();
    
    if (!content || !currentSupportSessionId) return;

    if (adminSupportWs && adminSupportWs.readyState === WebSocket.OPEN) {
        adminSupportWs.send(JSON.stringify({
            action: 'admin_reply',
            session_id: currentSupportSessionId,
            type: 'text',
            content: content
        }));
        input.value = '';
    }
}
