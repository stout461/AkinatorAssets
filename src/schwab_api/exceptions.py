class SchwabAPIError(Exception):
    def __init__(self, status_code, message, errors=None, correlation_id=None):
        self.status_code = status_code
        self.message = message
        self.errors = errors or []
        self.correlation_id = correlation_id
        super().__init__(f"{status_code} Error: {message}")