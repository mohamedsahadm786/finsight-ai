export default function SourceCitation({ chunkIds }) {
  if (!chunkIds || chunkIds.length === 0) return null
  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {chunkIds.slice(0, 3).map((id, i) => (
        <span key={i}
          className="font-mono text-xs text-ink-muted border border-ink-muted/15 px-1.5 py-0.5 rounded bg-surface-raised">
          src:{String(id).slice(0, 6)}
        </span>
      ))}
    </div>
  )
}