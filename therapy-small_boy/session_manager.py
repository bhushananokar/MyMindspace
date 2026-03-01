#!/usr/bin/env python3
"""
AI Therapy System - Session Management and Flow Control
Comprehensive session orchestration, flow management, and therapeutic conversation coordination
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from database import DatabaseManager
from models import Session, Patient, Assessment
from gemini_client import GeminiTherapyClient, ConversationContext, ConversationMode
from assessment_system import AssessmentSystem
from homework_system import HomeworkSystem
from goal_manager import GoalManager
from crisis_manager import CrisisManager
from documentation import DocumentationSystem
from config import Config, SessionStructures
from utils import log_action


class SessionPhase(Enum):
    """Session phases for structured therapy"""
    NOT_STARTED = "not_started"
    OPENING = "opening"
    CHECK_IN = "check_in"
    HOMEWORK_REVIEW = "homework_review"
    ASSESSMENT = "assessment"
    MAIN_WORK = "main_work"
    SKILL_PRACTICE = "skill_practice"
    HOMEWORK_ASSIGNMENT = "homework_assignment"
    GOAL_REVIEW = "goal_review"
    CLOSING = "closing"
    COMPLETED = "completed"
    EMERGENCY_INTERVENTION = "emergency_intervention"


class SessionStatus(Enum):
    """Session status tracking"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    EMERGENCY = "emergency"


@dataclass
class SessionState:
    """Current session state tracking"""
    session_id: int = 0
    patient_id: int = 0
    current_phase: str = SessionPhase.NOT_STARTED.value
    phase_start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = SessionStatus.SCHEDULED.value
    therapy_modality: str = "CBT"
    
    # Phase completion tracking
    phases_completed: List[str] = field(default_factory=list)
    phases_skipped: List[str] = field(default_factory=list)
    
    # Session metrics
    mood_ratings: Dict[str, int] = field(default_factory=dict)
    engagement_level: int = 7  # 1-10 scale
    crisis_detected: bool = False
    
    # Content tracking
    topics_discussed: List[str] = field(default_factory=list)
    interventions_used: List[str] = field(default_factory=list)
    assessments_completed: List[str] = field(default_factory=list)
    homework_assigned: List[str] = field(default_factory=list)
    
    # Session notes
    therapist_observations: List[str] = field(default_factory=list)
    patient_feedback: str = ""
    session_summary: str = ""


class SessionManager:
    """Manages therapy session flow, coordination, and state"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.gemini_client = GeminiTherapyClient(db)
        self.assessment_system = AssessmentSystem(db)
        self.homework_system = HomeworkSystem(db)
        self.goal_manager = GoalManager(db)
        self.crisis_manager = CrisisManager(db)
        self.documentation_system = DocumentationSystem(db)
        
        # Active session tracking
        self.active_sessions: Dict[int, SessionState] = {}  # patient_id -> SessionState
        self.session_handlers: Dict[str, Callable] = self._init_phase_handlers()
        
        # Session configuration
        self.default_session_structure = SessionStructures.STANDARD_SESSION
        
        log_action("Session manager initialized", "session_manager")
    
    def _init_phase_handlers(self) -> Dict[str, Callable]:
        """Initialize phase handler mapping"""
        return {
            SessionPhase.OPENING.value: self._handle_opening_phase,
            SessionPhase.CHECK_IN.value: self._handle_check_in_phase,
            SessionPhase.HOMEWORK_REVIEW.value: self._handle_homework_review_phase,
            SessionPhase.ASSESSMENT.value: self._handle_assessment_phase,
            SessionPhase.MAIN_WORK.value: self._handle_main_work_phase,
            SessionPhase.SKILL_PRACTICE.value: self._handle_skill_practice_phase,
            SessionPhase.HOMEWORK_ASSIGNMENT.value: self._handle_homework_assignment_phase,
            SessionPhase.GOAL_REVIEW.value: self._handle_goal_review_phase,
            SessionPhase.CLOSING.value: self._handle_closing_phase,
            SessionPhase.EMERGENCY_INTERVENTION.value: self._handle_emergency_intervention
        }
    
    async def start_session(self, patient_id: int, therapy_modality: str = "CBT", 
                           session_type: str = None) -> Dict[str, Any]:
        """Start a new therapy session"""
        
        # Get patient information
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        
        if not patient_data:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_data[0]
        
        # Use patient's preferred modality if not specified
        if not session_type:
            session_type = patient.get('preferred_therapy_mode', therapy_modality)
        
        # Create session record
        session = Session(
            patient_id=patient_id,
            session_type=session_type,
            duration=Config.DEFAULT_SESSION_DURATION
        )
        
        # Save session to database
        session_data = session.to_dict()
        session_data.pop('id', None)  # Remove id for insert
        
        session_id = self.db.execute_update('''
            INSERT INTO sessions 
            (patient_id, session_date, session_type, duration, mood_before, 
             mood_after, interventions_used, homework_assigned, crisis_flags, 
             therapist_notes, patient_feedback, session_phase, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.patient_id, session.session_date, session.session_type,
            session.duration, session.mood_before, session.mood_after,
            json.dumps(session.interventions_used), session.homework_assigned,
            json.dumps(session.crisis_flags), session.therapist_notes,
            session.patient_feedback, SessionPhase.OPENING.value, False
        ))
        
        # Initialize session state
        session_state = SessionState(
            session_id=session_id,
            patient_id=patient_id,
            current_phase=SessionPhase.OPENING.value,
            therapy_modality=session_type,
            status=SessionStatus.IN_PROGRESS.value
        )
        
        self.active_sessions[patient_id] = session_state
        
        # Create conversation context for Gemini
        context = ConversationContext(
            patient_id=patient_id,
            session_id=session_id,
            mode=session_type,
            phase=SessionPhase.OPENING.value
        )
        
        # Generate opening response
        opening_response = await self._handle_opening_phase(session_state, "", context)
        
        log_action(f"Session started: {session_type}", "session_manager", patient_id=patient_id, session_id=session_id)
        
        return {
            'session_id': session_id,
            'patient_id': patient_id,
            'therapy_modality': session_type,
            'current_phase': session_state.current_phase,
            'response': opening_response['content'],
            'phase_instructions': opening_response.get('instructions', ''),
            'estimated_duration': Config.DEFAULT_SESSION_DURATION,
            'session_structure': self._get_session_structure(session_type)
        }
    
    async def process_user_input(self, patient_id: int, user_input: str) -> Dict[str, Any]:
        """Process user input and advance session as needed"""
        
        if patient_id not in self.active_sessions:
            raise ValueError(f"No active session found for patient {patient_id}")
        
        session_state = self.active_sessions[patient_id]
        
        # Check for crisis indicators first
        crisis_detected = self.crisis_manager.detect_crisis(user_input, patient_id)
        if crisis_detected:
            session_state.crisis_detected = True
            session_state.current_phase = SessionPhase.EMERGENCY_INTERVENTION.value
            response = await self._handle_emergency_intervention(session_state, user_input)
# Continue to normal processing so the response is handled properly
        
        # Create conversation context
        context = ConversationContext(
            patient_id=patient_id,
            session_id=session_state.session_id,
            mode=session_state.therapy_modality,
            phase=session_state.current_phase
        )
        
        # Get current phase handler
        current_phase = session_state.current_phase
        if current_phase not in self.session_handlers:
            current_phase = SessionPhase.MAIN_WORK.value  # Default fallback
        
        handler = self.session_handlers[current_phase]
        
        # Process input with current phase handler
        response = await handler(session_state, user_input, context)
        
        # Update session state based on response
        if 'next_phase' in response:
            await self._transition_to_phase(session_state, response['next_phase'])
        
        # Track topics and interventions
        if 'topics' in response:
            session_state.topics_discussed.extend(response['topics'])
        
        if 'interventions' in response:
            session_state.interventions_used.extend(response['interventions'])
        
        # Update engagement tracking
        if 'engagement_indicators' in response:
            self._update_engagement_metrics(session_state, response['engagement_indicators'])
        
        log_action(f"Processed input in {current_phase} phase", "session_manager", 
                  patient_id=patient_id, session_id=session_state.session_id)
        
        return {
            'session_id': session_state.session_id,
            'current_phase': session_state.current_phase,
            'response': response['content'],
            'phase_progress': self._calculate_phase_progress(session_state),
            'session_metrics': self._get_session_metrics(session_state),
            'next_phase_available': response.get('phase_complete', False),
            'crisis_detected': session_state.crisis_detected
        }
    
    async def _handle_opening_phase(self, session_state: SessionState, user_input: str, 
                                  context: ConversationContext = None) -> Dict[str, Any]:
        """Handle session opening and initial greeting"""
        
        # Get patient information
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (session_state.patient_id,)
        )
        patient = patient_data[0]
        
        if not user_input:  # Initial opening
            opening_prompt = f"""Welcome, {patient['name']}! I'm glad to see you today for your {session_state.therapy_modality} session.

