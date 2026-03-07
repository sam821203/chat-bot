<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

/** Render assistant content as safe HTML: Markdown → HTML → DOMPurify. Only use for assistant messages. */
function renderMarkdown(text) {
  if (text == null || typeof text !== 'string') return ''
  const html = marked.parse(text)
  return DOMPurify.sanitize(html)
}

const THREADS_STORAGE_KEY = 'chatbot_threads'
const SIDEBAR_STORAGE_KEY = 'chatbot_sidebar_collapsed'
const SIDEBAR_WIDTH_STORAGE_KEY = 'chatbot_sidebar_width'
const OLD_STORAGE_KEY = 'chatbot_messages'

const SIDEBAR_WIDTH_MIN = 200
const SIDEBAR_WIDTH_MAX = 480
const SIDEBAR_WIDTH_DEFAULT = 260

const route = useRoute()
const router = useRouter()

const envApiBase =
  import.meta.env.VITE_API_BASE ||
  (import.meta.env.DEV ? 'http://localhost:10000' : 'https://chat-bot-7ua2.onrender.com')
const message = ref('')
const threads = ref([])
const activeThreadId = ref(null)
const sidebarCollapsed = ref(false)
const sidebarWidth = ref(SIDEBAR_WIDTH_DEFAULT)
const sidebarResizing = ref(false)
const loading = ref(false)
const messagesContainer = ref(null)
const mode = ref('ask')
const copied = ref(false)
const exportMenuOpen = ref(false)
const exportDropdownRef = ref(null)

