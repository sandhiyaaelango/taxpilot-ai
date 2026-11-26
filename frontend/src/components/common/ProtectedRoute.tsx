import React, { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { api } from '@/services/api/client'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: ('AUDITOR' | 'ADMIN')[]
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, user, updateUser, clearAuth } = useAuthStore()
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) return
    let mounted = true
    async function syncUser() {
      setSyncing(true)
      try {
        const res = await api.get('/auth/me')
        if (mounted && res.data?.success && res.data?.data) {
          updateUser(res.data.data)
        }
      } catch (err: any) {
        if (mounted && err.response?.status === 401) {
          clearAuth()
        }
      } finally {
        if (mounted) setSyncing(false)
      }
    }
    syncUser()
    return () => {
      mounted = false
    }
  }, [isAuthenticated])

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />
  }

  const normalizedRole = (user?.role || '').toUpperCase() === 'ADMIN' || (user?.role || '').toUpperCase() === 'OWNER'
    ? 'ADMIN'
    : 'AUDITOR'

  if (!syncing && allowedRoles && !allowedRoles.includes(normalizedRole)) {
    const fallback = normalizedRole === 'ADMIN' ? '/app/admin/dashboard' : '/app/auditor/dashboard'
    return <Navigate to={fallback} replace />
  }

  return <>{children}</>
}
