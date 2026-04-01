import { motion } from 'framer-motion'

export default function Button({
  children, onClick, type = 'button', variant = 'primary',
  size = 'md', disabled = false, loading = false, className = '', icon: Icon,
}) {
  const base = 'font-display font-bold tracking-widest rounded-lg transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-crimson hover:bg-crimson-light text-white shadow-crimson hover:shadow-crimson-lg',
    outline: 'border border-crimson/30 text-crimson hover:bg-crimson/10 hover:border-crimson',
    ghost:   'text-ink-secondary hover:text-ink-primary hover:bg-surface-raised',
    danger:  'bg-crimson/80 hover:bg-crimson text-white',
  }

  const sizes = {
    sm: 'text-xs px-3 py-1.5',
    md: 'text-sm px-5 py-2.5',
    lg: 'text-sm px-7 py-3.5',
  }

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {loading ? (
        <>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
          />
          PROCESSING...
        </>
      ) : (
        <>
          {Icon && <Icon className="w-4 h-4" />}
          {children}
        </>
      )}
    </motion.button>
  )
}