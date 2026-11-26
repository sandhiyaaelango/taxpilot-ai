import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'react-hot-toast'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#170B05',
            color: '#FFFFFF',
            border: '1px solid rgba(255, 255, 255, 0.14)',
            borderRadius: '16px',
            fontSize: '14px',
            fontFamily: 'Outfit, system-ui, sans-serif',
            boxShadow: '0 16px 40px -12px rgba(0, 0, 0, 0.75), inset 0 1px 0 0 rgba(255, 255, 255, 0.06)',
            backdropFilter: 'blur(16px)',
          },
          success: { iconTheme: { primary: '#30FFAC', secondary: '#0F0703' } },
          error: { iconTheme: { primary: '#FF5A4F', secondary: '#0F0703' } },
        }}
      />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