function generateThreadId() {
  return crypto.randomUUID ? crypto.randomUUID() : `t-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

const currentThread = computed(() =>
  activeThreadId.value == null ? null : threads.value.find((t) => t.id === activeThreadId.value)
)
const currentMessages = computed(() => (currentThread.value ? currentThread.value.messages : []))

const loadHistory = () => {
  try {
    const raw = localStorage.getItem(THREADS_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed && Array.isArray(parsed.threads)) {
        const valid = parsed.threads.filter(
          (t) =>
            t &&
            t.id &&
            typeof t.title === 'string' &&
            Array.isArray(t.messages) &&
          typeof t.createdAt === 'number'
        )
        threads.value = valid
        if (parsed.activeThreadId != null && valid.some((t) => t.id === parsed.activeThreadId)) {
          activeThreadId.value = parsed.activeThreadId
        } else {
          activeThreadId.value = valid.length ? valid[0].id : null
        }
      }
    }
    const oldRaw = localStorage.getItem(OLD_STORAGE_KEY)
    if (oldRaw && threads.value.length === 0) {
      try {
        const oldParsed = JSON.parse(oldRaw)
        if (Array.isArray(oldParsed) && oldParsed.every((m) => m && typeof m.content === 'string' && typeof m.isUser === 'boolean')) {
          const migrated = {
            id: generateThreadId(),
            title: '之前的對話',
            messages: oldParsed,
            createdAt: Date.now(),
          }
          threads.value = [migrated]
          activeThreadId.value = migrated.id
          localStorage.removeItem(OLD_STORAGE_KEY)
          saveHistory()
        }
      } catch {
        // ignore
      }
    }
    const sidebarRaw = localStorage.getItem(SIDEBAR_STORAGE_KEY)
    if (sidebarRaw !== null) sidebarCollapsed.value = sidebarRaw === 'true'
    const widthRaw = localStorage.getItem(SIDEBAR_WIDTH_STORAGE_KEY)
    if (widthRaw !== null) {
      const w = Number(widthRaw)
      if (!Number.isNaN(w) && w >= SIDEBAR_WIDTH_MIN && w <= SIDEBAR_WIDTH_MAX) {
        sidebarWidth.value = w
      }
    }
  } catch {
    // ignore invalid or missing data
  }
}

const saveHistory = () => {
  try {
    localStorage.setItem(
      THREADS_STORAGE_KEY,
      JSON.stringify({ threads: threads.value, activeThreadId: activeThreadId.value })
    )
  } catch {
    // ignore
  }
}

function saveSidebarState() {
  try {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(sidebarCollapsed.value))
  } catch {
    // ignore
  }
}

function saveSidebarWidth() {
  try {
    localStorage.setItem(SIDEBAR_WIDTH_STORAGE_KEY, String(sidebarWidth.value))
  } catch {
    // ignore
  }
}

function startSidebarResize(e) {
  if (sidebarCollapsed.value) return
  sidebarResizing.value = true
  const startX = e.clientX
  const startW = sidebarWidth.value
  const onMove = (e2) => {
    const delta = e2.clientX - startX
    const next = Math.min(SIDEBAR_WIDTH_MAX, Math.max(SIDEBAR_WIDTH_MIN, startW + delta))
    sidebarWidth.value = next
  }
  const onUp = () => {
    sidebarResizing.value = false
    saveSidebarWidth()
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function syncActiveThreadFromRoute() {
  const threadId = route.params.threadId
  if (threadId && threads.value.some((t) => t.id === threadId)) {
    activeThreadId.value = threadId
  } else {
    activeThreadId.value = null
  }
}

onMounted(() => {
  loadHistory()
  nextTick(syncActiveThreadFromRoute)
})
watch([threads, activeThreadId], saveHistory, { deep: true })

watch(
  () => route.params.threadId,
  () => {
    syncActiveThreadFromRoute()
  }
)

function createThread() {
  const id = generateThreadId()
  const thread = { id, title: 'New chat', messages: [], createdAt: Date.now() }
  threads.value = [thread, ...threads.value]
  activeThreadId.value = id
  router.push('/chat/' + id)
  return id
}

function startNewChat() {
  activeThreadId.value = null
  router.push('/chat')
}

function switchThread(id) {
  activeThreadId.value = id
  router.push('/chat/' + id)
}

function deleteThread(id, e) {
  e?.stopPropagation()
  const idx = threads.value.findIndex((t) => t.id === id)
  if (idx === -1) return
  threads.value = threads.value.filter((t) => t.id !== id)
  if (activeThreadId.value === id) {
    activeThreadId.value = threads.value[0]?.id ?? null
    router.push(activeThreadId.value ? '/chat/' + activeThreadId.value : '/chat')
  }
  saveHistory()
}

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

  let threadId = activeThreadId.value
  if (threadId == null) {
    threadId = createThread()
  }
  const thread = threads.value.find((t) => t.id === threadId)
  if (!thread) return

  const userContent = message.value.trim()
  thread.messages.push({ content: userContent, isUser: true })
  if (thread.title === 'New chat') {
    thread.title = userContent.slice(0, 30) + (userContent.length > 30 ? '…' : '')
  }
  message.value = ''
  loading.value = true

  await nextTick()
  scrollToBottom()

  try {
    const payloadMessages = thread.messages.map((m) => ({
      role: m.isUser ? 'user' : 'assistant',
      content: m.content,
    }))
    const response = await fetch(`${envApiBase}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages: payloadMessages, mode: mode.value }),
    })

    const data = await response.json()

    thread.messages.push({
      content: data.response,
      isUser: false,
      usedSearch: data.used_search === true,
    })
  } catch (error) {
    console.error('Error:', error)
    thread.messages.push({
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

const copyConversation = async () => {
  if (currentMessages.value.length === 0) return
  const text = currentMessages.value
    .map((m) => (m.isUser ? 'You' : 'Assistant') + ': ' + m.content)
    .join('\n\n')
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    // ignore
  }
}

function exportAsText() {
  return currentMessages.value
    .map((m) => (m.isUser ? 'You' : 'Assistant') + ': ' + m.content)
    .join('\n\n')
}

function exportAsMarkdown() {
  return currentMessages.value
    .map((m) => {
      const label = m.isUser ? '**You:**' : '**Assistant:**'
      let block = label + '\n\n' + m.content
      if (!m.isUser && m.usedSearch) block += '\n\n*已使用 Google 搜尋*'
      return block
    })
    .join('\n\n')
}

function downloadExport(extension, getContent) {
  if (currentMessages.value.length === 0) return
  const content = getContent()
  const mime = extension === 'md' ? 'text/markdown' : 'text/plain'
  const blob = new Blob([content], { type: mime })
  const ts = new Date().toISOString().slice(0, 19).replace('T', '-').replace(/:/g, '')
  const filename = `chatbot-export-${ts}.${extension}`
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
  exportMenuOpen.value = false
}

function closeExportMenuOnClickOutside(e) {
  if (exportDropdownRef.value && !exportDropdownRef.value.contains(e.target)) {
    exportMenuOpen.value = false
  }
}

function closeExportMenuOnEsc(e) {
  if (e.key === 'Escape') exportMenuOpen.value = false
}

watch(exportMenuOpen, (open) => {
  if (open) {
    nextTick(() => {
      document.addEventListener('click', closeExportMenuOnClickOutside)
      document.addEventListener('keydown', closeExportMenuOnEsc)
    })
  } else {
    document.removeEventListener('click', closeExportMenuOnClickOutside)
    document.removeEventListener('keydown', closeExportMenuOnEsc)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', closeExportMenuOnClickOutside)
  document.removeEventListener('keydown', closeExportMenuOnEsc)
})
</script>

<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside
      :class="['sidebar', { collapsed: sidebarCollapsed, resizing: sidebarResizing }]"
      :style="sidebarCollapsed ? undefined : { width: sidebarWidth + 'px', minWidth: sidebarWidth + 'px' }"
    >
      <div class="sidebar-header">
        <button
          type="button"
          class="sidebar-toggle"
          :aria-label="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="sidebarCollapsed = !sidebarCollapsed; saveSidebarState()"
        >
          <svg v-if="sidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18l6-6-6-6"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" x2="21" y1="6" y2="6"/>
            <line x1="3" x2="21" y1="12" y2="12"/>
            <line x1="3" x2="21" y1="18" y2="18"/>
          </svg>
        </button>
        <button
          v-if="!sidebarCollapsed"
          type="button"
          class="sidebar-new-chat"
          @click="startNewChat()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          <span>New chat</span>
        </button>
      </div>
      <div v-if="!sidebarCollapsed" class="sidebar-threads">
        <div
          v-for="t in threads"
          :key="t.id"
          role="button"
          tabindex="0"
          :class="['sidebar-thread', { active: activeThreadId === t.id }]"
          @click="switchThread(t.id)"
          @keydown.enter.prevent="switchThread(t.id)"
          @keydown.space.prevent="switchThread(t.id)"
        >
          <span class="sidebar-thread-title">{{ t.title || 'New chat' }}</span>
          <button
            type="button"
            class="sidebar-thread-delete"
            aria-label="Delete thread"
            @click="deleteThread(t.id, $event)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              <line x1="10" x2="10" y1="11" y2="17"/>
              <line x1="14" x2="14" y1="11" y2="17"/>
            </svg>
          </button>
        </div>
      </div>
      <div
        v-if="!sidebarCollapsed"
        class="sidebar-resize-handle"
        aria-label="Resize sidebar"
        @mousedown.prevent="startSidebarResize"
      />
    </aside>

    <div class="chat-container">
    <!-- Header -->
    <div class="chat-header">
      <div class="chat-header-left">
        <div class="header-bot-icon" v-html="botIcon"></div>
        <h1>ChatBot</h1>
      </div>
      <div class="chat-header-right">
        <div class="mode-group">
          <button type="button" :class="['mode-btn', { active: mode === 'ask' }]" @click="mode = 'ask'">
            Ask
          </button>
          <button type="button" :class="['mode-btn', { active: mode === 'agent' }]" @click="mode = 'agent'">
            Agent
          </button>
        </div>
        <div class="export-dropdown-wrap" ref="exportDropdownRef">
          <button
            type="button"
            class="icon-btn"
            title="Export conversation"
            aria-label="Export conversation"
            aria-haspopup="true"
            :aria-expanded="exportMenuOpen"
            :disabled="currentMessages.length === 0"
            @click="exportMenuOpen = !exportMenuOpen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" x2="12" y1="15" y2="3"/>
            </svg>
          </button>
          <div v-show="exportMenuOpen" class="export-menu" role="menu">
            <button type="button" role="menuitem" class="export-menu-item" @click="downloadExport('md', exportAsMarkdown)">
              Download as .md
            </button>
            <button type="button" role="menuitem" class="export-menu-item" @click="downloadExport('txt', exportAsText)">
              Download as .txt
            </button>
          </div>
        </div>
        <button type="button" class="icon-btn" title="Copy conversation" @click="copyConversation" aria-label="Copy conversation">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
            <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
          </svg>
          <span v-if="copied" class="copied-tip">Copied</span>
        </button>
      </div>
    </div>

    <!-- Messages Container -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="currentMessages.length === 0" class="empty-state">
        <div class="empty-state-icon" v-html="botIcon"></div>
        <p class="empty-state-title">Start a conversation.</p>
        <p class="empty-state-text">
          Send a message to begin. Use <strong>Ask</strong> for quick answers or <strong>Agent</strong> for multi-step tasks.
        </p>
      </div>
      <div
        v-for="(msg, index) in currentMessages"
        :key="index"
        :class="['message', msg.isUser ? 'user' : 'assistant']"
      >
        <div class="message-avatar" v-html="msg.isUser ? userIcon : botIcon"></div>
        <div class="message-body">
          <div
            class="message-content"
            :class="{ 'message-content--md': !msg.isUser }"
          >
            <template v-if="msg.isUser">{{ msg.content }}</template>
            <div v-else v-html="renderMarkdown(msg.content)"></div>
          </div>
          <div v-if="msg.usedSearch" class="search-badge">已使用 Google 搜尋</div>
        </div>
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
      <button type="submit" :disabled="loading" aria-label="Send">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
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
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  background-color: #f3f4f6;
}

.sidebar {
  width: 260px;
  min-width: 260px;
  background-color: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: min-width 0.2s, width 0.2s;
  flex-shrink: 0;
  position: relative;
}

.sidebar.resizing {
  transition: none;
}

.sidebar.collapsed {
  width: 60px;
  min-width: 60px;
}

.sidebar-resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  z-index: 1;
}

.sidebar-resize-handle:hover,
.sidebar.resizing .sidebar-resize-handle {
  background: linear-gradient(to right, transparent 0%, rgba(123, 59, 255, 0.15) 100%);
}

.sidebar-resize-handle::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 24px;
  border-radius: 1px;
  background-color: #d1d5db;
  opacity: 0;
  transition: opacity 0.15s;
}

