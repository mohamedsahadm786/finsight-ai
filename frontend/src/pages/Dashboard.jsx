import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileText, Upload, TrendingUp, Shield, Clock,
  AlertTriangle, CheckCircle, Loader, LogOut,
  ChevronRight, Activity, Database, Cpu
} from 'lucide-react'
import useAuthStore from '../store/authStore'
import apiClient from '../api/client'

// ── Sidebar ───────────────────────────────────────────────────────
function Sidebar({ user, onLogout }) {
  const navigate = useNavigate()
  const navItems = [
    { icon: Activity, label: 'Dashboard', path: '/dashboard', active: true },
    { icon: Upload, label: 'Upload', path: '/upload' },
   
    ...(user?.role === 'admin' ? [{ icon: Shield, label: 'Admin', path: '/admin' }] : []),
    ...(user?.role === 'superadmin' ? [{ icon: Database, label: 'Superadmin', path: '/superadmin' }] : []),
  ]

  return (
    <div className="fixed left-0 top-0 h-screen w-64 glass-strong border-r border-crimson/10 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-crimson/10">
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-crimson rounded-full flex items-center justify-center flex-shrink-0"
          >
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

      {/* User info */}
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

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ icon: Icon, label, path, active }) => (
          <motion.button
            key={label}
            onClick={() => {
              if (path.includes('#')) {
                const id = path.split('#')[1]
                const el = document.getElementById(id)
                if (el) {
                  const top = el.getBoundingClientRect().top + window.pageYOffset - 20
                  window.scrollTo({ top, behavior: 'smooth' })
                }
              } else {
                navigate(path)
              }
            }}
            whileHover={{ x: 4 }}
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
        ))}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-crimson/10">
        <motion.button
          onClick={onLogout}
          whileHover={{ x: 4 }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-ink-secondary hover:text-crimson transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          <span className="font-body text-sm">Sign Out</span>
        </motion.button>
      </div>
    </div>
  )
}

// ── Risk tier badge ───────────────────────────────────────────────
function RiskBadge({ tier }) {
  const config = {
    low: { color: 'text-risk-low border-risk-low/30 bg-risk-low/10', label: 'LOW RISK' },
    medium: { color: 'text-risk-medium border-risk-medium/30 bg-risk-medium/10', label: 'MEDIUM' },
    high: { color: 'text-risk-high border-risk-high/30 bg-risk-high/10', label: 'HIGH RISK' },
    distress: { color: 'text-risk-distress border-risk-distress/30 bg-risk-distress/10', label: 'DISTRESS' },
  }
  const c = config[tier] || config.medium
  return (
    <span className={`font-display text-xs px-2 py-0.5 rounded border font-bold tracking-wider ${c.color}`}>
      {c.label}
    </span>
  )
}

// ── Status badge ──────────────────────────────────────────────────
function StatusBadge({ status }) {
  const config = {
    completed: { icon: CheckCircle, color: 'text-risk-low', label: 'Completed' },
    processing: { icon: Loader, color: 'text-electric-light', label: 'Processing' },
    failed: { icon: AlertTriangle, color: 'text-crimson', label: 'Failed' },
    uploaded: { icon: Clock, color: 'text-ink-secondary', label: 'Queued' },
  }
  const c = config[status] || config.uploaded
  const Icon = c.icon
  return (
    <span className={`flex items-center gap-1 font-body text-xs ${c.color}`}>
      <Icon className="w-3 h-3" />
      {c.label}
    </span>
  )
}

