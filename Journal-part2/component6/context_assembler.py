"""
Context Assembler Module for Component 6.
Handles prompt engineering, token management, and context optimization.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from matplotlib import text
import yaml
from pathlib import Path

from shared.schemas import (
    MemoryContext, MemoryItem, UserProfile, ConversationContext,
    GeminiRequest, CommunicationStyle, EmotionalTone
)
from shared.utils import (
    get_logger, log_execution_time, generate_correlation_id,
    TokenCounter, clean_text, extract_keywords, summarize_text
)
from configu.settings import settings

class ContextAssembler:
    """Assembles conversation context for optimal Gemini prompts"""
    
    def __init__(self, prompts_config_path: Optional[str] = None):
        """Initialize context assembler"""
        self.logger = get_logger("context_assembler")
        self.token_counter = TokenCounter()
        self.prompts_config = self._load_prompts_config(prompts_config_path)
        self.template_cache = {}
        
        # Performance tracking
        self.assembly_times = []
        self.token_usage_stats = []
        
        self.logger.info("Context Assembler initialized")
    
    def _build_memories_section(self, memories: List[Any]) -> str:
        """Build memories section with proper error handling"""
        if not memories:
            return "No relevant memories found."
        
        memories_text = []
        for i, memory in enumerate(memories, 1):
            try:
                # Handle both dict and object formats
                if isinstance(memory, dict):
                    memory_type = memory.get('memory_type', 'unknown')
                    content = memory.get('content_summary', str(memory))
                    importance = memory.get('importance_score', 0.5)
                else:
                    # Handle MemoryItem objects
                    memory_type = getattr(memory, 'memory_type', 'unknown')
                    content = getattr(memory, 'content_summary', str(memory))
                    importance = getattr(memory, 'importance_score', 0.5)
                
                memories_text.append(
                    f"Memory {i} ({memory_type}): {content} [Relevance: {importance:.2f}]"
                )
                
            except Exception as e:
                # Fallback for any memory format issues
                memories_text.append(f"Memory {i}: {str(memory)[:100]}...")
        
        return "\n".join(memories_text)

    def _load_prompts_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load prompt templates configuration"""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)
            except Exception as e:
                self.logger.warning(f"Failed to load prompts config: {e}, using defaults")
        
        # Return default configuration
        return {
            "system_prompts": {
                "default": {
                    "name": "Default AI Personality",
                    "content": "You are an intelligent, empathetic AI companion designed to help users with personal journaling, reflection, and meaningful conversations."
                }
            },
            "context_templates": {
                "memory_integration": {
                    "name": "Memory Context Integration",
                    "content": "User Context and Memories:\n{memories_section}\n\nCurrent Emotional State: {emotional_state}\nCommunication Preferences: {communication_style}"
                }
            }
        }
    
    @log_execution_time
    async def assemble_context(
        self,
        conversation_context: ConversationContext,
        current_message: str,
        target_tokens: int = 2000
    ) -> GeminiRequest:
        """Assemble complete context for Gemini API request"""
        correlation_id = generate_correlation_id()
        self.logger.info(f"Assembling context for conversation {conversation_context.conversation_id}", extra={
            "correlation_id": correlation_id,
            "user_id": conversation_context.user_id,
            "target_tokens": target_tokens
        })
        
        start_time = datetime.utcnow()
        
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(conversation_context.personality_profile)
            
            # Build context section
            context_section = await self._build_context_section(
                conversation_context, current_message, target_tokens
            )
            
            # Build conversation history
            conversation_history = self._build_conversation_history(
                conversation_context.recent_history
            )
            
            # Build response guidelines
            response_guidelines = self._build_response_guidelines(
                conversation_context.personality_profile
            )
            
            # Build API parameters
            api_parameters = self._build_api_parameters(conversation_context)
            
            # Build user preferences
            user_preferences = self._build_user_preferences(conversation_context.personality_profile)
            
            # Create Gemini request
            gemini_request = GeminiRequest(
                conversation_id=conversation_context.conversation_id,
                user_id=conversation_context.user_id,
                system_prompt=system_prompt,
                context_section=context_section,
                conversation_history=conversation_history,
                current_message=current_message,
                response_guidelines=response_guidelines,
                api_parameters=api_parameters,
                user_preferences=user_preferences,
                token_budget=target_tokens
            )
            
            # Validate token usage
            total_tokens = self._calculate_total_tokens(gemini_request)
            if total_tokens > target_tokens:
                self.logger.warning(f"Context exceeds token budget: {total_tokens}/{target_tokens}")
                gemini_request = await self._optimize_context(gemini_request, target_tokens)
            
            # Update performance metrics
            self._update_performance_metrics(start_time, total_tokens)
            
            self.logger.info(f"Context assembled successfully", extra={
                "correlation_id": correlation_id,
                "total_tokens": total_tokens,
                "target_tokens": target_tokens,
                "memories_count": len(conversation_context.memories)
            })
            
            return gemini_request
            
        except Exception as e:
            self.logger.error(f"Failed to assemble context: {e}", extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "conversation_id": conversation_context.conversation_id
            })
            raise
    
    def _build_system_prompt(self, user_profile: UserProfile) -> str:
        """Build system prompt based on user profile"""
        # Get base system prompt
        base_prompt = self.prompts_config["system_prompts"]["default"]["content"]
        
        # Customize based on communication style
        style_customizations = {
            CommunicationStyle.FORMAL: "Maintain a formal, respectful tone throughout our conversation.",
            CommunicationStyle.CASUAL: "Feel free to use casual, friendly language as if talking to a good friend.",
            CommunicationStyle.PROFESSIONAL: "Keep responses professional and focused on practical solutions.",
            CommunicationStyle.FRIENDLY: "Be warm, approachable, and genuinely interested in helping.",
            CommunicationStyle.HUMOROUS: "Include appropriate humor and lightheartedness when suitable.",
            CommunicationStyle.DIRECT: "Provide direct, straightforward responses without unnecessary elaboration.",
            CommunicationStyle.ELABORATE: "Give detailed, comprehensive responses that thoroughly address topics."
        }
        
        style_instruction = style_customizations.get(
            user_profile.communication_style,
            style_customizations[CommunicationStyle.FRIENDLY]
        )
        
        # Add emotional matching instruction
        emotional_instruction = ""
        if user_profile.emotional_matching:
            emotional_instruction = "Adapt your emotional tone to complement the user's current emotional state."
        
        # Combine all parts
        system_prompt = f"{base_prompt}\n\n{style_instruction}"
        if emotional_instruction:
            system_prompt += f"\n{emotional_instruction}"
        
        return system_prompt
    
    async def _build_context_section(
    self,
    conversation_context: ConversationContext,
    current_message: str,
    target_tokens: int
) -> str:
        """Build context section with memories and user state"""
        context_parts = []
        
        # Add memories section with error handling
        try:
            if conversation_context.memories:
                memories_text = self._format_memories_for_context(
                    conversation_context.memories,
                    target_tokens // 2  # Reserve half tokens for memories
                )
                context_parts.append(f"Relevant Memories:\n{memories_text}")
        except Exception as e:
            self.logger.error(f"Error formatting memories: {e}")
            context_parts.append("Relevant Memories:\nMemory formatting temporarily unavailable.")
        
        # Add emotional state
        if conversation_context.emotional_state:
            try:
                emotional_text = self._format_emotional_state(
                    conversation_context.emotional_state
                )
                context_parts.append(f"Current Emotional State:\n{emotional_text}")
            except Exception as e:
                self.logger.warning(f"Error formatting emotional state: {e}")
        
        # Add personality profile highlights
        try:
            personality_text = self._format_personality_highlights(
                conversation_context.personality_profile
            )
            context_parts.append(f"Communication Preferences:\n{personality_text}")
        except Exception as e:
            self.logger.warning(f"Error formatting personality: {e}")
        
        # Add conversation goals if available
        if conversation_context.conversation_goals:
            try:
                goals_text = "Conversation Goals:\n" + "\n".join(
                    f"- {goal}" for goal in conversation_context.conversation_goals
                )
                context_parts.append(goals_text)
            except Exception as e:
                self.logger.warning(f"Error formatting goals: {e}")
        
        # Combine all parts
        context_section = "\n\n".join(context_parts) if context_parts else "Context information temporarily unavailable."
        
        return context_section
    
    def _format_memories_for_context(
    self,
    memories: List[Any],  # Change from List[MemoryItem] to List[Any]
    max_tokens: int
) -> str:
        """Format memories for context inclusion with dict/object compatibility"""
        if not memories:
            return "No relevant memories available."
        
        memory_texts = []
        current_tokens = 0
        
        for i, memory in enumerate(memories):
            try:
                # Handle both dict and object formats safely
                if isinstance(memory, dict):
                    memory_type = memory.get('memory_type', 'unknown')
                    content = memory.get('content_summary', str(memory))
                    importance = memory.get('importance_score', 0.5)
                    created_at = memory.get('created_at', 'unknown')
                else:
                    # Handle object format
                    memory_type = getattr(memory, 'memory_type', 'unknown')
                    content = getattr(memory, 'content_summary', str(memory))
                    importance = getattr(memory, 'importance_score', 0.5)
                    created_at = getattr(memory, 'created_at', 'unknown')
                
                # Format memory entry
                memory_text = f"Memory {i+1} ({memory_type}): {content} [Relevance: {importance:.2f}]"
                
                # Check token limit
                memory_tokens = self._estimate_tokens(memory_text)
                if current_tokens + memory_tokens > max_tokens and memory_texts:
                    break
                
                memory_texts.append(memory_text)
                current_tokens += memory_tokens
                
            except Exception as e:
                # Fallback for any problematic memory
                self.logger.warning(f"Error formatting memory {i}: {e}")
                fallback_text = f"Memory {i+1}: {str(memory)[:50]}..."
                memory_texts.append(fallback_text)
        
        return "\n".join(memory_texts) if memory_texts else "No memories could be formatted."
   
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation - 1 token per 4 characters"""
        return len(text) // 4
    
    def _format_single_memory(self, memory: MemoryItem) -> str:
        """Format a single memory for context"""
        template = """Memory: {type} - {summary}
