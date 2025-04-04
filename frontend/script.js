const API_URL = 'http://localhost:5001/api/chat';

const explanationPanel = document.getElementById('explanationPanel');
const explanationContent = document.getElementById('explanationContent');
console.log('Initial explanationPanel:', explanationPanel);
console.log('Initial explanationContent:', explanationContent);


window.addEventListener('DOMContentLoaded', checkApiConnection);

async function checkApiConnection() {
  const statusIndicator = document.getElementById('apiStatus');
  try {
    const response = await fetch(API_URL, { method: 'OPTIONS', mode: 'cors' });
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
    displayConnectionError(); 
  }
  setTimeout(() => { statusIndicator.style.opacity = '0.6'; }, 5000);
}

function displayConnectionError() {
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = `
      <div class="message bot-message">
        <div class="message-bubble bot-bubble error-message">
          Unable to connect to customer service. Please try again later or contact us at support@ssense.com.
        </div>
      </div>
    `;
    scrollToBottom(); 
    if (explanationPanel) {
        console.log('Hiding panel due to connection error.');
        explanationPanel.style.display = 'none';
    }
}


async function loadWelcomeMessage() {
  try {
    const response = await fetch(`${API_URL}/welcome`, { method: 'GET', mode: 'cors' });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    const data = await response.json();
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = '';
    addBotMessage(data.message || 'Welcome to SSENSE support. How can I help you today?');
  } catch (error) {
    console.error('Error loading welcome message:', error);
    if (!document.querySelector('.error-message')) {
        addBotMessage('Welcome to SSENSE support. How can I help?');
    }
    if (explanationPanel) {
        console.log('Hiding panel due to welcome message error.');
        explanationPanel.style.display = 'none';
    }
  }
}

function toggleChat() {
  const chat = document.getElementById("chatBox");
  const messages = document.getElementById("chatMessages");
  const computedStyle = window.getComputedStyle(chat);
  const isVisible = computedStyle.display !== "none";

  console.log(`Toggling chat. Currently visible: ${isVisible}`);
  chat.style.display = isVisible ? "none" : "flex";

  if (explanationPanel) {
      if (isVisible) { 
          console.log('Hiding panel because chat is closing.');
          explanationPanel.style.display = "none";
      } else { 
          if (explanationContent && explanationContent.textContent && explanationContent.textContent.trim() !== '') {
              console.log('Showing panel on chat open because it has content.');
              explanationPanel.style.display = "flex";
          } else {
              console.log('Keeping panel hidden on chat open because it is empty.');
              explanationPanel.style.display = "none";
          }
      }
  } else {
      console.warn('toggleChat: explanationPanel element not found!');
  }


  if (!isVisible) { 
    requestAnimationFrame(() => { messages.scrollTop = messages.scrollHeight; });
  }
}

function addBotMessage(message) {
  const chatMessages = document.getElementById("chatMessages");
  const messageContainer = document.createElement("div");
  messageContainer.className = "message bot-message";

  const bubbleElement = document.createElement("div");
  bubbleElement.className = "message-bubble bot-bubble";
  bubbleElement.innerHTML = message; 
  messageContainer.appendChild(bubbleElement);

  chatMessages.appendChild(messageContainer);
  scrollToBottom();
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

function addErrorMessage(message) {
  const chatMessages = document.getElementById("chatMessages");
  const messageElement = document.createElement("div");
  messageElement.className = "message bot-message"; 
  messageElement.innerHTML = `
    <div class="message-bubble bot-bubble error-message">
      ${escapeHtml(message)}
    </div>
  `;
  chatMessages.appendChild(messageElement);
  scrollToBottom();
}

function escapeHtml(unsafe) {
  if (typeof unsafe !== 'string') return '';
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showTypingIndicator() {
  document.getElementById("typingIndicator").style.display = "block";
  scrollToBottom();
}

function hideTypingIndicator() {
  document.getElementById("typingIndicator").style.display = "none";
}

function scrollToBottom() {
  const chatMessages = document.getElementById("chatMessages");
  requestAnimationFrame(() => {
      chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

async function sendMessage(event) {
  event.preventDefault();
  const messageInput = document.getElementById("messageInput");
  const userMessage = messageInput.value.trim();
  if (userMessage === "") return;

  addUserMessage(userMessage);
  messageInput.value = "";
  showTypingIndicator();

  console.log('sendMessage: Clearing/hiding explanation panel for new message.');
  if (explanationContent) explanationContent.textContent = '';
  if (explanationPanel) explanationPanel.style.display = 'none';
  else console.warn('sendMessage: explanationPanel element not found at start!');


  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    console.log('sendMessage: Fetching API response...');
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage }), 
      mode: 'cors',
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    hideTypingIndicator(); 
    console.log('sendMessage: Response status:', response.status);


    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json(); 
    console.log('sendMessage: Received data:', data);

    addBotMessage(data.response);

    const explanationText = data.explanation || null;

    if (explanationText && explanationPanel && explanationContent) {
        console.log('sendMessage: Explanation found. Updating content and showing panel.');
        explanationContent.textContent = explanationText; 
        explanationPanel.style.display = 'flex'; 
        console.log('sendMessage: Panel display set to flex.');
    } else {
        console.log('sendMessage: No explanation found or elements missing. Ensuring panel is hidden.');
        if (explanationPanel) {
            explanationPanel.style.display = 'none';
        }
    }

  } catch (error) {
    hideTypingIndicator();
    console.error("Error sending message:", error);

    if (error.name === 'AbortError') {
      addErrorMessage("Our service is taking longer than expected to respond. Please try again or contact us directly.");
    } else if (error.message.includes('API error')) {
       addErrorMessage("Sorry, there was a problem communicating with the service. Please try again later.");
    }
     else {
      addErrorMessage("We're experiencing technical difficulties. Please try again later or contact support.");
    }

    if (explanationPanel) {
        console.log('Hiding panel due to error in sendMessage.');
        explanationPanel.style.display = 'none';
    }

    const statusIndicator = document.getElementById('apiStatus');
    statusIndicator.textContent = 'API: Error';
    statusIndicator.className = 'api-status disconnected';
    statusIndicator.style.opacity = '1'; 
  }
}
