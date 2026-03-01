"""
Simple HTTP client using requests library as fallback
"""
import requests
import json
from typing import Dict, Any, List, Optional

class SimpleMeditationDBClient:
    """
    Simple synchronous client for MeditationDB API using requests
    """
    
    def __init__(self, base_url: str = "https://meditationdb-api-222233295505.asia-south1.run.app"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.timeout = 30
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        
        try:
            headers = {"Content-Type": "application/json"} if data else {}
            
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            # Handle different response status codes
            if response.status_code == 200:
                result = response.json()
                return result.get('data', result) if 'data' in result else result
            elif response.status_code == 201:
                result = response.json()
                return result.get('data', result) if 'data' in result else result
            elif response.status_code == 404:
                return None
            elif response.status_code >= 400:
                error_text = response.text
                print(f"API Error {response.status_code}: {error_text}")
                raise Exception(f"API request failed with status {response.status_code}: {error_text}")
            
            return response.json()
            
        except requests.RequestException as e:
            print(f"HTTP client error: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            print(f"Request error: {e}")
            raise
    
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        api_data = {
            "name": user_data.get("name", ""),
            "email": user_data.get("email"),
            "preferences": user_data.get("preferences", {})
        }
        
        if "preferences" not in api_data or not api_data["preferences"]:
            api_data["preferences"] = {}
        
        if "experience_level" not in api_data["preferences"]:
            api_data["preferences"]["experience_level"] = "beginner"
        
        if "goals" not in api_data["preferences"]:
            api_data["preferences"]["goals"] = ["stress_reduction"]
            
        result = self._make_request("POST", "/users", api_data)
        return result.get("id") or result.get("_id")
    
    def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create a meditation session"""
        api_data = {
            "user_id": session_data.get("user_id"),
            "input_type": session_data.get("input_type", "text"),
            "input_data": session_data.get("input_data", {})
        }
        
        result = self._make_request("POST", "/sessions", api_data)
        return result.get("id") or result.get("_id")
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        result = self._make_request("PUT", f"/sessions/{session_id}", updates)
        return result is not None
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return self._make_request("GET", "/health")

# Simple synchronous client
_simple_client = None

def get_simple_client() -> SimpleMeditationDBClient:
    """Get or create the simple client instance"""
    global _simple_client
    if _simple_client is None:
        _simple_client = SimpleMeditationDBClient()
    return _simple_client