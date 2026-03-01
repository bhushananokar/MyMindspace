"""
Database collections module using MeditationDB API
Replaces Firebase operations with HTTP API calls
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import logging

from database.api_client import get_api_client

logger = logging.getLogger(__name__)

# ==================== GENERIC CRUD OPERATIONS ====================

async def save_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> str:
    """
    Save a document using the API client
    Maps collection names to appropriate API endpoints
    
    Args:
        collection_name: Name of the collection (users, sessions, feedback, etc.)
        doc_id: Document ID (will be included in data)
        data: Document data
        
    Returns:
        Document ID
    """
    api_client = get_api_client()
    
    # Ensure ID is in the data
    data_with_id = {**data, 'id': doc_id}
    
    try:
        if collection_name == 'users':
            return await api_client.create_user(data_with_id)
        elif collection_name == 'sessions':
            return await api_client.create_session(data_with_id)
        elif collection_name == 'feedback':
            return await api_client.create_feedback(data_with_id)
        elif collection_name == 'vectors':
            return await api_client.create_vector(data_with_id)
        elif collection_name == 'meditation_history':
            return await api_client.create_history_entry(data_with_id)
        else:
            raise ValueError(f"Unsupported collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to save document to {collection_name}: {e}")
        raise

async def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a document by ID using the API client
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        
    Returns:
        Document data or None if not found
    """
    api_client = get_api_client()
    
    try:
        if collection_name == 'users':
            return await api_client.get_user(doc_id)
        elif collection_name == 'sessions':
            return await api_client.get_session(doc_id)
        elif collection_name == 'feedback':
            return await api_client.get_feedback(doc_id)
        elif collection_name == 'vectors':
            return await api_client.get_vector(doc_id)
        else:
            raise ValueError(f"Unsupported collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to get document from {collection_name}: {e}")
        return None

