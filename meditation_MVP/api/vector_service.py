import numpy as np
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib

from fastapi import HTTPException
from database.api_collections import (
    save_document, query_documents, 
    get_user, get_session, get_user_feedback
)

class VectorService:
    """Vector similarity service for personalized recommendations"""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.collection_name = 'vectors'
    
    async def create_user_embedding(self, user_id: str) -> str:
        """
        Create or update user embedding based on preferences, feedback, and session history
        
        Args:
            user_id: User ID
            
        Returns:
            Vector document ID
        """
        
        # Get user data
        user_data = await get_user(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's feedback history
        feedback_data = await get_user_feedback(user_id)
        
        # Get user's recent sessions
        sessions_data = await query_documents('sessions', 
                                            filters=[('user_id', '==', user_id)],
                                            limit=10)
        
        # Generate user embedding
        user_embedding = self._generate_user_embedding(user_data, feedback_data, sessions_data)
        
        # Calculate user success metrics
        success_rate = self._calculate_user_success_rate(feedback_data)
        
        # Save vector
        vector_id = str(uuid.uuid4())
        vector_doc = {
            'id': vector_id,
            'entity_id': user_id,
            'entity_type': 'user',
            'embedding': user_embedding.tolist(),
            'metadata': {
                'success_rate': success_rate,
                'session_count': len(sessions_data),
                'avg_rating': self._calculate_avg_rating(feedback_data)
            }
        }
        
        await save_document(self.collection_name, vector_id, vector_doc)
        return vector_id
    
    async def create_session_embedding(self, session_id: str) -> str:
        """
        Create embedding for a completed session
        
        Args:
            session_id: Session ID
            
        Returns:
            Vector document ID
        """
        
        # Get session data
        session_data = await get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_data.get('status') != 'completed':
            raise HTTPException(status_code=400, detail="Session not completed")
        
        # Generate session embedding
        session_embedding = self._generate_session_embedding(session_data)
        
        # Save vector
        vector_id = str(uuid.uuid4())
        vector_doc = {
            'id': vector_id,
            'entity_id': session_id,
            'entity_type': 'session',
            'embedding': session_embedding.tolist(),
            'metadata': {
                'dimension': 384,
                'version': '1.0'
            }
        }
        
        await save_document(self.collection_name, vector_id, vector_doc)
        return vector_id
    
    async def create_meditation_embeddings(self) -> List[str]:
        """
        Create embeddings for all meditation types for similarity search
        
        Returns:
            List of vector document IDs
        """
        
        # Load meditation types
        meditation_types = self._get_meditation_types()
        
        vector_ids = []
        for meditation_type, description in meditation_types.items():
            # Generate embedding for meditation type
            meditation_embedding = self._generate_meditation_embedding(meditation_type, description)
            
            vector_id = str(uuid.uuid4())
            vector_doc = {
                'id': vector_id,
                'entity_id': meditation_type,
                'entity_type': 'meditation',
                'embedding': meditation_embedding.tolist(),
                'metadata': {
                    'dimension': 384,
                    'version': '1.0'
                }
            }
            
            await save_document(self.collection_name, vector_id, vector_doc)
            vector_ids.append(vector_id)
        
        return vector_ids
    
    async def find_similar_users(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find users similar to given user based on preferences and success patterns
        
        Args:
            user_id: Target user ID
            limit: Number of similar users to return
            
        Returns:
            List of similar users with similarity scores
        """
        
        # Get target user's embedding
        target_vectors = await query_documents(self.collection_name,
                                             filters=[('entity_id', '==', user_id), 
                                                    ('entity_type', '==', 'user')])
        
        if not target_vectors:
            # Create user embedding if not exists
            await self.create_user_embedding(user_id)
            target_vectors = await query_documents(self.collection_name,
                                                 filters=[('entity_id', '==', user_id), 
                                                        ('entity_type', '==', 'user')])
        
        if not target_vectors:
            return []
        
        target_embedding = np.array(target_vectors[0]['embedding'])
        
        # Get all user vectors
        all_user_vectors = await query_documents(self.collection_name,
                                                filters=[('entity_type', '==', 'user')])
        
        similar_users = []
        for vector_doc in all_user_vectors:
            if vector_doc['entity_id'] == user_id:
                continue
            
            # Calculate similarity
            other_embedding = np.array(vector_doc['embedding'])
            similarity = self._cosine_similarity(target_embedding, other_embedding)
            
            similar_users.append({
                'user_id': vector_doc['entity_id'],
                'similarity': float(similarity),
                'metadata': vector_doc.get('metadata', {}),
                'success_rate': vector_doc.get('metadata', {}).get('success_rate', 0.0)
            })
        
        # Sort by similarity and return top results
        similar_users.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_users[:limit]
    
    async def find_similar_sessions(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find sessions similar to given session for recommendation enhancement
        
        Args:
            session_id: Target session ID
            limit: Number of similar sessions to return
            
        Returns:
            List of similar sessions with similarity scores
        """
        
        # Get target session's embedding
        target_vectors = await query_documents(self.collection_name,
                                             filters=[('entity_id', '==', session_id), 
                                                    ('entity_type', '==', 'session')])
        
        if not target_vectors:
            await self.create_session_embedding(session_id)
            target_vectors = await query_documents(self.collection_name,
                                                 filters=[('entity_id', '==', session_id), 
                                                        ('entity_type', '==', 'session')])
        
        if not target_vectors:
            return []
        
        target_embedding = np.array(target_vectors[0]['embedding'])
        
        # Get all session vectors
        all_session_vectors = await query_documents(self.collection_name,
                                                  filters=[('entity_type', '==', 'session')])
        
        similar_sessions = []
        for vector_doc in all_session_vectors:
            if vector_doc['entity_id'] == session_id:
                continue
            
            # Calculate similarity
            other_embedding = np.array(vector_doc['embedding'])
            similarity = self._cosine_similarity(target_embedding, other_embedding)
            
            similar_sessions.append({
                'session_id': vector_doc['entity_id'],
                'similarity': float(similarity),
                'metadata': vector_doc.get('metadata', {}),
                'recommendations': vector_doc.get('metadata', {}).get('recommendations', [])
            })
        
        # Sort by similarity
        similar_sessions.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_sessions[:limit]
    
    async def get_personalized_recommendations(self, user_id: str, base_recommendations: List[Dict]) -> List[Dict]:
        """
        Enhance base recommendations using vector similarity
        
        Args:
            user_id: User ID
            base_recommendations: Base recommendations from meditation service
            
        Returns:
            Enhanced recommendations with personalization scores
        """
        
        # Find similar users
        similar_users = await self.find_similar_users(user_id, limit=10)
        
        if not similar_users:
            return base_recommendations
        
        # Get successful meditation types from similar users
        successful_meditations = {}
        for similar_user in similar_users:
            success_rate = similar_user.get('success_rate', 0.0)
            similarity = similar_user.get('similarity', 0.0)
            
            # Weight by both similarity and success rate
            weight = similarity * success_rate
            
            # Get this user's preferences
            metadata = similar_user.get('metadata', {})
            preferences = metadata.get('preferences', {})
            favorite_meditations = preferences.get('favorite_meditations', [])
            
            for meditation in favorite_meditations:
                if meditation in successful_meditations:
                    successful_meditations[meditation] += weight
                else:
                    successful_meditations[meditation] = weight
        
        # Enhance base recommendations
        enhanced_recommendations = []
        for rec in base_recommendations:
            meditation_type = rec.get('meditation_type', '')
            
            # Boost confidence if similar users had success with this meditation
            personalization_boost = successful_meditations.get(meditation_type, 0.0)
            
            enhanced_rec = rec.copy()
            if personalization_boost > 0:
                # Apply boost (max 20% increase)
                boost_factor = 1.0 + min(0.2, personalization_boost * 0.1)
                enhanced_rec['confidence'] = min(0.95, rec['confidence'] * boost_factor)
                enhanced_rec['rationale'] += f" (Similar users found this effective)"
                enhanced_rec['personalization_score'] = float(personalization_boost)
            else:
                enhanced_rec['personalization_score'] = 0.0
            
            enhanced_recommendations.append(enhanced_rec)
        
        # Sort by enhanced confidence
        enhanced_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return enhanced_recommendations
    
    def _generate_user_embedding(self, user_data: Dict, feedback_data: List[Dict], sessions_data: List[Dict]) -> np.ndarray:
        """Generate embedding vector for a user based on their data"""
        
        embedding = np.zeros(self.embedding_dim, dtype=np.float32)
        
        # Encode preferences (first 128 dimensions)
        preferences = user_data.get('preferences', {})
        pref_embedding = self._encode_preferences(preferences)
        embedding[:len(pref_embedding)] = pref_embedding
        
        # Encode feedback patterns (next 128 dimensions)
        feedback_embedding = self._encode_feedback_history(feedback_data)
        start_idx = 128
        end_idx = start_idx + len(feedback_embedding)
        if end_idx <= self.embedding_dim:
            embedding[start_idx:end_idx] = feedback_embedding
        
        # Encode session patterns (remaining dimensions)
        session_embedding = self._encode_session_history(sessions_data)
        start_idx = 256
        end_idx = start_idx + len(session_embedding)
        if end_idx <= self.embedding_dim:
            embedding[start_idx:end_idx] = session_embedding
        
        return self._normalize_embedding(embedding)
    
    def _generate_session_embedding(self, session_data: Dict) -> np.ndarray:
        """Generate embedding vector for a session"""
        
        embedding = np.zeros(self.embedding_dim, dtype=np.float32)
        
        # Encode input data
        input_data = session_data.get('input_data', {})
        diary_text = input_data.get('diary_text', '')
        
        # Simple text encoding using hash
        if diary_text:
            text_embedding = self._encode_text(diary_text)
            embedding[:len(text_embedding)] = text_embedding
        
        # Encode recommendations
        results = session_data.get('results', {})
        recommendations = results.get('recommendations', [])
        
        if recommendations:
            rec_embedding = self._encode_recommendations(recommendations)
            start_idx = 192
            end_idx = start_idx + len(rec_embedding)
            if end_idx <= self.embedding_dim:
                embedding[start_idx:end_idx] = rec_embedding
        
        return self._normalize_embedding(embedding)
    
    def _generate_meditation_embedding(self, meditation_type: str, description: str) -> np.ndarray:
        """Generate embedding for a meditation type"""
        
        embedding = np.zeros(self.embedding_dim, dtype=np.float32)
        
        # Encode meditation name
        name_embedding = self._encode_text(meditation_type)
        embedding[:len(name_embedding)] = name_embedding
        
        # Encode description
        if description:
            desc_embedding = self._encode_text(description)
            start_idx = 192
            end_idx = start_idx + len(desc_embedding)
            if end_idx <= self.embedding_dim:
                embedding[start_idx:end_idx] = desc_embedding
        
        return self._normalize_embedding(embedding)
    
    def _encode_preferences(self, preferences: Dict) -> np.ndarray:
        """Encode user preferences into vector"""
        
        embedding = np.zeros(128, dtype=np.float32)
        
        # Encode categorical preferences
        favorite_meditations = preferences.get('favorite_meditations', [])
        for i, meditation in enumerate(favorite_meditations[:10]):  # Max 10
            hash_idx = self._hash_to_index(meditation, 64)
            embedding[hash_idx] += 1.0
        
        # Encode numeric preferences
        preferred_duration = preferences.get('preferred_duration', 10)
        embedding[64] = min(1.0, preferred_duration / 30.0)  # Normalize
        
        experience_level = preferences.get('experience_level', 'beginner')
        if experience_level == 'beginner':
            embedding[65] = 1.0
        elif experience_level == 'intermediate':
            embedding[66] = 1.0
        elif experience_level == 'advanced':
            embedding[67] = 1.0
        
        return embedding
    
    def _encode_feedback_history(self, feedback_data: List[Dict]) -> np.ndarray:
        """Encode user's feedback history"""
        
        embedding = np.zeros(128, dtype=np.float32)
        
        if not feedback_data:
            return embedding
        
        # Calculate average rating
        ratings = [f.get('rating', 3) for f in feedback_data]
        avg_rating = sum(ratings) / len(ratings) if ratings else 3.0
        embedding[0] = avg_rating / 5.0  # Normalize to 0-1
        
        # Encode meditation type preferences from feedback
        meditation_counts = {}
        for feedback in feedback_data:
            meditation_type = feedback.get('meditation_type', '')
            rating = feedback.get('rating', 3)
            if meditation_type:
                if meditation_type not in meditation_counts:
                    meditation_counts[meditation_type] = []
                meditation_counts[meditation_type].append(rating)
        
        # Encode top meditation preferences
        for i, (meditation, ratings) in enumerate(list(meditation_counts.items())[:10]):
            avg_rating = sum(ratings) / len(ratings)
            hash_idx = self._hash_to_index(meditation, 64) + 64
            if hash_idx < 128:
                embedding[hash_idx] = avg_rating / 5.0
        
        return embedding
    
    def _encode_session_history(self, sessions_data: List[Dict]) -> np.ndarray:
        """Encode user's session history patterns"""
        
        embedding = np.zeros(128, dtype=np.float32)
        
        if not sessions_data:
            return embedding
        
        # Session frequency
        embedding[0] = min(1.0, len(sessions_data) / 50.0)  # Normalize
        
        # Input type preferences
        text_sessions = sum(1 for s in sessions_data if s.get('input_type') == 'text')
        audio_sessions = sum(1 for s in sessions_data if s.get('input_type') == 'audio')
        
        total_sessions = len(sessions_data)
        if total_sessions > 0:
            embedding[1] = text_sessions / total_sessions
            embedding[2] = audio_sessions / total_sessions
        
        return embedding
    
    def _encode_text(self, text: str) -> np.ndarray:
        """Simple text encoding using hash"""
        
        embedding = np.zeros(192, dtype=np.float32)
        
        if not text:
            return embedding
        
        # Hash-based encoding
        words = text.lower().split()
        for word in words[:20]:  # Max 20 words
            hash_idx = self._hash_to_index(word, 192)
            embedding[hash_idx] += 1.0
        
        return embedding
    
    def _encode_recommendations(self, recommendations: List[Dict]) -> np.ndarray:
        """Encode recommendation patterns"""
        
        embedding = np.zeros(192, dtype=np.float32)
        
        for i, rec in enumerate(recommendations[:10]):  # Max 10 recs
            meditation_type = rec.get('meditation_type', '')
            confidence = rec.get('confidence', 0.0)
            
            hash_idx = self._hash_to_index(meditation_type, 96)
            embedding[hash_idx] = confidence
            
            # Encode confidence distribution
            conf_bucket = int(confidence * 10)  # 0-10 buckets
            if 96 + conf_bucket < 192:
                embedding[96 + conf_bucket] += 1.0
        
        return embedding
    
    def _hash_to_index(self, text: str, dim: int) -> int:
        """Convert text to hash index"""
        return int(hashlib.md5(text.encode()).hexdigest(), 16) % dim
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """L2 normalize embedding vector"""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    
    def _calculate_avg_rating(self, feedback_data: List[Dict]) -> float:
        """Calculate average rating from feedback"""
        if not feedback_data:
            return 0.0
        ratings = [f.get('rating', 0) for f in feedback_data if f.get('rating') is not None]
        return sum(ratings) / len(ratings) if ratings else 0.0

    def _calculate_user_success_rate(self, feedback_data: List[Dict]) -> float:
        """Calculate user success rate from feedback"""
        if not feedback_data:
            return 0.5  # Default neutral
        
        high_ratings = sum(1 for f in feedback_data if f.get('rating', 0) >= 4)
        return high_ratings / len(feedback_data)
    
    def _get_meditation_types(self) -> Dict[str, str]:
        """Get meditation types using valid API enum values as keys."""
        return {
            'mindfulness': 'Focus on present moment awareness',
            'body_scan': 'Systematically scan your body for tension',
            'breathing': 'Focus on natural breathing rhythm',
            'loving_kindness': 'Cultivate feelings of love and compassion',
            'zen': 'Seated meditation with focus on breath',
            'walking': 'Mindful walking practice',
            'guided_imagery': 'Guided imagery and mental visualization',
            'vipassana': 'Insight meditation observing sensations',
            'transcendental': 'Mantra-based transcendental practice',
            'movement': 'Mindful movement and body awareness',
            'sound_bath': 'Healing through sound vibrations',
            'mantra': 'Repetition of sacred sounds or phrases',
        }

    def _get_meditation_category(self, meditation_type: str) -> str:
        """meditation_type is already a valid API enum — category is unused in metadata."""
        return meditation_type

# Global service instance
vector_service = VectorService()