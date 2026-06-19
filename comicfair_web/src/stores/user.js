import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getCurrentUser, register as apiRegister } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('cf_token') || '')
  const refresh = ref(localStorage.getItem('cf_refresh') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('cf_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const role = computed(() => userInfo.value?.role || '')
  const isOrganizer = computed(() => role.value === 'organizer')
  const isExhibitor = computed(() => role.value === 'exhibitor')
  const isVisitor = computed(() => role.value === 'visitor')

  function setTokens(access, refreshToken) {
    token.value = access
    refresh.value = refreshToken
    localStorage.setItem('cf_token', access)
    localStorage.setItem('cf_refresh', refreshToken)
  }

  function setUser(user) {
    userInfo.value = user
    localStorage.setItem('cf_user', JSON.stringify(user))
  }

  async function login(credentials) {
    const res = await apiLogin(credentials)
    setTokens(res.access, res.refresh)
    setUser(res.user)
    return res
  }

  async function register(data) {
    return await apiRegister(data)
  }

  async function fetchUser() {
    if (!token.value) return null
    try {
      const user = await getCurrentUser()
      setUser(user)
      return user
    } catch (e) {
      logout()
      throw e
    }
  }

  function logout() {
    token.value = ''
    refresh.value = ''
    userInfo.value = null
    localStorage.removeItem('cf_token')
    localStorage.removeItem('cf_refresh')
    localStorage.removeItem('cf_user')
  }

  return {
    token,
    refresh,
    userInfo,
    isLoggedIn,
    role,
    isOrganizer,
    isExhibitor,
    isVisitor,
    login,
    register,
    fetchUser,
    setTokens,
    setUser,
    logout,
  }
})
