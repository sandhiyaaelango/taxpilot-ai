import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('taxpilot_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('taxpilot_token')
      localStorage.removeItem('taxpilot_user')
      if (window.location.pathname !== '/auth/login' && window.location.pathname !== '/') {
        window.location.href = '/auth/login'
      }
    }
    return Promise.reject(error)
  }
)
