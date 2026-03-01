#!/usr/bin/env python3
"""
AI Therapy System - Clinical Documentation System
Professional clinical documentation, progress notes, treatment plans, and reporting
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from database import DatabaseManager
from models import ProgressNote, TreatmentGoal
from utils import log_action


class NoteType(Enum):
    """Types of clinical notes"""
    SOAP = "SOAP"
    PROGRESS = "progress"
    CRISIS = "crisis"
    ASSESSMENT = "assessment"
    TREATMENT_PLAN = "treatment_plan"
    DISCHARGE = "discharge"
    CONSULTATION = "consultation"


class DocumentationStatus(Enum):
    """Documentation status levels"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    SIGNED = "signed"
    AMENDED = "amended"


@dataclass
class SOAPNote:
    """SOAP format progress note"""
    id: Optional[int] = None
    patient_id: int = 0
    session_id: Optional[int] = None
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "AI_Therapist"
    status: str = DocumentationStatus.DRAFT.value
    last_modified: Optional[str] = None
    signed: bool = False


@dataclass
class TreatmentPlan:
    """Comprehensive treatment plan"""
    id: Optional[int] = None
    patient_id: int = 0
    plan_name: str = ""
    primary_modality: str = ""
    presenting_problems: List[str] = field(default_factory=list)
    target_symptoms: List[str] = field(default_factory=list)
    treatment_goals: List[Dict[str, Any]] = field(default_factory=list)
    interventions_planned: List[str] = field(default_factory=list)
    estimated_duration: int = 0  # weeks
    session_frequency: str = "weekly"
    prognosis: str = ""
    discharge_criteria: List[str] = field(default_factory=list)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_reviewed: Optional[str] = None
    next_review_date: Optional[str] = None
    status: str = "active"
    created_by: str = "AI_System"


@dataclass
class ClinicalReport:
    """Clinical assessment and summary report"""
    id: Optional[int] = None
    patient_id: int = 0
    report_type: str = ""
    title: str = ""
    summary: str = ""
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    date_range: Dict[str, str] = field(default_factory=dict)
    generated_date: str = field(default_factory=lambda: datetime.now().isoformat())
    generated_by: str = "AI_System"