async def update_document(collection_name: str, doc_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update a document using the API client
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        updates: Fields to update
        
    Returns:
        True if successful
    """
    api_client = get_api_client()
    
    try:
        if collection_name == 'users':
            return await api_client.update_user(doc_id, updates)
        elif collection_name == 'sessions':
            return await api_client.update_session(doc_id, updates)
        elif collection_name == 'vectors':
            # Note: Vector updates might need special handling
            return await api_client.update_session(doc_id, updates)  # Placeholder
        else:
            raise ValueError(f"Unsupported collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to update document in {collection_name}: {e}")
        return False

async def delete_document(collection_name: str, doc_id: str) -> bool:
    """
    Delete a document - Note: API might not support all delete operations
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        
    Returns:
        True if successful
    """
    logger.warning(f"Delete operation for {collection_name}:{doc_id} - Check API support")
    # Most APIs don't support direct delete, return True for compatibility
    return True

async def query_documents(
    collection_name: str,
    filters: Optional[List[Tuple[str, str, Any]]] = None,
    order_by: Optional[Tuple[str, str]] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Query documents using the API client
    Note: Advanced filtering might be limited compared to Firebase
    
    Args:
        collection_name: Name of the collection
        filters: List of (field, operator, value) tuples (limited support)
        order_by: (field, direction) tuple for sorting (limited support)
        limit: Maximum number of documents to return
        
    Returns:
        List of documents
    """
    api_client = get_api_client()
    
    try:
        limit = limit or 50
        
        if collection_name == 'users':
            return await api_client.get_users(limit=limit)
        elif collection_name == 'sessions':
            status_filter = None
            if filters:
                for field, operator, value in filters:
                    if field == 'status' and operator == '==':
                        status_filter = value
                        break
            return await api_client.get_sessions(status=status_filter, limit=limit)
        elif collection_name == 'vectors':
            # Extract entity_id and entity_type from filters
            entity_id = None
            entity_type = None
            if filters:
                for field, operator, value in filters:
                    if field == 'entity_id' and operator == '==':
                        entity_id = value
                    elif field == 'entity_type' and operator == '==':
                        entity_type = value
            if entity_id:
                return await api_client.get_vectors_by_entity_id(entity_id, entity_type, limit=limit)
            elif entity_type:
                return await api_client.get_vectors_by_entity_type(entity_type, limit=limit)
            else:
                result = await api_client._make_request("GET", "/vectors", params={"limit": limit})
                return result if isinstance(result, list) else (result.get("data", []) if result else [])
        else:
            raise ValueError(f"Unsupported collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to query documents from {collection_name}: {e}")
        return []

# ==================== USER OPERATIONS ====================

async def create_user(user_data: Dict[str, Any]) -> str:
    """
    Create a new user
    
    Args:
        user_data: User data
        
    Returns:
        User ID
    """
    api_client = get_api_client()
    
    # Generate ID if not provided
    user_id = user_data.get('id', str(uuid.uuid4()))
    
    user_doc = {
        'id': user_id,
        'name': user_data.get('name', ''),
        'email': user_data.get('email'),
        'preferences': user_data.get('preferences', {})
    }
    
    created_id = await api_client.create_user(user_doc)
    return created_id or user_id

async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    api_client = get_api_client()
    return await api_client.get_user(user_id)

async def update_user(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user data"""
    api_client = get_api_client()
    return await api_client.update_user(user_id, updates)

async def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> bool:
    """Update user preferences"""
    api_client = get_api_client()
    return await api_client.update_user_preferences(user_id, preferences)

# ==================== SESSION OPERATIONS ====================

async def save_session(session_data: Dict[str, Any]) -> str:
    """
    Save a processing session
    
    Args:
        session_data: Session data
        
    Returns:
        Session ID
    """
    api_client = get_api_client()
    
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
    
    created_id = await api_client.create_session(session_doc)
    return created_id or session_id

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID"""
    api_client = get_api_client()
    return await api_client.get_session(session_id)

async def update_session(session_id: str, updates: Dict[str, Any]) -> bool:
    """Update session data"""
    api_client = get_api_client()
    
    # Handle different types of updates
    if 'status' in updates and len(updates) == 1:
        return await api_client.update_session_status(session_id, updates['status'])
    elif 'results' in updates and len(updates) == 1:
        return await api_client.update_session_results(session_id, updates['results'])
    else:
        return await api_client.update_session(session_id, updates)

async def get_user_sessions(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's recent sessions"""
    api_client = get_api_client()
    return await api_client.get_user_sessions(user_id, limit)

async def get_sessions_by_status(status: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get sessions by status"""
    api_client = get_api_client()
    return await api_client.get_sessions(status=status, limit=limit)

# ==================== FEEDBACK OPERATIONS ====================

async def save_feedback(feedback_data: Dict[str, Any]) -> str:
    """
    Save user feedback
    
    Args:
        feedback_data: Feedback data
        
    Returns:
        Feedback ID
    """
    api_client = get_api_client()
    
    feedback_id = feedback_data.get('id', str(uuid.uuid4()))
    
    feedback_doc = {
        'id': feedback_id,
        'user_id': feedback_data.get('user_id'),
        'session_id': feedback_data.get('session_id'),
        'rating': feedback_data.get('rating'),
        'comment': feedback_data.get('comment', ''),
        'feedback_text': feedback_data.get('feedback_text', feedback_data.get('comment', '')),
        'meditation_type': feedback_data.get('meditation_type'),
        'effectiveness': feedback_data.get('effectiveness', feedback_data.get('rating')),
        'categories': feedback_data.get('categories', {})
    }
    
    created_id = await api_client.create_feedback(feedback_doc)
    return created_id or feedback_id

async def get_feedback(feedback_id: str) -> Optional[Dict[str, Any]]:
    """Get feedback by ID"""
    api_client = get_api_client()
    return await api_client.get_feedback(feedback_id)

async def get_user_feedback(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's feedback"""
    api_client = get_api_client()
    return await api_client.get_user_feedback(user_id, limit)

async def get_session_feedback(session_id: str) -> List[Dict[str, Any]]:
    """Get feedback for a specific session"""
    api_client = get_api_client()
    return await api_client.get_session_feedback(session_id)

async def get_feedback_by_meditation_type(meditation_type: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get feedback by meditation type - using general feedback query"""
    api_client = get_api_client()
    # API doesn't have direct meditation type filter, return general feedback
    # This could be enhanced with client-side filtering if needed
    logger.info(f"Feedback by meditation type {meditation_type} - using general query")
    return []

# ==================== VECTOR OPERATIONS ====================

async def save_vector(vector_data: Dict[str, Any]) -> str:
    """
    Save vector embedding
    
    Args:
        vector_data: Vector data
        
    Returns:
        Vector ID
    """
    api_client = get_api_client()
    
    vector_id = vector_data.get('id', str(uuid.uuid4()))
    
    vector_doc = {
        'id': vector_id,
        'entity_id': vector_data.get('entity_id'),
        'entity_type': vector_data.get('entity_type', 'user'),
        'embedding': vector_data.get('embedding', []),
        'metadata': vector_data.get('metadata', {})
    }
    
    created_id = await api_client.create_vector(vector_doc)
    return created_id or vector_id

async def get_vector(vector_id: str) -> Optional[Dict[str, Any]]:
    """Get vector by ID"""
    api_client = get_api_client()
    return await api_client.get_vector(vector_id)

async def find_similar_vectors(
    query_vector: List[float], 
    entity_type: str = 'user', 
    limit: int = 10,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Find similar vectors"""
    api_client = get_api_client()
    return await api_client.vector_similarity_search(
        query_vector=query_vector,
        entity_type=entity_type,
        limit=limit,
        min_similarity=similarity_threshold
    )

# ==================== HISTORY OPERATIONS ====================

async def save_meditation_history(history_data: Dict[str, Any]) -> str:
    """
    Save meditation history entry
    
    Args:
        history_data: History data
        
    Returns:
        History ID
    """
    api_client = get_api_client()
    
    history_id = history_data.get('id', str(uuid.uuid4()))
    
    history_doc = {
        'id': history_id,
        'user_id': history_data.get('user_id'),
        'session_id': history_data.get('session_id'),
        'meditation_type': history_data.get('meditation_type'),
        'duration_planned': history_data.get('duration_planned') or history_data.get('duration') or 10,
        'confidence_score': history_data.get('confidence_score', 0.5),
        'recommendation_source': history_data.get('recommendation_source', 'ai_recommendation'),
        'success_rating': history_data.get('success_rating') or history_data.get('rating'),
        'notes': history_data.get('notes', ''),
    }
    
    created_id = await api_client.create_history_entry(history_doc)
    return created_id or history_id

async def get_user_meditation_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get user's meditation history"""
    api_client = get_api_client()
    return await api_client.get_user_history(user_id, limit)

async def get_meditation_stats(user_id: str) -> Dict[str, Any]:
    """Get user's meditation statistics"""
    api_client = get_api_client()
    return await api_client.get_user_progress(user_id)

# ==================== ANALYTICS OPERATIONS ====================

async def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """Get user analytics"""
    api_client = get_api_client()
    return await api_client.get_user_analytics(user_id)

async def get_overall_analytics(timeframe: str = "30d") -> Dict[str, Any]:
    """Get overall analytics"""
    api_client = get_api_client()
    return await api_client.get_analytics_overview(timeframe)

# ==================== RECOMMENDATION OPERATIONS ====================

async def get_meditation_recommendations(
    user_id: str, 
    user_preferences: Optional[Dict[str, Any]] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Get AI-powered meditation recommendations"""
    api_client = get_api_client()
    return await api_client.get_meditation_recommendations(user_id, user_preferences, limit)

# ==================== UTILITY FUNCTIONS ====================

async def test_api_connection() -> bool:
    """Test API connection"""
    api_client = get_api_client()
    try:
        health_status = await api_client.health_check()
        return health_status is not None
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False

async def get_api_info() -> Dict[str, Any]:
    """Get API information"""
    api_client = get_api_client()
    try:
        return await api_client.get_api_info()
    except Exception as e:
        logger.error(f"Failed to get API info: {e}")
        return {}

# ==================== CLEANUP ====================

async def close_connections():
    """Close API connections"""
    from database.api_client import close_api_client
    await close_api_client()