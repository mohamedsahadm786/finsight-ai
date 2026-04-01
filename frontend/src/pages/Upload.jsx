import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Upload as UploadIcon, FileText, X, CheckCircle,
  AlertCircle, ChevronLeft, Zap
} from 'lucide-react'
import useAuthStore from '../store/authStore'
import apiClient from '../api/client'

function Sidebar({ user, onLogout }) {
  const navigate = useNavigate()
  return (
    <div className="fixed left-0 top-0 h-screen w-64 glass-strong border-r border-crimson/10 flex flex-col z-50">
      <div className="p-6 border-b border-crimson/10">
        <div className="flex items-center gap-3">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-crimson rounded-full flex items-center justify-center flex-shrink-0">
            <div className="w-2 h-2 bg-crimson rounded-full" />
          </motion.div>
          <h1 className="font-display text-lg font-black text-ink-primary tracking-widest">
            FIN<span className="text-crimson">SIGHT</span>
          </h1>
        </div>
      </div>
      <div className="p-4 border-b border-crimson/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-crimson to-crimson-dark flex items-center justify-center font-display text-xs font-black text-white">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div>
            <p className="font-body text-sm font-semibold text-ink-primary truncate">{user?.full_name}</p>
            <p className="font-body text-xs text-ink-muted capitalize">{user?.role}</p>
          </div>
        </div>
      </div>
      <div className="flex-1 p-4">
        <motion.button onClick={() => navigate('/dashboard')} whileHover={{ x: 4 }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-ink-secondary hover:text-ink-primary hover:bg-surface-raised transition-all duration-200">
          <ChevronLeft className="w-4 h-4" />
          <span className="font-body text-sm">Back to Dashboard</span>
        </motion.button>
      </div>
    </div>
  )
}

export default function Upload() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [file, setFile] = useState(null)
  const [docType, setDocType] = useState('annual_report')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState('')

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError('')
    if (rejectedFiles.length > 0) {
      setError('Only PDF files are accepted. Maximum size: 50MB.')
      return
    }
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 50 * 1024 * 1024,
    multiple: false,
  })

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError('')
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', docType)

    try {
      const response = await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          setUploadProgress(percent)
        },
      })
      const { job_id, document_id } = response.data
      navigate(`/processing/${job_id}?document_id=${document_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
      setUploading(false)
    }
  }

  const docTypes = [
    { value: 'annual_report', label: 'Annual Report' },
    { value: 'earnings_call', label: 'Earnings Call' },
    { value: 'credit_agreement', label: 'Credit Agreement' },
    { value: 'other', label: 'Other' },
  ]

  return (
    <div className="min-h-screen bg-void flex">
      <Sidebar user={user} />
      <div className="ml-64 flex-1 p-8 flex flex-col items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-2xl"
        >
          <div className="mb-8 text-center">
            <h2 className="font-display text-2xl font-black text-ink-primary tracking-wider mb-2">
              UPLOAD DOCUMENT
            </h2>
            <p className="font-body text-ink-secondary text-sm">
              Upload a financial PDF to begin AI-powered credit risk analysis
            </p>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="flex items-center gap-2 bg-crimson/10 border border-crimson/30 rounded-lg p-3 mb-6">
                <AlertCircle className="w-4 h-4 text-crimson flex-shrink-0" />
                <span className="font-body text-crimson text-sm">{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Drop zone */}
          <div
            {...getRootProps()}
            className={`relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-300 mb-6 ${
              isDragActive
                ? 'border-crimson bg-crimson/5 shadow-crimson'
                : file
                ? 'border-risk-low/50 bg-risk-low/5'
                : 'border-ink-muted/30 hover:border-crimson/50 hover:bg-crimson/3'
            }`}
          >
            <input {...getInputProps()} />

            <AnimatePresence mode="wait">
              {file ? (
                <motion.div key="file" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
                  <div className="w-16 h-16 rounded-full bg-risk-low/10 border border-risk-low/30 flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-risk-low" />
                  </div>
                  <p className="font-display text-sm font-bold text-ink-primary tracking-wider mb-1">
                    {file.name}
                  </p>
                  <p className="font-body text-ink-secondary text-xs">
                    {(file.size / 1024 / 1024).toFixed(2)} MB — Ready for analysis
                  </p>
                  <button
                    onClick={(e) => { e.stopPropagation(); setFile(null) }}
                    className="mt-4 flex items-center gap-1 text-ink-muted hover:text-crimson transition-colors mx-auto text-xs font-body"
                  >
                    <X className="w-3 h-3" /> Remove file
                  </button>
                </motion.div>
              ) : isDragActive ? (
                <motion.div key="drag" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <motion.div
                    animate={{ y: [-5, 5, -5] }}
                    transition={{ duration: 1, repeat: Infinity }}
                    className="w-16 h-16 rounded-full bg-crimson/10 border border-crimson/30 flex items-center justify-center mx-auto mb-4"
                  >
                    <UploadIcon className="w-8 h-8 text-crimson" />
                  </motion.div>
                  <p className="font-display text-sm font-bold text-crimson tracking-wider">
                    DROP IT HERE
                  </p>
                </motion.div>
              ) : (
                <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <motion.div
                    animate={{ y: [-3, 3, -3] }}
                    transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                    className="w-16 h-16 rounded-full bg-surface-raised border border-ink-muted/20 flex items-center justify-center mx-auto mb-4"
                  >
                    <FileText className="w-8 h-8 text-ink-muted" />
                  </motion.div>
                  <p className="font-display text-sm font-bold text-ink-primary tracking-wider mb-2">
                    DRAG &amp; DROP PDF HERE
                  </p>
                  <p className="font-body text-ink-secondary text-xs mb-4">
                    or click to browse your files
                  </p>
                  <span className="font-body text-ink-muted text-xs border border-ink-muted/20 rounded-full px-3 py-1">
                    PDF only · Max 50MB
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Document type selector */}
          <div className="mb-6">
            <label className="font-body text-ink-secondary text-xs tracking-widest uppercase mb-3 block">
              Document Type
            </label>
            <div className="grid grid-cols-4 gap-2">
              {docTypes.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setDocType(value)}
                  className={`py-2.5 px-3 rounded-lg font-body text-xs font-medium transition-all duration-200 ${
                    docType === value
                      ? 'bg-crimson/10 border border-crimson/40 text-crimson'
                      : 'border border-ink-muted/20 text-ink-secondary hover:border-ink-muted/40'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Upload progress */}
          {uploading && (
            <div className="mb-6">
              <div className="flex justify-between mb-2">
                <span className="font-body text-xs text-ink-secondary">Uploading...</span>
                <span className="font-display text-xs text-crimson font-bold">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-surface-raised rounded-full h-1.5 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-crimson to-crimson-light rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
          )}

          {/* Submit button */}
          <motion.button
            onClick={handleUpload}
            disabled={!file || uploading}
            whileHover={{ scale: file && !uploading ? 1.02 : 1 }}
            whileTap={{ scale: file && !uploading ? 0.98 : 1 }}
            className="w-full bg-crimson hover:bg-crimson-light disabled:opacity-40 disabled:cursor-not-allowed text-white font-display font-bold py-3.5 rounded-lg tracking-widest text-sm transition-all duration-300 shadow-crimson flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                UPLOADING...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                INITIATE ANALYSIS
              </>
            )}
          </motion.button>
        </motion.div>
      </div>
    </div>
  )
}