import re
import sys
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

@dataclass
class EmotionalTrigger:
    """Identified emotional trigger"""
    trigger_text: str
    trigger_type: str  # situational, interpersonal, temporal, cognitive
    emotions_triggered: List[str]
    intensity: float
    context: str
    confidence: float

@dataclass
class CopingStrategy:
    """Identified coping mechanism"""
    strategy_text: str
    strategy_type: str  # social_support, professional_help, avoidance, problem_solving
    effectiveness_indicator: str  # positive, negative, neutral
    emotions_addressed: List[str]
    confidence: float

@dataclass
class EmotionalPattern:
    """Emotional state and transition patterns"""
    primary_emotion: str
    secondary_emotions: List[str]
    emotional_intensity: float
    emotional_transition: Optional[str]  # what -> what
    duration_indicator: Optional[str]  # ongoing, brief, extended
    context: str

@dataclass
class PsychologicalInsight:
    """High-level psychological insights"""
    insight_type: str  # stress_pattern, support_system, emotional_regulation, etc.
    description: str
    evidence: List[str]
    confidence: float
    recommendation: Optional[str]

@dataclass
class PsychologicalAnalysis:
    """Complete psychological analysis"""
    emotional_triggers: List[EmotionalTrigger]
    coping_strategies: List[CopingStrategy]
    emotional_patterns: List[EmotionalPattern]
    psychological_insights: List[PsychologicalInsight]
    mental_health_indicators: Dict[str, float]  # anxiety, depression, stress levels
    support_system_strength: float
    emotional_regulation_score: float

