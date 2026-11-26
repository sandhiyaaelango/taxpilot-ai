import { createBrowserRouter, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'

// Layouts
import { AppLayout } from '@/components/layout/AppLayout'
import { AuthLayout } from '@/components/layout/AuthLayout'

// Eagerly loaded
import { LoginPage } from '@/features/authentication/LoginPage'
import { RegisterPage } from '@/features/authentication/RegisterPage'
import { LandingPage } from '@/features/dashboard/LandingPage'

// Protected route guard
import { ProtectedRoute } from '@/components/common/ProtectedRoute'
import { useAuthStore } from '@/stores/authStore'

// AUDITOR Pages (Lazy Loaded)
const AuditorDashboardPage = lazy(() => import('@/features/auditor/AuditorDashboardPage').then(m => ({ default: m.AuditorDashboardPage })))
const AuditorNewInvestigationPage = lazy(() => import('@/features/auditor/AuditorNewInvestigationPage').then(m => ({ default: m.AuditorNewInvestigationPage })))
const AuditorAiMonitoringPage = lazy(() => import('@/features/auditor/AuditorAiMonitoringPage').then(m => ({ default: m.AuditorAiMonitoringPage })))
const AuditorInvestigationResultsPage = lazy(() => import('@/features/auditor/AuditorInvestigationResultsPage').then(m => ({ default: m.AuditorInvestigationResultsPage })))
const AuditorEvidencePage = lazy(() => import('@/features/auditor/AuditorEvidencePage').then(m => ({ default: m.AuditorEvidencePage })))
const AuditorResponseDraftsPage = lazy(() => import('@/features/auditor/AuditorResponseDraftsPage').then(m => ({ default: m.AuditorResponseDraftsPage })))
const AuditorPendingReviewPage = lazy(() => import('@/features/auditor/AuditorPendingReviewPage').then(m => ({ default: m.AuditorPendingReviewPage })))
const AuditorApprovedReportsPage = lazy(() => import('@/features/auditor/AuditorApprovedReportsPage').then(m => ({ default: m.AuditorApprovedReportsPage })))
const AuditorHistoryPage = lazy(() => import('@/features/auditor/AuditorHistoryPage').then(m => ({ default: m.AuditorHistoryPage })))
const AuditorProfilePage = lazy(() => import('@/features/auditor/AuditorProfilePage').then(m => ({ default: m.AuditorProfilePage })))

// Shared / Case Workspace (Lazy Loaded)
const InvestigationsPage = lazy(() => import('@/features/investigations/InvestigationsPage').then(m => ({ default: m.InvestigationsPage })))
const InvestigationWorkspace = lazy(() => import('@/features/investigations/InvestigationWorkspace').then(m => ({ default: m.InvestigationWorkspace })))

// ADMIN Pages (Lazy Loaded)
const AdminDashboardPage = lazy(() => import('@/features/admin/AdminDashboardPage').then(m => ({ default: m.AdminDashboardPage })))
const AdminUserManagementPage = lazy(() => import('@/features/admin/AdminUserManagementPage').then(m => ({ default: m.AdminUserManagementPage })))
const AdminOrganizationPage = lazy(() => import('@/features/admin/AdminOrganizationPage').then(m => ({ default: m.AdminOrganizationPage })))
const AdminMcpStatusPage = lazy(() => import('@/features/admin/AdminMcpStatusPage').then(m => ({ default: m.AdminMcpStatusPage })))
const AdminLlmConfigPage = lazy(() => import('@/features/admin/AdminLlmConfigPage').then(m => ({ default: m.AdminLlmConfigPage })))
const AdminSystemHealthPage = lazy(() => import('@/features/admin/AdminSystemHealthPage').then(m => ({ default: m.AdminSystemHealthPage })))
const AdminSettingsPage = lazy(() => import('@/features/admin/AdminSettingsPage').then(m => ({ default: m.AdminSettingsPage })))
const AdminProfilePage = lazy(() => import('@/features/admin/AdminProfilePage').then(m => ({ default: m.AdminProfilePage })))
const AgentMonitorPage = lazy(() => import('@/features/agent-monitor/AgentMonitorPage').then(m => ({ default: m.AgentMonitorPage })))
const AuditLogsPage = lazy(() => import('@/features/audit-logs/AuditLogsPage').then(m => ({ default: m.AuditLogsPage })))

const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-2 border-brand-orange border-t-transparent rounded-full animate-spin" />
      <span className="text-xs text-txt-secondary font-medium">Loading workspace...</span>
    </div>
  </div>
)

// Role Redirector Component
function RoleIndexRedirect() {
  const { user } = useAuthStore()
  const role = (user?.role || 'AUDITOR').toUpperCase()
  if (role === 'ADMIN' || role === 'OWNER') {
    return <Navigate to="/app/admin/dashboard" replace />
  }
  return <Navigate to="/app/auditor/dashboard" replace />
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/auth',
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      { index: true, element: <Navigate to="login" replace /> },
    ],
  },
  {
    path: '/app',
    element: <ProtectedRoute><AppLayout /></ProtectedRoute>,
    children: [
      { index: true, element: <RoleIndexRedirect /> },

      // Legacy fallback redirects
      { path: 'dashboard', element: <RoleIndexRedirect /> },
      { path: 'approvals', element: <Navigate to="/app/auditor/pending-review" replace /> },

      // ==========================================
      // AUDITOR WORKSPACE ROUTES (11 items)
      // ==========================================
      {
        path: 'auditor',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorDashboardPage /></Suspense></ProtectedRoute>,
        children: []
      },
      {
        path: 'auditor/dashboard',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorDashboardPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/new',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorNewInvestigationPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/my-investigations',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorHistoryPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/monitoring',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorAiMonitoringPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/results',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorInvestigationResultsPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/evidence',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorEvidencePage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/response-drafts',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorResponseDraftsPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/pending-review',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorPendingReviewPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/approved-reports',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorApprovedReportsPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/history',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorHistoryPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/profile',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><AuditorProfilePage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'auditor/investigations/:id',
        element: <ProtectedRoute allowedRoles={['AUDITOR']}><Suspense fallback={<PageLoader />}><InvestigationWorkspace /></Suspense></ProtectedRoute>,
      },

      // Shared / Workspace
      {
        path: 'investigations',
        element: <Suspense fallback={<PageLoader />}><AuditorHistoryPage /></Suspense>,
      },
      {
        path: 'investigations/:id',
        element: <Suspense fallback={<PageLoader />}><InvestigationWorkspace /></Suspense>,
      },

      // ==========================================
      // ADMIN WORKSPACE ROUTES (12 items)
      // ==========================================
      {
        path: 'admin/dashboard',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminDashboardPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/users',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminUserManagementPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/roles',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminUserManagementPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/organizations',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminOrganizationPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/investigations',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AuditorHistoryPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/agents',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AgentMonitorPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/mcp-status',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminMcpStatusPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/llm-config',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminLlmConfigPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/system-health',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminSystemHealthPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/audit-logs',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AuditLogsPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/settings',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminSettingsPage /></Suspense></ProtectedRoute>,
      },
      {
        path: 'admin/profile',
        element: <ProtectedRoute allowedRoles={['ADMIN']}><Suspense fallback={<PageLoader />}><AdminProfilePage /></Suspense></ProtectedRoute>,
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