class DocumentationSystem:
    """Manages all clinical documentation and reporting"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.templates = self._load_documentation_templates()
        self._init_documentation_tables()
    
    def _init_documentation_tables(self):
        """Initialize documentation-related database tables"""
        with self.db.get_connection() as conn:
            # Clinical reports table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS clinical_reports (
                    id INTEGER PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT,
                    findings TEXT DEFAULT '[]',
                    recommendations TEXT DEFAULT '[]',
                    data_sources TEXT DEFAULT '[]',
                    date_range_start TEXT,
                    date_range_end TEXT,
                    generated_date TEXT NOT NULL DEFAULT (datetime('now')),
                    generated_by TEXT DEFAULT 'AI_System',
                    status TEXT DEFAULT 'completed',
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            ''')
            
            # Documentation templates table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS documentation_templates (
                    id INTEGER PRIMARY KEY,
                    template_name TEXT NOT NULL UNIQUE,
                    template_type TEXT NOT NULL,
                    template_content TEXT NOT NULL,
                    variables TEXT DEFAULT '[]',
                    created_date TEXT NOT NULL DEFAULT (datetime('now')),
                    active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            conn.commit()
    
    def _load_documentation_templates(self) -> Dict[str, str]:
        """Load documentation templates"""
        templates = {
            'soap_note': '''
SOAP NOTE
Date: {date}
Patient: {patient_name}
Session: {session_number}
Duration: {session_duration} minutes
Modality: {therapy_modality}

SUBJECTIVE:
{subjective_content}

OBJECTIVE:
{objective_content}

ASSESSMENT:
{assessment_content}

PLAN:
{plan_content}

Clinician: {clinician_name}
Date: {completion_date}
''',
            
            'treatment_plan': '''
TREATMENT PLAN
Patient: {patient_name}
Date: {plan_date}
Primary Therapist: {therapist_name}

PRESENTING PROBLEMS:
{presenting_problems}

DIAGNOSTIC IMPRESSIONS:
{diagnoses}

TREATMENT GOALS:
{treatment_goals}

PLANNED INTERVENTIONS:
{interventions}

TREATMENT MODALITY: {modality}
ESTIMATED DURATION: {duration} weeks
SESSION FREQUENCY: {frequency}

PROGNOSIS: {prognosis}

DISCHARGE CRITERIA:
{discharge_criteria}

NEXT REVIEW DATE: {next_review}
''',
            
            'progress_summary': '''
PROGRESS SUMMARY
Patient: {patient_name}
Period: {start_date} to {end_date}

TREATMENT SUMMARY:
Total Sessions: {total_sessions}
Primary Modality: {modality}
Session Attendance: {attendance_rate}%

ASSESSMENT OUTCOMES:
{assessment_outcomes}

GOAL PROGRESS:
{goal_progress}

CLINICAL OBSERVATIONS:
{clinical_observations}

CURRENT STATUS:
{current_status}

RECOMMENDATIONS:
{recommendations}
'''
        }
        
        return templates
    
    def create_soap_note(self, patient_id: int, session_id: int, 
                        subjective: str, objective: str, 
                        assessment: str, plan: str) -> SOAPNote:
        """Create a SOAP format progress note"""
        
        soap_note = SOAPNote(
            patient_id=patient_id,
            session_id=session_id,
            subjective=subjective,
            objective=objective,
            assessment=assessment,
            plan=plan
        )
        
        # Save to database
        note_id = self.db.execute_update('''
            INSERT INTO progress_notes 
            (patient_id, session_id, note_type, subjective, objective, assessment, plan, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, session_id, NoteType.SOAP.value,
            subjective, objective, assessment, plan, soap_note.created_by
        ))
        
        soap_note.id = note_id
        
        log_action(f"SOAP note created for session {session_id}", 
                  "documentation", patient_id=patient_id)
        
        return soap_note
    
    def generate_auto_soap_note(self, patient_id: int, session_id: int) -> SOAPNote:
        """Auto-generate SOAP note from session data"""
        
        # Get session data
        session_data = self.db.execute_query(
            "SELECT * FROM sessions WHERE id = ? AND patient_id = ?",
            (session_id, patient_id)
        )
        
        if not session_data:
            raise ValueError(f"Session {session_id} not found for patient {patient_id}")
        
        session = session_data[0]
        
        # Get patient data
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        patient = patient_data[0] if patient_data else {}
        
        # Generate SUBJECTIVE section
        subjective = self._generate_subjective_section(session, patient_id)
        
        # Generate OBJECTIVE section
        objective = self._generate_objective_section(session, patient_id)
        
        # Generate ASSESSMENT section
        assessment = self._generate_assessment_section(session, patient_id)
        
        # Generate PLAN section
        plan = self._generate_plan_section(session, patient_id)
        
        return self.create_soap_note(patient_id, session_id, subjective, objective, assessment, plan)
    
    def _generate_subjective_section(self, session: Dict[str, Any], patient_id: int) -> str:
        """Generate subjective section from session data"""
        subjective_parts = []
        
        # Mood ratings
        if session.get('mood_before') and session.get('mood_after'):
            subjective_parts.append(
                f"Patient reported mood {session['mood_before']}/10 at session start, "
                f"{session['mood_after']}/10 at session end."
            )
        
        # Patient feedback
        if session.get('patient_feedback'):
            subjective_parts.append(f"Patient feedback: {session['patient_feedback']}")
        
        # Recent assessments
        recent_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? AND assessment_date > ? ORDER BY assessment_date DESC LIMIT 3",
            (patient_id, (datetime.now() - timedelta(days=7)).isoformat())
        )
        
        for assessment in recent_assessments:
            subjective_parts.append(
                f"{assessment['assessment_type']} score: {assessment['total_score']} "
                f"({assessment['severity_level']} severity)"
            )
        
        # Homework completion
        homework = self.db.execute_query(
            "SELECT * FROM homework_assignments WHERE patient_id = ? AND session_id = ?",
            (patient_id, session['id'])
        )
        
        if homework:
            completed = sum(1 for hw in homework if hw['completed'])
            subjective_parts.append(f"Homework completion: {completed}/{len(homework)} assignments")
        
        return "\n".join(subjective_parts) if subjective_parts else "Patient attended session as scheduled."
    
    def _generate_objective_section(self, session: Dict[str, Any], patient_id: int) -> str:
        """Generate objective section from observable data"""
        objective_parts = []
        
        # Session attendance and duration
        objective_parts.append(f"Patient attended {session['session_type']} session.")
        objective_parts.append(f"Session duration: {session.get('duration', 50)} minutes.")
        
        # Interventions used
        if session.get('interventions_used'):
            try:
                interventions = json.loads(session['interventions_used'])
                if interventions:
                    objective_parts.append(f"Interventions utilized: {', '.join(interventions)}")
            except json.JSONDecodeError:
                pass
        
        # Crisis flags
        if session.get('crisis_flags'):
            try:
                crisis_flags = json.loads(session['crisis_flags'])
                if crisis_flags:
                    objective_parts.append(f"Crisis indicators noted: {', '.join(crisis_flags)}")
            except json.JSONDecodeError:
                pass
        
        # Therapist observations
        if session.get('therapist_notes'):
            # Extract objective observations from therapist notes
            notes = session['therapist_notes']
            if 'appeared' in notes.lower() or 'observed' in notes.lower():
                objective_parts.append(f"Clinical observations: {notes}")
        
        return "\n".join(objective_parts)
    
    def _generate_assessment_section(self, session: Dict[str, Any], patient_id: int) -> str:
        """Generate assessment section with clinical analysis"""
        assessment_parts = []
        
        # Current diagnoses
        diagnoses = self.db.execute_query(
            "SELECT * FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        if diagnoses:
            dx_list = [f"{dx['diagnosis_name']} ({dx['severity']})" for dx in diagnoses]
            assessment_parts.append(f"Active diagnoses: {'; '.join(dx_list)}")
        
        # Progress assessment
        mood_change = None
        if session.get('mood_before') and session.get('mood_after'):
            mood_change = session['mood_after'] - session['mood_before']
            if mood_change > 0:
                assessment_parts.append(f"Mood improvement noted during session (+{mood_change} points)")
            elif mood_change < 0:
                assessment_parts.append(f"Mood decline noted during session ({mood_change} points)")
            else:
                assessment_parts.append("Mood remained stable during session")
        
        # Goal progress
        active_goals = self.db.execute_query(
            "SELECT * FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        if active_goals:
            avg_progress = sum(goal['current_progress'] for goal in active_goals) / len(active_goals)
            assessment_parts.append(f"Average goal progress: {avg_progress:.0f}%")
        
        # Treatment response
        if session['session_type'] in ['CBT', 'DBT', 'ACT']:
            assessment_parts.append(f"Patient demonstrated engagement with {session['session_type']} interventions")
        
        return "\n".join(assessment_parts) if assessment_parts else "Patient continues in active treatment."
    
    def _generate_plan_section(self, session: Dict[str, Any], patient_id: int) -> str:
        """Generate plan section with next steps"""
        plan_parts = []
        
        # Continue current modality
        plan_parts.append(f"Continue {session['session_type']} therapy")
        
        # Homework assignments
        if session.get('homework_assigned'):
            plan_parts.append(f"Homework assigned: {session['homework_assigned']}")
        
        # Next session planning
        plan_parts.append("Schedule next session per treatment plan")
        
        # Risk management if needed
        crisis_flags = session.get('crisis_flags')
        if crisis_flags:
            try:
                flags = json.loads(crisis_flags)
                if flags:
                    plan_parts.append("Continue crisis monitoring and safety planning")
            except json.JSONDecodeError:
                pass
        
        # Assessment recommendations
        last_assessment = self.db.execute_query(
            "SELECT assessment_date FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 1",
            (patient_id,)
        )
        
        if last_assessment:
            last_date = datetime.fromisoformat(last_assessment[0]['assessment_date'])
            days_since = (datetime.now() - last_date).days
            if days_since > 30:
                plan_parts.append("Consider repeat standardized assessments")
        
        return "\n".join(plan_parts)
    
    def create_treatment_plan(self, patient_id: int, **kwargs) -> TreatmentPlan:
        """Create comprehensive treatment plan"""
        
        # Get patient data
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        if not patient_data:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_data[0]
        
        # Get current diagnoses
        diagnoses = self.db.execute_query(
            "SELECT * FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        # Create treatment plan
        treatment_plan = TreatmentPlan(
            patient_id=patient_id,
            plan_name=kwargs.get('plan_name', f"Treatment Plan - {patient['name']}"),
            primary_modality=kwargs.get('primary_modality', patient.get('preferred_therapy_mode', 'CBT')),
            presenting_problems=kwargs.get('presenting_problems', []),
            target_symptoms=kwargs.get('target_symptoms', [dx['diagnosis_name'] for dx in diagnoses]),
            estimated_duration=kwargs.get('estimated_duration', 12),
            session_frequency=kwargs.get('session_frequency', 'weekly'),
            prognosis=kwargs.get('prognosis', 'Good with consistent engagement')
        )
        
        # Auto-generate goals if not provided
        if not kwargs.get('treatment_goals'):
            treatment_plan.treatment_goals = self._generate_smart_goals(patient_id, diagnoses)
        else:
            treatment_plan.treatment_goals = kwargs['treatment_goals']
        
        # Auto-generate interventions based on modality and diagnoses
        if not kwargs.get('interventions_planned'):
            treatment_plan.interventions_planned = self._suggest_interventions(
                treatment_plan.primary_modality, diagnoses
            )
        else:
            treatment_plan.interventions_planned = kwargs['interventions_planned']
        
        # Auto-generate discharge criteria
        if not kwargs.get('discharge_criteria'):
            treatment_plan.discharge_criteria = self._generate_discharge_criteria(diagnoses)
        else:
            treatment_plan.discharge_criteria = kwargs['discharge_criteria']
        
        # Calculate next review date
        review_weeks = 4 if treatment_plan.estimated_duration <= 12 else 6
        next_review = datetime.now() + timedelta(weeks=review_weeks)
        treatment_plan.next_review_date = next_review.isoformat()
        
        # Save to database
        plan_id = self._save_treatment_plan(treatment_plan)
        treatment_plan.id = plan_id
        
        log_action(f"Treatment plan created", "documentation", patient_id=patient_id)
        
        return treatment_plan
    
    def _generate_smart_goals(self, patient_id: int, diagnoses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate SMART treatment goals based on diagnoses"""
        goals = []
        
        for diagnosis in diagnoses:
            if 'depression' in diagnosis['diagnosis_name'].lower():
                goals.append({
                    'type': 'symptom',
                    'description': 'Reduce depressive symptoms as measured by PHQ-9 score to mild range (≤9)',
                    'measurement': 'PHQ-9 score ≤9 for 2 consecutive assessments',
                    'timeframe': '12 weeks',
                    'priority': 'high'
                })
                goals.append({
                    'type': 'functional',
                    'description': 'Increase engagement in pleasurable activities to 3-4 times per week',
                    'measurement': 'Activity log showing 3+ pleasant activities weekly',
                    'timeframe': '8 weeks',
                    'priority': 'medium'
                })
            
            elif 'anxiety' in diagnosis['diagnosis_name'].lower():
                goals.append({
                    'type': 'symptom',
                    'description': 'Reduce anxiety symptoms as measured by GAD-7 score to mild range (≤9)',
                    'measurement': 'GAD-7 score ≤9 for 2 consecutive assessments',
                    'timeframe': '12 weeks',
                    'priority': 'high'
                })
                goals.append({
                    'type': 'behavioral',
                    'description': 'Decrease avoidance behaviors by 50%',
                    'measurement': 'Exposure log showing 50% reduction in avoided situations',
                    'timeframe': '10 weeks',
                    'priority': 'medium'
                })
            
            elif 'ptsd' in diagnosis['diagnosis_name'].lower():
                goals.append({
                    'type': 'symptom',
                    'description': 'Reduce PTSD symptoms as measured by PCL-5 score below clinical threshold (<33)',
                    'measurement': 'PCL-5 score <33 for 2 consecutive assessments',
                    'timeframe': '16 weeks',
                    'priority': 'high'
                })
                goals.append({
                    'type': 'functional',
                    'description': 'Improve sleep quality to 6+ hours per night with <2 nighttime awakenings',
                    'measurement': 'Sleep diary showing consistent 6+ hours sleep',
                    'timeframe': '8 weeks',
                    'priority': 'medium'
                })
        
        # Add general goals if no specific diagnoses
        if not goals:
            goals.append({
                'type': 'functional',
                'description': 'Improve overall mental health functioning and quality of life',
                'measurement': 'ORS score improvement of 5+ points from baseline',
                'timeframe': '12 weeks',
                'priority': 'medium'
            })
        
        return goals
    
    def _suggest_interventions(self, modality: str, diagnoses: List[Dict[str, Any]]) -> List[str]:
        """Suggest evidence-based interventions"""
        interventions = []
        
        # Get interventions from database
        db_interventions = self.db.execute_query(
            "SELECT intervention_name, target_symptoms FROM interventions_library WHERE modality = ? AND active = TRUE",
            (modality,)
        )
        
        # Match interventions to diagnoses
        for diagnosis in diagnoses:
            dx_name = diagnosis['diagnosis_name'].lower()
            
            for intervention in db_interventions:
                target_symptoms = json.loads(intervention.get('target_symptoms', '[]'))
                
                # Check if intervention targets this diagnosis
                if any(symptom.lower() in dx_name for symptom in target_symptoms):
                    if intervention['intervention_name'] not in interventions:
                        interventions.append(intervention['intervention_name'])
        
        # Add modality-specific core interventions
        if modality == 'CBT':
            core_interventions = ['Cognitive Restructuring', 'Behavioral Activation', 'Homework Assignments']
        elif modality == 'DBT':
            core_interventions = ['Mindfulness Training', 'Distress Tolerance Skills', 'Emotion Regulation']
        elif modality == 'ACT':
            core_interventions = ['Values Clarification', 'Cognitive Defusion', 'Mindfulness Practice']
        else:
            core_interventions = ['Supportive Therapy', 'Psychoeducation']
        
        for intervention in core_interventions:
            if intervention not in interventions:
                interventions.append(intervention)
        
        return interventions[:6]  # Limit to 6 main interventions
    
    def _generate_discharge_criteria(self, diagnoses: List[Dict[str, Any]]) -> List[str]:
        """Generate appropriate discharge criteria"""
        criteria = [
            "Significant reduction in target symptoms",
            "Achievement of treatment goals",
            "Improved functional capacity",
            "Development of effective coping strategies",
            "Patient feels confident in independent symptom management"
        ]
        
        # Add diagnosis-specific criteria
        for diagnosis in diagnoses:
            if 'depression' in diagnosis['diagnosis_name'].lower():
                criteria.append("PHQ-9 score in minimal range (≤4) for 4 weeks")
            elif 'anxiety' in diagnosis['diagnosis_name'].lower():
                criteria.append("GAD-7 score in minimal range (≤4) for 4 weeks")
            elif 'ptsd' in diagnosis['diagnosis_name'].lower():
                criteria.append("PCL-5 score below clinical threshold (<33) for 6 weeks")
        
        return criteria
    
    def _save_treatment_plan(self, plan: TreatmentPlan) -> int:
        """Save treatment plan to database"""
        plan_id = self.db.execute_update('''
            INSERT INTO treatment_plans
            (patient_id, plan_name, primary_modality, target_symptoms, treatment_goals,
             estimated_duration, session_frequency, created_date, next_review_date, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            plan.patient_id,
            plan.plan_name,
            plan.primary_modality,
            json.dumps(plan.target_symptoms),
            json.dumps(plan.treatment_goals),
            plan.estimated_duration,
            plan.session_frequency,
            plan.created_date,
            plan.next_review_date,
            plan.status,
            plan.created_by
        ))
        
        # Save individual goals to treatment_goals table
        for goal in plan.treatment_goals:
            self.db.execute_update('''
                INSERT INTO treatment_goals
                (patient_id, goal_type, goal_description, measurement_criteria, target_date, priority_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                plan.patient_id,
                goal['type'],
                goal['description'],
                goal['measurement'],
                (datetime.now() + timedelta(weeks=int(goal['timeframe'].split()[0]))).isoformat(),
                3 if goal['priority'] == 'high' else 2 if goal['priority'] == 'medium' else 1
            ))
        
        return plan_id
    def generate_progress_report(self, patient_id: int, days: int = 30) -> ClinicalReport:
        """Generate comprehensive progress report"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get patient info
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        if not patient_data:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_data[0]
        
        report = ClinicalReport(
            patient_id=patient_id,
            report_type="progress_report",
            title=f"Progress Report - {patient['name']}",
            date_range={
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        )
        
        # Gather data sources
        report.data_sources = ['Sessions', 'Assessments', 'Treatment Goals', 'Homework Assignments']
        
        # Generate findings
        findings = []
        
        # Session attendance and engagement
        sessions = self.db.execute_query(
            "SELECT * FROM sessions WHERE patient_id = ? AND session_date BETWEEN ? AND ? ORDER BY session_date",
            (patient_id, start_date.isoformat(), end_date.isoformat())
        )
        
        if sessions:
            findings.append(f"Attended {len(sessions)} sessions over {days}-day period")
            
            # Average mood change
            mood_changes = [
                s['mood_after'] - s['mood_before'] 
                for s in sessions 
                if s.get('mood_before') and s.get('mood_after')
            ]
            if mood_changes:
                avg_change = sum(mood_changes) / len(mood_changes)
                findings.append(f"Average mood improvement per session: {avg_change:.1f} points")
        
        # Assessment outcomes
        assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? AND assessment_date BETWEEN ? AND ? ORDER BY assessment_date",
            (patient_id, start_date.isoformat(), end_date.isoformat())
        )
        
        assessment_summary = {}
        for assessment in assessments:
            a_type = assessment['assessment_type']
            if a_type not in assessment_summary:
                assessment_summary[a_type] = []
            assessment_summary[a_type].append(assessment['total_score'])
        
        for a_type, scores in assessment_summary.items():
            if len(scores) > 1:
                change = scores[-1] - scores[0]
                trend = "improved" if change < 0 else "worsened" if change > 0 else "stable"
                findings.append(f"{a_type}: {trend} from {scores[0]} to {scores[-1]} (change: {change:+d})")
            elif len(scores) == 1:
                findings.append(f"{a_type}: Current score {scores[0]}")
        
        # Goal progress
        goals = self.db.execute_query(
            "SELECT * FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        if goals:
            avg_progress = sum(goal['current_progress'] for goal in goals) / len(goals)
            findings.append(f"Average goal progress: {avg_progress:.0f}% ({len(goals)} active goals)")
            
            completed_goals = [g for g in goals if g['current_progress'] >= 100]
            if completed_goals:
                findings.append(f"Completed goals: {len(completed_goals)}")
        
        # Homework compliance
        homework = self.db.execute_query(
            "SELECT * FROM homework_assignments WHERE patient_id = ? AND assigned_date BETWEEN ? AND ?",
            (patient_id, start_date.isoformat(), end_date.isoformat())
        )
        
        if homework:
            completed = sum(1 for hw in homework if hw['completed'])
            compliance_rate = (completed / len(homework)) * 100
            findings.append(f"Homework compliance: {compliance_rate:.0f}% ({completed}/{len(homework)} assignments)")
        
        report.findings = findings
        
        # Generate recommendations
        recommendations = []
        
        # Based on assessment trends
        for a_type, scores in assessment_summary.items():
            if len(scores) > 1 and scores[-1] > scores[0]:
                recommendations.append(f"Consider intensifying treatment approach for persistent {a_type} symptoms")
        
        # Based on goal progress
        if goals:
            low_progress_goals = [g for g in goals if g['current_progress'] < 30]
            if low_progress_goals:
                recommendations.append(f"Review and potentially modify {len(low_progress_goals)} goals with limited progress")
        
        # Based on attendance
        if len(sessions) < (days / 7):  # Less than weekly attendance
            recommendations.append("Consider addressing attendance barriers or adjusting session frequency")
        
        # Based on homework compliance
        if homework and (completed / len(homework)) < 0.6:  # Less than 60% compliance
            recommendations.append("Address homework compliance barriers and adjust assignment difficulty")
        
        # General recommendations
        if not recommendations:
            if sessions and len(sessions) >= 4:
                recommendations.append("Continue current treatment approach with regular progress monitoring")
            else:
                recommendations.append("Gather more session data before making treatment modifications")
        
        report.recommendations = recommendations
        
        # Generate summary
        summary_parts = [
            f"Patient completed {len(sessions)} sessions over {days} days.",
            f"Current treatment approach: {patient.get('preferred_therapy_mode', 'Not specified')}."
        ]
        
        if assessment_summary:
            summary_parts.append(f"Assessment data available for: {', '.join(assessment_summary.keys())}.")
        
        if goals:
            summary_parts.append(f"Working toward {len(goals)} treatment goals with {avg_progress:.0f}% average progress.")
        
        report.summary = " ".join(summary_parts)
        
        # Save report
        report_id = self._save_clinical_report(report)
        report.id = report_id
        
        log_action(f"Progress report generated covering {days} days", 
                  "documentation", patient_id=patient_id)
        
        return report
    
    def _save_clinical_report(self, report: ClinicalReport) -> int:
        """Save clinical report to database"""
        report_id = self.db.execute_update('''
            INSERT INTO clinical_reports
            (patient_id, report_type, title, summary, findings, recommendations, 
             data_sources, date_range_start, date_range_end, generated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.patient_id,
            report.report_type,
            report.title,
            report.summary,
            json.dumps(report.findings),
            json.dumps(report.recommendations),
            json.dumps(report.data_sources),
            report.date_range.get('start'),
            report.date_range.get('end'),
            report.generated_by
        ))
        
        return report_id
    
    def generate_discharge_summary(self, patient_id: int) -> ClinicalReport:
        """Generate discharge summary report"""
        
        # Get patient info
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        if not patient_data:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_data[0]
        
        # Get all session data
        sessions = self.db.execute_query(
            "SELECT * FROM sessions WHERE patient_id = ? ORDER BY session_date",
            (patient_id,)
        )
        
        if not sessions:
            raise ValueError("Cannot generate discharge summary without session history")
        
        first_session = sessions[0]
        last_session = sessions[-1]
        
        report = ClinicalReport(
            patient_id=patient_id,
            report_type="discharge_summary",
            title=f"Discharge Summary - {patient['name']}",
            date_range={
                'start': first_session['session_date'],
                'end': last_session['session_date']
            }
        )
        
        # Treatment summary
        total_sessions = len(sessions)
        treatment_duration_days = (
            datetime.fromisoformat(last_session['session_date']) - 
            datetime.fromisoformat(first_session['session_date'])
        ).days
        
        # Get initial and final assessments
        first_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date ASC LIMIT 5",
            (patient_id,)
        )
        
        last_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 5",
            (patient_id,)
        )
        
        # Calculate assessment changes
        assessment_changes = {}
        for first_assess in first_assessments:
            for last_assess in last_assessments:
                if first_assess['assessment_type'] == last_assess['assessment_type']:
                    change = last_assess['total_score'] - first_assess['total_score']
                    assessment_changes[first_assess['assessment_type']] = {
                        'initial': first_assess['total_score'],
                        'final': last_assess['total_score'],
                        'change': change
                    }
        
        # Generate findings
        findings = [
            f"Total treatment duration: {treatment_duration_days} days ({total_sessions} sessions)",
            f"Primary treatment modality: {patient.get('preferred_therapy_mode', 'Mixed approach')}",
        ]
        
        # Add assessment outcomes
        for assess_type, change_data in assessment_changes.items():
            improvement = "improved" if change_data['change'] < 0 else "worsened" if change_data['change'] > 0 else "remained stable"
            findings.append(
                f"{assess_type}: {improvement} from {change_data['initial']} to {change_data['final']} "
                f"(change: {change_data['change']:+d})"
            )
        
        # Goal achievement summary
        all_goals = self.db.execute_query(
            "SELECT * FROM treatment_goals WHERE patient_id = ?",
            (patient_id,)
        )
        
        if all_goals:
            completed_goals = [g for g in all_goals if g['status'] == 'achieved' or g['current_progress'] >= 100]
            avg_progress = sum(g['current_progress'] for g in all_goals) / len(all_goals)
            findings.append(f"Treatment goals: {len(completed_goals)}/{len(all_goals)} achieved (avg progress: {avg_progress:.0f}%)")
        
        # Current diagnoses at discharge
        current_diagnoses = self.db.execute_query(
            "SELECT * FROM diagnoses WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        if current_diagnoses:
            findings.append(f"Diagnoses at discharge: {'; '.join([dx['diagnosis_name'] for dx in current_diagnoses])}")
        
        report.findings = findings
        
        # Generate recommendations
        recommendations = [
            "Continue practicing coping skills learned in therapy",
            "Maintain regular self-monitoring of symptoms",
            "Contact provider if symptoms return or worsen"
        ]
        
        # Add specific recommendations based on outcomes
        for assess_type, change_data in assessment_changes.items():
            if change_data['final'] > 0:  # Still has some symptoms
                if assess_type == 'PHQ9':
                    recommendations.append("Continue mood monitoring and depression prevention strategies")
                elif assess_type == 'GAD7':
                    recommendations.append("Continue anxiety management techniques")
                elif assess_type == 'PCL5':
                    recommendations.append("Continue trauma recovery practices")
        
        # Add follow-up recommendations
        if any(change_data['change'] > 0 for change_data in assessment_changes.values()):
            recommendations.append("Consider booster sessions if symptoms worsen")
        
        recommendations.append("Follow-up assessment recommended in 3-6 months")
        
        report.recommendations = recommendations
        
        # Generate comprehensive summary
        summary_parts = [
            f"{patient['name']} completed {total_sessions} therapy sessions over {treatment_duration_days} days.",
        ]
        
        if assessment_changes:
            improved_assessments = [k for k, v in assessment_changes.items() if v['change'] < 0]
            if improved_assessments:
                summary_parts.append(f"Showed improvement on {len(improved_assessments)} standardized measures.")
        
        if all_goals and completed_goals:
            summary_parts.append(f"Achieved {len(completed_goals)} of {len(all_goals)} treatment goals.")
        
        summary_parts.append("Patient demonstrated engagement with treatment and acquired coping skills.")
        
        report.summary = " ".join(summary_parts)
        
        # Save report
        report_id = self._save_clinical_report(report)
        report.id = report_id
        
        log_action(f"Discharge summary generated", "documentation", patient_id=patient_id)
        
        return report
    
    def format_documentation(self, doc_type: str, data: Dict[str, Any]) -> str:
        """Format documentation using templates"""
        if doc_type not in self.templates:
            raise ValueError(f"Template {doc_type} not found")
        
        template = self.templates[doc_type]
        
        try:
            formatted_doc = template.format(**data)
            return formatted_doc
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")
    
    def get_patient_documentation_summary(self, patient_id: int) -> Dict[str, Any]:
        """Get comprehensive documentation summary for patient"""
        
        summary = {
            'patient_id': patient_id,
            'generated_date': datetime.now().isoformat(),
            'progress_notes': {},
            'treatment_plans': {},
            'clinical_reports': {},
            'documentation_stats': {}
        }
        
        # Progress notes summary
        notes = self.db.execute_query(
            "SELECT note_type, COUNT(*) as count FROM progress_notes WHERE patient_id = ? GROUP BY note_type",
            (patient_id,)
        )
        
        for note in notes:
            summary['progress_notes'][note['note_type']] = note['count']
        
        # Treatment plans summary
        plans = self.db.execute_query(
            "SELECT status, COUNT(*) as count FROM treatment_plans WHERE patient_id = ? GROUP BY status",
            (patient_id,)
        )
        
        for plan in plans:
            summary['treatment_plans'][plan['status']] = plan['count']
        
        # Clinical reports summary
        reports = self.db.execute_query(
            "SELECT report_type, COUNT(*) as count FROM clinical_reports WHERE patient_id = ? GROUP BY report_type",
            (patient_id,)
        )
        
        for report in reports:
            summary['clinical_reports'][report['report_type']] = report['count']
        
        # Documentation statistics
        total_notes = sum(summary['progress_notes'].values()) if summary['progress_notes'] else 0
        total_plans = sum(summary['treatment_plans'].values()) if summary['treatment_plans'] else 0
        total_reports = sum(summary['clinical_reports'].values()) if summary['clinical_reports'] else 0
        
        summary['documentation_stats'] = {
            'total_progress_notes': total_notes,
            'total_treatment_plans': total_plans,
            'total_clinical_reports': total_reports,
            'total_documents': total_notes + total_plans + total_reports
        }
        
        # Get most recent documentation
        recent_note = self.db.execute_query(
            "SELECT created_date FROM progress_notes WHERE patient_id = ? ORDER BY created_date DESC LIMIT 1",
            (patient_id,)
        )
        
        if recent_note:
            summary['documentation_stats']['last_progress_note'] = recent_note[0]['created_date']
        
        recent_plan = self.db.execute_query(
            "SELECT created_date FROM treatment_plans WHERE patient_id = ? ORDER BY created_date DESC LIMIT 1",
            (patient_id,)
        )
        
        if recent_plan:
            summary['documentation_stats']['last_treatment_plan'] = recent_plan[0]['created_date']
        
        return summary
    
    def validate_documentation_completeness(self, patient_id: int) -> Dict[str, Any]:
        """Validate documentation completeness and quality"""
        
        validation = {
            'patient_id': patient_id,
            'validation_date': datetime.now().isoformat(),
            'completeness_score': 0,
            'missing_documentation': [],
            'quality_issues': [],
            'recommendations': []
        }
        
        completeness_checks = []
        
        # Check for initial assessment documentation
        initial_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date ASC LIMIT 1",
            (patient_id,)
        )
        
        if initial_assessments:
            completeness_checks.append(('Initial Assessment', True))
        else:
            completeness_checks.append(('Initial Assessment', False))
            validation['missing_documentation'].append('Initial clinical assessment')
        
        # Check for treatment plan
        treatment_plans = self.db.execute_query(
            "SELECT * FROM treatment_plans WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        if treatment_plans:
            completeness_checks.append(('Active Treatment Plan', True))
        else:
            completeness_checks.append(('Active Treatment Plan', False))
            validation['missing_documentation'].append('Current treatment plan')
        
        # Check for recent progress notes
        recent_notes = self.db.execute_query(
            "SELECT * FROM progress_notes WHERE patient_id = ? AND created_date > ?",
            (patient_id, (datetime.now() - timedelta(days=14)).isoformat())
        )
        
        if recent_notes:
            completeness_checks.append(('Recent Progress Notes', True))
        else:
            completeness_checks.append(('Recent Progress Notes', False))
            validation['missing_documentation'].append('Progress notes within last 14 days')
        
        # Check for goal documentation
        active_goals = self.db.execute_query(
            "SELECT * FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
            (patient_id,)
        )
        
        if active_goals:
            completeness_checks.append(('Treatment Goals', True))
        else:
            completeness_checks.append(('Treatment Goals', False))
            validation['missing_documentation'].append('Active treatment goals')
        
        # Check for crisis/safety documentation if indicated
        crisis_alerts = self.db.execute_query(
            "SELECT * FROM crisis_alerts WHERE patient_id = ? AND resolved = FALSE",
            (patient_id,)
        )
        
        if crisis_alerts:
            safety_plans = self.db.execute_query(
                "SELECT * FROM crisis_plans WHERE patient_id = ? AND active = TRUE",
                (patient_id,)
            )
            
            if safety_plans:
                completeness_checks.append(('Safety Planning', True))
            else:
                completeness_checks.append(('Safety Planning', False))
                validation['missing_documentation'].append('Safety plan for active crisis alerts')
        
        # Calculate completeness score
        completed_items = sum(1 for _, status in completeness_checks if status)
        total_items = len(completeness_checks)
        validation['completeness_score'] = (completed_items / total_items) * 100 if total_items > 0 else 0
        
        # Quality checks
        if recent_notes:
            for note in recent_notes:
                if not note.get('subjective') or len(note['subjective'].strip()) < 20:
                    validation['quality_issues'].append('Progress note subjective section too brief')
                if not note.get('plan') or len(note['plan'].strip()) < 20:
                    validation['quality_issues'].append('Progress note plan section too brief')
        
        if treatment_plans:
            for plan in treatment_plans:
                if not plan.get('treatment_goals') or plan['treatment_goals'] == '[]':
                    validation['quality_issues'].append('Treatment plan lacks specific goals')
        
        # Generate recommendations
        if validation['completeness_score'] < 80:
            validation['recommendations'].append('Complete missing documentation items to meet clinical standards')
        
        if validation['quality_issues']:
            validation['recommendations'].append('Address documentation quality issues for better clinical care')
        
        if not validation['missing_documentation'] and not validation['quality_issues']:
            validation['recommendations'].append('Documentation meets completeness and quality standards')
        
        return validation
    
    def export_patient_documentation(self, patient_id: int, format_type: str = "text") -> str:
        """Export all patient documentation in specified format"""
        
        # Get patient info
        patient_data = self.db.execute_query(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        if not patient_data:
            raise ValueError(f"Patient {patient_id} not found")
        
        patient = patient_data[0]
        
        if format_type == "text":
            return self._export_as_text(patient_id, patient)
        elif format_type == "json":
            return self._export_as_json(patient_id)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_as_text(self, patient_id: int, patient: Dict[str, Any]) -> str:
        """Export documentation as formatted text"""
        
        export_text = f"""
