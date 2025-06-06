<template>
  <div 
    class="vnc-card"
    :class="{
      'active': session && session.status === 'active',
      'own': isOwn,
      'creating': session && session.status === 'creating',
      'failed': session && session.status === 'failed'
    }"
  >
    <!-- Empty Slot -->
    <div v-if="!session" class="h-full flex items-center justify-center bg-gray-100 rounded-lg">
      <div class="text-center text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
        </svg>
        <p class="text-sm">空闲座位</p>
      </div>
    </div>

    <!-- Session Card -->
    <div v-else class="h-full relative">
      <!-- VNC Display Area -->
      <div class="h-full bg-black rounded-lg overflow-hidden relative">
        <!-- Creating State -->
        <div v-if="session.status === 'creating'" class="h-full flex items-center justify-center">
          <div class="text-center text-white">
            <div class="animate-spin w-8 h-8 border-2 border-white border-t-transparent rounded-full mx-auto mb-2"></div>
            <p class="text-sm">正在创建桌面...</p>
          </div>
        </div>

        <!-- Failed State -->
        <div v-else-if="session.status === 'failed'" class="h-full flex items-center justify-center">
          <div class="text-center text-red-400">
            <svg class="w-8 h-8 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
            </svg>
            <p class="text-sm">创建失败</p>
          </div>
        </div>

        <!-- Active VNC -->
        <div v-else-if="session.status === 'active'" class="h-full">
          <VncViewer
            :session-id="session.id"
            :vnc-url="session.vnc_url"
            :interactive="isOwn"
            :small="true"
            @click="handleClick"
          />
        </div>

        <!-- Overlay for non-owner sessions -->
        <div 
          v-if="session.status === 'active' && !isOwn"
          class="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-20 transition-all duration-200 cursor-pointer flex items-center justify-center"
          @click="handleClick"
        >
          <div class="opacity-0 hover:opacity-100 transition-opacity duration-200">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
          </div>
        </div>
      </div>

      <!-- Session Info -->
      <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-3">
        <div class="flex items-center justify-between text-white text-sm">
          <div class="flex items-center space-x-2">
            <!-- User Avatar -->
            <div class="w-6 h-6 rounded-full bg-white bg-opacity-20 flex items-center justify-center">
              <svg 
                class="w-4 h-4" 
                :data-jdenticon-value="session.user_name || session.user_id"
              ></svg>
            </div>
            <span class="font-medium">{{ session.user_name || `用户${session.user_id}` }}</span>
          </div>
          
          <div v-if="isOwn" class="flex items-center space-x-1">
            <span class="text-green-400 text-xs">●</span>
            <span class="text-xs">我的桌面</span>
          </div>
        </div>
      </div>

      <!-- Action Buttons (only for own session) -->
      <div v-if="isOwn && session.status === 'active'" class="absolute top-2 right-2 flex space-x-1">
        <button
          @click.stop="$emit('fullscreen', session)"
          class="bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-1.5 rounded transition-all duration-200"
          title="全屏显示"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import VncViewer from './VncViewer.vue'
import { jdenticon } from 'jdenticon'

const props = defineProps({
  session: {
    type: Object,
    default: null
  },
  isOwn: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['fullscreen'])

const handleClick = () => {
  if (props.session && props.session.status === 'active') {
    emit('fullscreen', props.session)
  }
}

onMounted(() => {
  // Initialize jdenticon for user avatars
  if (typeof window !== 'undefined') {
    jdenticon()
  }
})
</script>

<style scoped>
.vnc-card {
  @apply aspect-video bg-gray-100 rounded-lg overflow-hidden relative transition-all duration-200;
}

.vnc-card.active {
  @apply ring-2 ring-blue-500;
}

.vnc-card.own {
  @apply ring-2 ring-green-500;
}

.vnc-card.creating {
  @apply ring-2 ring-yellow-500;
}

.vnc-card.failed {
  @apply ring-2 ring-red-500;
}
</style>
