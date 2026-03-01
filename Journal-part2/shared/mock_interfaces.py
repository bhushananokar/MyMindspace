"""
Mock interfaces for Component 5 and other dependencies.
Enables independent development and testing of Components 6 & 7.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
import json
from dataclasses import asdict

from .schemas import (
    MemoryContext, MemoryItem, UserProfile, CommunicationStyle,
    ResponseAnalysis, ConversationMetrics, ContextEffectiveness
)
from .utils import get_logger, generate_correlation_id


logger = get_logger("mock_interfaces")


class MockComponent5Interface:
    """Mock implementation of Component 5 LSTM Memory Gates"""
    
    def __init__(self):
        """Initialize mock Component 5 with sample data"""
        self.logger = get_logger("mock_component5")
        self.sample_memories = self._generate_sample_memories()
        self.user_profiles = self._generate_sample_user_profiles()
        
        self.logger.info("Mock Component 5 initialized with sample data")
    
    async def get_memory_context(
        self,
        user_id: str,
        current_message: str,
        conversation_id: str,
        max_memories: int = 10
    ) -> MemoryContext:
        """Mock memory context retrieval from Component 5"""
        self.logger.info(f"Retrieving memory context for user {user_id}")
        
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Get user's memories
        user_memories = self.sample_memories.get(user_id, [])
        
        # Calculate relevance scores based on current message
        relevant_memories = []
        relevance_scores = []
        
        for memory in user_memories[:max_memories * 2]:
            relevance = self._calculate_mock_relevance(memory, current_message)
            if relevance > 0.1:
                relevant_memories.append(memory)
                relevance_scores.append(relevance)
        
        # Sort by relevance and take top memories
        sorted_pairs = sorted(zip(relevant_memories, relevance_scores), 
                             key=lambda x: x[1], reverse=True)
        
        if sorted_pairs:
            memories, scores = zip(*sorted_pairs[:max_memories])
            relevant_memories = list(memories)
            relevance_scores = list(scores)
        else:
            relevant_memories = []
            relevance_scores = []
        
        # Calculate token usage
        token_usage = sum(len(str(memory)) // 4 for memory in relevant_memories)
        
        # Generate assembly metadata
        assembly_metadata = {
            "retrieval_time_ms": random.randint(50, 150),
            "total_memories_considered": len(user_memories),
            "filtering_criteria": "relevance_score > 0.1",
            "compression_applied": False,
            "cache_hit": random.choice([True, False])
        }
        
        return MemoryContext(
            selected_memories=relevant_memories,
            relevance_scores=relevance_scores,
            token_usage=token_usage,
            assembly_metadata=assembly_metadata
        )
    
    async def update_memory_access(
        self,
        memory_id: str,
        user_id: str,
        access_type: str = "conversation_reference"
    ) -> bool:
        """Mock memory access update"""
        self.logger.info(f"Updating memory access: {memory_id} for user {user_id}")
        
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        # Find and update memory
        for memory in self.sample_memories.get(user_id, []):
            if memory.get('id') == memory_id:
                memory['access_frequency'] = memory.get('access_frequency', 0) + 1
                memory['last_accessed'] = datetime.utcnow()
                return True
        
        return False
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Mock user profile retrieval"""
        self.logger.info(f"Retrieving user profile for {user_id}")
        
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.02, 0.08))
        
        return self.user_profiles.get(user_id)
    
    def _generate_sample_memories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate sample memory data for testing"""
        sample_memories = {}
        
        # Generate memories for multiple users
        for user_id in ["user_001", "user_002", "user_003"]:
            user_memories = []
            
            # Generate different types of memories
            memory_types = ["conversation", "event", "emotion", "insight"]
            
            for i in range(random.randint(15, 25)):
                memory_type = random.choice(memory_types)
                
                memory = {
                    "id": f"memory_{user_id}_{i:03d}",
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "content_summary": self._generate_memory_content(memory_type, i),
                    "original_entry_id": f"entry_{user_id}_{i:03d}",
                    "importance_score": random.uniform(0.3, 1.0),
                    "emotional_significance": random.uniform(0.2, 1.0),
                    "temporal_relevance": random.uniform(0.1, 1.0),
                    "gate_scores": {
                        "forget_score": random.uniform(0.0, 0.8),
                        "input_score": random.uniform(0.4, 1.0),
                        "output_score": random.uniform(0.3, 1.0),
                        "confidence": random.uniform(0.6, 1.0)
                    },
                    "feature_vector": [random.uniform(-1, 1) for _ in range(90)],
                    "relationships": [f"memory_{user_id}_{j:03d}" for j in range(max(0, i-2), i)],
                    "context_needed": {
                        "emotional_state": random.choice(["happy", "sad", "neutral", "excited", "anxious"]),
                        "current_topic": random.choice(["work", "relationships", "health", "goals", "hobbies"]),
                        "stress_level": random.randint(1, 10)
                    },
                    "retrieval_triggers": self._generate_retrieval_triggers(memory_type),
                    "access_frequency": random.randint(0, 15),
                    "last_accessed": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 90))
                }
                
                user_memories.append(memory)
            
            sample_memories[user_id] = user_memories
        
        return sample_memories
    
    def _generate_memory_content(self, memory_type: str, index: int) -> str:
        """Generate realistic memory content based on type"""
        if memory_type == "conversation":
            topics = ["work stress", "relationship advice", "personal goals", "health concerns", "hobby discussion"]
            topic = random.choice(topics)
            return f"Had a meaningful conversation about {topic}. Felt {random.choice(['understood', 'supported', 'challenged', 'inspired'])}."
        
        elif memory_type == "event":
            events = ["job interview", "family gathering", "work presentation", "vacation planning", "medical appointment"]
            event = random.choice(events)
            return f"Experienced {event}. Outcome was {random.choice(['successful', 'challenging', 'surprising', 'expected'])}."
        
        elif memory_type == "emotion":
            emotions = ["overwhelmed", "grateful", "frustrated", "excited", "anxious", "proud"]
            emotion = random.choice(emotions)
            trigger = random.choice(["work deadline", "family news", "personal achievement", "health update"])
            return f"Felt {emotion} due to {trigger}. Coping strategy was {random.choice(['exercise', 'talking to friends', 'meditation', 'work'])}."
        
        else:  # insight
            insights = ["work-life balance", "communication patterns", "personal boundaries", "goal setting", "stress management"]
            insight = random.choice(insights)
            return f"Realized importance of {insight}. Planning to {random.choice(['implement changes', 'discuss with others', 'research more', 'set reminders'])}."
    
    def _generate_retrieval_triggers(self, memory_type: str) -> List[str]:
        """Generate relevant retrieval triggers for memory type"""
        if memory_type == "conversation":
            return random.sample(["communication", "relationships", "advice", "support", "listening"], 3)
        elif memory_type == "event":
            return random.sample(["milestone", "achievement", "challenge", "celebration", "learning"], 3)
        elif memory_type == "emotion":
            return random.sample(["feelings", "coping", "stress", "wellness", "self-care"], 3)
        else:  # insight
            return random.sample(["growth", "reflection", "learning", "change", "awareness"], 3)
    
    def _generate_sample_user_profiles(self) -> Dict[str, UserProfile]:
        """Generate sample user profiles for testing"""
        profiles = {}
        
        communication_styles = list(CommunicationStyle)
        
        for user_id in ["user_001", "user_002", "user_003"]:
            profile = UserProfile(
                user_id=user_id,
                communication_style=random.choice(communication_styles),
                preferred_response_length=random.choice(["brief", "moderate", "detailed"]),
                emotional_matching=random.choice([True, False]),
                cultural_context=random.choice([None, "US", "European", "Asian", "Latin American"]),
                humor_preference=random.uniform(0.2, 0.8),
                formality_level=random.uniform(0.3, 0.9),
                conversation_depth=random.uniform(0.5, 0.9),
                proactive_engagement=random.choice([True, False])
            )
            profiles[user_id] = profile
        
        return profiles
    
    def _calculate_mock_relevance(self, memory: Dict[str, Any], current_message: str) -> float:
        """Calculate mock relevance score between memory and current message"""
        # Simple keyword matching for mock purposes
        message_words = set(current_message.lower().split())
        memory_words = set(memory.get('content_summary', '').lower().split())
        
        if not message_words or not memory_words:
            return 0.0
        
        # Calculate simple overlap
        overlap = len(message_words & memory_words)
        total = len(message_words | memory_words)
        
        base_relevance = overlap / total if total > 0 else 0.0
        
        # Add some randomness and metadata factors
        importance_boost = memory.get('importance_score', 0.5) * 0.3
        emotional_boost = memory.get('emotional_significance', 0.5) * 0.2
        recency_boost = max(0, (30 - (datetime.utcnow() - memory.get('created_at', datetime.utcnow())).days) / 30) * 0.1
        
        final_relevance = base_relevance + importance_boost + emotional_boost + recency_boost
        return min(1.0, max(0.0, final_relevance))


def create_mock_interfaces() -> Dict[str, Any]:
    """Create and return all mock interfaces for development"""
    return {
        "component5": MockComponent5Interface(),
    }
