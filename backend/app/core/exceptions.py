from fastapi import HTTPException, status

class ProspectAIException(Exception):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DailyLimitReachedException(ProspectAIException):
    pass

class OutsideSendingWindowException(ProspectAIException):
    pass

class LeadSuppressedException(ProspectAIException):
    pass

class AIProviderException(ProspectAIException):
    pass

class EvolutionAPIException(ProspectAIException):
    pass

class SSRFProtectionException(ProspectAIException):
    pass
