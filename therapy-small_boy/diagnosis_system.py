#!/usr/bin/env python3
"""
AI Therapy System - Diagnostic Management System
DSM-5 based diagnostic criteria, assessment protocols, and treatment recommendations
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from database import DatabaseManager
from models import Assessment
from utils import log_action


class DiagnosticStatus(Enum):
    """Diagnostic status options"""
    ACTIVE = "active"
    IN_REMISSION = "in_remission"
    RESOLVED = "resolved"
    RULE_OUT = "rule_out"


class SeverityLevel(Enum):
    """Severity levels for diagnoses"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    IN_PARTIAL_REMISSION = "in_partial_remission"
    IN_FULL_REMISSION = "in_full_remission"


@dataclass
class DiagnosticCriteria:
    """DSM-5 diagnostic criteria structure"""
    diagnosis_code: str
    diagnosis_name: str
    category: str
    criteria_sets: Dict[str, List[str]]
    exclusion_criteria: List[str] = field(default_factory=list)
    severity_specifiers: List[str] = field(default_factory=list)
    duration_requirements: str = ""
    functional_impairment_required: bool = True


@dataclass
class DiagnosticAssessment:
    """Individual diagnostic assessment result"""
    id: Optional[int] = None
    patient_id: int = 0
    diagnosis_code: str = ""
    diagnosis_name: str = ""
    criteria_met: Dict[str, bool] = field(default_factory=dict)
    severity: str = SeverityLevel.MODERATE.value
    confidence_level: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    differential_diagnoses: List[str] = field(default_factory=list)
    recommended_assessments: List[str] = field(default_factory=list)
    treatment_recommendations: List[str] = field(default_factory=list)
    assessment_date: str = field(default_factory=lambda: datetime.now().isoformat())
    assessor: str = "AI_System"


