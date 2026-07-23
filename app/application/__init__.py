"""Application Layer — separates presentation from business logic.

Pipeline:
    REST Endpoint → Application Service → Engine → DTO Mapper → Response

This allows the same logic to be used for:
    REST API, Dashboard, CLI, Telegram, Worker
"""
