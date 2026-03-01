#!/usr/bin/env python3
"""
AI Therapy System - Data Models and Validation
Comprehensive data models with validation for all system entities
"""

import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
from abc import ABC, abstractmethod


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    IMMINENT = "imminent"


class TherapyModality(Enum):
    """Therapy modality options"""
    CBT = "CBT"
    DBT = "DBT"
    ACT = "ACT"
    PSYCHODYNAMIC = "psychodynamic"
    INTEGRATIVE = "integrative"


class Gender(Enum):
    """Gender options"""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class DiagnosisStatus(Enum):
    """Diagnosis status options"""
    ACTIVE = "active"
    IN_REMISSION = "in_remission"
    RESOLVED = "resolved"
    RULE_OUT = "rule_out"


class SessionType(Enum):
    """Session type options"""
    CBT = "CBT"
    DBT = "DBT"
    ACT = "ACT"
    PSYCHODYNAMIC = "psychodynamic"
    ASSESSMENT = "assessment"
    CRISIS = "crisis"
    CONSULTATION = "consultation"


class AssessmentType(Enum):
    """Assessment type options"""
    PHQ9 = "PHQ9"
    GAD7 = "GAD7"
    PCL5 = "PCL5"
    ORS = "ORS"
    SRS = "SRS"
    CUSTOM = "custom"


# Base Model Class
@dataclass
class BaseModel(ABC):
    """Base model class with common functionality"""
    
    id: Optional[int] = None
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Post-initialization validation"""
        self.validate()
    
    @abstractmethod
    def validate(self) -> None:
        """Validate model data - must be implemented by subclasses"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert model to JSON string"""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    def update_timestamp(self) -> None:
        """Update the last_updated timestamp"""
        self.last_updated = datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from dictionary"""
        return cls(**data)


# Patient Model
@dataclass
class Patient(BaseModel):
    """Patient data model with comprehensive validation"""
    
    name: str = ""
    date_of_birth: str = ""
    gender: str = Gender.PREFER_NOT_TO_SAY.value
    contact_info: str = ""
    emergency_contact: str = ""
    risk_level: str = RiskLevel.LOW.value
    preferred_therapy_mode: str = TherapyModality.CBT.value
    notes: str = ""
    active: bool = True
    
    # Additional patient information
    insurance_info: str = ""
    referring_provider: str = ""
    primary_language: str = "English"
    cultural_background: str = ""
    occupation: str = ""
    education_level: str = ""
    relationship_status: str = ""
    living_situation: str = ""
    
    # Treatment preferences
    session_preferences: Dict[str, Any] = field(default_factory=dict)
    communication_preferences: Dict[str, Any] = field(default_factory=dict)
    treatment_history: List[str] = field(default_factory=list)
    medication_history: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate patient data"""
        errors = []
        
        # Name validation
        if not self.name or len(self.name.strip()) < 2:
            errors.append("Name must be at least 2 characters long")
        
        if len(self.name) > 100:
            errors.append("Name must be less than 100 characters")
        
        # Date of birth validation
        if self.date_of_birth:
            if not self._is_valid_date(self.date_of_birth):
                errors.append("Invalid date of birth format. Use YYYY-MM-DD")
            else:
                # Check if date is reasonable (not in future, not too old)
                try:
                    birth_date = datetime.fromisoformat(self.date_of_birth).date()
                    today = date.today()
                    
                    if birth_date > today:
                        errors.append("Date of birth cannot be in the future")
                    
                    age = today.year - birth_date.year
                    if age > 120:
                        errors.append("Date of birth indicates unrealistic age")
                    
                except ValueError:
                    errors.append("Invalid date of birth format")
        
        # Gender validation
        valid_genders = [g.value for g in Gender]
        if self.gender and self.gender not in valid_genders:
            errors.append(f"Gender must be one of: {', '.join(valid_genders)}")
        
        # Risk level validation
        valid_risk_levels = [r.value for r in RiskLevel]
        if self.risk_level not in valid_risk_levels:
            errors.append(f"Risk level must be one of: {', '.join(valid_risk_levels)}")
        
        # Therapy modality validation
        valid_modalities = [m.value for m in TherapyModality]
        if self.preferred_therapy_mode not in valid_modalities:
            errors.append(f"Therapy modality must be one of: {', '.join(valid_modalities)}")
        
        # Contact info validation (if provided)
        if self.contact_info and not self._is_valid_contact_info(self.contact_info):
            errors.append("Contact info should include valid email or phone number")
        
        if errors:
            raise ValidationError(f"Patient validation errors: {'; '.join(errors)}")
    
    def _is_valid_date(self, date_string: str) -> bool:
        """Validate date format"""
        try:
            datetime.fromisoformat(date_string)
            return True
        except ValueError:
            return False
    
    def _is_valid_contact_info(self, contact: str) -> bool:
        """Basic validation for contact information"""
        # Check for email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.search(email_pattern, contact):
            return True
        
        # Check for phone pattern (basic)
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        if re.search(phone_pattern, contact):
            return True
        
        return False
    
    def calculate_age(self) -> Optional[int]:
        """Calculate patient's current age"""
        if not self.date_of_birth:
            return None
        
        try:
            birth_date = datetime.fromisoformat(self.date_of_birth).date()
            today = date.today()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except ValueError:
            return None
    
    def get_display_name(self) -> str:
        """Get formatted display name"""
        return self.name.strip().title()


