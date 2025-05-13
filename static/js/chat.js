document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const messagesLeftBadge = document.getElementById('messages-left-badge');
    const messagesLeftCount = document.getElementById('messages-left-count');
    const voicePlayer = document.getElementById('voice-player');
    
    // User ID from session or generate new one
    const userId = localStorage.getItem('user_id') || generateUUID();
    localStorage.setItem('user_id', userId);
    
    // Keep track of messages locally
    let messageCount = 0;
    let messagesLeft = 50;
    let isPremium = false;
    
    // Load chat history
    loadChatHistory();
    
    // Event listener for sending messages
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Clear input field
        messageInput.value = '';
        
        // Add user message to chat
        addMessageToChat(message, true);
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to backend
        sendMessage(message);
    });
    
    // Function to load chat history
    function loadChatHistory() {
        fetch('/history')
            .then(response => response.json())
            .then(data => {
                // Clear any existing messages
                chatMessages.innerHTML = '';
                
                // Update user status
                isPremium = data.is_premium || false;
                messageCount = data.message_count || 0;
                messagesLeft = data.messages_left || 50;
                
                // Update messages left badge
                updateMessagesLeftBadge();
                
                // Add messages to the chat
                if (data.history && data.history.length > 0) {
                    data.history.forEach(msg => {
                        // Check if message has audio
                        const audioUrl = msg.has_audio ? msg.audio_url : null;
                        addMessageToChat(msg.content, msg.is_user, false, audioUrl);
                    });
                    
                    // Scroll to the bottom
                    scrollToBottom();
                } else {
                    // Add introduction message if no history
                    const introDiv = document.createElement('div');
                    introDiv.classList.add('text-center', 'mb-4');
                    introDiv.innerHTML = `
                        <div class="sophia-intro mb-3">
                            <i class="fas fa-heart text-danger mb-3 fa-2x"></i>
                            <h5>Welcome to Sophia's Chat</h5>
                            <p class="text-muted">I'm excited to get to know you better... 😘</p>
                        </div>
                    `;
                    chatMessages.appendChild(introDiv);
                }
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
                addErrorMessage('Failed to load chat history. Please refresh the page.');
            });
    }
    
    // Function to send message to backend
    function sendMessage(message) {
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                user_id: userId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            if (data.error) {
                console.error('Error from server:', data.error);
                addErrorMessage('Sorry, I\'m having trouble responding right now.');
            } else {
                // Check if premium and if there's audio
                const audioUrl = data.audio_url || null;
                
                // Add Sophia's response to chat
                addMessageToChat(data.response, false, true, audioUrl);
                
                // Update premium status
                isPremium = data.is_premium || false;
                
                // Update message count and messages left
                messageCount = data.message_count || 0;
                messagesLeft = data.messages_left || 0;
                updateMessagesLeftBadge();
                
                // Auto-play audio if enabled
                if (audioUrl && voiceEnabled && voicePlayer) {
                    playAudio(audioUrl);
                }
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            removeTypingIndicator();
            addErrorMessage('Network error. Please try again later.');
        });
    }
    
    // Function to add message to chat
    function addMessageToChat(message, isUser, shouldScroll = true, audioUrl = null) {
        const messageEl = document.createElement('div');
        messageEl.classList.add('message', isUser ? 'user-message' : 'sophia-message');
        
        const contentEl = document.createElement('div');
        contentEl.classList.add('message-content');
        contentEl.textContent = message;
        
        const timeEl = document.createElement('div');
        timeEl.classList.add('message-time');
        timeEl.textContent = formatTime(new Date());
        
        messageEl.appendChild(contentEl);
        
        // Add voice indicator for premium users
        if (!isUser && audioUrl) {
            const voiceEl = document.createElement('span');
            voiceEl.classList.add('voice-indicator');
            voiceEl.innerHTML = '<i class="fas fa-volume-up"></i>';
            voiceEl.title = 'Play voice message';
            voiceEl.dataset.audioUrl = audioUrl;
            
            // Add click event to play audio
            voiceEl.addEventListener('click', function() {
                playAudio(this.dataset.audioUrl);
            });
            
            timeEl.appendChild(document.createTextNode(' '));
            timeEl.appendChild(voiceEl);
        }
        
        messageEl.appendChild(timeEl);
        chatMessages.appendChild(messageEl);
        
        if (shouldScroll) {
            scrollToBottom();
        }
    }
    
    // Function to play audio
    function playAudio(url) {
        if (!voicePlayer) return;
        
        voicePlayer.src = url;
        voicePlayer.classList.remove('d-none');
        
        // Play audio
        voicePlayer.play().catch(err => {
            console.error('Error playing audio:', err);
        });
    }
    
    // Function to add error message
    function addErrorMessage(message) {
        const errorEl = document.createElement('div');
        errorEl.classList.add('alert', 'alert-danger', 'mt-2');
        errorEl.textContent = message;
        
        chatMessages.appendChild(errorEl);
        scrollToBottom();
        
        // Remove error after 5 seconds
        setTimeout(() => {
            errorEl.remove();
        }, 5000);
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        const typingEl = document.createElement('div');
        typingEl.classList.add('typing-indicator', 'sophia-message');
        typingEl.id = 'typing-indicator';
        
        const contentEl = document.createElement('div');
        contentEl.classList.add('message-content');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            contentEl.appendChild(dot);
        }
        
        typingEl.appendChild(contentEl);
        chatMessages.appendChild(typingEl);
        scrollToBottom();
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const typingEl = document.getElementById('typing-indicator');
        if (typingEl) typingEl.remove();
    }
    
    // Function to scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to update messages left badge
    function updateMessagesLeftBadge() {
        if (isPremium) {
            // Premium users have unlimited messages
            if (messagesLeftBadge) {
                messagesLeftBadge.textContent = 'Unlimited';
                messagesLeftBadge.classList.remove('bg-warning', 'bg-danger');
                messagesLeftBadge.classList.add('bg-success');
            }
        } else {
            // Free users have limited messages
            if (messagesLeftCount) {
                messagesLeftCount.textContent = messagesLeft;
            }
            
            // Update badge color based on messages left
            if (messagesLeftBadge) {
                messagesLeftBadge.classList.remove('bg-success', 'bg-warning', 'bg-danger');
                
                if (messagesLeft > 10) {
                    messagesLeftBadge.classList.add('bg-success');
                } else if (messagesLeft > 0) {
                    messagesLeftBadge.classList.add('bg-warning');
                } else {
                    messagesLeftBadge.classList.add('bg-danger');
                }
            }
        }
    }
    
    // Utility function to format time
    function formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Utility function to generate UUID
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    // Enable focus on input when clicking anywhere in the chat area
    chatMessages.addEventListener('click', function(e) {
        // Don't focus if clicking on a button or link
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A' && !e.target.closest('.voice-indicator')) {
            messageInput.focus();
        }
    });
});