CLINICAL DOCUMENTATION EXPORT
Patient: {patient['name']}
Patient ID: {patient_id}
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*80}
PROGRESS NOTES
{'='*80}
"""
        
        # Progress notes
        notes = self.db.execute_query(
            "SELECT * FROM progress_notes WHERE patient_id = ? ORDER BY created_date DESC",
            (patient_id,)
        )
        
        for note in notes:
            export_text += f"""
Date: {note['created_date'][:10]}
Type: {note['note_type']}
Created by: {note['created_by']}

SUBJECTIVE:
{note.get('subjective', 'Not documented')}

OBJECTIVE:
{note.get('objective', 'Not documented')}

ASSESSMENT:
{note.get('assessment', 'Not documented')}

PLAN:
{note.get('plan', 'Not documented')}

{'-'*40}
"""
        
        # Treatment plans
        export_text += f"""
{'='*80}
TREATMENT PLANS
{'='*80}
"""
        
        plans = self.db.execute_query(
            "SELECT * FROM treatment_plans WHERE patient_id = ? ORDER BY created_date DESC",
            (patient_id,)
        )
        
        for plan in plans:
            export_text += f"""
Plan Name: {plan['plan_name']}
Created: {plan['created_date'][:10]}
Status: {plan['status']}
Primary Modality: {plan['primary_modality']}
Estimated Duration: {plan['estimated_duration']} weeks
Session Frequency: {plan['session_frequency']}

