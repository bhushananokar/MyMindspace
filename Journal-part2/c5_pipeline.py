#!/usr/bin/env python3
"""
Component 5 Pipeline - LSTM Memory Gates Processing
==================================================

This script processes retrieved Astra DB data through Component 5's memory gates system:
1. Retrieves memories from Astra DB for user_id="123"
2. Processes through LSTM gates (Input, Forget, Output)
3. Applies intelligent memory filtering and scoring
4. Outputs processed memories ready for Component 6

Architecture:
Astra DB → Feature Processing → LSTM Gates → Memory Filtering → Component 6 Input
"""

import os
import sys
import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from dotenv import load_dotenv
from astrapy import DataAPIClient

# Add comp5 to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
comp5_path = os.path.join(project_root, 'comp5')
sys.path.insert(0, comp5_path)

# Component 5 imports (simplified for pipeline)
from comp5_lstm_config import LSTMConfig
from simple_lstm_gates import SimpleLSTMGates

# Load environment variables
load_dotenv()

class Component5Pipeline:
    """
    Complete Component 5 processing pipeline
    Handles memory retrieval, gate processing, and intelligent filtering
    """
    
    def __init__(self):
        self.config = self._create_config()
        self.gate_network = None
        self.memory_manager = None
        self.astra_client = None
        self.collection = None
        
        # Processing statistics
        self.stats = {
            'memories_retrieved': 0,
            'memories_processed': 0,
            'input_gate_accepted': 0,
            'forget_gate_triggered': 0,
            'output_gate_filtered': 0,
            'final_memories_count': 0,
            'processing_time': 0.0
        }
    
    def _create_config(self) -> LSTMConfig:
        """Create Component 5 configuration from environment"""
        
        # Astra DB config
        astra_config = AstraDBConfig(
            endpoint=os.getenv("ASTRA_DB_API_ENDPOINT", ""),
            token=os.getenv("ASTRA_DB_TOKEN", ""),
            keyspace=os.getenv("KEYSPACE", "default_keyspace")
        )
        
        # Gate network config
        gate_config = GateNetworkConfig(
            input_size=90,  # Feature vector size from Component 4
            hidden_size=128,
            dropout_rate=0.1
        )
        
        # Memory config
        memory_config = MemoryConfig(
            forget_threshold=0.3,
            input_threshold=0.4,  # 40% acceptance rate
            output_threshold=0.4,
            max_context_tokens=2000,
            max_memories_per_context=20
        )
        
        return LSTMConfig(
            astra_db=astra_config,
            gate_network=gate_config,
            memory=memory_config
        )
    
    async def initialize(self):
        """Initialize the Component 5 pipeline"""
        print("🚀 Initializing Component 5 Pipeline...")
        
        # Initialize Astra DB connection
        await self._init_astra_connection()
        
        # Initialize gate networks
        self.gate_network = LSTMGateNetwork(
            input_size=self.config.gate_network.input_size,
            hidden_size=self.config.gate_network.hidden_size,
            dropout=self.config.gate_network.dropout_rate
        )
        
        # Try to load pre-trained model
        try:
            model_path = os.path.join(comp5_path, "models", "gate_network.pt")
            if os.path.exists(model_path):
                self.gate_network = LSTMGateNetwork.load_model(model_path)
                print("✅ Loaded pre-trained gate network")
            else:
                print("📝 Using fresh gate network (no pre-trained model found)")
        except Exception as e:
            print(f"⚠️ Could not load pre-trained model: {e}")
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(self.config)
        
        print("✅ Component 5 Pipeline initialized successfully")
    
    async def _init_astra_connection(self):
        """Initialize Astra DB connection"""
        api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        api_token = os.getenv("ASTRA_DB_TOKEN")
        keyspace = os.getenv("KEYSPACE", "default_keyspace")
        collection_name = os.getenv("COLLECTION", "chat_embeddings")
        
        if not api_endpoint or not api_token:
            raise ValueError("Missing ASTRA_DB_API_ENDPOINT or ASTRA_DB_TOKEN")
        
        # Connect to Astra DB
        self.astra_client = DataAPIClient(api_token)
        db = self.astra_client.get_database_by_api_endpoint(api_endpoint)
        self.collection = db.get_collection(collection_name, keyspace=keyspace)
        
        print(f"✅ Connected to Astra DB: {collection_name}")
    
    async def retrieve_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve memories from Astra DB for the specified user"""
        print(f"📊 Retrieving memories for user: {user_id}")
        
        try:
            # Query Astra DB
            query = {"user_id": user_id}
            docs = list(self.collection.find(query))
            
            formatted_memories = []
            for doc in docs:
                # Convert Astra DB document to Component 5 format
                memory = {
                    "id": str(doc.get('_id', '')),
                    "user_id": doc.get('user_id', ''),
                    "memory_type": doc.get('memory_type', 'conversation'),
                    "content_summary": doc.get('content_summary', ''),
                    "importance_score": float(doc.get('importance_score', 0.0)),
                    "gate_scores": doc.get('gate_scores', {}),
                    "feature_vector": doc.get('feature_vector', []),
                    "created_at": doc.get('created_at', ''),
                    "last_accessed": doc.get('last_accessed', ''),
                    "access_frequency": int(doc.get('access_frequency', 0)),
                    "emotional_significance": float(doc.get('emotional_significance', 0.0)),
                    "temporal_relevance": float(doc.get('temporal_relevance', 0.0)),
                    "relationships": doc.get('relationships', []),
                    "context_needed": doc.get('context_needed', {}),
                    "retrieval_triggers": doc.get('retrieval_triggers', []),
                    "original_entry_id": str(doc.get('original_entry_id', ''))
                }
                formatted_memories.append(memory)
            
            self.stats['memories_retrieved'] = len(formatted_memories)
            print(f"✅ Retrieved {len(formatted_memories)} memories from Astra DB")
            return formatted_memories
            
        except Exception as e:
            print(f"❌ Error retrieving memories: {e}")
            return []
    
    def _ensure_feature_vector(self, memory: Dict[str, Any]) -> List[float]:
        """Ensure memory has a valid 90-dimension feature vector"""
        feature_vector = memory.get('feature_vector', [])
        
        if not feature_vector or len(feature_vector) != 90:
            # Generate synthetic feature vector if missing
            # In production, this would come from Component 4
            print(f"⚠️ Generating synthetic feature vector for memory {memory.get('id', 'unknown')}")
            
            # Create features based on available metadata
            importance = memory.get('importance_score', 0.5)
            emotional = memory.get('emotional_significance', 0.5)
            temporal = memory.get('temporal_relevance', 0.5)
            access_freq = min(memory.get('access_frequency', 0) / 10.0, 1.0)
            
            # Memory type encoding (one-hot)
            memory_type = memory.get('memory_type', 'conversation')
            type_encoding = [0.0] * 4
            type_map = {'conversation': 0, 'event': 1, 'emotion': 2, 'insight': 3}
            if memory_type in type_map:
                type_encoding[type_map[memory_type]] = 1.0
            
            # Content features (synthetic)
            content_length = len(memory.get('content_summary', '')) / 500.0
            content_features = [content_length] * 10
            
            # Temporal features
            try:
                created_at = datetime.fromisoformat(memory.get('created_at', '2024-01-01'))
                days_old = (datetime.now() - created_at).days / 365.0  # Normalize to years
            except:
                days_old = 0.5
            
            temporal_features = [days_old] * 5
            
            # Relationship features
            relationship_count = len(memory.get('relationships', [])) / 10.0
            relationship_features = [relationship_count] * 5
            
            # Combine all features to make 90 dimensions
            feature_vector = (
                [importance, emotional, temporal, access_freq] +  # 4
                type_encoding +  # 4
                content_features +  # 10
                temporal_features +  # 5
                relationship_features +  # 5
                [0.5] * 62  # Padding to reach 90 dimensions
            )
            
            # Ensure exactly 90 dimensions
            feature_vector = feature_vector[:90]
            while len(feature_vector) < 90:
                feature_vector.append(0.5)
        
        return feature_vector
    
    async def process_memory_through_gates(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single memory through LSTM gates"""
        
        # Ensure valid feature vector
        feature_vector = self._ensure_feature_vector(memory)
        
        # Get gate decisions
        gate_decisions = self.gate_network.get_gate_decisions(feature_vector)
        
        # Update memory with gate scores
        processed_memory = memory.copy()
        processed_memory['gate_decisions'] = gate_decisions
        processed_memory['feature_vector'] = feature_vector
        
        # Update importance score based on input gate
        input_score = gate_decisions['input']['score']
        processed_memory['importance_score'] = input_score
        
        # Apply forget gate (memory decay)
        forget_score = gate_decisions['forget']['score']
        if gate_decisions['forget']['decision']:
            # Apply decay based on forget gate
            current_importance = processed_memory['importance_score']
            processed_memory['importance_score'] = current_importance * (1 - forget_score)
            self.stats['forget_gate_triggered'] += 1
        
        # Track input gate decisions
        if gate_decisions['input']['decision']:
            self.stats['input_gate_accepted'] += 1
        
        # Track output gate decisions
        if not gate_decisions['output']['decision']:
            self.stats['output_gate_filtered'] += 1
        
        return processed_memory
    
    async def filter_memories_by_gates(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter memories based on gate decisions"""
        
        filtered_memories = []
        
        for memory in memories:
            gate_decisions = memory.get('gate_decisions', {})
            
            # Apply input gate filter (for new memories)
            input_decision = gate_decisions.get('input', {}).get('decision', True)
            
            # Apply output gate filter (for retrieval)
            output_decision = gate_decisions.get('output', {}).get('decision', True)
            
            # Keep memory if it passes both input and output gates
            if input_decision and output_decision:
                # Additional importance threshold check
                importance = memory.get('importance_score', 0.0)
                if importance > 0.1:  # Minimum importance threshold
                    filtered_memories.append(memory)
        
        return filtered_memories
    
    async def rank_memories_by_importance(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank memories by importance score and relevance"""
        
        # Sort by importance score (descending)
        ranked_memories = sorted(
            memories, 
            key=lambda m: m.get('importance_score', 0.0), 
            reverse=True
        )
        
        # Add ranking metadata
        for i, memory in enumerate(ranked_memories):
            memory['rank'] = i + 1
            memory['percentile'] = (len(ranked_memories) - i) / len(ranked_memories)
        
        return ranked_memories
    
    async def process_user_memories(self, user_id: str) -> Dict[str, Any]:
        """Complete processing pipeline for user memories"""
        start_time = datetime.now()
        
        print(f"\n🔄 Processing Component 5 Pipeline for user: {user_id}")
        print("=" * 60)
        
        try:
            # Step 1: Retrieve memories from Astra DB
            print("\n📊 Step 1: Retrieving memories from Astra DB...")
            raw_memories = await self.retrieve_user_memories(user_id)
            
            if not raw_memories:
                print("⚠️ No memories found for user")
                return {
                    'user_id': user_id,
                    'processed_memories': [],
                    'statistics': self.stats,
                    'processing_time': 0.0
                }
            
            # Step 2: Process each memory through LSTM gates
            print(f"\n🧠 Step 2: Processing {len(raw_memories)} memories through LSTM gates...")
            processed_memories = []
            
            for i, memory in enumerate(raw_memories):
                print(f"   Processing memory {i+1}/{len(raw_memories)}: {memory.get('id', 'unknown')[:8]}...")
                processed_memory = await self.process_memory_through_gates(memory)
                processed_memories.append(processed_memory)
                self.stats['memories_processed'] += 1
            
            # Step 3: Filter memories based on gate decisions
            print(f"\n🔍 Step 3: Filtering memories based on gate decisions...")
            filtered_memories = await self.filter_memories_by_gates(processed_memories)
            print(f"   Filtered to {len(filtered_memories)} memories")
            
            # Step 4: Rank memories by importance
            print(f"\n📈 Step 4: Ranking memories by importance...")
            final_memories = await self.rank_memories_by_importance(filtered_memories)
            self.stats['final_memories_count'] = len(final_memories)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats['processing_time'] = processing_time
            
            # Generate summary
            print(f"\n✅ Component 5 Processing Complete!")
            print(f"   📊 Input memories: {len(raw_memories)}")
            print(f"   🧠 Processed: {len(processed_memories)}")
            print(f"   🔍 Filtered: {len(filtered_memories)}")
            print(f"   📈 Final output: {len(final_memories)}")
            print(f"   ⏱️ Processing time: {processing_time:.2f}s")
            
            return {
                'user_id': user_id,
                'processed_memories': final_memories,
                'raw_memories': raw_memories,
                'gate_statistics': {
                    'input_gate_acceptance_rate': self.stats['input_gate_accepted'] / max(1, self.stats['memories_processed']),
                    'forget_gate_trigger_rate': self.stats['forget_gate_triggered'] / max(1, self.stats['memories_processed']),
                    'output_gate_filter_rate': self.stats['output_gate_filtered'] / max(1, self.stats['memories_processed']),
                    'overall_retention_rate': len(final_memories) / max(1, len(raw_memories))
                },
                'statistics': self.stats,
                'processing_time': processing_time
            }
            
        except Exception as e:
            print(f"❌ Error in Component 5 processing: {e}")
            import traceback
            traceback.print_exc()
            return {
                'user_id': user_id,
                'error': str(e),
                'processed_memories': [],
                'statistics': self.stats
            }
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save processing results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"component5_output_{results['user_id']}_{timestamp}.json"
        
        # Convert datetime objects to strings for JSON serialization
        serializable_results = self._make_json_serializable(results)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")
        return filename
    
    def _make_json_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return self._make_json_serializable(obj.__dict__)
        else:
            return obj


async def main():
    """Main execution function"""
    print("🚀 Component 5 LSTM Memory Gates Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = Component5Pipeline()
    await pipeline.initialize()
    
    # Process memories for user_id = "123"
    user_id = "123"
    results = await pipeline.process_user_memories(user_id)
    
    # Save results
    output_file = pipeline.save_results(results)
    
    # Display summary
    print(f"\n📋 Processing Summary:")
    print(f"   User ID: {results['user_id']}")
    print(f"   Memories processed: {results['statistics']['memories_processed']}")
    print(f"   Final memories: {results['statistics']['final_memories_count']}")
    print(f"   Processing time: {results['statistics']['processing_time']:.2f}s")
    
    if 'gate_statistics' in results:
        gate_stats = results['gate_statistics']
        print(f"\n🧠 Gate Statistics:")
        print(f"   Input gate acceptance: {gate_stats['input_gate_acceptance_rate']:.1%}")
        print(f"   Forget gate trigger: {gate_stats['forget_gate_trigger_rate']:.1%}")
        print(f"   Output gate filter: {gate_stats['output_gate_filter_rate']:.1%}")
        print(f"   Overall retention: {gate_stats['overall_retention_rate']:.1%}")
    
    print(f"\n💾 Output saved to: {output_file}")
    print(f"🎯 Ready for Component 6 integration!")
    
    return results


if __name__ == "__main__":
    # Run the pipeline
    results = asyncio.run(main())
