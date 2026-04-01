import { motion } from 'framer-motion'

export default function Card({ children, className = '', hover = false, glow = false, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`
        glass rounded-xl border border-crimson/10
        ${hover ? 'hover:border-crimson/25 transition-all duration-300' : ''}
        ${glow ? 'shadow-inner-glow' : ''}
        ${className}
      `}
    >
      {children}
    </motion.div>
  )
}