class PlaneAPIException(Exception):
    """Custom exception for Plane API errors."""

    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)
