#!/usr/bin/env python3
"""
AI Therapy System - Goal Management System
SMART goal setting, progress tracking, and achievement monitoring for therapeutic treatment
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from database import DatabaseManager
from models import TreatmentGoal
from utils import log_action


class GoalType(Enum):
    """Types of treatment goals"""
    SYMPTOM = "symptom"
    FUNCTIONAL = "functional"
    BEHAVIORAL = "behavioral"
    INTERPERSONAL = "interpersonal"
    COGNITIVE = "cognitive"


class GoalStatus(Enum):
    """Goal status options"""
    ACTIVE = "active"
    ACHIEVED = "achieved"
    MODIFIED = "modified"
    DISCONTINUED = "discontinued"
    ON_HOLD = "on_hold"


class PriorityLevel(Enum):
    """Goal priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class GoalMilestone:
    """Individual milestone within a goal"""
    id: Optional[int] = None
    goal_id: int = 0
    milestone_description: str = ""
    target_date: str = ""
    completed: bool = False
    completion_date: Optional[str] = None
    notes: str = ""


@dataclass
class SMARTGoal:
    """SMART goal structure with comprehensive tracking"""
    id: Optional[int] = None
    patient_id: int = 0
    goal_type: str = GoalType.SYMPTOM.value
    title: str = ""
    specific_description: str = ""
    measurable_criteria: str = ""
    achievable_rationale: str = ""
    relevant_connection: str = ""
    time_bound_deadline: str = ""
    current_progress: int = 0  # 0-100%
    status: str = GoalStatus.ACTIVE.value
    priority_level: int = PriorityLevel.MEDIUM.value
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    target_date: str = ""
    milestones: List[GoalMilestone] = field(default_factory=list)
    barriers_identified: List[str] = field(default_factory=list)
    strategies_planned: List[str] = field(default_factory=list)
    support_needed: List[str] = field(default_factory=list)
    progress_notes: List[Dict[str, str]] = field(default_factory=list)


