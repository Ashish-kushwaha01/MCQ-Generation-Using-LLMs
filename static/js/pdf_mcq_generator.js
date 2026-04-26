document.addEventListener('DOMContentLoaded', function() {
    const chatbotIcon = document.getElementById('chatbotIcon');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatbotCloseBtn = document.getElementById('chatbotCloseBtn');
    const showAnswersBtn = document.querySelector('.btn-show-answers');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotSendBtn = document.getElementById('chatbotSendBtn');
    const chatbotBody = document.getElementById('chatbotBody');
    const currentSessionIdInput = document.getElementById('currentSessionId');
    // const chatbotLoading = document.getElementById('chatbotLoading'); // Removed static loading element

    // Function to show the chatbot icon
    function showChatbotIcon() {
        if (chatbotIcon) {
            chatbotIcon.style.display = 'flex';
        }
    }

    // Event listener for the "Show All Answers" button
    if (showAnswersBtn) {
        showAnswersBtn.addEventListener('click', showChatbotIcon);
    }

    // Event listener to toggle chatbot window visibility
    if (chatbotIcon) {
        chatbotIcon.addEventListener('click', function() {
            if (chatbotWindow) {
                chatbotWindow.style.display = chatbotWindow.style.display === 'none' ? 'flex' : 'none';
            }
        });
    }

    // Event listener to close chatbot window
    if (chatbotCloseBtn) {
        chatbotCloseBtn.addEventListener('click', function(event) {
            event.stopPropagation();
            if (chatbotWindow) {
                chatbotWindow.style.display = 'none';
            }
        });
    }

    // Function to append a message to the chatbot body
    function appendMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', `${sender}-message`);
        messageDiv.textContent = message;
        chatbotBody.appendChild(messageDiv);
        chatbotBody.scrollTop = chatbotBody.scrollHeight; // Auto-scroll to the bottom
    }

    // Function to send a message to the chatbot API
    async function sendMessage() {
        const question = chatbotInput.value.trim();
        if (!question) return;

        appendMessage('user', question);
        chatbotInput.value = ''; // Clear input

        // Dynamically create and show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.classList.add('chatbot-loading');
        loadingIndicator.innerHTML = '<span></span><span></span><span></span>';
        chatbotBody.appendChild(loadingIndicator);
        chatbotBody.scrollTop = chatbotBody.scrollHeight; // Scroll to show loader

        const sessionId = currentSessionIdInput ? currentSessionIdInput.value : null;

        try {
            const response = await fetch('/pdf_mcq/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Function to get CSRF token
                },
                body: JSON.stringify({ question: question, session_id: sessionId })
            });

            const data = await response.json();
            if (data.status === 'success') {
                appendMessage('bot', data.response);
            } else {
                appendMessage('bot', `Error: ${data.message}`);
            }
        } catch (error) {
            console.error('Error sending message to chatbot:', error);
            appendMessage('bot', 'Sorry, something went wrong. Please try again.');
        } finally {
            // Hide and remove loading indicator
            if (loadingIndicator && loadingIndicator.parentNode) {
                loadingIndicator.parentNode.removeChild(loadingIndicator);
            }
        }
    }

    // Event listener for send button
    if (chatbotSendBtn) {
        chatbotSendBtn.addEventListener('click', sendMessage);
    }

    // Event listener for Enter key in input field
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Function to scroll to the questions section (made global)
    window.scrollToQuestions = function() {
        const currentConversation = document.getElementById('currentConversation');
        if (currentConversation) {
            currentConversation.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    // --- Resizing Logic ---
    const resizeHandles = document.querySelectorAll('.resize-handle');
    let isResizing = false;
    let currentHandle = null;
    let startX, startY, startWidth, startHeight, startLeft, startTop;

    function startResize(e) {
        isResizing = true;
        currentHandle = e.target;
        startX = e.clientX;
        startY = e.clientY;

        const rect = chatbotWindow.getBoundingClientRect();
        startWidth = rect.width;
        startHeight = rect.height;
        startLeft = rect.left;
        startTop = rect.top;

        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', stopResize);
        document.body.style.userSelect = 'none'; // Prevent text selection during resize
        document.body.style.cursor = currentHandle.style.cursor; // Set cursor for dragging
    }

    function resize(e) {
        if (!isResizing) return;

        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        let newWidth = startWidth;
        let newHeight = startHeight;
        let newLeft = startLeft;
        let newTop = startTop;

        const minWidth = 300; // Should match CSS min-width
        const minHeight = 300; // Should match CSS min-height
        const maxWidth = window.innerWidth * 0.9; // Should match CSS max-width
        const maxHeight = window.innerHeight * 0.9; // Should match CSS max-height

        if (currentHandle.classList.contains('bottom-right') || currentHandle.classList.contains('right')) {
            newWidth = Math.min(Math.max(startWidth + dx, minWidth), maxWidth);
        }
        if (currentHandle.classList.contains('bottom-right') || currentHandle.classList.contains('bottom')) {
            newHeight = Math.min(Math.max(startHeight + dy, minHeight), maxHeight);
        }
        if (currentHandle.classList.contains('top-left') || currentHandle.classList.contains('left')) {
            newWidth = Math.min(Math.max(startWidth - dx, minWidth), maxWidth);
            newLeft = startLeft + startWidth - newWidth;
        }
        if (currentHandle.classList.contains('top-left') || currentHandle.classList.contains('top')) {
            newHeight = Math.min(Math.max(startHeight - dy, minHeight), maxHeight);
            newTop = startTop + startHeight - newHeight;
        }
        if (currentHandle.classList.contains('top-right')) {
            newWidth = Math.min(Math.max(startWidth + dx, minWidth), maxWidth);
            newHeight = Math.min(Math.max(startHeight - dy, minHeight), maxHeight);
            newTop = startTop + startHeight - newHeight;
        }
        if (currentHandle.classList.contains('bottom-left')) {
            newWidth = Math.min(Math.max(startWidth - dx, minWidth), maxWidth);
            newLeft = startLeft + startWidth - newWidth;
            newHeight = Math.min(Math.max(startHeight + dy, minHeight), maxHeight);
        }

        chatbotWindow.style.width = `${newWidth}px`;
        chatbotWindow.style.height = `${newHeight}px`;
        chatbotWindow.style.left = `${newLeft}px`;
        chatbotWindow.style.top = `${newTop}px`;
    }

    function stopResize() {
        isResizing = false;
        currentHandle = null;
        document.removeEventListener('mousemove', resize);
        document.removeEventListener('mouseup', stopResize);
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
    }

    resizeHandles.forEach(handle => {
        handle.addEventListener('mousedown', startResize);
    });
});