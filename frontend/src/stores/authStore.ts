import { create } from 'zustand'

export interface User {
  id: string
  email: string
  full_name: string
  role: string
  organization_id?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (user: User, token: string) => void
  updateUser: (user: User) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: JSON.parse(localStorage.getItem('taxpilot_user') || 'null'),
  token: localStorage.getItem('taxpilot_token'),
  isAuthenticated: !!localStorage.getItem('taxpilot_token'),

  setAuth: (user, token) => {
    localStorage.setItem('taxpilot_token', token)
    localStorage.setItem('taxpilot_user', JSON.stringify(user))
    set({ user, token, isAuthenticated: true })
  },

  updateUser: (user) => {
    localStorage.setItem('taxpilot_user', JSON.stringify(user))
    set({ user })
  },

  clearAuth: () => {
    localStorage.removeItem('taxpilot_token')
    localStorage.removeItem('taxpilot_user')
    set({ user: null, token: null, isAuthenticated: false })
  }
}))
