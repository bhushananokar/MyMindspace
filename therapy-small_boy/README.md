# Interactive AI Therapist API

A comprehensive FastAPI-based therapy system powered by Google's Gemini AI that conducts fully automated therapy sessions. The system mimics a professional AI therapist (Dr. Maya) who guides patients through structured therapy sessions including intake, assessment, treatment, goal setting, and homework assignment.

## Overview

This system provides a complete therapeutic experience where the AI therapist:
- Conducts natural conversation-based therapy sessions
- Automatically detects symptoms and mental health concerns
- Performs standardized clinical assessments (PHQ-9, GAD-7)
- Transitions through therapeutic phases dynamically
- Generates personalized treatment plans and goals
- Assigns evidence-based homework assignments
- Monitors for crisis situations and safety concerns
- Creates comprehensive session documentation

## Core Features

### Automated Therapy Sessions
- **Dr. Maya AI Therapist**: Professional, empathetic AI therapist persona
- **Dynamic Phase Management**: Automatic progression through therapy phases
- **Natural Language Processing**: Understands and responds to patient concerns
- **Context Awareness**: Maintains conversation history and therapeutic context
- **Crisis Detection**: Monitors for suicide/self-harm indicators with safety protocols

### Clinical Assessment Integration
- **PHQ-9 Depression Assessment**: Automatic administration and scoring
- **GAD-7 Anxiety Assessment**: Standardized anxiety evaluation
- **Symptom Detection**: Real-time identification of mental health symptoms
- **Severity Scoring**: Clinical interpretation of assessment results
- **Progress Tracking**: Longitudinal monitoring of symptom changes

### Treatment Planning
- **SMART Goals**: Specific, Measurable, Achievable, Relevant, Time-bound objectives
- **Evidence-Based Interventions**: CBT, DBT, ACT therapeutic approaches
- **Homework Assignments**: Personalized therapeutic exercises
- **Progress Monitoring**: Goal achievement tracking and adjustment

## System Architecture

### Technology Stack
- **Framework**: FastAPI with Pydantic models
- **AI Engine**: Google Gemini 2.0 Flash (or compatible model)
- **Database**: SQLite with comprehensive schema
- **Authentication**: CORS-enabled for cross-origin requests
- **Documentation**: OpenAPI/Swagger automatic documentation

### Database Schema

#### Patients Table
```sql
patients (
    id: Primary Key,
    name: Patient name,
    date_of_birth: Optional birth date,
    created_date: Account creation timestamp,
    preferred_therapy_mode: CBT/DBT/ACT/Psychodynamic,
    detected_symptoms: JSON array of identified symptoms,
    notes: Additional patient information
)
```

#### Interactive Sessions Table
```sql
interactive_sessions (
    id: Primary Key,
    patient_id: Foreign key to patients,
    session_date: Session start timestamp,
    current_phase: intake/assessment/therapy/goal_setting/homework_assignment/closing/completed,
    conversation_history: JSON array of all exchanges,
    detected_symptoms: JSON array of symptoms identified during session,
    session_insights: JSON array of therapeutic insights,
    assessment_results: JSON object of completed assessments,
    generated_goals: JSON array of treatment goals,
    session_completed: Boolean completion status,
    total_exchanges: Number of conversation rounds,
    crisis_flags: JSON array of safety concerns
)
```

#### Treatment Goals Table
```sql
treatment_goals (
    id: Primary Key,
    patient_id: Foreign key to patients,
    session_id: Foreign key to interactive_sessions,
    goal_type: symptom/behavioral/functional/interpersonal/cognitive,
    goal_description: Detailed goal statement,
    target_date: Expected completion date,
    current_progress: Percentage (0-100),
    status: active/achieved/modified/discontinued,
    created_date: Goal creation timestamp
)
```

#### Homework Assignments Table
```sql
homework_assignments (
    id: Primary Key,
    patient_id: Foreign key to patients,
    session_id: Foreign key to interactive_sessions,
    assignment_type: thought_record/activity_scheduling/behavioral_experiment/etc,
    description: Assignment description,
    instructions: Detailed completion instructions,
    assigned_date: Assignment creation timestamp,
    due_date: Expected completion date,
    completed: Boolean completion status
)
```

## Session Flow Architecture

### Phase 1: Intake (Exchanges 1-6)
**Objective**: Establish rapport and understand presenting concerns
- AI introduces itself as Dr. Maya, professional therapist
- Explores what brought the patient to therapy
- Identifies primary concerns and stressors
- Assesses support systems and coping mechanisms
- Builds therapeutic alliance and trust

**AI Behavior**:
- Warm, empathetic greeting and introduction
- Open-ended questions about current struggles
- Active listening with reflective responses
- Gentle exploration of symptoms without leading
- Assessment of immediate safety concerns

