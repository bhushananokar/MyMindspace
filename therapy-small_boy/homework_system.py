#!/usr/bin/env python3
"""
AI Therapy System - Homework Assignment Management System
Comprehensive homework assignment creation, tracking, and effectiveness monitoring
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

from database import DatabaseManager
from config import HomeworkTemplates, TherapyProtocols
from utils import log_action


class AssignmentType(Enum):
    """Types of homework assignments"""
    THOUGHT_RECORD = "thought_record"
    ACTIVITY_LOG = "activity_log"
    EXPOSURE_PRACTICE = "exposure_practice"
    MINDFULNESS_PRACTICE = "mindfulness_practice"
    SKILL_PRACTICE = "skill_practice"
    BEHAVIORAL_EXPERIMENT = "behavioral_experiment"
    MOOD_TRACKING = "mood_tracking"
    VALUES_EXERCISE = "values_exercise"
    COMMUNICATION_PRACTICE = "communication_practice"
    SELF_MONITORING = "self_monitoring"
    READING_ASSIGNMENT = "reading_assignment"
    RELAXATION_PRACTICE = "relaxation_practice"


class DifficultyLevel(Enum):
    """Difficulty levels for assignments"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    CHALLENGING = 4
    EXPERT = 5


class CompletionStatus(Enum):
    """Assignment completion status"""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    NOT_COMPLETED = "not_completed"
    EXTENDED = "extended"


@dataclass
class HomeworkAssignment:
    """Comprehensive homework assignment structure"""
    id: Optional[int] = None
    patient_id: int = 0
    session_id: Optional[int] = None
    assignment_type: str = AssignmentType.THOUGHT_RECORD.value
    title: str = ""
    description: str = ""
    instructions: str = ""
    learning_objectives: List[str] = field(default_factory=list)
    materials_needed: List[str] = field(default_factory=list)
    estimated_time: int = 15  # minutes
    difficulty_level: int = DifficultyLevel.BEGINNER.value
    therapy_modality: str = "CBT"
    assigned_date: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: str = ""
    completed: bool = False
    completion_date: Optional[str] = None
    completion_status: str = CompletionStatus.ASSIGNED.value
    completion_notes: str = ""
    effectiveness_rating: Optional[int] = None  # 1-5 scale
    difficulty_rating: Optional[int] = None  # 1-5 scale
    time_spent: Optional[int] = None  # actual minutes spent
    barriers_encountered: List[str] = field(default_factory=list)
    insights_gained: List[str] = field(default_factory=list)
    follow_up_needed: bool = False
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssignmentTemplate:
    """Template for creating homework assignments"""
    template_id: str = ""
    name: str = ""
    assignment_type: str = ""
    therapy_modality: str = ""
    target_symptoms: List[str] = field(default_factory=list)
    difficulty_level: int = DifficultyLevel.BEGINNER.value
    estimated_time: int = 15
    description_template: str = ""
    instructions_template: str = ""
    learning_objectives: List[str] = field(default_factory=list)
    materials_needed: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    common_barriers: List[str] = field(default_factory=list)
    modifications: Dict[str, str] = field(default_factory=dict)


