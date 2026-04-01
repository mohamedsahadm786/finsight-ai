import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronLeft, FileText, TrendingUp, Shield, BarChart2,
  AlertTriangle, CheckCircle, Brain, ChevronDown, ChevronUp
} from 'lucide-react'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, Cell, RadialBarChart, RadialBar
} from 'recharts'
import useAuthStore from '../store/authStore'
import apiClient from '../api/client'
import ChatWidget from '../components/chat/ChatWidget'

// ── Risk Gauge ────────────────────────────────────────────────────
function RiskGauge({ score, tier }) {
  const tierConfig = {
    low:      { color: '#00E676', label: 'LOW RISK' },
    medium:   { color: '#FFD740', label: 'MEDIUM RISK' },
    high:     { color: '#FF6D00', label: 'HIGH RISK' },
    distress: { color: '#D500F9', label: 'DISTRESS' },
  }
  const config = tierConfig[tier] || tierConfig.medium
  const percentage = Math.round((score || 0) * 100)
  const data = [{ value: percentage, fill: config.color }]

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-28">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%" cy="100%"
            innerRadius="60%" outerRadius="100%"
            startAngle={180} endAngle={0}
            data={data}
          >
            <RadialBar dataKey="value" cornerRadius={4} background={{ fill: '#1a1a2e' }} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center pointer-events-none">
          <div className="font-display text-3xl font-black" style={{ color: config.color }}>
            {percentage}
          </div>
          <div className="font-body text-xs text-ink-muted">/ 100</div>
        </div>
      </div>
      <div
        className="mt-2 font-display text-sm font-bold tracking-widest px-4 py-1 rounded-full border"
        style={{ color: config.color, borderColor: config.color + '40', backgroundColor: config.color + '15' }}
      >
        {config.label}
      </div>
    </div>
  )
}

// ── Ratio Card ────────────────────────────────────────────────────
function RatioCard({ label, value, imputed }) {
  const displayValue = value !== null && value !== undefined
    ? parseFloat(value).toFixed(2)
    : 'N/A'
  return (
    <div className="glass rounded-xl p-4 border border-crimson/10 hover:border-crimson/25 transition-all duration-300">
      <div className="flex items-center justify-between mb-2">
        <span className="font-body text-ink-muted text-xs tracking-widest uppercase">{label}</span>
        {imputed && (
          <span className="font-body text-xs text-risk-medium border border-risk-medium/30 px-1.5 py-0.5 rounded">
            EST
          </span>
        )}
      </div>
      <div className={`font-display text-2xl font-black ${value !== null && value !== undefined ? 'text-ink-primary' : 'text-ink-muted'}`}>
        {displayValue}
      </div>
    </div>
  )
}

