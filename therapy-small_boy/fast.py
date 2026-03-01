from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import json
import sqlite3
import uuid
from contextlib import contextmanager
import google.generativeai as genai
from enum import Enum
from datetime import datetime, timedelta
import re
import logging
from collections import Counter

# Import recommendation engine
from recommendations import RecommendationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Complete AI Therapist System",
    description="Comprehensive AI-powered therapy system with sessions, assessments, recommendations, and diagnosis documentation",
    version="2.0.0"
)

# Add CORS middleware - MUST be before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add OPTIONS handler for preflight requests
@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Configure Gemini
genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")  # Replace with your API key

# Database setup
DATABASE_PATH = "therapy.db"

class SessionPhase(Enum):
    INTAKE = "intake"
    ASSESSMENT = "assessment"
    THERAPY = "therapy"
    GOAL_SETTING = "goal_setting"
    HOMEWORK_ASSIGNMENT = "homework_assignment"
    CLOSING = "closing"
    COMPLETED = "completed"

def init_database():
    """Initialize SQLite database with all required tables"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        # Check if we need to migrate existing tables
        try:
            # Try to add missing columns if tables exist
            conn.execute("ALTER TABLE treatment_goals ADD COLUMN session_id INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists or table doesn't exist
        
        try:
            conn.execute("ALTER TABLE homework_assignments ADD COLUMN session_id INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists or table doesn't exist
            
        try:
            conn.execute("ALTER TABLE interactive_sessions ADD COLUMN recommendation_data TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists or table doesn't exist
        
        # Patients table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT,
                created_date TEXT DEFAULT (datetime('now')),
                preferred_therapy_mode TEXT DEFAULT 'CBT',
                detected_symptoms TEXT DEFAULT '[]',
                notes TEXT
            )
        ''')
        
        # Interactive sessions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS interactive_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_date TEXT DEFAULT (datetime('now')),
                current_phase TEXT DEFAULT 'intake',
                conversation_history TEXT DEFAULT '[]',
                detected_symptoms TEXT DEFAULT '[]',
                session_insights TEXT DEFAULT '[]',
                mood_ratings TEXT DEFAULT '[]',
                assessment_results TEXT DEFAULT '{}',
                generated_goals TEXT DEFAULT '[]',
                assigned_homework TEXT DEFAULT '{}',
                session_completed BOOLEAN DEFAULT FALSE,
                total_exchanges INTEGER DEFAULT 0,
                crisis_flags TEXT DEFAULT '[]',
                recommendation_data TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        ''')
        
        # Treatment goals table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS treatment_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                goal_type TEXT,
                goal_description TEXT NOT NULL,
                target_date TEXT,
                current_progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_date TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (session_id) REFERENCES interactive_sessions(id)
            )
        ''')
        
        # Homework assignments table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS homework_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                assignment_type TEXT NOT NULL,
                description TEXT NOT NULL,
                instructions TEXT,
                assigned_date TEXT DEFAULT (datetime('now')),
                due_date TEXT,
                completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (session_id) REFERENCES interactive_sessions(id)
            )
        ''')
        
        # Diagnosis documentation table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS diagnosis_documentation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                session_id INTEGER,
                diagnosis_code TEXT,
                diagnosis_name TEXT NOT NULL,
                severity TEXT,
                confidence_level TEXT DEFAULT 'preliminary',
                supporting_evidence TEXT,
                differential_diagnoses TEXT DEFAULT '[]',
                ruling_out TEXT DEFAULT '[]',
                clinical_notes TEXT,
                diagnostic_criteria TEXT DEFAULT '{}',
                created_date TEXT DEFAULT (datetime('now')),
                updated_date TEXT DEFAULT (datetime('now')),
                diagnosed_by TEXT DEFAULT 'AI_System',
                status TEXT DEFAULT 'active',
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (session_id) REFERENCES interactive_sessions(id)
            )
        ''')
        
        conn.commit()

# Initialize database on startup
init_database()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models
class PatientCreate(BaseModel):
    name: str

class InteractiveSessionStart(BaseModel):
    patient_id: int

class ChatMessage(BaseModel):
    message: str
    session_id: int

class DiagnosisCreate(BaseModel):
    patient_id: int
    session_id: Optional[int] = None
    diagnosis_name: str
    diagnosis_code: Optional[str] = None
    severity: Optional[str] = None
    confidence_level: str = "preliminary"
    supporting_evidence: str
    clinical_notes: Optional[str] = None

class RecommendationRequest(BaseModel):
    session_id: int
    content_count: Optional[int] = 5
    lifestyle_count: Optional[int] = 6

# AI Therapy System Class
class InteractiveTherapyAI:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Assessment templates
        self.assessments = {
            "PHQ9": {
                "name": "Patient Health Questionnaire-9 (PHQ-9)",
                "questions": [
                    "Little interest or pleasure in doing things",
                    "Feeling down, depressed, or hopeless", 
                    "Trouble falling or staying asleep, or sleeping too much",
                    "Feeling tired or having little energy",
                    "Poor appetite or overeating",
                    "Feeling bad about yourself or that you are a failure",
                    "Trouble concentrating on things",
                    "Moving or speaking slowly or being fidgety",
                    "Thoughts that you would be better off dead or of hurting yourself"
                ],
                "scoring": {
                    (0, 4): "Minimal depression",
                    (5, 9): "Mild depression",
                    (10, 14): "Moderate depression", 
                    (15, 19): "Moderately severe depression",
                    (20, 27): "Severe depression"
                }
            },
            "GAD7": {
                "name": "Generalized Anxiety Disorder-7 (GAD-7)",
                "questions": [
                    "Feeling nervous, anxious, or on edge",
                    "Not being able to stop or control worrying",
                    "Worrying too much about different things", 
                    "Trouble relaxing",
                    "Being so restless that it is hard to sit still",
                    "Becoming easily annoyed or irritable",
                    "Feeling afraid, as if something awful might happen"
                ],
                "scoring": {
                    (0, 4): "Minimal anxiety",
                    (5, 9): "Mild anxiety",
                    (10, 14): "Moderate anxiety",
                    (15, 21): "Severe anxiety"
                }
            }
        }
    
    async def get_ai_response(self, session_data: dict, user_input: str) -> dict:
        """Get contextual AI response based on session phase and conversation history"""
        
        current_phase = session_data['current_phase']
        conversation_history = json.loads(session_data['conversation_history'])
        detected_symptoms = json.loads(session_data['detected_symptoms'])
        patient_name = session_data['patient_name']
        
        # Build conversation context
        recent_history = "\n".join([
            f"Patient: {msg['user']}\nTherapist: {msg['ai']}" 
            for msg in conversation_history[-3:]  # Last 3 exchanges
        ])
        
        # Get appropriate prompt based on phase
        if current_phase == SessionPhase.INTAKE.value:
            prompt = self._get_intake_prompt(patient_name, user_input, recent_history)
        elif current_phase == SessionPhase.ASSESSMENT.value:
            prompt = self._get_assessment_prompt(patient_name, user_input, recent_history, detected_symptoms)
        elif current_phase == SessionPhase.THERAPY.value:
            prompt = self._get_therapy_prompt(patient_name, user_input, recent_history, detected_symptoms)
        elif current_phase == SessionPhase.GOAL_SETTING.value:
            prompt = self._get_goal_setting_prompt(patient_name, user_input, recent_history)
        elif current_phase == SessionPhase.HOMEWORK_ASSIGNMENT.value:
            prompt = self._get_homework_prompt(patient_name, user_input, recent_history)
        else:
            prompt = self._get_general_prompt(patient_name, user_input, recent_history)
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(prompt)
            )
            ai_response = response.text.strip()
            
            # Analyze for insights and phase transitions
            insights = await self._analyze_conversation(user_input, ai_response)
            
            # Check if we should transition phases
            new_phase = await self._check_phase_transition(
                current_phase, len(conversation_history), detected_symptoms
            )
            
            return {
                'response': ai_response,
                'insights': insights,
                'new_phase': new_phase,
                'crisis_detected': self._check_crisis_indicators(user_input)
            }
            
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return {
                'response': "I'm having trouble processing that right now. Can you tell me more about what's on your mind?",
                'insights': {},
                'new_phase': current_phase,
                'crisis_detected': False
            }
    
    def _get_intake_prompt(self, patient_name: str, user_input: str, history: str) -> str:
        return f"""You are Dr. Maya, a warm, professional AI therapist conducting an intake session with {patient_name}. 

