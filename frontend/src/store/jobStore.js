import { create } from 'zustand'

const useJobStore = create((set, get) => ({
  activeJobs: {},

  addJob: (jobId, documentId, filename) => {
    set((state) => ({
      activeJobs: {
        ...state.activeJobs,
        [jobId]: { jobId, documentId, filename, status: 'queued', currentAgent: '', startedAt: Date.now() },
      },
    }))
  },

  updateJob: (jobId, updates) => {
    set((state) => ({
      activeJobs: {
        ...state.activeJobs,
        [jobId]: { ...state.activeJobs[jobId], ...updates },
      },
    }))
  },

  removeJob: (jobId) => {
    set((state) => {
      const updated = { ...state.activeJobs }
      delete updated[jobId]
      return { activeJobs: updated }
    })
  },

  getJob: (jobId) => get().activeJobs[jobId],
}))

export default useJobStore