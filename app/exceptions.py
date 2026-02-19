#Code 2
from fastapi import HTTPException

class ServiceException(HTTPException):
    """
    Custom exception that behaves like FastAPI's HTTPException,
    so FastAPI will automatically return the correct status code
    instead of 500.
    """
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

# Code 1
#  Base custom exception class with a status code and detail message
'''
class ServiceException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
'''