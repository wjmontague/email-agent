// Email Helper Bot JavaScript with Rich Text Formatting
document.addEventListener("DOMContentLoaded", function() {
    // Enhanced initial message with formatting
    const welcomeMessage = `👋 **Hi! I'm your Email System Learning Assistant.**

I can help you understand and use your email classification system, dashboard features, and more.

**Quick topics I can help with:**
- 📧 Email classification and categories
- ⚡ Priority levels and urgency
- 📊 Dashboard navigation and features  
- 💬 Composing and replying to emails
- 🔍 Search and filtering options

**What would you like to learn about?**`;
    
    addBotMessage(welcomeMessage);
    
    // Focus on input
    document.getElementById('chat-input').focus();
});

// Enhanced message rendering with HTML support
function addMessage(message, isUser = false) {
    const chatBody = document.getElementById('chat-body');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'bot'}`;
    
    // Use innerHTML with proper formatting
    if (isUser) {
        // Keep user messages secure but allow basic HTML entities
        messageDiv.innerHTML = `<i class="fas fa-user"></i> ${escapeHtml(message)}`;
    } else {
        // Allow rich formatting for bot messages
        messageDiv.innerHTML = `<i class="fas fa-robot"></i> ${formatBotMessage(message)}`;
    }
    
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    return messageDiv;
}

function formatBotMessage(message) {
    // Convert common markdown-like formatting to HTML
    return message
        // Bold text: **text** or __text__
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        
        // Italic text: *text* or _text_ (but not if already in HTML tags)
        .replace(/(?<!<[^>]*)\*(.*?)\*(?![^<]*>)/g, '<em>$1</em>')
        .replace(/(?<!<[^>]*)\b_(.*?)_\b(?![^<]*>)/g, '<em>$1</em>')
        
        // Code blocks: `code`
        .replace(/`(.*?)`/g, '<code class="inline-code">$1</code>')
        
        // Line breaks (double line breaks become paragraph breaks)
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        
        // Wrap in paragraph tags if there are paragraph breaks
        .replace(/^(.*)$/s, function(match) {
            if (match.includes('</p><p>')) {
                return '<p>' + match + '</p>';
            }
            return match;
        })
        
        // Numbered lists: 1. item
        .replace(/^\d+\.\s(.+)$/gm, '<div class="list-item numbered">$1</div>')
        
        // Bullet points: - item or • item
        .replace(/^[-•]\s(.+)$/gm, '<div class="list-item bullet">• $1</div>')
        
        // Headings: ### Heading
        .replace(/^###\s(.+)$/gm, '<h6 class="bot-heading">$1</h6>')
        .replace(/^##\s(.+)$/gm, '<h5 class="bot-heading">$1</h5>')
        .replace(/^#\s(.+)$/gm, '<h4 class="bot-heading">$1</h4>')
        
        // Links: [text](url)
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="bot-link">$1 <i class="fas fa-external-link-alt"></i></a>')
        
        // Email addresses
        .replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '<a href="mailto:$1" class="bot-link">$1</a>')
        
        // Highlight priority levels with badges
        .replace(/\b(Critical|High|Medium|Low)(\s+Priority)?/gi, function(match, priority) {
            return `<span class="priority-badge priority-${priority.toLowerCase()}">${priority}</span>`;
        })
        
        // Highlight important UI terms
        .replace(/\b(Dashboard|Email Classification|Category|Categories|Priority|Priorities)\b/gi, '<span class="highlight-term">$1</span>')
        
        // Highlight button/UI element names in quotes or backticks
        .replace(/'([^']+)'/g, '<code class="ui-element">$1</code>')
        
        // Clean up any double spaces that might have been created
        .replace(/\s+/g, ' ')
        .trim();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addUserMessage(message) {
    return addMessage(message, true);
}

function addBotMessage(message) {
    return addMessage(message, false);
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

        // Add bot response with formatting
        addBotMessage(data.answer);

        // Enhanced contextual suggestions
        if (Math.random() < 0.3) {
            setTimeout(() => {
                const suggestions = getContextualSuggestions(message.toLowerCase());
                addBotMessage(`💡 *${suggestions}*`);
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        thinkingMsg.remove();
        addBotMessage(`❌ **Sorry, I encountered an error:** ${error.message}. Please try again.`);
    });

    // Clear input
    input.value = '';
}

// Enhanced contextual suggestions based on user's question
function getContextualSuggestions(userMessage) {
    if (userMessage.includes('dashboard')) {
        return "You might also want to ask about email priorities, category filters, or quick actions.";
    } else if (userMessage.includes('priority') || userMessage.includes('critical') || userMessage.includes('high')) {
        return "Try asking about dashboard navigation, email categories, or how to reply to urgent emails.";
    } else if (userMessage.includes('classification') || userMessage.includes('category')) {
        return "Consider asking about priority levels, dashboard features, or email workflows.";
    } else if (userMessage.includes('reply') || userMessage.includes('respond')) {
        return "You might want to learn about email templates, priority management, or dashboard shortcuts.";
    } else {
        const genericSuggestions = [
            "You might also want to ask about email priorities, dashboard navigation, or reply features.",
            "Consider asking about email categories, search functions, or automated processing.",
            "Try asking about priority levels, classification rules, or workflow management.",
            "You might find it helpful to learn about dashboard filters, quick actions, or reporting features."
        ];
        return genericSuggestions[Math.floor(Math.random() * genericSuggestions.length)];
    }
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
            addBotMessage("📝 *That's quite a long message! I'll do my best to help with your detailed question.*");
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

// Enhanced helpful tips with formatting
const helpfulTips = [
    "💡 **Tip:** Use the email **Priority** filters on your dashboard to quickly find urgent items!",
    "🎯 **Pro tip:** The **'Requires Action'** filter shows emails that need your response.",
    "📊 **Did you know?** Your dashboard shows *real-time* email statistics and trends.",
    "⚡ **Quick tip:** You can reply directly from the email view without switching screens.",
    "🔍 **Helpful hint:** Use the search function to find specific emails quickly.",
    "🏷️ **Classification tip:** The system learns from your manual corrections to improve accuracy.",
    "📝 **Workflow tip:** Use email templates for faster responses to common requests.",
    "🔄 **Processing tip:** Email classification runs automatically every 30 minutes.",
];

// Show random tip occasionally with better timing
setInterval(() => {
    if (Math.random() < 0.08 && document.querySelectorAll('.chat-message').length > 4) {
        const randomTip = helpfulTips[Math.floor(Math.random() * helpfulTips.length)];
        setTimeout(() => {
            addBotMessage(randomTip);
        }, Math.random() * 2000); // Random delay up to 2 seconds
    }
}, 45000); // Every 45 seconds, 8% chance

// Add smooth scrolling animation
function smoothScrollToBottom() {
    const chatBody = document.getElementById('chat-body');
    chatBody.scrollTo({
        top: chatBody.scrollHeight,
        behavior: 'smooth'
    });
}

// Enhanced message animation
function addMessageWithAnimation(messageDiv) {
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
        messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
        smoothScrollToBottom();
    }, 50);
}