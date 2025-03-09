const messagesContainer = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");

const userIcon = `
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
`;

const botIcon = `
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 8V4H8"/>
    <rect width="16" height="12" x="4" y="8" rx="2"/>
    <path d="M2 14h2"/>
    <path d="M20 14h2"/>
    <path d="M15 13v2"/>
    <path d="M9 13v2"/>
  </svg>
`;

function createMessageElement(content, isUser) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${isUser ? "user" : "assistant"}`;

  messageDiv.innerHTML = `
    <div class="message-avatar">
      ${isUser ? userIcon : botIcon}
    </div>
    <div class="message-content">${content}</div>
  `;

  return messageDiv;
}

function createLoadingIndicator() {
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message assistant";

  loadingDiv.innerHTML = `
    <div class="message-avatar">
      ${botIcon}
    </div>
    <div class="loading">
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
      <div class="loading-dot"></div>
    </div>
  `;

  return loadingDiv;
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 儲存發送訊息的函數
async function sendMessage() {
  const message = messageInput.value.trim();
  console.log("Message:", message);

  if (!message) return;

  messageInput.value = "";

  // 顯示用戶訊息
  const userMessage = createMessageElement(message, true);
  messagesContainer.appendChild(userMessage);
  scrollToBottom();

  // 顯示加載指示器
  const loadingIndicator = createLoadingIndicator();
  messagesContainer.appendChild(loadingIndicator);
  scrollToBottom();

  messageInput.disabled = true;

  try {
    const response = await fetch("http://localhost:5001/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    // 移除加載指示器
    messagesContainer.removeChild(loadingIndicator);

    const assistantMessage = createMessageElement(data.response, false);
    messagesContainer.appendChild(assistantMessage);
    scrollToBottom();
  } catch (error) {
    console.error("Error:", error);

    messagesContainer.removeChild(loadingIndicator);

    const errorMessage = createMessageElement(
      "Sorry, I encountered an error. Please try again.",
      false
    );
    messagesContainer.appendChild(errorMessage);
    scrollToBottom();
  } finally {
    // 重新啟用輸入框
    messageInput.disabled = false;
    messageInput.focus();
  }
}

// 監聽表單提交事件，避免頁面重新整理
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});
