import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../utils/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  const login = async (credentials) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/api/login', credentials)
      token.value = response.data.token
      localStorage.setItem('token', token.value)
      
      // Set token for future requests
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  const register = async (credentials) => {
    loading.value = true
    error.value = null
    
    try {
      await api.post('/api/register', credentials)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    delete api.defaults.headers.common['Authorization']
  }

  const initAuth = () => {
    if (token.value) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }
  }

  return {
    token,
    user,
    loading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    initAuth
  }
})
