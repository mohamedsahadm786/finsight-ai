import { AlertTriangle, CheckCircle } from 'lucide-react'

export default function BreachAlert({ breach }) {
  if (!breach?.breach_detected) {
    return (
      <div className="flex items-center gap-3 p-4">
        <CheckCircle className="w-8 h-8 text-risk-low" />
        <div>
          <p className="font-display text-sm font-bold text-risk-low tracking-wider">NO BREACHES DETECTED</p>
          <p className="font-body text-xs text-ink-secondary">No covenant violations found in this document</p>
        </div>
      </div>
    )
  }
  return (
    <div>
      <div className="flex items-center gap-2 bg-crimson/10 border border-crimson/30 rounded-lg p-3 mb-4">
        <AlertTriangle className="w-5 h-5 text-crimson flex-shrink-0" />
        <div>
          <p className="font-display text-sm font-bold text-crimson tracking-wider">
            {breach.breach_count} BREACH{breach.breach_count > 1 ? 'ES' : ''} DETECTED
          </p>
          <p className="font-body text-xs text-ink-secondary">Potential covenant violations found in document</p>
        </div>
      </div>
      {breach?.breach_details?.map((b, i) => (
        <div key={i} className="border border-crimson/15 rounded-lg p-3 mb-2 bg-crimson/3">
          <div className="flex items-center justify-between mb-1">
            <span className="font-display text-xs text-crimson font-bold">{b.clause || `Clause ${i + 1}`}</span>
            <span className="font-body text-xs text-ink-muted">p.{b.page_number} · {(b.confidence * 100).toFixed(0)}%</span>
          </div>
          <p className="font-body text-xs text-ink-secondary leading-relaxed">{b.text}</p>
        </div>
      ))}
    </div>
  )
}