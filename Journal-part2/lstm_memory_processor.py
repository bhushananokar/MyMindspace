#!/usr/bin/env python3
"""
LSTM Memory System Data Processor
Retrieves and processes memory data from AstraDB using the codebase components
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import LSTM system components as per README
from config.settings import LSTMConfig
from core.memory_manager import MemoryManager
from database.astra_connector import AstraDBConnector
from database.memory_store import MemoryStore
from models.memory_item import MemoryItem
from utils.token_counter import TokenCounter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryDataProcessor:
    """
    Main processor class that uses LSTM Memory System components
    to retrieve and process memory data from AstraDB
    """
    
    def __init__(self):
        self.config = None
        self.memory_manager = None
        self.db_connector = None
        self.memory_store = None
        self.token_counter = TokenCounter()
        
    async def initialize(self) -> bool:
        """Initialize the LSTM system using codebase components"""
        try:
            logger.info("🔄 Initializing LSTM Memory System...")
            
            # Create configuration from environment variables
            self.config = LSTMConfig()
            
            # Validate environment variables
            if not all([
                os.getenv('ASTRA_DATABASE_ID'),
                os.getenv('ASTRA_REGION'),
                os.getenv('ASTRA_TOKEN')
            ]):
                raise ValueError("Missing required Astra DB environment variables")
            
            # Initialize memory manager (as shown in README)
            self.memory_manager = MemoryManager(self.config)
            await self.memory_manager.initialize()
            
            # Get direct access to database components
            self.db_connector = self.memory_manager.db_connector
            self.memory_store = self.memory_manager.memory_store
            
            logger.info("✅ LSTM system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {e}")
            return False
    
    async def get_all_memory_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve all memory data using codebase functions
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            Processed memory data in JSON format
        """
        try:
            logger.info(f"📥 Retrieving memory data for user: {user_id or 'ALL USERS'}")
            
            if user_id:
                # Get memories for specific user using MemoryManager
                memories = await self.memory_manager._get_user_memories(user_id)
                user_ids = [user_id] if memories else []
            else:
                # Get all user IDs using MemoryStore
                user_ids = await self.memory_store.get_all_user_ids()
                memories = []
                
                # Get memories for all users
                for uid in user_ids:
                    user_memories = await self.memory_manager._get_user_memories(uid)
                    memories.extend(user_memories)
            
            logger.info(f"📊 Retrieved {len(memories)} memories for {len(user_ids)} users")
            
            # Process memories using codebase functions
            processed_data = await self._process_memories(memories, user_ids)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ Error retrieving memory data: {e}")
            return {"error": str(e), "memories": [], "statistics": {}}
    
    async def _process_memories(self, memories: List[MemoryItem], user_ids: List[str]) -> Dict[str, Any]:
        """
        Process memories using codebase utility functions
        
        Args:
            memories: List of MemoryItem objects
            user_ids: List of user IDs
            
        Returns:
            Processed data dictionary
        """
        processed_memories = []
        user_statistics = {}
        overall_statistics = {}
        
        # Process each memory using MemoryItem methods
        for memory in memories:
            try:
                # Convert MemoryItem to dictionary using built-in method
                memory_dict = memory.to_dict()
                
                # Add computed fields
                memory_dict['age_days'] = (datetime.now() - memory.created_at).days
                memory_dict['days_since_access'] = (datetime.now() - memory.last_accessed).days
                
                # Estimate tokens using TokenCounter from codebase
                token_estimate = self.token_counter.estimate_tokens(
                    memory.content_summary, 
                    tokenizer_type=self.token_counter.tokenizer_ratios.keys().__iter__().__next__()
                )
                memory_dict['estimated_tokens'] = token_estimate.token_count
                memory_dict['token_confidence'] = token_estimate.confidence
                
                processed_memories.append(memory_dict)
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing memory {memory.id}: {e}")
                continue
        
        # Generate user statistics using MemoryStore
        for user_id in user_ids:
            try:
                user_stats = await self.memory_store.get_memory_statistics(user_id)
                user_statistics[user_id] = user_stats
            except Exception as e:
                logger.warning(f"⚠️ Error getting statistics for user {user_id}: {e}")
                user_statistics[user_id] = {}
        
        # Calculate overall statistics
        overall_statistics = self._calculate_overall_statistics(processed_memories)
        
        # Use TokenCounter for memory token analysis
        memory_summaries = [m['content_summary'] for m in processed_memories]
        token_stats = self.token_counter.count_tokens_in_memories(memory_summaries)
        
        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_memories": len(processed_memories),
                "total_users": len(user_ids),
                "processing_method": "LSTM Memory System Components",
                "database_schema_version": "v1.0"
            },
            "memories": processed_memories,
            "user_statistics": user_statistics,
            "overall_statistics": overall_statistics,
            "token_analysis": token_stats,
            "gate_network_info": {
                "thresholds": self.memory_manager.gate_network.get_thresholds(),
                "configuration": self.config.to_dict()
            }
        }
    
    def _calculate_overall_statistics(self, memories: List[Dict]) -> Dict[str, Any]:
        """Calculate overall statistics from processed memories"""
        if not memories:
            return {}
        
        # Memory type distribution
        type_counts = {}
        importance_scores = []
        ages = []
        access_frequencies = []
        
        for memory in memories:
            # Type distribution
            mem_type = memory.get('memory_type', 'unknown')
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
            
            # Collect metrics
            importance_scores.append(memory.get('importance_score', 0))
            ages.append(memory.get('age_days', 0))
            access_frequencies.append(memory.get('access_frequency', 0))
        
        return {
            "memory_type_distribution": type_counts,
            "importance_statistics": {
                "mean": sum(importance_scores) / len(importance_scores),
                "min": min(importance_scores),
                "max": max(importance_scores)
            },
            "age_statistics": {
                "mean_days": sum(ages) / len(ages),
                "oldest_days": max(ages),
                "newest_days": min(ages)
            },
            "access_statistics": {
                "mean_frequency": sum(access_frequencies) / len(access_frequencies),
                "most_accessed": max(access_frequencies),
                "never_accessed": sum(1 for freq in access_frequencies if freq == 0)
            }
        }
    
    async def get_user_context(self, user_id: str, query: str = "General context") -> Dict[str, Any]:
        """
        Get relevant context for a user using MemoryManager's context assembly
        
        Args:
            user_id: User identifier
            query: Query for context relevance
            
        Returns:
            Context data in JSON format
        """
        try:
            logger.info(f"🔍 Getting context for user: {user_id}")
            
            # Generate dummy query features (in real implementation, use Component 4)
            import random
            query_features = [random.random() for _ in range(90)]
            
            # Use MemoryManager's context retrieval
            relevant_memories, metadata = await self.memory_manager.get_relevant_context(
                user_id=user_id,
                query=query,
                query_features=query_features,
                max_tokens=1500
            )
            
            # Process the context using ContextAssembler's formatting
            context_string = self.memory_manager.context_assembler.format_context_for_llm(
                relevant_memories, query
            )
            
            return {
                "user_id": user_id,
                "query": query,
                "relevant_memories": [memory.to_dict() for memory in relevant_memories],
                "context_metadata": metadata,
                "formatted_context": context_string,
                "context_statistics": self.memory_manager.context_assembler.get_context_statistics(relevant_memories)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user context: {e}")
            return {"error": str(e), "user_id": user_id}
    
    async def cleanup(self):
        """Cleanup resources using MemoryManager's cleanup"""
        if self.memory_manager:
            await self.memory_manager.cleanup()

async def main():
    """Main execution function"""
    processor = MemoryDataProcessor()
    
    try:
        # Initialize system
        if not await processor.initialize():
            logger.error("Failed to initialize system")
            return
        
        # Get command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Process LSTM Memory System data')
        parser.add_argument('--user-id', help='Specific user ID to process')
        parser.add_argument('--output-file', default='memory_data.json', help='Output JSON file')
        parser.add_argument('--context-query', help='Query for context retrieval')
        args = parser.parse_args()
        
        # Retrieve and process memory data
        logger.info("📊 Processing memory data...")
        memory_data = await processor.get_all_memory_data(args.user_id)
        
        # If context query provided, get context data
        if args.context_query and args.user_id:
            logger.info("🔍 Getting user context...")
            context_data = await processor.get_user_context(args.user_id, args.context_query)
            memory_data['user_context'] = context_data
        
        # Save to JSON file
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"✅ Data processed successfully! Output saved to: {args.output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("📋 PROCESSING SUMMARY")
        print("="*60)
        print(f"Total Memories: {memory_data['metadata']['total_memories']}")
        print(f"Total Users: {memory_data['metadata']['total_users']}")
        print(f"Total Tokens: {memory_data['token_analysis']['total_tokens']}")
        print(f"Output File: {args.output_file}")
        print(f"Timestamp: {memory_data['metadata']['timestamp']}")
        
        if 'user_context' in memory_data:
            print(f"Context Memories: {len(memory_data['user_context']['relevant_memories'])}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Script execution failed: {e}")
    
    finally:
        # Cleanup resources
        await processor.cleanup()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
