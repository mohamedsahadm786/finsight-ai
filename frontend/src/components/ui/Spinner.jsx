import { motion } from 'framer-motion'

export default function Spinner({ size = 'md', color = 'crimson' }) {
  const sizes = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12' }
  const colors = { crimson: 'border-crimson', electric: 'border-electric-light', white: 'border-white' }
  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      className={`${sizes[size]} border-2 ${colors[color]} border-t-transparent rounded-full`}
    />
  )
}