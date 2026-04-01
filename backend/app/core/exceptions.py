class MeetingIntelligenceException(Exception):
    """Base exception for the application"""
    pass


class AuthenticationError(MeetingIntelligenceException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(MeetingIntelligenceException):
    """Raised when user is not authorized"""
    pass


class MeetingNotFoundError(MeetingIntelligenceException):
    """Raised when a meeting is not found"""
    pass


class ProcessingError(MeetingIntelligenceException):
    """Raised when meeting processing fails"""
    pass


class VectorStoreError(MeetingIntelligenceException):
    """Raised when vector store operations fail"""
    pass
