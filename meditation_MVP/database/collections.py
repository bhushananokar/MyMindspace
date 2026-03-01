from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import uuid

from firebase_admin import firestore
from database.firebase_client import get_db

# ==================== GENERIC CRUD OPERATIONS ====================

async def get_collection(collection_name: str) -> firestore.CollectionReference:
    """Get a Firestore collection reference"""
    db = get_db()
    return db.collection(collection_name)

async def save_document(collection_name: str, doc_id: str, data: Dict[str, Any]) -> str:
    """
    Save a document to Firestore collection
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        data: Document data
        
    Returns:
        Document ID
    """
    db = get_db()
    
    # Add timestamp if not present
    if 'created_at' not in data:
        data['created_at'] = firestore.SERVER_TIMESTAMP
    
    # Update timestamp
    data['updated_at'] = firestore.SERVER_TIMESTAMP
    
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.set(data)
    
    return doc_id

async def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a document from Firestore collection
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        
    Returns:
        Document data or None if not found
    """
    db = get_db()
    doc_ref = db.collection(collection_name).document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    
    return None

async def update_document(collection_name: str, doc_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update a document in Firestore collection
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        updates: Fields to update
        
    Returns:
        True if successful
    """
    db = get_db()
    
    # Add update timestamp
    updates['updated_at'] = firestore.SERVER_TIMESTAMP
    
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.update(updates)
    
    return True

async def delete_document(collection_name: str, doc_id: str) -> bool:
    """
    Delete a document from Firestore collection
    
    Args:
        collection_name: Name of the collection
        doc_id: Document ID
        
    Returns:
        True if successful
    """
    db = get_db()
    doc_ref = db.collection(collection_name).document(doc_id)
    doc_ref.delete()
    
    return True

