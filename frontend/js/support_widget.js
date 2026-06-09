document.addEventListener("DOMContentLoaded", () => {
    // 1. Inject HTML
    const widgetHTML = `
        <div class="support-toggle-btn" id="supportToggleBtn">
            <i class="ri-customer-service-2-line"></i>
        </div>
        <div id="support-widget">
            <div class="support-header">
                <div style="display:flex; align-items:center; gap:8px;">
                    <button id="supportBackBtn" style="display: none; background:transparent; border:none; color:var(--yellow); font-size:18px; cursor:pointer;"><i class="ri-arrow-left-line"></i></button>
                    <h3>Elite Support</h3>
                </div>
                <button id="supportCloseBtn">&times;</button>
            </div>
            <div class="support-body" id="supportBody">
                <div class="support-role-select" id="supportRoleSelect">
                    <p style="text-align: center; color: var(--muted); font-size: 14px;">Who do you want to talk to?</p>
                    <button class="support-role-btn" data-role="Super Admin">Owner (Super Admin)</button>
                    <button class="support-role-btn" data-role="Normal Admin">Trainer (Normal Admin)</button>
                </div>
                <div id="supportChatArea" style="display: none; flex-direction: column; gap: 10px; flex: 1; overflow-y: auto;"></div>
            </div>
            <div class="support-footer" id="supportFooter" style="display: none;">
                <input type="file" id="supportImageInput" style="display: none;" accept="image/*">
                <button id="supportImageBtn" title="Attach Image"><i class="ri-image-add-line"></i></button>
                <input type="text" class="support-input" id="supportInput" placeholder="Type your message...">
                <button id="supportSendBtn"><i class="ri-send-plane-fill"></i></button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', widgetHTML);

    const toggleBtn = document.getElementById("supportToggleBtn");
    const widget = document.getElementById("support-widget");
    const closeBtn = document.getElementById("supportCloseBtn");
    const backBtn = document.getElementById("supportBackBtn");
    const roleSelect = document.getElementById("supportRoleSelect");
    const chatArea = document.getElementById("supportChatArea");
    const footer = document.getElementById("supportFooter");
    const roleBtns = document.querySelectorAll(".support-role-btn");
    const input = document.getElementById("supportInput");
    const sendBtn = document.getElementById("supportSendBtn");
    const imageBtn = document.getElementById("supportImageBtn");
    const imageInput = document.getElementById("supportImageInput");

    let ws = null;
    let currentRole = null;
    let sessionId = null;
    let isUploading = false;

    toggleBtn.addEventListener("click", () => {
        widget.classList.add("open");
        document.body.classList.add('support-is-open');
        toggleBtn.style.display = "none";
        if (!ws && currentRole) {
            initWebSocket();
        }
    });

    closeBtn.addEventListener("click", () => {
        widget.classList.remove("open");
        document.body.classList.remove('support-is-open');
        setTimeout(() => toggleBtn.style.display = "flex", 400);
    });

    backBtn.addEventListener("click", () => {
        if (ws) {
            ws.close();
            ws = null;
        }
        currentRole = null;
        sessionId = null;
        chatArea.innerHTML = "";
        
        backBtn.style.display = "none";
        chatArea.style.display = "none";
        footer.style.display = "none";
        roleSelect.style.display = "flex";
    });

    const appendMessage = (msg) => {
        const div = document.createElement("div");
        div.className = `support-msg ${msg.sender_type}`;
        if (msg.message_type === 'image') {
            div.innerHTML = `<img src="${msg.content}" alt="Image" onclick="window.open('${msg.content}', '_blank')">`;
        } else {
            div.textContent = msg.content;
        }
        chatArea.appendChild(div);
        chatArea.scrollTop = chatArea.scrollHeight;
    };

    const initWebSocket = () => {
        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please login to use support chat.");
            return;
        }
        
        const activeAPI = window.ELITE_API_URL || "https://mygym-p9rd.onrender.com";
        const wsUrl = activeAPI.replace(/^http/, 'ws') + `/api/support-ws/chat?token=${token}`;
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("Support WebSocket connected");
            // Ask for history
            ws.send(JSON.stringify({
                action: "fetch_history",
                targetRole: currentRole
            }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.event === "chat_history") {
                chatArea.innerHTML = "";
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(appendMessage);
                }
                sessionId = data.session_id;
            } else if (data.event === "new_message") {
                appendMessage(data);
            }
        };

        ws.onclose = () => {
            console.log("Support WebSocket disconnected");
            clearInterval(ws.pingInterval);
            ws = null;
        };

        // Keepalive to prevent Render timeout
        ws.pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: "ping" }));
            }
        }, 20000);
    };

    roleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const token = localStorage.getItem("token");
            if (!token) {
                alert("Please login to use support chat.");
                return;
            }
            currentRole = btn.getAttribute("data-role");
            roleSelect.style.display = "none";
            chatArea.style.display = "flex";
            footer.style.display = "flex";
            backBtn.style.display = "block";
            initWebSocket();
        });
    });

    const sendMessage = () => {
        const text = input.value.trim();
        if (text && ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                action: "send_message",
                targetRole: currentRole,
                content: text,
                type: "text"
            }));
            input.value = "";
        }
    };

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    imageBtn.addEventListener("click", () => {
        imageInput.click();
    });

    imageInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        isUploading = true;
        imageBtn.innerHTML = `<i class="ri-loader-4-line ri-spin"></i>`;
        
        const formData = new FormData();
        formData.append("image", file);

        try {
            const activeAPI = window.ELITE_API_URL || "https://mygym-p9rd.onrender.com";
            const res = await fetch(`${activeAPI}/api/support-ws/upload-image`, {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (data.url) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        action: "send_message",
                        targetRole: currentRole,
                        content: data.url,
                        type: "image"
                    }));
                }
            }
        } catch (err) {
            console.error("Upload failed", err);
            alert("Image upload failed");
        } finally {
            isUploading = false;
            imageBtn.innerHTML = `<i class="ri-image-add-line"></i>`;
            imageInput.value = "";
        }
    });
});
