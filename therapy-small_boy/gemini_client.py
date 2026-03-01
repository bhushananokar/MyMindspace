#!/usr/bin/env python3
"""
AI Therapy System - Gemini AI Integration
Gemini 2.5 Pro API integration with therapy-specific prompts and safety monitoring
"""

import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import os
from config import Config, TherapyProtocols
from database import DatabaseManager
from utils import log_action


class ConversationMode(Enum):
    """Different conversation modes for therapy sessions"""
    ASSESSMENT = "assessment"
    CBT = "CBT"
    DBT = "DBT"
    ACT = "ACT"
    PSYCHODYNAMIC = "psychodynamic"
    CRISIS = "crisis"
    GENERAL = "general"
    PSYCHOEDUCATION = "psychoeducation"


class ResponseType(Enum):
    """Types of AI responses"""
    THERAPEUTIC = "therapeutic"
    EDUCATIONAL = "educational"
    SUPPORTIVE = "supportive"
    DIRECTIVE = "directive"
    REFLECTIVE = "reflective"
    CRISIS_INTERVENTION = "crisis_intervention"


@dataclass
class ConversationContext:
    """Context information for therapeutic conversations"""
    patient_id: int = 0
    session_id: Optional[int] = None
    mode: str = ConversationMode.GENERAL.value
    phase: str = "main_work"
    current_goals: List[str] = field(default_factory=list)
    recent_assessments: Dict[str, Any] = field(default_factory=dict)
    active_diagnoses: List[str] = field(default_factory=list)
    session_history: List[Dict[str, str]] = field(default_factory=list)
    crisis_flags: List[str] = field(default_factory=list)
    therapeutic_alliance: float = 7.0  # 1-10 scale
    patient_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TherapeuticResponse:
    """Structure for AI therapeutic responses"""
    content: str = ""
    response_type: str = ResponseType.THERAPEUTIC.value
    confidence: float = 0.8
    crisis_detected: bool = False
    crisis_level: str = "none"
    follow_up_questions: List[str] = field(default_factory=list)
    homework_suggestions: List[str] = field(default_factory=list)
    intervention_used: str = ""
    emotional_tone: str = "supportive"
    next_phase_suggestion: Optional[str] = None


