import { motion } from 'framer-motion'
import Navbar from './Navbar'

export default function PageWrapper({ children, fullWidth = false }) {
  return (
    <div className="min-h-screen bg-void flex">
      <Navbar />
      <motion.main
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className={`ml-64 flex-1 ${fullWidth ? '' : 'max-w-6xl'} p-8`}
      >
        {children}
      </motion.main>
    </div>
  )
}