Target Symptoms:
{', '.join(json.loads(plan.get('target_symptoms', '[]')))}

Treatment Goals:
"""
            
            goals = json.loads(plan.get('treatment_goals', '[]'))
            for i, goal in enumerate(goals, 1):
                export_text += f"{i}. {goal.get('description', 'No description')}\n"
            
            export_text += f"\n{'-'*40}\n"
        
        # Clinical reports
        export_text += f"""
{'='*80}
CLINICAL REPORTS
{'='*80}
"""
        
        reports = self.db.execute_query(
            "SELECT * FROM clinical_reports WHERE patient_id = ? ORDER BY generated_date DESC",
            (patient_id,)
        )
        
        for report in reports:
            export_text += f"""
Report Type: {report['report_type']}
Title: {report['title']}
Generated: {report['generated_date'][:10]}

Summary:
{report.get('summary', 'No summary available')}

Key Findings:
"""
            
            findings = json.loads(report.get('findings', '[]'))
            for finding in findings:
                export_text += f"• {finding}\n"
            
            export_text += "\nRecommendations:\n"
            recommendations = json.loads(report.get('recommendations', '[]'))
            for rec in recommendations:
                export_text += f"• {rec}\n"
            
            export_text += f"\n{'-'*40}\n"
        
        return export_text
    
    def _export_as_json(self, patient_id: int) -> str:
        """Export documentation as JSON"""
        from database import DatabaseManager
        
        # Use the database's export function which is more comprehensive
        patient_data = self.db.export_patient_data(patient_id)
        return json.dumps(patient_data, indent=2, default=str)


# Utility functions
def create_soap_note_from_session(db: DatabaseManager, session_id: int) -> Dict[str, Any]:
    """Create SOAP note from session data (helper function)"""
    doc_system = DocumentationSystem(db)
    
    # Get session data
    session_data = db.execute_query("SELECT * FROM sessions WHERE id = ?", (session_id,))
    if not session_data:
        raise ValueError(f"Session {session_id} not found")
    
    session = session_data[0]
    soap_note = doc_system.generate_auto_soap_note(session['patient_id'], session_id)
    
    return {
        'soap_note_id': soap_note.id,
        'patient_id': soap_note.patient_id,
        'session_id': soap_note.session_id,
        'created_date': soap_note.created_date
    }


def generate_treatment_summary(db: DatabaseManager, patient_id: int) -> str:
    """Generate quick treatment summary (helper function)"""
    doc_system = DocumentationSystem(db)
    
    # Get basic treatment info
    sessions = db.execute_query(
        "SELECT COUNT(*) as count FROM sessions WHERE patient_id = ?", (patient_id,)
    )
    
    diagnoses = db.execute_query(
        "SELECT diagnosis_name FROM diagnoses WHERE patient_id = ? AND status = 'active'",
        (patient_id,)
    )
    
    goals = db.execute_query(
        "SELECT AVG(current_progress) as avg_progress FROM treatment_goals WHERE patient_id = ? AND status = 'active'",
        (patient_id,)
    )
    
    session_count = sessions[0]['count'] if sessions else 0
    avg_progress = goals[0]['avg_progress'] if goals and goals[0]['avg_progress'] else 0
    
    summary = f"""
