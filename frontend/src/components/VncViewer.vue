<template>
  <div 
    ref="vncContainer" 
    class="vnc-viewer"
    :class="{ 'small': small, 'interactive': interactive }"
  >
    <div v-if="!connected && !error" class="flex items-center justify-center h-full">
      <div class="text-center text-gray-400">
        <div class="animate-spin w-6 h-6 border-2 border-gray-400 border-t-transparent rounded-full mx-auto mb-2"></div>
        <p class="text-sm">连接中...</p>
      </div>
    </div>
    
    <div v-if="error" class="flex items-center justify-center h-full">
      <div class="text-center text-red-400">
        <svg class="w-6 h-6 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
        </svg>
        <p class="text-sm">连接失败</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
// import RFB from '@novnc/novnc/core/rfb.js'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  },
  vncUrl: {
    type: String,
    required: true
  },
  interactive: {
    type: Boolean,
    default: true
  },
  small: {
    type: Boolean,
    default: false
  }
})

const vncContainer = ref(null)
const rfb = ref(null)
const connected = ref(false)
const error = ref(null)

const connect = async () => {
  if (rfb.value) {
    disconnect()
  }

  try {
    await nextTick()
    
    if (!vncContainer.value) {
      console.error('VNC container not found')
      return
    }

    // Construct WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}${props.vncUrl}`
    
    console.log('Connecting to VNC:', wsUrl)

    // Create RFB connection
    rfb.value = new RFB(vncContainer.value, wsUrl, {
      credentials: { password: 'password' }, // Default password
      repeaterID: '',
      shared: !props.interactive, // Share connection for read-only viewers
      wsProtocols: ['binary']
    })

    // Event handlers
    rfb.value.addEventListener('connect', handleConnect)
    rfb.value.addEventListener('disconnect', handleDisconnect)
    rfb.value.addEventListener('credentialsrequired', handleCredentialsRequired)
    rfb.value.addEventListener('securityfailure', handleSecurityFailure)

    // Configure RFB settings
    rfb.value.viewOnly = !props.interactive
    rfb.value.scaleViewport = props.small
    rfb.value.resizeSession = false
    
    if (props.small) {
      rfb.value.qualityLevel = 6 // Lower quality for small view
      rfb.value.compressionLevel = 2
    }

  } catch (err) {
    console.error('Error creating VNC connection:', err)
    error.value = 'Failed to create VNC connection'
  }
}

const disconnect = () => {
  if (rfb.value) {
    rfb.value.disconnect()
    rfb.value = null
  }
  connected.value = false
  error.value = null
}

const handleConnect = () => {
  console.log('VNC connected')
  connected.value = true
  error.value = null
}

const handleDisconnect = (e) => {
  console.log('VNC disconnected:', e.detail)
  connected.value = false
  
  if (e.detail.clean) {
    error.value = null
  } else {
    error.value = 'Connection lost'
    
    // Auto-reconnect after 3 seconds if not a clean disconnect
    setTimeout(() => {
      if (!connected.value && vncContainer.value) {
        connect()
      }
    }, 3000)
  }
}

const handleCredentialsRequired = () => {
  console.log('VNC credentials required')
  // For now, we use a default password
  // In production, this should be handled properly
}

const handleSecurityFailure = (e) => {
  console.error('VNC security failure:', e.detail)
  error.value = 'Authentication failed'
}

// Watch for prop changes
watch(() => props.vncUrl, () => {
  if (props.vncUrl) {
    connect()
  }
}, { immediate: true })

watch(() => props.interactive, (newVal) => {
  if (rfb.value) {
    rfb.value.viewOnly = !newVal
  }
})

onMounted(() => {
  if (props.vncUrl) {
    connect()
  }
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.vnc-viewer {
  @apply w-full h-full relative overflow-hidden;
}

.vnc-viewer.small {
  @apply cursor-pointer;
}

.vnc-viewer.interactive {
  @apply cursor-default;
}

/* NoVNC specific styles */
:deep(.noVNC_canvas) {
  @apply w-full h-full object-contain;
}

:deep(.noVNC_container) {
  @apply w-full h-full;
}
</style>
