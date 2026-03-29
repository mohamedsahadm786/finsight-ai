"""
Pydantic schemas package.

All request/response schemas are organized by domain:
- auth: login, register, tokens, password reset
- document: upload, listing
- job: processing status
- report: full risk report with all agent outputs
- chat: RAG questions and answers
- admin: tenant user management
- superadmin: platform-wide management
"""