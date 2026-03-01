"""
Personality Engine Module for Component 6.
Handles AI personality adaptation and communication style management with
cultural adaptation and response pattern learning as specified in documentation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from shared.schemas import UserProfile, ConversationContext, CommunicationStyle
from shared.utils import get_logger, generate_correlation_id, SimpleCache
from configu.settings import settings


class PersonalityEngine:
    """Manages AI personality adaptation and communication style with advanced features"""
    
    def __init__(self):
        """Initialize personality engine"""
        self.logger = get_logger("personality_engine")
        self.communication_styles = self._load_communication_styles()
        self.cultural_adaptations = self._load_cultural_adaptations()
        self.response_patterns = self._load_response_patterns()
        self.profile_cache = SimpleCache(default_ttl=7200)
        self.adaptation_history = {}
        self.adaptation_times = []
        self.user_response_patterns = {}
        self.logger.info("Personality Engine initialized")
    
    async def adapt_personality(
        self,
        user_profile: UserProfile,
        conversation_context: ConversationContext,
        current_emotional_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Adapt AI personality based on user profile and context with cultural awareness"""
        try:
            start_time = datetime.utcnow()
            
            # Learn from response patterns
            self._learn_response_patterns(user_profile.user_id, conversation_context)
            
            # Generate comprehensive adaptation
            adaptation = {
                "primary_style": self._adapt_communication_style(user_profile, conversation_context),
                "emotional_tone": self._determine_emotional_tone(user_profile, current_emotional_state),
                "response_guidelines": self._generate_response_guidelines(user_profile),
                "cultural_adaptations": self._apply_cultural_adaptations(user_profile),
                "interaction_preferences": self._determine_interaction_preferences(user_profile, conversation_context),
                "adaptation_metadata": {
                    "adaptation_timestamp": datetime.utcnow(),
                    "confidence_level": self._calculate_adaptation_confidence(user_profile),
                    "learning_applied": user_profile.user_id in self.user_response_patterns,
                    "cultural_context": user_profile.cultural_context
                }
            }
            
            # Store adaptation history for learning
            self._store_adaptation_history(user_profile.user_id, adaptation)
            
            # Update performance metrics
            self.adaptation_times.append((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return adaptation
            
        except Exception as e:
            self.logger.error(f"Failed to adapt personality: {e}")
            return self._get_default_adaptation()
    
    def _adapt_communication_style(
        self,
        user_profile: UserProfile,
        conversation_context: ConversationContext
    ) -> Dict[str, Any]:
        """Adapt communication style based on user preferences and patterns"""
        base_style = self.communication_styles.get(
            user_profile.communication_style.value,
            self.communication_styles["friendly"]
        )
        
        # Apply learned patterns if available
        if user_profile.user_id in self.user_response_patterns:
            patterns = self.user_response_patterns[user_profile.user_id]
            base_style = self._apply_learned_patterns(base_style, patterns)
        
        # Adjust for conversation context
        if conversation_context.conversation_goals:
            if any("professional" in goal.lower() for goal in conversation_context.conversation_goals):
                base_style["formality_adjustment"] = 0.2
            elif any("casual" in goal.lower() for goal in conversation_context.conversation_goals):
                base_style["formality_adjustment"] = -0.2
        
        return base_style
    
    def _learn_response_patterns(
        self,
        user_id: str,
        conversation_context: ConversationContext
    ) -> None:
        """Learn user's preferred response patterns from conversation history"""
        if not conversation_context.recent_history:
            return
        
        if user_id not in self.user_response_patterns:
            self.user_response_patterns[user_id] = {
                "preferred_length": [],
                "response_time_preferences": [],
                "depth_preferences": [],
                "humor_responses": []
            }
        
        patterns = self.user_response_patterns[user_id]
        
        # Analyze recent exchanges for patterns
        for exchange in conversation_context.recent_history[-5:]:  # Last 5 exchanges
            if "user_message" in exchange and "ai_response" in exchange:
                user_msg = exchange["user_message"]
                ai_resp = exchange["ai_response"]
                
                # Learn length preferences from user engagement
                if len(user_msg) > 50:  # User provided detailed response
                    patterns["preferred_length"].append("detailed")
                elif len(user_msg) < 20:  # User provided brief response
                    patterns["preferred_length"].append("brief")
                
                # Learn depth preferences
                if any(word in user_msg.lower() for word in ["why", "how", "explain", "detail"]):
                    patterns["depth_preferences"].append("deep")
                elif any(word in user_msg.lower() for word in ["quick", "brief", "short"]):
                    patterns["depth_preferences"].append("shallow")
        
        # Keep only recent patterns (last 20)
        for key in patterns:
            patterns[key] = patterns[key][-20:]
    
    def _apply_cultural_adaptations(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Apply cultural context adaptations as specified in documentation"""
        cultural_context = user_profile.cultural_context
        if not cultural_context:
            return {"cultural_adjustments": None}
        
        adaptations = self.cultural_adaptations.get(cultural_context, {})
        
        return {
            "communication_norms": adaptations.get("communication_norms", {}),
            "formality_expectations": adaptations.get("formality_level", user_profile.formality_level),
            "directness_level": adaptations.get("directness", 0.5),
            "context_sensitivity": adaptations.get("context_importance", 0.5),
            "respect_protocols": adaptations.get("respect_protocols", [])
        }
    
    def _determine_interaction_preferences(
        self,
        user_profile: UserProfile,
        conversation_context: ConversationContext
    ) -> Dict[str, Any]:
        """Determine interaction preferences based on profile and learned patterns"""
        preferences = {
            "proactive_engagement": user_profile.proactive_engagement,
            "follow_up_questions": user_profile.conversation_depth > 0.5,
            "memory_references": True,
            "humor_level": user_profile.humor_preference,
            "emotional_responsiveness": user_profile.emotional_matching
        }
        
        # Apply learned patterns
        if user_profile.user_id in self.user_response_patterns:
            patterns = self.user_response_patterns[user_profile.user_id]
            
            # Adjust follow-up frequency based on user responses
            if patterns["depth_preferences"]:
                deep_responses = patterns["depth_preferences"].count("deep")
                shallow_responses = patterns["depth_preferences"].count("shallow")
                if shallow_responses > deep_responses:
                    preferences["follow_up_questions"] = False
        
        return preferences
    
    def _calculate_adaptation_confidence(self, user_profile: UserProfile) -> float:
        """Calculate confidence level in personality adaptation"""
        base_confidence = 0.5
        
        # Increase confidence based on interaction history
        if user_profile.user_id in self.user_response_patterns:
            patterns = self.user_response_patterns[user_profile.user_id]
            total_patterns = sum(len(p) for p in patterns.values())
            base_confidence += min(0.4, total_patterns * 0.02)
        
        # Increase confidence based on profile completeness
        profile_completeness = 0
        if user_profile.cultural_context:
            profile_completeness += 0.1
        if user_profile.humor_preference != 0.5:  # Not default
            profile_completeness += 0.1
        if user_profile.formality_level != 0.5:  # Not default
            profile_completeness += 0.1
        
        base_confidence += profile_completeness
        
        return min(1.0, base_confidence)
    
    def _determine_emotional_tone(self, user_profile: UserProfile, emotional_state: Optional[Dict[str, Any]]) -> str:
        """Determine appropriate emotional tone with enhanced matching"""
        if user_profile.emotional_matching and emotional_state:
            emotion = emotional_state.get("primary_emotion", "neutral")
            intensity = emotional_state.get("intensity", 0.5)
            
            # Enhanced emotional tone mapping
            tone_mapping = {
                "happy": "encouraging" if intensity > 0.6 else "supportive",
                "sad": "empathetic" if intensity > 0.6 else "gentle", 
                "angry": "calm" if intensity > 0.7 else "understanding",
                "anxious": "calming" if intensity > 0.6 else "reassuring",
                "excited": "encouraging" if intensity > 0.5 else "enthusiastic",
                "stressed": "calming",
                "confused": "clarifying",
                "frustrated": "patient"
            }
            return tone_mapping.get(emotion, "supportive")
        return "supportive"
    
    def _generate_response_guidelines(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Generate comprehensive response guidelines"""
        guidelines = {
            "response_length": user_profile.preferred_response_length,
            "humor_level": user_profile.humor_preference,
            "formality_level": user_profile.formality_level,
            "depth_level": user_profile.conversation_depth,
            "cultural_sensitivity": user_profile.cultural_context is not None,
            "proactive_suggestions": user_profile.proactive_engagement
        }
        
        # Add learned pattern adjustments
        if user_profile.user_id in self.user_response_patterns:
            patterns = self.user_response_patterns[user_profile.user_id]
            
            # Adjust based on learned preferences
            if patterns["preferred_length"]:
                most_common_length = max(set(patterns["preferred_length"]), key=patterns["preferred_length"].count)
                guidelines["learned_length_preference"] = most_common_length
        
        return guidelines
    
    def _load_communication_styles(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive communication styles"""
        return {
            "friendly": {
                "tone": "warm",
                "approach": "supportive",
                "formality": 0.3,
                "directness": 0.6,
                "enthusiasm": 0.7
            },
            "formal": {
                "tone": "respectful",
                "approach": "professional",
                "formality": 0.9,
                "directness": 0.8,
                "enthusiasm": 0.4
            },
            "casual": {
                "tone": "relaxed",
                "approach": "conversational",
                "formality": 0.2,
                "directness": 0.5,
                "enthusiasm": 0.6
            },
            "professional": {
                "tone": "businesslike",
                "approach": "solution-focused",
                "formality": 0.8,
                "directness": 0.9,
                "enthusiasm": 0.5
            },
            "humorous": {
                "tone": "playful",
                "approach": "lighthearted",
                "formality": 0.3,
                "directness": 0.6,
                "enthusiasm": 0.8
            },
            "direct": {
                "tone": "straightforward",
                "approach": "no-nonsense",
                "formality": 0.6,
                "directness": 0.95,
                "enthusiasm": 0.4
            },
            "elaborate": {
                "tone": "comprehensive",
                "approach": "thorough",
                "formality": 0.6,
                "directness": 0.7,
                "enthusiasm": 0.6
            }
        }
    
    def _load_cultural_adaptations(self) -> Dict[str, Dict[str, Any]]:
        """Load cultural adaptation guidelines"""
        return {
            "western": {
                "communication_norms": {"direct_feedback": True, "individual_focus": True},
                "formality_level": 0.4,
                "directness": 0.7,
                "context_importance": 0.3
            },
            "asian": {
                "communication_norms": {"indirect_communication": True, "hierarchy_respect": True},
                "formality_level": 0.7,
                "directness": 0.4,
                "context_importance": 0.8,
                "respect_protocols": ["use_titles", "avoid_confrontation"]
            },
            "latin": {
                "communication_norms": {"warmth_emphasis": True, "relationship_focus": True},
                "formality_level": 0.5,
                "directness": 0.6,
                "context_importance": 0.6
            },
            "middle_eastern": {
                "communication_norms": {"respect_tradition": True, "family_importance": True},
                "formality_level": 0.8,
                "directness": 0.5,
                "context_importance": 0.7,
                "respect_protocols": ["cultural_sensitivity", "religious_awareness"]
            }
        }
    
    def _load_response_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load response pattern templates"""
        return {
            "brief": {"max_words": 50, "sentences": 1-2},
            "moderate": {"max_words": 150, "sentences": 3-5},
            "detailed": {"max_words": 400, "sentences": 6-10}
        }
    
    def _apply_learned_patterns(
        self,
        base_style: Dict[str, Any],
        patterns: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Apply learned patterns to base communication style"""
        adjusted_style = base_style.copy()
        
        # Adjust formality based on learned patterns
        if patterns.get("depth_preferences"):
            deep_count = patterns["depth_preferences"].count("deep")
            shallow_count = patterns["depth_preferences"].count("shallow")
            
            if deep_count > shallow_count:
                adjusted_style["formality"] = min(1.0, adjusted_style.get("formality", 0.5) + 0.1)
            elif shallow_count > deep_count:
                adjusted_style["formality"] = max(0.0, adjusted_style.get("formality", 0.5) - 0.1)
        
        return adjusted_style
    
    def _store_adaptation_history(self, user_id: str, adaptation: Dict[str, Any]) -> None:
        """Store adaptation history for learning purposes"""
        if user_id not in self.adaptation_history:
            self.adaptation_history[user_id] = []
        
        self.adaptation_history[user_id].append({
            "timestamp": datetime.utcnow(),
            "adaptation": adaptation,
            "confidence": adaptation["adaptation_metadata"]["confidence_level"]
        })
        
        # Keep only last 50 adaptations per user
        self.adaptation_history[user_id] = self.adaptation_history[user_id][-50:]
    
    def _get_default_adaptation(self) -> Dict[str, Any]:
        """Get default adaptation"""
        return {
            "primary_style": "friendly",
            "emotional_tone": "supportive",
            "response_guidelines": {"response_length": "moderate"},
            "interaction_preferences": {"follow_up_questions": True},
            "adaptation_metadata": {"confidence_level": 0.5}
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "total_adaptations": len(self.adaptation_times),
            "cache_size": self.profile_cache.size()
        }
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            test_profile = UserProfile(
                user_id="test_user",
                communication_style="friendly",
                preferred_response_length="moderate"
            )
            
            test_context = ConversationContext(
                user_id="test_user",
                conversation_id="test_conversation",
                personality_profile=test_profile
            )
            
            adaptation = await self.adapt_personality(test_profile, test_context)
            return isinstance(adaptation, dict) and "primary_style" in adaptation
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