Your goals during intake:
- Understand their current mental health concerns and symptoms
- Explore what brought them to therapy today
- Assess their life stressors and challenges
- Understand their support systems
- Identify any safety concerns
- Build rapport and trust

Conversation so far:
{history}

Patient just said: "{user_input}"

Respond as Dr. Maya with empathy and ask thoughtful follow-up questions. Be a skilled therapist who listens carefully and guides the conversation naturally. If they mention symptoms of depression, anxiety, trauma, or other concerns, explore gently but thoroughly.

Keep your response conversational, supportive, and under 150 words."""
    
    def _get_assessment_prompt(self, patient_name: str, user_input: str, history: str, symptoms: list) -> str:
        symptoms_text = ", ".join(symptoms) if symptoms else "general mental health concerns"
        
        return f"""You are Dr. Maya conducting a thorough therapeutic assessment with {patient_name}. 

Based on your conversation, you've identified concerns with: {symptoms_text}

Your assessment goals:
- Conduct formal assessment questions (PHQ-9 for depression, GAD-7 for anxiety)
- Ask about symptom frequency, severity, and duration
- Explore impact on daily functioning
- Assess for safety risks

Conversation history:
{history}

Patient just said: "{user_input}"

Continue your assessment by asking specific, structured questions. You can ask the formal PHQ-9 or GAD-7 questions directly, or explore symptoms systematically. Be thorough but gentle. If you haven't started formal assessment questions yet, begin with: "I'd like to ask you some specific questions to better understand what you're experiencing. These are standard questions I ask all my patients."

Keep response under 150 words and focus on assessment."""
    
    def _get_therapy_prompt(self, patient_name: str, user_input: str, history: str, symptoms: list) -> str:
        return f"""You are Dr. Maya conducting therapy with {patient_name} using CBT techniques.

Detected symptoms/concerns: {", ".join(symptoms) if symptoms else "general concerns"}

CBT Focus Areas:
- Identify thought patterns and cognitive distortions
- Explore connections between thoughts, feelings, and behaviors
- Challenge negative thinking patterns
- Develop coping strategies and behavioral interventions
- Provide psychoeducation about their symptoms

Conversation history:
{history}

Patient just said: "{user_input}"

Respond as a skilled CBT therapist. Use cognitive restructuring, behavioral activation, and other CBT techniques. Be therapeutic, insightful, and help them understand the connections between their thoughts, feelings, and behaviors.

Keep response under 150 words and be therapeutically helpful."""
    
    def _get_goal_setting_prompt(self, patient_name: str, user_input: str, history: str) -> str:
        return f"""You are Dr. Maya helping {patient_name} set therapeutic goals.

Based on your conversation, help them identify:
- Specific, measurable, achievable goals
- Symptom reduction goals
- Functional improvement goals  
- Behavioral change goals

Make goals SMART (Specific, Measurable, Achievable, Relevant, Time-bound).

Conversation history:
{history}

Patient just said: "{user_input}"

Guide them to articulate clear, achievable goals. Ask about what they want to be different and how they'll know when they've made progress. Help them prioritize 2-3 main goals for treatment.

Keep response under 150 words and focus on collaborative goal setting."""
    
    def _get_homework_prompt(self, patient_name: str, user_input: str, history: str) -> str:
        return f"""You are Dr. Maya assigning therapeutic homework to {patient_name}.

Based on your conversation and their goals, assign appropriate homework:
- Thought records for cognitive work
- Activity scheduling for behavioral activation
- Mindfulness exercises for anxiety
- Exposure exercises if appropriate
- Journaling for insight and tracking

Conversation history:
{history}

Patient just said: "{user_input}"

Assign specific, manageable homework that matches their treatment goals and current capabilities. Explain clearly what they should do, when, and why it will help. Be encouraging and set them up for success.

Keep response under 150 words and be specific about homework assignments."""
    
    def _get_general_prompt(self, patient_name: str, user_input: str, history: str) -> str:
        return f"""You are Dr. Maya, a professional AI therapist in session with {patient_name}.

Conversation history:
{history}

Patient just said: "{user_input}"

Respond thoughtfully as a professional therapist. Be supportive, insightful, and therapeutic. Keep response under 150 words."""
    
    async def _analyze_conversation(self, user_input: str, ai_response: str) -> dict:
        """Analyze conversation for therapeutic insights"""
        
        insights = {
            'detected_symptoms': [],
            'mood_indicators': [],
            'behavioral_patterns': [],
            'cognitive_patterns': []
        }
        
        user_lower = user_input.lower()
        
        # Symptom detection
        symptom_keywords = {
            'anxiety': ['anxious', 'worried', 'panic', 'nervous', 'fear', 'racing thoughts', 'restless'],
            'depression': ['depressed', 'sad', 'hopeless', 'empty', 'worthless', 'tired', 'no energy'],
            'sleep': ['sleep', 'insomnia', 'tired', 'exhausted', 'wake up', 'nightmares'],
            'social': ['social', 'friends', 'lonely', 'isolated', 'avoid people', 'relationships'],
            'work_stress': ['work', 'job', 'boss', 'career', 'stressed', 'overwhelmed']
        }
        
        for symptom, keywords in symptom_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                insights['detected_symptoms'].append(symptom)
        
        # Mood indicators
        if any(word in user_lower for word in ['sad', 'down', 'depressed', 'low', 'awful']):
            insights['mood_indicators'].append('low_mood')
        if any(word in user_lower for word in ['anxious', 'worried', 'nervous', 'panic', 'scared']):
            insights['mood_indicators'].append('anxiety')
        if any(word in user_lower for word in ['angry', 'mad', 'frustrated', 'irritated']):
            insights['mood_indicators'].append('irritability')
        
        # Behavioral patterns
        if any(word in user_lower for word in ['avoid', 'staying home', 'cancelled', 'didn\'t go']):
            insights['behavioral_patterns'].append('avoidance')
        if any(word in user_lower for word in ['can\'t sleep', 'insomnia', 'staying up', 'tossing']):
            insights['behavioral_patterns'].append('sleep_disturbance')
        
        # Cognitive patterns
        if any(phrase in user_lower for phrase in ['i always', 'i never', 'everything is', 'nothing works']):
            insights['cognitive_patterns'].append('all_or_nothing_thinking')
        if any(phrase in user_lower for phrase in ['what if', 'probably will', 'going to happen']):
            insights['cognitive_patterns'].append('catastrophizing')
        
        return insights
    
    async def _check_phase_transition(self, current_phase: str, conversation_count: int, symptoms: list) -> str:
        """Determine if session should transition to next phase"""
        
        if current_phase == SessionPhase.INTAKE.value and conversation_count >= 6:
            return SessionPhase.ASSESSMENT.value
        elif current_phase == SessionPhase.ASSESSMENT.value and conversation_count >= 12:
            return SessionPhase.THERAPY.value  
        elif current_phase == SessionPhase.THERAPY.value and conversation_count >= 18:
            return SessionPhase.GOAL_SETTING.value
        elif current_phase == SessionPhase.GOAL_SETTING.value and conversation_count >= 22:
            return SessionPhase.HOMEWORK_ASSIGNMENT.value
        elif current_phase == SessionPhase.HOMEWORK_ASSIGNMENT.value and conversation_count >= 25:
            return SessionPhase.CLOSING.value
        elif current_phase == SessionPhase.CLOSING.value and conversation_count >= 27:
            return SessionPhase.COMPLETED.value
        
        return current_phase
    
    def _check_crisis_indicators(self, text: str) -> bool:
        """Check for crisis indicators in user input"""
        crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'hurt myself', 'die', 'death',
            'better off dead', 'end my life', 'take my life', 'harm myself'
        ]
        
        return any(keyword in text.lower() for keyword in crisis_keywords)
    
    async def conduct_automated_assessment(self, session_data: dict) -> dict:
        """Conduct automated assessment based on conversation"""
        
        conversation_history = json.loads(session_data['conversation_history'])
        detected_symptoms = json.loads(session_data['detected_symptoms'])
        
        # Determine which assessments to run
        assessments_to_run = []
        if 'anxiety' in detected_symptoms:
            assessments_to_run.append('GAD7')
        if 'depression' in detected_symptoms:
            assessments_to_run.append('PHQ9')
        
        if not assessments_to_run:
            assessments_to_run = ['PHQ9']  # Default
        
        assessment_results = {}
        
        for assessment_type in assessments_to_run:
            result = await self._simulate_assessment_from_conversation(
                assessment_type, conversation_history
            )
            assessment_results[assessment_type] = result
        
        return assessment_results
    
    async def _simulate_assessment_from_conversation(self, assessment_type: str, conversation: list) -> dict:
        """Simulate assessment responses based on conversation content"""
        
        assessment_data = self.assessments[assessment_type]
        
        conversation_text = "\n".join([
            f"Patient: {msg['user']}" for msg in conversation
        ])
        
        simulation_prompt = f"""Based on this therapy conversation, simulate realistic {assessment_type} assessment responses:

