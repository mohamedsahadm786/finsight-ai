import apiClient from './client'

export const documentsApi = {
  list: () => apiClient.get('/documents/'),

  upload: (file, documentType, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    return apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    })
  },

  getById: (id) => apiClient.get(`/documents/${id}`),
  getJobStatus: (jobId) => apiClient.get(`/jobs/${jobId}/status`),
}