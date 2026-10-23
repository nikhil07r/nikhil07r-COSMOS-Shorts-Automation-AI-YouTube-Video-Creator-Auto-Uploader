import re
from typing import Any, Dict

def redact_sensitive_data(data: Any) -> Any:
    """Recursively redacts API keys, tokens, and secrets from dictionaries or strings."""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(term in k_lower for term in ["token", "secret", "password", "key", "authorization"]):
                if isinstance(v, str) and len(v) > 8:
                    redacted[k] = f"{v[:4]}...{v[-4:]}"
                else:
                    redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_sensitive_data(v)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Redact bearer tokens or hex strings if found in text
        data = re.sub(r'(ya29\.[a-zA-Z0-9_-]+)', r'ya29.[REDACTED]', data)
        return data
    return data

def is_localhost(host: str) -> bool:
    """Verifies that the request originates from localhost."""
    return host in ["127.0.0.1", "localhost", "::1"]