# Session Model
@dataclass
class Session(BaseModel):
    """Therapy session data model"""
    
    patient_id: int = 0
    session_date: str = field(default_factory=lambda: datetime.now().isoformat())
    session_type: str = SessionType.CBT.value
    duration: int = 50  # minutes
    mood_before: Optional[int] = None  # 1-10 scale
    mood_after: Optional[int] = None   # 1-10 scale
    energy_before: Optional[int] = None  # 1-10 scale
    energy_after: Optional[int] = None   # 1-10 scale
    anxiety_before: Optional[int] = None  # 1-10 scale
    anxiety_after: Optional[int] = None   # 1-10 scale
    
    # Session content
    interventions_used: List[str] = field(default_factory=list)
    homework_assigned: str = ""
    homework_reviewed: bool = False
    crisis_flags: List[str] = field(default_factory=list)
    therapist_notes: str = ""
    patient_feedback: str = ""
    
    # Session structure tracking
    session_phase: str = "completed"  # opening, main_work, closing, completed
    completed: bool = True
    
    # Clinical observations
    mental_status_observations: Dict[str, Any] = field(default_factory=dict)
    risk_assessment_conducted: bool = False
    safety_plan_reviewed: bool = False
    
    # Session quality metrics
    therapeutic_alliance_rating: Optional[int] = None  # 1-10 scale
    session_satisfaction: Optional[int] = None  # 1-10 scale
    
    def validate(self) -> None:
        """Validate session data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Session type validation
        valid_session_types = [s.value for s in SessionType]
        if self.session_type not in valid_session_types:
            errors.append(f"Session type must be one of: {', '.join(valid_session_types)}")
        
        # Duration validation
        if self.duration <= 0 or self.duration > 300:  # 5 hours max
            errors.append("Session duration must be between 1 and 300 minutes")
        
        # Mood rating validations
        for rating_field in ['mood_before', 'mood_after', 'energy_before', 'energy_after', 
                           'anxiety_before', 'anxiety_after', 'therapeutic_alliance_rating', 'session_satisfaction']:
            rating_value = getattr(self, rating_field)
            if rating_value is not None and (rating_value < 1 or rating_value > 10):
                errors.append(f"{rating_field} must be between 1 and 10")
        
        # Date validation
        if not self._is_valid_datetime(self.session_date):
            errors.append("Invalid session date format")
        
        if errors:
            raise ValidationError(f"Session validation errors: {'; '.join(errors)}")
    
    def _is_valid_datetime(self, datetime_string: str) -> bool:
        """Validate datetime format"""
        try:
            datetime.fromisoformat(datetime_string)
            return True
        except ValueError:
            return False
    
    def calculate_mood_change(self) -> Optional[int]:
        """Calculate mood change from before to after session"""
        if self.mood_before is not None and self.mood_after is not None:
            return self.mood_after - self.mood_before
        return None
    
    def calculate_energy_change(self) -> Optional[int]:
        """Calculate energy change from before to after session"""
        if self.energy_before is not None and self.energy_after is not None:
            return self.energy_after - self.energy_before
        return None
    
    def calculate_anxiety_change(self) -> Optional[int]:
        """Calculate anxiety change from before to after session"""
        if self.anxiety_before is not None and self.anxiety_after is not None:
            return self.anxiety_before - self.anxiety_after  # Negative change is improvement
        return None
    
    def get_session_duration_formatted(self) -> str:
        """Get formatted session duration"""
        hours = self.duration // 60
        minutes = self.duration % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


# Assessment Model
@dataclass
class Assessment(BaseModel):
    """Assessment data model with comprehensive scoring"""
    
    patient_id: int = 0
    session_id: Optional[int] = None
    assessment_type: str = AssessmentType.PHQ9.value
    assessment_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Assessment responses and scoring
    questions_responses: Dict[str, Any] = field(default_factory=dict)
    total_score: int = 0
    subscale_scores: Dict[str, int] = field(default_factory=dict)
    severity_level: str = ""
    percentile_rank: Optional[float] = None
    
    # Clinical interpretation
    interpretation: str = ""
    clinical_significance: bool = False
    change_from_baseline: Optional[int] = None
    reliable_change_index: Optional[float] = None
    
    # Administration details
    administered_by: str = "AI_System"
    administration_method: str = "self_report"  # self_report, clinician_administered, observer_rated
    completion_time_minutes: Optional[int] = None
    
    # Quality indicators
    response_consistency: Optional[float] = None
    missing_responses: List[str] = field(default_factory=list)
    validity_flags: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate assessment data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Assessment type validation
        valid_assessment_types = [a.value for a in AssessmentType]
        if self.assessment_type not in valid_assessment_types:
            errors.append(f"Assessment type must be one of: {', '.join(valid_assessment_types)}")
        
        # Score validation based on assessment type
        score_ranges = {
            AssessmentType.PHQ9.value: (0, 27),
            AssessmentType.GAD7.value: (0, 21),
            AssessmentType.PCL5.value: (0, 80),
            AssessmentType.ORS.value: (0, 40),
            AssessmentType.SRS.value: (0, 40)
        }
        
        if self.assessment_type in score_ranges:
            min_score, max_score = score_ranges[self.assessment_type]
            if not (min_score <= self.total_score <= max_score):
                errors.append(f"Total score for {self.assessment_type} must be between {min_score} and {max_score}")
        
        # Date validation
        if not self._is_valid_datetime(self.assessment_date):
            errors.append("Invalid assessment date format")
        
        # Completion time validation
        if self.completion_time_minutes is not None and (self.completion_time_minutes < 1 or self.completion_time_minutes > 120):
            errors.append("Completion time must be between 1 and 120 minutes")
        
        if errors:
            raise ValidationError(f"Assessment validation errors: {'; '.join(errors)}")
    
    def _is_valid_datetime(self, datetime_string: str) -> bool:
        """Validate datetime format"""
        try:
            datetime.fromisoformat(datetime_string)
            return True
        except ValueError:
            return False
    
    def calculate_severity_level(self) -> str:
        """Calculate severity level based on assessment type and score"""
        severity_mappings = {
            AssessmentType.PHQ9.value: {
                (0, 4): "Minimal",
                (5, 9): "Mild",
                (10, 14): "Moderate",
                (15, 19): "Moderately Severe",
                (20, 27): "Severe"
            },
            AssessmentType.GAD7.value: {
                (0, 4): "Minimal",
                (5, 9): "Mild",
                (10, 14): "Moderate",
                (15, 21): "Severe"
            },
            AssessmentType.PCL5.value: {
                (0, 32): "Below Threshold",
                (33, 49): "Probable PTSD",
                (50, 80): "High Probability PTSD"
            }
        }
        
        if self.assessment_type in severity_mappings:
            mapping = severity_mappings[self.assessment_type]
            for (min_score, max_score), severity in mapping.items():
                if min_score <= self.total_score <= max_score:
                    return severity
        
        return "Unknown"
    
    def is_clinically_significant(self) -> bool:
        """Determine if score indicates clinical significance"""
        clinical_thresholds = {
            AssessmentType.PHQ9.value: 10,
            AssessmentType.GAD7.value: 10,
            AssessmentType.PCL5.value: 33,
            AssessmentType.ORS.value: 25,  # Below this indicates distress
            AssessmentType.SRS.value: 36   # Below this indicates alliance issues
        }
        
        if self.assessment_type in clinical_thresholds:
            threshold = clinical_thresholds[self.assessment_type]
            if self.assessment_type in [AssessmentType.ORS.value, AssessmentType.SRS.value]:
                return self.total_score < threshold  # Lower scores indicate problems
            else:
                return self.total_score >= threshold  # Higher scores indicate problems
        
        return False


# Diagnosis Model
@dataclass
class Diagnosis(BaseModel):
    """Diagnosis data model with DSM-5 compliance"""
    
    patient_id: int = 0
    diagnosis_code: str = ""  # ICD-10 or DSM-5 code
    diagnosis_name: str = ""
    category: str = ""  # e.g., "Depressive Disorders", "Anxiety Disorders"
    
    # Clinical details
    severity: str = ""  # mild, moderate, severe
    specifiers: List[str] = field(default_factory=list)
    date_diagnosed: str = field(default_factory=lambda: datetime.now().isoformat())
    date_resolved: Optional[str] = None
    status: str = DiagnosisStatus.ACTIVE.value
    
    # Supporting information
    supporting_criteria: Dict[str, Any] = field(default_factory=dict)
    differential_diagnoses: List[str] = field(default_factory=list)
    comorbidities: List[str] = field(default_factory=list)
    
    # Clinical documentation
    notes: str = ""
    diagnosed_by: str = "AI_System"
    confidence_level: Optional[float] = None  # 0.0 to 1.0
    
    # Treatment implications
    recommended_treatments: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    prognosis: str = ""
    
    def validate(self) -> None:
        """Validate diagnosis data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Diagnosis name validation
        if not self.diagnosis_name or len(self.diagnosis_name.strip()) < 3:
            errors.append("Diagnosis name must be at least 3 characters long")
        
        # Status validation
        valid_statuses = [s.value for s in DiagnosisStatus]
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Date validation
        if not self._is_valid_date(self.date_diagnosed):
            errors.append("Invalid date diagnosed format")
        
        if self.date_resolved and not self._is_valid_date(self.date_resolved):
            errors.append("Invalid date resolved format")
        
        # Confidence level validation
        if self.confidence_level is not None and (self.confidence_level < 0.0 or self.confidence_level > 1.0):
            errors.append("Confidence level must be between 0.0 and 1.0")
        
        # Severity validation
        valid_severities = ["mild", "moderate", "severe", "in_partial_remission", "in_full_remission"]
        if self.severity and self.severity not in valid_severities:
            errors.append(f"Severity must be one of: {', '.join(valid_severities)}")
        
        if errors:
            raise ValidationError(f"Diagnosis validation errors: {'; '.join(errors)}")
    
    def _is_valid_date(self, date_string: str) -> bool:
        """Validate date format"""
        try:
            datetime.fromisoformat(date_string)
            return True
        except ValueError:
            return False
    
    def is_active(self) -> bool:
        """Check if diagnosis is currently active"""
        return self.status == DiagnosisStatus.ACTIVE.value
    
    def days_since_diagnosis(self) -> int:
        """Calculate days since diagnosis"""
        try:
            diagnosis_date = datetime.fromisoformat(self.date_diagnosed)
            return (datetime.now() - diagnosis_date).days
        except ValueError:
            return 0


