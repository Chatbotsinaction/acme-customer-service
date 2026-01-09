const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

// Replace with your deployed Rasa server URL
const RASA_SERVER_URL = 'https://acme-rasa-server.onrender.com';
const sender_id = 'user_' + Math.random().toString(36).substr(2, 9);

// Add initial greeting
window.addEventListener('DOMContentLoaded', () => {
    addBotMessage("Hi, welcome to ACME customer service. I can help with orders and product information. What do you need?");
});

function addMessage(text, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addBotMessage(text) {
    addMessage(text, false);
}

function addUserMessage(text) {
    addMessage(text, true);
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot';
    typingDiv.id = 'typing-indicator';
    
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'typing-indicator';
    indicatorDiv.innerHTML = '<span></span><span></span><span></span>';
    
    typingDiv.appendChild(indicatorDiv);
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    addUserMessage(message);
    userInput.value = '';
    
    showTypingIndicator();
    
    try {
        const response = await fetch(`${RASA_SERVER_URL}/webhooks/rest/webhook`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender: sender_id,
                message: message
            })
        });
        
        removeTypingIndicator();
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        
        if (data && data.length > 0) {
            data.forEach(msg => {
                if (msg.text) {
                    addBotMessage(msg.text);
                }
            });
        } else {
            addBotMessage("I'm sorry, I didn't understand that. Could you rephrase?");
        }
    } catch (error) {
        removeTypingIndicator();
        console.error('Error:', error);
        addBotMessage("Sorry, I'm having trouble connecting to the server. Please try again later.");
    }
}

sendButton.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }

});