Importance: {importance}/10
Emotional Significance: {emotional}/10
Last Accessed: {last_accessed}
Related Topics: {topics}"""
        
        return template.format(
            type=memory.memory_type,
            summary=memory.content_summary,
            importance=int(memory.importance_score * 10),
            emotional=int(memory.emotional_significance * 10),
            last_accessed=self._format_timestamp(memory.last_accessed),
            topics=', '.join(memory.retrieval_triggers[:3])  # Limit topics
        )
    
    def _format_emotional_state(self, emotional_state: Dict[str, Any]) -> str:
        """Format emotional state for context"""
        if not emotional_state:
            return "Emotional state not available."
        
        parts = []
        
        if 'primary_emotion' in emotional_state:
            parts.append(f"Primary Emotion: {emotional_state['primary_emotion']}")
        
        if 'intensity' in emotional_state:
            intensity = emotional_state['intensity']
            intensity_desc = "low" if intensity < 0.4 else "moderate" if intensity < 0.7 else "high"
            parts.append(f"Intensity: {intensity_desc} ({intensity:.1f}/1.0)")
        
        if 'mood' in emotional_state:
            parts.append(f"Mood: {emotional_state['mood']}")
        
        if 'stress_level' in emotional_state:
            stress = emotional_state['stress_level']
            stress_desc = "low" if stress < 4 else "moderate" if stress < 7 else "high"
            parts.append(f"Stress Level: {stress_desc} ({stress}/10)")
        
        return "\n".join(parts)
    
    def _format_personality_highlights(self, user_profile: UserProfile) -> str:
        """Format key personality traits for context"""
        parts = []
        
        parts.append(f"Communication Style: {user_profile.communication_style.value}")
        parts.append(f"Response Length Preference: {user_profile.preferred_response_length}")
        
        if user_profile.humor_preference > 0.6:
            parts.append("Humor: Welcomed and appreciated")
        elif user_profile.humor_preference < 0.4:
            parts.append("Humor: Minimal, focus on practical help")
        
        if user_profile.formality_level > 0.7:
            parts.append("Tone: Formal and respectful")
        elif user_profile.formality_level < 0.3:
            parts.append("Tone: Casual and friendly")
        
        if user_profile.conversation_depth > 0.7:
            parts.append("Depth: Prefers deep, meaningful discussions")
        elif user_profile.conversation_depth < 0.4:
            parts.append("Depth: Prefers concise, practical responses")
        
        return "\n".join(parts)
    
    def _build_conversation_history(
        self,
        recent_history: List[Dict[str, Any]],
        max_exchanges: int = 5
    ) -> str:
        """Build conversation history section"""
        if not recent_history:
            return "No recent conversation history."
        
        # Take last N exchanges
        recent_exchanges = recent_history[-max_exchanges:]
        
        history_parts = []
        for exchange in recent_exchanges:
            user_message = exchange.get('user_message', '')
            ai_response = exchange.get('ai_response', '')
            
            if user_message and ai_response:
                history_parts.append(f"User: {user_message}")
                history_parts.append(f"AI: {ai_response}")
        
        if not history_parts:
            return "No recent conversation history."
        
        return "\n".join(history_parts)
    
    def _build_response_guidelines(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Build response guidelines based on user profile"""
        guidelines = {
            "communication_style": user_profile.communication_style.value,
            "response_length": user_profile.preferred_response_length,
            "emotional_matching": user_profile.emotional_matching,
            "humor_level": user_profile.humor_preference,
            "formality_level": user_profile.formality_level,
            "conversation_depth": user_profile.conversation_depth
        }
        
        # Add specific instructions
        if user_profile.preferred_response_length == "brief":
            guidelines["max_words"] = 100
        elif user_profile.preferred_response_length == "moderate":
            guidelines["max_words"] = 300
        else:  # detailed
            guidelines["max_words"] = 800
        
        return guidelines
    
    def _build_api_parameters(self, conversation_context: ConversationContext) -> Dict[str, Any]:
        """Build Gemini API parameters"""
        return {
            "model": settings.gemini_api.model_name,
            "temperature": settings.gemini_api.temperature,
            "top_p": settings.gemini_api.top_p,
            "top_k": settings.gemini_api.top_k,
            "max_tokens": settings.gemini_api.max_tokens,
            "safety_settings": settings.gemini_api.safety_settings
        }
    
    def _build_user_preferences(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Build user preferences for response generation"""
        return {
            "user_id": user_profile.user_id,
            "communication_style": user_profile.communication_style.value,
            "cultural_context": user_profile.cultural_context,
            "proactive_engagement": user_profile.proactive_engagement,
            "last_updated": user_profile.last_updated.isoformat()
        }
    
    def _calculate_total_tokens(self, gemini_request: GeminiRequest) -> int:
        """Calculate total token usage for the request"""
        sections = [
            gemini_request.system_prompt,
            gemini_request.context_section,
            gemini_request.conversation_history,
            gemini_request.current_message
        ]
        
        return self.token_counter.count_tokens_list(sections)
    
    async def _optimize_context(
        self,
        gemini_request: GeminiRequest,
        target_tokens: int
    ) -> GeminiRequest:
        """Optimize context to fit within token budget"""
        self.logger.info(f"Optimizing context to fit {target_tokens} tokens")
        
        # Start with system prompt (essential)
        system_tokens = self.token_counter.count_tokens(gemini_request.system_prompt)
        remaining_tokens = target_tokens - system_tokens
        
        if remaining_tokens <= 0:
            # Even system prompt is too long, truncate it
            gemini_request.system_prompt = self.token_counter.truncate_to_tokens(
                gemini_request.system_prompt, target_tokens
            )
            return gemini_request
        
        # Optimize context section
        context_tokens = self.token_counter.count_tokens(gemini_request.context_section)
        if context_tokens > remaining_tokens * 0.6:
            gemini_request.context_section = self._compress_context_section(
                gemini_request.context_section, int(remaining_tokens * 0.6)
            )
        
        # Optimize conversation history
        history_tokens = self.token_counter.count_tokens(gemini_request.conversation_history)
        remaining_after_context = remaining_tokens - self.token_counter.count_tokens(gemini_request.context_section)
        
        if history_tokens > remaining_after_context * 0.3:
            gemini_request.conversation_history = self._compress_conversation_history(
                gemini_request.conversation_history, int(remaining_after_context * 0.3)
            )
        
        return gemini_request
    
    def _compress_context_section(self, context: str, max_tokens: int) -> str:
        """Compress context section to fit token budget"""
        if self.token_counter.count_tokens(context) <= max_tokens:
            return context
        
        # Try to compress by summarizing sections
        sections = context.split('\n\n')
        compressed_sections = []
        current_tokens = 0
        
        for section in sections:
            section_tokens = self.token_counter.count_tokens(section)
            if current_tokens + section_tokens <= max_tokens:
                compressed_sections.append(section)
                current_tokens += section_tokens
            else:
                # Try to add a compressed version
                compressed_section = summarize_text(section, 100)
                compressed_tokens = self.token_counter.count_tokens(compressed_section)
                
                if current_tokens + compressed_tokens <= max_tokens:
                    compressed_sections.append(f"{compressed_section} (compressed)")
                    current_tokens += compressed_tokens
        
        return '\n\n'.join(compressed_sections)
    
    def _compress_conversation_history(self, history: str, max_tokens: int) -> str:
        """Compress conversation history to fit token budget"""
        if self.token_counter.count_tokens(history) <= max_tokens:
            return history
        
        # Split into exchanges and keep most recent
        exchanges = history.split('\n')
        compressed_exchanges = []
        current_tokens = 0
        
        # Process exchanges in reverse order (most recent first)
        for exchange in reversed(exchanges):
            if not exchange.strip():
                continue
                
            exchange_tokens = self.token_counter.count_tokens(exchange)
            if current_tokens + exchange_tokens <= max_tokens:
                compressed_exchanges.insert(0, exchange)
                current_tokens += exchange_tokens
            else:
                break
        
        if not compressed_exchanges:
            return "Recent conversation history available (compressed for space)."
        
        return '\n'.join(compressed_exchanges)
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format timestamp for display"""
        now = datetime.utcnow()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    
    def _update_performance_metrics(self, start_time: datetime, token_count: int) -> None:
        """Update performance tracking metrics"""
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.assembly_times.append(processing_time)
        self.token_usage_stats.append(token_count)
        
        # Keep only last 100 measurements
        if len(self.assembly_times) > 100:
            self.assembly_times = self.assembly_times[-100:]
        if len(self.token_usage_stats) > 100:
            self.token_usage_stats = self.token_usage_stats[-100:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        if not self.assembly_times:
            return {
                "avg_assembly_time_ms": 0.0,
                "avg_token_usage": 0.0,
                "total_assemblies": 0
            }
        
        return {
            "avg_assembly_time_ms": sum(self.assembly_times) / len(self.assembly_times),
            "min_assembly_time_ms": min(self.assembly_times),
            "max_assembly_time_ms": max(self.assembly_times),
            "avg_token_usage": sum(self.token_usage_stats) / len(self.token_usage_stats),
            "total_assemblies": len(self.assembly_times)
        }
    
    def clear_cache(self) -> None:
        """Clear template cache"""
        self.template_cache.clear()
        self.logger.info("Template cache cleared")
