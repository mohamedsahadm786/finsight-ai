import { motion } from 'framer-motion'
import { Brain } from 'lucide-react'

export default function ChatMessage({ message, index }) {
  const isUser = message.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <div className="w-6 h-6 rounded-full bg-crimson/15 border border-crimson/25 flex items-center justify-center flex-shrink-0 mr-2 mt-0.5">
          <Brain className="w-3 h-3 text-crimson" />
        </div>
      )}
      <div className={`max-w-[75%] rounded-2xl px-3 py-2 text-xs font-body leading-relaxed ${
        isUser
          ? 'bg-crimson/20 border border-crimson/25 text-ink-primary rounded-br-sm'
          : 'bg-surface-overlay border border-ink-muted/10 text-ink-secondary rounded-bl-sm'
      }`}>
        {message.content}
      </div>
    </motion.div>
  )
}