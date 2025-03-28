from dataclasses import dataclass
from typing import List, Optional
from playwright.sync_api import Request, Response

# TODO: lots of redundant information in HTTP requests can do some hiding
# header hiding and what-not
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
        req_str = "[Request]: " + str(self.method) + " " + str(self.url) + "\n"
        
        if self._request.redirected_from:
            req_str += "Redirected from: " + str(self._request.redirected_from.url) + "\n"
        if self._request.redirected_to:
            req_str += "Redirecting to: " + str(self._request.redirected_to.url) + "\n"
        if self._request.frame.parent_frame:
            req_str += "From iframe\n"

        req_str += str(self._request.headers) + "\n"
        req_str += str(self._request.post_data)
        return req_str
    
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

    # NOTE: response.body() can return eithejr sunc or asyunc depedning on context
    # of the calllingj function
    async def to_str(self):
        """String representation of HTTP response"""
        resp_str = "[Response]: " + str(self.url) + " " + str(self.status) + "\n"
        
        if self._response.frame.parent_frame:
            resp_str += "From iframe\n"
        resp_str += str(self._response.headers) + "\n"
        
        # Skip body for redirect responses (3xx)
        if 300 <= self.status < 400:
            resp_str += "[Redirect response - no body]"
            return resp_str
            
        try:
            resp_bytes = await self._response.body()
            resp_str += str(resp_bytes)
        except Exception as e:
            resp_str += f"[Error getting response body: {str(e)}]"
            
        return resp_str

@dataclass
class HTTPMessage:
    """Encapsulates a request/response pair"""
    request: HTTPRequest 
    response: Optional[HTTPResponse]

    async def to_str(self):
        req_str = str(self.request)
        resp_str = await self.response.to_str() if self.response else ""

        return f"{req_str}\n{resp_str}"
