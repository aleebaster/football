"""API Layer — REST API routers for the Football Analysis Platform.

All routes go through Application Services, never directly to Engines.

Pipeline:
    REST Endpoint → Application Service → Engine → DTO Mapper → Response
"""
