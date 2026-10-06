# security.py - Security utilities for the AI Career Recommendation System
"""
Security utilities including:
- Input validation and sanitization
- Rate limiting
- CORS configuration
- Basic authentication helpers
- Data privacy protections
"""

from typing import Dict, Any, List
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import time
import re
from collections import defaultdict
from collections import deque
import hashlib
import json


# Rate limiting storage (in production, use Redis or similar)
request_history: Dict[str, deque] = defaultdict(deque)


class RequestBodyLimitMiddleware:
    """Bound request buffering, including chunked bodies without Content-Length."""
    def __init__(self, app, max_bytes=1024 * 1024):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            body = message.get('body', b'')
            size += len(body)
            if size > self.max_bytes:
                response = JSONResponse(status_code=413, content={'detail': 'Request body is too large'})
                return await response(scope, receive, send)
            chunks.append(body)
            if not message.get('more_body', False):
                break
        consumed = False

        async def bounded_receive():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {'type': 'http.request', 'body': b''.join(chunks), 'more_body': False}
            return await receive()

        return await self.app(scope, bounded_receive, send)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Number of allowed requests
        self.period = period  # Time period in seconds

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else 'unknown'

        # Clean old requests
        now = time.time()
        request_times = request_history[client_ip]
        while request_times and request_times[0] <= now - self.period:
            request_times.popleft()

        # Check if rate limit exceeded
        if len(request_times) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(max(1, int(self.period - (now - request_times[0]))))}
            )

        # Add current request
        request_times.append(now)

        # Process request
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"

        return response


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return ""

    # Truncate to max length
    text = text[:max_length]

    # Remove potentially dangerous characters
    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove or escape HTML/script tags (basic protection)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]*>', '', text)

    # Remove SQL injection patterns (basic)
    sql_patterns = [
        r'(?i)\bunion\b.*\bselect\b',
        r'(?i)\bselect\b.*\bfrom\b',
        r'(?i)\binsert\s+into\b',
        r'(?i)\bdelete\s+from\b',
        r'(?i)\bdrop\s+table\b',
        r'(?i)\bexec\s*\(',
        r'(?i)\bexecute\s*\(',
        r'[\'"\s]*(?:--|#)',
        r';\s*(?:drop|delete|insert|update|union)',
    ]

    for pattern in sql_patterns:
        text = re.sub(pattern, '', text)

    return text.strip()


def validate_email(email: str) -> bool:
    """Basic email validation"""
    if not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage/logging"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def mask_pii(data: dict, fields_to_mask: List[str] = None) -> dict:
    """
    Mask personally identifiable information in dictionaries.

    Args:
        data: Dictionary containing data
        fields_to_mask: List of field names to mask (defaults to common PII fields)

    Returns:
        Dictionary with masked PII
    """
    if fields_to_mask is None:
        fields_to_mask = ['email', 'ssn', 'phone', 'address', 'full_name', 'name']

    masked_data = data.copy()
    for field in fields_to_mask:
        if field in masked_data and isinstance(masked_data[field], str):
            # Show only first and last character, mask the middle
            value = masked_data[field]
            if len(value) > 2:
                masked_data[field] = value[0] + '*' * (len(value) - 2) + value[-1]
            else:
                masked_data[field] = '*'

    return masked_data


class SecurityValidator:
    """Validation utilities for secure input handling"""

    @staticmethod
    def validate_string_input(value: str, field_name: str, max_length: int = 255) -> str:
        """Validate and sanitize string input"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")

        if len(value) > max_length:
            raise ValueError(f"{field_name} exceeds maximum length of {max_length}")

        return sanitize_input(value, max_length)

    @staticmethod
    def validate_numeric_range(value: int, field_name: str, min_val: int = None, max_val: int = None) -> int:
        """Validate numeric input within range"""
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError(f"{field_name} must be an integer")

        if min_val is not None and value < min_val:
            raise ValueError(f"{field_name} must be at least {min_val}")

        if max_val is not None and value > max_val:
            raise ValueError(f"{field_name} must be at most {max_val}")

        return value

    @staticmethod
    def validate_email_format(email: str) -> str:
        """Validate email format"""
        if not validate_email(email):
            raise ValueError("Invalid email format")
        return email.lower().strip()


# Example usage in main.py would be:
"""
from security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    sanitize_input,
    SecurityValidator
)

# Add middleware to FastAPI app
app.add_middleware(RateLimitMiddleware, calls=50, period=60)  # 50 requests per minute
app.add_middleware(SecurityHeadersMiddleware)

# Example endpoint validation
@app.post("/secure-endpoint")
async def secure_endpoint(user_input: str = Form(...)):
    # Validate and sanitize input
    safe_input = SecurityValidator.validate_string_input(user_input, "user_input", 500)
    # Process safe_input...
    return {"message": "Data processed securely"}
"""
