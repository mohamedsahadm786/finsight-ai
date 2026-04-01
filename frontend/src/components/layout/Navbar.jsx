import { motion } from 'framer-motion'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Activity, Upload, FileText, Shield,
  Database, LogOut, ChevronRight
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import apiClient from '../../api/client'

export default function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, clearAuth } = useAuthStore()

  const navItems = [
    { icon: Activity, label: 'Dashboard', path: '/dashboard' },
    { icon: Upload,   label: 'Upload',    path: '/upload' },
    ...(user?.role === 'admin'      ? [{ icon: Shield,   label: 'Admin',      path: '/admin' }] : []),
    ...(user?.role === 'superadmin' ? [{ icon: Database, label: 'Superadmin', path: '/superadmin' }] : []),
  ]

  const handleLogout = async () => {
    try { await apiClient.post('/auth/logout') } catch {}
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="fixed left-0 top-0 h-screen w-64 glass-strong border-r border-crimson/10 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-crimson/10">
        <div className="flex items-center gap-3">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-crimson rounded-full flex items-center justify-center flex-shrink-0">
            <div className="w-2 h-2 bg-crimson rounded-full" />
          </motion.div>
          <div>
            <h1 className="font-display text-lg font-black text-ink-primary tracking-widest">
              FIN<span className="text-crimson">SIGHT</span>
            </h1>
            <p className="font-body text-ink-muted text-xs">AI Platform</p>
          </div>
        </div>
      </div>

      {/* User */}
      <div className="p-4 border-b border-crimson/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-crimson to-crimson-dark flex items-center justify-center font-display text-xs font-black text-white flex-shrink-0">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="overflow-hidden">
            <p className="font-body text-sm font-semibold text-ink-primary truncate">{user?.full_name}</p>
            <p className="font-body text-xs text-ink-muted capitalize">{user?.role}</p>
          </div>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ icon: Icon, label, path }) => {
          const active = location.pathname === path
          return (
            <motion.button key={label} onClick={() => navigate(path)} whileHover={{ x: 4 }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-left ${
                active
                  ? 'bg-crimson/10 border border-crimson/20 text-crimson'
                  : 'text-ink-secondary hover:text-ink-primary hover:bg-surface-raised'
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="font-body text-sm font-medium">{label}</span>
              {active && <ChevronRight className="w-3 h-3 ml-auto" />}
            </motion.button>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-crimson/10">
        <motion.button onClick={handleLogout} whileHover={{ x: 4 }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-ink-secondary hover:text-crimson transition-all duration-200">
          <LogOut className="w-4 h-4" />
          <span className="font-body text-sm">Sign Out</span>
        </motion.button>
      </div>
    </div>
  )
}