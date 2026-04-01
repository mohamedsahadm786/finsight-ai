import { RISK_TIERS } from '../../utils/constants'

export function RiskBadge({ tier }) {
  const config = RISK_TIERS[tier] || RISK_TIERS.medium
  return (
    <span className={`font-display text-xs px-2 py-0.5 rounded border font-bold tracking-wider ${config.text} ${config.border} ${config.bg}`}>
      {config.label}
    </span>
  )
}

export function StatusBadge({ status }) {
  const config = {
    completed: { text: 'text-risk-low',      label: 'Completed' },
    processing: { text: 'text-electric-light', label: 'Processing' },
    failed:     { text: 'text-crimson',        label: 'Failed' },
    uploaded:   { text: 'text-ink-secondary',  label: 'Queued' },
    queued:     { text: 'text-ink-secondary',  label: 'Queued' },
  }
  const c = config[status] || config.uploaded
  return <span className={`font-body text-xs font-medium ${c.text}`}>{c.label}</span>
}

export function RoleBadge({ role }) {
  const config = {
    admin:      'text-crimson border-crimson/30 bg-crimson/10',
    analyst:    'text-electric-light border-electric/30 bg-electric/10',
    viewer:     'text-ink-secondary border-ink-muted/20 bg-surface-raised',
    superadmin: 'text-risk-distress border-risk-distress/30 bg-risk-distress/10',
  }
  return (
    <span className={`font-display text-xs font-bold px-2 py-0.5 rounded border tracking-wider ${config[role] || config.viewer}`}>
      {role?.toUpperCase()}
    </span>
  )
}