Conversation:
{conversation_text}

Assessment: {assessment_data['name']}

For each question, select the most appropriate response (0-3) based on the patient's described symptoms:
0 = Not at all
1 = Several days  
2 = More than half the days
3 = Nearly every day

Questions:
"""
        
        for i, question in enumerate(assessment_data['questions']):
            simulation_prompt += f"{i+1}. {question}\n"
        
        simulation_prompt += "\nRespond with just numbers separated by spaces (e.g., '2 1 3 1 0 2 1 2 3'):"
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(simulation_prompt)
            )
            
            # Parse numbers from response
            numbers = re.findall(r'\d', response.text)
            
            # Calculate score and get interpretation
            total_score = sum(int(n) for n in numbers[:len(assessment_data['questions'])])
            
            # Determine severity
            severity = "Unknown"
            for score_range, level in assessment_data['scoring'].items():
                if score_range[0] <= total_score <= score_range[1]:
                    severity = level
                    break
            
            return {
                'responses': {f'q{i+1}': int(numbers[i]) for i in range(len(numbers[:len(assessment_data['questions'])]))},
                'total_score': total_score,
                'severity': severity,
                'interpretation': f"Score of {total_score} indicates {severity}"
            }
            
        except Exception as e:
            # Fallback: moderate responses
            total_score = len(assessment_data['questions'])
            return {
                'responses': {f'q{i+1}': 1 for i in range(len(assessment_data['questions']))},
                'total_score': total_score,
                'severity': 'Mild',
                'interpretation': f"Estimated mild symptoms based on conversation"
            }

therapy_ai = InteractiveTherapyAI()
recommendation_engine = RecommendationEngine(therapy_ai.model)

# API Routes

@app.get("/")
async def root():
    return {"message": "Complete AI Therapist API", "version": "2.0.0"}

@app.post("/patients")
async def create_patient(patient: PatientCreate):
    """Create a new patient"""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO patients (name) VALUES (?)",
            (patient.name,)
        )
        patient_id = cursor.lastrowid
        conn.commit()
        
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        return dict(row)

@app.get("/patients")
async def list_patients():
    """List all patients"""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM patients ORDER BY created_date DESC").fetchall()
        return [dict(row) for row in rows]

@app.post("/sessions/start")
async def start_interactive_session(session_data: InteractiveSessionStart):
    """Start a new interactive therapy session"""
    with get_db() as conn:
        # Verify patient exists
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (session_data.patient_id,)).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create new interactive session
        cursor = conn.execute(
            """INSERT INTO interactive_sessions 
               (patient_id, current_phase, conversation_history, detected_symptoms, session_insights)
               VALUES (?, ?, ?, ?, ?)""",
            (session_data.patient_id, SessionPhase.INTAKE.value, '[]', '[]', '[]')
        )
        session_id = cursor.lastrowid
        conn.commit()
        
        # Generate initial AI greeting
        greeting_prompt = f"""You are Dr. Maya, a warm, professional AI therapist. You are starting a new therapy session with {patient['name']}.

Greet them warmly and naturally begin exploring what brings them to therapy today. Be empathetic and use open-ended questions. Keep it conversational and welcoming.

Start with something like welcoming them and asking what's been on their mind lately or what brought them to seek therapy.

Keep your greeting under 100 words."""
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: therapy_ai.model.generate_content(greeting_prompt)
            )
            greeting = response.text.strip()
        except:
            greeting = f"Hello {patient['name']}, I'm Dr. Maya. I'm so glad you're here today. This is a safe space where we can talk about whatever is on your mind. What brought you to therapy today?"
        
        return {
            "session_id": session_id,
            "patient_name": patient['name'],
            "initial_message": greeting,
            "phase": SessionPhase.INTAKE.value
        }

@app.post("/sessions/chat")
async def chat_in_session(chat_data: ChatMessage):
    """Continue conversation in interactive session"""
    with get_db() as conn:
        # Get session data
        session = conn.execute(
            """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
               JOIN patients p ON s.patient_id = p.id WHERE s.id = ?""",
            (chat_data.session_id,)
        ).fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session['session_completed']:
            raise HTTPException(status_code=400, detail="Session already completed")
        
        # Get AI response
        ai_result = await therapy_ai.get_ai_response(dict(session), chat_data.message)
        
        # Update conversation history
        conversation_history = json.loads(session['conversation_history'])
        conversation_history.append({
            'user': chat_data.message,
            'ai': ai_result['response'],
            'timestamp': datetime.now().isoformat(),
            'phase': session['current_phase']
        })
        
        # Update detected symptoms
        detected_symptoms = json.loads(session['detected_symptoms'])
        for symptom in ai_result['insights'].get('detected_symptoms', []):
            if symptom not in detected_symptoms:
                detected_symptoms.append(symptom)
        
        # Update session insights
        session_insights = json.loads(session['session_insights'])
        session_insights.append({
            'timestamp': datetime.now().isoformat(),
            'insights': ai_result['insights'],
            'phase': session['current_phase']
        })
        
        # Check for phase transition
        new_phase = ai_result['new_phase']
        phase_changed = new_phase != session['current_phase']
        
        # Handle automated actions based on phase transitions
        if phase_changed:
            if new_phase == SessionPhase.ASSESSMENT.value:
                # Conduct automated assessment
                assessment_results = await therapy_ai.conduct_automated_assessment(dict(session))
                conn.execute(
                    "UPDATE interactive_sessions SET assessment_results = ? WHERE id = ?",
                    (json.dumps(assessment_results), chat_data.session_id)
                )
            elif new_phase == SessionPhase.HOMEWORK_ASSIGNMENT.value:
                # Auto-generate goals and homework
                await auto_generate_treatment_plan(chat_data.session_id, dict(session))
        
        # Update session
        session_completed = (new_phase == SessionPhase.COMPLETED.value)
        
        conn.execute(
            """UPDATE interactive_sessions SET 
               current_phase = ?, conversation_history = ?, detected_symptoms = ?, 
               session_insights = ?, total_exchanges = ?, session_completed = ?,
               crisis_flags = ?
               WHERE id = ?""",
            (
                new_phase,
                json.dumps(conversation_history),
                json.dumps(detected_symptoms),
                json.dumps(session_insights),
                len(conversation_history),
                session_completed,
                json.dumps(['crisis_detected'] if ai_result['crisis_detected'] else []),
                chat_data.session_id
            )
        )
        conn.commit()
        
        response = {
            "response": ai_result['response'],
            "phase": new_phase,
            "phase_changed": phase_changed,
            "conversation_count": len(conversation_history),
            "detected_symptoms": detected_symptoms,
            "session_completed": session_completed
        }
        
        if ai_result['crisis_detected']:
            response['crisis_alert'] = "Crisis indicators detected. Please ensure patient safety."
        
        return response

async def auto_generate_treatment_plan(session_id: int, session_data: dict):
    """Auto-generate treatment goals and homework assignments"""
    
    conversation_history = json.loads(session_data['conversation_history'])
    detected_symptoms = json.loads(session_data['detected_symptoms'])
    patient_name = session_data['patient_name']
    
    conversation_summary = "\n".join([
        msg['user'] for msg in conversation_history
    ])
    
    # Generate goals using AI
    goals_prompt = f"""Based on this therapy conversation with {patient_name}, create 3 specific SMART treatment goals:

Patient conversation summary: {conversation_summary}
Detected symptoms: {', '.join(detected_symptoms)}