class GeminiTherapyClient:
    """Advanced Gemini AI client for therapeutic conversations"""
    
    def __init__(self, db: DatabaseManager):
        # Configure Gemini API

        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(
            Config.GEMINI_MODEL,
            generation_config=genai.types.GenerationConfig(
                temperature=Config.GEMINI_TEMPERATURE,
                max_output_tokens=Config.GEMINI_MAX_TOKENS,
                top_p=Config.GEMINI_TOP_P,
                top_k=Config.GEMINI_TOP_K
            )
        )
        
        self.db = db
        self.conversation_history: Dict[int, List[Dict[str, Any]]] = {}
        self.context_cache: Dict[int, ConversationContext] = {}
        self.safety_monitor = TherapySafetyMonitor()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests
        
        log_action("Gemini therapy client initialized", "gemini_client")
    
    async def generate_therapeutic_response(self, 
                                          user_input: str, 
                                          context: ConversationContext) -> TherapeuticResponse:
        """Generate therapeutic response with comprehensive safety and context awareness"""
        
        # Rate limiting
        await self._rate_limit()
        
        # Update context with current patient data
        context = await self._enrich_context(context)
        
        # Safety screening
        safety_result = self.safety_monitor.screen_input(user_input)
        
        if safety_result['crisis_detected']:
            return await self._handle_crisis_response(user_input, context, safety_result)
        
        # Build therapeutic prompt
        prompt = self._build_therapeutic_prompt(user_input, context)
        
        try:
            # Generate response
            response = await self._generate_with_retry(prompt)
            
            # Process and structure response
            therapeutic_response = self._process_response(response.text, context)
            
            # Store conversation
            self._store_conversation(context.patient_id, user_input, therapeutic_response.content, context.mode)
            
            # Update context cache
            self._update_context_cache(context.patient_id, therapeutic_response)
            
            log_action(f"Therapeutic response generated in {context.mode} mode", 
                      "gemini_client", patient_id=context.patient_id)
            
            return therapeutic_response
            
        except Exception as e:
            log_action(f"Error generating therapeutic response: {e}", "gemini_client", "ERROR")
            return self._create_fallback_response(context)
    
    async def _rate_limit(self):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    async def _enrich_context(self, context: ConversationContext) -> ConversationContext:
        """Enrich context with current patient data"""
        
        if context.patient_id == 0:
            return context
        
        # Get recent assessments
        recent_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 3",
            (context.patient_id,)
        )
        
        context.recent_assessments = {}
        for assessment in recent_assessments:
            context.recent_assessments[assessment['assessment_type']] = {
                'score': assessment['total_score'],
                'severity': assessment['severity_level'],
                'date': assessment['assessment_date']
            }
        
        # Get active diagnoses
        diagnoses = self.db.execute_query(
            "SELECT diagnosis_name FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (context.patient_id,)
        )
        context.active_diagnoses = [d['diagnosis_name'] for d in diagnoses]
        
        # Get current goals
        goals = self.db.execute_query(
            "SELECT goal_description FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
            (context.patient_id,)
        )
        context.current_goals = [g['goal_description'] for g in goals]
        
        # Get recent session history
        recent_sessions = self.db.execute_query(
            "SELECT therapist_notes, patient_feedback FROM sessions WHERE patient_id = ? ORDER BY session_date DESC LIMIT 3",
            (context.patient_id,)
        )
        
        context.session_history = []
        for session in recent_sessions:
            if session.get('therapist_notes') or session.get('patient_feedback'):
                context.session_history.append({
                    'therapist_notes': session.get('therapist_notes', ''),
                    'patient_feedback': session.get('patient_feedback', '')
                })
        
        return context
    
    def _build_therapeutic_prompt(self, user_input: str, context: ConversationContext) -> str:
        """Build comprehensive therapeutic prompt based on context"""
        
        # Base therapeutic instructions
        base_prompt = """You are an advanced AI therapy assistant trained in evidence-based therapeutic practices. You provide empathetic, professional, and clinically sound responses while maintaining appropriate therapeutic boundaries.

CORE PRINCIPLES:
- Always prioritize patient safety and well-being
- Maintain empathetic and non-judgmental stance
- Use evidence-based therapeutic techniques
- Respect patient autonomy and cultural differences
- Maintain appropriate professional boundaries
- Focus on patient strengths and resilience

COMMUNICATION STYLE:
- Use warm, collaborative, and respectful language
- Ask thoughtful, open-ended questions when appropriate
- Validate emotions while challenging unhelpful thoughts
- Provide psychoeducation when relevant
- Encourage self-reflection and insight"""
        
        # Add mode-specific instructions
        mode_prompts = {
            ConversationMode.CBT.value: """
CBT APPROACH:
- Help identify and examine thought patterns and cognitive distortions
- Guide behavioral experiments and activity scheduling
- Use Socratic questioning to promote insight
- Focus on here-and-now problems and solutions
- Encourage homework and between-session practice
- Common techniques: thought records, behavioral activation, exposure exercises
""",
            ConversationMode.DBT.value: """
DBT APPROACH:
- Emphasize balance between acceptance and change
- Teach and reinforce four core skill modules:
  * Mindfulness (observe, describe, participate)
  * Distress tolerance (TIPP, distraction, self-soothing)
  * Emotion regulation (PLEASE skills, opposite action)
  * Interpersonal effectiveness (DEAR MAN, GIVE, FAST)
- Use dialectical thinking (both/and rather than either/or)
- Focus on building life worth living
""",
            ConversationMode.ACT.value: """
ACT APPROACH:
- Promote psychological flexibility through six core processes
- Help clarify personal values and committed action
- Use cognitive defusion techniques for unhelpful thoughts
- Practice acceptance of difficult internal experiences
- Encourage present-moment awareness and mindfulness
- Focus on workability rather than truth of thoughts
""",
            ConversationMode.PSYCHODYNAMIC.value: """
PSYCHODYNAMIC APPROACH:
- Explore unconscious patterns and their origins
- Examine defense mechanisms and coping styles
- Look for recurring themes in relationships and behavior
- Use insight and interpretation to promote understanding
- Focus on the therapeutic relationship as source of learning
- Help process emotions and integrate experiences
""",
            ConversationMode.ASSESSMENT.value: """
ASSESSMENT APPROACH:
- Ask structured questions to gather relevant clinical information
- Assess for symptoms, functioning, and risk factors
- Be thorough but sensitive in questioning
- Normalize the assessment process for the patient
- Provide appropriate feedback about assessment findings
""",
            ConversationMode.CRISIS.value: """
CRISIS INTERVENTION:
- Prioritize immediate safety assessment
- Provide crisis de-escalation and stabilization
- Connect with support resources and emergency services
- Create safety plans and coping strategies
- Follow up on risk factors and protective elements
""",
            ConversationMode.PSYCHOEDUCATION.value: """
PSYCHOEDUCATION APPROACH:
- Provide clear, accessible information about mental health
- Help normalize patient experiences
- Explain treatment rationale and options
- Use metaphors and examples to aid understanding
- Encourage questions and active learning
"""
        }
        
        # Build context-specific information
        context_info = f"""
PATIENT CONTEXT:
Mode: {context.mode}
Session Phase: {context.phase}"""
        
        if context.active_diagnoses:
            context_info += f"\nActive Diagnoses: {', '.join(context.active_diagnoses)}"
        
        if context.recent_assessments:
            context_info += "\nRecent Assessment Scores:"
            for assessment, data in context.recent_assessments.items():
                context_info += f"\n  - {assessment}: {data['score']} ({data['severity']})"
        
        if context.current_goals:
            context_info += f"\nCurrent Treatment Goals:\n  - " + "\n  - ".join(context.current_goals[:3])
        
        if context.session_history:
            context_info += "\nRecent Session Themes:"
            for i, session in enumerate(context.session_history[:2], 1):
                if session['therapist_notes']:
                    context_info += f"\n  Session {i}: {session['therapist_notes'][:100]}..."
        
        # Build final prompt
        mode_specific = mode_prompts.get(context.mode, "")
        
        final_prompt = f"""{base_prompt}

{mode_specific}

{context_info}

PATIENT INPUT: "{user_input}"

Please provide a therapeutic response that:
1. Addresses the patient's input directly and empathetically
2. Uses techniques appropriate to the {context.mode} modality
3. Considers the patient's current diagnoses and treatment goals
4. Maintains a warm, collaborative therapeutic stance
5. Includes a follow-up question or reflection when appropriate

RESPONSE:"""
        
        return final_prompt
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> Any:
        """Generate response with retry logic"""
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                # Check if response was blocked
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    raise Exception(f"Response blocked: {response.prompt_feedback.block_reason}")
                
                return response
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    def _process_response(self, raw_response: str, context: ConversationContext) -> TherapeuticResponse:
        """Process and structure the raw AI response"""
        
        response = TherapeuticResponse(content=raw_response.strip())
        
        # Determine response type based on content analysis
        response.response_type = self._classify_response_type(raw_response)
        
        # Extract follow-up questions
        response.follow_up_questions = self._extract_questions(raw_response)
        
        # Extract homework suggestions
        response.homework_suggestions = self._extract_homework_suggestions(raw_response, context.mode)
        
        # Determine intervention used
        response.intervention_used = self._identify_intervention(raw_response, context.mode)
        
        # Assess emotional tone
        response.emotional_tone = self._assess_emotional_tone(raw_response)
        
        # Suggest next phase if appropriate
        response.next_phase_suggestion = self._suggest_next_phase(raw_response, context.phase)
        
        # Additional safety check
        safety_result = self.safety_monitor.screen_output(raw_response)
        if safety_result['crisis_detected']:
            response.crisis_detected = True
            response.crisis_level = safety_result['risk_level']
        
        return response
    
    def _classify_response_type(self, response: str) -> str:
        """Classify the type of therapeutic response"""
        response_lower = response.lower()
        
        # Crisis intervention indicators
        crisis_keywords = ['crisis', 'emergency', 'safety', 'suicide', 'harm']
        if any(keyword in response_lower for keyword in crisis_keywords):
            return ResponseType.CRISIS_INTERVENTION.value
        
        # Educational indicators
        educational_keywords = ['research shows', 'studies indicate', 'it\'s important to understand', 'let me explain']
        if any(keyword in response_lower for keyword in educational_keywords):
            return ResponseType.EDUCATIONAL.value
        
        # Directive indicators
        directive_keywords = ['i recommend', 'you should', 'try doing', 'next step is']
        if any(keyword in response_lower for keyword in directive_keywords):
            return ResponseType.DIRECTIVE.value
        
        # Reflective indicators
        reflective_keywords = ['it sounds like', 'i hear you saying', 'what i\'m understanding', 'it seems']
        if any(keyword in response_lower for keyword in reflective_keywords):
            return ResponseType.REFLECTIVE.value
        
        # Supportive indicators
        supportive_keywords = ['i\'m here for you', 'that takes courage', 'you\'re not alone', 'that\'s understandable']
        if any(keyword in response_lower for keyword in supportive_keywords):
            return ResponseType.SUPPORTIVE.value
        
        return ResponseType.THERAPEUTIC.value
    
    def _extract_questions(self, response: str) -> List[str]:
        """Extract follow-up questions from response"""
        # Find sentences ending with question marks
        questions = re.findall(r'[^.!?]*\?', response)
        
        # Clean and filter questions
        questions = [q.strip() for q in questions if len(q.strip()) > 10]
        
        # Limit to 2 most relevant questions
        return questions[:2]
    
    def _extract_homework_suggestions(self, response: str, mode: str) -> List[str]:
        """Extract homework or practice suggestions"""
        homework_patterns = [
            r'homework.*?[:](.*?)(?:\.|$)',
            r'practice.*?[:](.*?)(?:\.|$)',
            r'assignment.*?[:](.*?)(?:\.|$)',
            r'between now and.*?(?:\.|$)',
            r'try.*?at home.*?(?:\.|$)'
        ]
        
        suggestions = []
        for pattern in homework_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.DOTALL)
            suggestions.extend([match.strip() for match in matches if match.strip()])
        
        # Add mode-specific homework if not explicitly mentioned
        if not suggestions and mode in ['CBT', 'DBT', 'ACT']:
            if 'thought record' in response.lower() or 'thoughts' in response.lower():
                suggestions.append("Complete a daily thought record")
            elif 'activity' in response.lower() or 'behavioral' in response.lower():
                suggestions.append("Schedule and complete pleasant activities")
            elif 'mindfulness' in response.lower():
                suggestions.append("Practice daily mindfulness exercises")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _identify_intervention(self, response: str, mode: str) -> str:
        """Identify which therapeutic intervention was used"""
        response_lower = response.lower()
        
        # CBT interventions
        if mode == 'CBT':
            if 'thought record' in response_lower or 'challenging thoughts' in response_lower:
                return 'Cognitive Restructuring'
            elif 'activity scheduling' in response_lower or 'pleasant activities' in response_lower:
                return 'Behavioral Activation'
            elif 'exposure' in response_lower:
                return 'Exposure Therapy'
            elif 'evidence' in response_lower and ('for' in response_lower or 'against' in response_lower):
                return 'Evidence Examination'
        
        # DBT interventions
        elif mode == 'DBT':
            if 'mindfulness' in response_lower:
                return 'Mindfulness Skills'
            elif 'tipp' in response_lower or 'distress tolerance' in response_lower:
                return 'Distress Tolerance'
            elif 'emotion regulation' in response_lower or 'please skills' in response_lower:
                return 'Emotion Regulation'
            elif 'dear man' in response_lower or 'interpersonal' in response_lower:
                return 'Interpersonal Effectiveness'
        
        # ACT interventions
        elif mode == 'ACT':
            if 'values' in response_lower:
                return 'Values Clarification'
            elif 'defusion' in response_lower or 'distance from thoughts' in response_lower:
                return 'Cognitive Defusion'
            elif 'acceptance' in response_lower:
                return 'Acceptance Practices'
            elif 'mindful' in response_lower:
                return 'Mindfulness Practice'
        
        # General interventions
        if 'psychoeducation' in response_lower or 'let me explain' in response_lower:
            return 'Psychoeducation'
        elif 'reflect' in response_lower or 'sounds like' in response_lower:
            return 'Reflective Listening'
        elif 'support' in response_lower:
            return 'Supportive Intervention'
        
        return 'General Therapeutic Response'
    
    def _assess_emotional_tone(self, response: str) -> str:
        """Assess the emotional tone of the response"""
        response_lower = response.lower()
        
        # Empathetic tone
        empathetic_words = ['understand', 'difficult', 'challenging', 'feel', 'sounds tough']
        if sum(word in response_lower for word in empathetic_words) >= 2:
            return 'empathetic'
        
        # Encouraging tone
        encouraging_words = ['great', 'progress', 'strength', 'capable', 'resilient', 'proud']
        if any(word in response_lower for word in encouraging_words):
            return 'encouraging'
        
        # Curious tone
        curious_words = ['curious', 'wonder', 'explore', 'tell me more', 'what do you think']
        if any(word in response_lower for word in curious_words):
            return 'curious'
        
        # Gentle challenging
        challenging_words = ['notice', 'consider', 'what if', 'alternative', 'different perspective']
        if any(word in response_lower for word in challenging_words):
            return 'gently_challenging'
        
        return 'supportive'
    
    def _suggest_next_phase(self, response: str, current_phase: str) -> Optional[str]:
        """Suggest next session phase based on response content"""
        response_lower = response.lower()
        
        if current_phase == 'opening':
            if 'homework' in response_lower or 'assignment' in response_lower:
                return 'homework_review'
            elif 'goal' in response_lower or 'work on' in response_lower:
                return 'main_work'
        
        elif current_phase == 'main_work':
            if 'practice' in response_lower or 'try' in response_lower:
                return 'skill_practice'
            elif 'homework' in response_lower or 'between sessions' in response_lower:
                return 'homework_assignment'
        
        elif current_phase == 'skill_practice':
            if 'homework' in response_lower or 'next week' in response_lower:
                return 'homework_assignment'
        
        return None
    
    async def _handle_crisis_response(self, user_input: str, context: ConversationContext, 
                                     safety_result: Dict[str, Any]) -> TherapeuticResponse:
        """Handle crisis situations with immediate intervention"""
        
        crisis_prompt = f"""CRISIS INTERVENTION RESPONSE REQUIRED

The patient has expressed content indicating potential crisis: "{user_input}"
Risk Level: {safety_result['risk_level']}
Detected Issues: {', '.join(safety_result['crisis_indicators'])}

Provide an immediate, empathetic crisis intervention response that:
1. Validates the patient's pain without minimizing it
2. Assesses immediate safety
3. Provides crisis resources and emergency contacts
4. Uses de-escalation techniques
5. Offers immediate coping strategies
6. Expresses genuine concern and support

Include specific crisis resources:
- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- Emergency Services: 911

Be direct, compassionate, and focused on immediate safety."""
        
        try:
            response = await self._generate_with_retry(crisis_prompt)
            
            crisis_response = TherapeuticResponse(
                content=response.text,
                response_type=ResponseType.CRISIS_INTERVENTION.value,
                crisis_detected=True,
                crisis_level=safety_result['risk_level'],
                emotional_tone='urgent_supportive',
                intervention_used='Crisis Intervention'
            )
            
            # Log crisis response
            log_action(f"Crisis response generated - Risk Level: {safety_result['risk_level']}", 
                      "gemini_client", "WARNING", patient_id=context.patient_id)
            
            return crisis_response
            
        except Exception as e:
            log_action(f"Error generating crisis response: {e}", "gemini_client", "ERROR")
            return self._create_emergency_fallback_response()
    
    def _create_fallback_response(self, context: ConversationContext) -> TherapeuticResponse:
        """Create fallback response when AI generation fails"""
        
        fallback_content = """I apologize, but I'm having some technical difficulties right now. 
        
I want to make sure you're getting the support you need. If this is urgent or you're in crisis, please:
        
- Call 988 (National Suicide Prevention Lifeline)
- Text HOME to 741741 (Crisis Text Line)
- Call 911 for emergencies
- Contact your healthcare provider
        
I'm here to help once the technical issue is resolved. Thank you for your patience."""
        
        return TherapeuticResponse(
            content=fallback_content,
            response_type=ResponseType.SUPPORTIVE.value,
            confidence=1.0,  # High confidence in safety message
            emotional_tone='apologetic_supportive'
        )
    
    def _create_emergency_fallback_response(self) -> TherapeuticResponse:
        """Create emergency fallback for crisis situations"""
        
        emergency_content = """I'm very concerned about what you've shared. Your safety is the most important thing right now.

IMMEDIATE RESOURCES:
🆘 National Suicide Prevention Lifeline: 988
📱 Crisis Text Line: Text HOME to 741741  
🚨 Emergency Services: 911

Please reach out to one of these resources immediately. You don't have to go through this alone.

If you're having thoughts of suicide, please:
- Stay with someone or call someone to be with you
- Remove any means of self-harm from your area
- Go to your nearest emergency room
- Call one of the crisis numbers above

You matter, and there are people who want to help you through this difficult time."""
        
        return TherapeuticResponse(
            content=emergency_content,
            response_type=ResponseType.CRISIS_INTERVENTION.value,
            crisis_detected=True,
            crisis_level='high',
            confidence=1.0,
            emotional_tone='urgent_caring'
        )
    
    def _store_conversation(self, patient_id: int, user_input: str, ai_response: str, mode: str):
        """Store conversation in memory and database"""
        
        # Store in memory
        if patient_id not in self.conversation_history:
            self.conversation_history[patient_id] = []
        
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'ai_response': ai_response,
            'mode': mode
        }
        
        self.conversation_history[patient_id].append(conversation_entry)
        
        # Keep only recent conversations in memory (last 20)
        if len(self.conversation_history[patient_id]) > 20:
            self.conversation_history[patient_id] = self.conversation_history[patient_id][-20:]
        
        # Log to database
        self.db.execute_update(
            "INSERT INTO system_logs (log_level, module, action, patient_id, message) VALUES (?, ?, ?, ?, ?)",
            ('INFO', 'gemini_conversation', 'therapeutic_exchange', patient_id, 
             json.dumps({'input_length': len(user_input), 'response_length': len(ai_response), 'mode': mode}))
        )
    
    def _update_context_cache(self, patient_id: int, response: TherapeuticResponse):
        """Update context cache with response information"""
        
        if patient_id not in self.context_cache:
            self.context_cache[patient_id] = ConversationContext(patient_id=patient_id)
        
        context = self.context_cache[patient_id]
        
        # Update based on response
        if response.next_phase_suggestion:
            context.phase = response.next_phase_suggestion
        
        if response.crisis_detected:
            if response.crisis_level not in context.crisis_flags:
                context.crisis_flags.append(response.crisis_level)
        
        # Update therapeutic alliance based on response quality
        if response.emotional_tone in ['empathetic', 'supportive', 'encouraging']:
            context.therapeutic_alliance = min(10.0, context.therapeutic_alliance + 0.1)
        elif response.emotional_tone in ['challenging', 'directive']:
            context.therapeutic_alliance = max(1.0, context.therapeutic_alliance - 0.05)
    
    def get_conversation_summary(self, patient_id: int, days: int = 7) -> Dict[str, Any]:
        """Get conversation summary for specified period"""
        
        if patient_id not in self.conversation_history:
            return {'error': 'No conversation history found'}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_conversations = [
            conv for conv in self.conversation_history[patient_id]
            if datetime.fromisoformat(conv['timestamp']) > cutoff_date
        ]
        
        summary = {
            'patient_id': patient_id,
            'period_days': days,
            'total_exchanges': len(recent_conversations),
            'modes_used': {},
            'common_themes': [],
            'therapeutic_progress_indicators': []
        }
        
        # Analyze modes used
        for conv in recent_conversations:
            mode = conv.get('mode', 'general')
            summary['modes_used'][mode] = summary['modes_used'].get(mode, 0) + 1
        
        # Analyze common themes (simplified)
        all_text = ' '.join([conv['user_input'] + ' ' + conv['ai_response'] for conv in recent_conversations])
        
        theme_keywords = {
            'anxiety': ['anxious', 'worry', 'nervous', 'panic'],
            'depression': ['sad', 'hopeless', 'depressed', 'down'],
            'relationships': ['relationship', 'partner', 'family', 'friends'],
            'work_stress': ['work', 'job', 'career', 'workplace'],
            'coping': ['cope', 'manage', 'handle', 'deal with'],
            'progress': ['better', 'improved', 'progress', 'achievement']
        }
        
        for theme, keywords in theme_keywords.items():
            if sum(1 for keyword in keywords if keyword in all_text.lower()) >= 2:
                summary['common_themes'].append(theme)
        
        return summary
    
    def clear_conversation_history(self, patient_id: int):
        """Clear conversation history for patient"""
        if patient_id in self.conversation_history:
            del self.conversation_history[patient_id]
        
        if patient_id in self.context_cache:
            del self.context_cache[patient_id]
        
        log_action(f"Conversation history cleared", "gemini_client", patient_id=patient_id)


