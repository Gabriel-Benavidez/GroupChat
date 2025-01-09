document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const authorInput = document.getElementById('author-input');
    const messagesContainer = document.getElementById('messages');
    const pushButton = document.createElement('button');
    
    // Add Push to GitHub button
    pushButton.textContent = 'Push to GitHub';
    pushButton.className = 'push-button';
    document.body.appendChild(pushButton);

    // Handle message submission
    messageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        const author = authorInput.value.trim() || 'Anonymous';
        
        if (!message) return;
        
        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    author: author
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                messageInput.value = '';
                loadMessages();
            } else {
                alert('Error: ' + result.message);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Error sending message. Check console for details.');
        }
    });

    // Handle Push to GitHub
    pushButton.addEventListener('click', async function() {
        try {
            const response = await fetch('/push_to_github', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                alert('Messages successfully pushed to GitHub!');
            } else {
                alert('Error pushing to GitHub: ' + result.message);
            }
        } catch (error) {
            console.error('Error pushing to GitHub:', error);
            alert('Error pushing to GitHub. Check console for details.');
        }
    });

    // Load messages
    async function loadMessages() {
        try {
            const response = await fetch('/get_messages');
            const data = await response.json();
            
            messagesContainer.innerHTML = '';
            
            data.messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                messageDiv.innerHTML = `
                    <strong>${msg.author}</strong> 
                    <small>${new Date(msg.timestamp).toLocaleString()}</small>
                    <p>${msg.content}</p>
                `;
                messagesContainer.appendChild(messageDiv);
            });
        } catch (error) {
            console.error('Error loading messages:', error);
            messagesContainer.innerHTML = '<p>Error loading messages</p>';
        }
    }

    // Initial load of messages
    loadMessages();
});