Create goals that are:
- Specific and measurable
- Address the patient's main concerns  
- Achievable within 3-6 months

Format exactly as:
1. [Symptom] Specific goal description
2. [Behavioral] Specific goal description  
3. [Functional] Specific goal description

Only respond with the 3 numbered goals."""
    
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: therapy_ai.model.generate_content(goals_prompt)
        )
        goals_text = response.text.strip()
        
        # Parse and create goals
        goal_lines = [line.strip() for line in goals_text.split('\n') if line.strip() and line[0].isdigit()]
        
        created_goals = []
        with get_db() as conn:
            for goal_line in goal_lines[:3]:  # Max 3 goals
                # Extract goal type and description
                if '[' in goal_line and ']' in goal_line:
                    goal_type = goal_line.split('[')[1].split(']')[0].lower()
                    description = goal_line.split(']')[1].strip()
                else:
                    goal_type = 'symptom'
                    description = goal_line[2:].strip()  # Remove "1. " prefix
                
                # Create goal in database
                cursor = conn.execute('''
                    INSERT INTO treatment_goals 
                    (patient_id, session_id, goal_type, goal_description, target_date, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_data['patient_id'],
                    session_id,
                    goal_type if goal_type in ['symptom', 'behavioral', 'functional'] else 'symptom',
                    description,
                    (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
                    'active'
                ))
                
                created_goals.append(f"{goal_type.title()}: {description}")
            
            # Generate homework assignment
            homework_prompt = f"""Based on the therapy conversation, create 1 specific homework assignment for {patient_name}:

Symptoms: {', '.join(detected_symptoms)}
Goals: {'; '.join(created_goals)}

Create a homework assignment that:
- Is specific and actionable
- Matches their symptoms and goals
- Is achievable in one week

Respond with just: [Type] Assignment description"""
            
            hw_response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: therapy_ai.model.generate_content(homework_prompt)
            )
            hw_text = hw_response.text.strip()
            
            # Parse homework
            if '[' in hw_text and ']' in hw_text:
                hw_type = hw_text.split('[')[1].split(']')[0].lower().replace(' ', '_')
                hw_description = hw_text.split(']')[1].strip()
            else:
                hw_type = 'thought_record'
                hw_description = hw_text
            
            # Create homework assignment
            cursor = conn.execute('''
                INSERT INTO homework_assignments 
                (patient_id, session_id, assignment_type, description, instructions, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session_data['patient_id'],
                session_id,
                hw_type,
                hw_description,
                f"Complete this assignment over the next week and bring your observations to the next session.",
                (datetime.now() + timedelta(days=7)).isoformat()
            ))
            
            conn.commit()
            
            # Store generated treatment plan in session
            treatment_plan = {
                'goals': created_goals,
                'homework': {'type': hw_type, 'description': hw_description},
                'generated_date': datetime.now().isoformat()
            }
            
            conn.execute(
                "UPDATE interactive_sessions SET generated_goals = ? WHERE id = ?",
                (json.dumps(treatment_plan), session_id)
            )
            conn.commit()
            
    except Exception as e:
        logger.error(f"Error generating treatment plan: {e}")

@app.get("/sessions/{session_id}")
async def get_session_details(session_id: int):
    """Get detailed session information"""
    with get_db() as conn:
        session = conn.execute(
            """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
               JOIN patients p ON s.patient_id = p.id WHERE s.id = ?""",
            (session_id,)
        ).fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get goals and homework
        goals = conn.execute(
            "SELECT * FROM treatment_goals WHERE session_id = ?",
            (session_id,)
        ).fetchall()
        
        homework = conn.execute(
            "SELECT * FROM homework_assignments WHERE session_id = ?", 
            (session_id,)
        ).fetchall()
        
        session_data = dict(session)
        session_data['conversation_history'] = json.loads(session['conversation_history'])
        session_data['detected_symptoms'] = json.loads(session['detected_symptoms'])
        session_data['session_insights'] = json.loads(session['session_insights'])
        session_data['assessment_results'] = json.loads(session['assessment_results']) if session['assessment_results'] else {}
        session_data['generated_goals'] = json.loads(session['generated_goals']) if session['generated_goals'] else {}
        session_data['crisis_flags'] = json.loads(session['crisis_flags'])
        session_data['goals'] = [dict(row) for row in goals]
        session_data['homework'] = [dict(row) for row in homework]
        
        return session_data

@app.get("/patients/{patient_id}/sessions")
async def get_patient_sessions(patient_id: int):
    """Get all sessions for a patient"""
    with get_db() as conn:
        sessions = conn.execute(
            """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
               JOIN patients p ON s.patient_id = p.id 
               WHERE s.patient_id = ? ORDER BY s.session_date DESC""",
            (patient_id,)
        ).fetchall()
        
        return [dict(row) for row in sessions]

@app.get("/patients/{patient_id}/dashboard")
async def get_patient_dashboard(patient_id: int):
    """Get comprehensive patient dashboard"""
    with get_db() as conn:
        # Patient info
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Sessions
        sessions = conn.execute(
            """SELECT * FROM interactive_sessions WHERE patient_id = ? 
               ORDER BY session_date DESC LIMIT 5""",
            (patient_id,)
        ).fetchall()
        
        # Goals  
        goals = conn.execute(
            "SELECT * FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        ).fetchall()
        
        # Homework
        homework = conn.execute(
            "SELECT * FROM homework_assignments WHERE patient_id = ? AND completed = FALSE",
            (patient_id,)
        ).fetchall()
        
        # Latest session details
        latest_session = None
        if sessions:
            latest_session_data = dict(sessions[0])
            latest_session_data['conversation_history'] = json.loads(sessions[0]['conversation_history'])
            latest_session_data['detected_symptoms'] = json.loads(sessions[0]['detected_symptoms'])
            latest_session_data['assessment_results'] = json.loads(sessions[0]['assessment_results']) if sessions[0]['assessment_results'] else {}
            latest_session = latest_session_data
        
        return {
            "patient": dict(patient),
            "recent_sessions": [dict(row) for row in sessions],
            "active_goals": [dict(row) for row in goals],
            "pending_homework": [dict(row) for row in homework],
            "latest_session": latest_session,
            "summary": {
                "total_sessions": len(sessions),
                "active_goals": len(goals),
                "pending_homework": len(homework),
                "last_session": sessions[0]['session_date'] if sessions else None,
                "detected_symptoms": json.loads(sessions[0]['detected_symptoms']) if sessions else []
            }
        }

@app.get("/sessions/{session_id}/export")
async def export_session_transcript(session_id: int):
    """Export session transcript"""
    with get_db() as conn:
        session = conn.execute(
            """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
               JOIN patients p ON s.patient_id = p.id WHERE s.id = ?""",
            (session_id,)
        ).fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        conversation_history = json.loads(session['conversation_history'])
        
        # Format transcript
        transcript = f"""AI THERAPY SESSION TRANSCRIPT
Session ID: {session_id}
Patient: {session['patient_name']}
Date: {session['session_date']}
Duration: {session['total_exchanges']} exchanges
Final Phase: {session['current_phase']}
Completed: {'Yes' if session['session_completed'] else 'No'}

DETECTED SYMPTOMS:
{', '.join(json.loads(session['detected_symptoms'])) if session['detected_symptoms'] else 'None detected'}

