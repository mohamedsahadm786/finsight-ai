import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users, UserPlus, ChevronLeft, Shield,
  CheckCircle, AlertCircle, X, Mail,
  UserX, UserCheck, Copy, Check
} from 'lucide-react'
import useAuthStore from '../store/authStore'
import apiClient from '../api/client'

// Generate a strong random password
function generatePassword() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789@#$!'
  let pwd = ''
  for (let i = 0; i < 12; i++) {
    pwd += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return pwd
}

export default function AdminPanel() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showInvite, setShowInvite] = useState(false)
  const [inviteForm, setInviteForm] = useState({
    email: '',
    full_name: '',
    role: 'analyst',
    temporary_password: generatePassword(),
  })
  const [inviteLoading, setInviteLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [successInvite, setSuccessInvite] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => { fetchUsers() }, [])

  const fetchUsers = async () => {
    try {
      const response = await apiClient.get('/admin/users')
      setUsers(response.data.users || [])
    } catch (err) {
      console.error('Failed to fetch users:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleInvite = async (e) => {
    e.preventDefault()
    setInviteLoading(true)
    try {
      await apiClient.post('/admin/users/invite', {
        email: inviteForm.email,
        full_name: inviteForm.full_name,
        role: inviteForm.role,
        temporary_password: inviteForm.temporary_password,
      })
      setSuccessInvite({
        email: inviteForm.email,
        full_name: inviteForm.full_name,
        password: inviteForm.temporary_password,
      })
      setInviteForm({ email: '', full_name: '', role: 'analyst', temporary_password: generatePassword() })
      fetchUsers()
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to invite user' })
      setShowInvite(false)
    } finally {
      setInviteLoading(false)
    }
  }

  const handleCopyPassword = (pwd) => {
    navigator.clipboard.writeText(pwd)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDeactivate = async (userId, userName) => {
    if (!confirm(`Deactivate ${userName}?`)) return
    try {
      await apiClient.patch(`/admin/users/${userId}/deactivate`)
      setMessage({ type: 'success', text: `${userName} has been deactivated` })
      fetchUsers()
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to deactivate user' })
    }
  }

  const handleReactivate = async (userId, userName) => {
    if (!confirm(`Reactivate ${userName}?`)) return
    try {
      await apiClient.patch(`/admin/users/${userId}/reactivate`)
      setMessage({ type: 'success', text: `${userName} has been reactivated` })
      fetchUsers()
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to reactivate user' })
    }
  }

  const handleRoleChange = async (userId, newRole) => {
    try {
      await apiClient.patch(`/admin/users/${userId}/role`, { role: newRole })
      setMessage({ type: 'success', text: 'Role updated successfully' })
      fetchUsers()
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update role' })
    }
  }

  const roleColors = {
    admin:   'text-crimson border-crimson/30 bg-crimson/10',
    analyst: 'text-electric-light border-electric/30 bg-electric/10',
    viewer:  'text-ink-secondary border-ink-muted/30 bg-surface-raised',
  }

  return (
    <div className="min-h-screen bg-void">
      {/* Top nav */}
      <div className="sticky top-0 z-40 glass-strong border-b border-crimson/10 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-ink-secondary hover:text-crimson transition-colors font-body text-sm">
            <ChevronLeft className="w-4 h-4" />
            Dashboard
          </button>
          <div className="w-px h-4 bg-ink-muted/20" />
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-crimson" />
            <h1 className="font-display text-sm font-black text-ink-primary tracking-widest">ADMIN PANEL</h1>
          </div>
        </div>
        <motion.button
          onClick={() => { setSuccessInvite(null); setShowInvite(true) }}
          whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
          className="flex items-center gap-2 bg-crimson hover:bg-crimson-light text-white font-display font-bold px-4 py-2 rounded-lg tracking-widest text-xs transition-all duration-300 shadow-crimson"
        >
          <UserPlus className="w-3.5 h-3.5" />
          INVITE USER
        </motion.button>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Message */}
        <AnimatePresence>
          {message.text && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className={`flex items-center justify-between gap-2 rounded-lg p-3 mb-6 ${
                message.type === 'success' ? 'bg-risk-low/10 border border-risk-low/30' : 'bg-crimson/10 border border-crimson/30'
              }`}>
              <div className="flex items-center gap-2">
                {message.type === 'success'
                  ? <CheckCircle className="w-4 h-4 text-risk-low" />
                  : <AlertCircle className="w-4 h-4 text-crimson" />}
                <span className={`font-body text-sm ${message.type === 'success' ? 'text-risk-low' : 'text-crimson'}`}>
                  {message.text}
                </span>
              </div>
              <button onClick={() => setMessage({ type: '', text: '' })}>
                <X className="w-4 h-4 text-ink-muted hover:text-ink-primary" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Users table */}
        <div className="glass rounded-xl border border-crimson/10 overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-crimson/10">
            <div className="flex items-center gap-3">
              <Users className="w-4 h-4 text-crimson" />
              <h3 className="font-display text-sm font-bold text-ink-primary tracking-wider">TEAM MEMBERS</h3>
              <span className="font-display text-xs text-ink-muted bg-surface-raised px-2 py-0.5 rounded-full">
                {users.length}
              </span>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-8 h-8 border-2 border-crimson border-t-transparent rounded-full" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-crimson/10">
                    {['Member', 'Email', 'Role', 'Status', 'Actions'].map(h => (
                      <th key={h} className="text-left px-5 py-3 font-body text-ink-muted text-xs tracking-widest uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, i) => (
                    <motion.tr key={u.id}
                      initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="border-b border-crimson/5 hover:bg-surface-raised/30 transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-crimson to-crimson-dark flex items-center justify-center font-display text-xs font-black text-white flex-shrink-0">
                            {u.full_name?.charAt(0)}
                          </div>
                          <span className="font-body text-sm text-ink-primary">{u.full_name}</span>
                          {u.id === user?.id && <span className="font-body text-xs text-ink-muted">(you)</span>}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-body text-xs text-ink-secondary">{u.email}</span>
                      </td>
                      <td className="px-5 py-4">
                        {u.id !== user?.id ? (
                          <select value={u.role} onChange={(e) => handleRoleChange(u.id, e.target.value)}
                            className={`font-display text-xs font-bold px-2 py-1 rounded border bg-transparent cursor-pointer ${roleColors[u.role]}`}>
                            <option value="admin">ADMIN</option>
                            <option value="analyst">ANALYST</option>
                            <option value="viewer">VIEWER</option>
                          </select>
                        ) : (
                          <span className={`font-display text-xs font-bold px-2 py-1 rounded border ${roleColors[u.role]}`}>
                            {u.role.toUpperCase()}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <span className={`flex items-center gap-1.5 font-body text-xs ${u.is_active ? 'text-risk-low' : 'text-ink-muted'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-risk-low' : 'bg-ink-muted'}`} />
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          {u.id !== user?.id && u.is_active && (
                            <motion.button onClick={() => handleDeactivate(u.id, u.full_name)}
                              whileHover={{ scale: 1.1 }} title="Deactivate"
                              className="text-ink-muted hover:text-crimson transition-colors">
                              <UserX className="w-4 h-4" />
                            </motion.button>
                          )}
                          {u.id !== user?.id && !u.is_active && (
                            <motion.button onClick={() => handleReactivate(u.id, u.full_name)}
                              whileHover={{ scale: 1.1 }} title="Reactivate"
                              className="text-ink-muted hover:text-risk-low transition-colors">
                              <UserCheck className="w-4 h-4" />
                            </motion.button>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Invite modal */}
      <AnimatePresence>
        {showInvite && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-void/80 backdrop-blur-sm flex items-center justify-center z-50 px-4"
            onClick={(e) => e.target === e.currentTarget && setShowInvite(false)}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-strong rounded-2xl p-8 w-full max-w-md relative overflow-hidden">
              <div className="absolute top-0 left-0 w-10 h-10 border-t-2 border-l-2 border-crimson opacity-60" />
              <div className="absolute bottom-0 right-0 w-10 h-10 border-b-2 border-r-2 border-crimson opacity-60" />

              <AnimatePresence mode="wait">
                {/* Success state — show credentials */}
                {successInvite ? (
                  <motion.div key="success" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="font-display text-lg font-bold text-ink-primary tracking-wider">USER INVITED</h3>
                      <button onClick={() => { setShowInvite(false); setSuccessInvite(null) }}
                        className="text-ink-muted hover:text-crimson transition-colors">
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="w-14 h-14 rounded-full bg-risk-low/10 border border-risk-low/30 flex items-center justify-center mx-auto mb-4">
                      <CheckCircle className="w-7 h-7 text-risk-low" />
                    </div>

                    <p className="font-display text-sm font-bold text-ink-primary text-center tracking-wider mb-1">
                      {successInvite.full_name}
                    </p>
                    <p className="font-body text-xs text-ink-secondary text-center mb-6">{successInvite.email}</p>

                    <div className="bg-surface-raised rounded-xl p-4 border border-crimson/15 mb-4">
                      <p className="font-body text-ink-muted text-xs tracking-widest uppercase mb-2">
                        Share these credentials with the user
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-body text-xs text-ink-secondary">Email:</span>
                          <span className="font-mono text-xs text-ink-primary">{successInvite.email}</span>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <span className="font-body text-xs text-ink-secondary">Password:</span>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-electric-light bg-void/60 px-2 py-1 rounded border border-ink-muted/20">
                              {successInvite.password}
                            </span>
                            <motion.button
                              onClick={() => handleCopyPassword(successInvite.password)}
                              whileHover={{ scale: 1.1 }}
                              className="text-ink-muted hover:text-crimson transition-colors"
                            >
                              {copied ? <Check className="w-3.5 h-3.5 text-risk-low" /> : <Copy className="w-3.5 h-3.5" />}
                            </motion.button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <p className="font-body text-ink-muted text-xs text-center mb-4">
                      The user can change their password after first login using Forgot Password.
                    </p>

                    <motion.button
                      onClick={() => { setSuccessInvite(null); setInviteForm({ email: '', full_name: '', role: 'analyst', temporary_password: generatePassword() }) }}
                      whileHover={{ scale: 1.02 }}
                      className="w-full border border-crimson/30 text-crimson hover:bg-crimson/10 font-display font-bold py-2.5 rounded-lg tracking-widest text-sm transition-all duration-300"
                    >
                      INVITE ANOTHER
                    </motion.button>
                  </motion.div>
                ) : (
                  /* Form state */
                  <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="font-display text-lg font-bold text-ink-primary tracking-wider">INVITE USER</h3>
                      <button onClick={() => setShowInvite(false)}
                        className="text-ink-muted hover:text-crimson transition-colors">
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <form onSubmit={handleInvite} className="space-y-4">
                      <div>
                        <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">Full Name</label>
                        <input type="text" value={inviteForm.full_name}
                          onChange={(e) => setInviteForm({ ...inviteForm, full_name: e.target.value })}
                          required placeholder="Sara Ahmed"
                          className="w-full bg-void/60 border border-ink-muted/30 rounded-lg px-4 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson transition-all duration-300 text-sm"
                        />
                      </div>
                      <div>
                        <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">Email Address</label>
                        <div className="relative">
                          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
                          <input type="email" value={inviteForm.email}
                            onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                            required placeholder="sara@company.com"
                            className="w-full bg-void/60 border border-ink-muted/30 rounded-lg pl-10 pr-4 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson transition-all duration-300 text-sm"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">Role</label>
                        <select value={inviteForm.role}
                          onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                          className="w-full bg-void/60 border border-ink-muted/30 rounded-lg px-4 py-3 font-body text-ink-primary focus:outline-none focus:border-crimson transition-all duration-300 text-sm">
                          <option value="analyst">Analyst — can upload and view reports</option>
                          <option value="viewer">Viewer — can only view reports</option>
                          <option value="admin">Admin — full company access</option>
                        </select>
                      </div>

                      {/* Auto-generated password preview */}
                      <div>
                        <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                          Temporary Password (auto-generated)
                        </label>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-void/60 border border-ink-muted/20 rounded-lg px-4 py-3 font-mono text-electric-light text-sm">
                            {inviteForm.temporary_password}
                          </div>
                          <motion.button type="button"
                            onClick={() => setInviteForm({ ...inviteForm, temporary_password: generatePassword() })}
                            whileHover={{ scale: 1.05 }}
                            className="px-3 py-3 border border-ink-muted/20 rounded-lg text-ink-muted hover:text-crimson hover:border-crimson/30 transition-all text-xs font-body">
                            New
                          </motion.button>
                        </div>
                        <p className="font-body text-ink-muted text-xs mt-1">
                          You will see this password after inviting so you can share it.
                        </p>
                      </div>

                      <motion.button type="submit" disabled={inviteLoading}
                        whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                        className="w-full bg-crimson hover:bg-crimson-light disabled:opacity-50 text-white font-display font-bold py-3 rounded-lg tracking-widest text-sm transition-all duration-300 shadow-crimson mt-2">
                        {inviteLoading ? (
                          <span className="flex items-center justify-center gap-2">
                            <motion.div animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                              className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                            CREATING ACCOUNT...
                          </span>
                        ) : 'SEND INVITATION'}
                      </motion.button>
                    </form>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}