class TherapySafetyMonitor:
    """Safety monitoring for therapeutic conversations"""
    
    def __init__(self):
        self.crisis_keywords = {
            'high_risk': [
                'kill myself', 'suicide', 'end it all', 'better off dead',
                'going to hurt myself', 'planning to die', 'overdose',
                'hanging myself', 'gun', 'pills to die'
            ],
            'moderate_risk': [
                'hurt myself', 'self harm', 'cutting', 'worthless',
                'hopeless', 'can\'t go on', 'no point', 'give up',
                'hate myself', 'disappear', 'end the pain'
            ],
            'low_risk': [
                'sad', 'depressed', 'down', 'upset', 'struggling',
                'difficult', 'hard time', 'overwhelmed'
            ]
        }
        
        self.violence_keywords = [
            'hurt someone', 'kill them', 'violence', 'revenge',
            'make them pay', 'destroy', 'harm others'
        ]
        
        self.substance_keywords = [
            'overdosed', 'too many pills', 'drinking heavily',
            'using again', 'relapsed', 'high right now'
        ]
        
        self.psychosis_keywords = [
            'voices telling me', 'hearing voices', 'people watching',
            'conspiracy', 'they\'re after me', 'cameras everywhere'
        ]
    
    def screen_input(self, text: str) -> Dict[str, Any]:
        """Screen user input for crisis indicators"""
        text_lower = text.lower()
        
        result = {
            'crisis_detected': False,
            'risk_level': 'none',
            'crisis_indicators': [],
            'requires_immediate_attention': False
        }
        
        # Check for suicide risk
        high_risk_count = sum(1 for keyword in self.crisis_keywords['high_risk'] if keyword in text_lower)
        moderate_risk_count = sum(1 for keyword in self.crisis_keywords['moderate_risk'] if keyword in text_lower)
        
        if high_risk_count > 0:
            result['crisis_detected'] = True
            result['risk_level'] = 'high'
            result['crisis_indicators'].append('suicide_risk_high')
            result['requires_immediate_attention'] = True
        elif moderate_risk_count >= 2:
            result['crisis_detected'] = True
            result['risk_level'] = 'moderate'
            result['crisis_indicators'].append('suicide_risk_moderate')
        elif moderate_risk_count >= 1:
            result['crisis_detected'] = True
            result['risk_level'] = 'low'
            result['crisis_indicators'].append('suicide_risk_low')
        
        # Check for violence risk
        if any(keyword in text_lower for keyword in self.violence_keywords):
            result['crisis_detected'] = True
            result['crisis_indicators'].append('violence_risk')
            if result['risk_level'] in ['none', 'low']:
                result['risk_level'] = 'moderate'
        
        # Check for substance abuse crisis
        if any(keyword in text_lower for keyword in self.substance_keywords):
            result['crisis_detected'] = True
            result['crisis_indicators'].append('substance_crisis')
            if result['risk_level'] == 'none':
                result['risk_level'] = 'low'
        
        # Check for psychosis indicators
        if any(keyword in text_lower for keyword in self.psychosis_keywords):
            result['crisis_detected'] = True
            result['crisis_indicators'].append('psychosis_symptoms')
            if result['risk_level'] == 'none':
                result['risk_level'] = 'moderate'
        
        return result
    
    def screen_output(self, response: str) -> Dict[str, Any]:
        """Screen AI output for inappropriate content"""
        response_lower = response.lower()
        
        result = {
            'crisis_detected': False,
            'risk_level': 'none',
            'issues': []
        }
        
        # Check for inappropriate advice
        inappropriate_phrases = [
            'you should kill yourself',
            'end your life',
            'suicide is the answer',
            'hurt yourself',
            'you\'re worthless',
            'no hope for you'
        ]
        
        if any(phrase in response_lower for phrase in inappropriate_phrases):
            result['crisis_detected'] = True
            result['risk_level'] = 'high'
            result['issues'].append('inappropriate_advice')
        
        # Check for unprofessional content
        unprofessional_phrases = [
            'i don\'t care',
            'that\'s stupid',
            'you\'re crazy',
            'just get over it',
            'stop being dramatic'
        ]
        
        if any(phrase in response_lower for phrase in unprofessional_phrases):
            result['issues'].append('unprofessional_content')
        
        # Check for boundary violations
        boundary_violations = [
            'let\'s meet in person',
            'give me your number',
            'i love you',
            'we should be friends',
            'tell me your address'
        ]
        
        if any(phrase in response_lower for phrase in boundary_violations):
            result['issues'].append('boundary_violation')
        
        return result


