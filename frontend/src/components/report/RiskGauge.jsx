import { ResponsiveContainer, RadialBarChart, RadialBar } from 'recharts'
import { RISK_TIERS } from '../../utils/constants'

export default function RiskGauge({ score, tier }) {
  const config = RISK_TIERS[tier] || RISK_TIERS.medium
  const percentage = Math.round((score || 0) * 100)
  const data = [{ value: percentage, fill: config.color }]

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-28">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart cx="50%" cy="100%" innerRadius="60%" outerRadius="100%"
            startAngle={180} endAngle={0} data={data}>
            <RadialBar dataKey="value" cornerRadius={4} background={{ fill: '#1a1a2e' }} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center pointer-events-none">
          <div className="font-display text-3xl font-black" style={{ color: config.color }}>{percentage}</div>
          <div className="font-body text-xs text-ink-muted">/ 100</div>
        </div>
      </div>
      <div className="mt-2 font-display text-sm font-bold tracking-widest px-4 py-1 rounded-full border"
        style={{ color: config.color, borderColor: config.color + '40', backgroundColor: config.color + '15' }}>
        {config.label}
      </div>
    </div>
  )
}