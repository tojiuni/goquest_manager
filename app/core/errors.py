# app/core/errors.py
class PlaneManagerError(Exception):
    """기본 에러 클래스"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class APIConnectionError(PlaneManagerError):
    """Plane API 연결 실패 시 발생"""
    pass

class DatabaseError(PlaneManagerError):
    """DB 작업 실패 시 발생"""
    pass