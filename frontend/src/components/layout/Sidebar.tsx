import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import {
  LayoutDashboard,
  PlusCircle,
  FileSearch,
  Activity,
  Layers,
  Scale,
  FileText,
  FileCheck2,
  ShieldCheck,
  History,
  User,
  Users,
  ShieldAlert,
  Building2,
  Server,
  Cpu,
  HeartPulse,
  Settings,
  LogOut,
  X,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/components/ui/cn'

interface SidebarProps {
  mobileOpen?: boolean
  onClose?: () => void
}

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  badgeDot?: boolean
}

interface NavGroup {
  title: string
  items: NavItem[]
}

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()
  const role = (user?.role || 'AUDITOR').toUpperCase()
  const isAdmin = role === 'ADMIN' || role === 'OWNER'

  const auditorGroups: NavGroup[] = [
    {
      title: 'Workflow',
      items: [
        { to: '/app/auditor/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/app/auditor/new', label: 'New Investigation', icon: PlusCircle },
        { to: '/app/auditor/my-investigations', label: 'My Investigations', icon: FileSearch },
        { to: '/app/auditor/monitoring', label: 'AI Monitoring', icon: Activity, badgeDot: true },
        { to: '/app/auditor/results', label: 'Results', icon: Layers },
        { to: '/app/auditor/evidence', label: 'Evidence', icon: Scale },
        { to: '/app/auditor/response-drafts', label: 'Response Drafts', icon: FileText },
        { to: '/app/auditor/pending-review', label: 'Approval', icon: FileCheck2 },
      ],
    },
    {
      title: 'Archive',
      items: [
        { to: '/app/auditor/approved-reports', label: 'Approved Reports', icon: ShieldCheck },
        { to: '/app/auditor/history', label: 'History', icon: History },
      ],
    },
  ]

  const adminGroups: NavGroup[] = [
    {
      title: 'Admin Console',
      items: [
        { to: '/app/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/app/admin/users', label: 'User Management', icon: Users },
        { to: '/app/admin/roles', label: 'Role Management', icon: ShieldAlert },
        { to: '/app/admin/organizations', label: 'Organizations', icon: Building2 },
        { to: '/app/admin/investigations', label: 'Investigations', icon: FileSearch },
        { to: '/app/admin/agents', label: 'Agent Monitor', icon: Activity, badgeDot: true },
        { to: '/app/admin/mcp-status', label: 'MCP Status', icon: Server },
        { to: '/app/admin/llm-config', label: 'LLM Config', icon: Cpu },
        { to: '/app/admin/system-health', label: 'System Health', icon: HeartPulse },
        { to: '/app/admin/audit-logs', label: 'Audit Logs', icon: History },
      ],
    },
  ]

  const groups = isAdmin ? adminGroups : auditorGroups
  const profileRoute = isAdmin ? '/app/admin/profile' : '/app/auditor/profile'
  const settingsRoute = isAdmin ? '/app/admin/settings' : '/app/auditor/profile'

  const handleSignOut = () => {
    clearAuth()
    if (onClose) onClose()
    navigate('/auth/login')
  }

  const railContent = (isDrawer = false) => (
    <aside
      aria-label="Primary navigation"
      className={cn(
        'flex flex-col bg-elevated border border-border-subtle rounded-card shadow-glass overflow-hidden select-none',
        isDrawer
          ? 'w-[260px] h-full'
          : 'h-[calc(100vh-24px)] m-3 mr-0 lg:w-[76px] xl:w-[248px] shrink-0 transition-[width] duration-200'
      )}
    >
      {/* Top Mint Brand Logo */}
      <div className="h-[68px] px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-nav bg-accent-mint/12 border border-accent-mint/30 flex items-center justify-center shrink-0">
            <svg
              viewBox="0 0 24 24"
              className="w-5 h-5 text-accent-mint"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 2L4 6v6c0 5.5 3.4 10.6 8 12 4.6-1.4 8-6.5 8-12V6l-8-4z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </div>
          <div className={cn('min-w-0', !isDrawer && 'lg:hidden xl:block')}>
            <div className="text-[16px] font-semibold tracking-tight text-txt-primary leading-none">
              TaxPilot <span className="text-accent-mint">AI</span>
            </div>
            <div className="text-[11px] text-txt-muted mt-1 truncate">
              {isAdmin ? 'Admin Console' : 'GST Audit Suite'}
            </div>
          </div>
        </div>
        {isDrawer && onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="p-2 rounded-full text-txt-secondary hover:text-txt-primary hover:bg-surface-2"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Scrollable Navigation Groups */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-5">
        {groups.map((group) => (
          <div key={group.title}>
            <div
              className={cn(
                'px-3 mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-txt-muted',
                !isDrawer && 'lg:hidden xl:block'
              )}
            >
              {group.title}
            </div>
            <div className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    title={item.label}
                    onClick={onClose}
                    className={({ isActive }) =>
                      cn(
                        'relative flex items-center gap-3 px-3 py-2.5 rounded-nav text-[14px] font-medium transition-all duration-150',
                        !isDrawer && 'lg:justify-center xl:justify-start',
                        isActive
                          ? 'bg-brand-orange text-white shadow-orange-glow'
                          : 'text-txt-secondary hover:text-txt-primary hover:bg-surface-2'
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <div className="relative shrink-0 flex items-center justify-center">
                          <Icon className="w-5 h-5" strokeWidth={1.75} />
                          {item.badgeDot && !isActive && (
                            <span
                              className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-brand-orange ring-2 ring-elevated"
                              aria-hidden="true"
                            />
                          )}
                        </div>
                        <span className={cn('truncate', !isDrawer && 'lg:hidden xl:block')}>
                          {item.label}
                        </span>
                      </>
                    )}
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom Pinned: Profile, Settings, Sign out */}
      <div className="p-3 border-t border-border-subtle space-y-1 shrink-0">
        <NavLink
          to={profileRoute}
          title="Profile"
          onClick={onClose}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-nav text-[14px] font-medium transition-all duration-150',
              !isDrawer && 'lg:justify-center xl:justify-start',
              isActive
                ? 'bg-brand-orange text-white shadow-orange-glow'
                : 'text-txt-secondary hover:text-txt-primary hover:bg-surface-2'
            )
          }
        >
          <User className="w-5 h-5 shrink-0" strokeWidth={1.75} />
          <span className={cn('truncate', !isDrawer && 'lg:hidden xl:block')}>Profile</span>
        </NavLink>

        {isAdmin && (
          <NavLink
            to={settingsRoute}
            title="Settings"
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-nav text-[14px] font-medium transition-all duration-150',
                !isDrawer && 'lg:justify-center xl:justify-start',
                isActive
                  ? 'bg-brand-orange text-white shadow-orange-glow'
                  : 'text-txt-secondary hover:text-txt-primary hover:bg-surface-2'
              )
            }
          >
            <Settings className="w-5 h-5 shrink-0" strokeWidth={1.75} />
            <span className={cn('truncate', !isDrawer && 'lg:hidden xl:block')}>Settings</span>
          </NavLink>
        )}

        <button
          type="button"
          onClick={handleSignOut}
          title="Sign out"
          aria-label="Sign out"
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-nav text-[14px] font-medium text-txt-secondary hover:text-danger hover:bg-danger/10 transition-all duration-150',
            !isDrawer && 'lg:justify-center xl:justify-start'
          )}
        >
          <LogOut className="w-5 h-5 shrink-0" strokeWidth={1.75} />
          <span className={cn('truncate', !isDrawer && 'lg:hidden xl:block')}>Sign out</span>
        </button>
      </div>
    </aside>
  )

  return (
    <>
      {/* Desktop & Tablet Rail */}
      <div className="hidden lg:block">{railContent(false)}</div>

      {/* Mobile Off-Canvas Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />
          <div className="relative z-10 p-3 h-full">{railContent(true)}</div>
        </div>
      )}
    </>
  )
}
