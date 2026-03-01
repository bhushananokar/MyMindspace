# component6/conversation_manager.py (COMPLETE FIXED VERSION - CLEAN)
"""
Conversation Manager Module for Component 6.
Main orchestrator for conversation flow and memory integration with real Component 5.
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

# Add project root to path to find comp5_interface
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from shared.schemas import (
    ConversationContext, MemoryContext, UserProfile, EnhancedResponse,
    ProactiveMessage, CommunicationStyle, GeminiRequest
)
from shared.utils import (
    get_logger, log_execution_time, generate_correlation_id,
    with_timeout
)
from configu.settings import settings

from .memory_retriever import MemoryRetriever
from .context_assembler import ContextAssembler
from .gemini_client import GeminiClient
from .personality_engine import PersonalityEngine
from .proactive_engine import ProactiveEngine
from .response_processor import ResponseProcessor

# Import the actual Component 5 interface class
try:
    # Try to import from comp5_interface.py (your bridge file)
    from comp5_interface import Component5Bridge as Component5Interface
except ImportError:
    # Fallback to enhanced interface if comp5_interface doesn't exist
    from .enhanced_comp5_interface import EnhancedComponent5Interface as Component5Interface


class ConversationManager:
    """Main orchestrator for conversation management in Component 6"""
    
    def __init__(self, component5_interface: Optional[Component5Interface] = None):
        """Initialize conversation manager with real Component 5 bridge"""
        self.logger = get_logger("conversation_manager")
        
        # Use the provided Component 5 interface or create a new one
        self.component5_interface = component5_interface or Component5Interface()
        
        # Initialize sub-components with Component 5 interface
        self.memory_retriever = MemoryRetriever(self.component5_interface)
        self.context_assembler = ContextAssembler()
        self.gemini_client = GeminiClient()
        self.personality_engine = PersonalityEngine()
        self.proactive_engine = ProactiveEngine()
        self.response_processor = ResponseProcessor()
        
        # Conversation state tracking
        self.active_conversations = {}
        self.conversation_history = {}
        
        # Performance tracking
        self.conversation_metrics = {
            "total_conversations": 0,
            "active_conversations": 0,
            "avg_response_time_ms": 0.0,
            "success_rate": 0.0,
            "component5_calls": 0,
            "memory_context_successes": 0,
            "successful_conversations": 0
        }
        
        self.logger.info("Conversation Manager initialized with real Component 5")
    
    @log_execution_time
    async def process_conversation(
        self,
        user_id: str,
        user_message: str,
        conversation_id: Optional[str] = None,
        emotional_state: Optional[Dict[str, Any]] = None,
        conversation_goals: Optional[List[str]] = None
    ) -> EnhancedResponse:
        """Process a user message and generate AI response using Component 5 memories"""
        correlation_id = generate_correlation_id()
        self.logger.info(f"Processing conversation for user {user_id}", extra={
            "correlation_id": correlation_id,
            "conversation_id": conversation_id,
            "message_length": len(user_message)
        })
        
        start_time = datetime.utcnow()
        conversation_id = conversation_id or f"conv_{uuid.uuid4()}"
        
        try:
            # Step 1: Get memory context from Component 5 bridge
            memory_context = await self._get_memory_context(
                user_id, user_message, conversation_id
            )
            
            # Step 2: Get user profile
            user_profile = await self._get_user_profile(user_id)
            
            # Step 3: Create conversation context
            conversation_context = await self._create_conversation_context(
                user_id, conversation_id, user_message, memory_context, 
                user_profile, emotional_state, conversation_goals
            )
            
            # Step 4: Assemble context for Gemini API
            gemini_request = await self._assemble_gemini_context(
                conversation_context, user_message
            )
            
            # Step 5: Generate AI response
            ai_response = await self._generate_ai_response(gemini_request)
            
            # Step 6: Update conversation history and memory access
            await self._update_conversation_state(
                conversation_context, user_message, ai_response, memory_context
            )
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_metrics(processing_time, True)
            
            self.logger.info(f"Conversation processed successfully", extra={
                "correlation_id": correlation_id,
                "processing_time_ms": processing_time,
                "memories_used": len(memory_context.selected_memories)
            })
            
            return ai_response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_metrics(processing_time, False)
            
            self.logger.error(f"Conversation processing failed", extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "processing_time_ms": processing_time
            })
            raise
    
    async def _get_memory_context(
        self, 
        user_id: str, 
        user_message: str, 
        conversation_id: str
    ) -> MemoryContext:
        """Get memory context from Component 5 with error handling"""
        try:
            self.conversation_metrics["component5_calls"] += 1
            
            # Call Component 5 interface
            memory_context = await self.component5_interface.get_memory_context(
                user_id=user_id,
                current_message=user_message,
                conversation_id=conversation_id,
                max_memories=settings.performance.max_memories_per_context if hasattr(settings, 'performance') else 10
            )
            
            self.conversation_metrics["memory_context_successes"] += 1
            
            self.logger.info(f"Retrieved {len(memory_context.selected_memories)} memories from Component 5")
            return memory_context
            
        except Exception as e:
            self.logger.error(f"Component 5 memory retrieval failed: {e}")
            
            # Create minimal fallback context
            return MemoryContext(
                selected_memories=[],
                relevance_scores=[],
                token_usage=0,
                assembly_metadata={
                    'error': str(e),
                    'fallback_used': True,
                    'source': 'component5_error_fallback'
                }
            )
    
    async def _get_user_profile(self, user_id: str) -> UserProfile:
        """Get user profile from Component 5 or create default"""
        try:
            if hasattr(self.component5_interface, 'get_user_profile'):
                user_profile = await self.component5_interface.get_user_profile(user_id)
                if user_profile:
                    return user_profile
            
        except Exception as e:
            self.logger.warning(f"Could not get user profile from Component 5: {e}")
        
        # Create default user profile
        return UserProfile(
            user_id=user_id,
            communication_style=CommunicationStyle.FRIENDLY,
            preferred_response_length="moderate",
            emotional_matching=True,
            humor_preference=0.7,
            formality_level=0.3,
            conversation_depth=0.8
        )
    
    async def _create_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        memory_context: MemoryContext,
        user_profile: UserProfile,
        emotional_state: Optional[Dict[str, Any]] = None,
        conversation_goals: Optional[List[str]] = None
    ) -> ConversationContext:
        """Create conversation context from all available information"""
        try:
            # Get recent conversation history if available
            recent_history = self.conversation_history.get(conversation_id, [])
            
            # Create conversation context
            conversation_context = ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id,
                personality_profile=user_profile,
                memories=memory_context.selected_memories,
                emotional_state=emotional_state or {},
                recent_history=recent_history[-5:],  # Last 5 messages
                conversation_goals=conversation_goals or []
            )
            
            self.logger.debug(f"Created conversation context with {len(memory_context.selected_memories)} memories")
            return conversation_context
            
        except Exception as e:
            self.logger.error(f"Error creating conversation context: {e}")
            # Create minimal fallback context
            return ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id,
                personality_profile=user_profile,
                memories=[],
                emotional_state=emotional_state or {},
                recent_history=[],
                conversation_goals=conversation_goals or []
            )
    
    async def _assemble_gemini_context(
        self,
        conversation_context: ConversationContext,
        user_message: str
    ) -> GeminiRequest:
        """Assemble context for Gemini API request"""
        try:
            # Use context assembler to create Gemini request
            gemini_request = await self.context_assembler.assemble_context(
                conversation_context=conversation_context,
                current_message=user_message,
                target_tokens=2000
            )
            
            self.logger.debug(f"Assembled Gemini context with token budget: {gemini_request.token_budget}")
            return gemini_request
            
        except Exception as e:
            self.logger.error(f"Error assembling Gemini context: {e}")
            # Create minimal fallback request
            return GeminiRequest(
                conversation_id=conversation_context.conversation_id,
                user_id=conversation_context.user_id,
                system_prompt="You are a helpful AI assistant.",
                context_section="",
                conversation_history="",
                current_message=user_message,
                response_guidelines="Provide helpful and engaging responses.",
                api_parameters={
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.9
                },
                user_preferences={},
                token_budget=2000
            )
    
    async def _generate_ai_response(self, gemini_request: GeminiRequest) -> EnhancedResponse:
        """Generate AI response using Gemini API"""
        try:
            # Generate response using Gemini client
            gemini_response = await self.gemini_client.generate_response(gemini_request)
            
            if not gemini_response:
                raise Exception("Gemini client returned empty response")
            
            # The Gemini client already returns an EnhancedResponse, just return it
            self.logger.debug(f"Generated AI response")
            return gemini_response
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            # Create fallback response with ALL required fields
            return EnhancedResponse(
                response_id=f"resp_{uuid.uuid4().hex[:8]}",
                conversation_id=gemini_request.conversation_id,
                user_id=gemini_request.user_id,
                original_response="I apologize for the technical difficulty.",
                enhanced_response="I apologize, but I'm having trouble generating a response right now. Could you please try again?",
                enhancement_metadata={
                    'error': str(e),
                    'fallback_used': True,
                    'timestamp': datetime.utcnow().isoformat()
                },
                processing_timestamp=datetime.utcnow(),
                quality_metrics={'overall_quality': 0.5},
                safety_checks={'passed': True},
                context_usage={'utilized': False},
                response_metadata={
                    'fallback_used': True,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                },
                follow_up_suggestions=[
                    "Could you rephrase your question?",
                    "Is there something specific I can help you with?"
                ],
                proactive_suggestions=[],
                memory_context_metadata={'memories_used': 0},
                response_analysis=None
            )
    
    async def _update_conversation_state(
        self,
        conversation_context: ConversationContext,
        user_message: str,
        ai_response: EnhancedResponse,
        memory_context: MemoryContext
    ):
        """Update conversation history and state tracking"""
        try:
            conversation_id = conversation_context.conversation_id
            
            # Update conversation history
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            # Add user message and AI response to history
            self.conversation_history[conversation_id].extend([
                {
                    'role': 'user',
                    'content': user_message,
                    'timestamp': datetime.utcnow().isoformat()
                },
                {
                    'role': 'assistant', 
                    'content': ai_response.enhanced_response,
                    'timestamp': datetime.utcnow().isoformat()
                }
            ])
            
            # Keep only recent history (last 20 messages)
            self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-20:]
            
            # Update active conversations
            self.active_conversations[conversation_id] = {
                'user_id': conversation_context.user_id,
                'last_activity': datetime.utcnow(),
                'message_count': len(self.conversation_history[conversation_id])
            }
            
            self.logger.debug(f"Updated conversation state for {conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating conversation state: {e}")
    
    def _update_metrics(self, processing_time_ms: float, success: bool):
        """Update conversation processing metrics"""
        try:
            self.conversation_metrics["total_conversations"] += 1
            
            if success:
                self.conversation_metrics["successful_conversations"] += 1
            
            # Update average response time
            total_conversations = self.conversation_metrics["total_conversations"]
            current_avg = self.conversation_metrics["avg_response_time_ms"]
            self.conversation_metrics["avg_response_time_ms"] = (
                (current_avg * (total_conversations - 1) + processing_time_ms) / total_conversations
            )
            
            # Update success rate
            self.conversation_metrics["success_rate"] = (
                self.conversation_metrics["successful_conversations"] / total_conversations
            )
            
            # Update active conversations count
            self.conversation_metrics["active_conversations"] = len(self.active_conversations)
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get conversation manager performance metrics"""
        component5_success_rate = 0.0
        if self.conversation_metrics["component5_calls"] > 0:
            component5_success_rate = (
                self.conversation_metrics["memory_context_successes"] / 
                self.conversation_metrics["component5_calls"]
            )
        
        return {
            **self.conversation_metrics,
            "component5_success_rate": component5_success_rate,
            "memory_retrieval_stats": self.memory_retriever.get_retrieval_statistics() if hasattr(self.memory_retriever, 'get_retrieval_statistics') else {}
        }
    
    async def initiate_proactive_conversation(self, user_id: str) -> Optional[ProactiveMessage]:
        """Initiate proactive conversation with user"""
        try:
            return await self.proactive_engine.generate_proactive_message(user_id)
        except Exception as e:
            self.logger.error(f"Error initiating proactive conversation: {e}")
            return None
    
    async def cleanup_inactive_conversations(self, max_age_hours: int = 24):
        """Clean up inactive conversations older than specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            inactive_conversations = [
                conv_id for conv_id, conv_data in self.active_conversations.items()
                if conv_data['last_activity'] < cutoff_time
            ]
            
            for conv_id in inactive_conversations:
                del self.active_conversations[conv_id]
                if conv_id in self.conversation_history:
                    del self.conversation_history[conv_id]
            
            self.logger.info(f"Cleaned up {len(inactive_conversations)} inactive conversations")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up conversations: {e}")