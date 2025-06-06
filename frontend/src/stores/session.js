import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../utils/api'

export const useSessionStore = defineStore('session', () => {
  const mySession = ref(null)
  const allSessions = ref([])
  const loading = ref(false)
  const error = ref(null)
  const capacity = ref({ current: 0, max: 50 })

  const hasActiveSession = computed(() => !!mySession.value)
  const availableSlots = computed(() => capacity.value.max - capacity.value.current)

  const createSession = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/api/sessions')
      mySession.value = response.data
      await fetchAllSessions()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '创建会话失败'
      return false
    } finally {
      loading.value = false
    }
  }

  const fetchMySession = async () => {
    try {
      const response = await api.get('/api/sessions/me')
      mySession.value = response.data
      return true
    } catch (err) {
      if (err.response?.status !== 404) {
        error.value = err.response?.data?.detail || '获取会话失败'
      }
      mySession.value = null
      return false
    }
  }

  const fetchAllSessions = async () => {
    try {
      const response = await api.get('/api/sessions/all')
      allSessions.value = response.data.sessions
      capacity.value = {
        current: response.data.total,
        max: response.data.max_capacity
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '获取会话列表失败'
      return false
    }
  }

  const deleteSession = async () => {
    loading.value = true
    error.value = null
    
    try {
      await api.delete('/api/sessions/me')
      mySession.value = null
      await fetchAllSessions()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '删除会话失败'
      return false
    } finally {
      loading.value = false
    }
  }

  const extendSession = async () => {
    loading.value = true
    error.value = null
    
    try {
      await api.post('/api/sessions/me/extend')
      await fetchMySession()
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '延长会话失败'
      return false
    } finally {
      loading.value = false
    }
  }

  const getSessionById = (sessionId) => {
    return allSessions.value.find(session => session.id === sessionId)
  }

  const isMySession = (sessionId) => {
    return mySession.value?.id === sessionId
  }

  return {
    mySession,
    allSessions,
    loading,
    error,
    capacity,
    hasActiveSession,
    availableSlots,
    createSession,
    fetchMySession,
    fetchAllSessions,
    deleteSession,
    extendSession,
    getSessionById,
    isMySession
  }
})
