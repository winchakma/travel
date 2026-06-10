document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("gotrip-ai-chatbot")) return;

    const chatbotHTML = `
    <div id="gotrip-ai-chatbot" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: 'Inter', sans-serif;">
        <div id="chatbot-window" style="display: none; width: 350px; height: 500px; background: white; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); flex-direction: column; overflow: hidden; margin-bottom: 15px; border: 1px solid #eee;">
            <div style="background: #1a2b6b; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 32px; height: 32px; background: #e5c414; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 16px;">✨</div>
                    <span style="font-weight: 600; font-size: 16px;">GoTrip AI</span>
                </div>
                <button id="chatbot-close-btn" style="background: transparent; border: none; color: white; cursor: pointer; font-size: 20px;">&times;</button>
            </div>
            <div id="chatbot-messages" style="flex: 1; padding: 15px; overflow-y: auto; background: #f9f9f9; display: flex; flex-direction: column; gap: 10px;">
                <div style="align-self: flex-start; background: #e9ecef; padding: 10px 14px; border-radius: 12px; font-size: 14px; color: #333; max-width: 80%;">
                    Hello! I'm your GoTrip AI Travel Assistant. How can I help you plan your next adventure?
                </div>
            </div>
            <div style="padding: 15px; background: white; border-top: 1px solid #eee; display: flex; gap: 10px;">
                <input type="text" id="chatbot-input" placeholder="Ask about destinations..." style="flex: 1; padding: 10px 15px; border: 1px solid #ddd; border-radius: 20px; outline: none; font-size: 14px;">
                <button id="chatbot-send-btn" style="background: #e5c414; color: #1a2b6b; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; display: flex; justify-content: center; align-items: center; font-weight: bold;">➤</button>
            </div>
        </div>
        <button id="chatbot-toggle-btn" style="width: 60px; height: 60px; background: #e5c414; color: #1a2b6b; border: none; border-radius: 50%; box-shadow: 0 4px 15px rgba(0,0,0,0.2); cursor: pointer; display: flex; justify-content: center; align-items: center; font-size: 28px; float: right; transition: transform 0.2s;">
            ✨
        </button>
    </div>
    `;

    document.body.insertAdjacentHTML('beforeend', chatbotHTML);

    const toggleBtn = document.getElementById("chatbot-toggle-btn");
    const closeBtn = document.getElementById("chatbot-close-btn");
    const chatWindow = document.getElementById("chatbot-window");
    const sendBtn = document.getElementById("chatbot-send-btn");
    const inputField = document.getElementById("chatbot-input");
    const messagesContainer = document.getElementById("chatbot-messages");

    let chatHistory = [];

    toggleBtn.addEventListener("click", () => {
        chatWindow.style.display = chatWindow.style.display === "none" ? "flex" : "none";
        if (chatWindow.style.display === "flex") {
            inputField.focus();
        }
    });

    closeBtn.addEventListener("click", () => {
        chatWindow.style.display = "none";
    });

    function appendMessage(text, isUser) {
        const msgDiv = document.createElement("div");
        msgDiv.style.alignSelf = isUser ? "flex-end" : "flex-start";
        msgDiv.style.background = isUser ? "#1a2b6b" : "#e9ecef";
        msgDiv.style.color = isUser ? "white" : "#333";
        msgDiv.style.padding = "10px 14px";
        msgDiv.style.borderRadius = "12px";
        msgDiv.style.fontSize = "14px";
        msgDiv.style.maxWidth = "80%";
        msgDiv.style.lineHeight = "1.4";
        
        // Simple markdown parsing for bold and links
        let parsedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        parsedText = parsedText.replace(/\n/g, "<br>");
        
        msgDiv.innerHTML = parsedText;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
        const text = inputField.value.trim();
        if (!text) return;

        appendMessage(text, true);
        inputField.value = "";
        
        inputField.disabled = true;
        sendBtn.disabled = true;
        
        const typingId = "typing-" + Date.now();
        messagesContainer.insertAdjacentHTML('beforeend', `<div id="${typingId}" style="align-self: flex-start; font-size: 12px; color: #888;">AI is thinking...</div>`);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const apiBase = window.ELITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:10000' : 'https://travel-xyyl.onrender.com');
            const response = await fetch(apiBase + "/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, history: chatHistory })
            });

            const data = await response.json();
            document.getElementById(typingId)?.remove();
            
            if (response.ok && data.response) {
                appendMessage(data.response, false);
                chatHistory.push({ role: "user", text: text });
                chatHistory.push({ role: "model", text: data.response });
            } else {
                appendMessage("Error: Could not process request.", false);
            }
        } catch (error) {
            document.getElementById(typingId)?.remove();
            appendMessage("Connection error. Please try again.", false);
        } finally {
            inputField.disabled = false;
            sendBtn.disabled = false;
            inputField.focus();
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    inputField.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});