TREATMENT SUMMARY
Patient ID: {patient_id}
Total Sessions: {session_count}
Active Diagnoses: {', '.join([d['diagnosis_name'] for d in diagnoses]) if diagnoses else 'None'}
Average Goal Progress: {avg_progress:.0f}%
"""
    
    return summary.strip()


# Test function
def main():
    """Test documentation system functionality"""
    from database import DatabaseManager
    
    print("Testing Documentation System...")
    
    db = DatabaseManager(":memory:")
    doc_system = DocumentationSystem(db)
    
    # Create test patient
    patient_id = db.execute_update(
        "INSERT INTO patients (name, date_of_birth, preferred_therapy_mode) VALUES (?, ?, ?)",
        ("Test Patient", "1990-01-01", "CBT")
    )
    
    # Create test session
    session_id = db.execute_update(
        "INSERT INTO sessions (patient_id, session_type, mood_before, mood_after, therapist_notes) VALUES (?, ?, ?, ?, ?)",
        (patient_id, "CBT", 4, 7, "Patient engaged well in session")
    )
    
    print(f"Created test patient {patient_id} and session {session_id}")
    
    # Test SOAP note generation
    print("\n1. Testing SOAP note generation...")
    soap_note = doc_system.generate_auto_soap_note(patient_id, session_id)
    print(f"Generated SOAP note ID: {soap_note.id}")
    print(f"Subjective: {soap_note.subjective[:50]}...")
    
    # Test treatment plan creation
    print("\n2. Testing treatment plan creation...")
    treatment_plan = doc_system.create_treatment_plan(
        patient_id,
        presenting_problems=["Depression", "Anxiety"],
        estimated_duration=12
    )
    print(f"Generated treatment plan ID: {treatment_plan.id}")
    print(f"Number of goals: {len(treatment_plan.treatment_goals)}")
    
    # Test progress report
    print("\n3. Testing progress report...")
    try:
        progress_report = doc_system.generate_progress_report(patient_id, days=30)
        print(f"Generated progress report ID: {progress_report.id}")
        print(f"Number of findings: {len(progress_report.findings)}")
    except Exception as e:
        print(f"Progress report generation skipped: {e}")
    
    # Test documentation validation
    print("\n4. Testing documentation validation...")
    validation = doc_system.validate_documentation_completeness(patient_id)
    print(f"Completeness score: {validation['completeness_score']:.0f}%")
    print(f"Missing items: {len(validation['missing_documentation'])}")
    
    print("\nDocumentation system testing completed!")


if __name__ == "__main__":
    main()