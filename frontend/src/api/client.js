/**
 * Axios client — all API calls go through here.
 * Automatically attaches the access token from Zustand store.
 * Automatically handles token expiry.
 *
 * baseURL logic:
 *   - In development (Vite dev server): calls go to http://localhost:8000
 *   - In production (served by Nginx): calls go to /api (same origin, Nginx proxies to FastAPI)
 */
import axios from 'axios'

const baseURL = import.meta.env.DEV
  ? 'http://localhost:8000'
  : '/api'

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// ── Request interceptor — attach access token ─────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor — handle 401 errors ──────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient