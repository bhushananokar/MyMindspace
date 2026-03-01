"""
Simple synchronous collections using requests library
"""
from typing import Dict, Any, List, Optional
import uuid
import logging

from database.simple_client import get_simple_client

logger = logging.getLogger(__name__)

def sync_create_user(user_data: Dict[str, Any]) -> str:
    """Create a new user synchronously"""
    client = get_simple_client()
    
    user_id = user_data.get('id', str(uuid.uuid4()))
    
    user_doc = {
        'id': user_id,
        'name': user_data.get('name', ''),
        'email': user_data.get('email'),
        'preferences': user_data.get('preferences', {})
    }
    
    try:
        created_id = client.create_user(user_doc)
        return created_id or user_id
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise

def sync_save_session(session_data: Dict[str, Any]) -> str:
    """Save a processing session synchronously"""
    client = get_simple_client()
    
    session_id = session_data.get('id', str(uuid.uuid4()))
    
    session_doc = {
        'id': session_id,
        'user_id': session_data.get('user_id'),
        'status': session_data.get('status', 'pending'),
        'input_type': session_data.get('input_type'),
        'input_data': session_data.get('input_data', {}),
        'results': session_data.get('results', {}),
        'error': session_data.get('error'),
        'meditation_type': session_data.get('meditation_type'),
        'duration_minutes': session_data.get('duration_minutes')
    }
    
    try:
        created_id = client.create_session(session_doc)
        return created_id or session_id
    except Exception as e:
        logger.error(f"Failed to save session: {e}")
        raise

def sync_update_session(session_id: str, updates: Dict[str, Any]) -> bool:
    """Update session data synchronously"""
    client = get_simple_client()
    
    try:
        return client.update_session(session_id, updates)
    except Exception as e:
        logger.error(f"Failed to update session: {e}")
        return False

def sync_test_api_connection() -> bool:
    """Test API connection synchronously"""
    client = get_simple_client()
    try:
        health_status = client.health_check()
        return health_status is not None
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False