// ── SHAP Chart ────────────────────────────────────────────────────
function ShapChart({ shapValues }) {
  if (!shapValues) return null
  const data = Object.entries(shapValues).map(([key, value]) => ({
    name: key.replace(/_/g, ' ').toUpperCase(),
    value: parseFloat(parseFloat(value).toFixed(3)),
    absValue: Math.abs(parseFloat(value)),
    positive: parseFloat(value) >= 0,
  })).sort((a, b) => b.absValue - a.absValue)

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ left: 80, right: 20, top: 5, bottom: 5 }}>
        <XAxis type="number" tick={{ fill: '#9090A8', fontSize: 10 }} />
        <YAxis type="category" dataKey="name" tick={{ fill: '#9090A8', fontSize: 10 }} width={75} />
        <Tooltip
          contentStyle={{ background: '#0D0D14', border: '1px solid rgba(198,40,40,0.2)', borderRadius: 8 }}
          labelStyle={{ color: '#F0F0F5', fontFamily: 'Rajdhani' }}
          itemStyle={{ color: '#C62828' }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.positive ? '#C62828' : '#1565C0'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Sentiment Chart ───────────────────────────────────────────────
function SentimentChart({ sentiment }) {
  if (!sentiment) return null
  const data = [
    { name: 'POSITIVE', value: sentiment.positive_count || 0, color: '#00E676' },
    { name: 'NEUTRAL',  value: sentiment.neutral_count  || 0, color: '#9090A8' },
    { name: 'NEGATIVE', value: sentiment.negative_count || 0, color: '#C62828' },
  ]
  return (
    <ResponsiveContainer width="100%" height={120}>
      <BarChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
        <XAxis dataKey="name" tick={{ fill: '#9090A8', fontSize: 9 }} />
        <YAxis tick={{ fill: '#9090A8', fontSize: 9 }} />
        <Tooltip
          contentStyle={{ background: '#0D0D14', border: '1px solid rgba(198,40,40,0.2)', borderRadius: 8 }}
          labelStyle={{ color: '#F0F0F5' }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => <Cell key={i} fill={entry.color} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Main Report Page ──────────────────────────────────────────────
export default function Report() {
  const navigate = useNavigate()
  const { documentId } = useParams()
  const { user } = useAuthStore()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expandedSection, setExpandedSection] = useState('ratios')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchReport()
  }, [documentId])

  const fetchReport = async () => {
    try {
      const response = await apiClient.get(`/reports/${documentId}`)
      setReport(response.data)
    } catch (err) {
      setError('Report not found or still processing.')
    } finally {
      setLoading(false)
    }
  }

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-2 border-crimson border-t-transparent rounded-full"
        />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-void flex flex-col items-center justify-center gap-4">
        <AlertTriangle className="w-12 h-12 text-crimson" />
        <p className="font-display text-ink-primary tracking-wider">{error}</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="font-body text-crimson hover:text-crimson-light transition-colors text-sm"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  const ratios    = report?.ratios
  const sentiment = report?.sentiment
  const breach    = report?.breaches
  const risk      = report?.risk_score
  const imputed   = risk?.imputed_features || {}

  const ratioItems = [
    { label: 'DSCR',              key: 'dscr' },
    { label: 'LEVERAGE RATIO',    key: 'leverage_ratio' },
    { label: 'INTEREST COVERAGE', key: 'interest_coverage' },
    { label: 'CURRENT RATIO',     key: 'current_ratio' },
    { label: 'NET PROFIT MARGIN', key: 'net_profit_margin' },
  ]

  const sections = [
    { key: 'ratios',    icon: TrendingUp, label: 'FINANCIAL RATIOS' },
    { key: 'sentiment', icon: BarChart2,  label: 'SENTIMENT ANALYSIS' },
    { key: 'breach',    icon: Shield,     label: 'COVENANT BREACH DETECTION' },
    { key: 'shap',      icon: Brain,      label: 'RISK EXPLAINABILITY (SHAP)' },
    { key: 'summary',   icon: FileText,   label: 'GPT-4 ADVISORY SUMMARY' },
  ]

  return (
    <div className="min-h-screen bg-void">

      {/* ── Top nav ─────────────────────────────────────────────── */}
      <div className="sticky top-0 z-40 glass-strong border-b border-crimson/10 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-ink-secondary hover:text-crimson transition-colors font-body text-sm"
          >
            <ChevronLeft className="w-4 h-4" />
            Dashboard
          </button>
          <div className="w-px h-4 bg-ink-muted/20" />
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
              className="w-6 h-6 border border-crimson rounded-full flex items-center justify-center"
            >
              <div className="w-1.5 h-1.5 bg-crimson rounded-full" />
            </motion.div>
            <h1 className="font-display text-sm font-black text-ink-primary tracking-widest">
              FIN<span className="text-crimson">SIGHT</span>
            </h1>
          </div>
        </div>
        <span className="font-body text-ink-muted text-xs truncate max-w-xs">
          {report?.document?.original_filename}
        </span>
      </div>

      {/* ── Page content ────────────────────────────────────────── */}
      <div className="max-w-4xl mx-auto px-6 py-8">

        {/* Risk score hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-8 border border-crimson/15 mb-6 text-center relative overflow-hidden"
        >
          <div className="absolute inset-0 shadow-inner-glow rounded-2xl pointer-events-none" />
          <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-crimson opacity-40" />
          <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-crimson opacity-40" />

          <h2 className="font-display text-xs font-bold text-ink-muted tracking-widest uppercase mb-6">
            Credit Risk Assessment
          </h2>
          <div className="flex justify-center mb-4">
            <RiskGauge score={risk?.risk_score || 0} tier={risk?.risk_tier || 'medium'} />
          </div>
          <p className="font-body text-ink-secondary text-sm max-w-md mx-auto">
            Score reliability:{' '}
            <span className="text-ink-primary font-semibold capitalize">
              {risk?.score_reliability || 'N/A'}
            </span>
            {' · '}
            Ratios used:{' '}
            <span className="text-ink-primary font-semibold">
              {risk?.ratios_used_count || 0}/5
            </span>
          </p>
        </motion.div>

        {/* Collapsible sections */}
        <div className="space-y-3">
          {sections.map(({ key, icon: Icon, label }, idx) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="glass rounded-xl border border-crimson/10 overflow-hidden"
            >
              {/* Section header */}
              <button
                onClick={() => toggleSection(key)}
                className="w-full flex items-center justify-between p-5 hover:bg-surface-raised/30 transition-colors duration-200"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-crimson/10 border border-crimson/20 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-crimson" />
                  </div>
                  <span className="font-display text-sm font-bold text-ink-primary tracking-wider">
                    {label}
                  </span>
                </div>
                {expandedSection === key
                  ? <ChevronUp className="w-4 h-4 text-ink-muted" />
                  : <ChevronDown className="w-4 h-4 text-ink-muted" />
                }
              </button>

              {/* Section content */}
              <AnimatePresence>
                {expandedSection === key && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 pb-5 border-t border-crimson/5">

                      {/* RATIOS */}
                      {key === 'ratios' && (
                        <div className="grid grid-cols-2 gap-3 mt-4 sm:grid-cols-3">
                          {ratioItems.map(({ label: rLabel, key: rKey }) => (
                            <RatioCard
                              key={rKey}
                              label={rLabel}
                              value={ratios?.[rKey]}
                              imputed={imputed[rKey]}
                            />
                          ))}
                        </div>
                      )}

                      {/* SENTIMENT */}
                      {key === 'sentiment' && (
                        <div className="mt-4">
                          <div className="flex items-center gap-3 mb-4">
                            <span className={`font-display text-sm font-bold px-3 py-1 rounded-full border tracking-wider ${
                              sentiment?.overall_sentiment === 'positive'
                                ? 'text-risk-low border-risk-low/30 bg-risk-low/10'
                                : sentiment?.overall_sentiment === 'negative'
                                ? 'text-crimson border-crimson/30 bg-crimson/10'
                                : 'text-ink-secondary border-ink-muted/30 bg-surface-raised'
                            }`}>
                              {(sentiment?.overall_sentiment || 'N/A').toUpperCase()}
                            </span>
                            <span className="font-body text-ink-secondary text-xs">
                              Confidence:{' '}
                              {sentiment?.confidence_score
                                ? `${(sentiment.confidence_score * 100).toFixed(1)}%`
                                : 'N/A'}
                            </span>
                          </div>
                          <SentimentChart sentiment={sentiment} />
                          {sentiment?.flagged_sentences?.length > 0 && (
                            <div className="mt-4 space-y-2">
                              <p className="font-body text-ink-muted text-xs tracking-widest uppercase mb-2">
                                Most Negative Sentences
                              </p>
                              {sentiment.flagged_sentences.slice(0, 3).map((s, i) => (
                                <div key={i} className="bg-crimson/5 border border-crimson/15 rounded-lg p-3">
                                  <p className="font-body text-ink-secondary text-xs leading-relaxed">
                                    {typeof s === 'string' ? s : s.text}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* BREACH */}
                      {key === 'breach' && (
                        <div className="mt-4">
                          {breach?.breach_detected ? (
                            <div>
                              <div className="flex items-center gap-2 bg-crimson/10 border border-crimson/30 rounded-lg p-3 mb-4">
                                <AlertTriangle className="w-5 h-5 text-crimson flex-shrink-0" />
                                <div>
                                  <p className="font-display text-sm font-bold text-crimson tracking-wider">
                                    {breach.breach_count} BREACH{breach.breach_count > 1 ? 'ES' : ''} DETECTED
                                  </p>
                                  <p className="font-body text-xs text-ink-secondary">
                                    Potential covenant violations found in document
                                  </p>
                                </div>
                              </div>
                              {breach?.breach_details?.map((b, i) => (
                                <div key={i} className="border border-crimson/15 rounded-lg p-3 mb-2 bg-crimson/3">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="font-display text-xs text-crimson font-bold">
                                      {b.clause || `Clause ${i + 1}`}
                                    </span>
                                    <span className="font-body text-xs text-ink-muted">
                                      p.{b.page_number} · {(b.confidence * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <p className="font-body text-xs text-ink-secondary leading-relaxed">{b.text}</p>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="flex items-center gap-3 p-4">
                              <CheckCircle className="w-8 h-8 text-risk-low" />
                              <div>
                                <p className="font-display text-sm font-bold text-risk-low tracking-wider">
                                  NO BREACHES DETECTED
                                </p>
                                <p className="font-body text-xs text-ink-secondary">
                                  No covenant violations found in this document
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* SHAP */}
                      {key === 'shap' && (
                        <div className="mt-4">
                          <p className="font-body text-ink-secondary text-xs mb-4">
                            SHAP values show each ratio's contribution to the risk score.
                            Red bars increase risk, blue bars decrease risk.
                          </p>
                          <ShapChart shapValues={risk?.shap_values} />
                        </div>
                      )}

                      {/* SUMMARY */}
                      {key === 'summary' && (
                        <div className="mt-4">
                          <div className="bg-surface-raised rounded-xl p-5 border border-ink-muted/10 mb-4">
                            <p className="font-body text-ink-secondary text-sm leading-relaxed">
                              {report?.summary_text || 'Summary not available.'}
                            </p>
                          </div>
                          {report?.key_findings?.length > 0 && (
                            <div>
                              <p className="font-body text-ink-muted text-xs tracking-widest uppercase mb-3">
                                Key Findings
                              </p>
                              <div className="space-y-2">
                                {report.key_findings.map((finding, i) => (
                                  <div key={i} className="flex items-start gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-crimson mt-1.5 flex-shrink-0" />
                                    <p className="font-body text-sm text-ink-secondary">{finding}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>

      {/* ── Floating chat widget — bottom-right corner ───────────── */}
      <ChatWidget documentId={documentId} />

    </div>
  )
}