class PsychologicalAnalyzer:
    """Advanced psychological analysis of journal text"""
    
    def __init__(self):
        self.emotion_keywords = {
            'anxiety': ['anxious', 'worried', 'nervous', 'stressed', 'tense', 'overwhelmed'],
            'happiness': ['happy', 'excited', 'joyful', 'pleased', 'glad', 'thrilled'],
            'sadness': ['sad', 'down', 'depressed', 'disappointed', 'hurt', 'upset'],
            'anger': ['angry', 'frustrated', 'annoyed', 'irritated', 'mad', 'furious'],
            'fear': ['scared', 'afraid', 'terrified', 'panicked', 'frightened'],
            'pride': ['proud', 'accomplished', 'successful', 'confident', 'impressed']
        }
        
        self.trigger_patterns = {
            'situational': [
                r'interview', r'presentation', r'meeting', r'deadline', r'exam', r'performance',
                r'waiting\s+period', r'results', r'evaluation', r'judgment'
            ],
            'interpersonal': [
                r'with\s+\w+', r'called', r'talked\s+to', r'conversation', r'relationship',
                r'family', r'friend', r'colleague', r'boss'
            ],
            'temporal': [
                r'tomorrow', r'next\s+week', r'deadline', r'soon', r'later', r'eventually'
            ],
            'cognitive': [
                r'thinking\s+about', r'worried\s+about', r'concerned\s+about', 
                r'obsessing', r'ruminating', r'can\'t\s+stop'
            ]
        }
        
        self.coping_patterns = {
            'social_support': [
                r'called\s+\w+', r'talked\s+to', r'mom\s+called', r'friend\s+said',
                r'support', r'help', r'advice'
            ],
            'professional_help': [
                r'therapy', r'therapist', r'counselor', r'doctor', r'psychiatrist',
                r'appointment', r'session'
            ],
            'problem_solving': [
                r'plan', r'strategy', r'prepare', r'practice', r'organize', r'research'
            ],
            'avoidance': [
                r'avoid', r'ignore', r'postpone', r'distract', r'escape'
            ],
            'self_care': [
                r'relax', r'meditate', r'exercise', r'sleep', r'rest', r'break'
            ]
        }
    
    def analyze(self, text: str) -> PsychologicalAnalysis:
        """Perform comprehensive psychological analysis"""
        
        # Extract emotional triggers
        triggers = self._extract_emotional_triggers(text)
        
        # Identify coping strategies  
        coping = self._extract_coping_strategies(text)
        
        # Analyze emotional patterns
        patterns = self._analyze_emotional_patterns(text)
        
        # Generate psychological insights
        insights = self._generate_psychological_insights(text, triggers, coping, patterns)
        
        # Calculate mental health indicators
        mh_indicators = self._calculate_mental_health_indicators(text, patterns)
        
        # Assess support system
        support_strength = self._assess_support_system(text, coping)
        
        # Evaluate emotional regulation
        regulation_score = self._evaluate_emotional_regulation(text, patterns, coping)
        
        return PsychologicalAnalysis(
            emotional_triggers=triggers,
            coping_strategies=coping,
            emotional_patterns=patterns,
            psychological_insights=insights,
            mental_health_indicators=mh_indicators,
            support_system_strength=support_strength,
            emotional_regulation_score=regulation_score
        )
    
    def _extract_emotional_triggers(self, text: str) -> List[EmotionalTrigger]:
        """Extract emotional triggers from text"""
        triggers = []
        text_lower = text.lower()
        
        for trigger_type, patterns in self.trigger_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text_lower))
                
                for match in matches:
                    # Get surrounding context
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    
                    # Identify emotions in context
                    emotions = self._identify_emotions_in_context(context)
                    
                    if emotions:  # Only create trigger if emotions are present
                        trigger = EmotionalTrigger(
                            trigger_text=match.group(),
                            trigger_type=trigger_type,
                            emotions_triggered=emotions,
                            intensity=self._calculate_emotion_intensity(context),
                            context=context.strip(),
                            confidence=0.8
                        )
                        triggers.append(trigger)
        
        return triggers
    
    def _extract_coping_strategies(self, text: str) -> List[CopingStrategy]:
        """Extract coping strategies from text"""
        strategies = []
        text_lower = text.lower()
        
        for strategy_type, patterns in self.coping_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text_lower))
                
                for match in matches:
                    # Get surrounding context
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]
                    
                    # Determine effectiveness
                    effectiveness = self._determine_effectiveness(context)
                    
                    # Find emotions this strategy addresses
                    emotions_addressed = self._identify_emotions_in_context(context)
                    
                    strategy = CopingStrategy(
                        strategy_text=match.group(),
                        strategy_type=strategy_type,
                        effectiveness_indicator=effectiveness,
                        emotions_addressed=emotions_addressed,
                        confidence=0.7
                    )
                    strategies.append(strategy)
        
        return strategies
    
    def _analyze_emotional_patterns(self, text: str) -> List[EmotionalPattern]:
        """Analyze emotional patterns and transitions"""
        patterns = []
        sentences = text.split('.')
        
        for sentence in sentences:
            emotions = self._identify_emotions_in_context(sentence)
            
            if emotions:
                # Determine primary and secondary emotions
                primary = emotions[0]
                secondary = emotions[1:] if len(emotions) > 1 else []
                
                # Calculate intensity
                intensity = self._calculate_emotion_intensity(sentence)
                
                # Look for transitions
                transition = self._detect_emotional_transition(sentence)
                
                # Determine duration
                duration = self._determine_emotion_duration(sentence)
                
                pattern = EmotionalPattern(
                    primary_emotion=primary,
                    secondary_emotions=secondary,
                    emotional_intensity=intensity,
                    emotional_transition=transition,
                    duration_indicator=duration,
                    context=sentence.strip()
                )
                patterns.append(pattern)
        
        return patterns
    
    def _generate_psychological_insights(self, text: str, triggers: List[EmotionalTrigger], 
                                       coping: List[CopingStrategy], 
                                       patterns: List[EmotionalPattern]) -> List[PsychologicalInsight]:
        """Generate high-level psychological insights"""
        insights = []
        
        # Stress pattern analysis
        if any(t.trigger_type == 'situational' for t in triggers):
            stress_triggers = [t for t in triggers if 'anxiety' in t.emotions_triggered]
            if stress_triggers:
                insight = PsychologicalInsight(
                    insight_type='stress_pattern',
                    description='Pattern of situational stress around performance/evaluation contexts',
                    evidence=[t.context for t in stress_triggers],
                    confidence=0.8,
                    recommendation='Consider developing pre-performance coping strategies'
                )
                insights.append(insight)
        
        # Support system analysis
        social_coping = [c for c in coping if c.strategy_type == 'social_support']
        if social_coping:
            insight = PsychologicalInsight(
                insight_type='support_system',
                description='Active utilization of social support network',
                evidence=[c.strategy_text for c in social_coping],
                confidence=0.9,
                recommendation='Continue leveraging social connections for emotional support'
            )
            insights.append(insight)
        
        # Professional help engagement
        prof_help = [c for c in coping if c.strategy_type == 'professional_help']
        if prof_help:
            insight = PsychologicalInsight(
                insight_type='professional_engagement',
                description='Proactive engagement with mental health professionals',
                evidence=[c.strategy_text for c in prof_help],
                confidence=0.95,
                recommendation='Consistent therapy attendance shows healthy coping awareness'
            )
            insights.append(insight)
        
        # Emotional regulation analysis
        if patterns:
            positive_transitions = [p for p in patterns if p.emotional_transition and 'positive' in p.emotional_transition]
            if positive_transitions:
                insight = PsychologicalInsight(
                    insight_type='emotional_regulation',
                    description='Evidence of adaptive emotional regulation',
                    evidence=[p.context for p in positive_transitions],
                    confidence=0.7,
                    recommendation='Continue building on existing emotional regulation skills'
                )
                insights.append(insight)
        
        return insights
    
    def _identify_emotions_in_context(self, context: str) -> List[str]:
        """Identify emotions present in context"""
        context_lower = context.lower()
        found_emotions = []
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    found_emotions.append(emotion)
                    break
        
        return found_emotions
    
    def _calculate_emotion_intensity(self, context: str) -> float:
        """Calculate emotional intensity based on language"""
        intensifiers = ['very', 'extremely', 'really', 'so', 'incredibly', 'totally']
        context_lower = context.lower()
        
        base_intensity = 0.5
        for intensifier in intensifiers:
            if intensifier in context_lower:
                base_intensity += 0.2
        
        # Look for exclamation marks
        if '!' in context:
            base_intensity += 0.1
        
        # Look for all caps
        if any(word.isupper() and len(word) > 2 for word in context.split()):
            base_intensity += 0.2
        
        return min(base_intensity, 1.0)
    
    def _determine_effectiveness(self, context: str) -> str:
        """Determine if coping strategy appears effective"""
        positive_indicators = ['helped', 'better', 'calmed', 'relieved', 'good', 'happy']
        negative_indicators = ['worse', 'failed', 'didn\'t help', 'still', 'more']
        
        context_lower = context.lower()
        
        if any(pos in context_lower for pos in positive_indicators):
            return 'positive'
        elif any(neg in context_lower for neg in negative_indicators):
            return 'negative'
        else:
            return 'neutral'
    
    def _detect_emotional_transition(self, sentence: str) -> Optional[str]:
        """Detect emotional transitions within sentence"""
        transition_words = ['but', 'however', 'though', 'although', 'yet', 'still']
        sentence_lower = sentence.lower()
        
        for word in transition_words:
            if word in sentence_lower:
                # Simple transition detection
                parts = sentence_lower.split(word)
                if len(parts) == 2:
                    before_emotions = self._identify_emotions_in_context(parts[0])
                    after_emotions = self._identify_emotions_in_context(parts[1])
                    
                    if before_emotions and after_emotions:
                        return f"{before_emotions[0]} -> {after_emotions[0]}"
        
        return None
    
    def _determine_emotion_duration(self, sentence: str) -> Optional[str]:
        """Determine implied duration of emotion"""
        duration_indicators = {
            'brief': ['moment', 'briefly', 'quickly', 'suddenly'],
            'ongoing': ['still', 'continue', 'keep', 'always', 'constantly'],
            'extended': ['long', 'extended', 'prolonged', 'persistent']
        }
        
        sentence_lower = sentence.lower()
        
        for duration, indicators in duration_indicators.items():
            if any(ind in sentence_lower for ind in indicators):
                return duration
        
        return None
    
    def _calculate_mental_health_indicators(self, text: str, patterns: List[EmotionalPattern]) -> Dict[str, float]:
        """Calculate mental health indicator scores"""
        anxiety_score = 0.0
        depression_score = 0.0
        stress_score = 0.0
        
        # Count anxiety-related patterns
        anxiety_patterns = [p for p in patterns if p.primary_emotion == 'anxiety' or 'anxiety' in p.secondary_emotions]
        anxiety_score = min(len(anxiety_patterns) * 0.3, 1.0)
        
        # Count depression-related patterns  
        depression_patterns = [p for p in patterns if p.primary_emotion == 'sadness' or 'sadness' in p.secondary_emotions]
        depression_score = min(len(depression_patterns) * 0.25, 1.0)
        
        # Calculate stress based on triggers and emotional intensity
        if patterns:
            avg_intensity = sum(p.emotional_intensity for p in patterns) / len(patterns)
            stress_score = min(avg_intensity, 1.0)
        
        return {
            'anxiety': anxiety_score,
            'depression': depression_score, 
            'stress': stress_score
        }
    
    def _assess_support_system(self, text: str, coping: List[CopingStrategy]) -> float:
        """Assess strength of support system"""
        social_strategies = [c for c in coping if c.strategy_type == 'social_support']
        professional_strategies = [c for c in coping if c.strategy_type == 'professional_help']
        
        support_score = 0.0
        
        # Social support
        if social_strategies:
            support_score += 0.4
            # Bonus for effective social support
            effective_social = [c for c in social_strategies if c.effectiveness_indicator == 'positive']
            if effective_social:
                support_score += 0.2
        
        # Professional support
        if professional_strategies:
            support_score += 0.4
        
        return min(support_score, 1.0)
    
    def _evaluate_emotional_regulation(self, text: str, patterns: List[EmotionalPattern], 
                                     coping: List[CopingStrategy]) -> float:
        """Evaluate emotional regulation capabilities"""
        regulation_score = 0.5  # Baseline
        
        # Positive for emotional transitions
        transitions = [p for p in patterns if p.emotional_transition]
        if transitions:
            regulation_score += 0.2
        
        # Positive for diverse coping strategies
        strategy_types = set(c.strategy_type for c in coping)
        regulation_score += len(strategy_types) * 0.1
        
        # Positive for effective coping
        effective_coping = [c for c in coping if c.effectiveness_indicator == 'positive']
        if effective_coping:
            regulation_score += 0.2
        
        return min(regulation_score, 1.0)