# component6/enhanced_conversation_manager.py
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from .enhanced_comp5_interface import EnhancedComponent5Interface
from .gemini_client import GeminiClient
from .context_assembler import ContextAssembler
from .personality_engine import PersonalityEngine
from .response_processor import ResponseProcessor
from shared.schemas import ConversationContext, UserProfile, EnhancedResponse

class EnhancedConversationManager:
    """Enhanced conversation manager with LSTM integration"""
    
    def __init__(self):
        # Component 5 LSTM Interface
        self.lstm_interface = EnhancedComponent5Interface()
        
        # Component 6 modules
        self.gemini_client = GeminiClient()
        self.context_assembler = ContextAssembler()
        self.personality_engine = PersonalityEngine()
        self.response_processor = ResponseProcessor()
        
        # Integration stats
        self.integration_stats = {
            'total_queries': 0,
            'successful_retrievals': 0,
            'gemini_responses': 0,
            'processing_times': []
        }
    
    async def initialize(self):
        """Initialize all components"""
        print("🚀 Initializing Enhanced Conversation Manager...")
        
        # Initialize LSTM interface
        lstm_success = await self.lstm_interface.initialize()
        if not lstm_success:
            raise Exception("Failed to initialize LSTM interface")
        
        print("✅ Enhanced Conversation Manager initialized")
    
    async def process_user_query(self,
                                user_id: str,
                                user_query: str,
                                conversation_id: Optional[str] = None,
                                emotional_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main integration workflow: User Query → LSTM → Gemini → Response
        """
        start_time = datetime.utcnow()
        
        print(f"\n🔄 Processing User Query Integration Pipeline")
        print("=" * 60)
        print(f"User: {user_id}")
        print(f"Query: {user_query}")
        
        try:
            self.integration_stats['total_queries'] += 1
            
            # Step 1: LSTM Memory Retrieval (Component 5)
            print(f"\n📚 Step 1: LSTM Memory Retrieval...")
            memory_context = await self.lstm_interface.get_memory_context_for_query(
                user_id=user_id,
                user_query=user_query,
                max_memories=10
            )
            
            if memory_context.selected_memories:
                self.integration_stats['successful_retrievals'] += 1
                print(f"✅ Retrieved {len(memory_context.selected_memories)} memories")
            else:
                print("⚠️ No memories retrieved")
            
            # Step 2: Build Conversation Context for Gemini
            print(f"\n🧠 Step 2: Building Gemini Context...")
            user_profile = await self._get_or_create_user_profile(user_id)
            
            conversation_context = ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                personality_profile=user_profile,
                memories=memory_context.selected_memories,
                emotional_state=emotional_state or {},
                recent_history=[],
                conversation_goals=[]
            )
            
            # Step 3: Assemble Context for Gemini API
            print(f"\n🔧 Step 3: Assembling Gemini Request...")
            gemini_request = await self.context_assembler.assemble_context(
                conversation_context=conversation_context,
                current_message=user_query,
                target_tokens=2000
            )
            
            # Step 4: Generate Response via Gemini
            print(f"\n🤖 Step 4: Generating Gemini Response...")
            gemini_response = await self.gemini_client.generate_response(gemini_request)
            
            if gemini_response:
                self.integration_stats['gemini_responses'] += 1
                print(f"✅ Gemini response generated")
            else:
                print("❌ Failed to generate Gemini response")
                raise Exception("Gemini response generation failed")
            
            # Step 5: Process and Enhance Response
            print(f"\n✨ Step 5: Processing Response...")
            enhanced_response = await self.response_processor.process_response(
                gemini_response,
                conversation_context,
                user_query
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.integration_stats['processing_times'].append(processing_time)
            
            # Compile final result
            result = {
                'response': enhanced_response.enhanced_response,
                'response_id': enhanced_response.response_id,
                'conversation_id': conversation_context.conversation_id,
                'memories_used': len(memory_context.selected_memories),
                'memory_context': {
                    'retrieved_memories': len(memory_context.selected_memories),
                    'relevance_scores': memory_context.relevance_scores,
                    'token_usage': memory_context.token_usage
                },
                'processing_time_ms': processing_time * 1000,
                'lstm_stats': self.lstm_interface.stats,
                'integration_metadata': {
                    'workflow_steps': [
                        'LSTM Memory Retrieval',
                        'Context Assembly', 
                        'Gemini Response Generation',
                        'Response Processing'
                    ],
                    'components_used': ['Component5_LSTM', 'Component6_Gemini'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            print(f"\n✅ Integration Pipeline Complete!")
            print(f"   📊 Memories Used: {len(memory_context.selected_memories)}")
            print(f"   🤖 Response Generated: {len(enhanced_response.enhanced_response)} chars")
            print(f"   ⏱️ Processing Time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"❌ Integration pipeline failed: {e}")
            
            return {
                'error': str(e),
                'user_id': user_id,
                'user_query': user_query,
                'processing_time_ms': processing_time * 1000,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _get_or_create_user_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile for personality engine"""
        # Try to get existing profile
        user_profile = await self.personality_engine.get_user_profile(user_id)
        
        if not user_profile:
            # Create default profile
            from shared.schemas import CommunicationStyle
            user_profile = UserProfile(
                user_id=user_id,
                communication_style=CommunicationStyle.FRIENDLY,
                preferred_response_length="moderate",
                emotional_matching=True,
                humor_preference=0.7,
                formality_level=0.3,
                conversation_depth=0.8,
                proactive_engagement=True
            )
        
        return user_profile
