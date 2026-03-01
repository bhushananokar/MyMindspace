#!/usr/bin/env python3
"""
AI Therapy System - Assessment Tools
Comprehensive assessment system with PHQ-9, GAD-7, PCL-5, and session rating scales
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass
from models import Assessment
from database import DatabaseManager
from utils import log_action


@dataclass
class AssessmentQuestion:
    """Individual assessment question"""
    id: int
    text: str
    options: List[str]
    scores: List[int]


class AssessmentSystem:
    """Manages all assessment tools and scoring"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.assessments = {
            'PHQ9': PHQ9Assessment(),
            'GAD7': GAD7Assessment(),
            'PCL5': PCL5Assessment(),
            'ORS': OutcomeRatingScale(),
            'SRS': SessionRatingScale()
        }
    
    def run_assessment(self, patient_id: int, assessment_type: str, 
                      session_id: Optional[int] = None) -> Assessment:
        """Run a specific assessment for a patient"""
        
        if assessment_type not in self.assessments:
            raise ValueError(f"Assessment type {assessment_type} not supported")
        
        assessment_tool = self.assessments[assessment_type]
        
        print(f"\n{'='*60}")
        print(f"{assessment_tool.name}")
        print(f"{'='*60}")
        print(f"Instructions: {assessment_tool.instructions}")
        print()
        
        responses = {}
        total_score = 0
        
        # Administer each question
        for question in assessment_tool.questions:
            while True:
                print(f"Question {question.id}: {question.text}")
                print()
                
                # Display options
                for i, option in enumerate(question.options):
                    print(f"  {i}. {option}")
                
                try:
                    choice = input(f"\nEnter your choice (0-{len(question.options)-1}): ").strip()
                    choice_idx = int(choice)
                    
                    if 0 <= choice_idx < len(question.options):
                        responses[f"q{question.id}"] = {
                            'answer': question.options[choice_idx],
                            'score': question.scores[choice_idx]
                        }
                        total_score += question.scores[choice_idx]
                        print(f"Selected: {question.options[choice_idx]}\n")
                        break
                    else:
                        print("Invalid choice. Please try again.\n")
                        
                except (ValueError, IndexError):
                    print("Invalid input. Please enter a number.\n")
        
        # Calculate results
        severity_level, interpretation = assessment_tool.interpret_score(total_score)
        
        # Create assessment record
        assessment = Assessment(
            patient_id=patient_id,
            session_id=session_id,
            assessment_type=assessment_type,
            questions_responses=responses,
            total_score=total_score,
            severity_level=severity_level,
            interpretation=interpretation
        )
        
        # Save to database
        self.save_assessment(assessment)
        
        # Display results
        self.display_results(assessment, assessment_tool)
        
        log_action(f"Completed {assessment_type} assessment", "assessment", patient_id=patient_id)
        
        return assessment
    
    def get_assessment(self, assessment_type: str) -> Dict[str, Any]:
        """Get assessment questions and details"""
        if assessment_type not in self.assessments:
            return None
        
        assessment_tool = self.assessments[assessment_type]
        
        return {
            'name': assessment_tool.name,
            'description': getattr(assessment_tool, 'description', f'{assessment_type} Assessment'),
            'instructions': assessment_tool.instructions,
            'questions': [
                {
                    'text': q.text,
                    'options': q.options,
                    'scores': q.scores
                } for q in assessment_tool.questions
            ]
        }
    def calculate_severity(self, assessment_type: str, total_score: int) -> str:
        """Calculate severity level from total score"""
        if assessment_type not in self.assessments:
            return "Unknown"
        
        assessment_tool = self.assessments[assessment_type]
        severity, _ = assessment_tool.interpret_score(total_score)
        return severity

    def get_interpretation(self, assessment_type: str, total_score: int) -> str:
        """Get clinical interpretation of score"""
        if assessment_type not in self.assessments:
            return "Unable to interpret unknown assessment type"
        
        assessment_tool = self.assessments[assessment_type]
        _, interpretation = assessment_tool.interpret_score(total_score)
        return interpretation

    def save_assessment(self, patient_id: int, assessment_type: str, responses: Dict, 
                    total_score: int, severity_level: str, interpretation: str,
                    session_id: int = None) -> int:
        """Save assessment results to database"""
        assessment_id = self.db.execute_update('''
            INSERT INTO assessments 
            (patient_id, session_id, assessment_type, questions_responses, 
            total_score, severity_level, assessment_date, interpretation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, session_id, assessment_type, 
            json.dumps(responses), total_score, severity_level,
            datetime.now().isoformat(), interpretation
        ))
        
        return assessment_id
    
    def display_results(self, assessment: Assessment, assessment_tool):
        """Display assessment results"""
        print(f"\n{'='*60}")
        print(f"{assessment_tool.name} RESULTS")
        print(f"{'='*60}")
        print(f"Total Score: {assessment.total_score}")
        print(f"Severity Level: {assessment.severity_level}")
        print(f"Date: {assessment.assessment_date}")
        print()
        print("Interpretation:")
        print(assessment.interpretation)
        print(f"{'='*60}\n")
    
    def get_patient_assessments(self, patient_id: int, assessment_type: str = None) -> List[Dict]:
        """Get assessment history for a patient"""
        if assessment_type:
            return self.db.execute_query(
                "SELECT * FROM assessments WHERE patient_id = ? AND assessment_type = ? ORDER BY assessment_date DESC",
                (patient_id, assessment_type)
            )
        else:
            return self.db.execute_query(
                "SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessment_date DESC",
                (patient_id,)
            )
    
    def track_progress(self, patient_id: int, assessment_type: str) -> Dict[str, Any]:
        """Track assessment progress over time"""
        assessments = self.get_patient_assessments(patient_id, assessment_type)
        
        if len(assessments) < 2:
            return {"message": "Need at least 2 assessments to track progress"}
        
        scores = [a['total_score'] for a in assessments]
        dates = [a['assessment_date'] for a in assessments]
        
        latest_score = scores[0]
        previous_score = scores[1]
        change = latest_score - previous_score
        
        progress = {
            'assessment_type': assessment_type,
            'latest_score': latest_score,
            'previous_score': previous_score,
            'change': change,
            'improvement': change < 0,  # Lower scores usually mean improvement
            'scores_history': list(reversed(scores)),
            'dates_history': list(reversed(dates)),
            'total_assessments': len(assessments)
        }
        
        return progress


class PHQ9Assessment:
    """PHQ-9 Depression Assessment"""
    
    def __init__(self):
        self.name = "PHQ-9 Depression Assessment"
        self.instructions = "Over the last 2 weeks, how often have you been bothered by any of the following problems?"
        
        self.questions = [
            AssessmentQuestion(
                1, 
                "Little interest or pleasure in doing things",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                2,
                "Feeling down, depressed, or hopeless",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                3,
                "Trouble falling or staying asleep, or sleeping too much",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                4,
                "Feeling tired or having little energy",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                5,
                "Poor appetite or overeating",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                6,
                "Feeling bad about yourself or that you are a failure or have let yourself or your family down",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                7,
                "Trouble concentrating on things, such as reading the newspaper or watching television",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                8,
                "Moving or speaking so slowly that other people could have noticed, or being so fidgety or restless that you have been moving around a lot more than usual",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                9,
                "Thoughts that you would be better off dead, or thoughts of hurting yourself in some way",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            )
        ]
    
    def interpret_score(self, score: int) -> Tuple[str, str]:
        """Interpret PHQ-9 score"""
        if 0 <= score <= 4:
            severity = "Minimal"
            interpretation = "Minimal depression. These scores suggest the absence of a depressive disorder."
        elif 5 <= score <= 9:
            severity = "Mild"
            interpretation = "Mild depression. Consider watchful waiting, repeat PHQ-9 at followup."
        elif 10 <= score <= 14:
            severity = "Moderate"
            interpretation = "Moderate depression. Treatment plan should consider counseling, followup and/or pharmacotherapy."
        elif 15 <= score <= 19:
            severity = "Moderately Severe"
            interpretation = "Moderately severe depression. Active treatment with psychotherapy and/or medication is warranted."
        else:  # 20-27
            severity = "Severe"
            interpretation = "Severe depression. Immediate initiation of psychotherapy and/or pharmacotherapy is warranted."
        
        # Check for suicide risk (Question 9)
        # This should be handled separately in a real implementation
        if score >= 20:
            interpretation += "\n\nNOTE: High scores warrant immediate clinical attention and suicide risk assessment."
        
        return severity, interpretation


class GAD7Assessment:
    """GAD-7 Generalized Anxiety Disorder Assessment"""
    
    def __init__(self):
        self.name = "GAD-7 Anxiety Assessment"
        self.instructions = "Over the last 2 weeks, how often have you been bothered by the following problems?"
        
        self.questions = [
            AssessmentQuestion(
                1,
                "Feeling nervous, anxious, or on edge",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                2,
                "Not being able to stop or control worrying",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                3,
                "Worrying too much about different things",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                4,
                "Trouble relaxing",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                5,
                "Being so restless that it's hard to sit still",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                6,
                "Becoming easily annoyed or irritable",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            ),
            AssessmentQuestion(
                7,
                "Feeling afraid as if something awful might happen",
                ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                [0, 1, 2, 3]
            )
        ]
    
    def interpret_score(self, score: int) -> Tuple[str, str]:
        """Interpret GAD-7 score"""
        if 0 <= score <= 4:
            severity = "Minimal"
            interpretation = "Minimal anxiety. No treatment needed."
        elif 5 <= score <= 9:
            severity = "Mild"
            interpretation = "Mild anxiety. Watchful waiting or psychoeducation may be appropriate."
        elif 10 <= score <= 14:
            severity = "Moderate"
            interpretation = "Moderate anxiety. Consider counseling, self-help, or medication."
        else:  # 15-21
            severity = "Severe"
            interpretation = "Severe anxiety. Active treatment with counseling and/or medication is warranted."
        
        return severity, interpretation


class PCL5Assessment:
    """PCL-5 PTSD Assessment"""
    
    def __init__(self):
        self.name = "PCL-5 PTSD Assessment"
        self.instructions = "In the past month, how much were you bothered by:"
        
        self.questions = [
            AssessmentQuestion(
                1,
                "Repeated, disturbing, and unwanted memories of the stressful experience?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                2,
                "Repeated, disturbing dreams of the stressful experience?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                3,
                "Suddenly feeling or acting as if the stressful experience were actually happening again?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                4,
                "Feeling very upset when something reminded you of the stressful experience?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                5,
                "Having strong physical reactions when something reminded you of the stressful experience?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                6,
                "Avoiding memories, thoughts, or feelings related to the stressful experience?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                7,
                "Avoiding external reminders of the stressful experience?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                8,
                "Trouble remembering important parts of the stressful experience?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                9,
                "Having strong negative beliefs about yourself, other people, or the world?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                10,
                "Blaming yourself or someone else for the stressful experience or what happened after it?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                11,
                "Having strong negative feelings such as fear, horror, anger, guilt, or shame?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                12,
                "Loss of interest in activities that you used to enjoy?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                13,
                "Feeling distant or cut off from other people?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                14,
                "Trouble experiencing positive feelings?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                15,
                "Irritable behavior, angry outbursts, or acting aggressively?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                16,
                "Taking too many risks or doing things that could cause you harm?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                17,
                "Being 'superalert' or watchful or on guard?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                18,
                "Feeling jumpy or easily startled?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                19,
                "Having difficulty concentrating?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            ),
            AssessmentQuestion(
                20,
                "Trouble falling or staying asleep?",
                ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
                [0, 1, 2, 3, 4]
            )
        ]
    
    def interpret_score(self, score: int) -> Tuple[str, str]:
        """Interpret PCL-5 score"""
        if score < 31:
            severity = "Below Threshold"
            interpretation = "Score suggests PTSD symptoms are below clinical threshold. However, consider functional impairment and clinical judgment."
        elif 31 <= score <= 49:
            severity = "Probable PTSD"
            interpretation = "Score suggests probable PTSD. Clinical interview recommended to confirm diagnosis."
        else:  # 50+
            severity = "High Probability PTSD"
            interpretation = "Score suggests high probability of PTSD. Comprehensive clinical assessment and treatment planning recommended."
        
        return severity, interpretation


class OutcomeRatingScale:
    """Outcome Rating Scale (ORS) - Session outcome measurement"""
    
    def __init__(self):
        self.name = "Outcome Rating Scale (ORS)"
        self.instructions = "Rate how you have been doing in the following areas of your life during the past week:"
        
        self.questions = [
            AssessmentQuestion(
                1,
                "Individual (personal well-being)",
                ["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                [0, 2, 4, 6, 8, 10]
            ),
            AssessmentQuestion(
                2,
                "Interpersonal (family, close relationships)",
                ["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                [0, 2, 4, 6, 8, 10]
            ),
            AssessmentQuestion(
                3,
                "Social (work, school, friendships)",
                ["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                [0, 2, 4, 6, 8, 10]
            ),
            AssessmentQuestion(
                4,
                "Overall (general sense of well-being)",
                ["Very Poor", "Poor", "Fair", "Good", "Excellent"],
                [0, 2, 4, 6, 8, 10]
            )
        ]
    
    def interpret_score(self, score: int) -> Tuple[str, str]:
        """Interpret ORS score"""
        if score < 25:
            severity = "Clinical Range"
            interpretation = "Score suggests significant distress. Individual may benefit from therapeutic intervention."
        else:
            severity = "Functioning Range"
            interpretation = "Score suggests adequate functioning and well-being."
        
        return severity, interpretation


class SessionRatingScale:
    """Session Rating Scale (SRS) - Therapeutic alliance measurement"""
    
    def __init__(self):
        self.name = "Session Rating Scale (SRS)"
        self.instructions = "Please rate today's session by placing a mark on the line nearest to the description that best fits your experience:"
        
        self.questions = [
            AssessmentQuestion(
                1,
                "I did not feel heard, understood, and respected ←→ I felt heard, understood, and respected",
                ["Not at all", "Slightly", "Moderately", "Considerably", "Completely"],
                [0, 2, 4, 6, 8, 10]
            ),
            AssessmentQuestion(
                2,
                "We did not work on or talk about what I wanted ←→ We worked on and talked about what I wanted",
                ["Not at all", "Slightly", "Moderately", "Considerably", "Completely"],
                [0, 2, 4, 6, 8, 10]
            ),
            AssessmentQuestion(
                3,
                "The therapist's approach is not a good fit ←→ The therapist's approach is a good fit for me",
                ["Not at all", "Slightly", "Moderately", "Considerably", "Completely"],
                [0, 2, 4, 6, 8, 10]
            ),
            AssessmentQuestion(
                4,
                "There was something missing in the session today ←→ Overall, today's session was right for me",
                ["Not at all", "Slightly", "Moderately", "Considerably", "Completely"],
                [0, 2, 4, 6, 8, 10]
            )
        ]
    
    def interpret_score(self, score: int) -> Tuple[str, str]:
        """Interpret SRS score"""
        if score < 36:
            severity = "Below Cutoff"
            interpretation = "Session alliance may need attention. Consider discussing the therapeutic relationship and approach."
        else:
            severity = "Above Cutoff"
            interpretation = "Good therapeutic alliance and session satisfaction indicated."
        
        return severity, interpretation


def main():
    """Test function for assessment system"""
    from database import DatabaseManager
    
    db = DatabaseManager()
    assessment_system = AssessmentSystem(db)
    
    # Example usage
    print("Assessment System Test")
    print("Available assessments: PHQ9, GAD7, PCL5, ORS, SRS")
    
    assessment_type = input("Enter assessment type: ").upper()
    patient_id = int(input("Enter patient ID: "))
    
    try:
        assessment = assessment_system.run_assessment(patient_id, assessment_type)
        print(f"Assessment completed with ID: {assessment.id}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()