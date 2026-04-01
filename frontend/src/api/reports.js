import apiClient from './client'

export const reportsApi = {
  list: () => apiClient.get('/reports/'),
  getByDocumentId: (documentId) => apiClient.get(`/reports/${documentId}`),
}