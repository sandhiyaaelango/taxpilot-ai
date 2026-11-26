import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Search, RefreshCw, Bell, ChevronDown, User, LogOut, Menu } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'

interface TopNavProps {
  onMenuClick?: () => void
  onRefresh?: () => void
}

export function TopNav({ onMenuClick, onRefresh }: TopNavProps) {
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const role = (user?.role || 'AUDITOR').toUpperCase()
  const isAdmin = role === 'ADMIN' || role === 'OWNER'
  const displayRole = isAdmin ? 'Admin' : 'Auditor'

  useEffect(() => {
    const handleShortcut = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.code === 'Space') {
        e.preventDefault()
        searchInputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [])

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleOutside)
    return () => document.removeEventListener('mousedown', handleOutside)
  }, [])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const target = isAdmin ? '/app/admin/investigations' : '/app/auditor/my-investigations'
    navigate(searchQuery.trim() ? `${target}?q=${encodeURIComponent(searchQuery.trim())}` : target)
  }

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh()
    } else {
      window.location.reload()
    }
  }

  const handleLogout = () => {
    clearAuth()
    navigate('/auth/login')
  }

  return (
    <header className="h-[72px] px-5 md:px-8 flex items-center justify-between gap-4 shrink-0">
      {/* Left: Mobile Drawer Trigger + Search Pill */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Open navigation menu"
            className="lg:hidden w-10 h-10 rounded-full bg-surface-1 border border-border-subtle flex items-center justify-center text-txt-secondary hover:text-txt-primary hover:bg-surface-2 transition-colors shrink-0"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 text-txt-muted absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            ref={searchInputRef}
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search investigations, GSTIN, notice..."
            aria-label="Search investigations"
            className="w-full h-11 pl-11 pr-24 rounded-full bg-surface-1 border border-border-subtle text-[14px] text-txt-primary placeholder:text-txt-muted focus:outline-none focus:border-brand-orange/60 focus:bg-surface-2 transition-all"
          />
          <button
            type="button"
            onClick={() => searchInputRef.current?.focus()}
            className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-2 border border-border-subtle text-[11px] font-medium text-txt-secondary absolute right-2 top-1/2 -translate-y-1/2 hover:text-txt-primary"
          >
            <span>⌘ + Space</span>
          </button>
        </form>
      </div>

      {/* Right: Round Action Buttons + User Pill */}
      <div className="flex items-center gap-2.5 shrink-0">
        <button
          type="button"
          onClick={handleRefresh}
          aria-label="Refresh workspace"
          title="Refresh"
          className="w-10 h-10 rounded-full bg-surface-1 border border-border-subtle flex items-center justify-center text-txt-secondary hover:text-txt-primary hover:bg-surface-2 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={() => navigate(isAdmin ? '/app/admin/agents' : '/app/auditor/monitoring')}
          aria-label="Notifications and active pipeline"
          title="Pipeline notifications"
          className="relative w-10 h-10 rounded-full bg-surface-1 border border-border-subtle flex items-center justify-center text-txt-secondary hover:text-txt-primary hover:bg-surface-2 transition-colors"
        >
          <Bell className="w-4 h-4" />
          <span
            className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-brand-orange ring-2 ring-base"
            aria-hidden="true"
          />
        </button>

        {/* User Profile Pill */}
        <div ref={dropdownRef} className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((p) => !p)}
            aria-expanded={menuOpen}
            aria-label="User menu"
            className="flex items-center gap-2.5 pl-1.5 pr-3 py-1 rounded-full bg-surface-1 border border-border-subtle hover:bg-surface-2 hover:border-border-strong transition-colors"
          >
            <Avatar name={user?.full_name || user?.email} size="sm" />
            <div className="hidden sm:block text-left">
              <div className="text-[13px] font-medium text-txt-primary leading-tight max-w-[140px] truncate">
                {user?.full_name || 'Chartered Accountant'}
              </div>
              <div className="text-[11px] text-txt-muted leading-tight">
                {displayRole}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-txt-muted hidden sm:block" />
          </button>

          {menuOpen && (
            <div
              role="menu"
              className="absolute right-0 mt-2 w-52 rounded-inner bg-elevated border border-border-strong p-1.5 shadow-2xl z-50"
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false)
                  navigate(isAdmin ? '/app/admin/profile' : '/app/auditor/profile')
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] text-txt-secondary hover:text-txt-primary hover:bg-surface-2 transition-colors"
              >
                <User className="w-4 h-4" />
                <span>Profile</span>
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={handleLogout}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13.5px] text-danger hover:bg-danger/12 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