CONVERSATION TRANSCRIPT:
{'='*50}
"""
        
        for i, exchange in enumerate(conversation_history, 1):
            transcript += f"\nExchange {i} [{exchange.get('phase', 'unknown')}]:\n"
            transcript += f"Patient: {exchange['user']}\n"
            transcript += f"Dr. Maya: {exchange['ai']}\n"
            transcript += f"Time: {exchange['timestamp']}\n"
            transcript += "-" * 30 + "\n"
        
        # Add assessment results if available
        if session['assessment_results']:
            assessment_results = json.loads(session['assessment_results'])
            transcript += f"\nASSESSMENT RESULTS:\n{'='*20}\n"
            for assessment_type, results in assessment_results.items():
                transcript += f"\n{assessment_type}:\n"
                transcript += f"Total Score: {results['total_score']}\n"
                transcript += f"Severity: {results['severity']}\n"
                transcript += f"Interpretation: {results['interpretation']}\n"
        
        # Add treatment plan if available
        if session['generated_goals']:
            treatment_plan = json.loads(session['generated_goals'])
            transcript += f"\nTREATMENT PLAN:\n{'='*15}\n"
            if 'goals' in treatment_plan:
                transcript += "Goals:\n"
                for i, goal in enumerate(treatment_plan['goals'], 1):
                    transcript += f"{i}. {goal}\n"
            
            if 'homework' in treatment_plan:
                transcript += f"\nHomework Assignment:\n"
                transcript += f"Type: {treatment_plan['homework']['type']}\n"
                transcript += f"Description: {treatment_plan['homework']['description']}\n"
        
        transcript += f"\n\nSession exported on: {datetime.now().isoformat()}"
        
        return {"transcript": transcript, "session_summary": dict(session)}

@app.get("/sessions/{session_id}/insights")
async def get_session_insights(session_id: int):
    """Get AI-generated insights about the session"""
    with get_db() as conn:
        session = conn.execute(
            """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
               JOIN patients p ON s.patient_id = p.id WHERE s.id = ?""",
            (session_id,)
        ).fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        conversation_history = json.loads(session['conversation_history'])
        detected_symptoms = json.loads(session['detected_symptoms'])
        
        # Generate AI insights about the session
        conversation_summary = "\n".join([
            f"Patient: {msg['user']}\nTherapist: {msg['ai']}" 
            for msg in conversation_history
        ])
        
        insights_prompt = f"""Analyze this therapy session and provide professional clinical insights:

Patient: {session['patient_name']}
Session Length: {session['total_exchanges']} exchanges
Phases Completed: {session['current_phase']}
Detected Symptoms: {', '.join(detected_symptoms)}

Conversation:
{conversation_summary}

Provide insights on:
1. Key themes and patterns identified
2. Patient's primary concerns and symptoms
3. Therapeutic progress and engagement
4. Recommended next steps
5. Risk factors or concerns (if any)

Keep analysis professional and concise."""
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: therapy_ai.model.generate_content(insights_prompt)
            )
            ai_insights = response.text.strip()
        except Exception as e:
            ai_insights = f"Unable to generate AI insights: {e}"
        
        return {
            "session_id": session_id,
            "patient_name": session['patient_name'],
            "session_stats": {
                "total_exchanges": session['total_exchanges'],
                "current_phase": session['current_phase'],
                "detected_symptoms": detected_symptoms,
                "session_completed": session['session_completed'],
                "session_date": session['session_date']
            },
            "ai_insights": ai_insights,
            "session_insights": json.loads(session['session_insights']) if session['session_insights'] else []
        }

@app.post("/homework/{homework_id}/complete")
async def complete_homework(homework_id: int, completion_data: dict):
    """Mark homework assignment as completed"""
    with get_db() as conn:
        homework = conn.execute("SELECT * FROM homework_assignments WHERE id = ?", (homework_id,)).fetchone()
        
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        
        conn.execute(
            "UPDATE homework_assignments SET completed = TRUE WHERE id = ?",
            (homework_id,)
        )
        conn.commit()
        
        return {"message": "Homework marked as completed", "homework_id": homework_id}

@app.get("/goals/{goal_id}/progress")
async def update_goal_progress(goal_id: int, progress: int):
    """Update goal progress"""
    if not 0 <= progress <= 100:
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
    
    with get_db() as conn:
        goal = conn.execute("SELECT * FROM treatment_goals WHERE id = ?", (goal_id,)).fetchone()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        conn.execute(
            "UPDATE treatment_goals SET current_progress = ? WHERE id = ?",
            (progress, goal_id)
        )
        conn.commit()
        
        return {"message": "Goal progress updated", "goal_id": goal_id, "progress": progress}

# Recommendation Engine Endpoints

@app.post("/sessions/{session_id}/recommendations")
async def generate_session_recommendations(session_id: int, request: RecommendationRequest):
    """Generate comprehensive recommendations based on therapy session"""
    try:
        with get_db() as conn:
            # Get session data with patient info
            session = conn.execute(
                """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
                   JOIN patients p ON s.patient_id = p.id WHERE s.id = ?""",
                (session_id,)
            ).fetchone()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Get conversation history
            conversation_history = json.loads(session['conversation_history']) if session['conversation_history'] else []
            
            if not conversation_history:
                raise HTTPException(status_code=400, detail="Session has no conversation history to analyze")
            
            # Get patient's goals
            goals = conn.execute(
                "SELECT * FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
                (session['patient_id'],)
            ).fetchall()
            goals_list = [dict(goal) for goal in goals]
            
            # Get patient's homework
            homework = conn.execute(
                "SELECT * FROM homework_assignments WHERE patient_id = ? ORDER BY assigned_date DESC LIMIT 5",
                (session['patient_id'],)
            ).fetchall()
            homework_list = [dict(hw) for hw in homework]
            
            # Generate recommendations
            recommendations = await recommendation_engine.generate_recommendations(
                conversation_history=conversation_history,
                goals=goals_list,
                homework=homework_list,
                content_count=request.content_count,
                lifestyle_count=request.lifestyle_count
            )
            
            # Store recommendations in database
            recommendations_json = json.dumps(recommendations)
            conn.execute(
                "UPDATE interactive_sessions SET recommendation_data = ? WHERE id = ?",
                (recommendations_json, session_id)
            )
            conn.commit()
            
            return {
                "session_id": session_id,
                "patient_name": session['patient_name'],
                "recommendations": recommendations,
                "generated_at": recommendations["recommendation_metadata"]["generated_at"]
            }
            
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@app.get("/sessions/{session_id}/keywords")
async def extract_session_keywords(session_id: int):
    """Extract keywords and therapeutic themes from session conversation"""
    try:
        with get_db() as conn:
            session = conn.execute(
                "SELECT conversation_history, patient_id FROM interactive_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            conversation_history = json.loads(session['conversation_history']) if session['conversation_history'] else []
            
            if not conversation_history:
                raise HTTPException(status_code=400, detail="Session has no conversation to analyze")
            
            # Extract keywords using the recommendation engine
            keywords_data = await recommendation_engine.keyword_extractor.extract_keywords_and_themes(conversation_history)
            
            return {
                "session_id": session_id,
                "analysis": keywords_data,
                "conversation_length": len(conversation_history),
                "analyzed_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract keywords: {str(e)}")

# Diagnosis Documentation Endpoints

@app.post("/diagnosis")
async def create_diagnosis(diagnosis: DiagnosisCreate):
    """Create a new diagnosis documentation entry"""
    with get_db() as conn:
        # Verify patient exists
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (diagnosis.patient_id,)).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        cursor = conn.execute("""
            INSERT INTO diagnosis_documentation 
            (patient_id, session_id, diagnosis_code, diagnosis_name, severity, 
             confidence_level, supporting_evidence, clinical_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            diagnosis.patient_id,
            diagnosis.session_id,
            diagnosis.diagnosis_code,
            diagnosis.diagnosis_name,
            diagnosis.severity,
            diagnosis.confidence_level,
            diagnosis.supporting_evidence,
            diagnosis.clinical_notes
        ))
        
        diagnosis_id = cursor.lastrowid
        conn.commit()
        
        # Return created diagnosis
        created_diagnosis = conn.execute(
            "SELECT * FROM diagnosis_documentation WHERE id = ?", (diagnosis_id,)
        ).fetchone()
        
        return dict(created_diagnosis)

@app.get("/patients/{patient_id}/diagnoses")
async def get_patient_diagnoses(patient_id: int):
    """Get all diagnoses for a patient"""
    with get_db() as conn:
        diagnoses = conn.execute(
            """SELECT d.*, p.name as patient_name 
               FROM diagnosis_documentation d 
               JOIN patients p ON d.patient_id = p.id 
               WHERE d.patient_id = ? 
               ORDER BY d.created_date DESC""",
            (patient_id,)
        ).fetchall()
        
        return [dict(row) for row in diagnoses]

@app.get("/sessions/{session_id}/diagnosis")
async def get_session_diagnosis(session_id: int):
    """Get diagnosis documentation for a specific session"""
    with get_db() as conn:
        diagnoses = conn.execute(
            """SELECT d.*, p.name as patient_name 
               FROM diagnosis_documentation d 
               JOIN patients p ON d.patient_id = p.id 
               WHERE d.session_id = ? 
               ORDER BY d.created_date DESC""",
            (session_id,)
        ).fetchall()
        
        return [dict(row) for row in diagnoses]