# Treatment Goal Model
@dataclass
class TreatmentGoal(BaseModel):
    """Treatment goal data model with SMART goal structure"""
    
    patient_id: int = 0
    goal_type: str = "symptom"  # symptom, functional, behavioral, interpersonal, cognitive
    goal_description: str = ""
    
    # SMART goal components
    specific_description: str = ""
    measurable_criteria: str = ""
    achievable_rationale: str = ""
    relevant_connection: str = ""
    time_bound_deadline: str = ""
    
    # Progress tracking
    target_date: str = ""
    current_progress: int = 0  # 0-100%
    measurement_criteria: str = ""
    status: str = "active"  # active, achieved, modified, discontinued, on_hold
    
    # Priority and difficulty
    priority_level: int = 2  # 1=low, 2=medium, 3=high
    difficulty_level: int = 2  # 1=easy, 2=moderate, 3=challenging, 4=difficult, 5=very_difficult
    
    # Progress milestones
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Barriers and strategies
    identified_barriers: List[str] = field(default_factory=list)
    coping_strategies: List[str] = field(default_factory=list)
    support_needed: List[str] = field(default_factory=list)
    
    # Progress notes
    progress_notes: List[Dict[str, str]] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate treatment goal data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Goal description validation
        if not self.goal_description or len(self.goal_description.strip()) < 10:
            errors.append("Goal description must be at least 10 characters long")
        
        # Progress validation
        if not (0 <= self.current_progress <= 100):
            errors.append("Current progress must be between 0 and 100")
        
        # Priority level validation
        if not (1 <= self.priority_level <= 3):
            errors.append("Priority level must be between 1 and 3")
        
        # Difficulty level validation
        if not (1 <= self.difficulty_level <= 5):
            errors.append("Difficulty level must be between 1 and 5")
        
        # Status validation
        valid_statuses = ["active", "achieved", "modified", "discontinued", "on_hold"]
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Goal type validation
        valid_goal_types = ["symptom", "functional", "behavioral", "interpersonal", "cognitive"]
        if self.goal_type not in valid_goal_types:
            errors.append(f"Goal type must be one of: {', '.join(valid_goal_types)}")
        
        # Date validation
        if self.target_date and not self._is_valid_date(self.target_date):
            errors.append("Invalid target date format")
        
        if errors:
            raise ValidationError(f"Treatment goal validation errors: {'; '.join(errors)}")
    
    def _is_valid_date(self, date_string: str) -> bool:
        """Validate date format"""
        try:
            datetime.fromisoformat(date_string)
            return True
        except ValueError:
            return False
    
    def is_completed(self) -> bool:
        """Check if goal is completed"""
        return self.status == "achieved" or self.current_progress >= 100
    
    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        if not self.target_date or self.is_completed():
            return False
        
        try:
            target = datetime.fromisoformat(self.target_date)
            return datetime.now() > target
        except ValueError:
            return False
    
    def calculate_progress_rate(self) -> Optional[float]:
        """Calculate progress rate (progress per day since creation)"""
        try:
            created = datetime.fromisoformat(self.created_date)
            days_elapsed = (datetime.now() - created).days
            
            if days_elapsed > 0:
                return self.current_progress / days_elapsed
            
        except ValueError:
            pass
        
        return None
    
    def add_progress_note(self, note: str, progress_update: int = None) -> None:
        """Add a progress note"""
        progress_entry = {
            'date': datetime.now().isoformat(),
            'note': note,
            'progress_at_time': progress_update or self.current_progress
        }
        self.progress_notes.append(progress_entry)
        
        if progress_update is not None:
            self.current_progress = progress_update
        
        self.update_timestamp()


