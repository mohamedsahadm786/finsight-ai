import apiClient from './client'

export const chatApi = {
  send: (question, documentId, sessionId = null) =>
    apiClient.post('/chat/', { question, document_id: documentId, session_id: sessionId }),

  getHistory: (sessionId) => apiClient.get(`/chat/${sessionId}/history`),
}