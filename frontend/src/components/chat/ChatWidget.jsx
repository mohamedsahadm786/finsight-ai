import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, X, Send, Brain, Minimize2 } from 'lucide-react'
import { chatApi } from '../../api/chat'

export default function ChatWidget({ documentId }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I have analyzed this document. Ask me anything about the financial data, ratios, covenants, or risk factors.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      setTimeout(() => inputRef.current?.focus(), 300)
    }
  }, [messages, open])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const question = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const response = await chatApi.send(question, documentId, sessionId)
      const data = response.data
      if (!sessionId) setSessionId(data.session_id)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        chunks: data.retrieved_chunk_ids,
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      {/* Floating button */}
      <AnimatePresence>
        {!open && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-crimson shadow-crimson-lg flex items-center justify-center cursor-pointer"
            style={{ boxShadow: '0 0 30px rgba(198,40,40,0.6), 0 4px 20px rgba(0,0,0,0.4)' }}
          >
            {/* Pulse ring */}
            <motion.div
              animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0, 0.6] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute inset-0 rounded-full bg-crimson"
            />
            <MessageSquare className="w-6 h-6 text-white relative z-10" />
            {/* Unread dot */}
            <div className="absolute top-0 right-0 w-3.5 h-3.5 bg-risk-low rounded-full border-2 border-void animate-pulse" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat window */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 20, originX: 1, originY: 1 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 20 }}
            transition={{ type: 'spring', stiffness: 350, damping: 30 }}
            className="fixed bottom-6 right-6 z-50 w-80 sm:w-96 flex flex-col"
            style={{ height: '500px' }}
          >
            <div className="glass-strong rounded-2xl border border-crimson/25 flex flex-col h-full overflow-hidden"
              style={{ boxShadow: '0 0 40px rgba(198,40,40,0.2), 0 20px 60px rgba(0,0,0,0.5)' }}>

              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-crimson/15 flex-shrink-0">
                <div className="flex items-center gap-2.5">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                    className="w-7 h-7 rounded-lg bg-crimson/15 border border-crimson/30 flex items-center justify-center"
                  >
                    <Brain className="w-3.5 h-3.5 text-crimson" />
                  </motion.div>
                  <div>
                    <p className="font-display text-xs font-bold text-ink-primary tracking-wider">AI ANALYST</p>
                    <div className="flex items-center gap-1">
                      <motion.div
                        animate={{ opacity: [1, 0.3, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className="w-1.5 h-1.5 rounded-full bg-risk-low"
                      />
                      <span className="font-body text-xs text-risk-low">Online</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <motion.button
                    onClick={() => setOpen(false)}
                    whileHover={{ scale: 1.1 }}
                    className="w-7 h-7 rounded-lg hover:bg-surface-raised flex items-center justify-center text-ink-muted hover:text-ink-primary transition-colors"
                  >
                    <Minimize2 className="w-3.5 h-3.5" />
                  </motion.button>
                  <motion.button
                    onClick={() => setOpen(false)}
                    whileHover={{ scale: 1.1 }}
                    className="w-7 h-7 rounded-lg hover:bg-crimson/10 flex items-center justify-center text-ink-muted hover:text-crimson transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </motion.button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="w-6 h-6 rounded-full bg-crimson/15 border border-crimson/25 flex items-center justify-center flex-shrink-0 mr-2 mt-0.5">
                        <Brain className="w-3 h-3 text-crimson" />
                      </div>
                    )}
                    <div className={`max-w-[75%] rounded-2xl px-3 py-2 text-xs font-body leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-crimson/20 border border-crimson/25 text-ink-primary rounded-br-sm'
                        : 'bg-surface-overlay border border-ink-muted/10 text-ink-secondary rounded-bl-sm'
                    }`}>
                      {msg.content}
                    </div>
                  </motion.div>
                ))}

                {/* Typing indicator */}
                {loading && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start items-end gap-2">
                    <div className="w-6 h-6 rounded-full bg-crimson/15 border border-crimson/25 flex items-center justify-center flex-shrink-0">
                      <Brain className="w-3 h-3 text-crimson" />
                    </div>
                    <div className="bg-surface-overlay border border-ink-muted/10 rounded-2xl rounded-bl-sm px-3 py-2.5">
                      <div className="flex gap-1">
                        {[0, 1, 2].map(i => (
                          <motion.div key={i} className="w-1.5 h-1.5 rounded-full bg-ink-muted"
                            animate={{ y: [-3, 0, -3] }}
                            transition={{ duration: 0.7, repeat: Infinity, delay: i * 0.15 }} />
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="px-3 py-3 border-t border-crimson/10 flex-shrink-0">
                <div className="flex gap-2 items-end">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about this document..."
                    className="flex-1 bg-void/70 border border-ink-muted/20 rounded-xl px-3 py-2.5 font-body text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-crimson transition-all duration-300 resize-none"
                  />
                  <motion.button
                    onClick={sendMessage}
                    disabled={!input.trim() || loading}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="w-9 h-9 rounded-xl bg-crimson hover:bg-crimson-light disabled:opacity-40 flex items-center justify-center transition-all duration-300 flex-shrink-0 shadow-crimson"
                  >
                    <Send className="w-3.5 h-3.5 text-white" />
                  </motion.button>
                </div>
                <p className="font-body text-ink-muted text-xs mt-1.5 text-center opacity-60">
                  Hybrid RAG · HyDE · Cross-Encoder
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}