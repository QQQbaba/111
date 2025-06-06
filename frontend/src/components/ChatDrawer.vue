<template>
  <!-- Overlay -->
  <div 
    v-if="open"
    class="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
    @click="$emit('update:open', false)"
  ></div>

  <!-- Drawer -->
  <div 
    class="fixed right-0 top-0 h-full w-96 bg-white shadow-xl z-50 transform transition-transform duration-300 flex flex-col"
    :class="{ 'translate-x-0': open, 'translate-x-full': !open }"
  >
    <!-- Header -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200">
      <h3 class="text-lg font-medium text-gray-900">聊天室</h3>
      <button
        @click="$emit('update:open', false)"
        class="text-gray-400 hover:text-gray-600 transition-colors"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>

    <!-- Connection Status -->
    <div v-if="!chatStore.connected" class="p-4 bg-yellow-50 border-b border-yellow-200">
      <div class="flex items-center text-yellow-800 text-sm">
        <div class="animate-spin w-4 h-4 border-2 border-yellow-600 border-t-transparent rounded-full mr-2"></div>
        正在连接聊天服务器...
      </div>
    </div>

    <div v-if="chatStore.error" class="p-4 bg-red-50 border-b border-red-200">
      <div class="flex items-center justify-between">
        <div class="text-red-800 text-sm">{{ chatStore.error }}</div>
        <button
          @click="chatStore.clearError"
          class="text-red-600 hover:text-red-800"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div 
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-4 space-y-4"
    >
      <div
        v-for="message in chatStore.sortedMessages"
        :key="message.id || message.time"
        class="flex items-start space-x-3"
      >
        <!-- Avatar -->
        <div class="flex-shrink-0">
          <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
            <svg 
              class="w-6 h-6" 
              :data-jdenticon-value="message.user"
            ></svg>
          </div>
        </div>
        
        <!-- Message Content -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-2">
            <span class="text-sm font-medium text-gray-900">{{ message.user }}</span>
            <span class="text-xs text-gray-500">{{ formatTime(message.time) }}</span>
          </div>
          <p class="text-sm text-gray-700 mt-1 break-words">{{ message.text }}</p>
        </div>
      </div>

      <!-- Typing Indicators -->
      <div v-if="chatStore.typingUsers.length > 0" class="flex items-start space-x-3">
        <div class="flex-shrink-0">
          <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
            <div class="flex space-x-1">
              <div class="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
              <div class="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
          </div>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm text-gray-500 italic">
            {{ chatStore.typingUsers.join(', ') }} 正在输入...
          </p>
        </div>
      </div>
    </div>

    <!-- Message Input -->
    <div class="p-4 border-t border-gray-200">
      <form @submit.prevent="sendMessage" class="flex space-x-2">
        <input
          v-model="messageText"
          type="text"
          placeholder="输入消息..."
          class="flex-1 input"
          :disabled="!chatStore.connected"
          @input="handleTyping"
          @blur="stopTyping"
          maxlength="500"
        />
        <button
          type="submit"
          :disabled="!messageText.trim() || !chatStore.connected"
          class="btn btn-primary"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
          </svg>
        </button>
      </form>
      <div class="text-xs text-gray-500 mt-2">
        {{ messageText.length }}/500 字符
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { formatTime } from '../utils/time'
import * as jdenticon from 'jdenticon'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  username: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:open'])

const chatStore = useChatStore()
const messagesContainer = ref(null)
const messageText = ref('')
const typingTimeout = ref(null)

const sendMessage = () => {
  if (!messageText.value.trim() || !chatStore.connected) {
    return
  }

  const success = chatStore.sendMessage(messageText.value, props.username)
  if (success) {
    messageText.value = ''
    stopTyping()
  }
}

const handleTyping = () => {
  if (!chatStore.connected) return

  // Send typing indicator
  chatStore.sendTyping(props.username, true)

  // Clear existing timeout
  if (typingTimeout.value) {
    clearTimeout(typingTimeout.value)
  }

  // Set timeout to stop typing indicator
  typingTimeout.value = setTimeout(() => {
    stopTyping()
  }, 1000)
}

const stopTyping = () => {
  if (typingTimeout.value) {
    clearTimeout(typingTimeout.value)
    typingTimeout.value = null
  }
  
  if (chatStore.connected) {
    chatStore.sendTyping(props.username, false)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Watch for new messages and scroll to bottom
watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})

// Watch for drawer open/close
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    scrollToBottom()
  }
})

onMounted(() => {
  // Initialize jdenticon for user avatars
  if (typeof window !== 'undefined') {
    jdenticon()
  }
  scrollToBottom()
})
</script>