@app.post("/sessions/{session_id}/auto-diagnosis")
async def auto_generate_diagnosis(session_id: int):
    """Auto-generate diagnosis based on session conversation and assessment results"""
    try:
        with get_db() as conn:
            session = conn.execute(
                """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
                   JOIN patients p ON s.patient_id = p.id WHERE s.id = ?""",
                (session_id,)
            ).fetchone()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            conversation_history = json.loads(session['conversation_history']) if session['conversation_history'] else []
            assessment_results = json.loads(session['assessment_results']) if session['assessment_results'] else {}
            detected_symptoms = json.loads(session['detected_symptoms'])
            
            if not conversation_history:
                raise HTTPException(status_code=400, detail="No conversation history to analyze")
            
            # Build context for diagnosis
            conversation_summary = "\n".join([
                f"Patient: {msg['user']}\nTherapist: {msg['ai']}" 
                for msg in conversation_history
            ])
            
            assessment_summary = ""
            if assessment_results:
                assessment_summary = "\nAssessment Results:\n"
                for assessment_type, results in assessment_results.items():
                    assessment_summary += f"- {assessment_type}: Score {results['total_score']} ({results['severity']})\n"
            
            diagnosis_prompt = f"""Based on this therapy session, provide a preliminary clinical diagnosis assessment:

Patient: {session['patient_name']}
Detected Symptoms: {', '.join(detected_symptoms)}

Conversation Summary:
{conversation_summary}

{assessment_summary}

Provide a structured diagnostic assessment including:
1. Primary diagnosis (most likely)
2. Severity level
3. Confidence level (preliminary/probable/definitive)
4. Supporting evidence from the session
5. Differential diagnoses to consider
6. Ruling out other conditions
7. Clinical notes and recommendations

Format as JSON:
{{
    "primary_diagnosis": "diagnosis name",
    "diagnosis_code": "ICD-10 or DSM-5 code if applicable",
    "severity": "mild/moderate/severe",
    "confidence_level": "preliminary/probable/definitive",
    "supporting_evidence": "specific evidence from session",
    "differential_diagnoses": ["alternative diagnosis 1", "alternative diagnosis 2"],
    "ruling_out": ["conditions to rule out"],
    "clinical_notes": "professional clinical observations",
    "recommendations": "next steps and treatment recommendations"
}}

Focus on evidence-based diagnostic criteria. Be conservative with confidence levels."""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: therapy_ai.model.generate_content(diagnosis_prompt)
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                diagnosis_data = json.loads(json_match.group())
                
                # Create diagnosis documentation entry
                cursor = conn.execute("""
                    INSERT INTO diagnosis_documentation 
                    (patient_id, session_id, diagnosis_code, diagnosis_name, severity, 
                     confidence_level, supporting_evidence, differential_diagnoses, 
                     ruling_out, clinical_notes, diagnostic_criteria, diagnosed_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session['patient_id'],
                    session_id,
                    diagnosis_data.get('diagnosis_code'),
                    diagnosis_data.get('primary_diagnosis'),
                    diagnosis_data.get('severity'),
                    diagnosis_data.get('confidence_level', 'preliminary'),
                    diagnosis_data.get('supporting_evidence'),
                    json.dumps(diagnosis_data.get('differential_diagnoses', [])),
                    json.dumps(diagnosis_data.get('ruling_out', [])),
                    diagnosis_data.get('clinical_notes'),
                    json.dumps(diagnosis_data.get('recommendations', {})),
                    'AI_System_Auto'
                ))
                
                diagnosis_id = cursor.lastrowid
                conn.commit()
                
                return {
                    "diagnosis_id": diagnosis_id,
                    "session_id": session_id,
                    "auto_generated": True,
                    "diagnosis_data": diagnosis_data,
                    "generated_at": datetime.now().isoformat()
                }
            
            else:
                raise HTTPException(status_code=500, detail="Failed to parse AI diagnosis response")
                
    except Exception as e:
        logger.error(f"Error auto-generating diagnosis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to auto-generate diagnosis: {str(e)}")

@app.get("/diagnosis/{diagnosis_id}")
async def get_diagnosis_details(diagnosis_id: int):
    """Get detailed diagnosis documentation"""
    with get_db() as conn:
        diagnosis = conn.execute(
            """SELECT d.*, p.name as patient_name, s.session_date
               FROM diagnosis_documentation d 
               JOIN patients p ON d.patient_id = p.id 
               LEFT JOIN interactive_sessions s ON d.session_id = s.id
               WHERE d.id = ?""",
            (diagnosis_id,)
        ).fetchone()
        
        if not diagnosis:
            raise HTTPException(status_code=404, detail="Diagnosis not found")
        
        diagnosis_data = dict(diagnosis)
        diagnosis_data['differential_diagnoses'] = json.loads(diagnosis['differential_diagnoses']) if diagnosis['differential_diagnoses'] else []
        diagnosis_data['ruling_out'] = json.loads(diagnosis['ruling_out']) if diagnosis['ruling_out'] else []
        diagnosis_data['diagnostic_criteria'] = json.loads(diagnosis['diagnostic_criteria']) if diagnosis['diagnostic_criteria'] else {}
        
        return diagnosis_data

@app.put("/diagnosis/{diagnosis_id}")
async def update_diagnosis(diagnosis_id: int, updates: Dict[str, Any]):
    """Update diagnosis documentation"""
    with get_db() as conn:
        diagnosis = conn.execute("SELECT * FROM diagnosis_documentation WHERE id = ?", (diagnosis_id,)).fetchone()
        
        if not diagnosis:
            raise HTTPException(status_code=404, detail="Diagnosis not found")
        
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []
        
        allowed_fields = [
            'diagnosis_code', 'diagnosis_name', 'severity', 'confidence_level',
            'supporting_evidence', 'clinical_notes', 'status'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                update_values.append(value)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Add updated timestamp
        update_fields.append("updated_date = ?")
        update_values.append(datetime.now().isoformat())
        update_values.append(diagnosis_id)
        
        query = f"UPDATE diagnosis_documentation SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(query, update_values)
        conn.commit()
        
        # Return updated diagnosis
        updated_diagnosis = conn.execute(
            "SELECT * FROM diagnosis_documentation WHERE id = ?", (diagnosis_id,)
        ).fetchone()
        
        return dict(updated_diagnosis)

# Health check and system endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": [
            "Interactive AI Therapy Sessions",
            "Automated Assessment Conducting",
            "Dynamic Phase Transitions", 
            "AI-Generated Treatment Plans",
            "Crisis Detection",
            "Session Transcripts",
            "Real-time WebSocket Chat",
            "Content & Lifestyle Recommendations",
            "Diagnosis Documentation"
        ]
    }

@app.get("/analytics")
async def get_system_analytics():
    """Get system-wide analytics"""
    with get_db() as conn:
        total_patients = conn.execute("SELECT COUNT(*) as count FROM patients").fetchone()['count']
        total_sessions = conn.execute("SELECT COUNT(*) as count FROM interactive_sessions").fetchone()['count']
        completed_sessions = conn.execute("SELECT COUNT(*) as count FROM interactive_sessions WHERE session_completed = TRUE").fetchone()['count']
        total_diagnoses = conn.execute("SELECT COUNT(*) as count FROM diagnosis_documentation").fetchone()['count']
        
        # Most common symptoms
        all_symptoms = []
        symptoms_data = conn.execute("SELECT detected_symptoms FROM interactive_sessions WHERE detected_symptoms != '[]'").fetchall()
        for row in symptoms_data:
            symptoms = json.loads(row['detected_symptoms']) if row['detected_symptoms'] else []
            all_symptoms.extend(symptoms)
        
        symptom_counts = Counter(all_symptoms)
        
        # Average session length
        avg_exchanges = conn.execute("SELECT AVG(total_exchanges) as avg FROM interactive_sessions WHERE total_exchanges > 0").fetchone()['avg']
        
        # Diagnosis distribution
        diagnosis_counts = conn.execute(
            "SELECT diagnosis_name, COUNT(*) as count FROM diagnosis_documentation GROUP BY diagnosis_name ORDER BY count DESC"
        ).fetchall()
    return {
            "total_patients": total_patients,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_diagnoses": total_diagnoses,
            "completion_rate": round((completed_sessions / total_sessions * 100), 2) if total_sessions > 0 else 0,
            "average_session_exchanges": round(avg_exchanges, 1) if avg_exchanges else 0,
            "common_symptoms": dict(symptom_counts.most_common(5)),
            "diagnosis_distribution": {row['diagnosis_name']: row['count'] for row in diagnosis_counts[:5]},
            "system_uptime": datetime.now().isoformat()
        }

@app.get("/admin/fix-database")
async def fix_database():
    """Fix database schema issues"""
    try:
        with get_db() as conn:
            # Add missing columns if they don't exist
            columns_to_add = [
                ("treatment_goals", "session_id", "INTEGER"),
                ("homework_assignments", "session_id", "INTEGER"),
                ("interactive_sessions", "recommendation_data", "TEXT"),
                ("patients", "detected_symptoms", "TEXT DEFAULT '[]'")
            ]
            
            for table, column, definition in columns_to_add:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                    conn.commit()
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        logger.warning(f"Failed to add column {column} to {table}: {e}")
                        
        return {"message": "Database schema fixed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fix database: {e}")

# Additional Recommendation Engine Endpoints

@app.post("/sessions/{session_id}/content-recommendations")
async def generate_content_recommendations_only(session_id: int, count: Optional[int] = 5):
    """Generate only content recommendations (YouTube, articles, podcasts)"""
    try:
        with get_db() as conn:
            session = conn.execute(
                "SELECT conversation_history FROM interactive_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            conversation_history = json.loads(session['conversation_history']) if session['conversation_history'] else []
            
            if not conversation_history:
                raise HTTPException(status_code=400, detail="No conversation to analyze")
            
            # Extract keywords first
            keywords_data = await recommendation_engine.keyword_extractor.extract_keywords_and_themes(conversation_history)
            
            # Generate content recommendations
            content_recommendations = await recommendation_engine.content_generator.generate_content_recommendations(
                keywords_data, count
            )
            
            return {
                "session_id": session_id,
                "content_recommendations": [
                    {
                        "title": rec.title,
                        "description": rec.description,
                        "content_type": rec.content_type,
                        "search_query": rec.search_query,
                        "relevance_reason": rec.relevance_reason,
                        "estimated_duration": rec.estimated_duration
                    } for rec in content_recommendations
                ],
                "session_themes": keywords_data.get('therapeutic_themes', []),
                "primary_symptoms": keywords_data.get('primary_symptoms', [])
            }
            
    except Exception as e:
        logger.error(f"Error generating content recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate content recommendations: {str(e)}")

@app.post("/sessions/{session_id}/lifestyle-recommendations")
async def generate_lifestyle_recommendations_only(session_id: int, count: Optional[int] = 6):
    """Generate only lifestyle recommendations based on goals and homework"""
    try:
        with get_db() as conn:
            # Get session and patient data
            session = conn.execute(
                "SELECT conversation_history, patient_id FROM interactive_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            conversation_history = json.loads(session['conversation_history']) if session['conversation_history'] else []
            
            # Get goals and homework
            goals = conn.execute(
                "SELECT * FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
                (session['patient_id'],)
            ).fetchall()
            goals_list = [dict(goal) for goal in goals]
            
            homework = conn.execute(
                "SELECT * FROM homework_assignments WHERE patient_id = ? ORDER BY assigned_date DESC LIMIT 5",
                (session['patient_id'],)
            ).fetchall()
            homework_list = [dict(hw) for hw in homework]
            
            # Extract keywords first
            keywords_data = await recommendation_engine.keyword_extractor.extract_keywords_and_themes(conversation_history)
            
            # Generate lifestyle recommendations
            lifestyle_recommendations = await recommendation_engine.lifestyle_generator.generate_lifestyle_recommendations(
                keywords_data, goals_list, homework_list, count
            )
            
            return {
                "session_id": session_id,
                "lifestyle_recommendations": [
                    {
                        "title": rec.title,
                        "description": rec.description,
                        "activity_type": rec.activity_type,
                        "instructions": rec.instructions,
                        "frequency": rec.frequency,
                        "duration": rec.duration,
                        "difficulty_level": rec.difficulty_level,
                        "relates_to_goal": rec.relates_to_goal,
                        "relates_to_homework": rec.relates_to_homework
                    } for rec in lifestyle_recommendations
                ],
                "active_goals": len(goals_list),
                "recent_homework": len(homework_list),
                "motivation_level": keywords_data.get('motivation_level', 'medium')
            }
            
    except Exception as e:
        logger.error(f"Error generating lifestyle recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate lifestyle recommendations: {str(e)}")

@app.get("/patients/{patient_id}/recommendations-summary")
async def get_patient_recommendations_summary(patient_id: int):
    """Get a summary of all recommendations generated for a patient"""
    try:
        with get_db() as conn:
            # Verify patient exists
            patient = conn.execute("SELECT name FROM patients WHERE id = ?", (patient_id,)).fetchone()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")
            
            # Get all sessions with recommendation data
            sessions_with_recs = conn.execute(
                """SELECT id, session_date, recommendation_data, current_phase 
                   FROM interactive_sessions 
                   WHERE patient_id = ? AND recommendation_data IS NOT NULL
                   ORDER BY session_date DESC""",
                (patient_id,)
            ).fetchall()
            
            summary = {
                "patient_id": patient_id,
                "patient_name": patient['name'],
                "total_sessions_with_recommendations": len(sessions_with_recs),
                "sessions": []
            }
            
            content_types = {}
            activity_types = {}
            common_themes = []
            
            for session in sessions_with_recs:
                try:
                    rec_data = json.loads(session['recommendation_data'])
                    
                    # Count content types
                    for content_rec in rec_data.get('content_recommendations', []):
                        content_type = content_rec.get('content_type', 'unknown')
                        content_types[content_type] = content_types.get(content_type, 0) + 1
                    
                    # Count activity types
                    for lifestyle_rec in rec_data.get('lifestyle_recommendations', []):
                        activity_type = lifestyle_rec.get('activity_type', 'unknown')
                        activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
                    
                    # Collect themes
                    session_themes = rec_data.get('recommendation_metadata', {}).get('session_themes', [])
                    common_themes.extend(session_themes)
                    
                    summary['sessions'].append({
                        "session_id": session['id'],
                        "session_date": session['session_date'],
                        "phase": session['current_phase'],
                        "content_count": len(rec_data.get('content_recommendations', [])),
                        "lifestyle_count": len(rec_data.get('lifestyle_recommendations', [])),
                        "primary_focus": rec_data.get('recommendation_metadata', {}).get('primary_focus', [])
                    })
                    
                except json.JSONDecodeError:
                    continue
            
            # Calculate theme frequency
            theme_counts = Counter(common_themes)
            
            summary.update({
                "content_type_distribution": content_types,
                "activity_type_distribution": activity_types,
                "most_common_themes": dict(theme_counts.most_common(5)),
                "generated_at": datetime.now().isoformat()
            })
            
            return summary
            
    except Exception as e:
        logger.error(f"Error getting recommendations summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations summary: {str(e)}")

@app.get("/recommendations/analytics")
async def get_recommendation_analytics():
    """Get system-wide analytics about recommendations"""
    try:
        with get_db() as conn:
            # Get all sessions with recommendations
            sessions_with_recs = conn.execute(
                """SELECT recommendation_data, session_date, current_phase 
                   FROM interactive_sessions 
                   WHERE recommendation_data IS NOT NULL"""
            ).fetchall()
            
            if not sessions_with_recs:
                return {
                    "message": "No recommendation data available yet",
                    "total_sessions": 0
                }
            
            content_types = {}
            activity_types = {}
            all_themes = []
            primary_symptoms = {}
            motivation_levels = {}
            
            for session in sessions_with_recs:
                try:
                    rec_data = json.loads(session['recommendation_data'])
                    
                    # Analyze content recommendations
                    for content_rec in rec_data.get('content_recommendations', []):
                        content_type = content_rec.get('content_type', 'unknown')
                        content_types[content_type] = content_types.get(content_type, 0) + 1
                    
                    # Analyze lifestyle recommendations
                    for lifestyle_rec in rec_data.get('lifestyle_recommendations', []):
                        activity_type = lifestyle_rec.get('activity_type', 'unknown')
                        activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
                    
                    # Collect metadata
                    metadata = rec_data.get('recommendation_metadata', {})
                    
                    # Themes
                    themes = metadata.get('session_themes', [])
                    all_themes.extend(themes)
                    
                    # Primary symptoms
                    symptoms = metadata.get('primary_focus', [])
                    for symptom in symptoms:
                        primary_symptoms[symptom] = primary_symptoms.get(symptom, 0) + 1
                    
                    # Motivation levels
                    motivation = metadata.get('motivation_level', 'unknown')
                    motivation_levels[motivation] = motivation_levels.get(motivation, 0) + 1
                    
                except json.JSONDecodeError:
                    continue
            
            # Calculate theme frequency
            theme_counts = Counter(all_themes)
            
            return {
                "analytics_summary": {
                    "total_sessions_analyzed": len(sessions_with_recs),
                    "content_type_distribution": dict(sorted(content_types.items(), key=lambda x: x[1], reverse=True)),
                    "activity_type_distribution": dict(sorted(activity_types.items(), key=lambda x: x[1], reverse=True)),
                    "most_common_themes": dict(theme_counts.most_common(10)),
                    "primary_symptoms_addressed": dict(sorted(primary_symptoms.items(), key=lambda x: x[1], reverse=True)),
                    "motivation_level_distribution": motivation_levels
                },
                "insights": {
                    "most_recommended_content": max(content_types.items(), key=lambda x: x[1])[0] if content_types else None,
                    "most_recommended_activity": max(activity_types.items(), key=lambda x: x[1])[0] if activity_types else None,
                    "top_therapeutic_theme": theme_counts.most_common(1)[0][0] if theme_counts else None,
                    "most_common_symptom": max(primary_symptoms.items(), key=lambda x: x[1])[0] if primary_symptoms else None
                },
                "generated_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error generating recommendation analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")

# WebSocket endpoint for real-time chat
@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: int):
    """WebSocket endpoint for real-time therapy chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            if not user_message.strip():
                continue
            
            # Process message using existing chat logic
            with get_db() as conn:
                session = conn.execute(
                    """SELECT s.*, p.name as patient_name FROM interactive_sessions s 
                       JOIN patients p ON s.patient_id = p.id WHERE s.id = ?""",
                    (session_id,)
                ).fetchone()
                
                if not session or session['session_completed']:
                    await websocket.send_text(json.dumps({
                        "error": "Session not found or completed"
                    }))
                    continue
                
                # Get AI response
                ai_result = await therapy_ai.get_ai_response(dict(session), user_message)
                
                # Update session (similar to regular chat endpoint)
                conversation_history = json.loads(session['conversation_history'])
                conversation_history.append({
                    'user': user_message,
                    'ai': ai_result['response'],
                    'timestamp': datetime.now().isoformat(),
                    'phase': session['current_phase']
                })
                
                # Update detected symptoms and phase
                detected_symptoms = json.loads(session['detected_symptoms'])
                for symptom in ai_result['insights'].get('detected_symptoms', []):
                    if symptom not in detected_symptoms:
                        detected_symptoms.append(symptom)
                
                new_phase = ai_result['new_phase']
                session_completed = (new_phase == SessionPhase.COMPLETED.value)
                
                conn.execute(
                    """UPDATE interactive_sessions SET 
                       current_phase = ?, conversation_history = ?, detected_symptoms = ?, 
                       total_exchanges = ?, session_completed = ?
                       WHERE id = ?""",
                    (
                        new_phase,
                        json.dumps(conversation_history),
                        json.dumps(detected_symptoms),
                        len(conversation_history),
                        session_completed,
                        session_id
                    )
                )
                conn.commit()
                
                # Send response back to client
                response = {
                    "response": ai_result['response'],
                    "phase": new_phase,
                    "phase_changed": new_phase != session['current_phase'],
                    "conversation_count": len(conversation_history),
                    "detected_symptoms": detected_symptoms,
                    "session_completed": session_completed,
                    "crisis_detected": ai_result['crisis_detected']
                }
                
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({"error": str(e)}))