Before we begin, I'd like to check in with you:

1. How has your week been overall?
2. On a scale of 1-10, how is your mood right now?
3. What would you like to focus on in today's session?

Please share what's been on your mind since our last session."""
            
            response = {
                'content': opening_prompt,
                'instructions': 'Please share how your week has been and rate your current mood (1-10).',
                'phase_complete': False,
                'topics': ['session_opening', 'mood_check']
            }
        
        else:  # Process opening response
            if not context:
                context = ConversationContext(
                    patient_id=session_state.patient_id,
                    session_id=session_state.session_id,
                    mode=session_state.therapy_modality,
                    phase=SessionPhase.OPENING.value
                )
            
            # Extract mood rating if mentioned
            mood_rating = self._extract_mood_rating(user_input)
            if mood_rating:
                session_state.mood_ratings['session_start'] = mood_rating
                
                # Update session record
                self.db.execute_update(
                    "UPDATE sessions SET mood_before = ? WHERE id = ?",
                    (mood_rating, session_state.session_id)
                )
            
            # Generate contextual response
            gemini_response = await self.gemini_client.generate_therapeutic_response(
                user_input, context
            )
            
            # Check if opening is complete
            opening_complete = self._assess_opening_completeness(user_input, session_state)
            
            response = {
                'content': gemini_response.content,
                'phase_complete': opening_complete,
                'next_phase': SessionPhase.HOMEWORK_REVIEW.value if opening_complete else SessionPhase.OPENING.value,
                'topics': ['mood_assessment', 'session_goals'],
                'interventions': [gemini_response.intervention_used] if gemini_response.intervention_used else []
            }
        
        return response
    
    async def _handle_check_in_phase(self, session_state: SessionState, user_input: str, 
                                   context: ConversationContext) -> Dict[str, Any]:
        """Handle detailed check-in and symptom assessment"""
        
        check_in_prompt = """Let's do a quick check-in on how you've been feeling:

1. How have your energy levels been this week?
2. How has your sleep been?
3. Any significant stressors or challenges?
4. Have you noticed any changes in your symptoms?

Please rate your current anxiety level (1-10) as well."""
        
        if not user_input:
            return {
                'content': check_in_prompt,
                'phase_complete': False,
                'topics': ['symptom_check', 'energy_sleep']
            }
        
        # Process check-in response
        gemini_response = await self.gemini_client.generate_therapeutic_response(
            user_input, context
        )
        
        # Extract additional ratings
        energy_rating = self._extract_rating(user_input, ['energy', 'energetic'])
        anxiety_rating = self._extract_rating(user_input, ['anxiety', 'anxious', 'worry'])
        
        if energy_rating:
            session_state.mood_ratings['energy'] = energy_rating
        if anxiety_rating:
            session_state.mood_ratings['anxiety'] = anxiety_rating
        
        check_in_complete = len(session_state.mood_ratings) >= 2  # At least mood and one other rating
        
        return {
            'content': gemini_response.content,
            'phase_complete': check_in_complete,
            'next_phase': SessionPhase.HOMEWORK_REVIEW.value if check_in_complete else SessionPhase.CHECK_IN.value,
            'topics': ['symptom_monitoring', 'weekly_review'],
            'interventions': [gemini_response.intervention_used] if gemini_response.intervention_used else []
        }
    
    async def _handle_homework_review_phase(self, session_state: SessionState, user_input: str, 
                                          context: ConversationContext) -> Dict[str, Any]:
        """Handle homework review from previous session"""
        
        # Get pending homework assignments
        pending_homework = self.homework_system.get_patient_assignments(
            session_state.patient_id, status='active'
        )
        
        if not pending_homework and not user_input:
            # No homework to review, move to next phase
            return {
                'content': "It looks like there's no homework to review from last session. Let's move on to today's work.",
                'phase_complete': True,
                'next_phase': SessionPhase.MAIN_WORK.value,
                'topics': ['no_homework']
            }
        
        if not user_input:
            # Present homework for review
            homework_review_prompt = "Let's review your homework from our last session:\n\n"
            
            for hw in pending_homework[:3]:  # Review up to 3 assignments
                homework_review_prompt += f"• {hw['description']}\n"
            
            homework_review_prompt += "\nHow did these assignments go? What did you learn or notice? Were there any challenges?"
            
            return {
                'content': homework_review_prompt,
                'phase_complete': False,
                'topics': ['homework_review'],
                'instructions': 'Please share how your homework assignments went this week.'
            }
        
        else:
            # Process homework review response
            context.phase = SessionPhase.HOMEWORK_REVIEW.value
            gemini_response = await self.gemini_client.generate_therapeutic_response(
                user_input, context
            )
            
            # Update homework completion based on response
            self._process_homework_feedback(user_input, pending_homework)
            
            # Check if review is complete
            review_complete = self._assess_homework_review_completeness(user_input)
            
            return {
                'content': gemini_response.content,
                'phase_complete': review_complete,
                'next_phase': SessionPhase.MAIN_WORK.value if review_complete else SessionPhase.HOMEWORK_REVIEW.value,
                'topics': ['homework_completion', 'learning_insights'],
                'interventions': [gemini_response.intervention_used] if gemini_response.intervention_used else []
            }
    
    async def _handle_assessment_phase(self, session_state: SessionState, user_input: str, 
                                     context: ConversationContext) -> Dict[str, Any]:
        """Handle assessment administration during session"""
        
        # Determine if assessment is needed
        if 'assessment_type' not in context.current_goals:
            # Auto-determine assessment based on patient history and symptoms
            assessment_type = self._determine_needed_assessment(session_state.patient_id)
        else:
            assessment_type = context.current_goals.get('assessment_type')
        
        if not assessment_type:
            return {
                'content': "No assessment needed at this time. Let's continue with our therapy work.",
                'phase_complete': True,
                'next_phase': SessionPhase.MAIN_WORK.value,
                'topics': ['no_assessment_needed']
            }
        
        # Administer assessment (this would typically be interactive)
        assessment_prompt = f"""I'd like to have you complete a brief {assessment_type} assessment to track your progress. 

This will help us monitor how you're doing and adjust our treatment approach if needed. The assessment takes about 5-10 minutes.

Are you ready to proceed with the {assessment_type} assessment?"""
        
        if not user_input:
            return {
                'content': assessment_prompt,
                'phase_complete': False,
                'topics': ['assessment_administration']
            }
        
        # Process assessment consent and administration
        if any(word in user_input.lower() for word in ['yes', 'ready', 'sure', 'ok']):
            # In a real implementation, this would launch the assessment interface
            session_state.assessments_completed.append(assessment_type)
            
            return {
                'content': f"Great! I'll have you complete the {assessment_type} assessment now. Please answer each question honestly based on how you've been feeling recently.",
                'phase_complete': True,
                'next_phase': SessionPhase.MAIN_WORK.value,
                'topics': ['assessment_started'],
                'assessment_launched': assessment_type
            }
        else:
            return {
                'content': "That's okay. We can skip the assessment for today and focus on our therapy work. We can always do it next session if you'd prefer.",
                'phase_complete': True,
                'next_phase': SessionPhase.MAIN_WORK.value,
                'topics': ['assessment_declined']
            }
    
    async def _handle_main_work_phase(self, session_state: SessionState, user_input: str, 
                                    context: ConversationContext) -> Dict[str, Any]:
        """Handle the main therapeutic work of the session"""
        
        context.phase = SessionPhase.MAIN_WORK.value
        
        # Generate therapeutic response based on modality and patient needs
        gemini_response = await self.gemini_client.generate_therapeutic_response(
            user_input, context
        )
        
        # Track intervention used
        if gemini_response.intervention_used:
            session_state.interventions_used.append(gemini_response.intervention_used)
        
        # Extract topics from the conversation
        topics = self._extract_topics_from_response(gemini_response.content)
        session_state.topics_discussed.extend(topics)
        
        # Check if main work phase should continue
        main_work_complete = self._assess_main_work_completeness(session_state, user_input)
        
        return {
            'content': gemini_response.content,
            'phase_complete': main_work_complete,
            'next_phase': SessionPhase.SKILL_PRACTICE.value if main_work_complete else SessionPhase.MAIN_WORK.value,
            'topics': topics,
            'interventions': [gemini_response.intervention_used] if gemini_response.intervention_used else [],
            'engagement_indicators': self._assess_engagement(user_input)
        }
    
    async def _handle_skill_practice_phase(self, session_state: SessionState, user_input: str, 
                                         context: ConversationContext) -> Dict[str, Any]:
        """Handle in-session skill practice and rehearsal"""
        
        # Suggest skill practice based on modality and session content
        skill_to_practice = self._suggest_skill_practice(session_state)
        
        if not user_input:
            if skill_to_practice:
                skill_prompt = f"""Let's practice the {skill_to_practice} technique we've been working on.

This will help you feel more confident using this skill between sessions. Would you like to try a brief practice exercise now?"""
                
                return {
                    'content': skill_prompt,
                    'phase_complete': False,
                    'topics': ['skill_practice_introduction']
                }
            else:
                # Skip if no specific skill to practice
                return {
                    'content': "Let's move on to planning your homework for this week.",
                    'phase_complete': True,
                    'next_phase': SessionPhase.HOMEWORK_ASSIGNMENT.value,
                    'topics': ['skip_skill_practice']
                }
        
        # Process skill practice
        context.phase = SessionPhase.SKILL_PRACTICE.value
        gemini_response = await self.gemini_client.generate_therapeutic_response(
            user_input, context
        )
        
        # Check if practice is complete
        practice_complete = self._assess_skill_practice_completion(user_input)
        
        return {
            'content': gemini_response.content,
            'phase_complete': practice_complete,
            'next_phase': SessionPhase.HOMEWORK_ASSIGNMENT.value if practice_complete else SessionPhase.SKILL_PRACTICE.value,
            'topics': ['skill_rehearsal', skill_to_practice] if skill_to_practice else ['skill_rehearsal'],
            'interventions': [f"{skill_to_practice} practice"] if skill_to_practice else []
        }
    
    async def _handle_homework_assignment_phase(self, session_state: SessionState, user_input: str, 
                                              context: ConversationContext) -> Dict[str, Any]:
        """Handle homework assignment for the upcoming week"""
        
        if not user_input:
            # Suggest homework based on session content and modality
            suggested_homework = self._suggest_homework_assignments(session_state)
            
            if suggested_homework:
                homework_prompt = f"""Based on our work today, I'd like to suggest some homework assignments for this week:

{suggested_homework}

These assignments will help you practice what we've discussed and continue making progress between sessions. How do these sound to you?"""
            else:
                homework_prompt = "What would you like to work on between now and our next session? Any specific goals or practices you'd like to focus on?"
            
            return {
                'content': homework_prompt,
                'phase_complete': False,
                'topics': ['homework_assignment']
            }
        
        # Process homework assignment discussion
        context.phase = SessionPhase.HOMEWORK_ASSIGNMENT.value
        gemini_response = await self.gemini_client.generate_therapeutic_response(
            user_input, context
        )
        
        # Create homework assignments based on discussion
        homework_assignments = self._process_homework_assignment(session_state, user_input)
        session_state.homework_assigned.extend(homework_assignments)
        
        assignment_complete = len(homework_assignments) > 0 or "no homework" in user_input.lower()
        
        return {
            'content': gemini_response.content,
            'phase_complete': assignment_complete,
            'next_phase': SessionPhase.GOAL_REVIEW.value if assignment_complete else SessionPhase.HOMEWORK_ASSIGNMENT.value,
            'topics': ['homework_planning'],
            'homework_assigned': homework_assignments
        }
    
    async def _handle_goal_review_phase(self, session_state: SessionState, user_input: str, 
                                      context: ConversationContext) -> Dict[str, Any]:
        """Handle treatment goal review and progress check"""
        
        # Get active goals
        active_goals = self.goal_manager.get_patient_goals(
            session_state.patient_id, status='active'
        )
        
        if not active_goals and not user_input:
            return {
                'content': "Let's wrap up today's session. How are you feeling about the work we did today?",
                'phase_complete': True,
                'next_phase': SessionPhase.CLOSING.value,
                'topics': ['no_goals_to_review']
            }
        
        if not user_input:
            goal_review_prompt = "Let's briefly check in on your treatment goals:\n\n"
            
            for goal in active_goals[:2]:  # Review top 2 goals
                goal_review_prompt += f"• {goal['goal_description']}\n  Current progress: {goal['current_progress']}%\n\n"
            
            goal_review_prompt += "How do you feel about your progress on these goals? Any updates or insights to share?"
            
            return {
                'content': goal_review_prompt,
                'phase_complete': False,
                'topics': ['goal_review']
            }
        
        # Process goal review response
        context.phase = SessionPhase.GOAL_REVIEW.value
        gemini_response = await self.gemini_client.generate_therapeutic_response(
            user_input, context
        )
        
        # Update goal progress if indicated in response
        self._process_goal_updates(session_state, user_input, active_goals)
        
        return {
            'content': gemini_response.content,
            'phase_complete': True,
            'next_phase': SessionPhase.CLOSING.value,
            'topics': ['goal_progress_review'],
            'interventions': [gemini_response.intervention_used] if gemini_response.intervention_used else []
        }
    
    async def _handle_closing_phase(self, session_state: SessionState, user_input: str, 
                                  context: ConversationContext) -> Dict[str, Any]:
        """Handle session closing and wrap-up"""
        
        if not user_input:
            closing_prompt = f"""We're coming to the end of our session today. Before we finish:

1. How are you feeling now compared to when we started? (Rate 1-10)
2. What was most helpful about today's session?
3. Is there anything else you'd like to discuss or any concerns for the week ahead?

Remember, you have your homework assignments to work on, and I'm here if you need support."""
            
            return {
                'content': closing_prompt,
                'phase_complete': False,
                'topics': ['session_wrap_up']
            }
        
        # Process closing feedback
        context.phase = SessionPhase.CLOSING.value
        gemini_response = await self.gemini_client.generate_therapeutic_response(
            user_input, context
        )
        
        # Extract end-of-session mood rating
        end_mood = self._extract_mood_rating(user_input)
        if end_mood:
            session_state.mood_ratings['session_end'] = end_mood
            
            # Update session record
            self.db.execute_update(
                "UPDATE sessions SET mood_after = ? WHERE id = ?",
                (end_mood, session_state.session_id)
            )
        
        # Store patient feedback
        session_state.patient_feedback = user_input
        
        return {
            'content': gemini_response.content + "\n\nThank you for today's session. Take care, and I'll see you next time!",
            'phase_complete': True,
            'next_phase': SessionPhase.COMPLETED.value,
            'topics': ['session_feedback', 'session_closing'],
            'session_ending': True
        }
    
    async def _handle_emergency_intervention(self, session_state, user_input, context=None):
        """Handle emergency/crisis intervention"""
        
        # Get crisis response from crisis manager
        crisis_alert = self.crisis_manager.detect_crisis(user_input, session_state.patient_id)
        # Create a direct crisis response instead of calling get_crisis_response
        crisis_response = '''🚨 I'm concerned about your safety right now. Let's talk about this together.

        I want you to know that you're not alone, and there are people who want to help you through this difficult time.

        Right now, are you having thoughts of hurting yourself or ending your life?

        If you're in immediate danger, please:
        - Call 988 (Suicide & Crisis Lifeline)  
        - Go to your nearest emergency room
        - Call 100

        We can work through this together. Can you tell me what's happening right now?'''
        
        # Update session to reflect crisis intervention
        self.db.execute_update(
            "UPDATE sessions SET crisis_flags = ?, session_phase = ? WHERE id = ?",
            (json.dumps([crisis_alert.crisis_level]), SessionPhase.EMERGENCY_INTERVENTION.value, session_state.session_id)
        )
        
        # Mark session as emergency status
        session_state.status = SessionStatus.EMERGENCY.value
        
        return {
            'content': crisis_response,
            'phase_complete': False,  # Emergency intervention continues until resolved
            'topics': ['crisis_intervention', 'safety_planning'],
            'crisis_level': crisis_alert.crisis_level,
            'emergency_resources_provided': True,
            'requires_immediate_attention': True
        }
    
    async def end_session(self, patient_id: int, session_summary: str = "") -> Dict[str, Any]:
        """End the current session and finalize documentation"""
        
        if patient_id not in self.active_sessions:
            raise ValueError(f"No active session found for patient {patient_id}")
        
        session_state = self.active_sessions[patient_id]
        
        # Mark session as completed
        session_state.current_phase = SessionPhase.COMPLETED.value
        session_state.status = SessionStatus.COMPLETED.value
        session_state.session_summary = session_summary
        
        # Update session record with final data
        session_updates = {
            'completed': True,
            'session_phase': SessionPhase.COMPLETED.value,
            'interventions_used': json.dumps(session_state.interventions_used),
            'homework_assigned': '; '.join(session_state.homework_assigned),
            'therapist_notes': '; '.join(session_state.therapist_observations),
            'patient_feedback': session_state.patient_feedback
        }
        # Build update query
        update_parts = []
        update_values = []
        
        for key, value in session_updates.items():
            update_parts.append(f"{key} = ?")
            update_values.append(value)
        
        update_values.append(session_state.session_id)
        
        self.db.execute_update(
            f"UPDATE sessions SET {', '.join(update_parts)} WHERE id = ?",
            tuple(update_values)
        )
        
        # Generate session documentation
        documentation_result = await self._generate_session_documentation(session_state)
        
        # Calculate session metrics
        session_metrics = self._calculate_final_session_metrics(session_state)
        
        # Remove from active sessions
        del self.active_sessions[patient_id]
        
        log_action(f"Session completed", "session_manager", 
                  patient_id=patient_id, session_id=session_state.session_id)
        
        return {
            'session_id': session_state.session_id,
            'patient_id': patient_id,
            'session_duration': self._calculate_session_duration(session_state),
            'phases_completed': session_state.phases_completed,
            'interventions_used': session_state.interventions_used,
            'topics_discussed': session_state.topics_discussed,
            'homework_assigned_count': len(session_state.homework_assigned),
            'assessments_completed': session_state.assessments_completed,
            'mood_change': self._calculate_mood_change(session_state),
            'session_metrics': session_metrics,
            'documentation_generated': documentation_result,
            'crisis_detected': session_state.crisis_detected,
            'status': session_state.status
        }
    
    async def _generate_session_documentation(self, session_state: SessionState) -> Dict[str, Any]:
        """Generate comprehensive session documentation"""
        
        try:
            # Generate SOAP note
            soap_note = self.documentation_system.generate_auto_soap_note(
                session_state.patient_id, session_state.session_id
            )
            
            documentation_result = {
                'soap_note_generated': True,
                'soap_note_id': soap_note.id,
                'documentation_complete': True
            }
        
        except Exception as e:
            log_action(f"Error generating documentation: {e}", "session_manager", "ERROR")
            documentation_result = {
                'soap_note_generated': False,
                'error': str(e),
                'documentation_complete': False
            }
        
        return documentation_result
    
    def get_session_status(self, patient_id: int) -> Dict[str, Any]:
        """Get current session status and progress"""
        
        if patient_id not in self.active_sessions:
            return {
                'active_session': False,
                'message': 'No active session found'
            }
        
        session_state = self.active_sessions[patient_id]
        
        return {
            'active_session': True,
            'session_id': session_state.session_id,
            'current_phase': session_state.current_phase,
            'phases_completed': session_state.phases_completed,
            'session_progress': self._calculate_phase_progress(session_state),
            'estimated_time_remaining': self._estimate_time_remaining(session_state),
            'therapy_modality': session_state.therapy_modality,
            'topics_discussed': session_state.topics_discussed,
            'interventions_used': session_state.interventions_used,
            'mood_ratings': session_state.mood_ratings,
            'crisis_detected': session_state.crisis_detected,
            'engagement_level': session_state.engagement_level
        }
    
    async def _transition_to_phase(self, session_state: SessionState, next_phase: str) -> None:
        """Transition to the next phase of the session"""
        
        # Mark current phase as completed
        if session_state.current_phase not in session_state.phases_completed:
            session_state.phases_completed.append(session_state.current_phase)
        
        # Update to next phase
        previous_phase = session_state.current_phase
        session_state.current_phase = next_phase
        session_state.phase_start_time = datetime.now().isoformat()
        
        # Update database
        self.db.execute_update(
            "UPDATE sessions SET session_phase = ? WHERE id = ?",
            (next_phase, session_state.session_id)
        )
        
        log_action(f"Phase transition: {previous_phase} -> {next_phase}", 
                  "session_manager", session_id=session_state.session_id)
    
    def _extract_mood_rating(self, text: str) -> Optional[int]:
        """Extract mood rating from user input"""
        import re
        
        # Look for patterns like "7/10", "7 out of 10", "mood is 7"
        patterns = [
            r'(\d+)\s*(?:/|out of)\s*10',
            r'mood\s*(?:is|:)?\s*(\d+)',
            r'feeling\s*(?:like\s*)?(?:a\s*)?(\d+)',
            r'\b(\d+)\s*(?:today|right now|currently)'
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                rating = int(match.group(1))
                if 1 <= rating <= 10:
                    return rating
        
        return None
    
    def _extract_rating(self, text: str, keywords: List[str]) -> Optional[int]:
        """Extract rating for specific keywords from user input"""
        import re
        
        text_lower = text.lower()
        
        for keyword in keywords:
            # Look for patterns near the keyword
            pattern = rf'{keyword}.*?(\d+)(?:/10|out of 10)?'
            match = re.search(pattern, text_lower)
            if match:
                rating = int(match.group(1))
                if 1 <= rating <= 10:
                    return rating
        
        return None
    
    def _assess_opening_completeness(self, user_input: str, session_state: SessionState) -> bool:
        """Assess if opening phase is complete"""
        
        # Check if mood rating was provided
        has_mood_rating = 'session_start' in session_state.mood_ratings
        
        # Check if user provided substantive information
        has_content = len(user_input.strip()) > 20
        
        # Check for session goals or focus
        has_goals = any(word in user_input.lower() for word in 
                       ['want to', 'focus on', 'work on', 'discuss', 'talk about'])
        
        return has_mood_rating and has_content and (has_goals or len(user_input) > 50)
    
    def _assess_homework_review_completeness(self, user_input: str) -> bool:
        """Assess if homework review is complete"""
        
        completion_indicators = [
            'completed', 'finished', 'did all', 'done with',
            'learned', 'noticed', 'helpful', 'challenging',
            'struggled', 'easy', 'difficult'
        ]
        
        return any(indicator in user_input.lower() for indicator in completion_indicators)
    
    def _assess_main_work_completeness(self, session_state: SessionState, user_input: str) -> bool:
        """Assess if main work phase should continue"""
        
        # Check session duration
        session_start = datetime.fromisoformat(session_state.phase_start_time)
        minutes_in_main_work = (datetime.now() - session_start).total_seconds() / 60
        
        # Main work should be substantial portion of session
        target_main_work_time = Config.DEFAULT_SESSION_DURATION * 0.5  # 50% of session
        
        # Continue if haven't reached target time and user is engaged
        if minutes_in_main_work < target_main_work_time:
            return False
        
        # Check for natural conclusion indicators
        conclusion_indicators = [
            'makes sense', 'understand now', 'that helps',
            'feeling better', 'good strategy', 'will try that'
        ]
        
        return any(indicator in user_input.lower() for indicator in conclusion_indicators)
    
    def _assess_skill_practice_completion(self, user_input: str) -> bool:
        """Assess if skill practice is complete"""
        
        completion_indicators = [
            'got it', 'understand', 'makes sense', 'will practice',
            'feels good', 'helpful', 'ready to try', 'confident'
        ]
        
        return any(indicator in user_input.lower() for indicator in completion_indicators)
    
    def _assess_engagement(self, user_input: str) -> Dict[str, Any]:
        """Assess patient engagement level from input"""
        
        engagement_indicators = {
            'high_engagement': [
                'interesting', 'helpful', 'makes sense', 'i see',
                'that\'s right', 'exactly', 'yes', 'good point'
            ],
            'medium_engagement': [
                'okay', 'sure', 'i guess', 'maybe', 'possibly'
            ],
            'low_engagement': [
                'don\'t know', 'whatever', 'sure', 'fine', 'i suppose'
            ]
        }
        
        text_lower = user_input.lower()
        
        for level, indicators in engagement_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return {
                    'level': level,
                    'indicators_found': [ind for ind in indicators if ind in text_lower]
                }
        
        # Default based on response length and content
        if len(user_input.strip()) > 50:
            return {'level': 'medium_engagement', 'reason': 'substantial_response'}
        else:
            return {'level': 'low_engagement', 'reason': 'brief_response'}
    
    def _update_engagement_metrics(self, session_state: SessionState, engagement_indicators: Dict[str, Any]) -> None:
        """Update session engagement metrics"""
        
        engagement_mapping = {
            'high_engagement': 9,
            'medium_engagement': 6,
            'low_engagement': 3
        }
        
        level = engagement_indicators.get('level', 'medium_engagement')
        new_rating = engagement_mapping.get(level, 6)
        
        # Update engagement with moving average
        current_engagement = session_state.engagement_level
        session_state.engagement_level = round((current_engagement + new_rating) / 2)
    
    def _determine_needed_assessment(self, patient_id: int) -> Optional[str]:
        """Determine what assessment might be needed"""
        
        # Get last assessments
        recent_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 5",
            (patient_id,)
        )
        
        # Check if any major assessment is overdue (>30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        assessment_types_completed = set()
        for assessment in recent_assessments:
            if assessment['assessment_date'] > thirty_days_ago:
                assessment_types_completed.add(assessment['assessment_type'])
        
        # Suggest assessment based on what's missing
        priority_assessments = ['PHQ9', 'GAD7', 'ORS']
        
        for assessment_type in priority_assessments:
            if assessment_type not in assessment_types_completed:
                return assessment_type
        
        return None
    
    def _suggest_skill_practice(self, session_state: SessionState) -> Optional[str]:
        """Suggest skill to practice based on session content and modality"""
        
        modality_skills = {
            'CBT': ['thought challenging', 'cognitive restructuring', 'behavioral activation'],
            'DBT': ['mindfulness', 'distress tolerance', 'emotion regulation'],
            'ACT': ['cognitive defusion', 'values clarification', 'mindful acceptance']
        }
        
        available_skills = modality_skills.get(session_state.therapy_modality, [])
        
        # Choose skill based on interventions used
        for intervention in session_state.interventions_used:
            for skill in available_skills:
                if skill.lower() in intervention.lower():
                    return skill
        
        # Default to first skill for modality
        return available_skills[0] if available_skills else None
    
    def _suggest_homework_assignments(self, session_state: SessionState) -> str:
        """Suggest homework based on session content"""
        
        suggestions = []
        
        # Based on modality
        if session_state.therapy_modality == 'CBT':
            if 'cognitive restructuring' in session_state.interventions_used:
                suggestions.append("• Complete daily thought records when you notice difficult emotions")
            if 'behavioral activation' in session_state.interventions_used:
                suggestions.append("• Schedule 2-3 pleasant activities for this week")
        
        elif session_state.therapy_modality == 'DBT':
            if 'mindfulness' in session_state.interventions_used:
                suggestions.append("• Practice mindfulness exercises for 10 minutes daily")
            if 'distress tolerance' in session_state.interventions_used:
                suggestions.append("• Use distress tolerance skills when needed and track effectiveness")
        
        elif session_state.therapy_modality == 'ACT':
            if 'values' in session_state.interventions_used:
                suggestions.append("• Take one small action toward your values each day")
            if 'defusion' in session_state.interventions_used:
                suggestions.append("• Practice cognitive defusion techniques with difficult thoughts")
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "• Keep a brief daily mood log (1-10 scale)",
                "• Practice one coping skill we discussed when feeling stressed"
            ]
        
        return '\n'.join(suggestions)
    
    def _process_homework_feedback(self, feedback: str, homework_assignments: List[Dict[str, Any]]) -> None:
        """Process homework completion feedback"""
        
        feedback_lower = feedback.lower()
        
        for homework in homework_assignments:
            # Simple completion detection
            if any(word in feedback_lower for word in ['completed', 'finished', 'did it', 'done']):
                # Mark as completed (simplified)
                self.homework_system.complete_assignment(
                    homework['id'],
                    completion_notes=feedback[:200],  # First 200 chars
                    effectiveness_rating=4  # Default good rating
                )
    
    def _process_homework_assignment(self, session_state: SessionState, discussion: str) -> List[str]:
        """Process homework assignment discussion and create assignments"""
        
        assignments = []
        
        # Extract specific homework mentioned in discussion
        if 'thought record' in discussion.lower():
            assignments.append('Daily thought records')
        
        if 'activity' in discussion.lower() and 'schedule' in discussion.lower():
            assignments.append('Weekly activity scheduling')
        
        if 'mindfulness' in discussion.lower():
            assignments.append('Daily mindfulness practice')
        
        # If no specific assignments mentioned, use suggestions
        if not assignments:
            suggested = self._suggest_homework_assignments(session_state)
            assignments = [line.strip('• ') for line in suggested.split('\n') if line.strip()]
        
        return assignments[:3]  # Limit to 3 assignments
    
    def _process_goal_updates(self, session_state: SessionState, feedback: str, 
                            active_goals: List[Dict[str, Any]]) -> None:
        """Process goal progress updates from patient feedback"""
        
        feedback_lower = feedback.lower()
        
        # Look for progress indicators
        if any(word in feedback_lower for word in ['better', 'improving', 'progress', 'easier']):
            # Update first goal with progress increase
            if active_goals:
                current_progress = active_goals[0]['current_progress']
                new_progress = min(100, current_progress + 10)  # Increase by 10%
                
                self.goal_manager.update_goal_progress(
                    active_goals[0]['id'],
                    new_progress,
                    notes=f"Progress noted in session: {feedback[:100]}"
                )
    
    def _extract_topics_from_response(self, response_content: str) -> List[str]:
        """Extract discussion topics from response content"""
        
        topics = []
        content_lower = response_content.lower()
        
        # Topic indicators
        topic_keywords = {
            'anxiety': ['anxiety', 'anxious', 'worry', 'nervous'],
            'depression': ['depression', 'depressed', 'sad', 'hopeless'],
            'relationships': ['relationship', 'partner', 'family', 'friends'],
            'work_stress': ['work', 'job', 'career', 'workplace'],
            'coping_skills': ['coping', 'manage', 'handle', 'deal with'],
            'therapy_progress': ['progress', 'improvement', 'better', 'worse']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics[:3]  # Limit to 3 main topics
    
    def _calculate_phase_progress(self, session_state: SessionState) -> Dict[str, Any]:
        """Calculate session phase progress"""
        
        total_phases = len(SessionPhase) - 2  # Exclude NOT_STARTED and COMPLETED
        completed_phases = len(session_state.phases_completed)
        
        progress_percentage = (completed_phases / total_phases) * 100
        
        return {
            'completed_phases': completed_phases,
            'total_phases': total_phases,
            'progress_percentage': round(progress_percentage, 1),
            'current_phase': session_state.current_phase,
            'next_phase': self._get_next_phase(session_state.current_phase)
        }
    
    def _estimate_time_remaining(self, session_state: SessionState) -> int:
        """Estimate remaining session time in minutes"""
        
        session_start = datetime.fromisoformat(session_state.phase_start_time)
        elapsed_minutes = (datetime.now() - session_start).total_seconds() / 60
        
        return max(0, Config.DEFAULT_SESSION_DURATION - int(elapsed_minutes))
    
    def _get_next_phase(self, current_phase: str) -> str:
        """Get the next logical phase"""
        
        phase_order = [
            SessionPhase.OPENING.value,
            SessionPhase.HOMEWORK_REVIEW.value,
            SessionPhase.MAIN_WORK.value,
            SessionPhase.SKILL_PRACTICE.value,
            SessionPhase.HOMEWORK_ASSIGNMENT.value,
            SessionPhase.GOAL_REVIEW.value,
            SessionPhase.CLOSING.value,
            SessionPhase.COMPLETED.value
        ]
        
        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass
        
        return SessionPhase.COMPLETED.value
    
    def _get_session_structure(self, therapy_modality: str) -> Dict[str, Any]:
        """Get session structure for specific modality"""
        
        structures = {
            'CBT': {
                'total_duration': 50,
                'phases': {
                    'opening': 5,
                    'homework_review': 10,
                    'main_work': 25,
                    'skill_practice': 5,
                    'homework_assignment': 3,
                    'closing': 2
                }
            },
            'DBT': {
                'total_duration': 50,
                'phases': {
                    'opening': 5,
                    'homework_review': 8,
                    'main_work': 20,
                    'skill_practice': 12,
                    'homework_assignment': 3,
                    'closing': 2
                }
            },
            'ACT': {
                'total_duration': 50,
                'phases': {
                    'opening': 5,
                    'values_connection': 10,
                    'main_work': 20,
                    'skill_practice': 10,
                    'commitment_planning': 3,
                    'closing': 2
                }
            }
        }
        
        return structures.get(therapy_modality, structures['CBT'])
    
    def _calculate_session_duration(self, session_state: SessionState) -> int:
        """Calculate actual session duration in minutes"""
        
        try:
            start_time = datetime.fromisoformat(session_state.phase_start_time)
            duration_minutes = (datetime.now() - start_time).total_seconds() / 60
            return round(duration_minutes)
        except:
            return Config.DEFAULT_SESSION_DURATION
    
    def _calculate_mood_change(self, session_state: SessionState) -> Optional[int]:
        """Calculate mood change from start to end"""
        
        start_mood = session_state.mood_ratings.get('session_start')
        end_mood = session_state.mood_ratings.get('session_end')
        
        if start_mood and end_mood:
            return end_mood - start_mood
        
        return None
    
    def _get_session_metrics(self, session_state: SessionState) -> Dict[str, Any]:
        """Get current session metrics"""
        
        return {
            'engagement_level': session_state.engagement_level,
            'phases_completed_count': len(session_state.phases_completed),
            'interventions_used_count': len(session_state.interventions_used),
            'topics_discussed_count': len(session_state.topics_discussed),
            'mood_ratings_collected': len(session_state.mood_ratings),
            'crisis_detected': session_state.crisis_detected,
            'homework_assignments': len(session_state.homework_assigned)
        }
    
    def _calculate_final_session_metrics(self, session_state: SessionState) -> Dict[str, Any]:
        """Calculate final session metrics for documentation"""
        
        metrics = self._get_session_metrics(session_state)
        
        # Add completion metrics
        metrics.update({
            'session_completion_rate': (len(session_state.phases_completed) / 7) * 100,  # 7 main phases
            'therapeutic_alliance_estimated': session_state.engagement_level,
            'session_effectiveness_indicators': {
                'mood_improvement': self._calculate_mood_change(session_state),
                'engagement_maintained': session_state.engagement_level >= 6,
                'structured_completion': len(session_state.phases_completed) >= 5,
                'homework_assigned': len(session_state.homework_assigned) > 0
            }
        })
        
        return metrics


# Utility functions
def create_quick_session(db: DatabaseManager, patient_id: int, 
                        therapy_type: str = "CBT") -> Dict[str, Any]:
    """Quick session creation helper"""
    
    session_manager = SessionManager(db)
    
    # Start session synchronously for testing
    import asyncio
    
    result = asyncio.run(session_manager.start_session(patient_id, therapy_type))
    
    return {
        'session_started': True,
        'session_id': result['session_id'],
        'therapy_modality': result['therapy_modality'],
        'initial_response': result['response'][:100] + "..." if len(result['response']) > 100 else result['response']
    }


def get_session_dashboard_data(db: DatabaseManager, patient_id: int) -> Dict[str, Any]:
    """Get session dashboard data for patient"""
    
    session_manager = SessionManager(db)
    
    # Get session status
    session_status = session_manager.get_session_status(patient_id)
    
    # Get recent sessions
    recent_sessions = db.execute_query(
        "SELECT * FROM sessions WHERE patient_id = ? ORDER BY session_date DESC LIMIT 5",
        (patient_id,)
    )
    
    # Calculate session statistics
    total_sessions = len(recent_sessions)
    completed_sessions = len([s for s in recent_sessions if s['completed']])
    
    avg_mood_improvement = 0
    if recent_sessions:
        mood_improvements = []
        for session in recent_sessions:
            if session.get('mood_before') and session.get('mood_after'):
                improvement = session['mood_after'] - session['mood_before']
                mood_improvements.append(improvement)
        
        if mood_improvements:
            avg_mood_improvement = sum(mood_improvements) / len(mood_improvements)
    
    return {
        'patient_id': patient_id,
        'active_session': session_status['active_session'],
        'current_session_info': session_status if session_status['active_session'] else None,
        'recent_sessions_count': total_sessions,
        'completion_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        'average_mood_improvement': round(avg_mood_improvement, 1),
        'recent_session_types': [s['session_type'] for s in recent_sessions],
        'last_session_date': recent_sessions[0]['session_date'] if recent_sessions else None
    }


# Test function
def main():
    """Test session management functionality"""
    from database import DatabaseManager
    
    print("Testing Session Manager...")
    
    db = DatabaseManager(":memory:")
    session_manager = SessionManager(db)
    
    # Create test patient
    patient_id = db.execute_update(
        "INSERT INTO patients (name, preferred_therapy_mode) VALUES (?, ?)",
        ("Test Patient", "CBT")
    )
    
    print(f"Created test patient ID: {patient_id}")
    
    # Test session creation
    print("\n1. Testing session start...")
    try:
        import asyncio
        
        session_result = asyncio.run(
            session_manager.start_session(patient_id, "CBT")
        )
        
        print(f"Started session ID: {session_result['session_id']}")
        print(f"Current phase: {session_result['current_phase']}")
        print(f"Response length: {len(session_result['response'])} characters")
        
        # Test session status
        print("\n2. Testing session status...")
        status = session_manager.get_session_status(patient_id)
        print(f"Active session: {status['active_session']}")
        print(f"Current phase: {status.get('current_phase', 'N/A')}")
        print(f"Engagement level: {status.get('engagement_level', 'N/A')}")
        
        # Test user input processing
        print("\n3. Testing user input processing...")
        test_input = "I'm feeling okay today, maybe a 6 out of 10. I want to work on my anxiety."
        
        input_result = asyncio.run(
            session_manager.process_user_input(patient_id, test_input)
        )
        
        print(f"Response generated: {len(input_result['response'])} characters")
        print(f"Phase after input: {input_result['current_phase']}")
        
        # Test session end
        print("\n4. Testing session end...")
        end_result = asyncio.run(
            session_manager.end_session(patient_id, "Good session with progress on anxiety management")
        )
        
        print(f"Session ended: {end_result['session_id']}")
        print(f"Interventions used: {len(end_result['interventions_used'])}")
        print(f"Documentation generated: {end_result['documentation_generated']['documentation_complete']}")
        
    except Exception as e:
        print(f"Error during async testing: {e}")
        
        # Test synchronous helper
        print("\n5. Testing synchronous helper...")
        quick_session = create_quick_session(db, patient_id, "CBT")
        print(f"Quick session created: {quick_session['session_started']}")
    
    # Test dashboard data
    print("\n6. Testing dashboard data...")
    dashboard = get_session_dashboard_data(db, patient_id)
    print(f"Recent sessions: {dashboard['recent_sessions_count']}")
    print(f"Active session: {dashboard['active_session']}")
    
    print("\nSession manager testing completed!")


if __name__ == "__main__":
    main()