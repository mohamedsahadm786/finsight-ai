import { useState, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckCircle, Loader, AlertTriangle,
  FileText, Brain, BarChart2, Shield, TrendingUp, FileEdit
} from 'lucide-react'
import apiClient from '../api/client'

const AGENTS = [
  { key: 'Document Parser', icon: FileText, label: 'DOCUMENT PARSER', desc: 'Extracting text and indexing chunks into vector database' },
  { key: 'Ratio Extractor', icon: Brain, label: 'RATIO EXTRACTOR', desc: 'LLaMA 3.1 extracting financial ratios from document' },
  { key: 'Sentiment Analyst', icon: BarChart2, label: 'SENTIMENT ANALYST', desc: 'FinBERT analyzing financial tone across all sections' },
  { key: 'Breach Detector', icon: Shield, label: 'BREACH DETECTOR', desc: 'Scanning for covenant violations and risk flags' },
  { key: 'Risk Scorer', icon: TrendingUp, label: 'RISK SCORER', desc: 'XGBoost computing credit risk score with SHAP explainability' },
  { key: 'Report Writer', icon: FileEdit, label: 'REPORT WRITER', desc: 'GPT-4 composing the final credit risk advisory report' },
]

export default function Processing() {
  const navigate = useNavigate()
  const { jobId } = useParams()
  const [searchParams] = useSearchParams()
  const documentId = searchParams.get('document_id')

  const [status, setStatus] = useState('queued')
  const [currentAgent, setCurrentAgent] = useState('')
  const [error, setError] = useState('')
  const [startTime] = useState(Date.now())
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [startTime])

  useEffect(() => {
    if (!jobId) return
    const poll = setInterval(async () => {
      try {
        const response = await apiClient.get(`/jobs/${jobId}/status`)
        const data = response.data
        setStatus(data.status)
        setCurrentAgent(data.current_agent || '')

        if (data.status === 'completed') {
          clearInterval(poll)
          setTimeout(() => navigate(`/report/${documentId}`), 1500)
        }
        if (data.status === 'failed' || data.status === 'dead_letter') {
          clearInterval(poll)
          setError(data.error_message || 'Processing failed. Please try again.')
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 3000)
    return () => clearInterval(poll)
  }, [jobId, documentId, navigate])

  const getAgentStatus = (agentKey) => {
    const currentIndex = AGENTS.findIndex(a => a.key === currentAgent)
    const agentIndex = AGENTS.findIndex(a => a.key === agentKey)
    if (status === 'completed') return 'done'
    if (agentIndex < currentIndex) return 'done'
    if (agentIndex === currentIndex) return 'running'
    return 'waiting'
  }

  const formatElapsed = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

  return (
    <div className="min-h-screen bg-void grid-bg flex flex-col items-center justify-center px-4 py-16">
      <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-crimson opacity-5 rounded-full blur-3xl pointer-events-none" />

      {/* Logo */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-1">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-crimson rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-crimson rounded-full" />
          </motion.div>
          <h1 className="font-display text-2xl font-black text-ink-primary tracking-widest">
            FIN<span className="text-crimson">SIGHT</span>
          </h1>
        </div>
        <p className="font-body text-ink-secondary text-xs tracking-[0.3em] uppercase">AI Analysis Pipeline</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-lg"
      >
        <div className="glass-strong rounded-2xl p-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-crimson opacity-60" />
          <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-crimson opacity-60" />

          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="font-display text-lg font-bold text-ink-primary tracking-wider">
                {status === 'completed' ? 'ANALYSIS COMPLETE' : status === 'failed' ? 'ANALYSIS FAILED' : 'PROCESSING...'}
              </h2>
              <p className="font-body text-ink-secondary text-xs mt-0.5">
                {status === 'completed' ? 'Redirecting to report...' : `Elapsed: ${formatElapsed(elapsed)}`}
              </p>
            </div>
            {status !== 'completed' && status !== 'failed' && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className="w-10 h-10 border-2 border-crimson border-t-transparent rounded-full"
              />
            )}
            {status === 'completed' && (
              <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 200 }}>
                <CheckCircle className="w-10 h-10 text-risk-low" />
              </motion.div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 bg-crimson/10 border border-crimson/30 rounded-lg p-3 mb-6">
              <AlertTriangle className="w-4 h-4 text-crimson flex-shrink-0" />
              <span className="font-body text-crimson text-sm">{error}</span>
            </div>
          )}

          {/* Agent pipeline */}
          <div className="space-y-3">
            {AGENTS.map(({ key, icon: Icon, label, desc }, i) => {
              const agentStatus = getAgentStatus(key)
              return (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={`flex items-center gap-4 p-3 rounded-xl transition-all duration-500 ${
                    agentStatus === 'running'
                      ? 'bg-crimson/5 border border-crimson/25'
                      : agentStatus === 'done'
                      ? 'bg-risk-low/5 border border-risk-low/15'
                      : 'border border-transparent opacity-40'
                  }`}
                >
                  {/* Status icon */}
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    agentStatus === 'running' ? 'bg-crimson/10' :
                    agentStatus === 'done' ? 'bg-risk-low/10' : 'bg-surface-raised'
                  }`}>
                    {agentStatus === 'done' ? (
                      <CheckCircle className="w-4 h-4 text-risk-low" />
                    ) : agentStatus === 'running' ? (
                      <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                        <Loader className="w-4 h-4 text-crimson" />
                      </motion.div>
                    ) : (
                      <Icon className="w-4 h-4 text-ink-muted" />
                    )}
                  </div>

                  {/* Label */}
                  <div className="flex-1 min-w-0">
                    <p className={`font-display text-xs font-bold tracking-wider ${
                      agentStatus === 'running' ? 'text-crimson' :
                      agentStatus === 'done' ? 'text-risk-low' : 'text-ink-muted'
                    }`}>
                      {label}
                    </p>
                    {agentStatus === 'running' && (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="font-body text-ink-secondary text-xs mt-0.5 truncate"
                      >
                        {desc}
                      </motion.p>
                    )}
                  </div>

                  {/* Step number */}
                  <span className="font-mono text-xs text-ink-muted flex-shrink-0">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                </motion.div>
              )
            })}
          </div>

          {/* Progress bar */}
          {status !== 'failed' && (
            <div className="mt-6">
              <div className="w-full bg-surface-raised rounded-full h-1 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-crimson to-electric-light rounded-full"
                  animate={{
                    width: status === 'completed' ? '100%' :
                      `${(AGENTS.findIndex(a => a.key === currentAgent) + 1) / AGENTS.length * 100}%`
                  }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}