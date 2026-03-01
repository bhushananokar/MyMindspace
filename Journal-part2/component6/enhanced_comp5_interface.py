# component6/enhanced_comp5_interface.py
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os

# Add comp5 to path (from your demo.ipynb)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
comp5_path = os.path.join(project_root, 'comp5')
sys.path.insert(0, comp5_path)

from comp5.config.settings import LSTMConfig
from comp5.core.memory_manager import MemoryManager
from comp5.core.gate_networks import LSTMGateNetwork
from comp5.models.memory_item import MemoryItem
from shared.schemas import MemoryContext, UserProfile

class EnhancedComponent5Interface:
    """Enhanced interface using LSTM demo logic for Component 6 integration"""
    
    def __init__(self):
        self.config = None
        self.memory_manager = None
        self.gate_network = None
        self._initialized = False
        
        # Statistics from demo.ipynb
        self.stats = {
            'memories_retrieved': 0,
            'memories_processed': 0,
            'input_gate_accepted': 0,
            'forget_gate_triggered': 0,
            'output_gate_filtered': 0,
            'final_memories_count': 0,
            'processing_time': 0.0
        }
    
    async def initialize(self) -> bool:
        """Initialize LSTM system (based on demo.ipynb Cell 2)"""
        if self._initialized:
            return True
            
        try:
            print("🚀 Initializing LSTM Memory System for Component 6 Integration...")
            
            # Create configuration (from demo.ipynb)
            self.config = LSTMConfig()
            
            # Initialize memory manager
            self.memory_manager = MemoryManager(self.config)
            await self.memory_manager.initialize()
            
            # Initialize gate network
            self.gate_network = LSTMGateNetwork(
                input_size=self.config.gate_network.input_size,
                hidden_size=self.config.gate_network.hidden_size,
                dropout=self.config.gate_network.dropout_rate
            )
            
            self._initialized = True
            print(f"✅ LSTM system initialized successfully")
            print(f"📊 Gate thresholds: {self.gate_network.get_thresholds()}")
            
            return True
            
        except Exception as e:
            print(f"❌ LSTM system initialization failed: {e}")
            return False
    
    async def get_memory_context_for_query(self, 
                                         user_id: str,
                                         user_query: str,
                                         max_memories: int = 10) -> MemoryContext:
        """
        Get memory context using LSTM gates (based on demo.ipynb Cell 4)
        This is the core integration method for Component 6
        """
        print(f"🔍 Processing query through LSTM gates for user: {user_id}")
        print(f"❓ Query: '{user_query[:50]}...'")
        
        try:
            # Generate query features (placeholder - replace with Component 4)
            query_features = [random.random() for _ in range(90)]
            
            # Get relevant context using memory manager (demo.ipynb logic)
            relevant_memories, metadata = await self.memory_manager.get_relevant_context(
                user_id=user_id,
                query=user_query,
                query_features=query_features,
                max_tokens=1500
            )
            
            print(f"🎯 Found {len(relevant_memories)} relevant memories")
            print(f"📊 Metadata: {metadata}")
            
            # Convert to Component 6 format
            converted_memories = []
            relevance_scores = []
            
            for memory in relevant_memories:
                converted_memory = self._convert_memory_for_component6(memory)
                converted_memories.append(converted_memory)
                relevance_scores.append(memory.importance_score)
                
                print(f"   💭 {memory.memory_type}: {memory.content_summary[:60]}...")
                print(f"      Importance: {memory.importance_score:.3f}")
            
            # Update statistics
            self.stats['memories_retrieved'] = len(relevant_memories)
            self.stats['final_memories_count'] = len(converted_memories)
            
            return MemoryContext(
                selected_memories=converted_memories,
                relevance_scores=relevance_scores,
                token_usage=metadata.get('token_count', 0),
                assembly_metadata=metadata
            )
            
        except Exception as e:
            print(f"❌ Error retrieving memory context: {e}")
            return MemoryContext(
                selected_memories=[],
                relevance_scores=[],
                token_usage=0,
                assembly_metadata={"error": str(e)}
            )
    
    def _convert_memory_for_component6(self, lstm_memory: MemoryItem) -> Dict[str, Any]:
        """Convert LSTM MemoryItem to Component 6 format"""
        return {
            'id': lstm_memory.id,
            'user_id': lstm_memory.user_id,
            'content_summary': lstm_memory.content_summary,
            'memory_type': lstm_memory.memory_type,
            'importance_score': lstm_memory.importance_score,
            'emotional_significance': lstm_memory.emotional_significance or 0.5,
            'created_at': lstm_memory.created_at,
            'last_accessed': lstm_memory.last_accessed,
            'access_frequency': lstm_memory.access_frequency,
            'retrieval_triggers': lstm_memory.retrieval_triggers or [],
            'relationships': lstm_memory.relationships or [],
            'gate_scores': lstm_memory.gate_scores
        }
