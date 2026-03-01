#!/usr/bin/env python3
"""
AI Therapy System - Crisis Intervention and Safety Management
Comprehensive crisis intervention protocols, risk assessment, and safety planning
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from config import Config
from database import DatabaseManager
from models import Patient
from utils import log_action


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    IMMINENT = "imminent"


class CrisisType(Enum):
    """Types of crisis situations"""
    SUICIDE = "suicide"
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    PSYCHOSIS = "psychosis"
    SUBSTANCE_ABUSE = "substance_abuse"
    DOMESTIC_VIOLENCE = "domestic_violence"
    CHILD_ABUSE = "child_abuse"


@dataclass
class CrisisAlert:
    """Crisis alert data structure"""
    id: Optional[int] = None
    patient_id: int = 0
    crisis_type: str = ""
    crisis_level: str = "low"
    risk_level: str = RiskLevel.LOW.value
    trigger_text: str = ""
    assessment_score: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False
    interventions_used: List[str] = field(default_factory=list)
    follow_up_required: bool = True
    notes: str = ""


@dataclass 
class SafetyPlan:
    """Safety plan data structure"""
    id: Optional[int] = None
    patient_id: int = 0
    warning_signs: List[str] = field(default_factory=list)
    coping_strategies: List[str] = field(default_factory=list)
    social_supports: List[Dict[str, str]] = field(default_factory=list)
    professional_contacts: List[Dict[str, str]] = field(default_factory=list)
    environmental_safety: List[str] = field(default_factory=list)
    reasons_for_living: List[str] = field(default_factory=list)
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    active: bool = True


class CrisisManager:
    """Manages crisis detection, intervention, and safety planning"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.active_alerts: Dict[int, CrisisAlert] = {}
    
    def _init_crisis_tables(self):
        """Initialize crisis-related database tables"""
        with self.db.get_connection() as conn:
            
            # Crisis alerts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS crisis_alerts (
                    id INTEGER PRIMARY KEY,
                    patient_id INTEGER,
                    crisis_type TEXT,
                    risk_level TEXT,
                    trigger_text TEXT,
                    assessment_score INTEGER,
                    timestamp TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    interventions_used TEXT,
                    follow_up_required BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            ''')
            
            # Safety plans table (already exists in main schema, but ensure it's there)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS safety_plans (
                    id INTEGER PRIMARY KEY,
                    patient_id INTEGER,
                    warning_signs TEXT,
                    coping_strategies TEXT,
                    social_supports TEXT,
                    professional_contacts TEXT,
                    environmental_safety TEXT,
                    reasons_for_living TEXT,
                    created_date TEXT,
                    last_updated TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def detect_crisis(self, text: str, patient_id: int) -> Optional[CrisisAlert]:
        """Detect crisis indicators in user input"""
        text_lower = text.lower()
        
        # Check for different types of crisis indicators
        crisis_detected = None
        risk_level = RiskLevel.LOW
        crisis_type = None
        
        # Suicide risk detection
        suicide_score = self._assess_suicide_risk_from_text(text_lower)
        if suicide_score > 0:
            crisis_type = CrisisType.SUICIDE
            if suicide_score >= 7:
                risk_level = RiskLevel.IMMINENT
            elif suicide_score >= 5:
                risk_level = RiskLevel.HIGH
            elif suicide_score >= 3:
                risk_level = RiskLevel.MODERATE
            else:
                risk_level = RiskLevel.LOW
        
        # Self-harm detection
        elif any(keyword in text_lower for keyword in ['cut myself', 'hurt myself', 'self harm', 'cutting', 'burning myself']):
            crisis_type = CrisisType.SELF_HARM
            risk_level = RiskLevel.MODERATE
        
        # Violence indicators
        elif any(keyword in text_lower for keyword in ['kill someone', 'hurt others', 'violence', 'revenge']):
            crisis_type = CrisisType.VIOLENCE
            risk_level = RiskLevel.HIGH
        
        # Psychosis indicators
        elif any(keyword in text_lower for keyword in ['voices telling me', 'hearing voices', 'people watching me', 'conspiracy']):
            crisis_type = CrisisType.PSYCHOSIS
            risk_level = RiskLevel.MODERATE
        
        # Substance abuse crisis
        elif any(keyword in text_lower for keyword in ['overdose', 'too many pills', 'drinking too much', 'using again']):
            crisis_type = CrisisType.SUBSTANCE_ABUSE
            risk_level = RiskLevel.MODERATE
        
        # If crisis detected, create alert
        if crisis_type:
            crisis_alert = CrisisAlert(
                patient_id=patient_id,
                crisis_type=crisis_type.value,
                risk_level=risk_level.value,
                trigger_text=text[:500],  # Store first 500 chars
                assessment_score=suicide_score if crisis_type == CrisisType.SUICIDE else 0
            )
            
            # Save to database
            self._save_crisis_alert(crisis_alert)
            
            # Add to active alerts
            self.active_alerts[patient_id] = crisis_alert
            
            log_action(f"Crisis detected: {crisis_type.value} - {risk_level.value}", 
                      "crisis_manager", "WARNING", patient_id=patient_id)
            
            return crisis_alert
        
        return False
    
    def _assess_suicide_risk_from_text(self, text: str) -> int:
        """Assess suicide risk from text using keyword scoring"""
        risk_score = 0
        
        # High-risk keywords (3 points each)
        high_risk = ['suicide', 'kill myself', 'end my life', 'better off dead', 
                    'want to die', 'going to die', 'planning to die', 'end it all']
        for keyword in high_risk:
            if keyword in text:
                risk_score += 3
        
        # Moderate-risk keywords (2 points each)
        moderate_risk = ['hurt myself', 'harm myself', 'overdose', 'hanging', 
                        'jumping', 'worthless', 'hopeless', 'no point living']
        for keyword in moderate_risk:
            if keyword in text:
                risk_score += 2
        
        # Method-specific keywords (2 points each)
        methods = ['pills', 'rope', 'bridge', 'gun', 'knife', 'cutting']
        for method in methods:
            if method in text:
                risk_score += 2
        
        # Protective factors (subtract points)
        protective = ['family', 'children', 'future', 'hope', 'help', 'support']
        for factor in protective:
            if factor in text:
                risk_score = max(0, risk_score - 1)
        
        return min(risk_score, 10)  # Cap at 10
    
    def conduct_suicide_risk_assessment(self, patient_id: int) -> Dict[str, Any]:
        """Conduct comprehensive suicide risk assessment"""
        print("\n" + "="*60)
        print("SUICIDE RISK ASSESSMENT")
        print("="*60)
        print("Please answer the following questions honestly. This information")
        print("will help us ensure your safety and provide appropriate care.\n")
        
        questions = [
            {
                'question': 'Have you been having thoughts about death or dying?',
                'weight': 2,
                'type': 'yes_no'
            },
            {
                'question': 'Have you been thinking about hurting yourself?',
                'weight': 3,
                'type': 'yes_no'
            },
            {
                'question': 'Have you been thinking about suicide?',
                'weight': 4,
                'type': 'yes_no'
            },
            {
                'question': 'Do you have a plan for how you would hurt yourself?',
                'weight': 3,
                'type': 'yes_no'
            },
            {
                'question': 'Do you have access to means to hurt yourself?',
                'weight': 2,
                'type': 'yes_no'
            },
            {
                'question': 'How likely are you to act on these thoughts? (0-10 scale)',
                'weight': 1,
                'type': 'scale',
                'scale_max': 10
            },
            {
                'question': 'How hopeful do you feel about the future? (0-10 scale)',
                'weight': -1,  # Protective factor
                'type': 'scale',
                'scale_max': 10
            },
            {
                'question': 'How supported do you feel by others? (0-10 scale)',
                'weight': -0.5,  # Protective factor
                'type': 'scale',
                'scale_max': 10
            }
        ]
        
        total_score = 0
        responses = {}
        
        for i, q in enumerate(questions, 1):
            while True:
                print(f"Question {i}: {q['question']}")
                
                if q['type'] == 'yes_no':
                    answer = input("Answer (yes/no): ").lower().strip()
                    if answer in ['yes', 'y', '1', 'true']:
                        score = q['weight']
                        responses[f'q{i}'] = {'answer': 'yes', 'score': score}
                        total_score += score
                        break
                    elif answer in ['no', 'n', '0', 'false']:
                        responses[f'q{i}'] = {'answer': 'no', 'score': 0}
                        break
                    else:
                        print("Please answer yes or no.")
                
                elif q['type'] == 'scale':
                    try:
                        answer = int(input(f"Answer (0-{q['scale_max']}): "))
                        if 0 <= answer <= q['scale_max']:
                            score = answer * q['weight']
                            responses[f'q{i}'] = {'answer': answer, 'score': score}
                            total_score += score
                            break
                        else:
                            print(f"Please enter a number between 0 and {q['scale_max']}.")
                    except ValueError:
                        print("Please enter a valid number.")
                
                print()
        
        # Determine risk level
        if total_score >= 15:
            risk_level = RiskLevel.IMMINENT
        elif total_score >= 10:
            risk_level = RiskLevel.HIGH
        elif total_score >= 5:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW
        
        # Create crisis alert if needed
        if risk_level != RiskLevel.LOW:
            crisis_alert = CrisisAlert(
                patient_id=patient_id,
                crisis_type=CrisisType.SUICIDE.value,
                risk_level=risk_level.value,
                trigger_text="Formal suicide risk assessment",
                assessment_score=int(total_score)
            )
            self._save_crisis_alert(crisis_alert)
        
        assessment_result = {
            'patient_id': patient_id,
            'total_score': total_score,
            'risk_level': risk_level.value,
            'responses': responses,
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._get_risk_recommendations(risk_level)
        }
        
        log_action(f"Suicide risk assessment completed: {risk_level.value}", 
                  "crisis_manager", patient_id=patient_id)
        
        return assessment_result
    
    def _get_risk_recommendations(self, risk_level: RiskLevel) -> List[str]:
        """Get intervention recommendations based on risk level"""
        recommendations = {
            RiskLevel.LOW: [
                "Continue regular therapy sessions",
                "Monitor mood and thoughts",
                "Use coping strategies as needed",
                "Contact therapist if thoughts worsen"
            ],
            RiskLevel.MODERATE: [
                "Increase session frequency",
                "Develop/review safety plan",
                "Remove access to lethal means",
                "Increase social support and monitoring",
                "Consider psychiatric evaluation"
            ],
            RiskLevel.HIGH: [
                "Immediate safety planning required",
                "Consider intensive outpatient treatment",
                "Daily check-ins with support system",
                "Remove all lethal means from environment",
                "Psychiatric evaluation within 24 hours",
                "Consider partial hospitalization"
            ],
            RiskLevel.IMMINENT: [
                "IMMEDIATE INTERVENTION REQUIRED",
                "Do not leave person alone",
                "Contact emergency services if necessary",
                "Escort to emergency room for evaluation",
                "Consider involuntary commitment if needed",
                "Notify all treatment providers immediately"
            ]
        }
        
        return recommendations.get(risk_level, [])
    
    def create_safety_plan(self, patient_id: int) -> SafetyPlan:
        """Create comprehensive safety plan with patient"""
        print("\n" + "="*60)
        print("SAFETY PLAN CREATION")
        print("="*60)
        print("We're going to create a personalized safety plan together.")
        print("This plan will help you stay safe during difficult times.\n")
        
        safety_plan = SafetyPlan(patient_id=patient_id)
        
        # Step 1: Warning signs
        print("STEP 1: Warning Signs")
        print("What are the thoughts, feelings, or situations that might")
        print("indicate you're entering a crisis? (Enter one per line, 'done' to finish)")
        
        while True:
            warning_sign = input("Warning sign: ").strip()
            if warning_sign.lower() == 'done':
                break
            if warning_sign:
                safety_plan.warning_signs.append(warning_sign)
        
        # Step 2: Coping strategies
        print("\nSTEP 2: Coping Strategies")
        print("What are things you can do on your own to feel better?")
        print("(Enter one per line, 'done' to finish)")
        
        suggestions = [
            "Deep breathing exercises",
            "Listen to music",
            "Take a warm bath",
            "Go for a walk",
            "Write in a journal",
            "Practice mindfulness"
        ]
        print("Suggestions:", ", ".join(suggestions))
        
        while True:
            coping_strategy = input("Coping strategy: ").strip()
            if coping_strategy.lower() == 'done':
                break
            if coping_strategy:
                safety_plan.coping_strategies.append(coping_strategy)
        
        # Step 3: Social supports
        print("\nSTEP 3: Social Support Contacts")
        print("Who are people you can talk to when you're in crisis?")
        print("(Enter name and phone number, 'done' to finish)")
        
        while True:
            name = input("Contact name (or 'done'): ").strip()
            if name.lower() == 'done':
                break
            if name:
                phone = input(f"Phone number for {name}: ").strip()
                safety_plan.social_supports.append({
                    'name': name,
                    'phone': phone,
                    'relationship': input(f"Relationship to {name}: ").strip()
                })
        
        # Step 4: Professional contacts
        print("\nSTEP 4: Professional Support Contacts")
        
        # Add standard crisis resources
        safety_plan.professional_contacts = [
            {'name': 'National Suicide Prevention Lifeline', 'phone': '988'},
            {'name': 'Crisis Text Line', 'phone': '741741 (text HOME)'},
            {'name': 'Emergency Services', 'phone': '911'}
        ]
        
        print("Added standard crisis resources. Add any additional professional contacts:")
        while True:
            name = input("Professional contact name (or 'done'): ").strip()
            if name.lower() == 'done':
                break
            if name:
                phone = input(f"Phone number for {name}: ").strip()
                role = input(f"Role/Title of {name}: ").strip()
                safety_plan.professional_contacts.append({
                    'name': name,
                    'phone': phone,
                    'role': role
                })
        
        # Step 5: Environmental safety
        print("\nSTEP 5: Making Environment Safe")
        print("What steps can you take to remove or restrict access to lethal means?")
        
        while True:
            safety_step = input("Safety step (or 'done'): ").strip()
            if safety_step.lower() == 'done':
                break
            if safety_step:
                safety_plan.environmental_safety.append(safety_step)
        
        # Step 6: Reasons for living
        print("\nSTEP 6: Reasons for Living")
        print("What are your reasons for living? What gives your life meaning?")
        
        while True:
            reason = input("Reason for living (or 'done'): ").strip()
            if reason.lower() == 'done':
                break
            if reason:
                safety_plan.reasons_for_living.append(reason)
        
        # Save safety plan
        self._save_safety_plan(safety_plan)
        
        # Display completed plan
        self._display_safety_plan(safety_plan)
        
        log_action("Safety plan created", "crisis_manager", patient_id=patient_id)
        
        return safety_plan
    
    def _save_safety_plan(self, safety_plan: SafetyPlan) -> int:
        """Save safety plan to database"""
        plan_id = self.db.execute_update('''
            INSERT INTO safety_plans 
            (patient_id, warning_signs, coping_strategies, social_supports,
             professional_contacts, environmental_safety, reasons_for_living,
             created_date, last_updated, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            safety_plan.patient_id,
            json.dumps(safety_plan.warning_signs),
            json.dumps(safety_plan.coping_strategies),
            json.dumps(safety_plan.social_supports),
            json.dumps(safety_plan.professional_contacts),
            json.dumps(safety_plan.environmental_safety),
            json.dumps(safety_plan.reasons_for_living),
            safety_plan.created_date,
            safety_plan.last_updated,
            safety_plan.active
        ))
        
        safety_plan.id = plan_id
        return plan_id
    
    def _save_crisis_alert(self, crisis_alert: CrisisAlert) -> int:
        """Save crisis alert to database"""
        alert_id = self.db.execute_update('''
            INSERT INTO crisis_alerts 
            (patient_id, crisis_type, risk_level, trigger_text, assessment_score,
             timestamp, resolved, interventions_used, follow_up_required, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            crisis_alert.patient_id,
            crisis_alert.crisis_type,
            crisis_alert.risk_level,
            crisis_alert.trigger_text,
            crisis_alert.assessment_score,
            crisis_alert.timestamp,
            crisis_alert.resolved,
            json.dumps(crisis_alert.interventions_used),
            crisis_alert.follow_up_required,
            crisis_alert.notes
        ))
        
        crisis_alert.id = alert_id
        return alert_id
    
    def _display_safety_plan(self, safety_plan: SafetyPlan):
        """Display formatted safety plan"""
        print("\n" + "="*60)
        print("YOUR PERSONAL SAFETY PLAN")
        print("="*60)
        
        print("\n1. WARNING SIGNS:")
        for sign in safety_plan.warning_signs:
            print(f"   • {sign}")
        
        print("\n2. COPING STRATEGIES I CAN USE:")
        for strategy in safety_plan.coping_strategies:
            print(f"   • {strategy}")
        
        print("\n3. PEOPLE I CAN CONTACT FOR SUPPORT:")
        for contact in safety_plan.social_supports:
            print(f"   • {contact['name']} - {contact['phone']} ({contact.get('relationship', 'Friend')})")
        
        print("\n4. PROFESSIONAL CONTACTS:")
        for contact in safety_plan.professional_contacts:
            role = contact.get('role', 'Crisis Support')
            print(f"   • {contact['name']} - {contact['phone']} ({role})")
        
        print("\n5. MAKING MY ENVIRONMENT SAFE:")
        for step in safety_plan.environmental_safety:
            print(f"   • {step}")
        
        print("\n6. REASONS FOR LIVING:")
        for reason in safety_plan.reasons_for_living:
            print(f"   • {reason}")
        
        print("\n" + "="*60)
        print("Keep this safety plan with you and use it when you need it!")
        print("="*60)
    
    def get_safety_plan(self, patient_id: int) -> Optional[SafetyPlan]:
        """Retrieve active safety plan for patient"""
        plans = self.db.execute_query(
            "SELECT * FROM safety_plans WHERE patient_id = ? AND active = TRUE ORDER BY created_date DESC LIMIT 1",
            (patient_id,)
        )
        
        if plans:
            plan_data = plans[0]
            return SafetyPlan(
                id=plan_data['id'],
                patient_id=plan_data['patient_id'],
                warning_signs=json.loads(plan_data['warning_signs']),
                coping_strategies=json.loads(plan_data['coping_strategies']),
                social_supports=json.loads(plan_data['social_supports']),
                professional_contacts=json.loads(plan_data['professional_contacts']),
                environmental_safety=json.loads(plan_data['environmental_safety']),
                reasons_for_living=json.loads(plan_data['reasons_for_living']),
                created_date=plan_data['created_date'],
                last_updated=plan_data['last_updated'],
                active=plan_data['active']
            )
        
        return None
    
    def get_crisis_response(self, crisis_alert: CrisisAlert) -> str:
        """Generate appropriate crisis response"""
        risk_level = RiskLevel(crisis_alert.risk_level)
        crisis_type = CrisisType(crisis_alert.crisis_type)
        
        responses = {
            (CrisisType.SUICIDE, RiskLevel.IMMINENT): '''
I'm very concerned about what you've shared. Your safety is the most important thing right now.

IMMEDIATE ACTIONS:
• Do not leave yourself alone
• Contact 988 (Suicide Prevention Lifeline) right now
• Go to your nearest emergency room
• Call 911 if you're in immediate danger

You don't have to go through this alone. There are people who want to help you.
''',
            (CrisisType.SUICIDE, RiskLevel.HIGH): '''
Thank you for sharing what you're going through. I'm concerned about your safety.

IMPORTANT STEPS:
• Contact the Suicide Prevention Lifeline: 988
• Reach out to a trusted friend or family member
• Remove any means of self-harm from your area
• Consider going to an emergency room for evaluation

Your life has value and meaning. Let's work together to keep you safe.
''',
            (CrisisType.SELF_HARM, RiskLevel.MODERATE): '''
I hear that you're struggling and considering hurting yourself. That must be very painful.

HELPFUL ACTIONS:
• Try using distraction techniques (ice, intense exercise, drawing)
• Contact a trusted person for support
• Remove harmful objects from your immediate area
• Call 988 if thoughts intensify

Remember: These feelings are temporary, but the consequences of self-harm can be lasting.
'''
        }
        
        # Get specific response or default
        response_key = (crisis_type, risk_level)
        response = responses.get(response_key)
        
        if not response:
            response = f'''
I notice you may be experiencing {crisis_type.value} thoughts. This is concerning, and I want to help.

RESOURCES AVAILABLE:
• National Suicide Prevention Lifeline: 988
• Crisis Text Line: Text HOME to 741741
• Emergency Services: 911

Please reach out for support. You don't have to handle this alone.
'''
        
        # Add safety plan reference if available
        safety_plan = self.get_safety_plan(crisis_alert.patient_id)
        if safety_plan:
            response += "\n\nPlease refer to your personal safety plan for additional coping strategies and support contacts."
        
        return response.strip()
    
    def resolve_crisis_alert(self, alert_id: int, resolution_notes: str = ""):
        """Mark crisis alert as resolved"""
        self.db.execute_update(
            "UPDATE crisis_alerts SET resolved = TRUE, notes = ? WHERE id = ?",
            (resolution_notes, alert_id)
        )
        
        # Remove from active alerts
        for patient_id, alert in self.active_alerts.items():
            if alert.id == alert_id:
                del self.active_alerts[patient_id]
                break
        
        log_action(f"Crisis alert {alert_id} resolved", "crisis_manager")
    
    def get_patient_crisis_history(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get crisis history for a patient"""
        return self.db.execute_query(
            "SELECT * FROM crisis_alerts WHERE patient_id = ? ORDER BY timestamp DESC",
            (patient_id,)
        )
    
    def check_follow_up_needed(self, patient_id: int) -> bool:
        """Check if crisis follow-up is needed for patient"""
        recent_alerts = self.db.execute_query(
            "SELECT * FROM crisis_alerts WHERE patient_id = ? AND follow_up_required = TRUE AND resolved = FALSE",
            (patient_id,)
        )
        return len(recent_alerts) > 0


def main():
    """Test crisis management system"""
    from database import DatabaseManager
    
    db = DatabaseManager()
    crisis_manager = CrisisManager(db)
    
    print("Crisis Manager Test")
    
    # Test crisis detection
    test_inputs = [
        "I want to kill myself",
        "I'm feeling sad today",
        "I can't take it anymore, I want to end it all",
        "Maybe I should hurt myself"
    ]
    
    for text in test_inputs:
        print(f"\nTesting: '{text}'")
        alert = crisis_manager.detect_crisis(text, patient_id=1)
        if alert:
            print(f"CRISIS DETECTED: {alert.crisis_type} - {alert.risk_level}")
            response = crisis_manager.get_crisis_response(alert)
            print("Response:", response[:100] + "...")
        else:
            print("No crisis detected")


if __name__ == "__main__":
    main()