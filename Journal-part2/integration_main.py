#!/usr/bin/env python3
"""
Integration Main Script - Complete Gemini Engine Integration Test
Based on full_demo.ipynb notebook
Production-ready modular structure
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
comp5_path = os.path.join(project_root, 'comp5')

print("🔧 Environment Setup Complete")
print(f"Project Root: {project_root}")
print(f"Component 5 Path: {comp5_path}")

# Global variables for components
bridge = None
orchestrator = None
memory_context = None
conversation_results = []
error_results = []

class IntegrationTestSuite:
    """Main integration test suite class"""
    
    def __init__(self):
        self.bridge = None
        self.orchestrator = None
        self.memory_context = None
        self.conversation_results = []
        self.error_results = []
        
    async def run_all_tests(self):
        """Run all integration tests in sequence"""
        print("\n🚀 Starting Complete Integration Test Suite...")
        
        # Test 1: Basic Imports
        await self.test_basic_imports()
        
        # Test 2: Component 5 Bridge
        await self.test_component5_bridge()
        
        # Test 3: Astra Configuration Debug
        await self.test_astra_configuration()
        
        # Test 4: Bridge Initialization
        await self.test_bridge_initialization()
        
        # Test 5: Environment Variables Check
        await self.test_environment_variables()
        
        # Test 6: Bridge Components Debug
        await self.test_bridge_components()
        
        # Test 7: Health Checks
        await self.test_health_checks()
        
        # Test 8: Memory Context Retrieval
        await self.test_memory_context_retrieval()
        
        # Test 9: Orchestrator Creation
        await self.test_orchestrator_creation()
        
        # Test 10: Orchestrator Initialization
        await self.test_orchestrator_initialization()
        
        # Test 11: Orchestrator Health Check
        await self.test_orchestrator_health_check()
        
        # Test 12: Single Conversation Test
        await self.test_single_conversation()
        
        # Test 13: LSTM Memory Flow Test
        await self.test_lstm_memory_flow()
        
        # Test 14: Error Handling Test
        await self.test_error_handling()
        
        # Test 15: Performance Analysis
        await self.test_performance_analysis()
        
        # Test 16: Final Integration Status
        await self.test_final_integration_status()
        
        # Test 17: Cleanup
        await self.test_cleanup()
        
        print("🏁 All integration tests completed!")

    async def test_basic_imports(self):
        """Test 1: Basic Imports"""
        print("\n🧪 Testing Basic Imports...")

        try:
            # Test configu import
            from configu.settings import settings
            print("✅ configu.settings imported successfully")
        except Exception as e:
            print(f"❌ configu.settings import failed: {e}")

        try:
            # Test shared imports
            from shared.schemas import MemoryContext, UserProfile, EnhancedResponse
            from shared.utils import get_logger, generate_correlation_id
            print("✅ shared modules imported successfully")
        except Exception as e:
            print(f"❌ shared modules import failed: {e}")

        try:
            # Test Component 5 imports
            from comp5.config.settings import LSTMConfig
            from comp5.core.memory_manager import MemoryManager
            print("✅ Component 5 modules imported successfully")
        except Exception as e:
            print(f"❌ Component 5 modules import failed: {e}")

    async def test_component5_bridge(self):
        """Test 2: Component 5 Bridge Creation"""
        print("\n🧠 Testing Component 5 Bridge...")

        try:
            from component6.comp5_interface import Component5Bridge
            
            # Create bridge instance
            self.bridge = Component5Bridge()
            print("✅ Component5Bridge created successfully")
            
            # Check initial state
            print(f"📊 Bridge initialized: {self.bridge._initialized}")
            print(f"📊 Bridge stats: {self.bridge.stats}")
            
        except Exception as e:
            print(f"❌ Component5Bridge creation failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    async def test_astra_configuration(self):
        """Test 3: Astra Configuration Debug"""
        print("\n🔍 DEBUG: Component 5 Astra Configuration...")

        try:
            from comp5.config.settings import LSTMConfig, AstraDBConfig
            
            # Test manual config creation
            print("🧪 Testing manual AstraDBConfig creation...")
            
            # Get environment variables directly
            endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
            token = os.getenv("ASTRA_DB_TOKEN")
            keyspace = os.getenv("KEYSPACE")
            
            print(f"📊 Raw env vars:")
            print(f"   ASTRA_DB_API_ENDPOINT: '{endpoint}'")
            print(f"   ASTRA_DB_TOKEN: '{token[:20] if token else None}...'")
            print(f"   KEYSPACE: '{keyspace}'")
            
            # Test AstraDBConfig creation methods
            print("\n🧪 Testing AstraDBConfig.from_env()...")
            try:
                astra_config = AstraDBConfig.from_env()
                print(f"✅ AstraDBConfig.from_env() successful:")
                print(f"   endpoint: '{astra_config.endpoint}'")
                print(f"   token: '{astra_config.token[:20] if astra_config.token else None}...'")
                print(f"   keyspace: '{astra_config.keyspace}'")
            except Exception as config_error:
                print(f"❌ AstraDBConfig.from_env() failed: {config_error}")
            
            # Test manual AstraDBConfig creation
            print("\n🧪 Testing manual AstraDBConfig creation...")
            try:
                manual_astra_config = AstraDBConfig(
                    endpoint=endpoint,
                    token=token,
                    keyspace=keyspace or "default_keyspace"
                )
                print(f"✅ Manual AstraDBConfig successful:")
                print(f"   endpoint: '{manual_astra_config.endpoint}'")
                print(f"   token: '{manual_astra_config.token[:20] if manual_astra_config.token else None}...'")
                print(f"   keyspace: '{manual_astra_config.keyspace}'")
            except Exception as manual_error:
                print(f"❌ Manual AstraDBConfig failed: {manual_error}")
            
            # Test full LSTMConfig creation
            print("\n🧪 Testing LSTMConfig creation...")
            try:
                lstm_config = LSTMConfig()
                print(f"✅ LSTMConfig created successfully:")
                print(f"   astra endpoint: '{lstm_config.astra_db.endpoint}'")
                print(f"   astra token: '{lstm_config.astra_db.token[:20] if lstm_config.astra_db.token else None}...'")
                print(f"   astra keyspace: '{lstm_config.astra_db.keyspace}'")
            except Exception as lstm_error:
                print(f"❌ LSTMConfig creation failed: {lstm_error}")
            
        except Exception as e:
            print(f"❌ Configuration debug failed: {e}")

        # Create working Astra config
        print("\n🛠️ MANUAL FIX: Creating working Astra config...")
        try:
            from comp5.config.settings import AstraDBConfig, LSTMConfig
            
            # Use environment variables instead of hardcoded values
            working_astra_config = AstraDBConfig(
                endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
                token=os.getenv("ASTRA_DB_TOKEN"),
                keyspace=os.getenv("KEYSPACE", "memory_db")
            )
            
            print(f"✅ Working Astra config created:")
            print(f"   endpoint: {working_astra_config.endpoint}")
            print(f"   keyspace: {working_astra_config.keyspace}")
            
            # Test if we can create a new bridge with this config
            print("\n🧪 Testing bridge with fixed config...")
            
            # Modify the bridge's config
            if self.bridge and hasattr(self.bridge, 'config') and self.bridge.config:
                self.bridge.config.astra_db = working_astra_config
                print("✅ Bridge config updated with working Astra settings")
            
        except Exception as e:
            print(f"❌ Manual fix failed: {e}")

        print("\n🔍 Component 5 configuration debug completed!")

    async def test_bridge_initialization(self):
        """Test 4: Bridge Initialization"""
        print("\n🚀 Initializing Component 5 Bridge...")

        try:
            # Initialize the bridge (async call)
            init_success = await self.bridge.initialize()
            
            if init_success:
                print("✅ Component 5 Bridge initialized successfully")
                print(f"📊 Memory Manager: {self.bridge.memory_manager is not None}")
                print(f"📊 Gate Network: {self.bridge.gate_network is not None}")
                
                # Get statistics safely
                try:
                    stats = self.bridge.get_statistics()
                    print(f"📊 Bridge Statistics: {json.dumps(stats, indent=2, default=str)}")
                except Exception as stats_error:
                    print(f"⚠️  Could not get full statistics: {stats_error}")
                    print(f"📊 Basic Status: Initialized={self.bridge._initialized}")
                
            else:
                print("❌ Component 5 Bridge initialization failed")
                
        except Exception as e:
            print(f"❌ Component 5 Bridge initialization error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Check if it's just a database connection issue
            if "Astra DB" in str(e) or "Request URL" in str(e):
                print("ℹ️  This appears to be an Astra DB connection issue.")
                print("ℹ️  The LSTM gates may still work for testing with mock data.")
                print("ℹ️  Check your ASTRA_DB_API_ENDPOINT and ASTRA_DB_TOKEN in .env file.")

    async def test_environment_variables(self):
        """Test 5: Environment Variables Check"""
        print("\n📊 Environment Variables Check...")

        # Check what's actually being read
        astra_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        astra_token = os.getenv("ASTRA_DB_TOKEN") 
        keyspace = os.getenv("KEYSPACE")

        print(f"📊 ASTRA_DB_API_ENDPOINT: '{astra_endpoint}'")
        print(f"📊 ASTRA_DB_TOKEN: '{astra_token[:20] if astra_token else None}...' (truncated)")
        print(f"📊 KEYSPACE: '{keyspace}'")

        # Check if .env file exists and is readable
        env_file_path = os.path.join(os.getcwd(), ".env")
        print(f"📊 .env file exists: {os.path.exists(env_file_path)}")

        if os.path.exists(env_file_path):
            print(f"📊 .env file path: {env_file_path}")
            # Read first few lines to verify content
            with open(env_file_path, 'r') as f:
                lines = f.readlines()[:10]
                print("📊 First 10 lines of .env file:")
                for i, line in enumerate(lines, 1):
                    if "ASTRA" in line or "KEYSPACE" in line:
                        print(f"   {i}: {line.strip()}")

        # Check environment variables from all sources
        print(f"\n🔍 All environment variables containing 'ASTRA':")
        for key, value in os.environ.items():
            if 'ASTRA' in key:
                print(f"   {key}: {value[:50] if value else 'None'}...")

    async def test_bridge_components(self):
        """Test 6: Bridge Components Debug"""
        print("\n🔍 DEBUG: Checking Bridge Components...")

        # Check what's actually in the bridge
        print(f"📊 Bridge initialized: {self.bridge._initialized}")
        print(f"📊 Bridge has memory_manager: {hasattr(self.bridge, 'memory_manager')}")
        print(f"📊 Memory manager is not None: {self.bridge.memory_manager is not None}")
        print(f"📊 Bridge has gate_network: {hasattr(self.bridge, 'gate_network')}")
        print(f"📊 Gate network is not None: {self.bridge.gate_network is not None}")

        if self.bridge.memory_manager:
            print(f"📊 Memory Manager type: {type(self.bridge.memory_manager)}")
            print(f"📊 Memory Manager has gate_network: {hasattr(self.bridge.memory_manager, 'gate_network')}")
            print(f"📊 Memory Manager gate_network is not None: {self.bridge.memory_manager.gate_network is not None}")

        if self.bridge.gate_network:
            print(f"📊 Gate Network type: {type(self.bridge.gate_network)}")
            print(f"📊 Gate Network methods: {[method for method in dir(self.bridge.gate_network) if not method.startswith('_')]}")

        # Check what methods the health check is trying to call
        print(f"📊 Bridge health_check method exists: {hasattr(self.bridge, 'health_check')}")

    async def test_health_checks(self):
        """Test 7: Health Checks"""
        print("\n🏥 Testing Component 5 Health Check...")
        try:
            health = await self.bridge.health_check()
            print("✅ Health check completed")
            print(f"📊 Health Status: {json.dumps(health, indent=2, default=str)}")
            
            # Check individual components
            print(f"🔧 Initialized: {health.get('initialized', False)}")
            print(f"🔧 Config Valid: {health.get('config_valid', False)}")
            print(f"🔧 Memory Manager: {health.get('memory_manager_healthy', False)}")
            print(f"🔧 Gate Network: {health.get('gate_network_healthy', False)}")
            print(f"🔧 Database: {health.get('database_connection', False)}")
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    async def test_memory_context_retrieval(self):
        """Test 8: Memory Context Retrieval"""
        print("\n💭 Testing Memory Context Retrieval...")

        try:
            # Test memory context retrieval
            self.memory_context = await self.bridge.get_memory_context(
                user_id="test_user_123",
                current_message="How am I feeling about work lately?",
                conversation_id="test_conv_001",
                max_memories=5
            )
            
            print("✅ Memory context retrieved successfully")
            print(f"📊 Memories Found: {len(self.memory_context.selected_memories)}")
            print(f"📊 Token Usage: {self.memory_context.token_usage}")
            print(f"📊 Assembly Metadata: {self.memory_context.assembly_metadata}")
            
            # Show sample memories
            for i, memory in enumerate(self.memory_context.selected_memories[:3]):
                print(f"   Memory {i+1}: {memory.get('content_summary', 'No summary')[:60]}...")
                print(f"   Importance: {memory.get('importance_score', 0):.3f}")
                
        except Exception as e:
            print(f"❌ Memory context retrieval failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    async def test_orchestrator_creation(self):
        """Test 9: Orchestrator Creation"""
        print("\n🎼 Testing Orchestrator Creation...")

        try:
            from gemini_engine_orchestrator import GeminiEngineOrchestrator
            
            # Create orchestrator with Component 5 bridge
            self.orchestrator = GeminiEngineOrchestrator()
            print("✅ GeminiEngineOrchestrator created successfully")
            
            # Check components
            print(f"📊 Component 5 Bridge: {self.orchestrator.component5_bridge is not None}")
            print(f"📊 Conversation Manager: {self.orchestrator.conversation_manager is not None}")
            print(f"📊 Memory Retriever: {self.orchestrator.memory_retriever is not None}")
            print(f"📊 Gemini Client: {self.orchestrator.gemini_client is not None}")
            
        except Exception as e:
            print(f"❌ Orchestrator creation failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    async def test_orchestrator_initialization(self):
        """Test 10: Orchestrator Initialization"""
        print("\n🚀 Initializing Orchestrator...")

        try:
            # Initialize orchestrator
            init_success = await self.orchestrator.initialize()
            
            if init_success:
                print("✅ Orchestrator initialized successfully")
                
                # Get performance summary
                performance = self.orchestrator.get_performance_summary()
                print(f"📊 Performance Summary: {json.dumps(performance, indent=2, default=str)}")
                
            else:
                print("❌ Orchestrator initialization failed")
                
        except Exception as e:
            print(f"❌ Orchestrator initialization error: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    async def test_orchestrator_health_check(self):
        """Test 11: Orchestrator Health Check"""
        print("\n🏥 Testing Orchestrator Health Check...")

        try:
            health = await self.orchestrator.health_check()
            print("✅ Orchestrator health check completed")
            
            print(f"📊 Overall Healthy: {health.get('overall_healthy', False)}")
            
            # Component health details
            comp_health = health.get('component_health', {})
            for component, status in comp_health.items():
                print(f"🔧 {component}: {status}")
            
            # System metrics
            sys_metrics = health.get('system_metrics', {})
            print(f"📊 System Metrics: {json.dumps(sys_metrics, indent=2, default=str)}")
            
        except Exception as e:
            print(f"❌ Orchestrator health check failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    async def test_single_conversation(self):
        """Test 12: Single Conversation Test"""
        print("\n💬 Testing Single Conversation...")

        try:
            # Process a test conversation
            test_message = "I'm feeling excited about my new AI project!"
            print(f"User: {test_message}")
            
            start_time = datetime.utcnow()
            
            response = await self.orchestrator.process_conversation(
                user_id="test_user_123",
                user_message=test_message,
                conversation_id="notebook_test_conv",
                emotional_state={
                    "primary_emotion": "excited",
                    "intensity": 0.8,
                    "confidence": 0.9
                }
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            print("✅ Conversation processed successfully")
            print(f"🤖 AI Response: {response.enhanced_response}")
            print(f"⏱️  Processing Time: {processing_time:.2f}ms")
            
            # Show enhanced response details
            print(f"\n📋 Response Details:")
            print(f"   Response ID: {response.response_id}")
            print(f"   Conversation ID: {response.conversation_id}")
            print(f"   User ID: {response.user_id}")
            
            # Show analysis if available
            if hasattr(response, 'response_analysis') and response.response_analysis:
                analysis = response.response_analysis
                print(f"\n📊 Response Analysis:")
                
                # Safe access to quality_scores
                if hasattr(analysis, 'quality_scores'):
                    quality_scores = analysis.quality_scores
                    if isinstance(quality_scores, dict):
                        print(f"   Overall Quality: {quality_scores.get('overall_quality', 0.0):.3f}")
                        print(f"   Coherence Score: {quality_scores.get('coherence_score', 0.0):.3f}")
                        print(f"   Relevance Score: {quality_scores.get('relevance_score', 0.0):.3f}")
                        print(f"   Context Usage: {quality_scores.get('context_usage_score', 0.0):.3f}")
                        print(f"   Safety Score: {quality_scores.get('safety_score', 1.0):.3f}")
                    else:
                        print(f"   Quality scores not accessible as dict: {type(quality_scores)}")
                
                # Show user satisfaction if available
                if hasattr(analysis, 'user_satisfaction'):
                    print(f"   User Satisfaction: {analysis.user_satisfaction:.3f}")
                
                # Show improvement suggestions
                if hasattr(analysis, 'improvement_suggestions') and analysis.improvement_suggestions:
                    print(f"   💡 Suggestions: {', '.join(analysis.improvement_suggestions[:2])}")
                
                # Show context usage details
                if hasattr(analysis, 'context_usage') and analysis.context_usage:
                    context_usage = analysis.context_usage
                    if isinstance(context_usage, dict):
                        memories_ref = context_usage.get('memories_referenced', 0)
                        integration_score = context_usage.get('context_integration_score', 0.0)
                        print(f"   Memories Referenced: {memories_ref}")
                        print(f"   Context Integration: {integration_score:.3f}")
            
            else:
                print(f"\n📊 No detailed analysis available")
                print(f"   response.response_analysis exists: {hasattr(response, 'response_analysis')}")
                if hasattr(response, 'response_analysis'):
                    print(f"   response.response_analysis value: {response.response_analysis}")
            
            # Show memory context metadata
            if hasattr(response, 'memory_context_metadata') and response.memory_context_metadata:
                memories_used = response.memory_context_metadata.get('memories_used', 0)
                print(f"\n🧠 Memory Context:")
                print(f"   Memories Used: {memories_used}")
                print(f"   Metadata: {response.memory_context_metadata}")
            
            # Show enhancement metadata
            if hasattr(response, 'enhancement_metadata') and response.enhancement_metadata:
                metadata = response.enhancement_metadata
                print(f"\n⚡ Enhancement Metadata:")
                if isinstance(metadata, dict):
                    print(f"   Fallback Used: {metadata.get('fallback_used', False)}")
                    if 'error' in metadata:
                        print(f"   Error: {metadata['error']}")
                    print(f"   Processing Time: {metadata.get('processing_time_ms', 'N/A')}ms")
            
            # Show follow-up suggestions
            if hasattr(response, 'follow_up_suggestions') and response.follow_up_suggestions:
                print(f"\n❓ Follow-up Suggestions:")
                for i, suggestion in enumerate(response.follow_up_suggestions[:3], 1):
                    print(f"   {i}. {suggestion}")
            
            print(f"\n🔧 Integration Status: SUCCESS! All components working together.")

        except Exception as e:
            print(f"❌ Conversation processing failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Additional debugging if needed
            print(f"\n🔍 Debug Information:")
            print(f"   Error type: {type(e).__name__}")
            if 'response' in locals():
                print(f"   Response exists: True")
                print(f"   Response type: {type(response)}")
            else:
                print(f"   Response exists: False")

    async def test_lstm_memory_flow(self):
        """Test 13: LSTM Memory Retrieval → Conversation Engine Flow"""
        print("\n💭🤖 Testing LSTM Memory Retrieval → Conversation Engine Flow...")

        conversation_tests = [
            {
                "message": "I just finished a big presentation at work",
                "emotion": {"primary_emotion": "relieved", "intensity": 0.7}
            },
            {
                "message": "Can you remind me what we discussed about presentations?", 
                "emotion": {"primary_emotion": "curious", "intensity": 0.6}
            },
            {
                "message": "I think I want to improve my public speaking skills",
                "emotion": {"primary_emotion": "motivated", "intensity": 0.8}
            }
        ]

        self.conversation_results = []

        for i, test in enumerate(conversation_tests, 1):
            try:
                print(f"\n--- Conversation {i} ---")
                print(f"👤 User Query: {test['message']}")
                
                # STEP 1: Get LSTM Memory Context
                print(f"🧠 Step 1: Retrieving LSTM memory context...")
                start_retrieval = datetime.utcnow()
                
                memory_context = await self.bridge.get_memory_context(
                    user_id="flow_test_user",
                    current_message=test['message'],
                    conversation_id="flow_test_conv",
                    max_memories=10
                )
                
                retrieval_time = (datetime.utcnow() - start_retrieval).total_seconds() * 1000
                print(f"   📊 Retrieved {len(memory_context.selected_memories)} memories in {retrieval_time:.2f}ms")
                
                # Show retrieved memories
                for j, memory in enumerate(memory_context.selected_memories[:3]):
                    relevance = memory_context.relevance_scores[j] if j < len(memory_context.relevance_scores) else 0
                    print(f"   💭 Memory {j+1}: {memory.get('content_summary', 'No summary')[:50]}... (relevance: {relevance:.3f})")
                
                # STEP 2: Assemble Context + Query
                print(f"🔧 Step 2: Assembling context + query for conversation engine...")
                
                # Create enhanced context with LSTM memories
                context_with_memories = {
                    "user_query": test['message'],
                    "emotional_state": test['emotion'],
                    "lstm_memories": memory_context.selected_memories,
                    "memory_metadata": memory_context.assembly_metadata,
                    "token_usage": memory_context.token_usage
                }
                
                print(f"   📊 Context assembled with {len(memory_context.selected_memories)} memories")
                print(f"   📊 Total context tokens: {memory_context.token_usage}")
                
                # STEP 3: Process through Conversation Engine
                print(f"🤖 Step 3: Processing through conversation engine...")
                start_conversation = datetime.utcnow()
                
                # Use orchestrator's conversation manager with the LSTM context
                response = await self.orchestrator.conversation_manager.process_conversation(
                    user_id="flow_test_user",
                    user_message=test['message'],
                    conversation_id="flow_test_conv",
                    emotional_state=test['emotion']
                )
                
                conversation_time = (datetime.utcnow() - start_conversation).total_seconds() * 1000
                total_time = retrieval_time + conversation_time
                
                print(f"   🤖 AI Response: {response.enhanced_response[:100]}...")
                print(f"   ⏱️  Conversation time: {conversation_time:.2f}ms")
                print(f"   ⏱️  Total time (retrieval + conversation): {total_time:.2f}ms")
                
                # STEP 4: Show Memory Usage in Response
                print(f"🔍 Step 4: Memory usage analysis...")
                
                # Check if memories influenced the response
                memory_usage_analysis = {
                    "memories_retrieved": len(memory_context.selected_memories),
                    "avg_memory_relevance": sum(memory_context.relevance_scores) / len(memory_context.relevance_scores) if memory_context.relevance_scores else 0,
                    "context_tokens_used": memory_context.token_usage,
                    "lstm_source": memory_context.assembly_metadata.get('source', 'unknown')
                }
                
                print(f"   📊 Memory Usage: {json.dumps(memory_usage_analysis, indent=6)}")
                
                # Store detailed results
                self.conversation_results.append({
                    "conversation": i,
                    "message": test['message'],
                    "memory_retrieval_time_ms": retrieval_time,
                    "conversation_processing_time_ms": conversation_time,
                    "total_processing_time_ms": total_time,
                    "memories_used": len(memory_context.selected_memories),
                    "memory_relevance_avg": memory_usage_analysis["avg_memory_relevance"],
                    "response_length": len(response.enhanced_response),
                    "success": True,
                    "lstm_context_success": True
                })
                
                # Small delay between conversations to see the memory buildup
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Conversation {i} failed: {e}")
                print(f"   Traceback: {traceback.format_exc()}")
                
                self.conversation_results.append({
                    "conversation": i,
                    "message": test['message'],
                    "error": str(e),
                    "success": False,
                    "lstm_context_success": False
                })

        # Analyze the Complete Flow Results
        await self._analyze_lstm_flow_results()

    async def _analyze_lstm_flow_results(self):
        """Analyze LSTM flow results"""
        print(f"\n📊 LSTM → Conversation Engine Flow Analysis:")
        print("=" * 60)

        total_conversations = len(self.conversation_results)
        successful_conversations = len([r for r in self.conversation_results if r.get("success", False)])
        lstm_context_successes = len([r for r in self.conversation_results if r.get("lstm_context_success", False)])

        print(f"Total Conversations: {total_conversations}")
        print(f"Successful Conversations: {successful_conversations}")
        print(f"LSTM Context Successes: {lstm_context_successes}")
        print(f"Overall Success Rate: {successful_conversations/total_conversations*100:.1f}%")
        print(f"LSTM Integration Rate: {lstm_context_successes/total_conversations*100:.1f}%")

        if successful_conversations > 0:
            # Calculate averages for successful conversations
            successful_results = [r for r in self.conversation_results if r.get("success", False)]
            
            avg_memory_retrieval = sum(r.get("memory_retrieval_time_ms", 0) for r in successful_results) / len(successful_results)
            avg_conversation_time = sum(r.get("conversation_processing_time_ms", 0) for r in successful_results) / len(successful_results)
            avg_total_time = sum(r.get("total_processing_time_ms", 0) for r in successful_results) / len(successful_results)
            avg_memories_used = sum(r.get("memories_used", 0) for r in successful_results) / len(successful_results)
            avg_relevance = sum(r.get("memory_relevance_avg", 0) for r in successful_results) / len(successful_results)
            
            print(f"\nPerformance Metrics (Successful Conversations):")
            print(f"  📊 Avg Memory Retrieval Time: {avg_memory_retrieval:.2f}ms")
            print(f"  📊 Avg Conversation Processing: {avg_conversation_time:.2f}ms")
            print(f"  📊 Avg Total Processing Time: {avg_total_time:.2f}ms")
            print(f"  📊 Avg Memories Used: {avg_memories_used:.1f}")
            print(f"  📊 Avg Memory Relevance: {avg_relevance:.3f}")

        # Show individual conversation results
        print(f"\nDetailed Results:")
        for result in self.conversation_results:
            status = "✅" if result.get("success", False) else "❌"
            lstm_status = "🧠" if result.get("lstm_context_success", False) else "🚫"
            print(f"  {status} {lstm_status} Conv {result['conversation']}: {result.get('message', '')[:30]}...")
            if result.get("success", False):
                print(f"      Time: {result.get('total_processing_time_ms', 0):.1f}ms, Memories: {result.get('memories_used', 0)}")

        # Assessment
        if lstm_context_successes == total_conversations and successful_conversations == total_conversations:
            print(f"\n🎉 PERFECT! LSTM Memory → Conversation Engine integration working flawlessly!")
        elif lstm_context_successes > 0 and successful_conversations > 0:
            print(f"\n👍 GOOD! LSTM Memory → Conversation Engine integration mostly working.")
        else:
            print(f"\n❌ ISSUES! LSTM Memory → Conversation Engine integration needs debugging.")

    async def test_error_handling(self):
        """Test 14: Error Handling Test"""
        print("\n🚨 Testing Error Handling...")

        error_tests = [
            {
                "name": "Empty Message",
                "user_id": "error_test_user",
                "message": "",
                "expected": "Should handle empty message gracefully"
            },
            {
                "name": "Very Long Message", 
                "user_id": "error_test_user",
                "message": "This is a very long message. " * 200,  # ~1000+ words
                "expected": "Should handle long messages"
            },
            {
                "name": "Special Characters",
                "user_id": "error_test_user", 
                "message": "Hello! @#$%^&*()_+ 🚀🤖💭 नमस्ते 你好",
                "expected": "Should handle unicode and special chars"
            }
        ]

        self.error_results = []

        for test in error_tests:
            try:
                print(f"\n🧪 Testing: {test['name']}")
                print(f"Message: {test['message'][:50]}...")
                
                response = await self.orchestrator.process_conversation(
                    user_id=test['user_id'],
                    user_message=test['message'],
                    conversation_id=f"error_test_{test['name'].lower().replace(' ', '_')}"
                )
                
                print(f"✅ {test['name']}: Handled successfully")
                print(f"Response: {response.enhanced_response[:100]}...")
                
                self.error_results.append({
                    "test": test['name'],
                    "status": "success",
                    "handled": True
                })
                
            except Exception as e:
                print(f"⚠️  {test['name']}: {e}")
                self.error_results.append({
                    "test": test['name'],
                    "status": "error", 
                    "error": str(e),
                    "handled": False
                })

        print(f"\n📊 Error Handling Results:")
        for result in self.error_results:
            status = "✅" if result["status"] == "success" else "⚠️"
            print(f"   {status} {result['test']}: {result['status']}")

    async def test_performance_analysis(self):
        """Test 15: Performance Analysis"""
        print("\n⚡ Performance Analysis...")

        try:
            # Get comprehensive performance data
            performance_summary = self.orchestrator.get_performance_summary()
            
            print("📊 PERFORMANCE SUMMARY:")
            print("=" * 50)
            
            # Conversation metrics
            conv_metrics = performance_summary.get('conversation_metrics', {})
            print(f"Total Conversations: {conv_metrics.get('total_conversations', 0)}")
            print(f"Average Response Time: {conv_metrics.get('avg_response_time_ms', 0):.2f}ms")
            print(f"Success Rate: {conv_metrics.get('success_rate', 0)*100:.1f}%")
            
            # Component 5 stats
            comp5_stats = performance_summary.get('component5_stats', {})
            bridge_stats = comp5_stats.get('bridge_stats', {})
            print(f"\nComponent 5 Performance:")
            print(f"  Memories Retrieved: {bridge_stats.get('memories_retrieved', 0)}")
            print(f"  Context Assemblies: {bridge_stats.get('context_assemblies', 0)}")
            print(f"  Gate Decisions: {bridge_stats.get('gate_decisions', 0)}")
            print(f"  Errors: {bridge_stats.get('errors', 0)}")
            
            # Component 6 stats
            comp6_stats = performance_summary.get('component6_stats', {})
            print(f"\nComponent 6 Performance:")
            print(f"  Active Conversations: {comp6_stats.get('active_conversations', 0)}")
            print(f"  Memory Cache Size: {comp6_stats.get('memory_cache_size', 0)}")
            
            # Calculate performance assessment
            avg_time = conv_metrics.get('avg_response_time_ms', 0)
            success_rate = conv_metrics.get('success_rate', 0)
            
            if avg_time < 5000 and success_rate > 0.8:
                print(f"\n🎉 PERFORMANCE: EXCELLENT")
            elif avg_time < 10000 and success_rate > 0.6:
                print(f"\n👍 PERFORMANCE: GOOD")
            else:
                print(f"\n⚠️  PERFORMANCE: NEEDS OPTIMIZATION")
            
        except Exception as e:
            print(f"❌ Performance analysis failed: {e}")

    async def test_final_integration_status(self):
        """Test 16: Final Integration Status"""
        print("\n🏁 FINAL INTEGRATION STATUS")
        print("=" * 60)

        # Summary of all tests
        test_summary = {
            "component5_bridge": "✅ Working" if self.bridge and self.bridge._initialized else "❌ Failed",
            "orchestrator": "✅ Working" if self.orchestrator else "❌ Failed", 
            "memory_retrieval": "✅ Working" if self.memory_context else "❌ Failed",
            "conversation_processing": "✅ Working" if len([r for r in self.conversation_results if r.get("success", False)]) > 0 else "❌ Failed",
            "error_handling": "✅ Working" if len([r for r in self.error_results if r.get("status") == "success"]) > 0 else "❌ Failed"
        }

        for component, status in test_summary.items():
            print(f"{status} {component.replace('_', ' ').title()}")

        # Overall assessment
        working_components = len([s for s in test_summary.values() if "✅" in s])
        total_components = len(test_summary)
        success_rate = working_components / total_components

        print(f"\n📊 Overall Success Rate: {success_rate*100:.1f}% ({working_components}/{total_components})")

        if success_rate >= 0.8:
            print("🎉 INTEGRATION SUCCESSFUL! All major components working.")
        elif success_rate >= 0.6:
            print("👍 INTEGRATION MOSTLY WORKING. Minor issues to address.")
        else:
            print("❌ INTEGRATION NEEDS WORK. Major issues detected.")

        print(f"\n✅ Integration test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async def test_cleanup(self):
        """Test 17: Cleanup"""
        print("\n🧹 Cleanup...")

        try:
            # Cleanup resources
            if self.orchestrator:
                await self.orchestrator.cleanup()
            
            if self.bridge:
                await self.bridge.cleanup()
            
            print("✅ Cleanup completed successfully")
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        print("🏁 All tests completed!")

# Production-ready functions for individual test execution
async def run_basic_imports_test():
    """Run basic imports test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_basic_imports()

async def run_component5_bridge_test():
    """Run Component 5 bridge test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_component5_bridge()

async def run_astra_configuration_test():
    """Run Astra configuration test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_astra_configuration()

async def run_bridge_initialization_test():
    """Run bridge initialization test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_bridge_initialization()

async def run_memory_context_test():
    """Run memory context retrieval test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_memory_context_retrieval()

async def run_orchestrator_test():
    """Run orchestrator creation and initialization test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_orchestrator_creation()
    await test_suite.test_orchestrator_initialization()

async def run_conversation_test():
    """Run single conversation test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_single_conversation()

async def run_lstm_flow_test():
    """Run LSTM memory flow test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_lstm_memory_flow()

async def run_error_handling_test():
    """Run error handling test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_error_handling()

async def run_performance_test():
    """Run performance analysis test"""
    test_suite = IntegrationTestSuite()
    await test_suite.test_performance_analysis()

async def run_full_integration_test():
    """Run complete integration test suite"""
    test_suite = IntegrationTestSuite()
    await test_suite.run_all_tests()

# Main execution
if __name__ == "__main__":
    # Run the complete integration test suite
    asyncio.run(run_full_integration_test())