// ── Main Dashboard ────────────────────────────────────────────────
export default function Dashboard() {
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await apiClient.get('/documents/')
      setDocuments(response.data.documents || [])
    } catch (err) {
      console.error('Failed to fetch documents:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await apiClient.post('/auth/logout')
    } catch (err) {
      console.error('Logout error:', err)
    }
    clearAuth()
    navigate('/login')
  }

  const completed = documents.filter(d => d.status === 'completed').length
  const processing = documents.filter(d => d.status === 'processing').length
  const total = documents.length

  const stats = [
    { icon: FileText, label: 'Total Documents', value: total, color: 'text-electric-light' },
    { icon: CheckCircle, label: 'Completed', value: completed, color: 'text-risk-low' },
    { icon: Cpu, label: 'Processing', value: processing, color: 'text-risk-medium' },
    { icon: TrendingUp, label: 'Success Rate', value: total > 0 ? `${Math.round((completed / total) * 100)}%` : '—', color: 'text-crimson' },
  ]

  return (
    <div className="min-h-screen bg-void flex">
      <Sidebar user={user} onLogout={handleLogout} />

      {/* Main content */}
      <div className="ml-64 flex-1 p-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-2xl font-black text-ink-primary tracking-wider">
                COMMAND CENTER
              </h2>
              <p className="font-body text-ink-secondary text-sm mt-1">
                Welcome back, <span className="text-crimson font-semibold">{user?.full_name}</span>
              </p>
            </div>
            <motion.button
              onClick={() => navigate('/upload')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 bg-crimson hover:bg-crimson-light text-white font-display font-bold px-5 py-2.5 rounded-lg tracking-widest text-sm transition-all duration-300 shadow-crimson"
            >
              <Upload className="w-4 h-4" />
              NEW ANALYSIS
            </motion.button>
          </div>
        </motion.div>

        {/* Stats grid */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {stats.map(({ icon: Icon, label, value, color }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass rounded-xl p-4 border border-crimson/10 hover:border-crimson/25 transition-all duration-300"
            >
              <div className="flex items-center justify-between mb-3">
                <Icon className={`w-5 h-5 ${color}`} />
                <div className="w-1.5 h-1.5 rounded-full bg-crimson animate-pulse" />
              </div>
              <div className={`font-display text-2xl font-black ${color} mb-1`}>{value}</div>
              <div className="font-body text-ink-muted text-xs tracking-wider">{label}</div>
            </motion.div>
          ))}
        </div>

        {/* Documents table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass rounded-xl border border-crimson/10 overflow-hidden"
        >
          <div id="reports" className="flex items-center justify-between p-5 border-b border-crimson/10">
            <h3 className="font-display text-sm font-bold text-ink-primary tracking-wider">
              RECENT ANALYSES
            </h3>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-risk-low animate-pulse" />
              <span className="font-body text-ink-muted text-xs">Live</span>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-8 h-8 border-2 border-crimson border-t-transparent rounded-full"
              />
            </div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="w-16 h-16 rounded-full border border-crimson/20 flex items-center justify-center">
                <FileText className="w-7 h-7 text-ink-muted" />
              </div>
              <div className="text-center">
                <p className="font-display text-sm text-ink-secondary tracking-wider mb-1">NO ANALYSES YET</p>
                <p className="font-body text-ink-muted text-xs">Upload your first financial document to get started</p>
              </div>
              <motion.button
                onClick={() => navigate('/upload')}
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-2 border border-crimson/30 hover:border-crimson text-crimson font-display text-xs font-bold px-4 py-2 rounded-lg tracking-widest transition-all duration-300"
              >
                <Upload className="w-3 h-3" />
                UPLOAD DOCUMENT
              </motion.button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-crimson/10">
                    {['Document', 'Type', 'Status', 'Risk', 'Date', 'Action'].map(h => (
                      <th key={h} className="text-left px-5 py-3 font-body text-ink-muted text-xs tracking-widest uppercase">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc, i) => (
                    <motion.tr
                      key={doc.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="border-b border-crimson/5 hover:bg-surface-raised/50 transition-colors duration-200"
                    >
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-ink-muted flex-shrink-0" />
                          <span className="font-body text-sm text-ink-primary truncate max-w-48">
                            {doc.original_filename}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-body text-xs text-ink-secondary capitalize">
                          {doc.document_type?.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <StatusBadge status={doc.status} />
                      </td>
                      <td className="px-5 py-4">
                        {doc.status === 'completed' ? (
                          <span className="font-body text-xs text-ink-secondary">See Report</span>
                        ) : (
                          <span className="text-ink-muted text-xs">—</span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-body text-xs text-ink-secondary">
                          {new Date(doc.created_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        {doc.status === 'completed' ? (
                          <motion.button
                            onClick={() => navigate(`/report/${doc.id}`)}
                            whileHover={{ scale: 1.05 }}
                            className="font-display text-xs font-bold text-crimson hover:text-crimson-light tracking-wider transition-colors"
                          >
                            VIEW →
                          </motion.button>
                        ) : doc.status === 'processing' ? (
                          <motion.button
                            onClick={() => navigate(`/processing/${doc.id}`)}
                            className="font-body text-xs text-electric-light"
                          >
                            MONITOR
                          </motion.button>
                        ) : (
                          <span className="text-ink-muted text-xs">—</span>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}