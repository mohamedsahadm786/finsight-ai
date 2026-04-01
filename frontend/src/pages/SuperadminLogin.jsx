import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, EyeOff, AlertCircle, Shield } from 'lucide-react'
import useAuthStore from '../store/authStore'
import apiClient from '../api/client'

export default function SuperadminLogin() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await apiClient.post('/auth/superadmin/login', form)
      const { access_token } = response.data
      const superadminUser = {
        id: 'superadmin',
        full_name: 'Super Admin',
        email: form.email,
        role: 'superadmin',
        tenant_id: null,
      }
      setAuth(superadminUser, access_token)
      navigate('/superadmin')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid superadmin credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-void grid-bg flex flex-col items-center justify-center relative overflow-hidden px-4">
      <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-risk-distress opacity-5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/3 right-1/3 w-96 h-96 bg-crimson opacity-5 rounded-full blur-3xl pointer-events-none" />
      <motion.div
        className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-risk-distress to-transparent opacity-20 pointer-events-none"
        animate={{ y: ['0vh', '100vh'] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
      />

      {/* Logo */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-10 h-10 border-2 border-risk-distress rounded-full flex items-center justify-center">
            <Shield className="w-4 h-4 text-risk-distress" />
          </motion.div>
          <h1 className="font-display text-3xl font-black text-ink-primary tracking-widest">
            FIN<span className="text-crimson">SIGHT</span>
          </h1>
        </div>
        <p className="font-body text-ink-secondary text-sm tracking-[0.3em] uppercase">Superadmin Portal</p>
      </motion.div>

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="w-full max-w-md"
      >
        <div className="glass-strong rounded-2xl p-8 relative overflow-hidden border border-risk-distress/20">
          <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-risk-distress opacity-60" />
          <div className="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 border-risk-distress opacity-60" />
          <div className="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 border-risk-distress opacity-60" />
          <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-risk-distress opacity-60" />

          <div className="relative z-10">
            <div className="flex items-center gap-2 bg-risk-distress/10 border border-risk-distress/30 rounded-lg px-3 py-2 mb-6">
              <Shield className="w-4 h-4 text-risk-distress flex-shrink-0" />
              <span className="font-body text-risk-distress text-xs tracking-wider">
                RESTRICTED — PLATFORM ADMINISTRATORS ONLY
              </span>
            </div>

            <h2 className="font-display text-xl font-bold text-ink-primary mb-1 tracking-wider">SUPERADMIN ACCESS</h2>
            <p className="font-body text-ink-secondary text-sm mb-8">Full platform visibility and control</p>

            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="flex items-center gap-2 bg-crimson/10 border border-crimson/30 rounded-lg p-3 mb-6">
                  <AlertCircle className="w-4 h-4 text-crimson flex-shrink-0" />
                  <span className="font-body text-crimson text-sm">{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                  Superadmin Email
                </label>
                <input type="email" value={form.email}
                  onChange={(e) => { setForm({ ...form, email: e.target.value }); setError('') }}
                  required placeholder="superadmin@finsight.ai"
                  className="w-full bg-void/60 border border-ink-muted/30 rounded-lg px-4 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-risk-distress transition-all duration-300 text-sm"
                />
              </div>

              <div>
                <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                  Password
                </label>
                <div className="relative">
                  <input type={showPassword ? 'text' : 'password'} value={form.password}
                    onChange={(e) => { setForm({ ...form, password: e.target.value }); setError('') }}
                    required placeholder="••••••••"
                    className="w-full bg-void/60 border border-ink-muted/30 rounded-lg px-4 py-3 pr-12 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-risk-distress transition-all duration-300 text-sm"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-risk-distress transition-colors">
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <motion.button type="submit" disabled={loading}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                className="w-full disabled:opacity-50 disabled:cursor-not-allowed text-white font-display font-bold py-3 px-6 rounded-lg tracking-widest text-sm transition-all duration-300"
                style={{
                  background: loading ? '#4a0072' : 'linear-gradient(135deg, #6a0080, #D500F9)',
                  boxShadow: '0 0 20px rgba(213, 0, 249, 0.3)',
                }}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <motion.div animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    AUTHENTICATING...
                  </span>
                ) : 'ACCESS SUPERADMIN PORTAL'}
              </motion.button>
            </form>

            <div className="mt-6 text-center">
              <Link to="/login" className="font-body text-ink-muted text-xs hover:text-ink-secondary transition-colors">
                ← Back to regular login
              </Link>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Footer */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}
        className="mt-8 flex flex-col items-center gap-3">
        <div className="glass rounded-xl px-5 py-3 flex items-center gap-4 border border-risk-distress/20">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-crimson to-crimson-dark flex items-center justify-center font-display text-xs font-black text-white">
            MS
          </div>
          <div>
            <p className="font-display text-sm font-bold text-white tracking-wider">Mohamed Sahad M</p>
            <p className="font-body text-xs text-risk-distress">Passionate AI & Software Engineer</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}