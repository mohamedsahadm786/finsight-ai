import { motion } from 'framer-motion'
import { CheckCircle, Loader } from 'lucide-react'
import { AGENTS } from '../../utils/constants'

export default function ProgressPipeline({ currentAgent, status }) {
  const getStatus = (agentKey) => {
    if (status === 'completed') return 'done'
    const currentIdx = AGENTS.findIndex(a => a.key === currentAgent)
    const agentIdx = AGENTS.findIndex(a => a.key === agentKey)
    if (agentIdx < currentIdx) return 'done'
    if (agentIdx === currentIdx) return 'running'
    return 'waiting'
  }

  return (
    <div className="space-y-2">
      {AGENTS.map(({ key, label }, i) => {
        const s = getStatus(key)
        return (
          <motion.div key={key}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-400 ${
              s === 'running' ? 'bg-crimson/5 border border-crimson/20' :
              s === 'done'    ? 'bg-risk-low/5 border border-risk-low/10' :
              'opacity-35 border border-transparent'
            }`}
          >
            <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
              {s === 'done' ? (
                <CheckCircle className="w-4 h-4 text-risk-low" />
              ) : s === 'running' ? (
                <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                  <Loader className="w-4 h-4 text-crimson" />
                </motion.div>
              ) : (
                <span className="font-mono text-xs text-ink-muted">{String(i + 1).padStart(2, '0')}</span>
              )}
            </div>
            <span className={`font-display text-xs font-bold tracking-wider ${
              s === 'running' ? 'text-crimson' : s === 'done' ? 'text-risk-low' : 'text-ink-muted'
            }`}>
              {label}
            </span>
          </motion.div>
        )
      })}
    </div>
  )
}