# Homework Assignment Model
@dataclass
class HomeworkAssignment(BaseModel):
    """Homework assignment data model"""
    
    patient_id: int = 0
    session_id: Optional[int] = None
    assignment_type: str = ""
    description: str = ""
    instructions: str = ""
    
    # Assignment details
    due_date: str = ""
    assigned_date: str = field(default_factory=lambda: datetime.now().isoformat())
    estimated_time_minutes: int = 30
    difficulty_level: int = 2  # 1-5 scale
    
    # Completion tracking
    completed: bool = False
    completion_date: Optional[str] = None
    completion_notes: str = ""
    time_spent_minutes: Optional[int] = None
    
    # Effectiveness ratings
    effectiveness_rating: Optional[int] = None  # 1-5 scale
    difficulty_rating: Optional[int] = None  # 1-5 scale (actual difficulty)
    helpfulness_rating: Optional[int] = None  # 1-5 scale
    
    # Progress tracking
    progress_entries: List[Dict[str, Any]] = field(default_factory=list)
    barriers_encountered: List[str] = field(default_factory=list)
    insights_gained: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate homework assignment data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Description validation
        if not self.description or len(self.description.strip()) < 5:
            errors.append("Description must be at least 5 characters long")
        
        # Time validation
        if self.estimated_time_minutes <= 0 or self.estimated_time_minutes > 480:  # 8 hours max
            errors.append("Estimated time must be between 1 and 480 minutes")
        
        if self.time_spent_minutes is not None and (self.time_spent_minutes < 0 or self.time_spent_minutes > 480):
            errors.append("Time spent must be between 0 and 480 minutes")
        
        # Difficulty level validation
        if not (1 <= self.difficulty_level <= 5):
            errors.append("Difficulty level must be between 1 and 5")
        
        # Rating validations
        for rating_field in ['effectiveness_rating', 'difficulty_rating', 'helpfulness_rating']:
            rating_value = getattr(self, rating_field)
            if rating_value is not None and not (1 <= rating_value <= 5):
                errors.append(f"{rating_field} must be between 1 and 5")
        
        # Date validations
        if self.due_date and not self._is_valid_date(self.due_date):
            errors.append("Invalid due date format")
        
        if self.completion_date and not self._is_valid_date(self.completion_date):
            errors.append("Invalid completion date format")
        
        if errors:
            raise ValidationError(f"Homework assignment validation errors: {'; '.join(errors)}")
    
    def _is_valid_date(self, date_string: str) -> bool:
        """Validate date format"""
        try:
            datetime.fromisoformat(date_string)
            return True
        except ValueError:
            return False
    
    def is_overdue(self) -> bool:
        """Check if assignment is overdue"""
        if not self.due_date or self.completed:
            return False
        
        try:
            due = datetime.fromisoformat(self.due_date)
            return datetime.now() > due
        except ValueError:
            return False
    
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date"""
        if not self.due_date:
            return None
        
        try:
            due = datetime.fromisoformat(self.due_date)
            delta = due - datetime.now()
            return delta.days
        except ValueError:
            return None
    
    def mark_completed(self, completion_notes: str = "", time_spent: int = None) -> None:
        """Mark assignment as completed"""
        self.completed = True
        self.completion_date = datetime.now().isoformat()
        self.completion_notes = completion_notes
        if time_spent is not None:
            self.time_spent_minutes = time_spent
        self.update_timestamp()


# Progress Note Model
@dataclass
class ProgressNote(BaseModel):
    """Progress note data model (SOAP format)"""
    
    patient_id: int = 0
    session_id: Optional[int] = None
    note_type: str = "SOAP"  # SOAP, progress, crisis, assessment, treatment_plan
    
    # SOAP components
    subjective: str = ""  # Patient's reported experience
    objective: str = ""   # Observable behaviors and facts
    assessment: str = ""  # Clinical assessment and analysis
    plan: str = ""       # Treatment plan and next steps
    
    # Documentation details
    created_by: str = "AI_Therapist"
    signed: bool = False
    last_modified: Optional[str] = None
    
    # Clinical indicators
    risk_factors_noted: List[str] = field(default_factory=list)
    interventions_used: List[str] = field(default_factory=list)
    patient_response: str = ""
    
    def validate(self) -> None:
        """Validate progress note data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Note type validation
        valid_note_types = ["SOAP", "progress", "crisis", "assessment", "treatment_plan", "discharge"]
        if self.note_type not in valid_note_types:
            errors.append(f"Note type must be one of: {', '.join(valid_note_types)}")
        
        # SOAP components validation (if SOAP note)
        if self.note_type == "SOAP":
            if not self.subjective or len(self.subjective.strip()) < 10:
                errors.append("Subjective section must be at least 10 characters for SOAP notes")
            
            if not self.objective or len(self.objective.strip()) < 10:
                errors.append("Objective section must be at least 10 characters for SOAP notes")
            
            if not self.assessment or len(self.assessment.strip()) < 10:
                errors.append("Assessment section must be at least 10 characters for SOAP notes")
            
            if not self.plan or len(self.plan.strip()) < 10:
                errors.append("Plan section must be at least 10 characters for SOAP notes")
        
        if errors:
            raise ValidationError(f"Progress note validation errors: {'; '.join(errors)}")
    
    def get_word_count(self) -> Dict[str, int]:
        """Get word count for each section"""
        return {
            'subjective': len(self.subjective.split()),
            'objective': len(self.objective.split()),
            'assessment': len(self.assessment.split()),
            'plan': len(self.plan.split()),
            'total': len((self.subjective + ' ' + self.objective + ' ' + self.assessment + ' ' + self.plan).split())
        }
    
    def sign_note(self, signed_by: str = None) -> None:
        """Sign the progress note"""
        self.signed = True
        self.last_modified = datetime.now().isoformat()
        if signed_by:
            self.created_by = signed_by
        self.update_timestamp()


