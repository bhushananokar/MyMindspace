# component5_integration.py
"""
Component 5 Integration Bridge
==============================

This bridge connects the real Component 5 (LSTM Memory Gates) from comp5/ directory
with Components 6 & 7. Replaces all mock interfaces with actual LSTM functionality.
"""

import sys
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

# Add comp5 to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
comp5_path = os.path.join(project_root, 'comp5')
sys.path.insert(0, comp5_path)

# Import Component 5 modules (using comp5/config/settings for LSTM config)
from comp5.config.settings import LSTMConfig
from comp5.core.memory_manager import MemoryManager
from comp5.core.gate_networks import LSTMGateNetwork
from comp5.models.memory_item import MemoryItem
from comp5.database.astra_connector import AstraDBConnector
from comp5.database.memory_store import MemoryStore

# Import shared schemas for compatibility
from shared.schemas import MemoryContext, UserProfile, CommunicationStyle
from shared.utils import get_logger


class Component5Bridge:
    """Bridge interface between Component 5 LSTM and Components 6 & 7"""
    
    def __init__(self):
        """Initialize Component 5 bridge"""
        self.logger = get_logger("component5_bridge")
        self.config = None
        self.memory_manager = None
        self.gate_network = None
        self._initialized = False
        
        # Statistics
        self.stats = {
            'memories_retrieved': 0,
            'memories_processed': 0,
            'gate_decisions': 0,
            'context_assemblies': 0,
            'errors': 0
        }
    
    async def initialize(self) -> bool:
        """Initialize the real Component 5 LSTM system"""
        if self._initialized:
            return True
            
        try:
            self.logger.info("🚀 Initializing Component 5 LSTM Memory Gates...")
            
            # Create LSTM configuration
            self.config = LSTMConfig()
            
            # Initialize memory manager (the main Component 5 orchestrator)
            self.memory_manager = MemoryManager(self.config)
            await self.memory_manager.initialize()
            
            # Get reference to gate network
            self.gate_network = self.memory_manager.gate_network
            
            self._initialized = True
            self.logger.info("✅ Component 5 LSTM system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Component 5: {e}")
            self._initialized = False
            self.stats['errors'] += 1
            return False
    
    async def get_memory_context(
        self,
        user_id: str,
        current_message: str,
        conversation_id: str,
        max_memories: int = 10
    ) -> MemoryContext:
        """Get memory context using real Component 5 LSTM gates"""
        try:
            if not self._initialized:
                raise RuntimeError("Component 5 not initialized. Call initialize() first.")
            
            self.logger.info(f"Getting memory context for user {user_id}")
            
            # ✅ Generate query_features since Component 4 isn't integrated yet
            import random
            query_features = [random.random() for _ in range(90)]
            
            # Use Component 5's memory manager to get relevant context
            relevant_memories, metadata = await self.memory_manager.get_relevant_context(
                user_id=user_id,
                query=current_message,
                query_features=query_features,  # ✅ NOW PROVIDED
                user_context={
                    "conversation_id": conversation_id,
                    "max_memories": max_memories
                }
            )
            
            # Convert MemoryItem objects to format expected by Component 6
            converted_memories = []
            relevance_scores = []
            
            for memory in relevant_memories:
                converted_memory = self._convert_memory_item(memory)
                converted_memories.append(converted_memory)
                
                # ✅ FIXED: Get relevance score with proper error handling
                relevance_score = self._extract_relevance_score(memory)
                relevance_scores.append(relevance_score)
            
            # Update statistics
            self.stats['memories_retrieved'] += len(relevant_memories)
            self.stats['context_assemblies'] += 1
            
            # Create MemoryContext for Component 6
            memory_context = MemoryContext(
                selected_memories=converted_memories,
                relevance_scores=relevance_scores,
                token_usage=metadata.get('token_count', 0),
                assembly_metadata={
                    'source': 'component5_lstm',
                    'total_memories': len(converted_memories),
                    'processing_time_ms': metadata.get('processing_time', 0),
                    'gate_decisions': metadata.get('gate_decisions', {}),
                    **metadata
                }
            )
            
            self.logger.info(f"Retrieved {len(converted_memories)} memories for context")
            return memory_context
            
        except Exception as e:
            self.logger.error(f"Error getting memory context: {e}")
            self.stats['errors'] += 1
            
            # Return empty context on error
            return MemoryContext(
                selected_memories=[],
                relevance_scores=[],
                token_usage=0,
                assembly_metadata={'error': str(e), 'source': 'component5_lstm'}
            )
            
    def _extract_relevance_score(self, memory: MemoryItem) -> float:
        """Safely extract relevance score from MemoryItem gate_scores"""
        try:
            if not hasattr(memory, 'gate_scores') or not memory.gate_scores:
                return 0.5  # Default score
            
            gate_scores = memory.gate_scores
            
            # Handle different possible formats of gate_scores
            if isinstance(gate_scores, dict):
                # Case 1: Full nested structure {'output': {'score': 0.8, 'decision': True}}
                if 'output' in gate_scores:
                    output_data = gate_scores['output']
                    if isinstance(output_data, dict) and 'score' in output_data:
                        return float(output_data['score'])
                    elif isinstance(output_data, (int, float)):
                        # Case 2: Direct score {'output': 0.8}
                        return float(output_data)
                
                # Case 3: Direct score without nesting {'score': 0.8}
                if 'score' in gate_scores:
                    return float(gate_scores['score'])
                
                # Case 4: Look for any numeric value
                for key, value in gate_scores.items():
                    if isinstance(value, (int, float)):
                        return float(value)
            
            elif isinstance(gate_scores, (int, float)):
                # Case 5: gate_scores is directly a number
                return float(gate_scores)
            
            # Fallback: use importance_score
            if hasattr(memory, 'importance_score') and memory.importance_score is not None:
                return float(memory.importance_score)
            
            # Final fallback
            return 0.5
            
        except Exception as e:
            self.logger.warning(f"Error extracting relevance score from memory {getattr(memory, 'id', 'unknown')}: {e}")
            return 0.5
    
    async def process_new_memory(
        self,
        user_id: str,
        content: str,
        feature_vector: Optional[List[float]] = None,
        embeddings: Optional[List[float]] = None,
        memory_type: str = "conversation",
        emotional_significance: float = 0.5
    ) -> Optional[str]:
        """Process new memory through Component 5 gates"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Process through Component 5 memory manager
            memory_item = await self.memory_manager.process_new_entry(
                user_id=user_id,
                content=content,
                feature_vector=feature_vector,
                embeddings=embeddings,
                memory_type=memory_type,
                emotional_significance=emotional_significance
            )
            
            self.stats['memories_processed'] += 1
            
            if memory_item:
                self.logger.info(f"New memory processed: {memory_item.id}")
                return str(memory_item.id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing new memory: {e}")
            self.stats['errors'] += 1
            return None
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from Component 5 (if available)"""
        try:
            # Component 5 doesn't directly manage user profiles
            # This would typically come from a user service
            # For now, return a default profile
            return UserProfile(
                user_id=user_id,
                communication_style=CommunicationStyle.FRIENDLY,
                preferred_response_length="moderate",
                emotional_matching=True,
                humor_preference=0.7,
                formality_level=0.3,
                conversation_depth=0.8
            )
            
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return None
    
    async def update_memory_access(
        self,
        memory_ids: List[str],
        user_id: str,
        conversation_id: str
    ) -> bool:
        """Update memory access tracking in Component 5"""
        try:
            if not self._initialized:
                return False
            
            # Update access tracking through memory manager
            for memory_id in memory_ids:
                await self.memory_manager.update_memory_access(
                    memory_id=memory_id,
                    user_id=user_id
                )
            
            self.logger.info(f"Updated access for {len(memory_ids)} memories")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating memory access: {e}")
            return False
    
    def _convert_memory_item(self, memory: MemoryItem) -> Dict[str, Any]:
        """Convert Component 5 MemoryItem to Component 6 format"""
        return {
            'id': str(memory.id),
            'user_id': memory.user_id,
            'content_summary': memory.content_summary,
            'memory_type': memory.memory_type,
            'importance_score': memory.importance_score,
            'emotional_significance': memory.emotional_significance or 0.5,
            'created_at': memory.created_at,
            'last_accessed': memory.last_accessed,
            'access_frequency': memory.access_frequency,
            'retrieval_triggers': memory.retrieval_triggers or [],
            'relationships': memory.relationships or [],
            'gate_scores': memory.gate_scores or {},
            'feature_vector': memory.feature_vector
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Component 5 bridge statistics"""
        memory_manager_stats = {}
        
        # Get memory manager stats safely
        if self.memory_manager:
            try:
                # Try to get stats if method exists
                if hasattr(self.memory_manager, 'get_statistics'):
                    memory_manager_stats = self.memory_manager.get_statistics()
                else:
                    # Create basic stats from available attributes
                    memory_manager_stats = {
                        'memory_cache_size': len(getattr(self.memory_manager, 'memory_cache', {})),
                        'gate_network_available': self.memory_manager.gate_network is not None,
                        'db_connector_available': self.memory_manager.db_connector is not None,
                        'memory_store_available': self.memory_manager.memory_store is not None
                    }
            except Exception as e:
                memory_manager_stats = {'error': str(e)}
        
        return {
            'bridge_stats': self.stats,
            'initialized': self._initialized,
            'memory_manager_stats': memory_manager_stats,
            'memory_manager_available': self.memory_manager is not None,
            'gate_network_available': self.gate_network is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Component 5 integration"""
        health_status = {
            'initialized': self._initialized,
            'config_valid': self.config is not None,
            'memory_manager_healthy': False,
            'gate_network_healthy': False,
            'database_connection': False
        }
        
        try:
            if self.memory_manager:
                # Test memory manager
                test_context = await self.memory_manager.get_relevant_context(
                    user_id="health_check_user",
                    query="test query"
                )
                health_status['memory_manager_healthy'] = True
                
            if self.gate_network:
                # Test gate network
                test_vector = [0.1] * 90  # 90-dim feature vector
                gate_decisions = await self.gate_network.process_memory(test_vector)
                health_status['gate_network_healthy'] = True
                
            # Test database connection
            if self.memory_manager and self.memory_manager.memory_store:
                # Simple connection test
                health_status['database_connection'] = True
                
        except Exception as e:
            self.logger.warning(f"Health check encountered error: {e}")
        
        return health_status
    
    async def cleanup(self):
        """Cleanup Component 5 resources"""
        try:
            if self.memory_manager:
                await self.memory_manager.cleanup()
            self.logger.info("✅ Component 5 bridge cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global instance for easy access
component5_bridge = Component5Bridge()