class TherapyPromptLibrary:
    """Library of specialized therapy prompts"""
    
    @staticmethod
    def get_assessment_prompts() -> Dict[str, str]:
        """Get prompts for different assessment scenarios"""
        return {
            'intake_assessment': """
You are conducting an intake assessment. Your goals are to:
- Establish rapport and trust
- Gather comprehensive background information
- Assess current symptoms and functioning
- Identify treatment goals and preferences
- Screen for risk factors

Ask open-ended questions, be curious but sensitive, and normalize the assessment process.
""",
            
            'mental_status_exam': """
Conduct a mental status examination by observing and asking about:
- Appearance and behavior
- Speech and language
- Mood and affect
- Thought process and content
- Perceptual disturbances
- Cognitive functioning
- Insight and judgment

Be systematic but maintain a conversational flow.
""",
            
            'risk_assessment': """
Conduct a thorough risk assessment focusing on:
- Suicidal ideation, intent, and plan
- History of self-harm or suicide attempts
- Protective factors and support systems
- Access to means of self-harm
- Substance use patterns
- Risk to others

Be direct but compassionate in your questioning.
"""
        }
    
    @staticmethod
    def get_intervention_prompts() -> Dict[str, Dict[str, str]]:
        """Get prompts for specific therapeutic interventions"""
        return {
            'CBT': {
                'thought_challenging': """
Help the patient examine their automatic thoughts by:
1. Identifying the specific thought
2. Exploring the evidence for and against it
3. Considering alternative perspectives
4. Developing a more balanced thought
5. Planning behavioral tests

Use Socratic questioning throughout.
""",
                
                'behavioral_activation': """
Guide behavioral activation by:
1. Assessing current activity levels
2. Identifying valued activities and goals
3. Planning specific, achievable activities
4. Scheduling activities with pleasure/mastery ratings
5. Problem-solving barriers to engagement

Focus on small, concrete steps.
""",
                
                'exposure_planning': """
Develop an exposure plan by:
1. Creating a fear hierarchy (0-100 scale)
2. Starting with manageable exposure levels
3. Planning specific exposure exercises
4. Discussing coping strategies during exposure
5. Planning gradual progression

Emphasize collaboration and patient control.
"""
            },
            
            'DBT': {
                'mindfulness_teaching': """
Teach mindfulness skills focusing on:
- Observe: Notice internal and external experiences
- Describe: Put words to experiences without evaluation
- Participate: Be fully present in activities
- Non-judgmentally: Accept experiences without labeling good/bad
- One-mindfully: Focus attention on one thing
- Effectively: Do what works in the moment

Use practical exercises and metaphors.
""",
                
                'distress_tolerance': """
Teach distress tolerance skills:
- TIPP: Temperature, Intense exercise, Paced breathing, Paired muscle relaxation
- Distract: Activities, Contributing, Comparisons, Emotions, Push away, Thoughts, Sensations
- Self-soothe: Using the five senses
- IMPROVE the moment: Imagery, Meaning, Prayer, Relaxation, One thing, Vacation, Encouragement

Focus on crisis survival without making things worse.
""",
                
                'emotion_regulation': """
Guide emotion regulation by:
- Understanding the function of emotions
- Identifying and labeling emotions accurately
- Checking the facts about emotions
- Using opposite action when emotions don't fit facts
- Building mastery and pleasant activities
- Taking care of physical health (PLEASE skills)

Emphasize that all emotions are valid but not all actions are effective.
"""
            },
            
            'ACT': {
                'values_clarification': """
Help clarify values by:
1. Exploring different life domains (relationships, work, health, etc.)
2. Identifying what truly matters to the patient
3. Distinguishing values from goals
4. Exploring barriers to values-based living
5. Connecting current struggles to values

Use card sorts, metaphors, and experiential exercises.
""",
                
                'cognitive_defusion': """
Practice cognitive defusion using:
- "I'm having the thought that..." technique
- Singing thoughts to silly tunes
- Visualizing thoughts as leaves on a stream
- Thanking the mind for its thoughts
- Passengers on the bus metaphor

Help create distance from thoughts rather than changing their content.
""",
                
                'committed_action': """
Guide committed action by:
1. Identifying values-based goals
2. Breaking goals into specific, measurable steps
3. Anticipating barriers and planning responses
4. Building accountability and support
5. Celebrating progress and learning from setbacks

Focus on workability and values alignment rather than perfection.
"""
            }
        }
    
    @staticmethod
    def get_crisis_prompts() -> Dict[str, str]:
        """Get prompts for crisis intervention"""
        return {
            'suicide_assessment': """
Conduct suicide risk assessment by asking about:
- Current suicidal thoughts, frequency, and intensity
- Specific plans and access to means
- Intent and timeline
- Previous attempts and what helped before
- Protective factors and reasons for living
- Current support system and safety planning

Be direct, calm, and non-judgmental.
""",
            
            'safety_planning': """
Collaborate on safety planning by:
1. Identifying warning signs of crisis
2. Internal coping strategies patient can use alone
3. People and social settings that provide support
4. Family members or friends who can help
5. Mental health professionals to contact
6. Making the environment safe
7. Reasons for living

Make the plan specific, personal, and accessible.
""",
            
            'de_escalation': """
Use de-escalation techniques:
- Validate emotions while promoting safety
- Use calm, non-threatening body language and voice
- Listen actively and reflect understanding
- Avoid arguing or challenging delusions
- Offer choices and maintain hope
- Focus on immediate safety and stabilization

Prioritize safety over all other considerations.
"""
        }