# Treatment Plan Model
@dataclass
class TreatmentPlan(BaseModel):
    """Treatment plan data model"""
    
    patient_id: int = 0
    plan_name: str = ""
    primary_modality: str = TherapyModality.CBT.value
    
    # Plan components
    presenting_problems: List[str] = field(default_factory=list)
    target_symptoms: List[str] = field(default_factory=list)
    treatment_goals: List[int] = field(default_factory=list)  # Goal IDs
    interventions_planned: List[str] = field(default_factory=list)
    
    # Timeline and structure
    estimated_duration_weeks: int = 12
    session_frequency: str = "weekly"  # weekly, biweekly, monthly
    total_sessions_planned: int = 12
    
    # Clinical details
    prognosis: str = ""
    discharge_criteria: List[str] = field(default_factory=list)
    contraindications: List[str] = field(default_factory=list)
    
    # Status tracking
    status: str = "active"  # active, completed, modified, on_hold, discontinued
    last_reviewed: Optional[str] = None
    next_review_date: Optional[str] = None
    
    # Outcome tracking
    baseline_assessments: Dict[str, int] = field(default_factory=dict)
    progress_markers: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate treatment plan data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Plan name validation
        if not self.plan_name or len(self.plan_name.strip()) < 3:
            errors.append("Plan name must be at least 3 characters long")
        
        # Modality validation
        valid_modalities = [m.value for m in TherapyModality]
        if self.primary_modality not in valid_modalities:
            errors.append(f"Primary modality must be one of: {', '.join(valid_modalities)}")
        
        # Duration validation
        if not (1 <= self.estimated_duration_weeks <= 104):  # 2 years max
            errors.append("Estimated duration must be between 1 and 104 weeks")
        
        if not (1 <= self.total_sessions_planned <= 200):
            errors.append("Total sessions planned must be between 1 and 200")
        
        # Status validation
        valid_statuses = ["active", "completed", "modified", "on_hold", "discontinued"]
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        # Session frequency validation
        valid_frequencies = ["weekly", "biweekly", "monthly", "as_needed"]
        if self.session_frequency not in valid_frequencies:
            errors.append(f"Session frequency must be one of: {', '.join(valid_frequencies)}")
        
        if errors:
            raise ValidationError(f"Treatment plan validation errors: {'; '.join(errors)}")
    
    def calculate_expected_completion_date(self) -> str:
        """Calculate expected completion date based on duration and frequency"""
        try:
            start_date = datetime.fromisoformat(self.created_date)
            
            if self.session_frequency == "weekly":
                completion_date = start_date + timedelta(weeks=self.estimated_duration_weeks)
            elif self.session_frequency == "biweekly":
                completion_date = start_date + timedelta(weeks=self.estimated_duration_weeks * 2)
            elif self.session_frequency == "monthly":
                completion_date = start_date + timedelta(weeks=self.estimated_duration_weeks * 4)
            else:  # as_needed
                completion_date = start_date + timedelta(weeks=self.estimated_duration_weeks)
            
            return completion_date.isoformat()
        except ValueError:
            return ""
    
    def is_due_for_review(self) -> bool:
        """Check if treatment plan is due for review"""
        if not self.next_review_date:
            return True  # No review date set, so it's overdue
        
        try:
            review_date = datetime.fromisoformat(self.next_review_date)
            return datetime.now() >= review_date
        except ValueError:
            return True


