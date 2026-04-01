import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, EyeOff, Zap, Shield, TrendingUp, AlertCircle } from 'lucide-react'
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
      <motion.div
        className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-crimson to-transparent opacity-20"
        animate={{ y: ['0vh', '100vh'] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  )
}

function CornerDecor() {
  return (
    <>
      <div className="absolute top-0 left-0 w-16 h-16 border-t-2 border-l-2 border-crimson opacity-60" />
      <div className="absolute top-0 right-0 w-16 h-16 border-t-2 border-r-2 border-crimson opacity-60" />
      <div className="absolute bottom-0 left-0 w-16 h-16 border-b-2 border-l-2 border-crimson opacity-60" />
      <div className="absolute bottom-0 right-0 w-16 h-16 border-b-2 border-r-2 border-crimson opacity-60" />
    </>
  )
}

export default function Login() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await apiClient.post('/auth/login', form)
      const { access_token } = response.data
      const profileResponse = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })
      setAuth(profileResponse.data, access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  const socialLinks = [
    { label: 'LINKEDIN', href: 'https://www.linkedin.com/in/mohamed-sahad-m/' },
    { label: 'GITHUB', href: 'https://github.com/mohamedsahadm786' },
    { label: 'PORTFOLIO', href: 'https://d5qb6gsuemmzn.cloudfront.net/' },
  ]

  return (
    <div className="min-h-screen bg-void grid-bg flex flex-col items-center justify-center relative overflow-hidden px-4 py-20">
      <Particles />

      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-crimson opacity-5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-electric opacity-5 rounded-full blur-3xl pointer-events-none" />

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="mb-8 text-center"
      >
        <div className="flex items-center justify-center gap-3 mb-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-10 h-10 border-2 border-crimson rounded-full flex items-center justify-center"
          >
            <div className="w-3 h-3 bg-crimson rounded-full" />
          </motion.div>
          <h1 className="font-display text-3xl font-black text-ink-primary tracking-widest">
            FIN<span className="text-crimson text-glow">SIGHT</span>
          </h1>
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-10 h-10 border-2 border-electric rounded-full flex items-center justify-center"
          >
            <div className="w-3 h-3 bg-electric rounded-full" />
          </motion.div>
        </div>
        <p className="font-body text-ink-secondary text-sm tracking-[0.3em] uppercase">
          Financial Intelligence Platform
        </p>
      </motion.div>

      {/* Login card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="relative w-full max-w-md"
      >
        <div className="glass-strong rounded-2xl p-8 relative overflow-hidden">
          <CornerDecor />
          <div className="absolute inset-0 shadow-inner-glow rounded-2xl pointer-events-none" />

          <div className="relative z-10">
            <h2 className="font-display text-xl font-bold text-ink-primary mb-1 tracking-wider">
              SYSTEM ACCESS
            </h2>
            <p className="font-body text-ink-secondary text-sm mb-8">
              Enter your credentials to access the platform
            </p>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="flex items-center gap-2 bg-crimson/10 border border-crimson/30 rounded-lg p-3 mb-6"
                >
                  <AlertCircle className="w-4 h-4 text-crimson flex-shrink-0" />
                  <span className="font-body text-crimson text-sm">{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                  Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                  placeholder="analyst@company.com"
                  className="w-full bg-void/60 border border-ink-muted/30 rounded-lg px-4 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson focus:shadow-crimson transition-all duration-300 text-sm"
                />
              </div>

              <div>
                <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={form.password}
                    onChange={handleChange}
                    required
                    placeholder="••••••••"
                    className="w-full bg-void/60 border border-ink-muted/30 rounded-lg px-4 py-3 pr-12 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson focus:shadow-crimson transition-all duration-300 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-crimson transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <Link
                  to="/forgot-password"
                  className="font-body text-ink-secondary text-xs hover:text-crimson transition-colors"
                >
                  Forgot password?
                </Link>
              </div>

              <motion.button
                type="submit"
                disabled={loading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full bg-crimson hover:bg-crimson-light disabled:opacity-50 disabled:cursor-not-allowed text-white font-display font-bold py-3 px-6 rounded-lg tracking-widest text-sm transition-all duration-300 shadow-crimson hover:shadow-crimson-lg"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
                    />
                    AUTHENTICATING...
                  </span>
                ) : (
                  'INITIATE ACCESS'
                )}
              </motion.button>
            </form>

            <p className="font-body text-ink-secondary text-sm text-center mt-6">
              No account?{' '}
              <Link
                to="/register"
                className="text-crimson hover:text-crimson-light transition-colors font-semibold"
              >
                Register your organization
              </Link>
            </p>
            <div className="mt-3 text-center">
              <Link
                to="/superadmin-login"
                className="font-body text-ink-muted text-xs hover:text-ink-secondary transition-colors tracking-wider"
              >
                Platform administrator? →
              </Link>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats strip */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.5 }}
        className="flex items-center gap-10 mt-10"
      >
        {[
          { icon: Zap, label: 'PROCESSING', value: '< 5 MIN' },
          { icon: Shield, label: 'ACCURACY', value: '95.4%' },
          { icon: TrendingUp, label: 'REPORTS', value: '10K+' },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="text-center">
            <Icon className="w-4 h-4 text-crimson mx-auto mb-1" />
            <div className="font-display text-xs text-ink-primary font-bold">{value}</div>
            <div className="font-body text-ink-muted text-xs tracking-widest">{label}</div>
          </div>
        ))}
      </motion.div>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.8 }}
        className="mt-10 flex flex-col items-center gap-4"
      >
        <div className="flex items-center gap-3 w-64">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent to-crimson/30" />
          <span className="font-body text-ink-muted text-xs tracking-widest">BUILT BY</span>
          <div className="flex-1 h-px bg-gradient-to-l from-transparent to-crimson/30" />
        </div>

        <div className="glass rounded-xl px-5 py-3 flex items-center gap-4 border border-crimson/20">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-crimson to-crimson-dark flex items-center justify-center font-display text-sm font-black text-white shadow-crimson flex-shrink-0">
            MS
          </div>
          <div>
            <p className="font-display text-sm font-bold text-white tracking-wider">
              Mohamed Sahad M
            </p>
            <p className="font-body text-xs text-crimson">
              Passionate AI &amp; Software Engineer
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {socialLinks.map(({ label, href }, i) => (
            <span key={label} className="flex items-center gap-3">
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="font-body text-xs font-semibold tracking-widest text-ink-secondary hover:text-white hover:bg-crimson/20 border border-ink-muted/20 hover:border-crimson/40 px-3 py-1 rounded-full transition-all duration-300"
              >
                {label}
              </a>
              {i < 2 && (
                <span className="text-ink-muted text-xs">&middot;</span>
              )}
            </span>
          ))}
        </div>
      </motion.footer>
    </div>
  )
}