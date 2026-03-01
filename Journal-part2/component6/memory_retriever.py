# component6/memory_retriever.py (REPLACE EXISTING)
"""
Memory Retriever Module for Component 6.
Interfaces with Component 5 LSTM Memory Gates for context retrieval.
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

# Add project root to path to find component5_integration
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from shared.schemas import (
    MemoryContext, MemoryItem, UserProfile, ConversationContext
)
from shared.utils import (
    get_logger, log_execution_time, generate_correlation_id,
    calculate_memory_relevance, compress_memories, TokenCounter
)
from configu.settings import settings


class MemoryRetriever:
    """Retrieves and processes memory context from Component 5"""
    
    def __init__(self, component5_bridge):
        """Initialize memory retriever with Component 5 bridge"""
        self.logger = get_logger("memory_retriever")
        self.component5 = component5_bridge
        self.token_counter = TokenCounter()
        self.cache = {}
        
        # Performance tracking
        self.retrieval_times = []
        self.cache_hit_rate = 0.0
        self.total_requests = 0
        self.cache_hits = 0
        
        self.logger.info("Memory Retriever initialized with real Component 5")
    
    @log_execution_time
    async def get_memory_context(
        self,
        user_id: str,
        current_message: str,
        conversation_id: str,
        max_memories: int = 10,
        use_cache: bool = True
    ) -> MemoryContext:
        """Retrieve memory context from Component 5 LSTM gates"""
        correlation_id = generate_correlation_id()
        self.logger.info(f"Retrieving memory context for user {user_id}", extra={
            "correlation_id": correlation_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "max_memories": max_memories
        })
        
        start_time = datetime.utcnow()
        self.total_requests += 1
        
        try:
            # Check cache first
            cache_key = f"{user_id}_{conversation_id}_{hash(current_message)}"
            if use_cache and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if self._is_cache_valid(cached_result):
                    self.cache_hits += 1
                    self.cache_hit_rate = self.cache_hits / self.total_requests
                    self.logger.info(f"Cache hit for memory context", extra={
                        "correlation_id": correlation_id,
                        "cache_key": cache_key
                    })
                    return cached_result['memory_context']
            
            # Get memory context from Component 5 LSTM gates
            memory_context = await self.component5.get_memory_context(
                user_id=user_id,
                current_message=current_message,
                conversation_id=conversation_id,
                max_memories=max_memories
            )
            
            # Post-process and enhance context
            enhanced_context = await self._enhance_memory_context(
                memory_context, user_id, current_message
            )
            
            # Cache the result
            if use_cache:
                self.cache[cache_key] = {
                    'memory_context': enhanced_context,
                    'cached_at': datetime.utcnow(),
                    'ttl_minutes': 15
                }
                
                # Clean old cache entries
                await self._cleanup_cache()
            
            # Track performance
            retrieval_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.retrieval_times.append(retrieval_time)
            
            self.logger.info(f"Memory context retrieved successfully", extra={
                "correlation_id": correlation_id,
                "memories_count": len(enhanced_context.selected_memories),
                "retrieval_time_ms": retrieval_time,
                "token_usage": enhanced_context.token_usage
            })
            
            return enhanced_context
            
        except Exception as e:
            self.logger.error(f"Memory retrieval failed", extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "user_id": user_id
            })
            
            # Return empty context on error
            return MemoryContext(
                selected_memories=[],
                relevance_scores=[],
                token_usage=0,
                assembly_metadata={
                    'error': str(e),
                    'source': 'component5_lstm_error',
                    'fallback_used': True
                }
            )
    
    async def _enhance_memory_context(
        self,
        memory_context: MemoryContext,
        user_id: str,
        current_message: str
    ) -> MemoryContext:
        """Enhance memory context with additional Component 6 processing"""
        try:
            # Re-rank memories by relevance to current message
            enhanced_memories = []
            enhanced_relevance_scores = []
            
            for i, memory in enumerate(memory_context.selected_memories):
                # Calculate enhanced relevance using Component 6 logic
                enhanced_relevance = await self._calculate_enhanced_relevance(
                    memory, current_message, user_id
                )
                
                # Only include memories above threshold
                if enhanced_relevance > 0.2:
                    enhanced_memories.append(memory)
                    enhanced_relevance_scores.append(enhanced_relevance)
            
            # Sort by relevance (highest first)
            if enhanced_memories:
                sorted_pairs = sorted(
                    zip(enhanced_memories, enhanced_relevance_scores),
                    key=lambda x: x[1],
                    reverse=True
                )
                enhanced_memories, enhanced_relevance_scores = zip(*sorted_pairs)
                enhanced_memories = list(enhanced_memories)
                enhanced_relevance_scores = list(enhanced_relevance_scores)
            
            # Update token usage calculation
            total_tokens = sum(
                self.token_counter.count_tokens(mem.get('content_summary', ''))
                for mem in enhanced_memories
            )
            
            # Update metadata
            enhanced_metadata = {
                **memory_context.assembly_metadata,
                'component6_enhancement': True,
                'enhanced_relevance_applied': True,
                'memories_filtered': len(memory_context.selected_memories) - len(enhanced_memories),
                'final_token_count': total_tokens
            }
            
            return MemoryContext(
                selected_memories=enhanced_memories,
                relevance_scores=enhanced_relevance_scores,
                token_usage=total_tokens,
                assembly_metadata=enhanced_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error enhancing memory context: {e}")
            return memory_context  # Return original on error
    
    async def _calculate_enhanced_relevance(
        self,
        memory: Dict[str, Any],
        current_message: str,
        user_id: str
    ) -> float:
        """Calculate enhanced relevance using Component 6 algorithms"""
        try:
            # Base relevance from Component 5 output gate
            base_relevance = memory.get('gate_scores', {}).get('output', {}).get('score', 0.5)
            
            # Semantic similarity boost
            semantic_boost = calculate_memory_relevance(
                memory.get('content_summary', ''),
                current_message
            ) * 0.3
            
            # Temporal relevance boost
            created_at = memory.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                days_old = (datetime.utcnow() - created_at).days
                temporal_boost = max(0, (30 - days_old) / 30) * 0.2
            else:
                temporal_boost = 0.1
            
            # Emotional significance boost
            emotional_boost = memory.get('emotional_significance', 0.5) * 0.2
            
            # Access frequency boost
            access_freq = memory.get('access_frequency', 0)
            frequency_boost = min(access_freq / 10, 0.1) * 0.1
            
            # Memory type boost (prioritize certain types)
            memory_type = memory.get('memory_type', 'conversation')
            type_boost = {
                'event': 0.1,
                'emotion': 0.15,
                'insight': 0.1,
                'conversation': 0.05
            }.get(memory_type, 0.05)
            
            enhanced_relevance = (
                base_relevance + 
                semantic_boost + 
                temporal_boost + 
                emotional_boost + 
                frequency_boost + 
                type_boost
            )
            
            return min(1.0, max(0.0, enhanced_relevance))
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced relevance: {e}")
            return 0.5  # Default relevance
    
    def _is_cache_valid(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached memory context is still valid"""
        try:
            cached_at = cached_item.get('cached_at')
            ttl_minutes = cached_item.get('ttl_minutes', 15)
            
            if not cached_at:
                return False
            
            age_minutes = (datetime.utcnow() - cached_at).total_seconds() / 60
            return age_minutes < ttl_minutes
            
        except:
            return False
    
    async def _cleanup_cache(self):
        """Remove expired cache entries"""
        try:
            current_time = datetime.utcnow()
            expired_keys = []
            
            for key, cached_item in self.cache.items():
                if not self._is_cache_valid(cached_item):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            self.logger.error(f"Cache cleanup failed: {e}")
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a specific user"""
        try:
            keys_to_remove = [
                key for key in self.cache.keys() 
                if key.startswith(f"{user_id}_")
            ]
            
            for key in keys_to_remove:
                del self.cache[key]
            
            self.logger.info(f"Invalidated {len(keys_to_remove)} cache entries for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error invalidating user cache: {e}")
    
    def get_retrieval_statistics(self) -> Dict[str, Any]:
        """Get memory retrieval performance statistics"""
        avg_retrieval_time = (
            sum(self.retrieval_times) / len(self.retrieval_times)
            if self.retrieval_times else 0.0
        )
        
        return {
            "total_requests": self.total_requests,
            "cache_hit_rate": self.cache_hit_rate,
            "avg_retrieval_time_ms": avg_retrieval_time,
            "cache_size": len(self.cache),
            "recent_retrieval_times": self.retrieval_times[-10:] if self.retrieval_times else []
        }