.sidebar-resize-handle:hover::after,
.sidebar.resizing .sidebar-resize-handle::after {
  opacity: 1;
}

.sidebar-header {
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sidebar-toggle {
  padding: 0.35rem;
  border: none;
  background: transparent;
  color: #4b5563;
  cursor: pointer;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s, background-color 0.2s;
}

.sidebar-toggle:hover {
  color: var(--color-primary);
  background-color: #f3f4f6;
}

.sidebar-new-chat {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.sidebar-new-chat:hover {
  border-color: var(--color-primary);
  background-color: #faf5ff;
  color: var(--color-primary);
}

.sidebar-new-chat-icon {
  padding: 0.35rem;
  border: none;
  background: transparent;
  color: #4b5563;
  cursor: pointer;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s, background-color 0.2s;
}

.sidebar-new-chat-icon:hover {
  color: var(--color-primary);
  background-color: #f3f4f6;
}

.sidebar-threads {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sidebar-thread {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 0.375rem;
  background: transparent;
  color: #374151;
  font-size: 0.875rem;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s;
}

.sidebar-thread:hover {
  background-color: #f3f4f6;
}

.sidebar-thread.active {
  background-color: #ede9fe;
  color: var(--color-primary);
  font-weight: 500;
}

.sidebar-thread-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-thread-delete {
  padding: 0.25rem;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s, color 0.2s, background-color 0.2s;
}

.sidebar-thread:hover .sidebar-thread-delete {
  opacity: 1;
}

.sidebar-thread-delete:hover {
  color: #ef4444;
  background-color: #fef2f2;
}

.chat-container {
  flex: 1;
  min-width: 0;
  max-width: 100%;
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
  justify-content: space-between;
  gap: 1rem;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chat-header h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.header-bot-icon {
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-bot-icon :deep(svg) {
  width: 30px;
  height: 30px;
}

.chat-header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mode-group {
  display: flex;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  padding: 3px;
  background-color: #f0f3f6;
  gap: 0;
}

.mode-btn {
  padding: 0.35rem 0.875rem;
  font-size: 0.875rem;
  font-weight: 500;
  border: none;
  border-radius: 9999px;
  background-color: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.mode-btn:hover {
  color: #374151;
}

.mode-btn.active {
  background-color: white;
  color: #1a202c;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.icon-btn {
  padding: 0.35rem;
  border: none;
  background: transparent;
  color: #4b5563;
  cursor: pointer;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: color 0.2s, background-color 0.2s;
}

.icon-btn:hover:not(:disabled) {
  color: var(--color-primary);
  background-color: #f3f4f6;
}

.icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.copied-tip {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-primary);
  white-space: nowrap;
}

.export-dropdown-wrap {
  position: relative;
}

.export-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.25rem;
  min-width: 10rem;
  padding: 0.25rem 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  z-index: 50;
}

.export-menu-item {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  text-align: left;
  border: none;
  background: transparent;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.15s;
}

.export-menu-item:hover {
  background-color: #f3f4f6;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  min-height: 200px;
}

.empty-state-icon {
  color: #9ca3af;
  margin-bottom: 1rem;
}

.empty-state-icon :deep(svg) {
  width: 64px;
  height: 64px;
}

.empty-state-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.empty-state-text {
  font-size: 0.9375rem;
  color: #6b7280;
  max-width: 320px;
  line-height: 1.5;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  max-width: min(80%, 42rem);
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
  background-color: var(--color-primary);
}

.message.assistant .message-avatar {
  background-color: #4b5563;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}

.message-content {
  padding: 0.75rem;
  border-radius: 0.5rem;
  line-height: 1.5;
  max-width: 100%;
  overflow-wrap: break-word;
  word-break: break-word;
}

.message.user .message-content {
  background-color: var(--color-primary);
  color: white;
}

.message.assistant .message-content {
  background-color: #f2f2f2;
  color: #1f2937;
}

/* Markdown-rendered content (assistant only); use :deep for v-html children */
.message-content--md :deep(p),
.message-content--md :deep(li),
.message-content--md :deep(h2),
.message-content--md :deep(h3),
.message-content--md :deep(h4),
.message-content--md :deep(blockquote) {
  overflow-wrap: break-word;
  word-break: break-word;
}
.message-content--md :deep(h2) {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0.75em 0 0.35em;
}
.message-content--md :deep(h2:first-child) {
  margin-top: 0;
}
.message-content--md :deep(h3),
.message-content--md :deep(h4) {
  font-size: 1rem;
  font-weight: 600;
  margin: 0.6em 0 0.25em;
}
.message-content--md :deep(p) {
  margin: 0.5em 0;
}
.message-content--md :deep(p:first-child) {
  margin-top: 0;
}
.message-content--md :deep(ul),
.message-content--md :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5rem;
}
.message-content--md :deep(li) {
  margin: 0.2em 0;
}
.message-content--md :deep(code) {
  font-family: ui-monospace, monospace;
  font-size: 0.9em;
  background-color: rgba(0, 0, 0, 0.06);
  padding: 0.15em 0.4em;
  border-radius: 0.25rem;
}
.message-content--md :deep(pre) {
  margin: 0.5em 0;
  padding: 0.75rem;
  background-color: rgba(0, 0, 0, 0.06);
  border-radius: 0.375rem;
  overflow-x: auto;
  font-size: 0.9em;
}
.message-content--md :deep(pre code) {
  padding: 0;
  background: none;
}
.message-content--md :deep(strong) {
  font-weight: 700;
}
.message-content--md :deep(blockquote) {
  margin: 0.5em 0;
  padding-left: 1rem;
  border-left: 3px solid #9ca3af;
  color: #4b5563;
}

.search-badge {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
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
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(123, 59, 255, 0.25);
}

.chat-form button {
  background-color: var(--color-primary);
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
  background-color: var(--color-primary-hover);
}

.chat-form button:disabled {
  background-color: var(--color-primary-muted);
  cursor: not-allowed;
}
</style>
