<template>
  <!-- Modal Overlay -->
  <div 
    v-if="open"
    class="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4"
    @click="handleOverlayClick"
  >
    <!-- Modal Content -->
    <div 
      class="bg-white rounded-lg shadow-xl w-full h-full max-w-7xl max-h-full flex flex-col"
      @click.stop
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <!-- User Avatar -->
            <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <svg 
                class="w-6 h-6" 
                :data-jdenticon-value="session?.user_name || session?.user_id"
              ></svg>
            </div>
            <div>
              <h3 class="text-lg font-medium text-gray-900">
                {{ session?.user_name || `用户${session?.user_id}` }}
              </h3>
              <p class="text-sm text-gray-500">
                {{ isOwn ? '我的学习桌面' : '观看模式' }}
              </p>
            </div>
          </div>
          
          <!-- Session Info -->
          <div v-if="session" class="text-sm text-gray-600">
            <span v-if="isOwn">{{ formatExpireTime(session.expires) }}</span>
            <span v-else>只读模式</span>
          </div>
        </div>

        <!-- Controls -->
        <div class="flex items-center space-x-2">
          <!-- Fullscreen Toggle -->
          <button
            @click="toggleFullscreen"
            class="btn btn-secondary"
            title="切换全屏"
          >
            <svg v-if="!isFullscreen" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5M15 9h4.5M15 9V4.5M15 9l5.5-5.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5M15 15h4.5M15 15v4.5m0-4.5l5.5 5.5"></path>
            </svg>
          </button>

          <!-- Close Button -->
          <button
            @click="$emit('update:open', false)"
            class="btn btn-secondary"
            title="关闭"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- VNC Display -->
      <div class="flex-1 bg-black relative overflow-hidden">
        <VncViewer
          v-if="session && session.status === 'active'"
          :session-id="session.id"
          :vnc-url="session.vnc_url"
          :interactive="isOwn"
          :small="false"
        />
        
        <!-- Loading State -->
        <div v-else-if="session && session.status === 'creating'" class="h-full flex items-center justify-center">
          <div class="text-center text-white">
            <div class="animate-spin w-12 h-12 border-4 border-white border-t-transparent rounded-full mx-auto mb-4"></div>
            <p class="text-lg">正在创建桌面...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="session && session.status === 'failed'" class="h-full flex items-center justify-center">
          <div class="text-center text-red-400">
            <svg class="w-12 h-12 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
            </svg>
            <p class="text-lg">桌面创建失败</p>
          </div>
        </div>

        <!-- Read-only Overlay -->
        <div 
          v-if="session && session.status === 'active' && !isOwn"
          class="absolute top-4 left-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm"
        >
          <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
          </svg>
          观看模式
        </div>
      </div>

      <!-- Footer (only for own session) -->
      <div v-if="isOwn && session" class="p-4 border-t border-gray-200 bg-gray-50">
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-600">
            <span class="font-medium">提示：</span>
            您可以在此桌面中进行学习，其他用户可以观看但无法操作
          </div>
          
          <div class="flex space-x-2">
            <button
              @click="$emit('extend')"
              class="btn btn-secondary"
            >
              延长30分钟
            </button>
            <button
              @click="$emit('delete')"
              class="btn btn-danger"
            >
              结束学习
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import VncViewer from './VncViewer.vue'
import { formatExpireTime } from '../utils/time'
import { jdenticon } from 'jdenticon'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  session: {
    type: Object,
    default: null
  },
  isOwn: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:open', 'extend', 'delete'])

const isFullscreen = ref(false)

const handleOverlayClick = () => {
  emit('update:open', false)
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

const handleKeydown = (e) => {
  // Close modal on Escape key
  if (e.key === 'Escape' && props.open) {
    emit('update:open', false)
  }
  
  // Toggle fullscreen on F11
  if (e.key === 'F11' && props.open) {
    e.preventDefault()
    toggleFullscreen()
  }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('keydown', handleKeydown)
  
  // Initialize jdenticon for user avatars
  if (typeof window !== 'undefined') {
    jdenticon()
  }
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('keydown', handleKeydown)
  
  // Exit fullscreen if still in fullscreen mode
  if (document.fullscreenElement) {
    document.exitFullscreen()
  }
})
</script>
