import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { io } from 'socket.io-client'

export const useChatStore = defineStore('chat', () => {
  const socket = ref(null)
  const messages = ref([])
  const connected = ref(false)
  const typing = ref(new Set())
  const error = ref(null)

  const sortedMessages = computed(() => {
    return [...messages.value].sort((a, b) => a.time - b.time)
  })

  const typingUsers = computed(() => {
    return Array.from(typing.value)
  })

  const connect = (username) => {
    if (socket.value) {
      disconnect()
    }

    const socketUrl = window.location.protocol === 'https:' 
      ? `wss://${window.location.host}/ws/chat`
      : `ws://${window.location.host}/ws/chat`

    socket.value = io(socketUrl, {
      transports: ['websocket', 'polling'],
      upgrade: true,
      rememberUpgrade: true
    })

    socket.value.on('connect', () => {
      connected.value = true
      error.value = null
      console.log('Connected to chat server')
    })

    socket.value.on('disconnect', () => {
      connected.value = false
      console.log('Disconnected from chat server')
    })

    socket.value.on('connect_error', (err) => {
      error.value = '连接聊天服务器失败'
      console.error('Chat connection error:', err)
    })

    socket.value.on('chat:history', (history) => {
      messages.value = history
    })

    socket.value.on('chat:new', (message) => {
      messages.value.push(message)
      
      // Keep only last 100 messages in memory
      if (messages.value.length > 100) {
        messages.value = messages.value.slice(-100)
      }
    })

    socket.value.on('chat:typing', (data) => {
      if (data.isTyping) {
        typing.value.add(data.user)
      } else {
        typing.value.delete(data.user)
      }
      
      // Auto-remove typing indicator after 3 seconds
      if (data.isTyping) {
        setTimeout(() => {
          typing.value.delete(data.user)
        }, 3000)
      }
    })

    socket.value.on('chat:error', (data) => {
      error.value = data.message
    })
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
    }
    connected.value = false
    typing.value.clear()
  }

  const sendMessage = (text, username) => {
    if (!socket.value || !connected.value) {
      error.value = '未连接到聊天服务器'
      return false
    }

    if (!text.trim()) {
      return false
    }

    socket.value.emit('chat:send', {
      text: text.trim(),
      user: username
    })

    return true
  }

  const sendTyping = (username, isTyping) => {
    if (!socket.value || !connected.value) {
      return
    }

    socket.value.emit('chat:typing', {
      user: username,
      isTyping
    })
  }

  const clearError = () => {
    error.value = null
  }

  return {
    socket,
    messages,
    connected,
    typing,
    error,
    sortedMessages,
    typingUsers,
    connect,
    disconnect,
    sendMessage,
    sendTyping,
    clearError
  }
})