### Phase 2: Assessment (Exchanges 7-12)
**Objective**: Conduct formal clinical assessment
- Administers standardized assessments based on detected symptoms
- Explores symptom frequency, severity, and duration
- Assesses functional impairment and daily life impact
- Evaluates risk factors and protective factors
- Determines appropriate treatment modality

**AI Behavior**:
- Introduces formal assessment process
- Asks structured PHQ-9 or GAD-7 questions
- Explores symptom patterns and triggers
- Assesses impact on work, relationships, daily functioning
- Provides normalizing and validating responses

**Automated Processes**:
- Symptom detection algorithm analyzes conversation
- Selects appropriate assessments (PHQ-9 for depression, GAD-7 for anxiety)
- Simulates realistic responses based on conversation content
- Calculates scores and severity levels
- Stores results for treatment planning

### Phase 3: Therapy (Exchanges 13-18)
**Objective**: Provide evidence-based therapeutic interventions
- Implements CBT techniques by default (cognitive restructuring, behavioral activation)
- Explores thought-feeling-behavior connections
- Challenges cognitive distortions and negative thinking patterns
- Teaches coping strategies and emotional regulation skills
- Provides psychoeducation about identified conditions

**AI Behavior**:
- Uses Socratic questioning to explore thoughts and beliefs
- Introduces cognitive behavioral concepts
- Helps identify thinking patterns and triggers
- Teaches practical coping strategies
- Provides homework suggestions for skill practice

### Phase 4: Goal Setting (Exchanges 19-22)
**Objective**: Collaborative treatment goal establishment
- Creates SMART goals based on assessment and conversation
- Prioritizes goals by importance and achievability
- Establishes measurable outcomes and timelines
- Discusses potential obstacles and solutions
- Ensures goals align with patient values and priorities

**AI Behavior**:
- Reviews session themes and identified concerns
- Guides collaborative goal formulation
- Ensures goals are specific and measurable
- Discusses realistic timelines and milestones
- Confirms patient commitment and motivation

**Automated Processes**:
- AI analyzes conversation to identify key themes
- Generates 3-4 SMART goals using Gemini AI
- Categorizes goals by type (symptom, behavioral, functional)
- Sets appropriate target dates (typically 3-6 months)
- Stores goals in database with active status

### Phase 5: Homework Assignment (Exchanges 23-25)
**Objective**: Assign evidence-based between-session activities
- Provides homework assignments matched to therapy modality
- Explains rationale and expected benefits
- Ensures assignments are appropriately challenging
- Gives clear instructions and completion criteria
- Sets realistic expectations and timelines

**AI Behavior**:
- Introduces homework as collaborative treatment component
- Explains specific assignment details and rationale
- Addresses potential barriers or concerns
- Provides encouragement and motivation
- Sets clear expectations for completion and review

**Assignment Types by Modality**:
- **CBT**: Thought records, activity scheduling, behavioral experiments
- **DBT**: Mindfulness practice, distress tolerance skills, emotion regulation
- **ACT**: Values exploration, defusion exercises, mindfulness meditation
- **Psychodynamic**: Reflection journaling, pattern recognition, insight exercises

### Phase 6: Closing (Exchanges 26-27)
**Objective**: Session wrap-up and planning
- Summarizes key session themes and insights
- Reviews goals and homework assignments
- Addresses remaining questions or concerns
- Provides crisis resources if needed
- Schedules or discusses next steps

## API Endpoints Reference

### Core Session Management

#### Start Interactive Session
```http
POST /sessions/start
Content-Type: application/json

{
  "patient_id": 1
}
```

**Response**:
```json
{
  "session_id": 123,
  "patient_name": "John Doe",
  "initial_message": "Hello John, I'm Dr. Maya. I'm so glad you're here today...",
  "phase": "intake"
}
```

#### Continue Session Chat
```http
POST /sessions/chat
Content-Type: application/json

{
  "message": "I've been feeling really anxious lately and can't sleep",
  "session_id": 123
}
```

**Response**:
```json
{
  "response": "I'm sorry to hear you've been struggling with anxiety and sleep...",
  "phase": "intake",
  "phase_changed": false,
  "conversation_count": 3,
  "detected_symptoms": ["anxiety", "sleep"],
  "session_completed": false,
  "crisis_alert": null
}
```

#### Get Session Details
```http
GET /sessions/{session_id}
```

