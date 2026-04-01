import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Mail, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react'
import apiClient from '../api/client'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [resetToken, setResetToken] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await apiClient.post('/auth/forgot-password', { email })
      setSuccess(true)
      // In development the token is returned directly
      if (response.data.reset_token) {
        setResetToken(response.data.reset_token)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-void grid-bg flex flex-col items-center justify-center relative overflow-hidden px-4">
      <div className="absolute top-1/3 left-1/3 w-80 h-80 bg-crimson opacity-5 rounded-full blur-3xl pointer-events-none" />

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 text-center"
      >
        <Link to="/login" className="flex items-center justify-center gap-2 mb-2">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-crimson rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-crimson rounded-full" />
          </motion.div>
          <h1 className="font-display text-2xl font-black text-ink-primary tracking-widest">
            FIN<span className="text-crimson">SIGHT</span>
          </h1>
        </Link>
        <p className="font-body text-ink-secondary text-sm tracking-[0.3em] uppercase">
          Password Recovery
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="w-full max-w-md"
      >
        <div className="glass-strong rounded-2xl p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-crimson opacity-60" />
          <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-crimson opacity-60" />

          <AnimatePresence mode="wait">
            {!success ? (
              <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <h2 className="font-display text-xl font-bold text-ink-primary mb-1 tracking-wider">
                  RESET PASSWORD
                </h2>
                <p className="font-body text-ink-secondary text-sm mb-8">
                  Enter your email and we will send you a reset link
                </p>

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
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="your@email.com"
                        className="w-full bg-void/60 border border-ink-muted/30 rounded-lg pl-10 pr-4 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson focus:shadow-crimson transition-all duration-300 text-sm"
                      />
                    </div>
                  </div>

                  <motion.button
                    type="submit"
                    disabled={loading}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full bg-crimson hover:bg-crimson-light disabled:opacity-50 text-white font-display font-bold py-3 rounded-lg tracking-widest text-sm transition-all duration-300 shadow-crimson"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <motion.div animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                          className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                        SENDING...
                      </span>
                    ) : 'SEND RESET LINK'}
                  </motion.button>
                </form>
              </motion.div>
            ) : (
              <motion.div key="success" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                className="text-center py-4">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200 }}
                  className="w-16 h-16 rounded-full bg-risk-low/10 border border-risk-low/30 flex items-center justify-center mx-auto mb-4"
                >
                  <CheckCircle className="w-8 h-8 text-risk-low" />
                </motion.div>
                <h3 className="font-display text-lg font-bold text-ink-primary mb-2 tracking-wider">
                  LINK SENT
                </h3>
                <p className="font-body text-ink-secondary text-sm mb-4">
                  Check your email for the password reset link. It expires in 15 minutes.
                </p>
                {resetToken && (
                  <div className="bg-surface rounded-lg p-3 mb-4 text-left">
                    <p className="font-body text-ink-muted text-xs mb-1">DEV MODE — Reset Token:</p>
                    <p className="font-mono text-xs text-electric-light break-all">{resetToken}</p>
                  </div>
                )}
                <Link to="/reset-password"
                  className="font-body text-crimson hover:text-crimson-light text-sm transition-colors">
                  Enter reset token →
                </Link>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="mt-6 flex justify-center">
            <Link to="/login"
              className="flex items-center gap-2 font-body text-ink-secondary text-sm hover:text-crimson transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Back to login
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  )
}