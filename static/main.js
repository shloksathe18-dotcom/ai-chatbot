document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatContainer = document.getElementById('chat-container');

    // Add a message to the chat
    function addMessage(content, isUser = false, sources = [], confidence = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'} mb-4`;
        
        if (isUser) {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-end">
                    <div class="message-content p-3 rounded-3 shadow-sm">
                        <p class="mb-0">${content}</p>
                    </div>
                    <div class="avatar bg-primary text-white rounded-circle d-flex align-items-center justify-content-center ms-3">
                        <span>U</span>
                    </div>
                </div>
            `;
        } else {
            // Bot message with sources
            let sourcesHtml = '';
            if (sources.length > 0) {
                sourcesHtml = '<div class="sources mt-2"><small class="fw-bold">Sources:</small><ul class="mb-0">';
                sources.forEach(source => {
                    sourcesHtml += `<li><a href="${source.url}" target="_blank">${source.title}</a></li>`;
                });
                sourcesHtml += '</ul></div>';
            }
            
            let confidenceBadge = '';
            if (confidence) {
                let badgeClass = 'badge-low';
                if (confidence === 'high') badgeClass = 'badge-high';
                else if (confidence === 'medium') badgeClass = 'badge-medium';
                
                confidenceBadge = `<span class="badge ${badgeClass} ms-2">${confidence}</span>`;
            }
            
            messageDiv.innerHTML = `
                <div class="d-flex">
                    <div class="avatar bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center me-3">
                        <span>A</span>
                    </div>
                    <div class="message-content bg-light p-3 rounded-3 shadow-sm">
                        <p class="mb-0">${content}${confidenceBadge}</p>
                        ${sourcesHtml}
                    </div>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message mb-4';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="d-flex">
                <div class="avatar bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center me-3">
                    <span>A</span>
                </div>
                <div class="message-content bg-light p-3 rounded-3 shadow-sm">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                        <span class="ms-2">Askuno is searching...</span>
                    </div>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }

    // Hide typing indicator
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, true);
        
        // Clear input
        userInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            if (response.ok) {
                const data = await response.json();
                hideTypingIndicator();
                addMessage(data.answer, false, data.sources, data.confidence);
            } else if (response.status === 429) {
                hideTypingIndicator();
                addMessage("Rate limit exceeded. Please wait a moment before sending another message.");
            } else {
                hideTypingIndicator();
                addMessage("Sorry, I encountered an error processing your request.");
            }
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage("Sorry, I encountered an error processing your request.");
        }
    });

    // Scroll to bottom initially
    scrollToBottom();
});