**Response**:
```json
{
  "id": 123,
  "patient_id": 1,
  "patient_name": "John Doe",
  "session_date": "2024-01-15T10:30:00",
  "current_phase": "therapy",
  "conversation_history": [
    {
      "user": "I've been feeling anxious",
      "ai": "Tell me more about that anxiety...",
      "timestamp": "2024-01-15T10:31:00",
      "phase": "intake"
    }
  ],
  "detected_symptoms": ["anxiety", "sleep", "depression"],
  "assessment_results": {
    "GAD7": {
      "total_score": 12,
      "severity": "Moderate anxiety",
      "interpretation": "Score of 12 indicates moderate anxiety"
    }
  },
  "goals": [
    {
      "id": 456,
      "goal_type": "symptom",
      "goal_description": "Reduce anxiety symptoms to mild level within 8 weeks",
      "current_progress": 0,
      "status": "active"
    }
  ],
  "homework": [
    {
      "id": 789,
      "assignment_type": "thought_record",
      "description": "Complete daily thought records for negative thoughts",
      "due_date": "2024-01-22T00:00:00",
      "completed": false
    }
  ],
  "total_exchanges": 15,
  "session_completed": false
}
```

### Patient Management

#### Create Patient
```http
POST /patients
Content-Type: application/json

{
  "name": "John Doe"
}
```

#### List All Patients
```http
GET /patients
```

#### Get Patient Sessions
```http
GET /patients/{patient_id}/sessions
```

#### Get Patient Dashboard
```http
GET /patients/{patient_id}/dashboard
```

**Response**: Comprehensive patient overview including recent sessions, active goals, pending homework, assessment results, and summary statistics.

### Session Analysis and Export

#### Get Session Insights
```http
GET /sessions/{session_id}/insights
```

**Response**:
```json
{
  "session_id": 123,
  "patient_name": "John Doe",
  "session_stats": {
    "total_exchanges": 25,
    "current_phase": "completed",
    "detected_symptoms": ["anxiety", "depression", "sleep"],
    "session_completed": true
  },
  "ai_insights": "This session revealed significant anxiety symptoms with sleep disturbances. The patient shows good insight and motivation for change. Recommended CBT approach with focus on cognitive restructuring and sleep hygiene. Goals appropriately target symptom reduction and functional improvement.",
  "session_insights": [
    {
      "timestamp": "2024-01-15T10:35:00",
      "insights": {
        "detected_symptoms": ["anxiety"],
        "mood_indicators": ["low_mood"],
        "cognitive_patterns": ["catastrophizing"]
      },
      "phase": "intake"
    }
  ]
}
```

#### Export Session Transcript
```http
GET /sessions/{session_id}/export
```

**Response**: Complete session transcript in text format including conversation history, assessment results, treatment plan, and session metadata.

### Progress Tracking

#### Complete Homework Assignment
```http
POST /homework/{homework_id}/complete
Content-Type: application/json

{
  "notes": "Completed 5 thought records this week. Very helpful!",
  "rating": 4
}
```

#### Update Goal Progress
```http
GET /goals/{goal_id}/progress?progress=75
```

### System Administration

#### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0",
  "features": [
    "Interactive AI Therapy Sessions",
    "Automated Assessment Conducting",
    "Dynamic Phase Transitions",
    "AI-Generated Treatment Plans",
    "Crisis Detection",
    "Session Transcripts",
    "Real-time WebSocket Chat"
  ]
}
```

#### System Analytics
```http
GET /analytics
```

#### Fix Database Schema
```http
GET /admin/fix-database
```

## Setup and Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key
- Internet connection for AI API calls

### Installation Steps

1. **Install Dependencies**:
```bash
pip install fastapi uvicorn google-generativeai
```

2. **Configure Gemini API**:
   - Obtain API key from Google AI Studio
   - Replace `"YOUR_GEMINI_API_KEY_HERE"` in the code
   - Alternatively, set environment variable: `export GEMINI_API_KEY="your-key"`

3. **Run the Server**:
```bash
python main.py
```

4. **Verify Installation**:
   - Server starts on `http://localhost:8000`
   - API documentation available at `http://localhost:8000/docs`
   - Health check at `http://localhost:8000/health`

### Configuration Options

#### Gemini Model Selection
```python
# In InteractiveTherapyAI class
self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Latest model
# Alternative models:
# 'gemini-1.5-pro'     # More capable but slower
# 'gemini-1.5-flash'   # Faster but less capable
```

#### Database Location
```python
DATABASE_PATH = "therapy.db"  # Default location
# Change to custom path:
# DATABASE_PATH = "/path/to/custom/therapy_database.db"
```

#### Phase Transition Thresholds
```python
# In _check_phase_transition method
if current_phase == SessionPhase.INTAKE.value and conversation_count >= 6:
    return SessionPhase.ASSESSMENT.value
# Adjust numbers to change when phases transition
```

## Usage Examples

