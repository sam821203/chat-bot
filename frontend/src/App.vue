<script setup>
import { ref, nextTick } from 'vue'

const message = ref('')
const messages = ref([])
const loading = ref(false)
const messagesContainer = ref(null)

const userIcon = `
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
`

const botIcon = `
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 8V4H8"/>
    <rect width="16" height="12" x="4" y="8" rx="2"/>
    <path d="M2 14h2"/>
    <path d="M20 14h2"/>
    <path d="M15 13v2"/>
    <path d="M9 13v2"/>
  </svg>
`

const sendMessage = async () => {
  if (!message.value.trim()) return

  // 添加用戶訊息
  messages.value.push({ content: message.value, isUser: true })
  const userMessage = message.value
  message.value = ''
  loading.value = true

  await nextTick()
  scrollToBottom()

  try {
    const response = await fetch('https://chat-bot-7ua2.onrender.com/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userMessage }),
    })

    const data = await response.json()

    // 添加機器人回應
    messages.value.push({ content: data.response, isUser: false })
  } catch (error) {
    console.error('Error:', error)
    messages.value.push({
      content: 'Sorry, I encountered an error. Please try again.',
      isUser: false,
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<template>
  <div class="chat-container">
    <!-- Header -->
    <div class="chat-header">
      <div class="bot-icon header-bot-icon"></div>
      <img src="./assets/bot.svg" alt="" />
      <h1>AI Chat Assistant</h1>
    </div>

    <!-- Messages Container -->
    <div class="messages-container" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.isUser ? 'user' : 'assistant']"
      >
        <div class="message-avatar" v-html="msg.isUser ? userIcon : botIcon"></div>
        <div class="message-content">{{ msg.content }}</div>
      </div>
      <div v-if="loading" class="message assistant">
        <div class="message-avatar" v-html="botIcon"></div>
        <div class="loading">
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
        </div>
      </div>
    </div>

    <!-- Input Form -->
    <form class="chat-form" @submit.prevent="sendMessage">
      <input v-model="message" type="text" placeholder="Type your message..." required />
      <button type="submit" :disabled="loading">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="m22 2-7 20-4-9-9-4Z" />
          <path d="M22 2 11 13" />
        </svg>
      </button>
    </form>
  </div>
</template>

<style scoped>
.chat-container {
  width: 100%;
  max-width: 800px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chat-header {
  padding: 1rem;
  background-color: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chat-header h1 {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1f2937;
}

.bot-icon {
  color: #f96887;
}

.header-bot-icon svg {
  width: 40px;
  height: 40px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  max-width: 80%;
}

.message.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-avatar {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-avatar svg {
  width: 1.5rem;
  height: 1.5rem;
}

.message-avatar svg {
  width: 20px;
  height: 20px;
}

.message.user .message-avatar {
  background-color: #f96887;
}

.message.assistant .message-avatar {
  background-color: #4b5563;
}

.message-content {
  padding: 0.75rem;
  border-radius: 0.5rem;
  line-height: 1.5;
}

.message.user .message-content {
  background-color: #f96887;
  color: white;
}

.message.assistant .message-content {
  background-color: #f2f2f2;
  color: #1f2937;
}

/* Loading animation */
.loading {
  display: flex;
  gap: 0.25rem;
  padding: 0.75rem;
  background-color: #f2f2f2;
  border-radius: 0.75rem;
  width: fit-content;
}

.loading-dot {
  width: 0.5rem;
  height: 0.5rem;
  background-color: #9ca3af;
  border-radius: 50%;
  animation: bounce 0.5s infinite;
}

.loading-dot:nth-child(2) {
  animation-delay: 0.15s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.chat-form {
  padding: 1rem;
  background-color: white;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
}

.chat-form input {
  flex: 1;
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.chat-form input:focus {
  border-color: #f96887;
  box-shadow: 0 0 0 3px rgba(249, 104, 135, 0.2);
}

.chat-form button {
  background-color: #f96887;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-form button:hover {
  background-color: #d0546f;
}

.chat-form button:disabled {
  background-color: #f9a6b8;
  cursor: not-allowed;
}
</style>