class HomeworkSystem:
    """Manages homework assignments, tracking, and effectiveness monitoring"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.assignment_templates = self._load_assignment_templates()
        self._init_homework_tables()
    
    def _init_homework_tables(self):
        """Initialize homework-related database tables"""
        with self.db.get_connection() as conn:
            # Assignment templates table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS assignment_templates (
                    id INTEGER PRIMARY KEY,
                    template_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    assignment_type TEXT NOT NULL,
                    therapy_modality TEXT NOT NULL,
                    target_symptoms TEXT DEFAULT '[]',
                    difficulty_level INTEGER DEFAULT 1,
                    estimated_time INTEGER DEFAULT 15,
                    description_template TEXT NOT NULL,
                    instructions_template TEXT NOT NULL,
                    learning_objectives TEXT DEFAULT '[]',
                    materials_needed TEXT DEFAULT '[]',
                    success_criteria TEXT DEFAULT '[]',
                    common_barriers TEXT DEFAULT '[]',
                    modifications TEXT DEFAULT '{}',
                    created_date TEXT NOT NULL DEFAULT (datetime('now')),
                    active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Assignment progress tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS assignment_progress (
                    id INTEGER PRIMARY KEY,
                    assignment_id INTEGER NOT NULL,
                    progress_date TEXT NOT NULL DEFAULT (datetime('now')),
                    progress_notes TEXT,
                    time_spent INTEGER,
                    barriers_encountered TEXT DEFAULT '[]',
                    insights_gained TEXT DEFAULT '[]',
                    completion_percentage INTEGER DEFAULT 0,
                    mood_before INTEGER,
                    mood_after INTEGER,
                    FOREIGN KEY (assignment_id) REFERENCES homework_assignments(id) ON DELETE CASCADE
                )
            ''')
            
            # Assignment reminders table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS assignment_reminders (
                    id INTEGER PRIMARY KEY,
                    assignment_id INTEGER NOT NULL,
                    reminder_date TEXT NOT NULL,
                    reminder_type TEXT DEFAULT 'due_soon',
                    message TEXT,
                    sent BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (assignment_id) REFERENCES homework_assignments(id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def _load_assignment_templates(self) -> Dict[str, AssignmentTemplate]:
        """Load pre-defined assignment templates"""
        templates = {}
        
        # CBT Templates
        templates['cbt_thought_record'] = AssignmentTemplate(
            template_id='cbt_thought_record',
            name='Daily Thought Record',
            assignment_type=AssignmentType.THOUGHT_RECORD.value,
            therapy_modality='CBT',
            target_symptoms=['depression', 'anxiety', 'negative_thinking'],
            difficulty_level=DifficultyLevel.BEGINNER.value,
            estimated_time=20,
            description_template='Track your automatic thoughts and examine the evidence for and against them',
            instructions_template='''Daily Thought Record Instructions:

1. When you notice feeling upset, anxious, or distressed, pause and identify:
   - The situation that triggered the feeling
   - Your automatic thoughts
   - Your emotions and their intensity (0-10)
   - Physical sensations you noticed

2. Examine the evidence:
   - What evidence supports this thought?
   - What evidence contradicts this thought?
   - What would you tell a friend in this situation?

3. Develop a more balanced thought:
   - Consider alternative perspectives
   - Focus on facts rather than assumptions
   - Rate your emotions again (0-10) after reframing

4. Plan a helpful response or action

Complete this exercise at least once daily, ideally when you notice difficult emotions.''',
            learning_objectives=[
                'Increase awareness of automatic thoughts',
                'Learn to examine evidence objectively',
                'Develop more balanced thinking patterns',
                'Reduce emotional intensity through cognitive restructuring'
            ],
            materials_needed=['Thought record worksheet', 'Pen/pencil', 'Quiet space for reflection'],
            success_criteria=[
                'Completes at least 5 thought records during the week',
                'Shows evidence of examining thoughts objectively',
                'Demonstrates ability to generate alternative perspectives'
            ],
            common_barriers=[
                'Forgetting to complete when upset',
                'Difficulty identifying thoughts vs. feelings',
                'Resistance to challenging negative thoughts'
            ]
        )
        
        templates['cbt_activity_schedule'] = AssignmentTemplate(
            template_id='cbt_activity_schedule',
            name='Weekly Activity Schedule',
            assignment_type=AssignmentType.ACTIVITY_LOG.value,
            therapy_modality='CBT',
            target_symptoms=['depression', 'low_motivation', 'anhedonia'],
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            estimated_time=30,
            description_template='Plan and track daily activities, rating them for pleasure and mastery',
            instructions_template='''Weekly Activity Schedule Instructions:

1. Planning Phase:
   - Schedule activities for each day of the week
   - Include necessary tasks, pleasant activities, and meaningful pursuits
   - Start with small, achievable activities
   - Balance solitary and social activities

2. Daily Tracking:
   - Rate each completed activity for:
     * Pleasure (P): How much you enjoyed it (0-10)
     * Mastery (M): How accomplished you felt (0-10)
   - Note your mood before and after activities
   - Record any insights or observations

3. Weekly Review:
   - Identify patterns between activities and mood
   - Notice which activities provide the most pleasure/mastery
   - Plan next week based on what worked well

Aim for a mix of activities that provide either pleasure, mastery, or both.''',
            learning_objectives=[
                'Increase engagement in meaningful activities',
                'Identify relationship between activities and mood',
                'Develop better activity planning skills',
                'Combat behavioral inactivity and isolation'
            ],
            materials_needed=['Activity schedule template', 'Daily planner', 'Mood tracking sheet'],
            success_criteria=[
                'Completes activity planning for at least 5 days',
                'Rates activities for pleasure and mastery consistently',
                'Shows increased engagement in pleasant activities'
            ]
        )
        
        templates['cbt_behavioral_experiment'] = AssignmentTemplate(
            template_id='cbt_behavioral_experiment',
            name='Behavioral Experiment',
            assignment_type=AssignmentType.BEHAVIORAL_EXPERIMENT.value,
            therapy_modality='CBT',
            target_symptoms=['anxiety', 'avoidance', 'social_anxiety'],
            difficulty_level=DifficultyLevel.ADVANCED.value,
            estimated_time=60,
            description_template='Test the accuracy of your predictions through planned behavioral experiments',
            instructions_template='''Behavioral Experiment Instructions:

1. Identify the Prediction:
   - What specific situation are you avoiding?
   - What do you predict will happen? (be specific)
   - How confident are you in this prediction? (0-100%)
   - What evidence is this prediction based on?

2. Design the Experiment:
   - Plan a specific, manageable way to test your prediction
   - Identify what you will observe and measure
   - Set a specific time and place for the experiment
   - Plan coping strategies if anxiety arises

3. Conduct the Experiment:
   - Follow through with your planned activity
   - Observe what actually happens
   - Note your anxiety levels before, during, and after
   - Collect evidence about your prediction

4. Review the Results:
   - Was your prediction accurate?
   - What actually happened vs. what you expected?
   - What did you learn from this experience?
   - How might this change your future behavior?''',
            learning_objectives=[
                'Test the accuracy of anxious predictions',
                'Gather real-world evidence about feared situations',
                'Reduce avoidance behaviors',
                'Build confidence through direct experience'
            ],
            materials_needed=['Experiment planning sheet', 'Anxiety rating scale', 'Observation log']
        )
        
        # DBT Templates
        templates['dbt_mindfulness_practice'] = AssignmentTemplate(
            template_id='dbt_mindfulness_practice',
            name='Daily Mindfulness Practice',
            assignment_type=AssignmentType.MINDFULNESS_PRACTICE.value,
            therapy_modality='DBT',
            target_symptoms=['emotional_dysregulation', 'impulsivity', 'stress'],
            difficulty_level=DifficultyLevel.BEGINNER.value,
            estimated_time=15,
            description_template='Practice core mindfulness skills daily using the "What" and "How" skills',
            instructions_template='''Daily Mindfulness Practice Instructions:

"What" Skills - What you do:
1. OBSERVE: Notice your internal experiences (thoughts, feelings, sensations) and external environment without trying to change anything
2. DESCRIBE: Put words to your experiences using facts, not judgments
3. PARTICIPATE: Fully engage in your current activity with complete attention

"How" Skills - How you do it:
1. NON-JUDGMENTALLY: Accept experiences without labeling them as good or bad
2. ONE-MINDFULLY: Focus your attention on one thing at a time
3. EFFECTIVELY: Do what works to achieve your goals

Daily Practice:
- Choose one mindfulness exercise each day (breathing, body scan, mindful walking, etc.)
- Practice for 10-15 minutes
- Use the "What" and "How" skills during practice
- Complete brief reflection afterward''',
            learning_objectives=[
                'Develop present-moment awareness',
                'Learn to observe without judgment',
                'Improve emotional regulation through mindfulness',
                'Build foundation for other DBT skills'
            ],
            materials_needed=['Quiet space', 'Timer', 'Mindfulness exercise instructions'],
            success_criteria=[
                'Practices mindfulness at least 5 days per week',
                'Demonstrates understanding of "What" and "How" skills',
                'Shows increased present-moment awareness'
            ]
        )
        
        templates['dbt_distress_tolerance'] = AssignmentTemplate(
            template_id='dbt_distress_tolerance',
            name='Distress Tolerance Skills Practice',
            assignment_type=AssignmentType.SKILL_PRACTICE.value,
            therapy_modality='DBT',
            target_symptoms=['crisis_situations', 'overwhelming_emotions', 'impulsivity'],
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            estimated_time=25,
            description_template='Practice distress tolerance skills to survive crisis situations without making them worse',
            instructions_template='''Distress Tolerance Skills Practice:

Crisis Survival Skills:
1. TIPP (use when overwhelmed):
   - Temperature: Cold water on face/hands or ice cubes
   - Intense Exercise: 10-15 minutes of vigorous activity
   - Paced Breathing: Breathe out longer than you breathe in
   - Paired Muscle Relaxation: Tense and release muscle groups

2. DISTRACT (when you can't solve the problem right now):
   - Activities: Engage in absorbing activities
   - Contributing: Help others or do something meaningful
   - Comparisons: Compare to less fortunate times/people
   - Emotions: Create different emotions (funny videos, uplifting music)
   - Push away: Mentally push the situation away temporarily
   - Thoughts: Count, recite, do puzzles
   - Sensations: Hold ice, listen to loud music, hot/cold shower

Practice Instructions:
- Choose 2-3 skills to focus on this week
- Use them when experiencing distress (before it becomes crisis)
- Rate distress before and after using skills (0-10)
- Note which skills work best for different situations''',
            learning_objectives=[
                'Learn to tolerate distressing emotions without impulsive actions',
                'Develop crisis survival skills repertoire',
                'Reduce self-destructive behaviors',
                'Increase confidence in handling difficult emotions'
            ]
        )
        
        # ACT Templates
        templates['act_values_clarification'] = AssignmentTemplate(
            template_id='act_values_clarification',
            name='Values Exploration Exercise',
            assignment_type=AssignmentType.VALUES_EXERCISE.value,
            therapy_modality='ACT',
            target_symptoms=['lack_of_direction', 'meaninglessness', 'depression'],
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            estimated_time=45,
            description_template='Explore and clarify your core personal values across different life domains',
            instructions_template='''Values Exploration Instructions:

1. Life Domains Assessment:
   Review these life areas and consider what matters most to you:
   - Family/Relationships
   - Career/Work
   - Education/Personal Growth
   - Recreation/Fun
   - Spirituality/Meaning
   - Community/Citizenship
   - Physical Health
   - Mental Health

2. Values Identification:
   For each domain, ask yourself:
   - What do I want to stand for?
   - What kind of person do I want to be in this area?
   - What would I want written about me regarding this domain?
   
3. Values vs. Goals Distinction:
   - Values are ongoing directions (like "being loving")
   - Goals are achievable outcomes (like "get married")
   - Focus on the values, not just the goals

4. Current Living Assessment:
   Rate how well you're currently living each value (0-10)
   Identify gaps between your values and actions

5. Action Planning:
   Choose one small action this week that moves you toward your most important values''',
            learning_objectives=[
                'Clarify personal values and life directions',
                'Distinguish between values and goals',
                'Increase motivation through values connection',
                'Plan values-consistent actions'
            ]
        )
        
        templates['act_cognitive_defusion'] = AssignmentTemplate(
            template_id='act_cognitive_defusion',
            name='Cognitive Defusion Exercises',
            assignment_type=AssignmentType.SKILL_PRACTICE.value,
            therapy_modality='ACT',
            target_symptoms=['rumination', 'cognitive_fusion', 'anxiety'],
            difficulty_level=DifficultyLevel.ADVANCED.value,
            estimated_time=20,
            description_template='Practice creating psychological distance from difficult thoughts',
            instructions_template='''Cognitive Defusion Exercises:

1. "I'm Having the Thought That..." Technique:
   - When you notice a difficult thought, add the prefix:
   - Instead of "I'm a failure" → "I'm having the thought that I'm a failure"
   - Notice how this changes your relationship to the thought

2. Silly Voice Technique:
   - Take the difficult thought and say it in a silly cartoon voice
   - Try Mickey Mouse, Darth Vader, or a robot voice
   - Notice how this affects the thought's power over you

3. Thoughts as Leaves on a Stream:
   - Imagine your thoughts as leaves floating down a stream
   - Don't try to stop them or grab them
   - Just watch them float by

4. Thank Your Mind:
   - When your mind offers unhelpful thoughts, simply say:
   - "Thanks, mind, for that thought"
   - Acknowledge without buying into it

Practice Schedule:
- Use these techniques 3-4 times daily
- Focus especially on repetitive or distressing thoughts
- Note which techniques work best for you
- Remember: the goal isn't to eliminate thoughts, but to change your relationship with them''',
            learning_objectives=[
                'Develop psychological flexibility with thoughts',
                'Reduce cognitive fusion and rumination',
                'Learn that thoughts are mental events, not facts',
                'Increase ability to act on values despite difficult thoughts'
            ]
        )
        
        # Add mood and self-monitoring templates
        templates['mood_tracking'] = AssignmentTemplate(
            template_id='mood_tracking',
            name='Daily Mood and Symptom Tracking',
            assignment_type=AssignmentType.MOOD_TRACKING.value,
            therapy_modality='General',
            target_symptoms=['mood_fluctuations', 'symptom_monitoring'],
            difficulty_level=DifficultyLevel.BEGINNER.value,
            estimated_time=10,
            description_template='Track daily mood patterns and associated factors',
            instructions_template='''Daily Mood Tracking Instructions:

Morning Check-in (5 minutes):
- Rate your mood upon waking (1-10 scale)
- Note sleep quality and duration
- Identify any immediate stressors or concerns
- Set a mood goal for the day

Evening Reflection (5 minutes):
- Rate your overall mood for the day (1-10 scale)
- Note significant events or interactions
- Identify factors that influenced your mood positively/negatively
- Rate anxiety, energy, and motivation levels
- Record any coping strategies used

Weekly Pattern Review:
- Look for patterns in mood fluctuations
- Identify triggers and protective factors
- Note progress over time
- Adjust strategies based on observations''',
            learning_objectives=[
                'Increase awareness of mood patterns',
                'Identify triggers and protective factors',
                'Track treatment progress objectively',
                'Develop better self-monitoring skills'
            ]
        )
        
        return templates
    
    def create_assignment(self, patient_id: int, template_id: str = None, 
                         custom_params: Dict[str, Any] = None, 
                         session_id: int = None) -> HomeworkAssignment:
        """Create homework assignment from template or custom parameters"""
        
        assignment = HomeworkAssignment(patient_id=patient_id, session_id=session_id)
        
        # Use template if specified
        if template_id and template_id in self.assignment_templates:
            template = self.assignment_templates[template_id]
            
            assignment.assignment_type = template.assignment_type
            assignment.title = template.name
            assignment.description = template.description_template
            assignment.instructions = template.instructions_template
            assignment.learning_objectives = template.learning_objectives.copy()
            assignment.materials_needed = template.materials_needed.copy()
            assignment.estimated_time = template.estimated_time
            assignment.difficulty_level = template.difficulty_level
            assignment.therapy_modality = template.therapy_modality
            
            # Set due date based on assignment type
            if template.assignment_type in [AssignmentType.THOUGHT_RECORD.value, AssignmentType.MOOD_TRACKING.value]:
                # Daily assignments - due in 1 week
                assignment.due_date = (datetime.now() + timedelta(days=7)).isoformat()
            elif template.assignment_type == AssignmentType.MINDFULNESS_PRACTICE.value:
                # Practice assignments - due in 1 week
                assignment.due_date = (datetime.now() + timedelta(days=7)).isoformat()
            else:
                # Other assignments - due in 3-5 days
                assignment.due_date = (datetime.now() + timedelta(days=4)).isoformat()
        
        # Override with custom parameters
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(assignment, key):
                    setattr(assignment, key, value)
        
        # Personalize assignment based on patient data
        assignment = self._personalize_assignment(assignment)
        
        # Save to database
        assignment_id = self._save_assignment(assignment)
        assignment.id = assignment_id
        
        # Create reminders
        self._create_assignment_reminders(assignment)
        
        log_action(f"Homework assignment created: {assignment.title}", 
                  "homework_system", patient_id=patient_id)
        
        return assignment
    
    def _personalize_assignment(self, assignment: HomeworkAssignment) -> HomeworkAssignment:
        """Personalize assignment based on patient data"""
        
        # Get patient information
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (assignment.patient_id,)
        )
        
        if not patient_data:
            return assignment
        
        patient = patient_data[0]
        
        # Get patient's diagnoses
        diagnoses = self.db.execute_query(
            "SELECT diagnosis_name FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (assignment.patient_id,)
        )
        
        diagnosis_names = [d['diagnosis_name'].lower() for d in diagnoses]
        
        # Get recent assessment scores
        recent_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 3",
            (assignment.patient_id,)
        )
        
        # Adjust difficulty based on assessment scores
        if recent_assessments:
            latest_assessment = recent_assessments[0]
            if latest_assessment['assessment_type'] in ['PHQ9', 'GAD7', 'PCL5']:
                if latest_assessment['total_score'] > 15:  # High severity
                    assignment.difficulty_level = max(1, assignment.difficulty_level - 1)
                    assignment.estimated_time = max(10, assignment.estimated_time - 5)
        
        # Modify instructions based on diagnoses
        if any('depression' in dx for dx in diagnosis_names):
            if assignment.assignment_type == AssignmentType.ACTIVITY_LOG.value:
                assignment.instructions += "\n\nNote for depression: Focus especially on activities that provide a sense of accomplishment or connection with others. Start small - even brief activities count as success."
        
        if any('anxiety' in dx for dx in diagnosis_names):
            if assignment.assignment_type == AssignmentType.BEHAVIORAL_EXPERIMENT.value:
                assignment.instructions += "\n\nNote for anxiety: Start with lower-anxiety situations and gradually work up. Remember that some anxiety is normal and expected."
        
        # Adjust based on preferred therapy mode
        preferred_mode = patient.get('preferred_therapy_mode', 'CBT')
        if preferred_mode != assignment.therapy_modality and preferred_mode in ['CBT', 'DBT', 'ACT']:
            # Add brief explanation of why this assignment fits their treatment
            assignment.description += f"\n\nThis assignment complements your {preferred_mode} therapy by providing additional skills practice."
        
        return assignment
    
    def _save_assignment(self, assignment: HomeworkAssignment) -> int:
        """Save assignment to database"""
        
        assignment_id = self.db.execute_update('''
            INSERT INTO homework_assignments
            (patient_id, session_id, assignment_type, description, instructions,
             due_date, assigned_date, completed, completion_notes, 
             effectiveness_rating, difficulty_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assignment.patient_id,
            assignment.session_id,
            assignment.assignment_type,
            f"{assignment.title}: {assignment.description}",
            assignment.instructions,
            assignment.due_date,
            assignment.assigned_date,
            assignment.completed,
            assignment.completion_notes,
            assignment.effectiveness_rating,
            assignment.difficulty_rating
        ))
        
        return assignment_id
    
    def _create_assignment_reminders(self, assignment: HomeworkAssignment):
        """Create automated reminders for assignment"""
        
        if not assignment.due_date:
            return
        
        due_date = datetime.fromisoformat(assignment.due_date)
        
        # Create reminders at different intervals
        reminder_intervals = [
            (timedelta(days=1), "due_tomorrow", "Your homework assignment is due tomorrow!"),
            (timedelta(hours=6), "due_today", "Your homework assignment is due today!"),
            (timedelta(days=-1), "overdue", "Your homework assignment is overdue. Please complete when you can.")
        ]
        
        for interval, reminder_type, message in reminder_intervals:
            reminder_date = due_date - interval
            
            if reminder_date > datetime.now():  # Only create future reminders
                self.db.execute_update('''
                    INSERT INTO assignment_reminders
                    (assignment_id, reminder_date, reminder_type, message)
                    VALUES (?, ?, ?, ?)
                ''', (assignment.id, reminder_date.isoformat(), reminder_type, message))
    
    def update_assignment_progress(self, assignment_id: int, 
                                 progress_notes: str = "",
                                 time_spent: int = None,
                                 barriers: List[str] = None,
                                 insights: List[str] = None,
                                 completion_percentage: int = 0,
                                 mood_before: int = None,
                                 mood_after: int = None) -> Dict[str, Any]:
        """Update assignment progress with detailed tracking"""
        
        # Record progress entry
        progress_id = self.db.execute_update('''
            INSERT INTO assignment_progress
            (assignment_id, progress_notes, time_spent, barriers_encountered,
             insights_gained, completion_percentage, mood_before, mood_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assignment_id,
            progress_notes,
            time_spent,
            json.dumps(barriers or []),
            json.dumps(insights or []),
            completion_percentage,
            mood_before,
            mood_after
        ))
        
        # Update main assignment if completed
        if completion_percentage >= 100:
            self.complete_assignment(
                assignment_id,
                completion_notes=progress_notes,
                effectiveness_rating=None,
                difficulty_rating=None
            )
        
        result = {
            'progress_id': progress_id,
            'assignment_id': assignment_id,
            'completion_percentage': completion_percentage,
            'time_spent': time_spent,
            'barriers': barriers or [],
            'insights': insights or [],
            'mood_change': mood_after - mood_before if mood_before and mood_after else None
        }
        
        log_action(f"Assignment progress updated: {completion_percentage}%", 
                  "homework_system")
        
        return result
    
    def complete_assignment(self, assignment_id: int, 
                          completion_notes: str = "",
                          effectiveness_rating: int = None,
                          difficulty_rating: int = None,
                          time_spent: int = None) -> Dict[str, Any]:
        """Mark assignment as completed and gather feedback"""
        
        # Get assignment details
        assignments = self.db.execute_query(
            "SELECT * FROM homework_assignments WHERE id = ?", (assignment_id,)
        )
        
        if not assignments:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        assignment = assignments[0]
        
        # Update assignment completion
        self.db.execute_update('''
            UPDATE homework_assignments 
            SET completed = TRUE, completion_date = ?, completion_notes = ?,
                effectiveness_rating = ?, difficulty_rating = ?
            WHERE id = ?
        ''', (
            datetime.now().isoformat(),
            completion_notes,
            effectiveness_rating,
            difficulty_rating,
            assignment_id
        ))
        
        # Create final progress entry
        final_progress = self.update_assignment_progress(
            assignment_id,
            progress_notes=f"Assignment completed. {completion_notes}",
            time_spent=time_spent,
            completion_percentage=100
        )
        
        # Generate completion analysis
        completion_analysis = self._analyze_assignment_completion(assignment_id)
        
        result = {
            'assignment_id': assignment_id,
            'completion_date': datetime.now().isoformat(),
            'effectiveness_rating': effectiveness_rating,
            'difficulty_rating': difficulty_rating,
            'completion_notes': completion_notes,
            'analysis': completion_analysis
        }
        
        log_action(f"Assignment completed: {assignment['description'][:50]}", 
                  "homework_system", patient_id=assignment['patient_id'])
        
        return result
    
    def _analyze_assignment_completion(self, assignment_id: int) -> Dict[str, Any]:
        """Analyze assignment completion patterns and effectiveness"""
        
        # Get assignment and progress data
        assignment = self.db.execute_query(
            "SELECT * FROM homework_assignments WHERE id = ?", (assignment_id,)
        )[0]
        
        progress_entries = self.db.execute_query(
            "SELECT * FROM assignment_progress WHERE assignment_id = ? ORDER BY progress_date",
            (assignment_id,)
        )
        
        analysis = {
            'assignment_id': assignment_id,
            'assignment_type': assignment['assignment_type'],
            'total_time_spent': 0,
            'progress_entries_count': len(progress_entries),
            'common_barriers': [],
            'key_insights': [],
            'mood_impact': None,
            'completion_pattern': 'unknown'
        }
        
        # Analyze progress entries
        all_barriers = []
        all_insights = []
        mood_changes = []
        
        for entry in progress_entries:
            if entry.get('time_spent'):
                analysis['total_time_spent'] += entry['time_spent']
            
            if entry.get('barriers_encountered'):
                try:
                    barriers = json.loads(entry['barriers_encountered'])
                    all_barriers.extend(barriers)
                except json.JSONDecodeError:
                    pass
            
            if entry.get('insights_gained'):
                try:
                    insights = json.loads(entry['insights_gained'])
                    all_insights.extend(insights)
                except json.JSONDecodeError:
                    pass
            
            if entry.get('mood_before') and entry.get('mood_after'):
                mood_change = entry['mood_after'] - entry['mood_before']
                mood_changes.append(mood_change)
        
        # Summarize barriers and insights
        barrier_counts = {}
        for barrier in all_barriers:
            barrier_counts[barrier] = barrier_counts.get(barrier, 0) + 1
        
        analysis['common_barriers'] = [
            {'barrier': barrier, 'frequency': count}
            for barrier, count in sorted(barrier_counts.items(), key=lambda x: x[1], reverse=True)
        ][:3]  # Top 3 barriers
        
        analysis['key_insights'] = list(set(all_insights))[:5]  # Unique insights, max 5
        
        # Calculate mood impact
        if mood_changes:
            avg_mood_change = sum(mood_changes) / len(mood_changes)
            analysis['mood_impact'] = {
                'average_change': round(avg_mood_change, 1),
                'positive_sessions': len([x for x in mood_changes if x > 0]),
                'negative_sessions': len([x for x in mood_changes if x < 0]),
                'total_sessions': len(mood_changes)
            }
        
        # Determine completion pattern
        if len(progress_entries) <= 1:
            analysis['completion_pattern'] = 'completed_all_at_once'
        elif len(progress_entries) > 5:
            analysis['completion_pattern'] = 'gradual_consistent_progress'
        else:
            analysis['completion_pattern'] = 'moderate_progress_tracking'
        
        return analysis
    
    def get_patient_assignments(self, patient_id: int, 
                              status: str = None,
                              assignment_type: str = None,
                              days: int = None) -> List[Dict[str, Any]]:
        """Get patient's homework assignments with filtering options"""
        
        query = "SELECT * FROM homework_assignments WHERE patient_id = ?"
        params = [patient_id]
        
        if status == 'completed':
            query += " AND completed = TRUE"
        elif status == 'active':
            query += " AND completed = FALSE"
        
        if assignment_type:
            query += " AND assignment_type = ?"
            params.append(assignment_type)
        
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND assigned_date >= ?"
            params.append(cutoff_date)
        
        query += " ORDER BY assigned_date DESC"
        
        assignments = self.db.execute_query(query, tuple(params))
        
        # Enrich with progress data
        for assignment in assignments:
            progress_entries = self.db.execute_query(
                "SELECT * FROM assignment_progress WHERE assignment_id = ? ORDER BY progress_date DESC",
                (assignment['id'],)
            )
            assignment['progress_entries'] = progress_entries
            
            # Calculate completion percentage from latest entry
            if progress_entries:
                assignment['current_progress'] = progress_entries[0].get('completion_percentage', 0)
            else:
                assignment['current_progress'] = 100 if assignment['completed'] else 0
        
        return assignments
    
    def generate_homework_compliance_report(self, patient_id: int, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive homework compliance and effectiveness report"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get assignments in period
        assignments = self.get_patient_assignments(patient_id, days=days)
        
        report = {
            'patient_id': patient_id,
            'report_period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'compliance_metrics': {},
            'effectiveness_analysis': {},
            'assignment_breakdown': {},
            'recommendations': []
        }
        
        if not assignments:
            report['compliance_metrics'] = {'total_assignments': 0}
            report['recommendations'] = ['No homework assignments in this period']
            return report
        
        # Calculate compliance metrics
        total_assignments = len(assignments)
        completed_assignments = len([a for a in assignments if a['completed']])
        overdue_assignments = len([
            a for a in assignments 
            if not a['completed'] and a.get('due_date') and 
            datetime.fromisoformat(a['due_date']) < datetime.now()
        ])
        
        compliance_rate = (completed_assignments / total_assignments) * 100 if total_assignments > 0 else 0
        
        report['compliance_metrics'] = {
            'total_assignments': total_assignments,
            'completed_assignments': completed_assignments,
            'compliance_rate': round(compliance_rate, 1),
            'overdue_assignments': overdue_assignments,
            'active_assignments': total_assignments - completed_assignments,
            'average_completion_time': self._calculate_average_completion_time(assignments)
        }
        
        # Analyze effectiveness
        completed_with_ratings = [
            a for a in assignments 
            if a['completed'] and a.get('effectiveness_rating')
        ]
        
        if completed_with_ratings:
            avg_effectiveness = sum(a['effectiveness_rating'] for a in completed_with_ratings) / len(completed_with_ratings)
            
            report['effectiveness_analysis'] = {
                'assignments_with_ratings': len(completed_with_ratings),
                'average_effectiveness': round(avg_effectiveness, 1),
                'highly_effective': len([a for a in completed_with_ratings if a['effectiveness_rating'] >= 4]),
                'moderately_effective': len([a for a in completed_with_ratings if a['effectiveness_rating'] == 3]),
                'low_effectiveness': len([a for a in completed_with_ratings if a['effectiveness_rating'] <= 2])
            }
        
        # Assignment type breakdown
        type_breakdown = {}
        for assignment in assignments:
            a_type = assignment['assignment_type']
            if a_type not in type_breakdown:
                type_breakdown[a_type] = {
                    'total': 0,
                    'completed': 0,
                    'avg_effectiveness': 0,
                    'effectiveness_count': 0
                }
            
            type_breakdown[a_type]['total'] += 1
            if assignment['completed']:
                type_breakdown[a_type]['completed'] += 1
                
                if assignment.get('effectiveness_rating'):
                    type_breakdown[a_type]['avg_effectiveness'] += assignment['effectiveness_rating']
                    type_breakdown[a_type]['effectiveness_count'] += 1
        
        # Calculate average effectiveness per type
        for a_type, data in type_breakdown.items():
            if data['effectiveness_count'] > 0:
                data['avg_effectiveness'] = round(data['avg_effectiveness'] / data['effectiveness_count'], 1)
            else:
                data['avg_effectiveness'] = None
            
            data['completion_rate'] = round((data['completed'] / data['total']) * 100, 1) if data['total'] > 0 else 0
        
        report['assignment_breakdown'] = type_breakdown
        
        # Generate recommendations
        recommendations = []
        
        if compliance_rate < 60:
            recommendations.append("Consider reducing assignment complexity or frequency to improve compliance")
        elif compliance_rate > 90:
            recommendations.append("Excellent compliance! Consider gradually increasing assignment challenge")
        
        if overdue_assignments > 2:
            recommendations.append("Address barriers to assignment completion and consider deadline adjustments")
        
        # Type-specific recommendations
        for a_type, data in type_breakdown.items():
            if data['completion_rate'] < 50 and data['total'] >= 3:
                recommendations.append(f"Review {a_type.replace('_', ' ')} assignments - low completion rate")
            elif data['avg_effectiveness'] and data['avg_effectiveness'] >= 4:
                recommendations.append(f"{a_type.replace('_', ' ')} assignments are highly effective - consider using more")
        
        if not recommendations:
            recommendations.append("Continue current homework approach with regular monitoring")
        
        report['recommendations'] = recommendations
        
        return report
    
    def _calculate_average_completion_time(self, assignments: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate average time from assignment to completion"""
        
        completed_assignments = [a for a in assignments if a['completed'] and a.get('completion_date')]
        
        if not completed_assignments:
            return None
        
        completion_times = []
        for assignment in completed_assignments:
            assigned = datetime.fromisoformat(assignment['assigned_date'])
            completed = datetime.fromisoformat(assignment['completion_date'])
            days_to_complete = (completed - assigned).days
            completion_times.append(days_to_complete)
        
        return round(sum(completion_times) / len(completion_times), 1)
    
    def suggest_next_assignments(self, patient_id: int) -> Dict[str, Any]:
        """Suggest next homework assignments based on patient progress and needs"""
        
        # Get patient data
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        
        if not patient_data:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_data[0]
        
        # Get recent assignments and their effectiveness
        recent_assignments = self.get_patient_assignments(patient_id, days=30)
        
        # Get diagnoses and assessments
        diagnoses = self.db.execute_query(
            "SELECT diagnosis_name FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        recent_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 3",
            (patient_id,)
        )
        
        suggestions = {
            'patient_id': patient_id,
            'recommended_assignments': [],
            'assignment_modifications': [],
            'rationale': []
        }
        
        # Analyze recent assignment performance
        completed_types = set()
        effective_types = set()
        struggling_types = set()
        
        for assignment in recent_assignments:
            if assignment['completed']:
                completed_types.add(assignment['assignment_type'])
                
                if assignment.get('effectiveness_rating'):
                    if assignment['effectiveness_rating'] >= 4:
                        effective_types.add(assignment['assignment_type'])
                    elif assignment['effectiveness_rating'] <= 2:
                        struggling_types.add(assignment['assignment_type'])
        
        # Suggest based on diagnoses and missing assignment types
        diagnosis_names = [d['diagnosis_name'].lower() for d in diagnoses]
        
        # Depression-specific suggestions
        if any('depression' in dx for dx in diagnosis_names):
            if AssignmentType.ACTIVITY_LOG.value not in completed_types:
                suggestions['recommended_assignments'].append({
                    'template_id': 'cbt_activity_schedule',
                    'priority': 'high',
                    'rationale': 'Behavioral activation is highly effective for depression'
                })
            
            if AssignmentType.MOOD_TRACKING.value not in completed_types:
                suggestions['recommended_assignments'].append({
                    'template_id': 'mood_tracking',
                    'priority': 'medium',
                    'rationale': 'Mood tracking helps identify patterns and triggers'
                })
        
        # Anxiety-specific suggestions
        if any('anxiety' in dx for dx in diagnosis_names):
            if AssignmentType.THOUGHT_RECORD.value not in completed_types:
                suggestions['recommended_assignments'].append({
                    'template_id': 'cbt_thought_record',
                    'priority': 'high',
                    'rationale': 'Thought challenging is fundamental for anxiety management'
                })
            
            if AssignmentType.BEHAVIORAL_EXPERIMENT.value not in completed_types:
                # Only suggest if patient has completed basic assignments
                if len(completed_types) >= 2:
                    suggestions['recommended_assignments'].append({
                        'template_id': 'cbt_behavioral_experiment',
                        'priority': 'medium',
                        'rationale': 'Behavioral experiments help test anxious predictions'
                    })
        
        # PTSD-specific suggestions
        if any('ptsd' in dx for dx in diagnosis_names):
            if AssignmentType.MINDFULNESS_PRACTICE.value not in completed_types:
                suggestions['recommended_assignments'].append({
                    'template_id': 'dbt_mindfulness_practice',
                    'priority': 'high',
                    'rationale': 'Mindfulness is crucial for PTSD symptom management'
                })
        
        # Build on effective assignment types
        for effective_type in effective_types:
            if effective_type == AssignmentType.THOUGHT_RECORD.value:
                suggestions['recommended_assignments'].append({
                    'template_id': 'cbt_behavioral_experiment',
                    'priority': 'medium',
                    'rationale': 'Build on successful thought challenging with behavioral experiments'
                })
            elif effective_type == AssignmentType.MINDFULNESS_PRACTICE.value:
                suggestions['recommended_assignments'].append({
                    'template_id': 'dbt_distress_tolerance',
                    'priority': 'medium',
                    'rationale': 'Expand mindfulness skills with distress tolerance techniques'
                })
        
        # Address struggling assignment types
        for struggling_type in struggling_types:
            suggestions['assignment_modifications'].append({
                'assignment_type': struggling_type,
                'modification': 'reduce_difficulty',
                'suggestion': 'Consider breaking this assignment into smaller, more manageable parts'
            })
        
        # General progression suggestions
        if len(completed_types) >= 3 and patient.get('preferred_therapy_mode') == 'ACT':
            suggestions['recommended_assignments'].append({
                'template_id': 'act_values_clarification',
                'priority': 'medium',
                'rationale': 'Values work can provide motivation and direction for continued progress'
            })
        
        # Limit recommendations to avoid overwhelming
        suggestions['recommended_assignments'] = suggestions['recommended_assignments'][:3]
        
        return suggestions
    
    def create_assignment_reminder(self, assignment_id: int, reminder_date: str, 
                                 message: str = None) -> int:
        """Create custom assignment reminder"""
        
        if not message:
            message = "Don't forget to work on your homework assignment!"
        
        reminder_id = self.db.execute_update('''
            INSERT INTO assignment_reminders
            (assignment_id, reminder_date, reminder_type, message)
            VALUES (?, ?, ?, ?)
        ''', (assignment_id, reminder_date, 'custom', message))
        
        return reminder_id
    
    def get_due_assignments(self, patient_id: int = None, days_ahead: int = 3) -> List[Dict[str, Any]]:
        """Get assignments due within specified days"""
        
        future_date = datetime.now() + timedelta(days=days_ahead)
        
        query = "SELECT * FROM homework_assignments WHERE completed = FALSE AND due_date <= ?"
        params = [future_date.isoformat()]
        
        if patient_id:
            query += " AND patient_id = ?"
            params.append(patient_id)
        
        query += " ORDER BY due_date ASC"
        
        return self.db.execute_query(query, tuple(params))
    
    def get_assignment_statistics(self, patient_id: int = None) -> Dict[str, Any]:
        """Get comprehensive assignment statistics"""
        
        query_base = "SELECT * FROM homework_assignments"
        params = []
        
        if patient_id:
            query_base += " WHERE patient_id = ?"
            params.append(patient_id)
        
        all_assignments = self.db.execute_query(query_base, tuple(params))
        
        if not all_assignments:
            return {'total_assignments': 0}
        
        stats = {
            'total_assignments': len(all_assignments),
            'completed_assignments': len([a for a in all_assignments if a['completed']]),
            'completion_rate': 0,
            'average_effectiveness': 0,
            'average_difficulty': 0,
            'assignment_type_distribution': {},
            'therapy_modality_distribution': {},
            'monthly_trends': {}
        }
        
        # Calculate completion rate
        if stats['total_assignments'] > 0:
            stats['completion_rate'] = round((stats['completed_assignments'] / stats['total_assignments']) * 100, 1)
        
        # Calculate averages for completed assignments with ratings
        completed_with_ratings = [
            a for a in all_assignments 
            if a['completed'] and a.get('effectiveness_rating') and a.get('difficulty_rating')
        ]
        
        if completed_with_ratings:
            stats['average_effectiveness'] = round(
                sum(a['effectiveness_rating'] for a in completed_with_ratings) / len(completed_with_ratings), 1
            )
            stats['average_difficulty'] = round(
                sum(a['difficulty_rating'] for a in completed_with_ratings) / len(completed_with_ratings), 1
            )
        
        # Assignment type distribution
        for assignment in all_assignments:
            a_type = assignment['assignment_type']
            if a_type not in stats['assignment_type_distribution']:
                stats['assignment_type_distribution'][a_type] = 0
            stats['assignment_type_distribution'][a_type] += 1
        
        # Monthly trends (last 6 months)
        for i in range(6):
            month_start = datetime.now() - timedelta(days=30 * (i + 1))
            month_end = datetime.now() - timedelta(days=30 * i)
            
            month_assignments = [
                a for a in all_assignments
                if month_start.isoformat() <= a['assigned_date'] <= month_end.isoformat()
            ]
            
            month_key = month_start.strftime('%Y-%m')
            stats['monthly_trends'][month_key] = {
                'assigned': len(month_assignments),
                'completed': len([a for a in month_assignments if a['completed']])
            }
        
        return stats
    
    def export_homework_data(self, patient_id: int) -> Dict[str, Any]:
        """Export comprehensive homework data for patient"""
        
        assignments = self.get_patient_assignments(patient_id)
        
        # Get all progress entries
        all_progress = []
        for assignment in assignments:
            progress_entries = self.db.execute_query(
                "SELECT * FROM assignment_progress WHERE assignment_id = ?",
                (assignment['id'],)
            )
            all_progress.extend(progress_entries)
        
        export_data = {
            'patient_id': patient_id,
            'export_date': datetime.now().isoformat(),
            'total_assignments': len(assignments),
            'assignments': assignments,
            'progress_entries': all_progress,
            'statistics': self.get_assignment_statistics(patient_id),
            'compliance_report': self.generate_homework_compliance_report(patient_id, days=90)
        }
        
        return export_data


# Utility functions
def create_quick_assignment(db: DatabaseManager, patient_id: int, 
                          assignment_type: str, description: str,
                          due_days: int = 7) -> Dict[str, Any]:
    """Quick assignment creation helper"""
    
    homework_system = HomeworkSystem(db)
    
    custom_params = {
        'assignment_type': assignment_type,
        'title': f"Custom {assignment_type.replace('_', ' ').title()}",
        'description': description,
        'instructions': f"Complete the following: {description}",
        'due_date': (datetime.now() + timedelta(days=due_days)).isoformat()
    }
    
    assignment = homework_system.create_assignment(
        patient_id=patient_id,
        custom_params=custom_params
    )
    
    return {
        'assignment_id': assignment.id,
        'title': assignment.title,
        'due_date': assignment.due_date,
        'created': True
    }


def get_homework_dashboard_data(db: DatabaseManager, patient_id: int) -> Dict[str, Any]:
    """Generate homework dashboard data"""
    
    homework_system = HomeworkSystem(db)
    
    # Get active assignments
    active_assignments = homework_system.get_patient_assignments(patient_id, status='active')
    
    # Get due soon assignments
    due_soon = homework_system.get_due_assignments(patient_id, days_ahead=3)
    
    # Get compliance report
    compliance = homework_system.generate_homework_compliance_report(patient_id, days=30)
    
    dashboard = {
        'patient_id': patient_id,
        'active_assignments': len(active_assignments),
        'due_soon': len(due_soon),
        'compliance_rate': compliance['compliance_metrics'].get('compliance_rate', 0),
        'recent_assignments': active_assignments[:5],
        'upcoming_due_dates': [
            {
                'assignment_id': a['id'],
                'title': a['description'].split(':')[0] if ':' in a['description'] else a['description'][:30],
                'due_date': a['due_date'],
                'days_until_due': (datetime.fromisoformat(a['due_date']) - datetime.now()).days if a.get('due_date') else None
            }
            for a in due_soon
        ]
    }
    
    return dashboard


# Test function
def main():
    """Test homework system functionality"""
    from database import DatabaseManager
    
    print("Testing Homework System...")
    
    db = DatabaseManager(":memory:")
    homework_system = HomeworkSystem(db)
    
    # Create test patient
    patient_id = db.execute_update(
        "INSERT INTO patients (name, preferred_therapy_mode) VALUES (?, ?)",
        ("Test Patient", "CBT")
    )
    
    # Add diagnosis for better assignment suggestions
    db.execute_update(
        "INSERT INTO diagnoses (patient_id, diagnosis_name, status) VALUES (?, ?, ?)",
        (patient_id, "Major Depressive Disorder", "active")
    )
    
    print(f"Created test patient ID: {patient_id}")
    
    # Test assignment creation from template
    print("\n1. Testing assignment creation from template...")
    assignment = homework_system.create_assignment(
        patient_id, 
        template_id='cbt_thought_record'
    )
    print(f"Created assignment: {assignment.title}")
    print(f"Assignment ID: {assignment.id}")
    print(f"Due date: {assignment.due_date}")
    print(f"Estimated time: {assignment.estimated_time} minutes")
    
    # Test progress update
    print("\n2. Testing progress update...")
    progress_result = homework_system.update_assignment_progress(
        assignment.id,
        progress_notes="Completed 3 thought records so far",
        completion_percentage=60,
        barriers=["Difficult to remember during emotional moments"],
        insights=["Noticed I catastrophize about work situations"],
        mood_before=4,
        mood_after=6
    )
    print(f"Progress updated: {progress_result['completion_percentage']}%")
    print(f"Mood change: {progress_result['mood_change']}")
    
    # Test assignment completion
    print("\n3. Testing assignment completion...")
    completion_result = homework_system.complete_assignment(
        assignment.id,
        completion_notes="Completed all thought records. Very helpful!",
        effectiveness_rating=4,
        difficulty_rating=2
    )
    print(f"Assignment completed on: {completion_result['completion_date']}")
    print(f"Effectiveness rating: {completion_result['effectiveness_rating']}/5")
    
    # Test compliance report
    print("\n4. Testing compliance report...")
    compliance_report = homework_system.generate_homework_compliance_report(patient_id, days=30)
    print(f"Compliance rate: {compliance_report['compliance_metrics']['compliance_rate']}%")
    print(f"Total assignments: {compliance_report['compliance_metrics']['total_assignments']}")
    
    # Test assignment suggestions
    print("\n5. Testing assignment suggestions...")
    suggestions = homework_system.suggest_next_assignments(patient_id)
    print(f"Recommended assignments: {len(suggestions['recommended_assignments'])}")
    for rec in suggestions['recommended_assignments']:
        print(f"  - {rec['template_id']} (Priority: {rec['priority']})")
    
    # Test dashboard data
    print("\n6. Testing dashboard data...")
    dashboard = get_homework_dashboard_data(db, patient_id)
    print(f"Active assignments: {dashboard['active_assignments']}")
    print(f"Due soon: {dashboard['due_soon']}")
    print(f"Compliance rate: {dashboard['compliance_rate']}%")
    
    print("\nHomework system testing completed successfully!")


if __name__ == "__main__":
    main()  