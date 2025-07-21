// Email Helper Bot JavaScript
document.addEventListener("DOMContentLoaded", function() {
    // Initial bot message
    addBotMessage("👋 Hi! I'm your Email System Learning Assistant. I can help you understand and use your email classification system, dashboard features, and more. What would you like to learn about?");

    // Focus on input
    document.getElementById('chat-input').focus();
});

function addMessage(message, isUser = false) {
    const chatBody = document.getElementById('chat-body');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'bot'}`;
    messageDiv.innerHTML = message;
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    return messageDiv;
}

function addUserMessage(message) {
    return addMessage(`<i class="fas fa-user"></i> ${message}`, true);
}

function addBotMessage(message) {
    return addMessage(`<i class="fas fa-robot"></i> ${message}`, false);
}

function addThinkingMessage() {
    const messageDiv = addBotMessage('<i class="fas fa-spinner fa-spin"></i> Thinking...');
    messageDiv.classList.add('thinking');
    return messageDiv;
}

function handleInput(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}

function sendInput() {
    sendMessage();
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    const lang = document.getElementById('language-select').value;

    if (!message) return;

    // Add user message
    addUserMessage(message);

    // Add thinking message
    const thinkingMsg = addThinkingMessage();

    // Send to server
    fetch("/helper_bot/email-helper-chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({
            question: message,
            language: lang
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Remove thinking message
        thinkingMsg.remove();

        // Add bot response
        addBotMessage(data.answer);

        // Suggest related questions occasionally
        if (Math.random() < 0.3) {
            setTimeout(() => {
                addBotMessage("💡 <em>You might also want to ask about email priorities, dashboard navigation, or how to reply to classified emails.</em>");
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        thinkingMsg.remove();
        addBotMessage(`❌ Sorry, I encountered an error: ${error.message}. Please try again.`);
    });

    // Clear input
    input.value = '';
}

function askQuestion(question) {
    const input = document.getElementById('chat-input');
    input.value = question;
    sendMessage();
}

function returnToDashboard() {
    if (confirm('Return to the main dashboard?')) {
        window.location.href = '/dashboard';
    }
}

// Auto-resize chat input and handle paste events
document.getElementById('chat-input').addEventListener('paste', function() {
    setTimeout(() => {
        if (this.value.length > 200) {
            addBotMessage("📝 <em>That's quite a long message! I'll do my best to help with your detailed question.</em>");
        }
    }, 100);
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape to return to dashboard
    if (e.key === 'Escape') {
        returnToDashboard();
    }

    // Ctrl/Cmd + K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('chat-input').focus();
    }
});

// Add some personality with random helpful tips
const helpfulTips = [
    "💡 Tip: Use the email priority filters on your dashboard to quickly find urgent items!",
    "🎯 Pro tip: The 'Requires Action' filter shows emails that need your response.",
    "📊 Did you know? Your dashboard shows real-time email statistics and trends.",
    "⚡ Quick tip: You can reply directly from the email view without switching screens.",
    "🔍 Helpful hint: Use the search function to find specific emails quickly.",
];

// Show random tip occasionally
setInterval(() => {
    if (Math.random() < 0.1 && document.querySelectorAll('.chat-message').length > 4) {
        const randomTip = helpfulTips[Math.floor(Math.random() * helpfulTips.length)];
        addBotMessage(randomTip);
    }
}, 30000); // Every 30 seconds, 10% chance