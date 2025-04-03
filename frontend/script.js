const API_URL = 'http://localhost:5001/api/chat';

window.addEventListener('DOMContentLoaded', checkApiConnection);

async function checkApiConnection() {
  const statusIndicator = document.getElementById('apiStatus');
  
  try {
    const response = await fetch(API_URL, {
      method: 'OPTIONS',
      headers: {
        'Content-Type': 'application/json'
      },
      mode: 'cors'
    });
    
    if (response.ok) {
      console.log('API connection successful');
      statusIndicator.textContent = 'API: Connected';
      statusIndicator.className = 'api-status connected';
      
      loadWelcomeMessage();
    } else {
      throw new Error('API responded with status: ' + response.status);
    }
  } catch (error) {
    console.warn('API connection failed:', error);
    statusIndicator.textContent = 'API: Disconnected';
    statusIndicator.className = 'api-status disconnected';
    
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = `
      <div class="message bot-message">
        <div class="message-bubble bot-bubble error-message">
          Unable to connect to customer service. Please try again later or contact us at support@ssense.com.
        </div>
      </div>
    `;
  }
  
  setTimeout(() => {
    statusIndicator.style.opacity = '0.6';
  }, 5000);
}

async function loadWelcomeMessage() {
  try {
    const response = await fetch(`${API_URL}/welcome`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      mode: 'cors'
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = `
      <div class="message bot-message">
        <div class="message-bubble bot-bubble">
          ${data.message || 'Welcome to SSENSE support. How can I help you today?'}
        </div>
      </div>
    `;
  } catch (error) {
    console.error('Error loading welcome message:', error);
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = `
      <div class="message bot-message">
        <div class="message-bubble bot-bubble">
          Welcome to SSENSE support. Please connect to our server to chat with us.
        </div>
      </div>
    `;
  }
}

function toggleChat() {
  const chat = document.getElementById("chatBox");
  const messages = document.getElementById("chatMessages");
  
  const computedStyle = window.getComputedStyle(chat);
  const isVisible = computedStyle.display !== "none";
  
  chat.style.display = isVisible ? "none" : "flex";
  
  if (!isVisible) {
    requestAnimationFrame(() => {
      messages.scrollTop = messages.scrollHeight;
    });
  }
}

function addUserMessage(message) {
  const chatMessages = document.getElementById("chatMessages");
  const messageElement = document.createElement("div");
  messageElement.className = "message user-message";
  messageElement.innerHTML = `
    <div class="message-bubble user-bubble">
      ${escapeHtml(message)}
    </div>
  `;
  chatMessages.appendChild(messageElement);
  scrollToBottom();
}

function addBotMessage(message) {
  const chatMessages = document.getElementById("chatMessages");
  const messageElement = document.createElement("div");
  messageElement.className = "message bot-message";
  messageElement.innerHTML = `
    <div class="message-bubble bot-bubble">
      ${message}
    </div>
  `;
  chatMessages.appendChild(messageElement);
  scrollToBottom();
}

function addErrorMessage(message) {
  const chatMessages = document.getElementById("chatMessages");
  const messageElement = document.createElement("div");
  messageElement.className = "message bot-message";
  messageElement.innerHTML = `
    <div class="message-bubble bot-bubble error-message">
      ${message}
    </div>
  `;
  chatMessages.appendChild(messageElement);
  scrollToBottom();
}

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showTypingIndicator() {
  const typingIndicator = document.getElementById("typingIndicator");
  typingIndicator.style.display = "block";
  scrollToBottom();
}

function hideTypingIndicator() {
  const typingIndicator = document.getElementById("typingIndicator");
  typingIndicator.style.display = "none";
}

function scrollToBottom() {
  const chatMessages = document.getElementById("chatMessages");
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function callChatApi(message) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
    mode: 'cors'
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  return data.response;
}

async function sendMessage(event) {
  event.preventDefault();
  
  const messageInput = document.getElementById("messageInput");
  const userMessage = messageInput.value.trim();
  
  if (userMessage === "") return;
  
  addUserMessage(userMessage);
  messageInput.value = "";
  
  showTypingIndicator();
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userMessage }),
      mode: 'cors',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    
    hideTypingIndicator();
    
    addBotMessage(data.response);
  } catch (error) {
    hideTypingIndicator();
    
    console.error("Error sending message:", error);
    
    if (error.name === 'AbortError') {
      addErrorMessage("Our service is taking longer than expected to respond. Please try again or contact us directly at support@ssense.com.");
    } else {
      addErrorMessage("We're experiencing technical difficulties. Please try again later or email us at support@ssense.com.");
    }
    
    document.getElementById('apiStatus').textContent = 'API: Error';
    document.getElementById('apiStatus').className = 'api-status disconnected';
    document.getElementById('apiStatus').style.opacity = '1';
  }
}