# Utility functions for prompt management
def build_context_prompt(patient_data: Dict[str, Any], session_type: str) -> str:
    """Build context-aware prompt from patient data"""
    
    context_parts = [
        f"Patient Information:",
        f"- Session Type: {session_type}"
    ]
    
    if patient_data.get('diagnoses'):
        diagnoses = [d['diagnosis_name'] for d in patient_data['diagnoses']]
        context_parts.append(f"- Diagnoses: {', '.join(diagnoses)}")
    
    if patient_data.get('recent_assessments'):
        context_parts.append("- Recent Assessment Scores:")
        for assessment in patient_data['recent_assessments']:
            context_parts.append(f"  * {assessment['type']}: {assessment['score']} ({assessment['severity']})")
    
    if patient_data.get('treatment_goals'):
        context_parts.append("- Current Treatment Goals:")
        for goal in patient_data['treatment_goals'][:3]:  # Top 3 goals
            context_parts.append(f"  * {goal['description']}")
    
    if patient_data.get('risk_factors'):
        context_parts.append(f"- Risk Factors: {', '.join(patient_data['risk_factors'])}")
    
    return "\n".join(context_parts)


async def test_gemini_client():
    """Test function for Gemini client"""
    try:
        from database import DatabaseManager
        
        # Initialize components
        db = DatabaseManager(":memory:")
        client = GeminiTherapyClient(db)
        
        print("Testing Gemini Therapy Client...")
        
        # Create test patient
        patient_id = db.execute_update(
            "INSERT INTO patients (name, preferred_therapy_mode) VALUES (?, ?)",
            ("Test Patient", "CBT")
        )
        
        # Create test context
        context = ConversationContext(
            patient_id=patient_id,
            mode=ConversationMode.CBT.value,
            phase="main_work"
        )
        
        # Test therapeutic response
        test_input = "I've been feeling really anxious lately and having trouble sleeping."
        
        print(f"\nTest Input: {test_input}")
        print("Generating response...")
        
        response = await client.generate_therapeutic_response(test_input, context)
        
        print(f"\nResponse Type: {response.response_type}")
        print(f"Intervention Used: {response.intervention_used}")
        print(f"Emotional Tone: {response.emotional_tone}")
        print(f"Crisis Detected: {response.crisis_detected}")
        print(f"\nContent: {response.content[:200]}...")
        
        if response.follow_up_questions:
            print(f"\nFollow-up Questions: {response.follow_up_questions}")
        
        if response.homework_suggestions:
            print(f"Homework Suggestions: {response.homework_suggestions}")
        
        # Test crisis detection
        print("\n" + "="*50)
        print("Testing Crisis Detection...")
        
        crisis_input = "I can't take this anymore. I want to end it all."
        print(f"\nCrisis Input: {crisis_input}")
        
        crisis_response = await client.generate_therapeutic_response(crisis_input, context)
        
        print(f"\nCrisis Detected: {crisis_response.crisis_detected}")
        print(f"Crisis Level: {crisis_response.crisis_level}")
        print(f"Response Type: {crisis_response.response_type}")
        print(f"\nCrisis Response: {crisis_response.content[:300]}...")
        
        # Test conversation summary
        print("\n" + "="*50)
        print("Testing Conversation Summary...")
        
        summary = client.get_conversation_summary(patient_id, days=7)
        print(f"Total Exchanges: {summary.get('total_exchanges', 0)}")
        print(f"Modes Used: {summary.get('modes_used', {})}")
        print(f"Common Themes: {summary.get('common_themes', [])}")
        
        print("\nGemini client testing completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        
        # Test fallback response
        print("\nTesting fallback response...")
        fallback = client._create_fallback_response(context)
        print(f"Fallback content: {fallback.content[:200]}...")


def create_session_context(db: DatabaseManager, patient_id: int, session_type: str) -> ConversationContext:
    """Helper function to create session context"""
    
    context = ConversationContext(
        patient_id=patient_id,
        mode=session_type,
        phase="opening"
    )
    
    # Enrich with patient data
    patient_data = db.execute_query("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient_data:
        patient = patient_data[0]
        context.patient_preferences = {
            'preferred_modality': patient.get('preferred_therapy_mode', 'CBT'),
            'risk_level': patient.get('risk_level', 'low')
        }
    
    return context


def validate_api_setup() -> bool:
    """Validate that Gemini API is properly configured"""
    try:
        if Config.GEMINI_API_KEY == 'your-api-key-here':
            print("❌ GEMINI_API_KEY not configured")
            print("Please set your API key in environment variables:")
            print("export GEMINI_API_KEY='your-actual-api-key'")
            return False
        
        # Test API connection
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        # Simple test
        response = model.generate_content("Hello, this is a test.")
        
        if response.text:
            print("✅ Gemini API connection successful")
            return True
        else:
            print("❌ Gemini API test failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API setup error: {e}")
        return False


# Main execution
def main():
    """Main function for testing and validation"""
    print("Gemini Therapy Client - Setup and Testing")
    print("=" * 50)
    
    # Validate API setup
    if not validate_api_setup():
        return
    
    # Run async tests
    try:
        asyncio.run(test_gemini_client())
    except Exception as e:
        print(f"Testing failed: {e}")


if __name__ == "__main__":
    main()