async def query_documents(
    collection_name: str,
    filters: Optional[List[Tuple[str, str, Any]]] = None,
    order_by: Optional[Tuple[str, str]] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Query documents from Firestore collection
    
    Args:
        collection_name: Name of the collection
        filters: List of (field, operator, value) tuples
        order_by: (field, direction) tuple for sorting
        limit: Maximum number of documents to return
        
    Returns:
        List of documents
    """
    db = get_db()
    query = db.collection(collection_name)
    
    # Apply filters
    if filters:
        for field, operator, value in filters:
            query = query.where(field, operator, value)
    
    # Apply ordering
    if order_by:
        field, direction = order_by
        direction_enum = firestore.Query.DESCENDING if direction.lower() == 'desc' else firestore.Query.ASCENDING
        query = query.order_by(field, direction=direction_enum)
    
    # Apply limit
    if limit:
        query = query.limit(limit)
    
    # Execute query
    docs = query.stream()
    
    results = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        results.append(data)
    
    return results

# ==================== USER OPERATIONS ====================

async def create_user(user_data: Dict[str, Any]) -> str:
    """
    Create a new user
    
    Args:
        user_data: User data
        
    Returns:
        User ID
    """
    user_id = user_data.get('id', str(uuid.uuid4()))
    
    user_doc = {
        'id': user_id,
        'name': user_data.get('name', ''),
        'email': user_data.get('email'),
        'preferences': user_data.get('preferences', {}),
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    await save_document('users', user_id, user_doc)
    return user_id

async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    return await get_document('users', user_id)

async def update_user(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user data"""
    return await update_document('users', user_id, updates)

async def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> bool:
    """Update user preferences"""
    return await update_document('users', user_id, {'preferences': preferences})

# ==================== SESSION OPERATIONS ====================

async def save_session(session_data: Dict[str, Any]) -> str:
    """
    Save a processing session
    
    Args:
        session_data: Session data
        
    Returns:
        Session ID
    """
    session_id = session_data.get('id', str(uuid.uuid4()))
    
    session_doc = {
        'id': session_id,
        'user_id': session_data.get('user_id'),
        'status': session_data.get('status', 'processing'),
        'input_type': session_data.get('input_type'),
        'input_data': session_data.get('input_data', {}),
        'results': session_data.get('results', {}),
        'error': session_data.get('error'),
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    await save_document('sessions', session_id, session_doc)
    return session_id

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID"""
    return await get_document('sessions', session_id)

async def update_session(session_id: str, updates: Dict[str, Any]) -> bool:
    """Update session data"""
    # Add completion timestamp if status is completed
    if updates.get('status') == 'completed' and 'completed_at' not in updates:
        updates['completed_at'] = firestore.SERVER_TIMESTAMP
    
    return await update_document('sessions', session_id, updates)

async def get_user_sessions(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's recent sessions"""
    return await query_documents(
        'sessions',
        filters=[('user_id', '==', user_id)],
        order_by=('created_at', 'desc'),
        limit=limit
    )

async def get_sessions_by_status(status: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get sessions by status"""
    return await query_documents(
        'sessions',
        filters=[('status', '==', status)],
        order_by=('created_at', 'desc'),
        limit=limit
    )

# ==================== FEEDBACK OPERATIONS ====================

async def save_feedback(feedback_data: Dict[str, Any]) -> str:
    """
    Save user feedback
    
    Args:
        feedback_data: Feedback data
        
    Returns:
        Feedback ID
    """
    feedback_id = str(uuid.uuid4())
    
    feedback_doc = {
        'id': feedback_id,
        'user_id': feedback_data.get('user_id'),
        'session_id': feedback_data.get('session_id'),
        'meditation_type': feedback_data.get('meditation_type'),
        'rating': feedback_data.get('rating'),
        'comment': feedback_data.get('comment'),
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    await save_document('feedback', feedback_id, feedback_doc)
    
    # Also update user preferences based on feedback
    await _update_user_preferences_from_feedback(feedback_data)
    
    return feedback_id

async def get_feedback(feedback_id: str) -> Optional[Dict[str, Any]]:
    """Get feedback by ID"""
    return await get_document('feedback', feedback_id)

async def get_feedback_for_user(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get feedback for a specific user"""
    return await query_documents(
        'feedback',
        filters=[('user_id', '==', user_id)],
        order_by=('created_at', 'desc'),
        limit=limit
    )

async def get_feedback_for_session(session_id: str) -> List[Dict[str, Any]]:
    """Get feedback for a specific session"""
    return await query_documents(
        'feedback',
        filters=[('session_id', '==', session_id)]
    )

async def get_feedback_for_meditation_type(meditation_type: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get feedback for a specific meditation type"""
    return await query_documents(
        'feedback',
        filters=[('meditation_type', '==', meditation_type)],
        order_by=('created_at', 'desc'),
        limit=limit
    )

async def _update_user_preferences_from_feedback(feedback_data: Dict[str, Any]) -> None:
    """Update user preferences based on feedback"""
    user_id = feedback_data.get('user_id')
    meditation_type = feedback_data.get('meditation_type')
    rating = feedback_data.get('rating', 3)
    
    if not user_id or not meditation_type:
        return
    
    # Get current user
    user = await get_user(user_id)
    if not user:
        return
    
    # Update preferences
    preferences = user.get('preferences', {})
    favorite_meditations = preferences.get('favorite_meditations', [])
    
    # Add to favorites if high rating and not already in list
    if rating >= 4 and meditation_type not in favorite_meditations:
        favorite_meditations.append(meditation_type)
        # Keep only top 10 favorites
        if len(favorite_meditations) > 10:
            favorite_meditations = favorite_meditations[-10:]
        
        preferences['favorite_meditations'] = favorite_meditations
        await update_user_preferences(user_id, preferences)

# ==================== VECTOR OPERATIONS ====================

async def save_vector(vector_data: Dict[str, Any]) -> str:
    """
    Save vector embedding
    
    Args:
        vector_data: Vector data
        
    Returns:
        Vector ID
    """
    vector_id = vector_data.get('id', str(uuid.uuid4()))
    
    vector_doc = {
        'id': vector_id,
        'entity_id': vector_data.get('entity_id'),
        'entity_type': vector_data.get('entity_type'),
        'embedding': vector_data.get('embedding'),
        'metadata': vector_data.get('metadata', {}),
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    await save_document('vectors', vector_id, vector_doc)
    return vector_id

async def get_vectors_by_entity(entity_id: str, entity_type: str) -> List[Dict[str, Any]]:
    """Get vectors for a specific entity"""
    return await query_documents(
        'vectors',
        filters=[
            ('entity_id', '==', entity_id),
            ('entity_type', '==', entity_type)
        ]
    )

async def get_vectors_by_type(entity_type: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get all vectors of a specific type"""
    return await query_documents(
        'vectors',
        filters=[('entity_type', '==', entity_type)],
        limit=limit
    )

# ==================== MEDITATION HISTORY OPERATIONS ====================

async def save_meditation_history(history_data: Dict[str, Any]) -> str:
    """
    Save meditation session to history
    
    Args:
        history_data: History data
        
    Returns:
        History ID
    """
    history_id = str(uuid.uuid4())
    
    history_doc = {
        'id': history_id,
        'user_id': history_data.get('user_id'),
        'session_id': history_data.get('session_id'),
        'meditation_type': history_data.get('meditation_type'),
        'confidence_score': history_data.get('confidence_score', 0.0),
        'success_rating': history_data.get('success_rating'),  # From feedback
        'duration_minutes': history_data.get('duration_minutes'),
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    await save_document('meditation_history', history_id, history_doc)
    return history_id

async def get_user_meditation_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get user's meditation history"""
    return await query_documents(
        'meditation_history',
        filters=[('user_id', '==', user_id)],
        order_by=('created_at', 'desc'),
        limit=limit
    )

async def get_successful_meditations_for_user(user_id: str, min_rating: int = 4) -> List[Dict[str, Any]]:
    """Get successful meditations for a user"""
    return await query_documents(
        'meditation_history',
        filters=[
            ('user_id', '==', user_id),
            ('success_rating', '>=', min_rating)
        ],
        order_by=('created_at', 'desc')
    )

# ==================== ANALYTICS & STATS ====================

async def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get user statistics"""
    
    # Get session count
    sessions = await get_user_sessions(user_id, limit=1000)
    session_count = len(sessions)
    
    # Get feedback stats
    feedback = await get_feedback_for_user(user_id, limit=1000)
    feedback_count = len(feedback)
    
    avg_rating = 0.0
    if feedback:
        avg_rating = sum(f.get('rating', 0) for f in feedback) / len(feedback)
    
    # Get meditation history stats
    history = await get_user_meditation_history(user_id, limit=1000)
    
    # Calculate favorite meditations
    meditation_counts = {}
    for h in history:
        med_type = h.get('meditation_type', '')
        if med_type:
            meditation_counts[med_type] = meditation_counts.get(med_type, 0) + 1
    
    top_meditations = sorted(meditation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'user_id': user_id,
        'total_sessions': session_count,
        'total_feedback': feedback_count,
        'average_rating': avg_rating,
        'meditation_count': len(history),
        'favorite_meditations': [m[0] for m in top_meditations],
        'meditation_stats': dict(top_meditations)
    }

async def get_system_stats() -> Dict[str, Any]:
    """Get system-wide statistics"""
    
    # Count documents in each collection
    users_count = len(await query_documents('users', limit=10000))
    sessions_count = len(await query_documents('sessions', limit=10000))
    feedback_count = len(await query_documents('feedback', limit=10000))
    
    # Get recent activity
    recent_sessions = await query_documents('sessions', 
                                          order_by=('created_at', 'desc'), 
                                          limit=10)
    
    recent_feedback = await query_documents('feedback',
                                          order_by=('created_at', 'desc'),
                                          limit=10)
    
    return {
        'total_users': users_count,
        'total_sessions': sessions_count,
        'total_feedback': feedback_count,
        'recent_sessions': len(recent_sessions),
        'recent_feedback': len(recent_feedback),
        'last_updated': datetime.utcnow().isoformat()
    }