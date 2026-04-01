import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'

export default function SentimentChart({ sentiment }) {
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
        <Tooltip contentStyle={{ background: '#0D0D14', border: '1px solid rgba(198,40,40,0.2)', borderRadius: 8 }}
          labelStyle={{ color: '#F0F0F5' }} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => <Cell key={i} fill={entry.color} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}