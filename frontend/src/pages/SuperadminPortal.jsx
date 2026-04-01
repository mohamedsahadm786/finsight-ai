import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Building2, Users, TrendingUp, AlertTriangle,
  CheckCircle, X, ChevronLeft, Database,
  PauseCircle, PlayCircle, Trash2, Settings,
  BarChart2, Cpu, DollarSign
} from 'lucide-react'
import apiClient from '../api/client'

export default function SuperadminPortal() {
  const navigate = useNavigate()
  const [tenants, setTenants] = useState([])
  const [llmConfigs, setLlmConfigs] = useState([])
  const [usageData, setUsageData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('tenants')
  const [message, setMessage] = useState({ type: '', text: '' })
  const [suspendModal, setSuspendModal] = useState(null)
  const [suspendReason, setSuspendReason] = useState('')

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    try {
      const [tenantsRes, llmRes, usageRes] = await Promise.all([
        apiClient.get('/superadmin/tenants'),
        apiClient.get('/superadmin/llm-config'),
        apiClient.get('/superadmin/usage'),
      ])
      setTenants(tenantsRes.data.tenants || [])
      setLlmConfigs(llmRes.data.configs || [])
      setUsageData(usageRes.data)
    } catch (err) {
      console.error('Failed to fetch superadmin data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSuspend = async () => {
    if (!suspendReason.trim()) return
    try {
      await apiClient.patch(`/superadmin/tenants/${suspendModal.id}/suspend`, {
        reason: suspendReason
      })
      setMessage({ type: 'success', text: `${suspendModal.name} suspended` })
      setSuspendModal(null)
      setSuspendReason('')
      fetchAll()
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to suspend' })
    }
  }

  const handleRestore = async (tenant) => {
    try {
      await apiClient.patch(`/superadmin/tenants/${tenant.id}/restore`)
      setMessage({ type: 'success', text: `${tenant.name} restored` })
      fetchAll()
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to restore tenant' })
    }
  }

  const handleToggleLLM = async (config) => {
    try {
      await apiClient.patch(`/superadmin/llm-config/${config.id}`, {
        is_active: !config.is_active
      })
      setMessage({ type: 'success', text: `${config.model_name} ${!config.is_active ? 'enabled' : 'disabled'}` })
      fetchAll()
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update model config' })
    }
  }

  const statusColors = {
    active: 'text-risk-low border-risk-low/30 bg-risk-low/10',
    suspended: 'text-risk-medium border-risk-medium/30 bg-risk-medium/10',
    deleted: 'text-ink-muted border-ink-muted/20 bg-surface-raised',
  }

  const tabs = [
    { key: 'tenants', icon: Building2, label: 'TENANTS' },
    { key: 'usage', icon: BarChart2, label: 'USAGE' },
    { key: 'models', icon: Cpu, label: 'AI MODELS' },
  ]

  return (
    <div className="min-h-screen bg-void">
      {/* Top nav */}
      <div className="sticky top-0 z-40 glass-strong border-b border-crimson/10 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/login')}
            className="flex items-center gap-2 text-ink-secondary hover:text-crimson transition-colors font-body text-sm">
            <ChevronLeft className="w-4 h-4" />
            Exit
          </button>
          <div className="w-px h-4 bg-ink-muted/20" />
          <div className="flex items-center gap-2">
            <motion.div animate={{ rotate: 360 }}
              transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
              className="w-6 h-6 border border-crimson rounded-full flex items-center justify-center">
              <div className="w-1.5 h-1.5 bg-crimson rounded-full" />
            </motion.div>
            <h1 className="font-display text-sm font-black text-ink-primary tracking-widest">
              FIN<span className="text-crimson">SIGHT</span>
              <span className="text-ink-muted ml-2 font-normal text-xs">SUPERADMIN</span>
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Message */}
        <AnimatePresence>
          {message.text && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className={`flex items-center justify-between gap-2 rounded-lg p-3 mb-6 ${
                message.type === 'success'
                  ? 'bg-risk-low/10 border border-risk-low/30'
                  : 'bg-crimson/10 border border-crimson/30'
              }`}>
              <div className="flex items-center gap-2">
                {message.type === 'success'
                  ? <CheckCircle className="w-4 h-4 text-risk-low" />
                  : <AlertTriangle className="w-4 h-4 text-crimson" />
                }
                <span className={`font-body text-sm ${message.type === 'success' ? 'text-risk-low' : 'text-crimson'}`}>
                  {message.text}
                </span>
              </div>
              <button onClick={() => setMessage({ type: '', text: '' })}>
                <X className="w-4 h-4 text-ink-muted" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { icon: Building2, label: 'Total Companies', value: tenants.length, color: 'text-electric-light' },
            { icon: Users, label: 'Active Tenants', value: tenants.filter(t => t.status === 'active').length, color: 'text-risk-low' },
            { icon: DollarSign, label: 'Total Cost (All Time)', value: usageData ? `$${usageData.total_cost_all_time.toFixed(2)}` : '—', color: 'text-crimson' },
          ].map(({ icon: Icon, label, value, color }, i) => (
            <motion.div key={label}
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass rounded-xl p-4 border border-crimson/10">
              <Icon className={`w-5 h-5 ${color} mb-2`} />
              <div className={`font-display text-2xl font-black ${color} mb-1`}>{value}</div>
              <div className="font-body text-ink-muted text-xs">{label}</div>
            </motion.div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-1 bg-surface rounded-xl mb-6 w-fit">
          {tabs.map(({ key, icon: Icon, label }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-display text-xs font-bold tracking-wider transition-all duration-200 ${
                activeTab === key
                  ? 'bg-crimson/10 border border-crimson/25 text-crimson'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}>
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* TENANTS TAB */}
        {activeTab === 'tenants' && (
          <div className="glass rounded-xl border border-crimson/10 overflow-hidden">
            <div className="p-5 border-b border-crimson/10">
              <h3 className="font-display text-sm font-bold text-ink-primary tracking-wider">
                ALL COMPANIES
              </h3>
            </div>
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <motion.div animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-8 h-8 border-2 border-crimson border-t-transparent rounded-full" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-crimson/10">
                      {['Company', 'Plan', 'Users', 'Docs', 'Status', 'Actions'].map(h => (
                        <th key={h} className="text-left px-5 py-3 font-body text-ink-muted text-xs tracking-widest uppercase">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tenants.map((tenant, i) => (
                      <motion.tr key={tenant.id}
                        initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.05 }}
                        className="border-b border-crimson/5 hover:bg-surface-raised/30 transition-colors">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-crimson/10 border border-crimson/20 flex items-center justify-center font-display text-xs font-bold text-crimson">
                              {tenant.name?.charAt(0)}
                            </div>
                            <div>
                              <p className="font-body text-sm text-ink-primary">{tenant.name}</p>
                              <p className="font-body text-xs text-ink-muted">{tenant.slug}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className="font-display text-xs text-electric-light capitalize">{tenant.plan_tier}</span>
                        </td>
                        <td className="px-5 py-4">
                          <span className="font-body text-xs text-ink-secondary">{tenant.user_count}</span>
                        </td>
                        <td className="px-5 py-4">
                          <span className="font-body text-xs text-ink-secondary">{tenant.document_count}</span>
                        </td>
                        <td className="px-5 py-4">
                          <span className={`font-display text-xs font-bold px-2 py-0.5 rounded border ${statusColors[tenant.status]}`}>
                            {tenant.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            {tenant.status === 'active' && (
                              <motion.button whileHover={{ scale: 1.1 }}
                                onClick={() => setSuspendModal(tenant)}
                                className="text-ink-muted hover:text-risk-medium transition-colors" title="Suspend">
                                <PauseCircle className="w-4 h-4" />
                              </motion.button>
                            )}
                            {tenant.status === 'suspended' && (
                              <motion.button whileHover={{ scale: 1.1 }}
                                onClick={() => handleRestore(tenant)}
                                className="text-ink-muted hover:text-risk-low transition-colors" title="Restore">
                                <PlayCircle className="w-4 h-4" />
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
        )}

        {/* USAGE TAB */}
        {activeTab === 'usage' && (
          <div className="glass rounded-xl border border-crimson/10 p-6">
            <h3 className="font-display text-sm font-bold text-ink-primary tracking-wider mb-4">
              TOKEN USAGE OVERVIEW
            </h3>
            {usageData?.summaries?.length === 0 ? (
              <p className="font-body text-ink-secondary text-sm text-center py-8">
                No usage data yet. Usage is tracked after documents are processed.
              </p>
            ) : (
              <div className="space-y-4">
                {usageData?.summaries?.map((summary, i) => (
                  <motion.div key={i}
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="border border-crimson/10 rounded-xl p-4 hover:border-crimson/20 transition-colors">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="font-display text-sm font-bold text-ink-primary">{summary.year_month}</p>
                        <p className="font-body text-xs text-ink-muted">{summary.documents_processed} documents processed</p>
                      </div>
                      <div className="text-right">
                        <p className="font-display text-lg font-black text-crimson">${summary.total_cost_usd.toFixed(4)}</p>
                        <p className="font-body text-xs text-ink-muted">{summary.total_tokens.toLocaleString()} tokens</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { label: 'LLaMA', value: summary.llama_tokens },
                        { label: 'FinBERT', value: summary.finbert_tokens },
                        { label: 'GPT-4', value: summary.gpt4_tokens },
                        { label: 'GPT-3.5', value: summary.gpt35_tokens },
                      ].map(({ label, value }) => (
                        <div key={label} className="bg-surface-raised rounded-lg p-2 text-center">
                          <p className="font-display text-xs font-bold text-ink-primary">{value?.toLocaleString() || 0}</p>
                          <p className="font-body text-xs text-ink-muted">{label}</p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* MODELS TAB */}
        {activeTab === 'models' && (
          <div className="glass rounded-xl border border-crimson/10 overflow-hidden">
            <div className="p-5 border-b border-crimson/10">
              <h3 className="font-display text-sm font-bold text-ink-primary tracking-wider">
                LLM MODEL CONFIGURATIONS
              </h3>
              <p className="font-body text-ink-muted text-xs mt-1">
                Toggle models on/off. Changes take effect within 5 minutes.
              </p>
            </div>
            <div className="p-4 space-y-3">
              {llmConfigs.map((config, i) => (
                <motion.div key={config.id}
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`flex items-center justify-between p-4 rounded-xl border transition-all duration-300 ${
                    config.is_active
                      ? 'border-risk-low/20 bg-risk-low/3'
                      : 'border-ink-muted/10 opacity-60'
                  }`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${config.is_active ? 'bg-risk-low animate-pulse' : 'bg-ink-muted'}`} />
                    <div>
                      <p className="font-display text-sm font-bold text-ink-primary tracking-wider">
                        {config.model_name.toUpperCase()}
                      </p>
                      <p className="font-body text-xs text-ink-muted">
                        {config.model_path || 'OpenAI API'} · max {config.max_tokens} tokens
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-display text-xs text-crimson font-bold">
                        ${config.cost_per_1k_input_tokens}/1K in
                      </p>
                      <p className="font-body text-xs text-ink-muted">
                        ${config.cost_per_1k_output_tokens}/1K out
                      </p>
                    </div>
                    <motion.button
                      onClick={() => handleToggleLLM(config)}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className={`px-3 py-1.5 rounded-lg font-display text-xs font-bold tracking-wider border transition-all duration-300 ${
                        config.is_active
                          ? 'border-crimson/30 text-crimson hover:bg-crimson/10'
                          : 'border-risk-low/30 text-risk-low hover:bg-risk-low/10'
                      }`}
                    >
                      {config.is_active ? 'DISABLE' : 'ENABLE'}
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Suspend modal */}
      <AnimatePresence>
        {suspendModal && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-void/80 backdrop-blur-sm flex items-center justify-center z-50 px-4"
            onClick={(e) => e.target === e.currentTarget && setSuspendModal(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-strong rounded-2xl p-8 w-full max-w-md"
            >
              <div className="flex items-center gap-3 mb-6">
                <AlertTriangle className="w-6 h-6 text-risk-medium" />
                <h3 className="font-display text-lg font-bold text-ink-primary tracking-wider">
                  SUSPEND TENANT
                </h3>
              </div>
              <p className="font-body text-ink-secondary text-sm mb-6">
                You are about to suspend <span className="text-ink-primary font-semibold">{suspendModal.name}</span>.
                All users will lose access until restored.
              </p>
              <div className="mb-6">
                <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-2 block">
                  Reason (required)
                </label>
                <textarea
                  value={suspendReason}
                  onChange={(e) => setSuspendReason(e.target.value)}
                  rows={3}
                  placeholder="Enter reason for suspension..."
                  className="w-full bg-void/60 border border-ink-muted/30 rounded-lg px-4 py-3 font-body text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson transition-all duration-300 text-sm resize-none"
                />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setSuspendModal(null)}
                  className="flex-1 border border-ink-muted/20 text-ink-secondary hover:text-ink-primary font-display text-sm font-bold py-2.5 rounded-lg tracking-wider transition-all">
                  CANCEL
                </button>
                <motion.button onClick={handleSuspend}
                  disabled={!suspendReason.trim()}
                  whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  className="flex-1 bg-risk-medium/80 hover:bg-risk-medium disabled:opacity-40 text-void font-display text-sm font-bold py-2.5 rounded-lg tracking-wider transition-all">
                  SUSPEND
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}