# Crisis Plan Model
@dataclass
class CrisisPlan(BaseModel):
    """Crisis intervention plan data model"""
    
    patient_id: int = 0
    
    # Crisis identification
    warning_signs: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    
    # Coping strategies
    internal_coping_strategies: List[str] = field(default_factory=list)
    external_supports: List[Dict[str, str]] = field(default_factory=list)  # name, phone, relationship
    professional_contacts: List[Dict[str, str]] = field(default_factory=list)  # name, phone, role
    
    # Environmental safety
    environmental_safety_steps: List[str] = field(default_factory=list)
    restricted_access_items: List[str] = field(default_factory=list)
    
    # Motivation and hope
    reasons_for_living: List[str] = field(default_factory=list)
    future_goals: List[str] = field(default_factory=list)
    
    # Plan status
    active: bool = True
    last_reviewed: Optional[str] = None
    next_review_date: Optional[str] = None
    
    def validate(self) -> None:
        """Validate crisis plan data"""
        errors = []
        
        # Patient ID validation
        if self.patient_id <= 0:
            errors.append("Patient ID must be a positive integer")
        
        # Ensure essential components are present
        if not self.warning_signs:
            errors.append("Warning signs must be specified")
        
        if not self.internal_coping_strategies:
            errors.append("At least one internal coping strategy must be specified")
        
        if not self.professional_contacts:
            errors.append("At least one professional contact must be specified")
        
        # Validate contact information structure
        for contact in self.external_supports + self.professional_contacts:
            if not isinstance(contact, dict) or 'name' not in contact or 'phone' not in contact:
                errors.append("Contacts must include name and phone number")
        
        if errors:
            raise ValidationError(f"Crisis plan validation errors: {'; '.join(errors)}")
    
    def add_support_contact(self, name: str, phone: str, relationship: str = "") -> None:
        """Add a support contact"""
        contact = {
            'name': name,
            'phone': phone,
            'relationship': relationship
        }
        self.external_supports.append(contact)
        self.update_timestamp()
    
    def add_professional_contact(self, name: str, phone: str, role: str = "") -> None:
        """Add a professional contact"""
        contact = {
            'name': name,
            'phone': phone,
            'role': role
        }
        self.professional_contacts.append(contact)
        self.update_timestamp()


