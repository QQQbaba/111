<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-semibold text-gray-900">网络自习室</h1>
            <div class="ml-4 text-sm text-gray-500">
              在线: {{ sessionStore.capacity.current }}/{{ sessionStore.capacity.max }}
            </div>
          </div>
          
          <div class="flex items-center space-x-4">
            <!-- Chat Toggle -->
            <button
              @click="toggleChat"
              class="btn btn-secondary relative"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a9.863 9.863 0 01-4.255-.949L5 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 3.582-8 8-8s8 3.582 8 8z"></path>
              </svg>
              聊天室
              <span v-if="unreadCount > 0" class="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </button>
            
            <!-- Logout -->
            <button
              @click="handleLogout"
              class="btn btn-secondary"
            >
              退出登录
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Session Controls -->
      <div class="mb-8">
        <div v-if="!sessionStore.hasActiveSession" class="text-center">
          <div class="mb-4">
            <h2 class="text-lg font-medium text-gray-900 mb-2">开始学习</h2>
            <p class="text-gray-600">点击下方按钮创建您的专属学习桌面</p>
          </div>
          <button
            @click="createSession"
            :disabled="sessionStore.loading || sessionStore.availableSlots <= 0"
            class="btn btn-primary"
          >
            <span v-if="sessionStore.loading" class="inline-block animate-spin w-4 h-4 mr-2">⟳</span>
            {{ sessionStore.availableSlots <= 0 ? '座位已满' : '创建学习桌面' }}
          </button>
        </div>
        
        <div v-else class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-medium text-gray-900">我的学习桌面</h3>
              <p class="text-sm text-gray-600 mt-1">
                {{ formatExpireTime(sessionStore.mySession.expires) }}
              </p>
            </div>
            <div class="flex space-x-3">
              <button
                @click="extendSession"
                :disabled="sessionStore.loading"
                class="btn btn-secondary"
              >
                延长30分钟
              </button>
              <button
                @click="deleteSession"
                :disabled="sessionStore.loading"
                class="btn btn-danger"
              >
                结束学习
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="sessionStore.error" class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex">
          <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
          </svg>
          <div class="ml-3">
            <p class="text-sm text-red-800">{{ sessionStore.error }}</p>
          </div>
        </div>
      </div>

      <!-- Desktop Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <VncCard
          v-for="(session, index) in displaySessions"
          :key="session?.id || `empty-${index}`"
          :session="session"
          :is-own="session && sessionStore.isMySession(session.id)"
          @fullscreen="openFullscreen"
        />
      </div>
    </main>

    <!-- Chat Drawer -->
    <ChatDrawer
      v-model:open="chatOpen"
      :username="username"
    />

    <!-- Fullscreen VNC Modal -->
    <VncModal
      v-model:open="fullscreenOpen"
      :session="fullscreenSession"
      :is-own="fullscreenSession && sessionStore.isMySession(fullscreenSession.id)"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSessionStore } from '../stores/session'
import { useChatStore } from '../stores/chat'
import { formatExpireTime } from '../utils/time'
import VncCard from '../components/VncCard.vue'
import ChatDrawer from '../components/ChatDrawer.vue'
import VncModal from '../components/VncModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const chatStore = useChatStore()

const chatOpen = ref(false)
const fullscreenOpen = ref(false)
const fullscreenSession = ref(null)
const unreadCount = ref(0)
const username = ref('用户' + Math.random().toString(36).substr(2, 5)) // Temporary username

let refreshInterval = null

// Computed
const displaySessions = computed(() => {
  const sessions = [...sessionStore.allSessions]
  const totalSlots = 50
  
  // Fill empty slots
  while (sessions.length < totalSlots) {
    sessions.push(null)
  }
  
  return sessions.slice(0, totalSlots)
})

// Methods
const createSession = async () => {
  const success = await sessionStore.createSession()
  if (success) {
    console.log('Session created successfully')
  }
}

const extendSession = async () => {
  const success = await sessionStore.extendSession()
  if (success) {
    console.log('Session extended successfully')
  }
}

const deleteSession = async () => {
  if (confirm('确定要结束学习吗？')) {
    const success = await sessionStore.deleteSession()
    if (success) {
      console.log('Session deleted successfully')
    }
  }
}

const toggleChat = () => {
  chatOpen.value = !chatOpen.value
  if (chatOpen.value) {
    unreadCount.value = 0
  }
}

const openFullscreen = (session) => {
  fullscreenSession.value = session
  fullscreenOpen.value = true
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    chatStore.disconnect()
    authStore.logout()
    router.push('/login')
  }
}

const refreshData = async () => {
  await sessionStore.fetchAllSessions()
  if (sessionStore.hasActiveSession) {
    await sessionStore.fetchMySession()
  }
}

// Lifecycle
onMounted(async () => {
  // Initial data fetch
  await refreshData()
  
  // Connect to chat
  chatStore.connect(username.value)
  
  // Set up refresh interval
  refreshInterval = setInterval(refreshData, 10000) // Refresh every 10 seconds
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  chatStore.disconnect()
})
</script>
