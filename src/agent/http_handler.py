from dataclasses import dataclass
from typing import List, Optional
from playwright.sync_api import Request, Response


class HTTPRequest:
    """Encapsulates a request object"""
    def __init__(self, request: Request):
        self._request = request
        
    @property
    def method(self):
        return self._request.method
        
    @property
    def url(self):
        return self._request.url

    def __str__(self):
        """String representation of HTTP request"""
        return f"[Request]: {self.method} {self.url}"
    
class HTTPResponse:
    def __init__(self, response: Response):
        self._response = response
        
    @property
    def url(self):
        return self._response.url
        
    @property
    def status(self):
        return self._response.status
        
    @property
    def headers(self):
        return self._response.headers
        
    def get_content_type(self) -> str:
        """Get content type from response headers"""
        if not self.headers:
            return ""
        content_type = self.headers.get("content-type", "")
        return content_type.lower()
    
    def get_status_code(self) -> int:
        """Get HTTP status code"""
        if not self.status:
            return 0
        return self.status
    
    def get_response_size(self) -> int:
        """Get response payload size in bytes"""
        if not self.headers:
            return 0
        content_length = self.headers.get("content-length")
        if content_length and content_length.isdigit():
            return int(content_length)
        # If content-length not available, could try to get actual body size
        return 0

    def __str__(self):
        """String representation of HTTP response"""
        return f"[Response]: {self.url}"

@dataclass
class HTTPMessage:
    """Encapsulates a request/response pair"""
    request: HTTPRequest 
    response: Optional[HTTPResponse]

    def __str__(self):
        """String representation of HTTP message"""
        return f"{str(self.request)}\n{str(self.response)}"

