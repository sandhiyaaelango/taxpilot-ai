import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="relative flex h-screen w-screen overflow-hidden bg-base text-txt-primary">
      {/* Subtle fixed ambient orange radial glows */}
      <div className="ambient-glow-canvas" aria-hidden="true">
        <div className="ambient-glow-top-right" />
        <div className="ambient-glow-bottom-left" />
      </div>

      {/* Floating Sidebar Rail */}
      <div className="relative z-20 flex">
        <Sidebar
          mobileOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
        />
      </div>

      {/* Top bar + Scrollable Content */}
      <div className="relative z-10 flex flex-col flex-1 h-screen overflow-hidden min-w-0">
        <TopNav onMenuClick={() => setMobileMenuOpen(true)} />
        <main className="flex-1 overflow-y-auto px-5 pb-8 pt-2 md:px-8">
          <div className="max-w-[1440px] mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
