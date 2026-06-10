document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("gotrip-support-widget")) return;

    const token = localStorage.getItem("gotrip_token");

    const supportHTML = `
    <div id="gotrip-support-widget" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: 'Inter', sans-serif;">
        <div id="support-window" style="display: none; width: 350px; height: 500px; background: #1a1a1a; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); flex-direction: column; overflow: hidden; margin-bottom: 15px; border: 1px solid #333;">
            <div style="background: #000; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-weight: 800; font-size: 14px; letter-spacing: 1px;">ELITE SUPPORT</span>
                </div>
                <button id="support-close-btn" style="background: transparent; border: none; color: white; cursor: pointer; font-size: 20px;">&times;</button>
            </div>
            
            ${!token ? `
                <div style="flex: 1; display: flex; align-items: center; justify-content: center; color: white; padding: 20px; text-align: center;">
                    Please log in to use Elite Support.
                </div>
            ` : `
                <div id="support-role-selector" style="flex: 1; display: flex; flex-direction: column; justify-content: center; padding: 20px; gap: 15px;">
                    <p style="color: #888; text-align: center; margin-bottom: 10px; font-size: 14px;">Who do you want to talk to?</p>
                    <button class="support-role-btn" data-role="Super Admin" style="background: transparent; border: 1px solid #333; color: white; padding: 15px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: bold; transition: all 0.2s;">OWNER (SUPER ADMIN)</button>
                    <button class="support-role-btn" data-role="Normal Admin" style="background: transparent; border: 1px solid #333; color: white; padding: 15px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: bold; transition: all 0.2s;">TRAVEL AGENT (NORMAL ADMIN)</button>
                </div>
                
                <div id="support-chat-area" style="display: none; flex: 1; flex-direction: column; overflow: hidden;">
                    <div id="support-messages" style="flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #1a1a1a;">
                        <div style="text-align: center; color: #555; font-size: 12px; margin-top: 10px;">Connecting to secure line...</div>
                    </div>
                    <div style="padding: 15px; background: #111; border-top: 1px solid #333; display: flex; gap: 10px;">
                        <input type="text" id="support-input" placeholder="Type a message..." style="flex: 1; padding: 10px 15px; background: #222; border: 1px solid #333; border-radius: 20px; color: white; outline: none; font-size: 14px;">
                        <button id="support-send-btn" style="background: transparent; color: #e5c414; border: none; cursor: pointer; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 18px;">➤</button>
                    </div>
                </div>
            `}
        </div>
        <button id="support-toggle-btn" style="width: 60px; height: 60px; background: #facc15; color: #000; border: none; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); cursor: pointer; display: flex; justify-content: center; align-items: center; font-size: 24px; float: right; transition: transform 0.2s; font-weight: bold; font-family: monospace;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        </button>
    </div>
    `;

    document.body.insertAdjacentHTML('beforeend', supportHTML);

    const toggleBtn = document.getElementById("support-toggle-btn");
    const closeBtn = document.getElementById("support-close-btn");
    const supportWindow = document.getElementById("support-window");
    
    toggleBtn.addEventListener("click", () => {
        supportWindow.style.display = supportWindow.style.display === "none" ? "flex" : "none";
    });
    
    closeBtn.addEventListener("click", () => {
        supportWindow.style.display = "none";
    });

    if (!token) return;

    const roleSelector = document.getElementById("support-role-selector");
    const chatArea = document.getElementById("support-chat-area");
    const messagesContainer = document.getElementById("support-messages");
    const inputField = document.getElementById("support-input");
    const sendBtn = document.getElementById("support-send-btn");
    const roleBtns = document.querySelectorAll(".support-role-btn");

    roleBtns.forEach(btn => {
        btn.addEventListener("mouseenter", () => { btn.style.background = "#222"; btn.style.borderColor = "#555"; });
        btn.addEventListener("mouseleave", () => { btn.style.background = "transparent"; btn.style.borderColor = "#333"; });
    });

    let ws = null;
    let selectedRole = null;
    let sessionId = null;

    function initWebSocket() {
        if (ws) ws.close();
        
        const activeAPI = window.ELITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:10000' : 'https://travel-xyyl.onrender.com');
        let wsUrl = activeAPI.replace(/^http/, 'ws') + '/api/support-ws/chat?token=' + encodeURIComponent(token);
        
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log("Support WS Connected");
            messagesContainer.innerHTML = '<div style="text-align: center; color: #e5c414; font-size: 12px; margin-top: 10px; text-transform: uppercase; letter-spacing: 1px;">Secure Connection Established</div>';
            
            ws.send(JSON.stringify({
                action: "fetch_history",
                targetRole: selectedRole
            }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.event === "chat_history") {
                sessionId = data.session_id;
                messagesContainer.innerHTML = "";
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => appendMessage(msg));
                } else {
                    messagesContainer.innerHTML = '<div style="text-align: center; color: #555; font-size: 12px; margin-top: 10px;">Start the conversation...</div>';
                }
            } else if (data.event === "new_message") {
                appendMessage(data);
            }
        };

        ws.onclose = () => {
            console.log("Support WS Disconnected");
            setTimeout(initWebSocket, 5000);
        };

        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: "ping" }));
            }
        }, 20000);
    }

    roleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            selectedRole = btn.getAttribute("data-role");
            roleSelector.style.display = "none";
            chatArea.style.display = "flex";
            initWebSocket();
        });
    });

    function appendMessage(msg) {
        if (messagesContainer.innerHTML.includes("Start the conversation...")) {
            messagesContainer.innerHTML = "";
        }

        const isUser = msg.sender_type === "user";
        const msgDiv = document.createElement("div");
        msgDiv.style.alignSelf = isUser ? "flex-end" : "flex-start";
        msgDiv.style.background = isUser ? "#e5c414" : "#222";
        msgDiv.style.color = isUser ? "black" : "white";
        msgDiv.style.padding = "10px 14px";
        msgDiv.style.borderRadius = "12px";
        msgDiv.style.fontSize = "13px";
        msgDiv.style.maxWidth = "80%";
        msgDiv.style.lineHeight = "1.4";
        msgDiv.style.border = isUser ? "none" : "1px solid #333";
        
        let contentHtml = msg.content.replace(/\n/g, "<br>");
        
        msgDiv.innerHTML = `<div style="font-size: 9px; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; color: ${isUser ? '#000' : '#888'};">${isUser ? 'You' : msg.sender_name}</div>${contentHtml}`;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function sendMessage() {
        const text = inputField.value.trim();
        if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

        ws.send(JSON.stringify({
            action: "send_message",
            targetRole: selectedRole,
            type: "text",
            content: text
        }));
        
        inputField.value = "";
    }

    sendBtn.addEventListener("click", sendMessage);
    inputField.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});
