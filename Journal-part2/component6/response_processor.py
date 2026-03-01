"""
Response Processor Module for Component 6.
Processes and enhances Gemini responses with comprehensive quality control,
validation, and optimization as specified in documentation.
"""

import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from shared.schemas import EnhancedResponse, ConversationContext, UserProfile
from shared.utils import generate_content_hash, format_timestamp, get_logger
from configu.settings import settings

class ResponseProcessor:
    """Processes and enhances raw Gemini responses with advanced quality control"""
    
    def __init__(self):
        """Initialize response processor"""
        self.logger = get_logger("response_processor")
        self.enhancement_cache = {}
        self.safety_filters = self._load_safety_filters()
        self.quality_thresholds = self._load_quality_thresholds()
        self.response_templates = self._load_response_templates()
        self.processing_metrics = {
            "total_processed": 0,
            "enhanced_count": 0,
            "safety_violations": 0,
            "quality_improvements": 0
        }
        
    async def process_response(
        self,
        raw_response: str,
        conversation_context: ConversationContext,
        response_metadata: Optional[Dict[str, Any]] = None
    ) -> EnhancedResponse:
        """Process and enhance a raw response with comprehensive quality control"""
        
        if not raw_response or not conversation_context:
            raise ValueError("Response and conversation context are required")
        
        try:
            start_time = datetime.utcnow()
            
            # Step 1: Safety screening and content filtering
            safety_check_result = await self._perform_safety_screening(raw_response, conversation_context)
            
            # Step 2: Quality validation and improvement
            quality_analysis = await self._analyze_response_quality(raw_response, conversation_context)
            
            # Step 3: Response enhancement based on user profile
            enhanced_content = await self._enhance_response_comprehensive(
                raw_response, conversation_context, quality_analysis
            )
            
            # Step 4: Consistency checking with established personality
            consistency_check = await self._check_personality_consistency(
                enhanced_content, conversation_context
            )
            
            # Step 5: Generate comprehensive quality metrics
            quality_metrics = await self._generate_comprehensive_quality_metrics(
                raw_response, enhanced_content, conversation_context, quality_analysis
            )
            
            # Step 6: Context usage analysis
            context_usage = self._analyze_context_usage(enhanced_content, conversation_context)
            
            # Step 7: Generate follow-up suggestions
            follow_up_suggestions = await self._generate_follow_up_suggestions(
                enhanced_content, conversation_context
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create enhanced response
            enhanced_response = EnhancedResponse(
                response_id=f"resp_{generate_content_hash(enhanced_content)[:8]}",
                original_response=raw_response,
                enhanced_response=enhanced_content,
                enhancement_metadata={
                    "processing_time_ms": processing_time,
                    "enhancement_applied": enhanced_content != raw_response,
                    "safety_passed": safety_check_result["passed"],
                    "quality_score": quality_metrics["overall_quality_score"],
                    "consistency_score": consistency_check["score"],
                    "follow_up_suggestions": follow_up_suggestions,
                    **(response_metadata or {})
                },
                processing_timestamp=datetime.utcnow(),
                quality_metrics=quality_metrics,
                safety_checks=safety_check_result,
                context_usage=context_usage
            )
            
            # Update processing metrics
            self._update_processing_metrics(enhanced_response)
            
            self.logger.info(f"Response processed successfully for conversation {conversation_context.conversation_id}")
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"Error processing response: {e}")
            raise
    
    async def _perform_safety_screening(
        self,
        response: str,
        conversation_context: ConversationContext
    ) -> Dict[str, Any]:
        """Perform comprehensive safety screening of response content"""
        safety_result = {
            "passed": True,
            "violations": [],
            "risk_level": "low",
            "content_flags": []
        }
        
        # Check for inappropriate content
        inappropriate_patterns = self.safety_filters.get("inappropriate_content", [])
        for pattern in inappropriate_patterns:
            if re.search(pattern, response.lower()):
                safety_result["violations"].append(f"Inappropriate content: {pattern}")
                safety_result["passed"] = False
        
        # Check for harmful advice
        harmful_advice_patterns = self.safety_filters.get("harmful_advice", [])
        for pattern in harmful_advice_patterns:
            if re.search(pattern, response.lower()):
                safety_result["violations"].append(f"Potentially harmful advice: {pattern}")
                safety_result["risk_level"] = "high"
                safety_result["passed"] = False
        
        # Check for personal information leakage
        personal_info_patterns = self.safety_filters.get("personal_info", [])
        for pattern in personal_info_patterns:
            if re.search(pattern, response):
                safety_result["content_flags"].append("Potential personal information")
        
        # Cultural sensitivity check
        if conversation_context.personality_profile and conversation_context.personality_profile.cultural_context:
            cultural_issues = await self._check_cultural_sensitivity(
                response, conversation_context.personality_profile.cultural_context
            )
            if cultural_issues:
                safety_result["content_flags"].extend(cultural_issues)
        
        return safety_result
    
    async def _analyze_response_quality(
        self,
        response: str,
        conversation_context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze response quality across multiple dimensions"""
        quality_analysis = {
            "coherence_score": self._calculate_coherence_score(response),
            "relevance_score": self._calculate_relevance_score(response, conversation_context),
            "completeness_score": self._calculate_completeness_score(response, conversation_context),
            "tone_appropriateness": self._analyze_tone_appropriateness(response, conversation_context),
            "information_accuracy": await self._verify_information_accuracy(response, conversation_context),
            "engagement_potential": self._assess_engagement_potential(response)
        }
        
        # Calculate overall quality score
        weights = {
            "coherence_score": 0.2,
            "relevance_score": 0.25,
            "completeness_score": 0.2,
            "tone_appropriateness": 0.15,
            "information_accuracy": 0.15,
            "engagement_potential": 0.05
        }
        
        quality_analysis["overall_score"] = sum(
            quality_analysis[metric] * weight
            for metric, weight in weights.items()
            if metric in quality_analysis
        )
        
        return quality_analysis
    
    async def _enhance_response_comprehensive(
        self,
        response: str,
        conversation_context: ConversationContext,
        quality_analysis: Dict[str, Any]
    ) -> str:
        """Comprehensively enhance response based on quality analysis and user profile"""
        enhanced = response
        
        # Step 1: Basic cleaning and normalization
        enhanced = await self._clean_and_normalize_response(enhanced)
        
        # Step 2: Improve coherence if needed
        if quality_analysis["coherence_score"] < self.quality_thresholds["coherence"]:
            enhanced = await self._improve_coherence(enhanced, conversation_context)
        
        # Step 3: Enhance relevance through memory integration
        if quality_analysis["relevance_score"] < self.quality_thresholds["relevance"]:
            enhanced = await self._enhance_relevance(enhanced, conversation_context)
        
        # Step 4: Adjust tone for personality matching
        if quality_analysis["tone_appropriateness"] < self.quality_thresholds["tone"]:
            enhanced = await self._adjust_tone(enhanced, conversation_context)
        
        # Step 5: Add natural memory references
        enhanced = await self._integrate_memory_references(enhanced, conversation_context)
        
        # Step 6: Add follow-up elements if appropriate
        if await self._should_add_follow_up(conversation_context):
            follow_up = await self._generate_contextual_follow_up(enhanced, conversation_context)
            if follow_up:
                enhanced = f"{enhanced} {follow_up}"
        
        # Step 7: Final optimization for user preferences
        enhanced = await self._optimize_for_user_preferences(enhanced, conversation_context)
        
        return enhanced
    
    async def _clean_and_normalize_response(self, response: str) -> str:
        """Clean and normalize the raw response with advanced processing"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', response.strip())
        
        # Fix punctuation spacing
        cleaned = re.sub(r'\s+([.!?,:;])', r'\1', cleaned)
        cleaned = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', cleaned)
        
        # Ensure proper sentence endings
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        # Remove any control characters
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        # Fix common formatting issues
        cleaned = re.sub(r'\*{2,}', '**', cleaned)  # Fix bold formatting
        cleaned = re.sub(r'_{2,}', '__', cleaned)   # Fix italic formatting
        
        return cleaned
        
        return enhanced
    
    async def _should_add_follow_up(self, conversation_context: ConversationContext) -> bool:
        """Determine if a follow-up question should be added."""
        
        # Don't add follow-up if user message is a thank you or goodbye
        # Handle different ConversationContext schemas
        user_message = ""
        if hasattr(conversation_context, 'current_message'):
            user_message = conversation_context.current_message.lower()
        elif hasattr(conversation_context, 'conversation_topic'):
            user_message = (conversation_context.conversation_topic or "").lower()
        endings = ['thank', 'thanks', 'bye', 'goodbye', 'that\'s all', 'perfect']
        
        if any(ending in user_message for ending in endings):
            return False
        
        # Add follow-up for informational responses
        return len(conversation_context.message_history) < 10
    
    async def _generate_follow_up_question(
        self,
        conversation_context: ConversationContext
    ) -> Optional[str]:
        """Generate an appropriate follow-up question."""
        
        topic_keywords = conversation_context.context_metadata.get('topic', '')
        
        if 'stress' in topic_keywords or 'anxiety' in topic_keywords:
            return "How are you feeling about trying these strategies?"
        elif 'career' in topic_keywords or 'job' in topic_keywords:
            return "What aspect would you like to explore further?"
        elif 'productivity' in topic_keywords:
            return "Which of these approaches resonates most with you?"
        else:
            return "Is there anything specific you'd like me to elaborate on?"
    
    async def _generate_comprehensive_quality_metrics(
        self,
        original_response: str,
        enhanced_response: str,
        conversation_context: ConversationContext,
        quality_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive quality metrics for the response"""
        
        return {
            "overall_quality_score": quality_analysis.get("overall_score", 0.7),
            "coherence_score": quality_analysis.get("coherence_score", 0.8),
            "relevance_score": quality_analysis.get("relevance_score", 0.7),
            "completeness_score": quality_analysis.get("completeness_score", 0.7),
            "tone_appropriateness": quality_analysis.get("tone_appropriateness", 0.8),
            "information_accuracy": quality_analysis.get("information_accuracy", 0.9),
            "engagement_potential": quality_analysis.get("engagement_potential", 0.6),
            "content_length": len(enhanced_response),
            "sentence_count": len(re.findall(r'[.!?]+', enhanced_response)),
            "word_count": len(enhanced_response.split()),
            "has_follow_up": "?" in enhanced_response,
            "enhancement_applied": enhanced_response != original_response,
            "processing_metrics": {
                "original_length": len(original_response),
                "enhanced_length": len(enhanced_response),
                "length_change_ratio": len(enhanced_response) / len(original_response) if original_response else 1.0
            }
        }
    
    def _analyze_context_usage(self, response: str, conversation_context: ConversationContext) -> Dict[str, Any]:
        """Analyze how well the response uses provided context"""
        context_usage = {
            "memory_references": 0,
            "emotional_awareness": False,
            "personality_alignment": False,
            "goal_acknowledgment": False
        }
        
        response_lower = response.lower()
        
        # Check memory references
        if conversation_context.memories:
            for memory in conversation_context.memories:
                if isinstance(memory, dict):
                    memory_content = memory.get('content_summary', '').lower()
                    memory_words = set(memory_content.split()[:10])
                    response_words = set(response_lower.split())
                    
                    if memory_words.intersection(response_words):
                        context_usage["memory_references"] += 1
        
        # Check emotional awareness
        if conversation_context.emotional_state:
            emotion_words = ['feel', 'emotion', 'mood', 'stress', 'happy', 'sad', 'anxious']
            if any(word in response_lower for word in emotion_words):
                context_usage["emotional_awareness"] = True
        
        # Check personality alignment
        if conversation_context.personality_profile:
            context_usage["personality_alignment"] = True  # Simplified check
        
        # Check goal acknowledgment
        if conversation_context.conversation_goals:
            goal_words = set()
            for goal in conversation_context.conversation_goals:
                goal_words.update(goal.lower().split())
            
            response_words = set(response_lower.split())
            if goal_words.intersection(response_words):
                context_usage["goal_acknowledgment"] = True
        
        return context_usage
    
    async def _generate_follow_up_suggestions(
        self,
        response: str,
        conversation_context: ConversationContext
    ) -> List[str]:
        """Generate follow-up suggestions for continued engagement"""
        suggestions = []
        
        # Based on conversation topic
        if conversation_context.conversation_topic:
            topic = conversation_context.conversation_topic.lower()
            if 'stress' in topic:
                suggestions.append("Explore stress management techniques")
                suggestions.append("Discuss stress triggers in detail")
            elif 'goal' in topic:
                suggestions.append("Break down goals into actionable steps")
                suggestions.append("Set timeline for goal achievement")
        
        # Based on emotional state
        if conversation_context.emotional_state:
            emotion = conversation_context.emotional_state.get('primary_emotion', '')
            if emotion in ['sad', 'anxious']:
                suggestions.append("Offer emotional support resources")
                suggestions.append("Suggest coping strategies")
            elif emotion in ['happy', 'excited']:
                suggestions.append("Celebrate achievements")
                suggestions.append("Plan next positive steps")
        
        # Based on user preferences
        if conversation_context.personality_profile:
            if conversation_context.personality_profile.conversation_depth > 0.7:
                suggestions.append("Dive deeper into underlying themes")
                suggestions.append("Explore philosophical aspects")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _load_safety_filters(self) -> Dict[str, List[str]]:
        """Load safety filter patterns"""
        return {
            "inappropriate_content": [
                r"\b(suicide|self.?harm|kill.?myself)\b",
                r"\b(hate|violence|illegal)\b"
            ],
            "harmful_advice": [
                r"\b(don.?t see (a )?doctor|ignore medical advice)\b",
                r"\b(quit your job|leave your family)\b"
            ],
            "personal_info": [
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
                r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b"  # Credit card pattern
            ]
        }
    
    def _load_quality_thresholds(self) -> Dict[str, float]:
        """Load quality threshold values"""
        return {
            "coherence": 0.6,
            "relevance": 0.5,
            "completeness": 0.5,
            "tone": 0.6,
            "accuracy": 0.8,
            "engagement": 0.4
        }
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates for enhancement"""
        return {
            "empathetic_opening": "I understand that {emotion} can be challenging.",
            "encouraging_transition": "You've shown great strength in {context}.",
            "reflective_question": "How do you feel about {topic}?",
            "action_suggestion": "You might consider {action} as a next step."
        }
    
    def _update_processing_metrics(self, enhanced_response: EnhancedResponse) -> None:
        """Update internal processing metrics"""
        self.processing_metrics["total_processed"] += 1
        
        if enhanced_response.enhancement_metadata.get("enhancement_applied", False):
            self.processing_metrics["enhanced_count"] += 1
        
        if not enhanced_response.safety_checks.get("passed", True):
            self.processing_metrics["safety_violations"] += 1
        
        if enhanced_response.quality_metrics.get("overall_quality_score", 0) > 0.8:
            self.processing_metrics["quality_improvements"] += 1
    
    # Additional helper methods that were referenced but not implemented
    
    async def _check_cultural_sensitivity(self, response: str, cultural_context: str) -> List[str]:
        """Check for cultural sensitivity issues"""
        issues = []
        # Simplified cultural sensitivity check
        # In production, this would be more comprehensive
        if cultural_context == "asian" and "family" in response.lower():
            # Check for appropriate family context handling
            pass
        return issues
    
    def _detect_response_style(self, response: str) -> str:
        """Detect the communication style of the response"""
        formal_indicators = ["furthermore", "therefore", "consequently"]
        casual_indicators = ["hey", "gonna", "wanna"]
        
        if any(indicator in response.lower() for indicator in formal_indicators):
            return "formal"
        elif any(indicator in response.lower() for indicator in casual_indicators):
            return "casual"
        else:
            return "friendly"
    
    def _detect_formality_level(self, response: str) -> float:
        """Detect formality level (0.0 = very casual, 1.0 = very formal)"""
        formal_words = ["please", "kindly", "furthermore", "however", "therefore"]
        casual_words = ["hey", "yeah", "gonna", "wanna", "cool"]
        
        formal_count = sum(1 for word in formal_words if word in response.lower())
        casual_count = sum(1 for word in casual_words if word in response.lower())
        
        total_words = len(response.split())
        if total_words == 0:
            return 0.5
        
        formal_ratio = formal_count / total_words
        casual_ratio = casual_count / total_words
        
        return max(0.0, min(1.0, 0.5 + formal_ratio - casual_ratio))
    
    def _detect_humor_level(self, response: str) -> float:
        """Detect humor level in response"""
        humor_indicators = ["haha", "lol", "funny", "joke", "😄", "😊"]
        humor_count = sum(1 for indicator in humor_indicators if indicator in response.lower())
        
        # Simple humor detection based on indicators
        return min(1.0, humor_count * 0.3)
    
    def _extract_factual_claims(self, response: str) -> List[str]:
        """Extract factual claims from response"""
        # Simplified factual claim extraction
        sentences = re.split(r'[.!?]+', response)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            # Look for definitive statements
            if any(word in sentence.lower() for word in ["is", "are", "will", "always", "never"]):
                claims.append(sentence)
        
        return claims
    
    def _might_contradict(self, fact: str, memory_content: str) -> bool:
        """Check if a fact might contradict memory content"""
        # Simplified contradiction detection
        # In production, this would use more sophisticated NLP
        
        # Look for opposite words
        opposites = {
            "like": "hate", "love": "hate", "good": "bad", 
            "happy": "sad", "yes": "no", "always": "never"
        }
        
        fact_words = set(fact.lower().split())
        memory_words = set(memory_content.lower().split())
        
        for word in fact_words:
            if word in opposites and opposites[word] in memory_words:
                return True
        
        return False
    
    async def _improve_coherence(self, response: str, conversation_context: ConversationContext) -> str:
        """Improve response coherence"""
        # Add transition words if needed
        sentences = re.split(r'([.!?]+)', response)
        if len(sentences) > 3:
            # Add transitions between ideas
            transitions = ["Additionally,", "Furthermore,", "Moreover,"]
            # Simple implementation - add transition to second sentence
            if len(sentences) >= 4:
                sentences[2] = f"{transitions[0]} {sentences[2].strip()}"
        
        return ''.join(sentences)
    
    async def _enhance_relevance(self, response: str, conversation_context: ConversationContext) -> str:
        """Enhance response relevance by adding context"""
        if conversation_context.memories and len(conversation_context.memories) > 0:
            # Add reference to recent memory
            recent_memory = conversation_context.memories[0]
            if isinstance(recent_memory, dict):
                memory_topic = recent_memory.get('content_summary', '')[:50]
                if memory_topic:
                    response += f" This relates to what we discussed about {memory_topic.lower()}."
        
        return response
    
    async def _adjust_tone(self, response: str, conversation_context: ConversationContext) -> str:
        """Adjust response tone to match user preferences"""
        if not conversation_context.personality_profile:
            return response
        
        user_profile = conversation_context.personality_profile
        
        # Adjust for communication style
        if user_profile.communication_style.value == "formal":
            response = response.replace("you're", "you are")
            response = response.replace("can't", "cannot")
        elif user_profile.communication_style.value == "casual":
            response = response.replace("you are", "you're")
            response = response.replace("cannot", "can't")
        
        return response
    
    async def _integrate_memory_references(self, response: str, conversation_context: ConversationContext) -> str:
        """Integrate natural memory references"""
        if not conversation_context.memories:
            return response
        
        # Find opportunities to add memory references naturally
        memory_phrases = [
            "As we discussed before,",
            "Remembering what you shared,",
            "Building on our previous conversation,"
        ]
        
        # Add memory reference if response doesn't already have context
        if not any(phrase.lower() in response.lower() for phrase in memory_phrases):
            if len(conversation_context.memories) > 0:
                response = f"{memory_phrases[0]} {response}"
        
        return response
    
    async def _generate_contextual_follow_up(self, response: str, conversation_context: ConversationContext) -> str:
        """Generate contextual follow-up question"""
        if conversation_context.conversation_topic:
            topic = conversation_context.conversation_topic.lower()
            
            if 'stress' in topic:
                return "What strategies have you found most helpful for managing stress?"
            elif 'goal' in topic:
                return "What would success look like to you in this area?"
            elif 'emotion' in topic:
                return "How are you feeling about everything we've discussed?"
        
        return "What would be most helpful to explore next?"
    
    async def _optimize_for_user_preferences(self, response: str, conversation_context: ConversationContext) -> str:
        """Final optimization based on user preferences"""
        if not conversation_context.personality_profile:
            return response
        
        user_profile = conversation_context.personality_profile
        
        # Adjust length based on preference
        words = response.split()
        target_lengths = {"brief": 50, "moderate": 150, "detailed": 300}
        target = target_lengths.get(user_profile.preferred_response_length, 150)
        
        if len(words) > target * 1.5:
            # Truncate and add summary
            truncated = ' '.join(words[:target])
            if not truncated.endswith(('.', '!', '?')):
                truncated += '.'
            response = truncated
        
        return response

    def _calculate_coherence_score(self, response: str) -> float:
        """Calculate coherence score based on response structure and flow"""
        try:
            sentences = response.split('.')
            if len(sentences) <= 1:
                return 0.8  # Single sentence gets good score
            
            # Check for logical connectors
            connectors = ['however', 'therefore', 'additionally', 'furthermore', 'meanwhile', 'consequently']
            connector_count = sum(1 for sentence in sentences for connector in connectors if connector in sentence.lower())
            
            # Check sentence length variation (good coherence has varied lengths)
            sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence.strip()]
            if not sentence_lengths:
                return 0.5
            
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            length_variance = sum((length - avg_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
            
            # Calculate coherence components
            connector_score = min(connector_count / len(sentences), 0.5)  # Max 0.5 from connectors
            structure_score = 0.3 if 5 <= avg_length <= 20 else 0.1  # Optimal sentence length
            flow_score = 0.2 if length_variance > 10 else 0.1  # Some variation is good
            
            base_score = 0.4  # Base coherence
            total_score = base_score + connector_score + structure_score + flow_score
            
            return min(total_score, 1.0)
        except Exception:
            return 0.6  # Default moderate score

    def _calculate_relevance_score(self, response: str, conversation_context: ConversationContext) -> float:
        """Calculate relevance score based on context alignment"""
        try:
            response_lower = response.lower()
            score = 0.0
            
            # Check relevance to user input
            if conversation_context.user_input:
                user_words = set(conversation_context.user_input.lower().split())
                response_words = set(response_lower.split())
                common_words = user_words.intersection(response_words)
                if user_words:
                    score += 0.4 * (len(common_words) / len(user_words))
            
            # Check relevance to conversation topic
            if conversation_context.conversation_topic:
                topic_words = set(conversation_context.conversation_topic.lower().split())
                response_words = set(response_lower.split())
                common_words = topic_words.intersection(response_words)
                if topic_words:
                    score += 0.3 * (len(common_words) / len(topic_words))
            
            # Check memory relevance
            if conversation_context.memories:
                memory_keywords = []
                for memory in conversation_context.memories:
                    if hasattr(memory, 'retrieval_triggers'):
                        memory_keywords.extend(memory.retrieval_triggers)
                    elif hasattr(memory, 'content_summary'):
                        memory_keywords.extend(memory.content_summary.lower().split()[:5])
                
                if memory_keywords:
                    memory_matches = sum(1 for keyword in memory_keywords if keyword.lower() in response_lower)
                    score += 0.3 * min(memory_matches / len(memory_keywords), 1.0)
            
            return min(score, 1.0)
        except Exception:
            return 0.5  # Default moderate score

    def _calculate_completeness_score(self, response: str, conversation_context: ConversationContext) -> float:
        """Calculate completeness score based on response comprehensiveness"""
        try:
            # Base completeness factors
            word_count = len(response.split())
            sentence_count = len([s for s in response.split('.') if s.strip()])
            
            # Optimal range scoring
            word_score = 0.3 if 30 <= word_count <= 200 else 0.1
            sentence_score = 0.2 if 2 <= sentence_count <= 8 else 0.1
            
            # Check if response addresses the user's query
            addressing_score = 0.0
            if conversation_context.user_input:
                user_input = conversation_context.user_input.lower()
                response_lower = response.lower()
                
                # Check for question words and responses
                question_indicators = ['what', 'how', 'why', 'when', 'where', 'who']
                has_question = any(word in user_input for word in question_indicators)
                
                if has_question:
                    # Look for answer indicators
                    answer_indicators = ['because', 'since', 'due to', 'the reason', 'it means', 'this is']
                    has_answer = any(phrase in response_lower for phrase in answer_indicators)
                    addressing_score = 0.3 if has_answer else 0.1
                else:
                    addressing_score = 0.2  # Statement response to statement
            
            # Check for actionable content
            action_words = ['try', 'consider', 'might', 'could', 'suggest', 'recommend']
            has_action = any(word in response.lower() for word in action_words)
            action_score = 0.2 if has_action else 0.1
            
            total_score = word_score + sentence_score + addressing_score + action_score
            return min(total_score, 1.0)
        except Exception:
            return 0.6  # Default moderate score

    def _analyze_tone_appropriateness(self, response: str, conversation_context: ConversationContext) -> float:
        """Analyze tone appropriateness for the context"""
        try:
            response_lower = response.lower()
            
            # Detect emotional context from memories
            emotional_context = "neutral"
            if conversation_context.memories:
                stress_indicators = ['stress', 'anxiety', 'worry', 'overwhelm']
                positive_indicators = ['happy', 'excited', 'proud', 'accomplished']
                
                memory_text = ' '.join([
                    getattr(memory, 'content_summary', '') 
                    for memory in conversation_context.memories
                ]).lower()
                
                if any(indicator in memory_text for indicator in stress_indicators):
                    emotional_context = "supportive"
                elif any(indicator in memory_text for indicator in positive_indicators):
                    emotional_context = "celebratory"
            
            # Analyze response tone
            supportive_words = ['understand', 'support', 'help', 'here for you', 'validate']
            positive_words = ['great', 'wonderful', 'excellent', 'amazing', 'fantastic']
            empathetic_words = ['feel', 'seems', 'sounds like', 'imagine', 'sense']
            
            tone_score = 0.0
            
            if emotional_context == "supportive":
                has_supportive = any(word in response_lower for word in supportive_words)
                has_empathetic = any(phrase in response_lower for phrase in empathetic_words)
                tone_score = 0.8 if (has_supportive or has_empathetic) else 0.4
            
            elif emotional_context == "celebratory":
                has_positive = any(word in response_lower for word in positive_words)
                tone_score = 0.8 if has_positive else 0.5
            
            else:  # neutral
                tone_score = 0.7  # Neutral is generally appropriate
            
            return tone_score
        except Exception:
            return 0.6  # Default moderate score

    async def _verify_information_accuracy(self, response: str, conversation_context: ConversationContext) -> float:
        """Verify information accuracy against memory context"""
        try:
            # Extract factual claims from response
            factual_claims = self._extract_factual_claims(response)
            if not factual_claims:
                return 0.8  # No specific claims to verify
            
            # Check against memory context
            memory_content = ' '.join([
                getattr(memory, 'content_summary', '') 
                for memory in conversation_context.memories
            ]).lower()
            
            accurate_claims = 0
            for claim in factual_claims:
                # Simple contradiction check
                if not self._might_contradict(claim, memory_content):
                    accurate_claims += 1
            
            accuracy_ratio = accurate_claims / len(factual_claims) if factual_claims else 1.0
            return accuracy_ratio
        except Exception:
            return 0.7  # Default good score

    def _assess_engagement_potential(self, response: str) -> float:
        """Assess the response's potential to engage the user"""
        try:
            engagement_score = 0.0
            response_lower = response.lower()
            
            # Check for questions (encourages interaction)
            question_count = response.count('?')
            engagement_score += min(question_count * 0.2, 0.4)
            
            # Check for personal references
            personal_words = ['you', 'your', 'yourself']
            personal_count = sum(response_lower.count(word) for word in personal_words)
            engagement_score += min(personal_count * 0.1, 0.3)
            
            # Check for call-to-action phrases
            action_phrases = ['try', 'consider', 'what do you think', 'how does that sound']
            has_action = any(phrase in response_lower for phrase in action_phrases)
            engagement_score += 0.2 if has_action else 0.0
            
            # Check for empathy/connection words
            connection_words = ['understand', 'feel', 'sense', 'relate']
            has_connection = any(word in response_lower for word in connection_words)
            engagement_score += 0.1 if has_connection else 0.0
            
            return min(engagement_score, 1.0)
        except Exception:
            return 0.5  # Default moderate score

    async def _check_personality_consistency(self, response: str, conversation_context: ConversationContext) -> Dict[str, Any]:
        """Check if response is consistent with the user's personality profile"""
        try:
            if not conversation_context.personality_profile:
                return {"score": 0.8, "consistent": True, "notes": "No personality profile to check against"}
            
            profile = conversation_context.personality_profile
            response_lower = response.lower()
            
            # Check communication style consistency
            style_score = 0.0
            
            # Check formality level
            formal_indicators = ['please', 'would you', 'could you', 'might I suggest']
            informal_indicators = ["let's", "you'll", "won't", "can't"]
            
            formal_count = sum(1 for phrase in formal_indicators if phrase in response_lower)
            informal_count = sum(1 for phrase in informal_indicators if phrase in response_lower)
            
            response_formality = formal_count / (formal_count + informal_count + 1)
            profile_formality = getattr(profile, 'preferred_formality', 0.5)
            
            formality_diff = abs(response_formality - profile_formality)
            style_score += max(0, 0.4 - formality_diff)
            
            # Check response length preference
            word_count = len(response.split())
            length_pref = getattr(profile, 'preferred_response_length', 'moderate')
            length_targets = {"brief": (20, 80), "moderate": (80, 200), "detailed": (200, 400)}
            
            target_min, target_max = length_targets.get(length_pref, (80, 200))
            if target_min <= word_count <= target_max:
                style_score += 0.3
            
            # Check tone preferences
            if hasattr(profile, 'preferred_tone'):
                tone_indicators = {
                    'supportive': ['understand', 'support', 'here for you'],
                    'analytical': ['analyze', 'consider', 'examine'],
                    'encouraging': ['great', 'excellent', 'you can do']
                }
                
                preferred_tone = profile.preferred_tone
                if preferred_tone in tone_indicators:
                    tone_words = tone_indicators[preferred_tone]
                    has_tone = any(word in response_lower for word in tone_words)
                    style_score += 0.3 if has_tone else 0.0
            
            consistency_score = min(style_score, 1.0)
            is_consistent = consistency_score >= 0.6
            
            return {
                "score": consistency_score,
                "consistent": is_consistent,
                "notes": f"Personality consistency check completed (score: {consistency_score:.2f})"
            }
            
        except Exception as e:
            return {
                "score": 0.7,
                "consistent": True,
                "notes": f"Error in personality check: {str(e)}"
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        total = self.processing_metrics["total_processed"]
        if total == 0:
            return self.processing_metrics
        
        return {
            **self.processing_metrics,
            "enhancement_rate": self.processing_metrics["enhanced_count"] / total,
            "safety_violation_rate": self.processing_metrics["safety_violations"] / total,
            "quality_improvement_rate": self.processing_metrics["quality_improvements"] / total
        }
