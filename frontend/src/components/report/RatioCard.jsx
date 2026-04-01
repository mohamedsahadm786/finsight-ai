export default function RatioCard({ label, value, imputed }) {
  const display = value !== null && value !== undefined ? parseFloat(value).toFixed(2) : 'N/A'
  return (
    <div className="glass rounded-xl p-4 border border-crimson/10 hover:border-crimson/25 transition-all duration-300">
      <div className="flex items-center justify-between mb-2">
        <span className="font-body text-ink-muted text-xs tracking-widest uppercase">{label}</span>
        {imputed && (
          <span className="font-body text-xs text-risk-medium border border-risk-medium/30 px-1.5 py-0.5 rounded">EST</span>
        )}
      </div>
      <div className={`font-display text-2xl font-black ${value !== null && value !== undefined ? 'text-ink-primary' : 'text-ink-muted'}`}>
        {display}
      </div>
    </div>
  )
}