# Test endpoints
@app.post("/test/recommendations")
async def test_recommendations():
    """Test endpoint for recommendation engine"""
    try:
        # Sample conversation for testing
        sample_conversation = [
            {
                "user": "I've been feeling really anxious about work lately",
                "ai": "I hear that work has been causing you anxiety. Can you tell me more?",
                "phase": "intake"
            },
            {
                "user": "My boss keeps giving me impossible deadlines and I can't sleep",
                "ai": "That sounds very stressful. Sleep problems often go with work anxiety.",
                "phase": "assessment"
            },
            {
                "user": "I worry about everything and it's affecting my relationships",
                "ai": "It sounds like the anxiety is spreading to other areas of your life. Let's explore some coping strategies.",
                "phase": "therapy"
            }
        ]
        
        # Sample goals
        sample_goals = [
            {
                "goal_type": "symptom",
                "goal_description": "Reduce work-related anxiety from severe to moderate within 8 weeks",
                "status": "active"
            },
            {
                "goal_type": "behavioral", 
                "goal_description": "Establish healthy work boundaries and improve sleep routine",
                "status": "active"
            }
        ]
        
        # Sample homework
        sample_homework = [
            {
                "assignment_type": "thought_record",
                "description": "Track anxious thoughts about work daily using thought record worksheet"
            },
            {
                "assignment_type": "sleep_hygiene",
                "description": "Implement evening routine to improve sleep quality"
            }
        ]
        
        # Generate test recommendations
        recommendations = await recommendation_engine.generate_recommendations(
            conversation_history=sample_conversation,
            goals=sample_goals,
            homework=sample_homework,
            content_count=5,
            lifestyle_count=6
        )
        
        return {
            "test_status": "success",
            "sample_data": {
                "conversation_exchanges": len(sample_conversation),
                "goals_count": len(sample_goals),
                "homework_count": len(sample_homework)
            },
            "recommendations": recommendations,
            "note": "This is test data for demonstration purposes"
        }
        
    except Exception as e:
        logger.error(f"Test recommendations error: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# Export/Import functionality
@app.get("/sessions/{session_id}/recommendations/export")
async def export_session_recommendations(session_id: int):
    """Export session recommendations in structured format"""
    try:
        with get_db() as conn:
            session = conn.execute(
                """SELECT s.*, p.name as patient_name 
                   FROM interactive_sessions s 
                   JOIN patients p ON s.patient_id = p.id 
                   WHERE s.id = ?""",
                (session_id,)
            ).fetchone()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if not session['recommendation_data']:
                raise HTTPException(status_code=404, detail="No recommendations found for this session")
            
            recommendations = json.loads(session['recommendation_data'])
            
            # Format for export
            export_data = {
                "patient_info": {
                    "name": session['patient_name'],
                    "session_date": session['session_date'],
                    "session_id": session_id
                },
                "session_analysis": recommendations.get('session_analysis', {}),
                "content_recommendations": {
                    "total_count": len(recommendations.get('content_recommendations', [])),
                    "recommendations": recommendations.get('content_recommendations', [])
                },
                "lifestyle_recommendations": {
                    "total_count": len(recommendations.get('lifestyle_recommendations', [])), 
                    "recommendations": recommendations.get('lifestyle_recommendations', [])
                },
                "metadata": recommendations.get('recommendation_metadata', {}),
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "format_version": "1.0"
                }
            }
            
            return export_data
            
    except Exception as e:
        logger.error(f"Export recommendations error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# System events
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    init_database()
    logger.info("Complete AI Therapist System initialized")
    logger.info("Features: Sessions, Assessments, Goals, Homework, Recommendations, Diagnosis")

if __name__ == "__main__":
    import uvicorn
    print("🧠 Complete AI Therapist System Starting...")
    print("Features:")
    print("- Fully automated AI therapy sessions")
    print("- Dynamic conversation phases (Intake → Assessment → Therapy → Goals → Homework)")
    print("- Automatic symptom detection and assessment")
    print("- AI-generated treatment plans and homework")
    print("- Content & lifestyle recommendations")
    print("- Diagnosis documentation")
    print("- Crisis detection and safety monitoring")
    print("- Session transcripts and insights")
    print("- Real-time WebSocket support")
    print("- Comprehensive analytics")
    print("\n📖 Set your GEMINI_API_KEY in the code before starting!")
    print("🚀 Starting server on http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)    