class DiagnosticSystem:
    """Manages diagnostic assessments and DSM-5 criteria"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.diagnostic_criteria = self._load_diagnostic_criteria()
        self._init_diagnostic_tables()
    
    def _init_diagnostic_tables(self):
        """Initialize diagnostic-related database tables"""
        with self.db.get_connection() as conn:
            # Diagnostic assessments table (separate from main diagnoses table)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS diagnostic_assessments (
                    id INTEGER PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    diagnosis_code TEXT,
                    diagnosis_name TEXT NOT NULL,
                    criteria_met TEXT DEFAULT '{}',
                    severity TEXT,
                    confidence_level REAL,
                    supporting_evidence TEXT DEFAULT '[]',
                    differential_diagnoses TEXT DEFAULT '[]',
                    recommended_assessments TEXT DEFAULT '[]',
                    treatment_recommendations TEXT DEFAULT '[]',
                    assessment_date TEXT NOT NULL DEFAULT (datetime('now')),
                    assessor TEXT DEFAULT 'AI_System',
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            ''')
            
            # Symptom tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS symptom_tracking (
                    id INTEGER PRIMARY KEY,
                    patient_id INTEGER NOT NULL,
                    symptom_name TEXT NOT NULL,
                    severity INTEGER CHECK (severity BETWEEN 0 AND 10),
                    frequency TEXT CHECK (frequency IN ('never', 'rarely', 'sometimes', 'often', 'always')),
                    duration_days INTEGER,
                    impairment_level INTEGER CHECK (impairment_level BETWEEN 0 AND 10),
                    onset_date TEXT,
                    recorded_date TEXT NOT NULL DEFAULT (datetime('now')),
                    notes TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            ''')
            
            conn.commit()
    
    def _load_diagnostic_criteria(self) -> Dict[str, DiagnosticCriteria]:
        """Load DSM-5 diagnostic criteria"""
        criteria = {}
        
        # Major Depressive Disorder (296.xx)
        criteria["296.2x"] = DiagnosticCriteria(
            diagnosis_code="296.2x",
            diagnosis_name="Major Depressive Disorder, Single Episode",
            category="Depressive Disorders",
            criteria_sets={
                "A": [
                    "Depressed mood most of the day, nearly every day",
                    "Markedly diminished interest or pleasure in activities",
                    "Significant weight loss or gain, or decrease/increase in appetite",
                    "Insomnia or hypersomnia nearly every day",
                    "Psychomotor agitation or retardation",
                    "Fatigue or loss of energy nearly every day",
                    "Feelings of worthlessness or excessive guilt",
                    "Diminished ability to think or concentrate",
                    "Recurrent thoughts of death or suicidal ideation"
                ],
                "B": ["Symptoms cause significant distress or impairment"],
                "C": ["Episode not attributable to substance use or medical condition"],
                "D": ["Not better explained by psychotic disorders"],
                "E": ["No history of manic or hypomanic episodes"]
            },
            duration_requirements="At least 2 weeks",
            severity_specifiers=["Mild", "Moderate", "Severe"]
        )
        
        # Generalized Anxiety Disorder (300.02)
        criteria["300.02"] = DiagnosticCriteria(
            diagnosis_code="300.02",
            diagnosis_name="Generalized Anxiety Disorder",
            category="Anxiety Disorders",
            criteria_sets={
                "A": ["Excessive anxiety and worry about multiple events or activities"],
                "B": ["Difficulty controlling the worry"],
                "C": [
                    "Restlessness or feeling keyed up or on edge",
                    "Being easily fatigued",
                    "Difficulty concentrating or mind going blank",
                    "Irritability",
                    "Muscle tension",
                    "Sleep disturbance"
                ],
                "D": ["Anxiety causes significant distress or impairment"],
                "E": ["Not attributable to substance use or medical condition"],
                "F": ["Not better explained by another mental disorder"]
            },
            duration_requirements="More days than not for at least 6 months"
        )
        
        # Post-Traumatic Stress Disorder (309.81)
        criteria["309.81"] = DiagnosticCriteria(
            diagnosis_code="309.81",
            diagnosis_name="Post-Traumatic Stress Disorder",
            category="Trauma and Stressor-Related Disorders",
            criteria_sets={
                "A": ["Exposure to actual or threatened death, serious injury, or sexual violence"],
                "B": [
                    "Recurrent, involuntary, intrusive memories",
                    "Recurrent distressing dreams",
                    "Dissociative reactions (flashbacks)",
                    "Intense psychological distress at trauma cues",
                    "Marked physiological reactions to trauma cues"
                ],
                "C": [
                    "Avoidance of trauma-related thoughts or feelings",
                    "Avoidance of external reminders of trauma"
                ],
                "D": [
                    "Inability to remember important aspects of trauma",
                    "Persistent negative beliefs about self or world",
                    "Persistent distorted blame of self or others",
                    "Pervasive negative emotional state",
                    "Markedly diminished interest in activities",
                    "Feelings of detachment from others",
                    "Persistent inability to experience positive emotions"
                ],
                "E": [
                    "Irritable behavior and angry outbursts",
                    "Reckless or self-destructive behavior",
                    "Hypervigilance",
                    "Exaggerated startle response",
                    "Problems with concentration",
                    "Sleep disturbance"
                ],
                "F": ["Duration more than 1 month"],
                "G": ["Symptoms cause significant distress or impairment"],
                "H": ["Not attributable to substance use or medical condition"]
            }
        )
        
        # Panic Disorder (300.01)
        criteria["300.01"] = DiagnosticCriteria(
            diagnosis_code="300.01",
            diagnosis_name="Panic Disorder",
            category="Anxiety Disorders",
            criteria_sets={
                "A": ["Recurrent unexpected panic attacks"],
                "B": [
                    "Persistent concern about having additional attacks",
                    "Worry about implications or consequences of attacks",
                    "Significant maladaptive change in behavior related to attacks"
                ]
            },
            duration_requirements="At least one month of criterion B"
        )
        
        # Social Anxiety Disorder (300.23)
        criteria["300.23"] = DiagnosticCriteria(
            diagnosis_code="300.23",
            diagnosis_name="Social Anxiety Disorder",
            category="Anxiety Disorders",
            criteria_sets={
                "A": ["Marked fear or anxiety about social situations"],
                "B": ["Fear of negative evaluation by others"],
                "C": ["Social situations almost always provoke fear or anxiety"],
                "D": ["Social situations are avoided or endured with intense fear"],
                "E": ["Fear is out of proportion to actual threat"],
                "F": ["Fear persists for 6 months or more"],
                "G": ["Causes significant distress or impairment"],
                "H": ["Not attributable to substance use or medical condition"],
                "I": ["Not better explained by another mental disorder"]
            }
        )
        
        # Borderline Personality Disorder (301.83)
        criteria["301.83"] = DiagnosticCriteria(
            diagnosis_code="301.83",
            diagnosis_name="Borderline Personality Disorder",
            category="Personality Disorders",
            criteria_sets={
                "A": [
                    "Frantic efforts to avoid abandonment",
                    "Pattern of unstable interpersonal relationships",
                    "Identity disturbance and unstable self-image",
                    "Impulsivity in potentially damaging areas",
                    "Recurrent suicidal behavior or self-mutilation",
                    "Affective instability due to mood reactivity",
                    "Chronic feelings of emptiness",
                    "Inappropriate intense anger or difficulty controlling anger",
                    "Transient stress-related paranoia or dissociation"
                ]
            },
            duration_requirements="Pervasive pattern beginning by early adulthood"
        )
        
        return criteria
    
    def conduct_diagnostic_interview(self, patient_id: int, suspected_diagnoses: List[str] = None) -> List[DiagnosticAssessment]:
        """Conduct structured diagnostic interview"""
        print("\n" + "="*60)
        print("DIAGNOSTIC ASSESSMENT INTERVIEW")
        print("="*60)
        print("This assessment will help determine if you meet criteria for specific mental health conditions.")
        print("Please answer honestly based on your experiences.\n")
        
        if not suspected_diagnoses:
            suspected_diagnoses = self._suggest_diagnoses_from_assessments(patient_id)
        
        diagnostic_results = []
        
        for diagnosis_code in suspected_diagnoses:
            if diagnosis_code in self.diagnostic_criteria:
                result = self._assess_single_diagnosis(patient_id, diagnosis_code)
                diagnostic_results.append(result)
        
        # Save all diagnostic assessments
        for result in diagnostic_results:
            self._save_diagnostic_assessment(result)
        
        # Display results summary
        self._display_diagnostic_summary(diagnostic_results)
        
        return diagnostic_results
    
    def _suggest_diagnoses_from_assessments(self, patient_id: int) -> List[str]:
        """Suggest diagnoses based on recent assessment scores"""
        suggested = []
        
        # Get recent assessments
        recent_assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 10",
            (patient_id,)
        )
        
        for assessment in recent_assessments:
            if assessment['assessment_type'] == 'PHQ9' and assessment['total_score'] >= 10:
                suggested.append("296.2x")  # Major Depression
            elif assessment['assessment_type'] == 'GAD7' and assessment['total_score'] >= 10:
                suggested.append("300.02")  # GAD
            elif assessment['assessment_type'] == 'PCL5' and assessment['total_score'] >= 33:
                suggested.append("309.81")  # PTSD
        
        # Default to common diagnoses if none suggested
        if not suggested:
            suggested = ["296.2x", "300.02"]
        
        return list(set(suggested))  # Remove duplicates
    
    def _assess_single_diagnosis(self, patient_id: int, diagnosis_code: str) -> DiagnosticAssessment:
        """Assess a single diagnosis through structured interview"""
        criteria = self.diagnostic_criteria[diagnosis_code]
        
        print(f"\n--- Assessing {criteria.diagnosis_name} ---")
        print(f"Duration requirement: {criteria.duration_requirements}")
        print()
        
        assessment = DiagnosticAssessment(
            patient_id=patient_id,
            diagnosis_code=diagnosis_code,
            diagnosis_name=criteria.diagnosis_name
        )
        
        criteria_met = {}
        total_criteria = 0
        met_criteria = 0
        
        # Assess each criteria set
        for criterion_set, criterion_list in criteria.criteria_sets.items():
            print(f"CRITERION {criterion_set}:")
            
            if criterion_set == "A" and criteria.diagnosis_name == "Major Depressive Disorder, Single Episode":
                # Special handling for MDD - need 5+ symptoms with at least one core symptom
                core_symptoms = criterion_list[:2]  # First two are core symptoms
                core_met = 0
                total_symptoms = 0
                
                for i, criterion in enumerate(criterion_list):
                    response = self._ask_criterion_question(criterion)
                    if response:
                        total_symptoms += 1
                        if i < 2:  # Core symptom
                            core_met += 1
                    criteria_met[f"{criterion_set}_{i+1}"] = response
                
                # MDD requires 5+ symptoms with at least 1 core symptom
                set_met = total_symptoms >= 5 and core_met >= 1
                print(f"Symptoms met: {total_symptoms}/9 (need 5+, including 1 core)")
                
            elif len(criterion_list) > 1:
                # Multiple criteria - count how many are met
                set_score = 0
                for i, criterion in enumerate(criterion_list):
                    response = self._ask_criterion_question(criterion)
                    if response:
                        set_score += 1
                    criteria_met[f"{criterion_set}_{i+1}"] = response
                
                # Determine if set is met based on diagnosis
                if criteria.diagnosis_name == "Generalized Anxiety Disorder" and criterion_set == "C":
                    set_met = set_score >= 3  # Need 3+ symptoms
                elif criteria.diagnosis_name == "Post-Traumatic Stress Disorder":
                    if criterion_set == "B":
                        set_met = set_score >= 1  # Need 1+ intrusion symptoms
                    elif criterion_set == "C":
                        set_met = set_score >= 1  # Need 1+ avoidance symptoms  
                    elif criterion_set == "D":
                        set_met = set_score >= 2  # Need 2+ negative mood/cognition symptoms
                    elif criterion_set == "E":
                        set_met = set_score >= 2  # Need 2+ arousal symptoms
                    else:
                        set_met = set_score > 0
                elif criteria.diagnosis_name == "Borderline Personality Disorder":
                    set_met = set_score >= 5  # Need 5+ of 9 criteria
                else:
                    set_met = set_score > 0
                    
                print(f"Criteria met in set {criterion_set}: {set_score}/{len(criterion_list)}")
                
            else:
                # Single criterion
                response = self._ask_criterion_question(criterion_list[0])
                criteria_met[criterion_set] = response
                set_met = response
                
            criteria_met[f"set_{criterion_set}_met"] = set_met
            total_criteria += 1
            if set_met:
                met_criteria += 1
            
            print(f"Criterion {criterion_set}: {'MET' if set_met else 'NOT MET'}\n")
        
        # Calculate overall diagnosis
        diagnosis_met = met_criteria == total_criteria
        confidence = met_criteria / total_criteria if total_criteria > 0 else 0
        
        assessment.criteria_met = criteria_met
        assessment.confidence_level = confidence
        
        # Determine severity if diagnosis is met
        if diagnosis_met:
            severity = self._assess_severity(criteria, criteria_met)
            assessment.severity = severity
            
            # Generate treatment recommendations
            assessment.treatment_recommendations = self._get_treatment_recommendations(diagnosis_code, severity)
            
        # Add supporting evidence
        assessment.supporting_evidence = self._gather_supporting_evidence(patient_id, diagnosis_code)
        
        # Suggest differential diagnoses
        assessment.differential_diagnoses = self._get_differential_diagnoses(diagnosis_code)
        
        print(f"DIAGNOSIS RESULT: {criteria.diagnosis_name}")
        print(f"Criteria met: {met_criteria}/{total_criteria}")
        print(f"Confidence: {confidence:.2%}")
        print(f"Diagnosis: {'MET' if diagnosis_met else 'NOT MET'}")
        if diagnosis_met:
            print(f"Severity: {assessment.severity}")
        
        return assessment
    
    def _ask_criterion_question(self, criterion: str) -> bool:
        """Ask a yes/no question about a diagnostic criterion"""
        print(f"  • {criterion}")
        
        while True:
            response = input("    Does this apply to you? (yes/no): ").lower().strip()
            if response in ['yes', 'y', '1', 'true']:
                return True
            elif response in ['no', 'n', '0', 'false']:
                return False
            else:
                print("    Please answer yes or no.")
    
    def _assess_severity(self, criteria: DiagnosticCriteria, criteria_met: Dict[str, bool]) -> str:
        """Assess severity level for diagnosis"""
        # This is a simplified severity assessment
        # In practice, this would be more sophisticated
        
        if criteria.diagnosis_name == "Major Depressive Disorder, Single Episode":
            # Count symptom severity based on number met
            symptom_count = sum(1 for key, value in criteria_met.items() 
                              if key.startswith("A_") and value)
            if symptom_count >= 8:
                return SeverityLevel.SEVERE.value
            elif symptom_count >= 6:
                return SeverityLevel.MODERATE.value
            else:
                return SeverityLevel.MILD.value
        
        # Default to moderate if no specific rules
        return SeverityLevel.MODERATE.value
    
    def _get_treatment_recommendations(self, diagnosis_code: str, severity: str) -> List[str]:
        """Get evidence-based treatment recommendations"""
        recommendations = {
            "296.2x": {  # Major Depression
                "mild": [
                    "Cognitive Behavioral Therapy (CBT)",
                    "Behavioral Activation",
                    "Regular exercise and activity scheduling",
                    "Sleep hygiene improvement",
                    "Social support activation"
                ],
                "moderate": [
                    "Cognitive Behavioral Therapy (CBT)",
                    "Consider medication evaluation",
                    "Behavioral Activation",
                    "Interpersonal Therapy (IPT)",
                    "Regular psychiatric monitoring"
                ],
                "severe": [
                    "Immediate psychiatric evaluation",
                    "Combination therapy (medication + psychotherapy)",
                    "Intensive outpatient treatment",
                    "Safety planning and risk assessment",
                    "Family involvement in treatment"
                ]
            },
            "300.02": {  # GAD
                "mild": [
                    "Cognitive Behavioral Therapy (CBT)",
                    "Relaxation training",
                    "Mindfulness-based interventions",
                    "Regular exercise",
                    "Stress management techniques"
                ],
                "moderate": [
                    "CBT with exposure exercises",
                    "Consider medication consultation",
                    "Acceptance and Commitment Therapy (ACT)",
                    "Progressive muscle relaxation",
                    "Lifestyle modifications"
                ],
                "severe": [
                    "Intensive CBT or ACT",
                    "Psychiatric medication evaluation",
                    "Possible intensive outpatient program",
                    "Family psychoeducation",
                    "Regular monitoring"
                ]
            },
            "309.81": {  # PTSD
                "mild": [
                    "Trauma-focused CBT",
                    "EMDR (Eye Movement Desensitization and Reprocessing)",
                    "Narrative Exposure Therapy",
                    "Mindfulness and grounding techniques",
                    "Gradual exposure therapy"
                ],
                "moderate": [
                    "Intensive trauma-focused therapy",
                    "Consider medication evaluation",
                    "Group therapy for trauma survivors",
                    "Skills training (DBT skills)",
                    "Family therapy if appropriate"
                ],
                "severe": [
                    "Intensive trauma treatment program",
                    "Psychiatric medication management",
                    "Inpatient treatment if severe impairment",
                    "Comprehensive case management",
                    "Crisis intervention planning"
                ]
            }
        }
        
        diagnosis_recs = recommendations.get(diagnosis_code, {})
        return diagnosis_recs.get(severity, ["General psychotherapy", "Consider specialist referral"])
    
    def _gather_supporting_evidence(self, patient_id: int, diagnosis_code: str) -> List[str]:
        """Gather supporting evidence from patient history"""
        evidence = []
        
        # Check assessment scores
        assessments = self.db.execute_query(
            "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC LIMIT 5",
            (patient_id,)
        )
        
        for assessment in assessments:
            if diagnosis_code == "296.2x" and assessment['assessment_type'] == 'PHQ9':
                if assessment['total_score'] >= 15:
                    evidence.append(f"PHQ-9 score of {assessment['total_score']} indicates moderately severe depression")
                elif assessment['total_score'] >= 10:
                    evidence.append(f"PHQ-9 score of {assessment['total_score']} indicates moderate depression")
            
            elif diagnosis_code == "300.02" and assessment['assessment_type'] == 'GAD7':
                if assessment['total_score'] >= 15:
                    evidence.append(f"GAD-7 score of {assessment['total_score']} indicates severe anxiety")
                elif assessment['total_score'] >= 10:
                    evidence.append(f"GAD-7 score of {assessment['total_score']} indicates moderate anxiety")
            
            elif diagnosis_code == "309.81" and assessment['assessment_type'] == 'PCL5':
                if assessment['total_score'] >= 50:
                    evidence.append(f"PCL-5 score of {assessment['total_score']} indicates high PTSD probability")
                elif assessment['total_score'] >= 33:
                    evidence.append(f"PCL-5 score of {assessment['total_score']} indicates probable PTSD")
        
        # Check session notes for relevant symptoms
        sessions = self.db.execute_query(
            "SELECT therapist_notes FROM sessions WHERE patient_id = ? AND therapist_notes IS NOT NULL ORDER BY session_date DESC LIMIT 5",
            (patient_id,)
        )
        
        for session in sessions:
            notes = session['therapist_notes'].lower()
            if 'depression' in notes or 'hopeless' in notes:
                evidence.append("Clinical notes document depressive symptoms")
            if 'anxiety' in notes or 'worry' in notes:
                evidence.append("Clinical notes document anxiety symptoms")
            if 'trauma' in notes or 'flashback' in notes:
                evidence.append("Clinical notes document trauma-related symptoms")
        
        return evidence
    
    def _get_differential_diagnoses(self, diagnosis_code: str) -> List[str]:
        """Get differential diagnoses to consider"""
        differentials = {
            "296.2x": [
                "Persistent Depressive Disorder (Dysthymia)",
                "Bipolar Disorder (depressed episode)",
                "Adjustment Disorder with Depressed Mood",
                "Substance-Induced Depressive Disorder",
                "Medical condition-induced depression"
            ],
            "300.02": [
                "Panic Disorder",
                "Social Anxiety Disorder",
                "Specific Phobia",
                "Anxiety due to medical condition",
                "Substance-induced anxiety"
            ],
            "309.81": [
                "Acute Stress Disorder",
                "Adjustment Disorder",
                "Major Depressive Disorder",
                "Dissociative Disorders",
                "Anxiety Disorders"
            ]
        }
        
        return differentials.get(diagnosis_code, [])
    
    def _save_diagnostic_assessment(self, assessment: DiagnosticAssessment) -> int:
        """Save diagnostic assessment to database"""
        assessment_id = self.db.execute_update('''
            INSERT INTO diagnostic_assessments
            (patient_id, diagnosis_code, diagnosis_name, criteria_met, severity,
             confidence_level, supporting_evidence, differential_diagnoses,
             recommended_assessments, treatment_recommendations, assessment_date, assessor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment.patient_id,
            assessment.diagnosis_code,
            assessment.diagnosis_name,
            json.dumps(assessment.criteria_met),
            assessment.severity,
            assessment.confidence_level,
            json.dumps(assessment.supporting_evidence),
            json.dumps(assessment.differential_diagnoses),
            json.dumps(assessment.recommended_assessments),
            json.dumps(assessment.treatment_recommendations),
            assessment.assessment_date,
            assessment.assessor
        ))
        
        # If diagnosis is met with high confidence, add to main diagnoses table
        if assessment.confidence_level >= 0.8:  # 80% confidence threshold
            self._add_formal_diagnosis(assessment)
        
        assessment.id = assessment_id
        return assessment_id
    
    def _add_formal_diagnosis(self, assessment: DiagnosticAssessment):
        """Add formal diagnosis to main diagnoses table"""
        self.db.execute_update('''
            INSERT INTO diagnoses
            (patient_id, diagnosis_code, diagnosis_name, severity, status,
             supporting_criteria, notes, diagnosed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment.patient_id,
            assessment.diagnosis_code,
            assessment.diagnosis_name,
            assessment.severity,
            DiagnosticStatus.ACTIVE.value,
            json.dumps(assessment.criteria_met),
            f"Confidence: {assessment.confidence_level:.2%}. Evidence: " + "; ".join(assessment.supporting_evidence[:3]),
            assessment.assessor
        ))
        
        log_action(f"Formal diagnosis added: {assessment.diagnosis_name}", 
                  "diagnosis_system", patient_id=assessment.patient_id)
    
    def _display_diagnostic_summary(self, assessments: List[DiagnosticAssessment]):
        """Display comprehensive diagnostic summary"""
        print("\n" + "="*80)
        print("DIAGNOSTIC ASSESSMENT SUMMARY")
        print("="*80)
        
        for assessment in assessments:
            print(f"\nDiagnosis: {assessment.diagnosis_name}")
            print(f"Code: {assessment.diagnosis_code}")
            print(f"Confidence Level: {assessment.confidence_level:.2%}")
            print(f"Severity: {assessment.severity}")
            
            if assessment.confidence_level >= 0.8:
                print("STATUS: DIAGNOSIS MET - Added to formal diagnoses")
            elif assessment.confidence_level >= 0.6:
                print("STATUS: PROBABLE - Consider additional assessment")
            else:
                print("STATUS: NOT MET - Criteria not sufficiently satisfied")
            
            if assessment.supporting_evidence:
                print("\nSupporting Evidence:")
                for evidence in assessment.supporting_evidence[:3]:
                    print(f"  • {evidence}")
            
            if assessment.treatment_recommendations:
                print("\nTreatment Recommendations:")
                for rec in assessment.treatment_recommendations[:3]:
                    print(f"  • {rec}")
            
            if assessment.differential_diagnoses:
                print("\nDifferential Diagnoses to Consider:")
                for diff in assessment.differential_diagnoses[:3]:
                    print(f"  • {diff}")
            
            print("-" * 80)
    
    def get_patient_diagnoses(self, patient_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get patient's current diagnoses"""
        if active_only:
            return self.db.execute_query(
                "SELECT * FROM diagnoses WHERE patient_id = ? AND status = 'active' ORDER BY date_diagnosed DESC",
                (patient_id,)
            )
        else:
            return self.db.execute_query(
                "SELECT * FROM diagnoses WHERE patient_id = ? ORDER BY date_diagnosed DESC",
                (patient_id,)
            )
    
    def update_diagnosis_status(self, diagnosis_id: int, new_status: str, notes: str = ""):
        """Update diagnosis status"""
        update_data = {
            'status': new_status,
            'notes': notes
        }
        
        if new_status in ['resolved', 'in_remission']:
            update_data['date_resolved'] = datetime.now().isoformat()
        
        self.db.execute_update(
            "UPDATE diagnoses SET status = ?, notes = ?, date_resolved = ? WHERE id = ?",
            (new_status, notes, update_data.get('date_resolved'), diagnosis_id)
        )
        
        log_action(f"Diagnosis status updated to {new_status}", "diagnosis_system")
    
    def track_symptoms(self, patient_id: int, symptoms_data: List[Dict[str, Any]]):
        """Track patient symptoms over time"""
        for symptom in symptoms_data:
            self.db.execute_update('''
                INSERT INTO symptom_tracking
                (patient_id, symptom_name, severity, frequency, duration_days,
                 impairment_level, onset_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                symptom['name'],
                symptom.get('severity', 5),
                symptom.get('frequency', 'sometimes'),
                symptom.get('duration_days', 0),
                symptom.get('impairment_level', 5),
                symptom.get('onset_date', ''),
                symptom.get('notes', '')
            ))
        
        log_action(f"Symptoms tracked for patient {patient_id}", "diagnosis_system", patient_id=patient_id)
    
    def get_symptom_trends(self, patient_id: int, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """Get symptom trends over specified time period"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        symptoms = self.db.execute_query('''
            SELECT symptom_name, severity, frequency, recorded_date, impairment_level
            FROM symptom_tracking
            WHERE patient_id = ? AND recorded_date > ?
            ORDER BY symptom_name, recorded_date
        ''', (patient_id, cutoff_date))
        
        # Group by symptom name
        trends = {}
        for symptom in symptoms:
            name = symptom['symptom_name']
            if name not in trends:
                trends[name] = []
            trends[name].append(symptom)
        
        return trends
    
    def generate_diagnostic_report(self, patient_id: int) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        report = {
            'patient_id': patient_id,
            'report_date': datetime.now().isoformat(),
            'current_diagnoses': [],
            'diagnostic_history': [],
            'symptom_summary': {},
            'treatment_recommendations': [],
            'follow_up_needed': []
        }
        
        # Current active diagnoses
        current_diagnoses = self.get_patient_diagnoses(patient_id, active_only=True)
        report['current_diagnoses'] = current_diagnoses
        
        # Diagnostic assessment history
        diagnostic_history = self.db.execute_query(
            "SELECT * FROM diagnostic_assessments WHERE patient_id = ? ORDER BY assessment_date DESC",
            (patient_id,)
        )
        report['diagnostic_history'] = diagnostic_history
        
        # Symptom trends
        symptom_trends = self.get_symptom_trends(patient_id, days=90)
        report['symptom_summary'] = {
            'tracked_symptoms': list(symptom_trends.keys()),
            'symptom_count': len(symptom_trends),
            'trending_worse': [],
            'trending_better': [],
            'stable_symptoms': []
        }
        
        # Analyze trends
        for symptom_name, trend_data in symptom_trends.items():
            if len(trend_data) >= 2:
                recent_severity = trend_data[-1]['severity']
                initial_severity = trend_data[0]['severity']
                
                if recent_severity > initial_severity + 1:
                    report['symptom_summary']['trending_worse'].append(symptom_name)
                elif recent_severity < initial_severity - 1:
                    report['symptom_summary']['trending_better'].append(symptom_name)
                else:
                    report['symptom_summary']['stable_symptoms'].append(symptom_name)
        
        # Compile treatment recommendations from all diagnoses
        all_recommendations = set()
        for diagnosis in current_diagnoses:
            if diagnosis.get('diagnosis_code') in self.diagnostic_criteria:
                recs = self._get_treatment_recommendations(
                    diagnosis['diagnosis_code'], 
                    diagnosis.get('severity', 'moderate')
                )
                all_recommendations.update(recs)
        
        report['treatment_recommendations'] = list(all_recommendations)
        
        # Follow-up recommendations
        follow_up = []
        
        # Check for unresolved high-confidence assessments
        for assessment in diagnostic_history[:5]:  # Recent 5 assessments
            if assessment['confidence_level'] >= 0.6:
                # Check if formal diagnosis exists
                formal_diagnosis = any(
                    d['diagnosis_code'] == assessment['diagnosis_code'] 
                    for d in current_diagnoses
                )
                if not formal_diagnosis:
                    follow_up.append(f"Consider formal diagnosis for {assessment['diagnosis_name']}")
        
        # Check for worsening symptoms
        if report['symptom_summary']['trending_worse']:
            follow_up.append("Reassess treatment plan due to worsening symptoms")
        
        # Check for outdated diagnoses (no assessment in 6 months)
        six_months_ago = (datetime.now() - timedelta(days=180)).isoformat()
        for diagnosis in current_diagnoses:
            if diagnosis['date_diagnosed'] < six_months_ago:
                follow_up.append(f"Review status of {diagnosis['diagnosis_name']} (diagnosed {diagnosis['date_diagnosed'][:10]})")
        
        report['follow_up_needed'] = follow_up
        
        return report
    
    def suggest_additional_assessments(self, patient_id: int) -> List[str]:
        """Suggest additional assessments based on current diagnoses and symptoms"""
        suggestions = []
        
        current_diagnoses = self.get_patient_diagnoses(patient_id)
        
        # Get recent assessment types
        recent_assessments = self.db.execute_query(
            "SELECT DISTINCT assessment_type FROM assessments WHERE patient_id = ? AND assessment_date > ?",
            (patient_id, (datetime.now() - timedelta(days=30)).isoformat())
        )
        
        completed_types = {a['assessment_type'] for a in recent_assessments}
        
        # Suggest based on diagnoses
        for diagnosis in current_diagnoses:
            code = diagnosis['diagnosis_code']
            
            if code == "296.2x":  # Depression
                if 'PHQ9' not in completed_types:
                    suggestions.append("PHQ-9 (Depression screening)")
                if 'GAD7' not in completed_types:
                    suggestions.append("GAD-7 (Comorbid anxiety assessment)")
                    
            elif code == "300.02":  # GAD
                if 'GAD7' not in completed_types:
                    suggestions.append("GAD-7 (Anxiety severity)")
                if 'PHQ9' not in completed_types:
                    suggestions.append("PHQ-9 (Comorbid depression screening)")
                    
            elif code == "309.81":  # PTSD
                if 'PCL5' not in completed_types:
                    suggestions.append("PCL-5 (PTSD symptom severity)")
                if 'PHQ9' not in completed_types:
                    suggestions.append("PHQ-9 (Trauma-related depression)")
        
        # Remove duplicates and return
        return list(set(suggestions))
    
    def create_differential_diagnosis_matrix(self, patient_id: int) -> Dict[str, Any]:
        """Create differential diagnosis matrix"""
        matrix = {
            'patient_id': patient_id,
            'created_date': datetime.now().isoformat(),
            'diagnoses_considered': [],
            'symptom_matrix': {},
            'likelihood_scores': {},
            'recommended_next_steps': []
        }
        
        # Get all diagnostic assessments
        assessments = self.db.execute_query(
            "SELECT * FROM diagnostic_assessments WHERE patient_id = ? ORDER BY confidence_level DESC",
            (patient_id,)
        )
        
        # Common symptoms across disorders
        common_symptoms = [
            'depressed_mood', 'anxiety', 'sleep_disturbance', 'concentration_problems',
            'fatigue', 'irritability', 'appetite_changes', 'social_withdrawal',
            'hopelessness', 'worry', 'restlessness', 'muscle_tension'
        ]
        
        # Create matrix of symptoms vs diagnoses
        for assessment in assessments:
            diagnosis = assessment['diagnosis_name']
            matrix['diagnoses_considered'].append(diagnosis)
            matrix['likelihood_scores'][diagnosis] = assessment['confidence_level']
            
            # Initialize symptom presence for this diagnosis
            if diagnosis not in matrix['symptom_matrix']:
                matrix['symptom_matrix'][diagnosis] = {}
            
            # Map criteria to common symptoms (simplified)
            criteria_met = json.loads(assessment['criteria_met'])
            for symptom in common_symptoms:
                # This is a simplified mapping - in practice would be more sophisticated
                symptom_present = any(criteria_met.get(key, False) for key in criteria_met.keys())
                matrix['symptom_matrix'][diagnosis][symptom] = symptom_present
        
        # Recommendations based on differential
        if len(matrix['diagnoses_considered']) > 1:
            matrix['recommended_next_steps'].append("Conduct detailed clinical interview to differentiate diagnoses")
            matrix['recommended_next_steps'].append("Consider structured diagnostic instruments")
            matrix['recommended_next_steps'].append("Review family history and medical history")
        
        return matrix
    
    def validate_diagnosis_criteria(self, diagnosis_code: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate diagnosis against DSM-5 criteria using patient data"""
        if diagnosis_code not in self.diagnostic_criteria:
            return {'valid': False, 'error': 'Diagnosis code not found'}
        
        criteria = self.diagnostic_criteria[diagnosis_code]
        validation = {
            'diagnosis_code': diagnosis_code,
            'diagnosis_name': criteria.diagnosis_name,
            'valid': True,
            'criteria_analysis': {},
            'missing_requirements': [],
            'recommendations': []
        }
        
        # Validate each criterion set
        for criterion_set, criterion_list in criteria.criteria_sets.items():
            set_key = f"criterion_{criterion_set}"
            validation['criteria_analysis'][set_key] = {
                'required_items': len(criterion_list),
                'met_items': 0,
                'missing_items': [],
                'satisfied': False
            }
            
            # Check if patient data supports each criterion
            for i, criterion in enumerate(criterion_list):
                criterion_key = f"{criterion_set}_{i+1}"
                if criterion_key in patient_data:
                    if patient_data[criterion_key]:
                        validation['criteria_analysis'][set_key]['met_items'] += 1
                    else:
                        validation['criteria_analysis'][set_key]['missing_items'].append(criterion)
                else:
                    validation['criteria_analysis'][set_key]['missing_items'].append(f"Data missing for: {criterion}")
            
            # Determine if criterion set is satisfied
            met_count = validation['criteria_analysis'][set_key]['met_items']
            required_count = validation['criteria_analysis'][set_key]['required_items']
            
            if diagnosis_code == "296.2x" and criterion_set == "A":
                # MDD requires 5+ symptoms
                validation['criteria_analysis'][set_key]['satisfied'] = met_count >= 5
            elif diagnosis_code == "300.02" and criterion_set == "C":
                # GAD requires 3+ symptoms
                validation['criteria_analysis'][set_key]['satisfied'] = met_count >= 3
            else:
                # Default: all items must be met
                validation['criteria_analysis'][set_key]['satisfied'] = met_count == required_count
        
        # Check duration requirements
        if criteria.duration_requirements:
            if 'duration_met' not in patient_data:
                validation['missing_requirements'].append(f"Duration requirement: {criteria.duration_requirements}")
            elif not patient_data['duration_met']:
                validation['missing_requirements'].append(f"Insufficient duration: {criteria.duration_requirements}")
        
        # Check functional impairment
        if criteria.functional_impairment_required:
            if 'functional_impairment' not in patient_data:
                validation['missing_requirements'].append("Functional impairment assessment needed")
            elif not patient_data['functional_impairment']:
                validation['missing_requirements'].append("Functional impairment not demonstrated")
        
        # Overall validation
        all_criteria_met = all(
            analysis['satisfied'] 
            for analysis in validation['criteria_analysis'].values()
        )
        
        validation['valid'] = all_criteria_met and len(validation['missing_requirements']) == 0
        
        # Generate recommendations
        if not validation['valid']:
            if validation['missing_requirements']:
                validation['recommendations'].append("Complete missing assessments before finalizing diagnosis")
            
            unsatisfied_criteria = [
                criterion_set for criterion_set, analysis in validation['criteria_analysis'].items()
                if not analysis['satisfied']
            ]
            
            if unsatisfied_criteria:
                validation['recommendations'].append(f"Reassess criteria: {', '.join(unsatisfied_criteria)}")
                validation['recommendations'].append("Consider differential diagnoses")
        
        return validation
    
    def export_diagnostic_summary(self, patient_id: int) -> str:
        """Export diagnostic summary in a standardized format"""
        report = self.generate_diagnostic_report(patient_id)
        
        # Get patient info
        patient_info = self.db.execute_query("SELECT name FROM patients WHERE id = ?", (patient_id,))
        patient_name = patient_info[0]['name'] if patient_info else f"Patient {patient_id}"
        
        summary = f"""
DIAGNOSTIC SUMMARY REPORT
Patient: {patient_name}
Patient ID: {patient_id}
Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
CURRENT ACTIVE DIAGNOSES
{'='*60}
"""
        
        if report['current_diagnoses']:
            for i, diagnosis in enumerate(report['current_diagnoses'], 1):
                summary += f"""
{i}. {diagnosis['diagnosis_name']}
   Code: {diagnosis['diagnosis_code']}
   Severity: {diagnosis.get('severity', 'Not specified')}
   Date Diagnosed: {diagnosis['date_diagnosed'][:10]}
   Status: {diagnosis['status']}
"""
        else:
            summary += "\nNo active diagnoses on record.\n"
        
        summary += f"""
{'='*60}
SYMPTOM SUMMARY
{'='*60}
Total Tracked Symptoms: {report['symptom_summary']['symptom_count']}
Worsening Symptoms: {', '.join(report['symptom_summary']['trending_worse']) if report['symptom_summary']['trending_worse'] else 'None'}
Improving Symptoms: {', '.join(report['symptom_summary']['trending_better']) if report['symptom_summary']['trending_better'] else 'None'}
Stable Symptoms: {', '.join(report['symptom_summary']['stable_symptoms']) if report['symptom_summary']['stable_symptoms'] else 'None'}

{'='*60}
TREATMENT RECOMMENDATIONS
{'='*60}
"""
        
        if report['treatment_recommendations']:
            for i, rec in enumerate(report['treatment_recommendations'], 1):
                summary += f"{i}. {rec}\n"
        else:
            summary += "No specific treatment recommendations generated.\n"
        
        summary += f"""
{'='*60}
FOLLOW-UP NEEDED
{'='*60}
"""
        
        if report['follow_up_needed']:
            for i, follow_up in enumerate(report['follow_up_needed'], 1):
                summary += f"{i}. {follow_up}\n"
        else:
            summary += "No specific follow-up actions identified.\n"
        
        summary += f"""
{'='*60}
DIAGNOSTIC ASSESSMENT HISTORY
{'='*60}
"""
        
        if report['diagnostic_history']:
            for assessment in report['diagnostic_history'][:5]:  # Last 5 assessments
                summary += f"""
Assessment: {assessment['diagnosis_name']}
Date: {assessment['assessment_date'][:10]}
Confidence: {float(assessment['confidence_level']):.1%}
Severity: {assessment.get('severity', 'Not specified')}
Assessor: {assessment['assessor']}
---
"""
        else:
            summary += "No diagnostic assessment history available.\n"
        
        summary += "\nEnd of Report"
        
        return summary


# Utility functions
def quick_depression_screen(db: DatabaseManager, patient_id: int) -> Dict[str, Any]:
    """Quick depression screening based on core symptoms"""
    print("Quick Depression Screen")
    print("Answer yes/no to the following questions:")
    
    core_questions = [
        "Over the past 2 weeks, have you felt depressed or sad most of the day, nearly every day?",
        "Over the past 2 weeks, have you had little interest or pleasure in doing things?",
        "Have you had thoughts that you would be better off dead or of hurting yourself?"
    ]
    
    responses = {}
    risk_score = 0
    
    for i, question in enumerate(core_questions):
        response = input(f"{question} (yes/no): ").lower().strip()
        responses[f"q{i+1}"] = response == 'yes' or response == 'y'
        if responses[f"q{i+1}"]:
            risk_score += 2 if i == 2 else 1  # Suicide question weighted higher
    
    result = {
        'patient_id': patient_id,
        'screening_date': datetime.now().isoformat(),
        'responses': responses,
        'risk_score': risk_score,
        'recommendation': ''
    }
    
    if risk_score >= 3:
        result['recommendation'] = "HIGH PRIORITY: Immediate comprehensive assessment needed"
    elif risk_score >= 2:
        result['recommendation'] = "MODERATE PRIORITY: Consider PHQ-9 assessment and clinical evaluation"
    elif risk_score == 1:
        result['recommendation'] = "LOW PRIORITY: Monitor symptoms and consider follow-up"
    else:
        result['recommendation'] = "Negative screen: Continue routine monitoring"
    
    # Save screening result
    db.execute_update('''
        INSERT INTO system_logs (log_level, module, action, patient_id, message)
        VALUES (?, ?, ?, ?, ?)
    ''', ('INFO', 'diagnosis_system', 'quick_depression_screen', patient_id, json.dumps(result)))
    
    return result


def map_assessments_to_diagnoses(assessment_scores: Dict[str, int]) -> List[str]:
    """Map assessment scores to likely diagnoses"""
    likely_diagnoses = []
    
    if 'PHQ9' in assessment_scores and assessment_scores['PHQ9'] >= 10:
        likely_diagnoses.append("296.2x")  # Major Depression
    
    if 'GAD7' in assessment_scores and assessment_scores['GAD7'] >= 10:
        likely_diagnoses.append("300.02")  # GAD
    
    if 'PCL5' in assessment_scores and assessment_scores['PCL5'] >= 33:
        likely_diagnoses.append("309.81")  # PTSD
    
    # Comorbidity patterns
    if 'PHQ9' in assessment_scores and 'GAD7' in assessment_scores:
        if assessment_scores['PHQ9'] >= 10 and assessment_scores['GAD7'] >= 10:
            # Mixed anxiety-depression
            if "296.2x" not in likely_diagnoses:
                likely_diagnoses.append("296.2x")
            if "300.02" not in likely_diagnoses:
                likely_diagnoses.append("300.02")
    
    return likely_diagnoses


# Test function
def main():
    """Test diagnostic system functionality"""
    from database import DatabaseManager
    
    print("Testing Diagnostic System...")
    
    db = DatabaseManager(":memory:")
    diagnostic_system = DiagnosticSystem(db)
    
    # Create test patient
    patient_id = db.execute_update(
        "INSERT INTO patients (name, date_of_birth) VALUES (?, ?)",
        ("Test Patient", "1990-01-01")
    )
    
    print(f"Created test patient ID: {patient_id}")
    
    # Test quick depression screen
    print("\nTesting quick depression screen...")
    # Simulate responses
    import sys
    from io import StringIO
    
    # Mock input for testing
    old_input = input
    test_responses = iter(["yes", "yes", "no"])
    def mock_input(prompt):
        return next(test_responses)
    
    try:
        sys.modules['builtins'].input = mock_input
        screen_result = quick_depression_screen(db, patient_id)
        print(f"Depression screen result: {screen_result['recommendation']}")
    finally:
        sys.modules['builtins'].input = old_input
    
    # Test diagnosis mapping
    print("\nTesting assessment-to-diagnosis mapping...")
    test_scores = {'PHQ9': 15, 'GAD7': 12}
    mapped_diagnoses = map_assessments_to_diagnoses(test_scores)
    print(f"Mapped diagnoses: {mapped_diagnoses}")
    
    # Test diagnostic report generation
    print("\nTesting diagnostic report generation...")
    report = diagnostic_system.generate_diagnostic_report(patient_id)
    print(f"Generated report for patient {patient_id}")
    print(f"Current diagnoses: {len(report['current_diagnoses'])}")
    
    print("\nDiagnostic system testing completed!")


if __name__ == "__main__":
    main()