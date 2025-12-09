from fastapi import HTTPException, Query
import json
import os

def load_api_keys():
    """Load API keys from file"""
    if os.path.exists('api_keys.json'):
        with open('api_keys.json', 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return set(data.values())
            return set(data)
    
    print("WARNING: api_keys.json not found!")
    print("Run: python generate_keys.py")
    return set()

VALID_API_KEYS = load_api_keys()

def verify_api_key(key: str = Query(..., description="API key for authentication")):
    """Verify the API key is valid"""
    if not VALID_API_KEYS:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "API keys not configured. Contact administrator.",
                "responseType": "error"
            }
        )
    
    if key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Invalid API key",
                "responseType": "error"
            }
        )
    
    return key