#!/usr/bin/env python3
"""
AI Therapy System - Configuration and Protocols
All system configuration and evidence-based therapy protocol definitions
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class Config:
    """System configuration settings"""
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-api-key-here')
    GEMINI_MODEL = 'gemini-1.5-pro'
    GEMINI_MAX_TOKENS = 8192
    GEMINI_TEMPERATURE = 0.7
    GEMINI_TOP_P = 0.8
    GEMINI_TOP_K = 40
    
    # Database Configuration
    DATABASE_PATH = 'therapy.db'
    BACKUP_INTERVAL = 24  # hours
    MAX_BACKUP_FILES = 7
    DATABASE_TIMEOUT = 30  # seconds
    
    # Session Configuration
    DEFAULT_SESSION_DURATION = 50  # minutes
    SESSION_PHASES = ['opening', 'homework_review', 'main_work', 'skill_practice', 'homework_assignment', 'closing']
    SESSION_REMINDER_TIME = 5  # minutes before session
    MAX_SESSION_HISTORY = 100
    
    # Clinical Assessment Thresholds
    PHQ9_CUTOFFS = {
        'minimal': (0, 4),
        'mild': (5, 9),
        'moderate': (10, 14),
        'moderately_severe': (15, 19),
        'severe': (20, 27)
    }
    
    GAD7_CUTOFFS = {
        'minimal': (0, 4),
        'mild': (5, 9),
        'moderate': (10, 14),
        'severe': (15, 21)
    }
    
    PCL5_CUTOFFS = {
        'below_threshold': (0, 30),
        'probable_ptsd': (31, 49),
        'high_probability': (50, 80)
    }
    
    ORS_CUTOFF = 25  # Below indicates clinical distress
    SRS_CUTOFF = 36  # Below indicates alliance issues
    
    # Crisis Keywords and Risk Levels
    CRISIS_KEYWORDS = {
        'high_risk': [
            'suicide', 'kill myself', 'end it all', 'better off dead',
            'want to die', 'going to hurt myself', 'planning to die',
            'overdose', 'cutting myself', 'hanging myself'
        ],
        'moderate_risk': [
            'hurt myself', 'self harm', 'cutting', 'worthless',
            'hopeless', 'cant go on', 'no point', 'give up'
        ],
        'low_risk': [
            'sad', 'depressed', 'anxious', 'worried', 'stressed'
        ]
    }
    
    # Emergency Resources
    CRISIS_RESOURCES = {
        'suicide_hotline': '988',
        'crisis_text': 'Text HOME to 741741',
        'emergency': '911',
        'online_chat': 'suicidepreventionlifeline.org/chat'
    }
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'therapy_system.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Security Settings
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default-key-change-me')
    SESSION_TIMEOUT = 60  # minutes
    MAX_LOGIN_ATTEMPTS = 3
    
    # Documentation Settings
    DOCUMENTATION_TEMPLATES = {
        'soap_note': True,
        'progress_note': True,
        'treatment_plan': True,
        'crisis_plan': True,
        'discharge_summary': True
    }


class TherapyProtocols:
    """Evidence-based therapy protocols and interventions"""
    
    # Cognitive Behavioral Therapy (CBT) Protocols
    CBT_INTERVENTIONS = {
        'cognitive_restructuring': {
            'name': 'Cognitive Restructuring',
            'description': 'Identifying and challenging negative thought patterns and cognitive distortions',
            'techniques': [
                'Thought records and analysis',
                'Evidence examination (for/against)',
                'Alternative perspective generation',
                'Cost-benefit analysis',
                'Behavioral experiments',
                'Hypothesis testing'
            ],
            'target_symptoms': ['depression', 'anxiety', 'negative_thinking', 'catastrophizing'],
            'session_time': 15,
            'homework_options': [
                'Daily thought record',
                'Evidence collection worksheet',
                'Alternative thoughts log'
            ]
        },
        'behavioral_activation': {
            'name': 'Behavioral Activation',
            'description': 'Increasing engagement in positive and meaningful activities',
            'techniques': [
                'Activity scheduling',
                'Pleasure and mastery rating',
                'Goal setting and planning',
                'Activity monitoring',
                'Graded task assignment',
                'Value-based activity selection'
            ],
            'target_symptoms': ['depression', 'low_motivation', 'anhedonia', 'isolation'],
            'session_time': 20,
            'homework_options': [
                'Weekly activity schedule',
                'Pleasant activity log',
                'Goal achievement tracker'
            ]
        },
        'exposure_therapy': {
            'name': 'Exposure Therapy',
            'description': 'Gradual exposure to feared situations or stimuli',
            'techniques': [
                'Fear hierarchy development',
                'Systematic desensitization',
                'In-vivo exposure',
                'Imaginal exposure',
                'Response prevention',
                'Flooding (when appropriate)'
            ],
            'target_symptoms': ['anxiety', 'phobias', 'ptsd', 'avoidance'],
            'session_time': 25,
            'homework_options': [
                'Daily exposure exercises',
                'Anxiety rating log',
                'Avoidance behavior tracker'
            ]
        },
        'problem_solving': {
            'name': 'Problem Solving Training',
            'description': 'Structured approach to identifying and solving life problems',
            'techniques': [
                'Problem identification',
                'Goal setting',
                'Solution generation',
                'Decision making',
                'Solution implementation',
                'Outcome evaluation'
            ],
            'target_symptoms': ['depression', 'anxiety', 'life_stress', 'decision_making'],
            'session_time': 15,
            'homework_options': [
                'Problem-solving worksheet',
                'Solution implementation plan',
                'Outcome tracking log'
            ]
        }
    }
    
    # Dialectical Behavior Therapy (DBT) Modules
    DBT_MODULES = {
        'mindfulness': {
            'name': 'Mindfulness Skills',
            'description': 'Core mindfulness skills for present-moment awareness',
            'core_skills': {
                'what_skills': ['Observe', 'Describe', 'Participate'],
                'how_skills': ['Non-judgmentally', 'One-mindfully', 'Effectively']
            },
            'techniques': [
                'Breathing meditation',
                'Body scan',
                'Mindful observation',
                'Present moment awareness',
                'Acceptance practice',
                'Letting go exercises'
            ],
            'target_symptoms': ['emotional_dysregulation', 'impulsivity', 'dissociation'],
            'session_time': 20,
            'homework_options': [
                'Daily mindfulness practice',
                'Mindfulness diary',
                'Present moment exercises'
            ]
        },
        'distress_tolerance': {
            'name': 'Distress Tolerance Skills',
            'description': 'Skills for surviving crisis situations without making them worse',
            'crisis_skills': {
                'TIPP': ['Temperature', 'Intense exercise', 'Paced breathing', 'Paired muscle relaxation'],
                'distraction': ['Activities', 'Contributing', 'Comparisons', 'Emotions', 'Push away', 'Thoughts', 'Sensations'],
                'self_soothing': ['Vision', 'Hearing', 'Smell', 'Taste', 'Touch'],
                'improve': ['Imagery', 'Meaning', 'Prayer', 'Relaxation', 'One thing', 'Vacation', 'Encouragement']
            },
            'acceptance_skills': ['Radical acceptance', 'Turning the mind', 'Willingness'],
            'target_symptoms': ['crisis_situations', 'self_harm_urges', 'impulsivity', 'overwhelming_emotions'],
            'session_time': 25,
            'homework_options': [
                'Distress tolerance skills practice',
                'Crisis survival kit',
                'Radical acceptance exercises'
            ]
        },
        'emotion_regulation': {
            'name': 'Emotion Regulation Skills',
            'description': 'Skills for understanding and managing emotions effectively',
            'skills': {
                'understanding_emotions': ['Functions of emotions', 'Emotion identification', 'Emotion myths'],
                'changing_emotions': ['Opposite action', 'Problem solving', 'PLEASE skills'],
                'reducing_vulnerability': ['Treat physical illness', 'Balance eating', 'Avoid substances', 'Balance sleep', 'Get exercise'],
                'mindfulness_of_emotions': ['Observe emotions', 'Experience emotions', 'Label emotions']
            },
            'target_symptoms': ['emotional_dysregulation', 'mood_swings', 'intensity', 'emotional_avoidance'],
            'session_time': 20,
            'homework_options': [
                'Emotion diary card',
                'Opposite action practice',
                'PLEASE skills tracker'
            ]
        },
        'interpersonal_effectiveness': {
            'name': 'Interpersonal Effectiveness Skills',
            'description': 'Skills for maintaining relationships while achieving goals',
            'skills': {
                'asking_effectively': 'DEAR MAN',
                'maintaining_relationships': 'GIVE',
                'maintaining_self_respect': 'FAST'
            },
            'techniques': [
                'Objective effectiveness',
                'Relationship effectiveness',
                'Self-respect effectiveness',
                'Factors that interfere',
                'Building mastery'
            ],
            'target_symptoms': ['relationship_problems', 'communication_issues', 'boundary_problems'],
            'session_time': 20,
            'homework_options': [
                'Interpersonal situation analysis',
                'Communication skills practice',
                'Relationship goals tracker'
            ]
        }
    }
    
    # Acceptance and Commitment Therapy (ACT) Processes
    ACT_PROCESSES = {
        'psychological_flexibility': {
            'name': 'Psychological Flexibility',
            'description': 'The ability to stay present and take action guided by values',
            'core_processes': {
                'acceptance': {
                    'description': 'Willingness to experience difficult thoughts, feelings, and sensations',
                    'techniques': ['Acceptance exercises', 'Willingness practices', 'Creative hopelessness'],
                    'target_symptoms': ['avoidance', 'emotional_suppression', 'experiential_avoidance']
                },
                'cognitive_defusion': {
                    'description': 'Creating psychological distance from thoughts',
                    'techniques': ['Leaves on a stream', 'Silly voices', 'Thank your mind', 'Passengers on the bus'],
                    'target_symptoms': ['cognitive_fusion', 'rumination', 'thought_suppression']
                },
                'present_moment': {
                    'description': 'Flexible attention to the here and now',
                    'techniques': ['Mindfulness exercises', 'Present moment awareness', 'Attention training'],
                    'target_symptoms': ['rumination', 'worry', 'dissociation']
                },
                'self_as_context': {
                    'description': 'Flexible sense of self as the context for experiences',
                    'techniques': ['Observer self exercises', 'Self-as-context metaphors', 'Perspective-taking'],
                    'target_symptoms': ['self_criticism', 'identity_issues', 'self_concept_rigidity']
                },
                'values': {
                    'description': 'Chosen life directions that give meaning and purpose',
                    'techniques': ['Values clarification', 'Values card sort', 'Life domains exploration'],
                    'target_symptoms': ['lack_of_direction', 'meaninglessness', 'value_confusion']
                },
                'committed_action': {
                    'description': 'Taking steps toward valued goals despite obstacles',
                    'techniques': ['Goal setting', 'Barrier identification', 'Action planning', 'SMART goals'],
                    'target_symptoms': ['procrastination', 'goal_avoidance', 'behavioral_inflexibility']
                }
            }
        }
    }
    
    # Psychodynamic Therapy Approaches
    PSYCHODYNAMIC_APPROACHES = {
        'insight_oriented': {
            'name': 'Insight-Oriented Therapy',
            'description': 'Exploring unconscious patterns and gaining self-understanding',
            'techniques': {
                'free_association': 'Encouraging spontaneous expression of thoughts and feelings',
                'interpretation': 'Offering insights about unconscious patterns and meanings',
                'transference_analysis': 'Examining relationship patterns reflected in therapy',
                'defense_analysis': 'Identifying and exploring psychological defenses',
                'dream_work': 'Exploring symbolic content of dreams',
                'here_and_now': 'Focusing on immediate emotional experiences'
            },
            'target_symptoms': ['relationship_patterns', 'recurring_themes', 'unconscious_conflicts'],
            'session_time': 30,
            'focus_areas': [
                'Childhood experiences and their impact',
                'Repetitive relationship patterns',
                'Defense mechanisms and coping styles',
                'Unconscious motivations and conflicts',
                'Emotional processing and integration'
            ]
        }
    }


class SessionStructures:
    """Session templates and timing for different therapy modalities"""
    
    STANDARD_SESSION = {
        'total_duration': 50,
        'phases': {
            'opening': {
                'duration': 5,
                'activities': ['Greeting', 'Check-in', 'Mood assessment', 'Session agenda']
            },
            'homework_review': {
                'duration': 10,
                'activities': ['Review assignments', 'Discuss insights', 'Problem-solve obstacles']
            },
            'main_work': {
                'duration': 25,
                'activities': ['Primary intervention', 'Skill practice', 'Problem exploration']
            },
            'skill_practice': {
                'duration': 5,
                'activities': ['In-session rehearsal', 'Role-play', 'Technique demonstration']
            },
            'homework_assignment': {
                'duration': 3,
                'activities': ['Assign practice', 'Clarify instructions', 'Set goals']
            },
            'wrap_up': {
                'duration': 2,
                'activities': ['Session summary', 'Feedback', 'Scheduling']
            }
        }
    }
    
    CBT_SESSION = {
        'total_duration': 50,
        'structure': 'Standard CBT format with thought record review',
        'opening': 5,
        'homework_review': 10,
        'agenda_setting': 5,
        'main_intervention': 20,
        'homework_assignment': 5,
        'summary_feedback': 5
    }
    
    DBT_SESSION = {
        'total_duration': 50,
        'structure': 'Skills-focused with mindfulness',
        'mindfulness_practice': 5,
        'homework_review': 10,
        'skills_training': 25,
        'practice_exercise': 7,
        'wrap_up': 3
    }
    
    ACT_SESSION = {
        'total_duration': 50,
        'structure': 'Values-focused with experiential exercises',
        'check_in': 5,
        'values_connection': 10,
        'experiential_exercise': 20,
        'processing': 10,
        'commitment': 5
    }


class HomeworkTemplates:
    """Pre-designed homework assignments for different modalities"""
    
    CBT_HOMEWORK = {
        'thought_record': {
            'name': 'Thought Record Worksheet',
            'description': 'Track negative thoughts and practice cognitive restructuring',
            'instructions': [
                '1. Notice when you feel upset or anxious',
                '2. Write down the situation that triggered the feeling',
                '3. Identify the automatic thoughts',
                '4. Rate the intensity of emotions (0-10)',
                '5. Examine evidence for and against the thoughts',
                '6. Develop more balanced alternative thoughts',
                '7. Rate emotions again after reframing'
            ],
            'frequency': 'Daily for one week',
            'target_skills': ['cognitive_restructuring', 'thought_awareness']
        },
        'activity_schedule': {
            'name': 'Weekly Activity Schedule',
            'description': 'Plan and track activities to improve mood and functioning',
            'instructions': [
                '1. Plan activities for each day of the week',
                '2. Include a mix of necessary, pleasant, and meaningful activities',
                '3. Rate each activity for pleasure (P) and mastery (M) on 0-10 scale',
                '4. Notice patterns between activities and mood',
                '5. Adjust schedule based on what works'
            ],
            'frequency': 'Daily planning and rating',
            'target_skills': ['behavioral_activation', 'mood_monitoring']
        },
        'exposure_log': {
            'name': 'Exposure Practice Log',
            'description': 'Gradual exposure to feared situations or objects',
            'instructions': [
                '1. Choose a situation from your fear hierarchy',
                '2. Rate anxiety before exposure (0-10)',
                '3. Stay in situation until anxiety decreases by half',
                '4. Rate anxiety after exposure',
                '5. Note any insights or learning',
                '6. Plan next exposure step'
            ],
            'frequency': 'As scheduled in treatment plan',
            'target_skills': ['anxiety_reduction', 'avoidance_decrease']
        }
    }
    
    DBT_HOMEWORK = {
        'distress_tolerance_practice': {
            'name': 'Distress Tolerance Skills Practice',
            'description': 'Practice crisis survival skills',
            'instructions': [
                '1. Identify a distressing situation',
                '2. Choose appropriate distress tolerance skill',
                '3. Apply the skill fully',
                '4. Rate distress before and after (0-10)',
                '5. Note which skills work best for you'
            ],
            'frequency': 'Use as needed during distressing moments',
            'skills_focus': ['TIPP', 'distraction', 'self_soothing', 'IMPROVE']
        },
        'emotion_diary': {
            'name': 'Daily Emotion Diary',
            'description': 'Track emotions and practice regulation skills',
            'instructions': [
                '1. Record primary emotion each day',
                '2. Rate intensity (0-10)',
                '3. Identify prompting event',
                '4. Note body sensations and thoughts',
                '5. Record any skills used',
                '6. Rate effectiveness of skills'
            ],
            'frequency': 'Daily entry',
            'skills_focus': ['emotion_identification', 'regulation_skills']
        },
        'mindfulness_practice': {
            'name': 'Daily Mindfulness Practice',
            'description': 'Regular mindfulness skill practice',
            'instructions': [
                '1. Choose a mindfulness exercise',
                '2. Practice for designated time',
                '3. Note what you observed',
                '4. Rate how mindful you felt (0-10)',
                '5. Notice any judgments or distractions'
            ],
            'frequency': 'Daily 10-15 minutes',
            'skills_focus': ['observe', 'describe', 'participate']
        }
    }
    
    ACT_HOMEWORK = {
        'values_exploration': {
            'name': 'Values Clarification Exercise',
            'description': 'Explore and identify core personal values',
            'instructions': [
                '1. Review different life domains (relationships, work, health, etc.)',
                '2. Identify what truly matters to you in each area',
                '3. Write values statements for top 3-5 values',
                '4. Rate how well you are living each value (0-10)',
                '5. Identify one small action toward each value'
            ],
            'frequency': 'Weekly review and daily actions',
            'skills_focus': ['values_clarity', 'committed_action']
        },
        'defusion_practice': {
            'name': 'Cognitive Defusion Exercises',
            'description': 'Practice creating distance from difficult thoughts',
            'instructions': [
                '1. Notice a difficult or unhelpful thought',
                '2. Try a defusion technique (silly voice, "I\'m having the thought that...", etc.)',
                '3. Rate how much you believe the thought before and after (0-10)',
                '4. Note any changes in emotional intensity',
                '5. Continue with valued action'
            ],
            'frequency': 'As needed when struggling with thoughts',
            'skills_focus': ['cognitive_defusion', 'psychological_flexibility']
        },
        'mindful_action': {
            'name': 'Mindful Values-Based Action',
            'description': 'Practice taking action guided by values with full awareness',
            'instructions': [
                '1. Choose a values-based action for the day',
                '2. Before acting, connect with why this matters to you',
                '3. Perform the action with full attention',
                '4. Notice any difficult thoughts/feelings that arise',
                '5. Continue action regardless of internal experiences',
                '6. Reflect on the experience'
            ],
            'frequency': 'Daily values-based actions',
            'skills_focus': ['mindfulness', 'values', 'committed_action']
        }
    }


class ClinicalGuidelines:
    """Clinical guidelines and best practices"""
    
    RISK_ASSESSMENT_PROTOCOLS = {
        'suicide_risk': {
            'assessment_frequency': 'Every session for high-risk clients',
            'risk_factors': [
                'Previous suicide attempts',
                'Severe depression or hopelessness',
                'Substance abuse',
                'Social isolation',
                'Recent major losses',
                'Access to lethal means',
                'Impulsivity',
                'Chronic pain or illness'
            ],
            'protective_factors': [
                'Strong therapeutic relationship',
                'Family support',
                'Religious or spiritual beliefs',
                'Responsibility to children/pets',
                'Future goals and plans',
                'Problem-solving skills'
            ],
            'intervention_levels': {
                'low': 'Regular monitoring, safety planning',
                'moderate': 'Increased session frequency, detailed safety plan',
                'high': 'Consider hospitalization, immediate intervention'
            }
        }
    }
    
    DOCUMENTATION_STANDARDS = {
        'progress_notes': {
            'format': 'SOAP (Subjective, Objective, Assessment, Plan)',
            'required_elements': [
                'Date and duration of session',
                'Patient presentation and mood',
                'Interventions used',
                'Patient response to interventions',
                'Homework assignments',
                'Risk assessment (if applicable)',
                'Plan for next session'
            ]
        },
        'treatment_plans': {
            'review_frequency': 'Every 4-6 sessions or as needed',
            'required_elements': [
                'Primary diagnosis',
                'Treatment goals (SMART format)',
                'Interventions to be used',
                'Frequency of sessions',
                'Expected duration of treatment',
                'Discharge criteria'
            ]
        }
    }


def get_intervention_by_symptom(symptom: str, modality: str = None) -> List[Dict[str, Any]]:
    """Get recommended interventions based on presenting symptom"""
    interventions = []
    
    # Search across all modalities if none specified
    modalities_to_search = [modality] if modality else ['CBT', 'DBT', 'ACT', 'Psychodynamic']
    
    for mod in modalities_to_search:
        if mod == 'CBT':
            for key, intervention in TherapyProtocols.CBT_INTERVENTIONS.items():
                if symptom.lower() in [s.lower() for s in intervention.get('target_symptoms', [])]:
                    interventions.append({
                        'modality': 'CBT',
                        'intervention': key,
                        'details': intervention
                    })
    
    return interventions


def get_session_structure(modality: str) -> Dict[str, Any]:
    """Get session structure for specific modality"""
    structures = {
        'CBT': SessionStructures.CBT_SESSION,
        'DBT': SessionStructures.DBT_SESSION,
        'ACT': SessionStructures.ACT_SESSION,
        'Standard': SessionStructures.STANDARD_SESSION
    }
    return structures.get(modality, structures['Standard'])


def get_homework_options(modality: str, skill_focus: str = None) -> List[Dict[str, Any]]:
    """Get homework options for specific modality and skill focus"""
    homework_dict = {
        'CBT': HomeworkTemplates.CBT_HOMEWORK,
        'DBT': HomeworkTemplates.DBT_HOMEWORK,
        'ACT': HomeworkTemplates.ACT_HOMEWORK
    }
    
    if modality in homework_dict:
        homework_options = homework_dict[modality]
        if skill_focus:
            # Filter by skill focus if specified
            filtered_options = {}
            for key, hw in homework_options.items():
                if skill_focus in hw.get('target_skills', []) or skill_focus in hw.get('skills_focus', []):
                    filtered_options[key] = hw
            return filtered_options
        return homework_options
    
    return {}


# Module test function
def main():
    """Test configuration and protocol access"""
    print("Therapy System Configuration Test")
    print(f"Gemini Model: {Config.GEMINI_MODEL}")
    print(f"Database Path: {Config.DATABASE_PATH}")
    print(f"Session Duration: {Config.DEFAULT_SESSION_DURATION} minutes")
    
    print("\nAvailable CBT Interventions:")
    for name, details in TherapyProtocols.CBT_INTERVENTIONS.items():
        print(f"- {details['name']}: {details['description']}")
    
    print("\nDBT Core Modules:")
    for name, details in TherapyProtocols.DBT_MODULES.items():
        print(f"- {details['name']}: {details['description']}")
    
    print("\nTesting symptom-based intervention lookup:")
    depression_interventions = get_intervention_by_symptom('depression')
    for intervention in depression_interventions:
        print(f"- {intervention['modality']}: {intervention['intervention']}")


if __name__ == "__main__":
    main()