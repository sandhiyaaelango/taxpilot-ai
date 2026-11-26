import React from 'react'
import { Outlet, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function AuthLayout() {
  const { isAuthenticated, user } = useAuthStore()

  if (isAuthenticated) {
    const role = (user?.role || '').toUpperCase()
    const target = role === 'ADMIN' || role === 'OWNER' ? '/app/admin/dashboard' : '/app/auditor/dashboard'
    return <Navigate to={target} replace />
  }

  return (
    <div className="min-h-screen bg-base text-txt-primary relative overflow-hidden">
      <div className="ambient-glow-canvas" aria-hidden="true">
        <div className="ambient-glow-top-right" />
        <div className="ambient-glow-bottom-left" />
      </div>
      <div className="relative z-10">
        <Outlet />
      </div>
    </div>
  )
}