### Basic Session Flow
```python
# 1. Create patient
patient_response = requests.post("http://localhost:8000/patients", 
                                json={"name": "Alice Smith"})
patient_id = patient_response.json()["id"]

# 2. Start session
session_response = requests.post("http://localhost:8000/sessions/start",
                                json={"patient_id": patient_id})
session_id = session_response.json()["session_id"]

# 3. Conduct therapy conversation
messages = [
    "I've been feeling really depressed lately",
    "I can't seem to enjoy anything anymore",
    "I'm having trouble sleeping and eating",
    "Work feels overwhelming and pointless",
    # ... continue natural conversation
]

for message in messages:
    response = requests.post("http://localhost:8000/sessions/chat",
                           json={"message": message, "session_id": session_id})
    ai_response = response.json()["response"]
    print(f"Patient: {message}")
    print(f"Dr. Maya: {ai_response}")
    print(f"Phase: {response.json()['phase']}")
    print("---")

# 4. Get final session results
session_details = requests.get(f"http://localhost:8000/sessions/{session_id}")
print("Assessment Results:", session_details.json()["assessment_results"])
print("Generated Goals:", session_details.json()["goals"])
print("Homework Assignments:", session_details.json()["homework"])
```

### WebSocket Real-Time Chat
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log("AI Response:", data.response);
    console.log("Current Phase:", data.phase);
    
    if (data.crisis_detected) {
        alert("Crisis detected! Safety protocols activated.");
    }
    
    if (data.session_completed) {
        console.log("Session completed with treatment plan generated");
    }
};

// Send message
ws.send(JSON.stringify({
    message: "I'm feeling anxious about my job interview tomorrow"
}));
```

## Customization and Extension

### Adding New Assessment Tools
```python
# In InteractiveTherapyAI.__init__()
self.assessments["CUSTOM_SCALE"] = {
    "name": "Custom Assessment Scale",
    "questions": [
        "Question 1 text",
        "Question 2 text",
        # ... additional questions
    ],
    "scoring": {
        (0, 10): "Low severity",
        (11, 20): "Moderate severity",
        (21, 30): "High severity"
    }
}
```

### Custom Therapy Modalities
```python
def _get_custom_therapy_prompt(self, patient_name, user_input, history, symptoms):
    return f"""You are Dr. Maya conducting {custom_modality} therapy...
    
    Specific techniques for this modality:
    - Technique 1
    - Technique 2
    
    Patient input: {user_input}
    Respond with appropriate {custom_modality} interventions."""
```

### Modified Phase Transitions
```python
async def _check_phase_transition(self, current_phase, conversation_count, symptoms):
    # Custom logic for phase transitions
    if current_phase == "intake" and "severe_depression" in symptoms:
        return "crisis_assessment"  # Skip to crisis mode
    
    # Custom phase durations
    if current_phase == "therapy" and conversation_count >= 25:  # Longer therapy phase
        return "goal_setting"
    
    return current_phase
```

## Error Handling and Troubleshooting

### Common Issues

#### Database Schema Errors
```
sqlite3.OperationalError: no such column: session_id
```
**Solution**: Use `/admin/fix-database` endpoint to add missing columns

#### Gemini API Errors
```
google.generativeai.errors.ResourceExhausted
```
**Solution**: Check API key validity and usage limits

#### CORS Issues
```
Failed to fetch: CORS policy blocked
```
**Solution**: Ensure CORS middleware is properly configured

### Debug Mode
Enable detailed logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Backup
```python
# Backup database before major operations
import shutil
shutil.copy("therapy.db", "therapy_backup.db")
```

## Security Considerations

### Data Protection
- Patient data stored locally in SQLite database
- No data transmitted to external services except Gemini API
- Conversation history encrypted in storage (implement as needed)
- Regular database backups recommended

### Crisis Safety Protocols
- Automatic detection of suicide/self-harm language
- Crisis flags logged and alerted immediately
- System provides crisis hotline information
- Professional referral recommendations for high-risk cases

### API Security
- Input validation on all endpoints
- Rate limiting for API calls
- SQL injection prevention through parameterized queries
- Authentication system (implement as needed for production)

## Performance Optimization

### Database Optimization
```sql
-- Create indices for frequently queried columns
CREATE INDEX idx_patient_sessions ON interactive_sessions(patient_id);
CREATE INDEX idx_session_date ON interactive_sessions(session_date);
CREATE INDEX idx_goal_patient ON treatment_goals(patient_id);
```

### Gemini API Optimization
- Implement response caching for common queries
- Use connection pooling for concurrent requests
- Monitor and optimize prompt length
- Implement fallback responses for API failures

### Scalability Considerations
- Database migration to PostgreSQL for production
- Redis caching for session state
- Load balancing for multiple instances
- Separate analytics database for reporting


##Demo
#Thoughts of the model are also displayed in the demo when neccessary (enclosed in '()')
https://www.loom.com/share/d986203ba1af402a8e6e50cf11d9102b?sid=a59f6c0f-131d-40d7-9478-1ad587e74ab3
This comprehensive system provides a complete therapeutic experience while maintaining professional standards and clinical safety protocols.