# Model Factory and Utility Functions
class ModelFactory:
    """Factory class for creating model instances"""
    
    model_classes = {
        'patient': Patient,
        'session': Session,
        'assessment': Assessment,
        'diagnosis': Diagnosis,
        'treatment_goal': TreatmentGoal,
        'homework_assignment': HomeworkAssignment,
        'progress_note': ProgressNote,
        'treatment_plan': TreatmentPlan,
        'crisis_plan': CrisisPlan
    }
    
    @classmethod
    def create(cls, model_type: str, **kwargs) -> BaseModel:
        """Create model instance of specified type"""
        if model_type not in cls.model_classes:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(cls.model_classes.keys())}")
        
        model_class = cls.model_classes[model_type]
        return model_class(**kwargs)
    
    @classmethod
    def from_dict(cls, model_type: str, data: Dict[str, Any]) -> BaseModel:
        """Create model instance from dictionary"""
        if model_type not in cls.model_classes:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model_class = cls.model_classes[model_type]
        return model_class.from_dict(data)
    
    @classmethod
    def get_model_fields(cls, model_type: str) -> List[str]:
        """Get list of fields for a model type"""
        if model_type not in cls.model_classes:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model_class = cls.model_classes[model_type]
        return list(model_class.__dataclass_fields__.keys())


def validate_all_models() -> Dict[str, Any]:
    """Validate all model classes and return validation report"""
    validation_report = {
        'timestamp': datetime.now().isoformat(),
        'models_tested': 0,
        'validation_errors': {},
        'all_valid': True
    }
    
    for model_name, model_class in ModelFactory.model_classes.items():
        validation_report['models_tested'] += 1
        
        try:
            # Create instance with minimal valid data
            if model_name == 'patient':
                test_instance = model_class(name="Test Patient")
            elif model_name in ['session', 'assessment', 'diagnosis', 'treatment_goal', 
                               'homework_assignment', 'progress_note', 'treatment_plan', 'crisis_plan']:
                test_instance = model_class(patient_id=1)
            else:
                test_instance = model_class()
            
            # Validation passed if no exception raised
            validation_report[f'{model_name}_valid'] = True
            
        except ValidationError as e:
            validation_report['validation_errors'][model_name] = str(e)
            validation_report[f'{model_name}_valid'] = False
            validation_report['all_valid'] = False
        
        except Exception as e:
            validation_report['validation_errors'][model_name] = f"Unexpected error: {str(e)}"
            validation_report[f'{model_name}_valid'] = False
            validation_report['all_valid'] = False
    
    return validation_report


