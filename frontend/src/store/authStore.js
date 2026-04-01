/**
 * Global auth state — stores user info and access token.
 * Persists to localStorage so user stays logged in on refresh.
 */
import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  accessToken: localStorage.getItem('access_token') || null,
  isAuthenticated: !!localStorage.getItem('access_token'),

  setAuth: (user, accessToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, accessToken, isAuthenticated: true })
  },

  clearAuth: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    set({ user: null, accessToken: null, isAuthenticated: false })
  },

  updateUser: (userData) => {
    const updated = { ...JSON.parse(localStorage.getItem('user') || '{}'), ...userData }
    localStorage.setItem('user', JSON.stringify(updated))
    set({ user: updated })
  },
}))

export default useAuthStore