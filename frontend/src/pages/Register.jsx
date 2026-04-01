import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, EyeOff, AlertCircle, Building2, User, Mail, Lock } from 'lucide-react'
import useAuthStore from '../store/authStore'
import apiClient from '../api/client'

function Particles() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full bg-crimson-light"
          initial={{
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            opacity: Math.random() * 0.3 + 0.1,
          }}
          animate={{
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
          }}
          transition={{
            duration: Math.random() * 15 + 10,
            repeat: Infinity,
            repeatType: 'reverse',
            ease: 'linear',
          }}
          style={{ width: Math.random() * 3 + 1, height: Math.random() * 3 + 1 }}
        />
      ))}
    </div>
  )
}

export default function Register() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    tenant_name: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await apiClient.post('/auth/register', {
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        tenant_name: form.tenant_name,
      })
      const { access_token } = response.data
      const profileResponse = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })
      setAuth(profileResponse.data, access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { name: 'full_name', label: 'Full Name', type: 'text', placeholder: 'John Smith', icon: User },
    { name: 'tenant_name', label: 'Organization Name', type: 'text', placeholder: 'ADCB Bank', icon: Building2 },
    { name: 'email', label: 'Email Address', type: 'email', placeholder: 'john@company.com', icon: Mail },
  ]

  return (
    <div className="min-h-screen bg-void grid-bg flex flex-col items-center justify-center relative overflow-hidden px-4 py-16">
      <Particles />
      <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-crimson opacity-5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/3 left-1/4 w-80 h-80 bg-electric opacity-5 rounded-full blur-3xl pointer-events-none" />

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="mb-8 text-center"
      >
        <Link to="/login" className="flex items-center justify-center gap-3 mb-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-crimson rounded-full flex items-center justify-center"
          >
            <div className="w-2 h-2 bg-crimson rounded-full" />
          </motion.div>
          <h1 className="font-display text-2xl font-black text-ink-primary tracking-widest">
            FIN<span className="text-crimson text-glow">SIGHT</span>
          </h1>
        </Link>
        <p className="font-body text-ink-secondary text-sm tracking-[0.3em] uppercase">
          Register Your Organization
        </p>
      </motion.div>

      {/* Register card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="relative w-full max-w-md"
      >
        <div className="glass-strong rounded-2xl p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-crimson opacity-60" />
          <div className="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 border-crimson opacity-60" />
          <div className="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 border-crimson opacity-60" />
          <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-crimson opacity-60" />

          <div className="relative z-10">
            <h2 className="font-display text-xl font-bold text-ink-primary mb-1 tracking-wider">
              CREATE ACCOUNT
            </h2>
            <p className="font-body text-ink-secondary text-sm mb-6">
              Your organization gets its own secure workspace
            </p>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="flex items-center gap-2 bg-crimson/10 border border-crimson/30 rounded-lg p-3 mb-5"
                >
                  <AlertCircle className="w-4 h-4 text-crimson flex-shrink-0" />
                  <span className="font-body text-crimson text-sm">{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="space-y-4">
              {fields.map(({ name, label, type, placeholder, icon: Icon }) => (
                <div key={name}>
                  <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                    {label}
                  </label>
                  <div className="relative">
                    <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
                    <input
                      type={type}
                      name={name}
                      value={form[name]}
                      onChange={handleChange}
                      required
                      placeholder={placeholder}
                      className="w-full bg-void/60 border border-ink-muted/30 rounded-lg pl-10 pr-4 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson focus:shadow-crimson transition-all duration-300 text-sm"
                    />
                  </div>
                </div>
              ))}

              {/* Password */}
              <div>
                <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={form.password}
                    onChange={handleChange}
                    required
                    placeholder="Min. 8 characters"
                    className="w-full bg-void/60 border border-ink-muted/30 rounded-lg pl-10 pr-12 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson focus:shadow-crimson transition-all duration-300 text-sm"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-crimson transition-colors">
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    name="confirmPassword"
                    value={form.confirmPassword}
                    onChange={handleChange}
                    required
                    placeholder="Repeat your password"
                    className="w-full bg-void/60 border border-ink-muted/30 rounded-lg pl-10 pr-12 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson focus:shadow-crimson transition-all duration-300 text-sm"
                  />
                  <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-crimson transition-colors">
                    {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full bg-crimson hover:bg-crimson-light disabled:opacity-50 disabled:cursor-not-allowed text-white font-display font-bold py-3 px-6 rounded-lg tracking-widest text-sm transition-all duration-300 shadow-crimson hover:shadow-crimson-lg mt-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
                    />
                    CREATING ACCOUNT...
                  </span>
                ) : 'REGISTER ORGANIZATION'}
              </motion.button>
            </form>

            <p className="font-body text-ink-secondary text-sm text-center mt-6">
              Already have an account?{' '}
              <Link to="/login" className="text-crimson hover:text-crimson-light transition-colors font-semibold">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </motion.div>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.8 }}
        className="mt-8 flex flex-col items-center gap-3"
      >
        <div className="glass rounded-xl px-5 py-3 flex items-center gap-4 border border-crimson/20">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-crimson to-crimson-dark flex items-center justify-center font-display text-xs font-black text-white shadow-crimson flex-shrink-0">
            MS
          </div>
          <div>
            <p className="font-display text-sm font-bold text-white tracking-wider">Mohamed Sahad M</p>
            <p className="font-body text-xs text-crimson">Passionate AI & Software Engineer</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {[
            { label: 'LINKEDIN', href: 'https://linkedin.com' },
            { label: 'GITHUB', href: 'https://github.com' },
            { label: 'PORTFOLIO', href: 'https://portfolio.com' },
          ].map(({ label, href }, i) => (
            <span key={label} className="flex items-center gap-3">
              <a href={href} target="_blank" rel="noreferrer"
                className="font-body text-xs font-semibold tracking-widest text-ink-secondary hover:text-white hover:bg-crimson/20 border border-ink-muted/20 hover:border-crimson/40 px-3 py-1 rounded-full transition-all duration-300">
                {label}
              </a>
              {i < 2 && <span className="text-ink-muted text-xs">·</span>}
            </span>
          ))}
        </div>
      </motion.footer>
    </div>
  )
}