import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)

  // Actions
  async function login(email, password) {
    try {
      const data = await authService.login(email, password)
      token.value = data.token
      user.value = data.user
      localStorage.setItem('token', data.token)
      return data
    } catch (error) {
      throw error
    }
  }

  async function register(username, email, password) {
    try {
      const data = await authService.register(username, email, password)
      // Registration doesn't return token, user needs to login
      return data
    } catch (error) {
      throw error
    }
  }

  async function loadUser() {
    try {
      const data = await authService.getCurrentUser()
      user.value = data.user
      return data.user
    } catch (error) {
      // If loading user fails, clear auth state
      logout()
      throw error
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    authService.logout().catch(() => {
      // Ignore errors on logout
    })
  }

  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('token', newToken)
    } else {
      localStorage.removeItem('token')
    }
  }

  function setUser(userData) {
    user.value = userData
  }

  return {
    // State
    user,
    token,
    // Getters
    isAuthenticated,
    // Actions
    login,
    register,
    loadUser,
    logout,
    setToken,
    setUser,
  }
})