def create_sample_data() -> Dict[str, BaseModel]:
    """Create sample instances of all models for testing"""
    samples = {}
    
    # Sample Patient
    samples['patient'] = Patient(
        name="John Doe",
        date_of_birth="1990-05-15",
        gender=Gender.MALE.value,
        contact_info="john.doe@email.com",
        risk_level=RiskLevel.LOW.value,
        preferred_therapy_mode=TherapyModality.CBT.value,
        notes="Sample patient for testing purposes"
    )
    
    # Sample Session
    samples['session'] = Session(
        patient_id=1,
        session_type=SessionType.CBT.value,
        duration=50,
        mood_before=4,
        mood_after=6,
        interventions_used=["Cognitive Restructuring", "Homework Assignment"],
        therapist_notes="Patient engaged well in session, showed good insight"
    )
    
    # Sample Assessment
    samples['assessment'] = Assessment(
        patient_id=1,
        assessment_type=AssessmentType.PHQ9.value,
        total_score=12,
        severity_level="Moderate",
        interpretation="Moderate depression symptoms indicated"
    )
    
    # Sample Diagnosis
    samples['diagnosis'] = Diagnosis(
        patient_id=1,
        diagnosis_code="296.22",
        diagnosis_name="Major Depressive Disorder, Single Episode, Moderate",
        severity="moderate",
        status=DiagnosisStatus.ACTIVE.value,
        confidence_level=0.85
    )
    
    # Sample Treatment Goal
    samples['treatment_goal'] = TreatmentGoal(
        patient_id=1,
        goal_type="symptom",
        goal_description="Reduce depressive symptoms to mild range",
        specific_description="Decrease PHQ-9 score to 9 or below",
        measurable_criteria="PHQ-9 score ≤ 9 for two consecutive assessments",
        current_progress=30,
        priority_level=3
    )
    
    # Sample Homework Assignment
    samples['homework_assignment'] = HomeworkAssignment(
        patient_id=1,
        assignment_type="thought_record",
        description="Daily thought record practice",
        instructions="Complete thought record when experiencing negative emotions",
        due_date=(datetime.now() + timedelta(days=7)).isoformat(),
        estimated_time_minutes=20
    )
    
    # Sample Progress Note
    samples['progress_note'] = ProgressNote(
        patient_id=1,
        session_id=1,
        subjective="Patient reports feeling 'somewhat better' this week with improved sleep",
        objective="Patient appeared more energetic, maintained good eye contact throughout session",
        assessment="Moderate improvement in mood and energy. Depression symptoms decreasing.",
        plan="Continue CBT interventions, assign behavioral activation homework"
    )
    
    # Sample Treatment Plan
    samples['treatment_plan'] = TreatmentPlan(
        patient_id=1,
        plan_name="CBT for Depression",
        primary_modality=TherapyModality.CBT.value,
        presenting_problems=["Depression", "Low motivation"],
        estimated_duration_weeks=12,
        total_sessions_planned=12
    )
    
    # Sample Crisis Plan
    samples['crisis_plan'] = CrisisPlan(
        patient_id=1,
        warning_signs=["Hopeless thoughts", "Sleep problems", "Social isolation"],
        internal_coping_strategies=["Deep breathing", "Call a friend", "Take a walk"],
        reasons_for_living=["Family", "Future goals", "Pet"]
    )
    
    return samples


def export_model_schemas() -> Dict[str, Dict[str, Any]]:
    """Export schema information for all models"""
    schemas = {}
    
    for model_name, model_class in ModelFactory.model_classes.items():
        schema = {
            'model_name': model_name,
            'fields': {},
            'field_count': 0
        }
        
        for field_name, field_info in model_class.__dataclass_fields__.items():
            field_type = str(field_info.type)
            field_default = field_info.default if field_info.default != field_info.default_factory else "factory"
            
            schema['fields'][field_name] = {
                'type': field_type,
                'default': str(field_default),
                'required': field_info.default == field_info.default_factory and field_default == "factory"
            }
        
        schema['field_count'] = len(schema['fields'])
        schemas[model_name] = schema
    
    return schemas


# Test function
def main():
    """Test all models and validation"""
    print("Testing Data Models...")
    
    # Test model validation
    print("\n1. Testing model validation...")
    validation_report = validate_all_models()
    print(f"Models tested: {validation_report['models_tested']}")
    print(f"All models valid: {validation_report['all_valid']}")
    
    if validation_report['validation_errors']:
        print("Validation errors found:")
        for model, error in validation_report['validation_errors'].items():
            print(f"  {model}: {error}")
    
    # Test sample data creation
    print("\n2. Testing sample data creation...")
    try:
        samples = create_sample_data()
        print(f"Created {len(samples)} sample instances successfully")
        
        # Test a few sample validations
        for model_type, instance in list(samples.items())[:3]:
            print(f"  {model_type}: {instance.__class__.__name__} - Valid")
    
    except Exception as e:
        print(f"Error creating samples: {e}")
    
    # Test model factory
    print("\n3. Testing model factory...")
    try:
        test_patient = ModelFactory.create('patient', name="Factory Test Patient")
        print(f"Factory created patient: {test_patient.name}")
        
        patient_fields = ModelFactory.get_model_fields('patient')
        print(f"Patient model has {len(patient_fields)} fields")
    
    except Exception as e:
        print(f"Factory test error: {e}")
    
    # Test JSON serialization
    print("\n4. Testing JSON serialization...")
    try:
        test_session = samples['session']
        json_data = test_session.to_json()
        print(f"Session JSON length: {len(json_data)} characters")
        
        # Test dictionary conversion
        session_dict = test_session.to_dict()
        print(f"Session dictionary has {len(session_dict)} keys")
    
    except Exception as e:
        print(f"Serialization test error: {e}")
    
    print("\nModel testing completed!")


if __name__ == "__main__":
    main()