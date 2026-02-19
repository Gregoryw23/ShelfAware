from fastapi import HTTPException

class ServiceException(HTTPException):
    """
    Custom exception that behaves like FastAPI's HTTPException,
    so FastAPI will automatically return the correct status code
    instead of 500.
    """
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class ChromaEmbeddingConflictError(ServiceException):
    def __init__(self, detail: str, persisted_llm_provider: str):
        super().__init__(status_code=409, detail=detail) # 409 Conflict
        self.persisted_llm_provider = persisted_llm_provider
