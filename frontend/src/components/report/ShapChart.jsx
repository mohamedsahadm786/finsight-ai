import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'

export default function ShapChart({ shapValues }) {
  if (!shapValues) return <p className="font-body text-ink-muted text-sm text-center py-4">No SHAP data available.</p>
  const data = Object.entries(shapValues)
    .map(([key, value]) => ({
      name: key.replace(/_/g, ' ').toUpperCase(),
      value: parseFloat(parseFloat(value).toFixed(3)),
      positive: parseFloat(value) >= 0,
    }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ left: 90, right: 20, top: 5, bottom: 5 }}>
        <XAxis type="number" tick={{ fill: '#9090A8', fontSize: 10 }} />
        <YAxis type="category" dataKey="name" tick={{ fill: '#9090A8', fontSize: 10 }} width={85} />
        <Tooltip contentStyle={{ background: '#0D0D14', border: '1px solid rgba(198,40,40,0.2)', borderRadius: 8 }}
          labelStyle={{ color: '#F0F0F5' }} itemStyle={{ color: '#C62828' }} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((entry, i) => <Cell key={i} fill={entry.positive ? '#C62828' : '#1565C0'} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}