class GoalManager:
    """Manages treatment goals, progress tracking, and achievement monitoring"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.goal_templates = self._load_goal_templates()
        self._init_goal_tables()
    
    def _init_goal_tables(self):
        """Initialize goal-related database tables"""
        with self.db.get_connection() as conn:
            # Goal milestones table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS goal_milestones (
                    id INTEGER PRIMARY KEY,
                    goal_id INTEGER NOT NULL,
                    milestone_description TEXT NOT NULL,
                    target_date TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    completion_date TEXT,
                    notes TEXT,
                    created_date TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (goal_id) REFERENCES treatment_goals(id) ON DELETE CASCADE
                )
            ''')
            
            # Goal progress tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS goal_progress_tracking (
                    id INTEGER PRIMARY KEY,
                    goal_id INTEGER NOT NULL,
                    progress_date TEXT NOT NULL DEFAULT (datetime('now')),
                    progress_percentage INTEGER CHECK (progress_percentage BETWEEN 0 AND 100),
                    progress_notes TEXT,
                    barriers_encountered TEXT DEFAULT '[]',
                    strategies_used TEXT DEFAULT '[]',
                    next_steps TEXT,
                    recorded_by TEXT DEFAULT 'patient',
                    FOREIGN KEY (goal_id) REFERENCES treatment_goals(id) ON DELETE CASCADE
                )
            ''')
            
            # Goal templates table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS goal_templates (
                    id INTEGER PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    goal_type TEXT NOT NULL,
                    diagnosis_tags TEXT DEFAULT '[]',
                    template_description TEXT NOT NULL,
                    measurement_criteria TEXT NOT NULL,
                    typical_timeframe TEXT,
                    common_milestones TEXT DEFAULT '[]',
                    suggested_strategies TEXT DEFAULT '[]',
                    active BOOLEAN DEFAULT TRUE,
                    created_date TEXT NOT NULL DEFAULT (datetime('now'))
                )
            ''')
            
            conn.commit()
    def create_goal(self, patient_id: int, goal_type: str, description: str, 
               target_date: str, measurement_criteria: str) -> int:
        """Create a new treatment goal"""
        
        goal_id = self.db.execute_update('''
            INSERT INTO treatment_goals 
            (patient_id, goal_type, goal_description, target_date, 
            measurement_criteria, current_progress, status, created_date, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, goal_type, description, target_date,
            measurement_criteria, 0, 'active',
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        
        return goal_id

    def update_goal_progress(self, goal_id: int, progress: int, notes: str = None) -> bool:
        """Update goal progress"""
        update_data = {
            'current_progress': progress,
            'last_updated': datetime.now().isoformat()
        }
        
        if notes:
            # Get existing notes
            existing = self.db.execute_query("SELECT notes FROM treatment_goals WHERE id = ?", (goal_id,))
            if existing:
                old_notes = existing[0].get('notes', '') or ''
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                new_notes = f"{old_notes}\n[{timestamp}] {notes}".strip()
                update_data['notes'] = new_notes
        
        # Automatically mark as achieved if 100% progress
        if progress >= 100:
            update_data['status'] = 'achieved'
        
        rows_updated = self.db.execute_update('''
            UPDATE treatment_goals 
            SET current_progress = ?, last_updated = ?, notes = ?, status = ?
            WHERE id = ?
        ''', (
            update_data['current_progress'], 
            update_data['last_updated'],
            update_data.get('notes'),
            update_data.get('status', 'active'),
            goal_id
        ))
        
        return rows_updated > 0

    def get_patient_goals(self, patient_id: int, status: str = None) -> List[Dict]:
        """Get all goals for a patient"""
        if status:
            return self.db.execute_query(
                "SELECT * FROM treatment_goals WHERE patient_id = ? AND status = ? ORDER BY created_date DESC",
                (patient_id, status)
            )
        else:
            return self.db.execute_query(
                "SELECT * FROM treatment_goals WHERE patient_id = ? ORDER BY created_date DESC",
                (patient_id,)
            )

    def calculate_goal_progress_summary(self, patient_id: int) -> Dict[str, Any]:
        """Calculate overall goal progress for a patient"""
        goals = self.get_patient_goals(patient_id, 'active')
        
        if not goals:
            return {'total_goals': 0, 'avg_progress': 0, 'goals_achieved': 0}
        
        total_progress = sum(goal['current_progress'] for goal in goals)
        avg_progress = total_progress / len(goals)
        
        all_goals = self.get_patient_goals(patient_id)
        achieved_goals = len([g for g in all_goals if g['status'] == 'achieved'])
        
        return {
            'total_goals': len(goals),
            'avg_progress': round(avg_progress, 1),
            'goals_achieved': achieved_goals,
            'active_goals': len(goals)
        }
    def _load_goal_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load pre-defined goal templates"""
        templates = {
            'depression_symptom_reduction': {
                'goal_type': GoalType.SYMPTOM.value,
                'title': 'Reduce Depression Symptoms',
                'description': 'Decrease depressive symptoms to mild or minimal range',
                'measurement': 'PHQ-9 score ≤ 9 for two consecutive assessments',
                'timeframe': '12 weeks',
                'milestones': [
                    'Achieve PHQ-9 score ≤ 14 (moderate range)',
                    'Achieve PHQ-9 score ≤ 9 (mild range)',
                    'Maintain mild range for 4 weeks'
                ],
                'strategies': [
                    'Daily mood monitoring',
                    'Cognitive restructuring practice',
                    'Behavioral activation activities',
                    'Regular therapy attendance'
                ]
            },
            
            'anxiety_management': {
                'goal_type': GoalType.SYMPTOM.value,
                'title': 'Manage Anxiety Symptoms',
                'description': 'Develop effective anxiety management skills',
                'measurement': 'GAD-7 score ≤ 9 and use of coping skills in anxiety-provoking situations',
                'timeframe': '10 weeks',
                'milestones': [
                    'Learn and practice 3 anxiety management techniques',
                    'Use coping skills in 50% of anxiety situations',
                    'Use coping skills in 80% of anxiety situations'
                ],
                'strategies': [
                    'Deep breathing exercises',
                    'Progressive muscle relaxation',
                    'Exposure exercises',
                    'Cognitive restructuring'
                ]
            },
            
            'social_functioning': {
                'goal_type': GoalType.FUNCTIONAL.value,
                'title': 'Improve Social Functioning',
                'description': 'Increase quality and frequency of social interactions',
                'measurement': 'Engage in meaningful social activities 2-3 times per week',
                'timeframe': '8 weeks',
                'milestones': [
                    'Initiate 1 social interaction per week',
                    'Participate in 2 social activities weekly',
                    'Maintain 3 regular social activities weekly'
                ],
                'strategies': [
                    'Social skills practice',
                    'Gradual exposure to social situations',
                    'Activity scheduling',
                    'Communication skills training'
                ]
            },
            
            'sleep_improvement': {
                'goal_type': GoalType.BEHAVIORAL.value,
                'title': 'Improve Sleep Quality',
                'description': 'Establish healthy sleep patterns and improve sleep quality',
                'measurement': 'Sleep 7-8 hours per night with ≤ 2 night wakings, 5 nights per week',
                'timeframe': '6 weeks',
                'milestones': [
                    'Establish consistent bedtime routine',
                    'Fall asleep within 30 minutes most nights',
                    'Sleep through night 5+ nights per week'
                ],
                'strategies': [
                    'Sleep hygiene education',
                    'Relaxation techniques before bed',
                    'Stimulus control techniques',
                    'Sleep diary monitoring'
                ]
            },
            
            'emotional_regulation': {
                'goal_type': GoalType.COGNITIVE.value,
                'title': 'Improve Emotional Regulation',
                'description': 'Develop skills to identify, understand, and manage emotions effectively',
                'measurement': 'Use emotion regulation skills in 80% of distressing situations',
                'timeframe': '12 weeks',
                'milestones': [
                    'Accurately identify emotions in daily situations',
                    'Use 3 different emotion regulation techniques',
                    'Effectively manage intense emotions without destructive behaviors'
                ],
                'strategies': [
                    'Emotion identification practice',
                    'Mindfulness meditation',
                    'Distress tolerance skills',
                    'Opposite action technique'
                ]
            },
            
            'relationship_skills': {
                'goal_type': GoalType.INTERPERSONAL.value,
                'title': 'Enhance Relationship Skills',
                'description': 'Improve communication and relationship maintenance skills',
                'measurement': 'Successfully navigate conflicts using healthy communication 80% of the time',
                'timeframe': '10 weeks',
                'milestones': [
                    'Learn and practice assertive communication',
                    'Set appropriate boundaries in relationships',
                    'Resolve conflicts constructively'
                ],
                'strategies': [
                    'Communication skills training',
                    'Boundary setting practice',
                    'Conflict resolution techniques',
                    'Empathy building exercises'
                ]
            }
        }
        
        return templates
    
    def create_smart_goal(self, patient_id: int, **kwargs) -> SMARTGoal:
        """Create a comprehensive SMART goal"""
        
        goal = SMARTGoal(patient_id=patient_id)
        
        # Use template if specified
        if 'template' in kwargs and kwargs['template'] in self.goal_templates:
            template = self.goal_templates[kwargs['template']]
            goal.goal_type = template['goal_type']
            goal.title = template['title']
            goal.specific_description = template['description']
            goal.measurable_criteria = template['measurement']
            goal.time_bound_deadline = template['timeframe']
            
            # Create milestones from template
            for milestone_desc in template['milestones']:
                milestone = GoalMilestone(
                    milestone_description=milestone_desc,
                    target_date=self._calculate_milestone_date(goal.created_date, template['timeframe'], len(template['milestones']))
                )
                goal.milestones.append(milestone)
            
            goal.strategies_planned = template['strategies']
        
        # Override with provided parameters
        if 'goal_type' in kwargs:
            goal.goal_type = kwargs['goal_type']
        if 'title' in kwargs:
            goal.title = kwargs['title']
        if 'specific_description' in kwargs:
            goal.specific_description = kwargs['specific_description']
        if 'measurable_criteria' in kwargs:
            goal.measurable_criteria = kwargs['measurable_criteria']
        if 'target_date' in kwargs:
            goal.target_date = kwargs['target_date']
        else:
            goal.target_date = self._calculate_target_date(kwargs.get('timeframe', '12 weeks'))
        
        # Validate SMART criteria
        validation = self._validate_smart_criteria(goal)
        if not validation['valid']:
            raise ValueError(f"Goal does not meet SMART criteria: {', '.join(validation['issues'])}")
        
        # Set achievable rationale
        goal.achievable_rationale = kwargs.get('achievable_rationale', 
            "Goal is achievable with consistent effort and appropriate support")
        
        # Set relevant connection
        goal.relevant_connection = kwargs.get('relevant_connection',
            self._generate_relevance_statement(patient_id, goal.goal_type))
        
        # Set priority level
        goal.priority_level = kwargs.get('priority_level', PriorityLevel.MEDIUM.value)
        
        # Save to database
        goal_id = self._save_smart_goal(goal)
        goal.id = goal_id
        
        log_action(f"SMART goal created: {goal.title}", "goal_manager", patient_id=patient_id)
        
        return goal
    
    def _validate_smart_criteria(self, goal: SMARTGoal) -> Dict[str, Any]:
        """Validate that goal meets SMART criteria"""
        validation = {
            'valid': True,
            'issues': []
        }
        
        # Specific: Goal should be clear and specific
        if not goal.specific_description or len(goal.specific_description.strip()) < 20:
            validation['valid'] = False
            validation['issues'].append("Goal description is not specific enough")
        
        # Measurable: Should have clear measurement criteria
        if not goal.measurable_criteria or len(goal.measurable_criteria.strip()) < 10:
            validation['valid'] = False
            validation['issues'].append("Goal lacks measurable criteria")
        
        # Achievable: Should have rationale for achievability (optional check)
        # This is validated during creation process
        
        # Relevant: Should be connected to patient's treatment
        if not goal.relevant_connection or len(goal.relevant_connection.strip()) < 10:
            validation['valid'] = False
            validation['issues'].append("Goal relevance not clearly established")
        
        # Time-bound: Should have a deadline
        if not goal.target_date and not goal.time_bound_deadline:
            validation['valid'] = False
            validation['issues'].append("Goal lacks time-bound deadline")
        
        return validation
    
    def _calculate_target_date(self, timeframe: str) -> str:
        """Calculate target date from timeframe string"""
        try:
            # Extract number and unit from timeframe (e.g., "12 weeks", "3 months")
            match = re.search(r'(\d+)\s*(week|month|day)', timeframe.lower())
            if not match:
                # Default to 12 weeks
                return (datetime.now() + timedelta(weeks=12)).isoformat()
            
            number = int(match.group(1))
            unit = match.group(2)
            
            if unit.startswith('week'):
                target_date = datetime.now() + timedelta(weeks=number)
            elif unit.startswith('month'):
                target_date = datetime.now() + timedelta(weeks=number * 4)  # Approximate
            elif unit.startswith('day'):
                target_date = datetime.now() + timedelta(days=number)
            else:
                target_date = datetime.now() + timedelta(weeks=12)  # Default
            
            return target_date.isoformat()
            
        except Exception:
            # Default to 12 weeks if parsing fails
            return (datetime.now() + timedelta(weeks=12)).isoformat()
    
    def _calculate_milestone_date(self, start_date: str, total_timeframe: str, milestone_index: int, total_milestones: int) -> str:
        """Calculate target date for individual milestones"""
        try:
            start = datetime.fromisoformat(start_date)
            target = datetime.fromisoformat(self._calculate_target_date(total_timeframe))
            
            # Distribute milestones evenly across timeframe
            total_days = (target - start).days
            milestone_interval = total_days / (total_milestones + 1)  # +1 to avoid milestone on final date
            
            milestone_date = start + timedelta(days=int(milestone_interval * (milestone_index + 1)))
            return milestone_date.isoformat()
            
        except Exception:
            # Default to 4 weeks from start
            start = datetime.fromisoformat(start_date)
            return (start + timedelta(weeks=4)).isoformat()
    
    def _generate_relevance_statement(self, patient_id: int, goal_type: str) -> str:
        """Generate relevance statement based on patient data"""
        
        # Get patient diagnoses
        diagnoses = self.db.execute_query(
            "SELECT diagnosis_name FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        diagnosis_names = [d['diagnosis_name'].lower() for d in diagnoses]
        
        relevance_templates = {
            GoalType.SYMPTOM.value: "This goal directly addresses core symptoms that impact daily functioning and quality of life",
            GoalType.FUNCTIONAL.value: "Improving functional capacity is essential for overall well-being and treatment success",
            GoalType.BEHAVIORAL.value: "Behavioral changes support symptom reduction and improved coping strategies",
            GoalType.INTERPERSONAL.value: "Healthy relationships are crucial for emotional support and recovery",
            GoalType.COGNITIVE.value: "Developing cognitive skills enhances emotional regulation and problem-solving abilities"
        }
        
        base_relevance = relevance_templates.get(goal_type, "This goal supports overall treatment objectives")
        
        # Add diagnosis-specific relevance
        if any('depression' in dx for dx in diagnosis_names):
            base_relevance += ", particularly important for managing depressive symptoms"
        elif any('anxiety' in dx for dx in diagnosis_names):
            base_relevance += ", especially relevant for anxiety management"
        elif any('ptsd' in dx for dx in diagnosis_names):
            base_relevance += ", critical for trauma recovery and healing"
        
        return base_relevance
    
    def _save_smart_goal(self, goal: SMARTGoal) -> int:
        """Save SMART goal to database"""
        
        # Save main goal
        goal_id = self.db.execute_update('''
            INSERT INTO treatment_goals
            (patient_id, goal_type, goal_description, target_date, current_progress,
             measurement_criteria, status, created_date, last_updated, priority_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            goal.patient_id,
            goal.goal_type,
            f"{goal.title}: {goal.specific_description}",
            goal.target_date,
            goal.current_progress,
            goal.measurable_criteria,
            goal.status,
            goal.created_date,
            goal.last_updated,
            goal.priority_level
        ))
        
        # Save milestones
        for milestone in goal.milestones:
            milestone.goal_id = goal_id
            self.db.execute_update('''
                INSERT INTO goal_milestones
                (goal_id, milestone_description, target_date, notes)
                VALUES (?, ?, ?, ?)
            ''', (
                goal_id,
                milestone.milestone_description,
                milestone.target_date,
                milestone.notes
            ))
        
        return goal_id
    
    def update_goal_progress(self, goal_id: int, progress_percentage: int, 
                           notes: str = "", barriers: List[str] = None, 
                           strategies: List[str] = None, next_steps: str = "") -> Dict[str, Any]:
        """Update goal progress with comprehensive tracking"""
        
        if not 0 <= progress_percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        
        # Get current goal
        goals = self.db.execute_query(
            "SELECT * FROM treatment_goals WHERE id = ?", (goal_id,)
        )
        
        if not goals:
            raise ValueError(f"Goal {goal_id} not found")
        
        goal = goals[0]
        previous_progress = goal['current_progress']
        
        # Update main goal
        self.db.execute_update('''
            UPDATE treatment_goals 
            SET current_progress = ?, last_updated = ?
            WHERE id = ?
        ''', (progress_percentage, datetime.now().isoformat(), goal_id))
        
        # Record progress tracking entry
        tracking_id = self.db.execute_update('''
            INSERT INTO goal_progress_tracking
            (goal_id, progress_percentage, progress_notes, barriers_encountered,
             strategies_used, next_steps, recorded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            goal_id,
            progress_percentage,
            notes,
            json.dumps(barriers or []),
            json.dumps(strategies or []),
            next_steps,
            'system'
        ))
        
        # Check for goal completion
        if progress_percentage >= 100:
            self._mark_goal_achieved(goal_id)
        
        # Check milestones
        milestone_updates = self._check_milestone_completion(goal_id, progress_percentage)
        
        # Calculate progress velocity
        progress_change = progress_percentage - previous_progress
        
        update_result = {
            'goal_id': goal_id,
            'previous_progress': previous_progress,
            'new_progress': progress_percentage,
            'progress_change': progress_change,
            'tracking_id': tracking_id,
            'milestones_updated': milestone_updates,
            'goal_completed': progress_percentage >= 100
        }
        
        log_action(f"Goal progress updated: {progress_change:+d}% to {progress_percentage}%", 
                  "goal_manager", patient_id=goal['patient_id'])
        
        return update_result
    
    def _mark_goal_achieved(self, goal_id: int):
        """Mark goal as achieved and handle completion tasks"""
        
        self.db.execute_update('''
            UPDATE treatment_goals 
            SET status = ?, last_updated = ?
            WHERE id = ?
        ''', (GoalStatus.ACHIEVED.value, datetime.now().isoformat(), goal_id))
        
        # Mark all milestones as completed
        self.db.execute_update('''
            UPDATE goal_milestones 
            SET completed = TRUE, completion_date = ?
            WHERE goal_id = ? AND completed = FALSE
        ''', (datetime.now().isoformat(), goal_id))
        
        log_action(f"Goal {goal_id} marked as achieved", "goal_manager")
    
    def _check_milestone_completion(self, goal_id: int, current_progress: int) -> List[Dict[str, Any]]:
        """Check and update milestone completion based on progress"""
        
        # Get all milestones for this goal
        milestones = self.db.execute_query(
            "SELECT * FROM goal_milestones WHERE goal_id = ? ORDER BY target_date",
            (goal_id,)
        )
        
        updates = []
        
        # Simple logic: complete milestones based on progress percentage
        # Each milestone represents a portion of the total goal
        milestone_threshold = 100 / len(milestones) if milestones else 100
        
        for i, milestone in enumerate(milestones):
            expected_progress = milestone_threshold * (i + 1)
            
            if current_progress >= expected_progress and not milestone['completed']:
                # Mark milestone as completed
                self.db.execute_update('''
                    UPDATE goal_milestones 
                    SET completed = TRUE, completion_date = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), milestone['id']))
                
                updates.append({
                    'milestone_id': milestone['id'],
                    'description': milestone['milestone_description'],
                    'completed': True
                })
                
                log_action(f"Milestone completed: {milestone['milestone_description'][:50]}...", 
                          "goal_manager")
        
        return updates
    
    def get_patient_goals(self, patient_id: int, status: str = None, 
                         goal_type: str = None) -> List[Dict[str, Any]]:
        """Get patient's treatment goals with filtering options"""
        
        query = "SELECT * FROM treatment_goals WHERE patient_id = ?"
        params = [patient_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if goal_type:
            query += " AND goal_type = ?"
            params.append(goal_type)
        
        query += " ORDER BY priority_level DESC, created_date DESC"
        
        goals = self.db.execute_query(query, tuple(params))
        
        # Enrich with milestone data
        for goal in goals:
            milestones = self.db.execute_query(
                "SELECT * FROM goal_milestones WHERE goal_id = ? ORDER BY target_date",
                (goal['id'],)
            )
            goal['milestones'] = milestones
            
            # Get recent progress entries
            recent_progress = self.db.execute_query(
                "SELECT * FROM goal_progress_tracking WHERE goal_id = ? ORDER BY progress_date DESC LIMIT 3",
                (goal['id'],)
            )
            goal['recent_progress'] = recent_progress
        
        return goals
    
    def generate_goal_progress_report(self, patient_id: int, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive goal progress report"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all goals
        all_goals = self.get_patient_goals(patient_id)
        
        report = {
            'patient_id': patient_id,
            'report_period': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'summary_stats': {},
            'goal_progress': [],
            'achievements': [],
            'recommendations': []
        }
        
        # Calculate summary statistics
        active_goals = [g for g in all_goals if g['status'] == GoalStatus.ACTIVE.value]
        achieved_goals = [g for g in all_goals if g['status'] == GoalStatus.ACHIEVED.value]
        
        if active_goals:
            avg_progress = sum(g['current_progress'] for g in active_goals) / len(active_goals)
        else:
            avg_progress = 0
        
        report['summary_stats'] = {
            'total_goals': len(all_goals),
            'active_goals': len(active_goals),
            'achieved_goals': len(achieved_goals),
            'average_progress': round(avg_progress, 1),
            'goals_on_track': len([g for g in active_goals if g['current_progress'] >= 60]),
            'goals_needing_attention': len([g for g in active_goals if g['current_progress'] < 30])
        }
        
        # Analyze each goal's progress
        for goal in all_goals:
            # Get progress over the reporting period
            progress_entries = self.db.execute_query(
                "SELECT * FROM goal_progress_tracking WHERE goal_id = ? AND progress_date >= ? ORDER BY progress_date",
                (goal['id'], start_date.isoformat())
            )
            
            if progress_entries:
                first_progress = progress_entries[0]['progress_percentage']
                last_progress = progress_entries[-1]['progress_percentage']
                progress_change = last_progress - first_progress
            else:
                progress_change = 0
                first_progress = goal['current_progress']
                last_progress = goal['current_progress']
            
            goal_analysis = {
                'goal_id': goal['id'],
                'goal_title': goal['goal_description'].split(':')[0] if ':' in goal['goal_description'] else goal['goal_description'][:50],
                'goal_type': goal['goal_type'],
                'current_progress': goal['current_progress'],
                'progress_change': progress_change,
                'status': goal['status'],
                'priority': goal['priority_level'],
                'target_date': goal.get('target_date', ''),
                'milestones_completed': len([m for m in goal.get('milestones', []) if m['completed']]),
                'total_milestones': len(goal.get('milestones', [])),
                'trend': 'improving' if progress_change > 5 else 'stable' if progress_change >= -5 else 'declining'
            }
            
            report['goal_progress'].append(goal_analysis)
        
        # Identify achievements
        recent_achievements = []
        
        # Recently completed goals
        for goal in achieved_goals:
            if goal.get('last_updated'):
                last_updated = datetime.fromisoformat(goal['last_updated'])
                if last_updated > start_date:
                    recent_achievements.append({
                        'type': 'goal_completion',
                        'description': f"Completed goal: {goal['goal_description'].split(':')[0]}",
                        'date': goal['last_updated']
                    })
        
        # Recently completed milestones
        for goal in all_goals:
            for milestone in goal.get('milestones', []):
                if milestone['completed'] and milestone.get('completion_date'):
                    completion_date = datetime.fromisoformat(milestone['completion_date'])
                    if completion_date > start_date:
                        recent_achievements.append({
                            'type': 'milestone_completion',
                            'description': f"Milestone: {milestone['milestone_description']}",
                            'date': milestone['completion_date']
                        })
        
        report['achievements'] = sorted(recent_achievements, key=lambda x: x['date'], reverse=True)
        
        # Generate recommendations
        recommendations = []
        
        if report['summary_stats']['goals_needing_attention'] > 0:
            recommendations.append(
                f"Review and potentially modify {report['summary_stats']['goals_needing_attention']} goals with limited progress"
            )
        
        if report['summary_stats']['average_progress'] < 40:
            recommendations.append("Consider reassessing goal achievability and breaking down large goals into smaller steps")
        
        declining_goals = [g for g in report['goal_progress'] if g['trend'] == 'declining']
        if declining_goals:
            recommendations.append(f"Address barriers for {len(declining_goals)} goals showing declining progress")
        
        if report['summary_stats']['achieved_goals'] > 0:
            recommendations.append("Celebrate recent achievements and set new challenging goals")
        
        if not recommendations:
            recommendations.append("Continue current approach with regular progress monitoring")
        
        report['recommendations'] = recommendations
        
        return report
    
    def suggest_goal_modifications(self, goal_id: int) -> Dict[str, Any]:
        """Suggest modifications for goals that aren't progressing well"""
        
        # Get goal and progress data
        goals = self.db.execute_query("SELECT * FROM treatment_goals WHERE id = ?", (goal_id,))
        if not goals:
            raise ValueError(f"Goal {goal_id} not found")
        
        goal = goals[0]
        
        # Get progress history
        progress_history = self.db.execute_query(
            "SELECT * FROM goal_progress_tracking WHERE goal_id = ? ORDER BY progress_date DESC LIMIT 5",
            (goal_id,)
        )
        
        # Analyze progress patterns
        if len(progress_history) >= 2:
            recent_change = progress_history[0]['progress_percentage'] - progress_history[-1]['progress_percentage']
            avg_progress = sum(p['progress_percentage'] for p in progress_history) / len(progress_history)
        else:
            recent_change = 0
            avg_progress = goal['current_progress']
        
        suggestions = {
            'goal_id': goal_id,
            'current_status': goal['status'],
            'current_progress': goal['current_progress'],
            'progress_trend': 'improving' if recent_change > 0 else 'stable' if recent_change == 0 else 'declining',
            'recommended_actions': [],
            'modification_options': {},
            'barrier_analysis': []
        }
        
        # Analyze barriers from progress entries
        all_barriers = []
        for entry in progress_history:
            if entry.get('barriers_encountered'):
                try:
                    barriers = json.loads(entry['barriers_encountered'])
                    all_barriers.extend(barriers)
                except json.JSONDecodeError:
                    pass
        
        # Count barrier frequency
        barrier_counts = {}
        for barrier in all_barriers:
            barrier_counts[barrier] = barrier_counts.get(barrier, 0) + 1
        
        suggestions['barrier_analysis'] = [
            {'barrier': barrier, 'frequency': count} 
            for barrier, count in sorted(barrier_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Generate recommendations based on progress pattern
        if goal['current_progress'] < 20 and len(progress_history) >= 3:
            suggestions['recommended_actions'].append("Consider breaking goal into smaller, more achievable milestones")
            suggestions['modification_options']['break_down'] = {
                'description': 'Split current goal into 2-3 smaller sub-goals',
                'rationale': 'Large goals can be overwhelming and demotivating'
            }
        
        if recent_change < 0:
            suggestions['recommended_actions'].append("Identify and address barriers preventing progress")
            suggestions['recommended_actions'].append("Consider adjusting timeline or measurement criteria")
        
        if avg_progress < 30 and goal['priority_level'] == 3:
            suggestions['modification_options']['lower_priority'] = {
                'description': 'Reduce goal priority to focus on more achievable objectives',
                'rationale': 'High-priority goals with low progress can create frustration'
            }
        
        if len(barrier_counts) > 0:
            most_common_barrier = max(barrier_counts.items(), key=lambda x: x[1])
            suggestions['recommended_actions'].append(f"Address recurring barrier: {most_common_barrier[0]}")
        
        # Timeline adjustments
        if goal.get('target_date'):
            target_date = datetime.fromisoformat(goal['target_date'])
            days_remaining = (target_date - datetime.now()).days
            
            if days_remaining < 14 and goal['current_progress'] < 70:
                suggestions['modification_options']['extend_timeline'] = {
                    'description': 'Extend goal deadline by 4-6 weeks',
                    'rationale': 'Current timeline appears too aggressive given progress rate'
                }
        
        # Measurement criteria adjustments
        if goal['current_progress'] < 25 and len(progress_history) >= 4:
            suggestions['modification_options']['adjust_criteria'] = {
                'description': 'Modify measurement criteria to be more specific or achievable',
                'rationale': 'Current criteria may be too vague or difficult to measure'
            }
        
        return suggestions
    
    def create_goal_from_template(self, patient_id: int, template_name: str, 
                                 customizations: Dict[str, Any] = None) -> SMARTGoal:
        """Create goal from predefined template with optional customizations"""
        
        if template_name not in self.goal_templates:
            available_templates = list(self.goal_templates.keys())
            raise ValueError(f"Template '{template_name}' not found. Available: {available_templates}")
        
        template = self.goal_templates[template_name]
        customizations = customizations or {}
        
        # Build goal parameters from template
        goal_params = {
            'template': template_name,
            'goal_type': customizations.get('goal_type', template['goal_type']),
            'title': customizations.get('title', template['title']),
            'specific_description': customizations.get('description', template['description']),
            'measurable_criteria': customizations.get('measurement', template['measurement']),
            'timeframe': customizations.get('timeframe', template['timeframe']),
            'priority_level': customizations.get('priority_level', PriorityLevel.MEDIUM.value)
        }
        
        # Add custom milestones if provided
        if 'milestones' in customizations:
            goal_params['custom_milestones'] = customizations['milestones']
        
        return self.create_smart_goal(patient_id, **goal_params)
    
    def bulk_update_goals(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform bulk updates on multiple goals"""
        
        results = {
            'successful_updates': 0,
            'failed_updates': 0,
            'errors': [],
            'updated_goals': []
        }
        
        for update in updates:
            try:
                goal_id = update['goal_id']
                
                if 'progress' in update:
                    result = self.update_goal_progress(
                        goal_id, 
                        update['progress'],
                        notes=update.get('notes', ''),
                        barriers=update.get('barriers', []),
                        strategies=update.get('strategies', [])
                    )
                    results['updated_goals'].append(result)
                
                if 'status' in update:
                    self.db.execute_update(
                        "UPDATE treatment_goals SET status = ?, last_updated = ? WHERE id = ?",
                        (update['status'], datetime.now().isoformat(), goal_id)
                    )
                
                if 'priority' in update:
                    self.db.execute_update(
                        "UPDATE treatment_goals SET priority_level = ?, last_updated = ? WHERE id = ?",
                        (update['priority'], datetime.now().isoformat(), goal_id)
                    )
                
                results['successful_updates'] += 1
                
            except Exception as e:
                results['failed_updates'] += 1
                results['errors'].append({
                    'goal_id': update.get('goal_id', 'unknown'),
                    'error': str(e)
                })
        
        return results
    
    def get_goal_recommendations(self, patient_id: int) -> Dict[str, Any]:
        """Get personalized goal recommendations based on patient data"""
        
        # Get patient diagnoses
        diagnoses = self.db.execute_query(
            "SELECT diagnosis_name FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        # Get current goals
        current_goals = self.get_patient_goals(patient_id, status=GoalStatus.ACTIVE.value)
        
        # Get recent assessment data
        assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 5",
            (patient_id,)
        )
        
        recommendations = {
            'patient_id': patient_id,
            'current_goal_count': len(current_goals),
            'suggested_goals': [],
            'goal_adjustments': [],
            'priority_suggestions': []
        }
        
        # Analyze current goal coverage
        current_goal_types = {goal['goal_type'] for goal in current_goals}
        
        # Recommend goals based on diagnoses
        diagnosis_names = [d['diagnosis_name'].lower() for d in diagnoses]
        
        for diagnosis in diagnosis_names:
            if 'depression' in diagnosis and GoalType.SYMPTOM.value not in current_goal_types:
                recommendations['suggested_goals'].append({
                    'template': 'depression_symptom_reduction',
                    'rationale': 'Depression diagnosis indicates need for symptom-focused goals',
                    'priority': PriorityLevel.HIGH.value
                })
            
            if 'anxiety' in diagnosis and GoalType.SYMPTOM.value not in current_goal_types:
                recommendations['suggested_goals'].append({
                    'template': 'anxiety_management',
                    'rationale': 'Anxiety diagnosis suggests need for coping skills development',
                    'priority': PriorityLevel.HIGH.value
                })
            
            if 'ptsd' in diagnosis:
                if GoalType.COGNITIVE.value not in current_goal_types:
                    recommendations['suggested_goals'].append({
                        'template': 'emotional_regulation',
                        'rationale': 'PTSD often involves emotional dysregulation',
                        'priority': PriorityLevel.HIGH.value
                    })
        
        # Recommend functional goals if missing
        if GoalType.FUNCTIONAL.value not in current_goal_types and len(current_goals) < 4:
            recommendations['suggested_goals'].append({
                'template': 'social_functioning',
                'rationale': 'Functional improvement supports overall recovery',
                'priority': PriorityLevel.MEDIUM.value
            })
        
        # Analyze assessment trends for goal recommendations
        if assessments:
            latest_assessments = {}
            for assessment in assessments:
                if assessment['assessment_type'] not in latest_assessments:
                    latest_assessments[assessment['assessment_type']] = assessment
            
            # Sleep issues indicated by multiple high scores
            if any(score['total_score'] > 15 for score in latest_assessments.values()):
                if not any('sleep' in goal['goal_description'].lower() for goal in current_goals):
                    recommendations['suggested_goals'].append({
                        'template': 'sleep_improvement',
                        'rationale': 'Assessment scores suggest sleep difficulties',
                        'priority': PriorityLevel.MEDIUM.value
                    })
        
        # Analyze current goal performance for adjustments
        for goal in current_goals:
            if goal['current_progress'] < 20:
                # Days since goal creation
                created_date = datetime.fromisoformat(goal['created_date'])
                days_active = (datetime.now() - created_date).days
                
                if days_active > 28:  # More than 4 weeks with minimal progress
                    recommendations['goal_adjustments'].append({
                        'goal_id': goal['id'],
                        'current_progress': goal['current_progress'],
                        'recommendation': 'Consider breaking down into smaller milestones',
                        'rationale': 'Goal has been active for 4+ weeks with minimal progress'
                    })
        
        # Priority balancing suggestions
        high_priority_goals = [g for g in current_goals if g['priority_level'] == PriorityLevel.HIGH.value]
        
        if len(high_priority_goals) > 3:
            recommendations['priority_suggestions'].append({
                'suggestion': 'Consider reducing some goals to medium priority',
                'rationale': 'Too many high-priority goals can be overwhelming and reduce focus'
            })
        
        if len(current_goals) > 6:
            recommendations['priority_suggestions'].append({
                'suggestion': 'Focus on 3-5 most important goals',
                'rationale': 'Research suggests 3-5 concurrent goals optimize success rates'
            })
        
        return recommendations
    
    def export_goal_data(self, patient_id: int) -> Dict[str, Any]:
        """Export comprehensive goal data for patient"""
        
        # Get all goals
        goals = self.get_patient_goals(patient_id)
        
        # Get all progress tracking data
        all_progress = []
        for goal in goals:
            progress_entries = self.db.execute_query(
                "SELECT * FROM goal_progress_tracking WHERE goal_id = ? ORDER BY progress_date",
                (goal['id'],)
            )
            all_progress.extend(progress_entries)
        
        export_data = {
            'patient_id': patient_id,
            'export_date': datetime.now().isoformat(),
            'total_goals': len(goals),
            'goals': goals,
            'progress_history': all_progress,
            'summary_statistics': self._calculate_goal_statistics(goals, all_progress)
        }
        
        return export_data
    
    def _calculate_goal_statistics(self, goals: List[Dict[str, Any]], 
                                  progress_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive goal statistics"""
        
        if not goals:
            return {'total_goals': 0}
        
        stats = {
            'total_goals': len(goals),
            'by_status': {},
            'by_type': {},
            'by_priority': {},
            'progress_metrics': {
                'average_progress': 0,
                'median_progress': 0,
                'goals_above_50_percent': 0,
                'goals_completed': 0
            },
            'timeline_analysis': {
                'overdue_goals': 0,
                'on_track_goals': 0,
                'ahead_of_schedule': 0
            }
        }
        
        # Count by status
        for goal in goals:
            status = goal['status']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Count by type
        for goal in goals:
            goal_type = goal['goal_type']
            stats['by_type'][goal_type] = stats['by_type'].get(goal_type, 0) + 1
        
        # Count by priority
        for goal in goals:
            priority = goal['priority_level']
            stats['by_priority'][str(priority)] = stats['by_priority'].get(str(priority), 0) + 1
        
        # Progress metrics
        progress_values = [goal['current_progress'] for goal in goals]
        if progress_values:
            stats['progress_metrics']['average_progress'] = round(sum(progress_values) / len(progress_values), 1)
            stats['progress_metrics']['median_progress'] = sorted(progress_values)[len(progress_values) // 2]
            stats['progress_metrics']['goals_above_50_percent'] = len([p for p in progress_values if p >= 50])
            stats['progress_metrics']['goals_completed'] = len([p for p in progress_values if p >= 100])
        
        # Timeline analysis
        for goal in goals:
            if goal.get('target_date') and goal['status'] == GoalStatus.ACTIVE.value:
                target_date = datetime.fromisoformat(goal['target_date'])
                days_remaining = (target_date - datetime.now()).days
                
                if days_remaining < 0:
                    stats['timeline_analysis']['overdue_goals'] += 1
                elif goal['current_progress'] >= (100 - (days_remaining / 7) * 10):  # Rough on-track calculation
                    stats['timeline_analysis']['ahead_of_schedule'] += 1
                else:
                    stats['timeline_analysis']['on_track_goals'] += 1
        
        return stats
    
    def get_goal_templates(self) -> Dict[str, Any]:
        """Get all available goal templates"""
        return {
            'templates': self.goal_templates,
            'template_count': len(self.goal_templates),
            'available_types': list(set(template['goal_type'] for template in self.goal_templates.values()))
        }


# Utility functions
def create_quick_goal(db: DatabaseManager, patient_id: int, goal_description: str, 
                     target_weeks: int = 8) -> Dict[str, Any]:
    """Quick goal creation helper function"""
    
    goal_manager = GoalManager(db)
    
    # Simple goal creation
    goal = goal_manager.create_smart_goal(
        patient_id=patient_id,
        title="Custom Goal",
        specific_description=goal_description,
        measurable_criteria="Progress measured through self-reporting and clinical observation",
        timeframe=f"{target_weeks} weeks",
        achievable_rationale="Goal is realistic with appropriate support and effort",
        relevant_connection="Directly supports treatment objectives and patient well-being"
    )
    
    return {
        'goal_id': goal.id,
        'title': goal.title,
        'description': goal.specific_description,
        'target_date': goal.target_date,
        'created_date': goal.created_date
    }


def track_daily_progress(db: DatabaseManager, patient_id: int, 
                        goal_progress_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Helper function for daily progress tracking"""
    
    goal_manager = GoalManager(db)
    results = []
    
    for update in goal_progress_updates:
        try:
            result = goal_manager.update_goal_progress(
                goal_id=update['goal_id'],
                progress_percentage=update['progress'],
                notes=update.get('notes', ''),
                barriers=update.get('barriers', []),
                strategies=update.get('strategies', [])
            )
            results.append(result)
        except Exception as e:
            results.append({
                'goal_id': update['goal_id'],
                'error': str(e)
            })
    
    return {
        'patient_id': patient_id,
        'updates_processed': len(results),
        'results': results,
        'timestamp': datetime.now().isoformat()
    }


def generate_goal_dashboard_data(db: DatabaseManager, patient_id: int) -> Dict[str, Any]:
    """Generate data for goal dashboard display"""
    
    goal_manager = GoalManager(db)
    
    # Get active goals
    active_goals = goal_manager.get_patient_goals(patient_id, status=GoalStatus.ACTIVE.value)
    
    # Get recent achievements
    achieved_goals = goal_manager.get_patient_goals(patient_id, status=GoalStatus.ACHIEVED.value)
    recent_achieved = [g for g in achieved_goals if 
                      (datetime.now() - datetime.fromisoformat(g['last_updated'])).days <= 30]
    
    # Calculate dashboard metrics
    dashboard_data = {
        'patient_id': patient_id,
        'active_goal_count': len(active_goals),
        'recent_achievements': len(recent_achieved),
        'average_progress': round(sum(g['current_progress'] for g in active_goals) / len(active_goals), 1) if active_goals else 0,
        'goals_on_track': len([g for g in active_goals if g['current_progress'] >= 50]),
        'goals_need_attention': len([g for g in active_goals if g['current_progress'] < 30]),
        'top_priority_goals': [g for g in active_goals if g['priority_level'] == PriorityLevel.HIGH.value][:3],
        'recent_progress': []
    }
    
    # Get recent progress for active goals
    for goal in active_goals[:5]:  # Top 5 goals
        recent_progress = db.execute_query(
            "SELECT progress_percentage, progress_date FROM goal_progress_tracking WHERE goal_id = ? ORDER BY progress_date DESC LIMIT 5",
            (goal['id'],)
        )
        
        if recent_progress:
            dashboard_data['recent_progress'].append({
                'goal_id': goal['id'],
                'goal_title': goal['goal_description'].split(':')[0] if ':' in goal['goal_description'] else goal['goal_description'][:30],
                'current_progress': goal['current_progress'],
                'progress_history': [{'date': p['progress_date'], 'progress': p['progress_percentage']} for p in recent_progress]
            })
    
    return dashboard_data


# Test function
def main():
    """Test goal management system functionality"""
    from database import DatabaseManager
    
    print("Testing Goal Management System...")
    
    db = DatabaseManager(":memory:")
    goal_manager = GoalManager(db)
    
    # Create test patient
    patient_id = db.execute_update(
        "INSERT INTO patients (name, preferred_therapy_mode) VALUES (?, ?)",
        ("Test Patient", "CBT")
    )
    
    # Add test diagnosis
    db.execute_update(
        "INSERT INTO diagnoses (patient_id, diagnosis_name, status) VALUES (?, ?, ?)",
        (patient_id, "Major Depressive Disorder", "active")
    )
    
    print(f"Created test patient ID: {patient_id}")
    
    # Test goal creation from template
    print("\n1. Testing goal creation from template...")
    goal = goal_manager.create_goal_from_template(
        patient_id, 
        'depression_symptom_reduction',
        customizations={'timeframe': '10 weeks'}
    )
    print(f"Created goal: {goal.title} (ID: {goal.id})")
    print(f"Target date: {goal.target_date}")
    print(f"Milestones: {len(goal.milestones)}")
    
    # Test progress update
    print("\n2. Testing progress update...")
    progress_result = goal_manager.update_goal_progress(
        goal.id, 
        35, 
        notes="Making steady progress with mood tracking",
        barriers=["Difficulty with morning routine"],
        strategies=["Using phone reminders"]
    )
    print(f"Progress updated to: {progress_result['new_progress']}%")
    print(f"Progress change: {progress_result['progress_change']:+d}%")
    
    # Test goal recommendations
    print("\n3. Testing goal recommendations...")
    recommendations = goal_manager.get_goal_recommendations(patient_id)
    print(f"Current goals: {recommendations['current_goal_count']}")
    print(f"Suggested new goals: {len(recommendations['suggested_goals'])}")
    
    # Test progress report
    print("\n4. Testing progress report...")
    report = goal_manager.generate_goal_progress_report(patient_id, days=30)
    print(f"Active goals: {report['summary_stats']['active_goals']}")
    print(f"Average progress: {report['summary_stats']['average_progress']}%")
    print(f"Recommendations: {len(report['recommendations'])}")
    
    # Test dashboard data
    print("\n5. Testing dashboard data...")
    dashboard = generate_goal_dashboard_data(db, patient_id)
    print(f"Dashboard metrics - Active: {dashboard['active_goal_count']}, Avg Progress: {dashboard['average_progress']}%")
    
    print("\nGoal management system testing completed successfully!")


if __name__ == "__main__":
    main()