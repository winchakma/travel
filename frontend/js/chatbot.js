document.addEventListener('DOMContentLoaded', () => {
    const chatbotContainer = document.createElement('div');
    chatbotContainer.className = 'chatbot-container';
    
    chatbotContainer.innerHTML = `
        <div class="chatbot-bubble" id="chatbotBubble">
            <div class="neural-pulse"></div>
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
        </div>
        <div class="chatbot-window" id="chatbotWindow">
            <div class="chatbot-header">
                <h3>Neural Assistant HUD</h3>
                <span class="close-chat" id="closeChat">&times;</span>
            </div>
            <div class="chatbot-messages" id="chatMessages">
                <div class="message bot">System Online. I am your East Blue Neural Assistant. How can I optimize your performance today?</div>
            </div>
            <div class="typing" id="typingIndicator">Analyzing biological data...</div>
            
            <div class="quick-replies">
                <div class="reply-chip" onclick="handleQuickReply('Diet for 90kg to 60kg')">Transformation</div>
                <div class="reply-chip" onclick="handleQuickReply('Elite Protein Plan')">Protein Sync</div>
                <div class="reply-chip" onclick="handleQuickReply('Muscle Gain Diet')">Bulk Mode</div>
                <div class="reply-chip" onclick="handleQuickReply('Membership')">Membership</div>
            </div>

            <form class="chatbot-input" id="chatbotForm">
                <input type="text" id="chatInput" placeholder="Enter biological data (e.g. 90kg)..." required autocomplete="off">
                <button type="submit">
                    <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </form>
        </div>
    `;

    document.body.appendChild(chatbotContainer);

    const bubble = document.getElementById('chatbotBubble');
    const chatWindow = document.getElementById('chatbotWindow');
    const closeBtn = document.getElementById('closeChat');
    const form = document.getElementById('chatbotForm');
    const input = document.getElementById('chatInput');
    const messagesContainer = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');

    let chatHistory = [];

    // Local Intelligence Database has been replaced by the World Library API

    bubble.addEventListener('click', () => {
        chatWindow.classList.toggle('active');
        document.body.classList.toggle('chatbot-is-open', chatWindow.classList.contains('active'));
        if (chatWindow.classList.contains('active')) {
            input.focus();
        }
    });

    closeBtn.addEventListener('click', () => {
        chatWindow.classList.remove('active');
        document.body.classList.remove('chatbot-is-open');
    });

    window.handleQuickReply = (text) => {
        input.value = text;
        form.dispatchEvent(new Event('submit'));
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        input.value = '';
        typingIndicator.style.display = 'block';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Simulate Neural Processing Delay for UI feel
        setTimeout(async () => {
            let reply = "Neural Link failed. Please check your connection.";
            
            try {
                const API_URL = window.ELITE_API_URL || '';
                if (!API_URL) {
                    reply = 'Backend URL not configured. Check js/config.js on this deployment.';
                } else {
                    let response = await fetch(`${API_URL}/api/chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message, history: chatHistory })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        reply = data.reply || data.response || data.detail || reply;
                    } else {
                        console.error("Backend returned error:", response.status);
                        reply = 'Neural connection interrupted. Try again in a moment.';
                    }
                }
            } catch (err) {
                console.error("Brain connection failed:", err);
                reply = 'Neural link offline. The backend may be waking up (Render) — try again in 30 seconds.';
            }

            addMessage(reply, 'bot');
            chatHistory.push({ role: 'user', text: message });
            chatHistory.push({ role: 'bot', text: reply });
            if (typeof window.logActivity === 'function') window.logActivity('AI HUD Consultation');
            
            typingIndicator.style.display = 'none';
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 500);
    });

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.textContent = text;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
