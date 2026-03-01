"""
AI Therapy System - Therapeutic Interventions Module
Implements CBT, DBT, ACT, and Psychodynamic therapy interventions
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import random
from config import TherapyProtocols


class CBTModule:
    """Cognitive Behavioral Therapy interventions"""
    
    def __init__(self):
        self.cognitive_distortions = {
            'all_or_nothing': {
                'name': 'All-or-Nothing Thinking',
                'description': 'Seeing things in black and white categories',
                'examples': ['I never do anything right', 'This is a complete disaster'],
                'challenge': 'What evidence supports and contradicts this thought?'
            },
            'catastrophizing': {
                'name': 'Catastrophizing',
                'description': 'Expecting the worst possible outcome',
                'examples': ['If I fail this test, my life is ruined', 'One mistake means I\'m a failure'],
                'challenge': 'What is the most realistic outcome?'
            },
            'mental_filter': {
                'name': 'Mental Filter',
                'description': 'Focusing only on negative details',
                'examples': ['Nothing good ever happens to me', 'All I see are my mistakes'],
                'challenge': 'What positive aspects am I not considering?'
            },
            'mind_reading': {
                'name': 'Mind Reading',
                'description': 'Assuming you know what others are thinking',
                'examples': ['They think I\'m stupid', 'Everyone is judging me'],
                'challenge': 'What evidence do I have for what others are thinking?'
            },
            'fortune_telling': {
                'name': 'Fortune Telling',
                'description': 'Predicting negative outcomes without evidence',
                'examples': ['I know I\'ll fail', 'This will never work out'],
                'challenge': 'What other outcomes are possible?'
            }
        }
    
    def cognitive_restructuring(self, patient_thought: str, patient_id: int = None) -> Dict[str, Any]:
        """Main cognitive restructuring intervention"""
        
        # Analyze thought for distortions
        identified_distortions = self._identify_distortions(patient_thought)
        
        restructuring_steps = {
            'original_thought': patient_thought,
            'identified_distortions': identified_distortions,
            'evidence_for': [],
            'evidence_against': [],
            'balanced_thought': '',
            'emotion_before': None,
            'emotion_after': None,
            'homework_assigned': self._generate_thought_record_homework()
        }
        
        # Guiding questions for cognitive restructuring
        guiding_questions = [
            "What evidence supports this thought?",
            "What evidence contradicts this thought?",
            "What would you tell a friend who had this thought?",
            "What's the most realistic way to look at this situation?",
            "How might someone else view this situation?",
            "What's the worst that could realistically happen?",
            "What's the best that could happen?",
            "What's most likely to happen?",
            "How important will this be in 5 years?"
        ]
        
        restructuring_steps['guiding_questions'] = guiding_questions
        
        return restructuring_steps
    
    def behavioral_activation(self, patient_id: int, current_mood: int) -> Dict[str, Any]:
        """Behavioral activation intervention for depression"""
        
        activity_categories = {
            'pleasure': [
                'Listen to favorite music',
                'Watch a funny movie',
                'Take a warm bath',
                'Read for enjoyment',
                'Call a friend',
                'Look at photos',
                'Play with a pet'
            ],
            'mastery': [
                'Complete a small task',
                'Organize one drawer',
                'Learn something new',
                'Exercise for 10 minutes',
                'Cook a simple meal',
                'Write in a journal',
                'Practice a skill'
            ],
            'social': [
                'Text a friend',
                'Have coffee with someone',
                'Join a group activity',
                'Video call family',
                'Help someone else',
                'Attend a social event',
                'Volunteer'
            ],
            'physical': [
                'Take a walk',
                'Do stretching exercises',
                'Garden',
                'Dance to music',
                'Clean a room',
                'Go for a bike ride',
                'Practice yoga'
            ]
        }
        
        # Create personalized activity schedule
        activity_plan = {
            'current_mood': current_mood,
            'target_activities': {},
            'scheduling_guidance': self._create_activity_schedule(),
            'monitoring_sheet': self._create_activity_monitoring_sheet()
        }
        
        # Select activities based on mood level
        if current_mood <= 3:  # Very low mood
            activity_plan['target_activities'] = {
                'immediate': random.sample(activity_categories['pleasure'], 2),
                'daily': random.sample(activity_categories['mastery'], 1)
            }
        elif current_mood <= 6:  # Moderate mood
            activity_plan['target_activities'] = {
                'pleasure': random.sample(activity_categories['pleasure'], 2),
                'mastery': random.sample(activity_categories['mastery'], 2),
                'social': random.sample(activity_categories['social'], 1)
            }
        else:  # Higher mood
            activity_plan['target_activities'] = {
                'maintain': random.sample(activity_categories['pleasure'], 1),
                'build': random.sample(activity_categories['mastery'], 2),
                'connect': random.sample(activity_categories['social'], 2)
            }
        
        return activity_plan
    
    def exposure_therapy_protocol(self, fear_target: str, anxiety_level: int) -> Dict[str, Any]:
        """Create exposure hierarchy for anxiety treatment"""
        
        exposure_plan = {
            'target_fear': fear_target,
            'current_anxiety': anxiety_level,
            'hierarchy_steps': [],
            'exposure_principles': [
                'Start with least anxiety-provoking situations',
                'Stay in situation until anxiety decreases by 50%',
                'Practice regularly and consistently',
                'Use coping skills during exposure',
                'Record anxiety levels before, during, and after'
            ],
            'coping_strategies': [
                'Deep breathing exercises',
                'Progressive muscle relaxation',
                'Grounding techniques (5-4-3-2-1)',
                'Positive self-talk',
                'Mindfulness techniques'
            ]
        }
        
        # Generate sample hierarchy (would be customized in practice)
        sample_hierarchy = self._create_exposure_hierarchy(fear_target)
        exposure_plan['hierarchy_steps'] = sample_hierarchy
        
        return exposure_plan
    
    def _identify_distortions(self, thought: str) -> List[str]:
        """Identify cognitive distortions in a thought"""
        thought_lower = thought.lower()
        identified = []
        
        # Simple keyword-based identification
        distortion_keywords = {
            'all_or_nothing': ['never', 'always', 'everyone', 'no one', 'everything', 'nothing'],
            'catastrophizing': ['disaster', 'terrible', 'awful', 'worst', 'ruined'],
            'mental_filter': ['only', 'just', 'nothing but'],
            'mind_reading': ['they think', 'everyone thinks', 'people think'],
            'fortune_telling': ['will never', 'going to', 'know it will']
        }
        
        for distortion, keywords in distortion_keywords.items():
            if any(keyword in thought_lower for keyword in keywords):
                identified.append(distortion)
        
        return identified
    
    def _generate_thought_record_homework(self) -> Dict[str, Any]:
        """Generate thought record homework assignment"""
        return {
            'assignment_type': 'thought_record',
            'instructions': [
                '1. When you notice feeling upset, write down the situation',
                '2. Identify and record your automatic thoughts',
                '3. Rate the intensity of your emotions (0-10)',
                '4. Look for cognitive distortions in your thoughts',
                '5. Challenge the thoughts with evidence',
                '6. Write a more balanced alternative thought',
                '7. Re-rate your emotion intensity'
            ],
            'duration': '1 week',
            'frequency': 'Daily or when distressed'
        }
    
    def _create_activity_schedule(self) -> Dict[str, Any]:
        """Create weekly activity scheduling template"""
        return {
            'schedule_type': 'weekly_planner',
            'time_slots': ['Morning', 'Afternoon', 'Evening'],
            'activity_rating': 'Rate pleasure (P) and mastery (M) 0-10',
            'instructions': [
                'Plan at least one pleasant activity daily',
                'Include one mastery activity daily',
                'Schedule activities at optimal energy times',
                'Start small and build gradually'
            ]
        }
    
    def _create_activity_monitoring_sheet(self) -> Dict[str, Any]:
        """Create activity monitoring worksheet"""
        return {
            'tracking_elements': [
                'Activity description',
                'Time spent',
                'Mood before (0-10)',
                'Mood after (0-10)',
                'Pleasure rating (0-10)',
                'Mastery rating (0-10)',
                'Notes/observations'
            ],
            'review_questions': [
                'Which activities improved my mood most?',
                'What patterns do I notice?',
                'What activities should I do more often?',
                'What barriers prevented me from doing activities?'
            ]
        }
    
    def _create_exposure_hierarchy(self, fear_target: str) -> List[Dict[str, Any]]:
        """Create sample exposure hierarchy"""
        # This would be customized based on specific fears
        return [
            {'step': 1, 'description': f'Look at pictures related to {fear_target}', 'anxiety_level': '2-3'},
            {'step': 2, 'description': f'Watch videos about {fear_target}', 'anxiety_level': '3-4'},
            {'step': 3, 'description': f'Imagine {fear_target} scenario', 'anxiety_level': '4-5'},
            {'step': 4, 'description': f'Approach {fear_target} from distance', 'anxiety_level': '5-6'},
            {'step': 5, 'description': f'Brief contact with {fear_target}', 'anxiety_level': '6-7'},
            {'step': 6, 'description': f'Extended contact with {fear_target}', 'anxiety_level': '7-8'}
        ]


class DBTModule:
    """Dialectical Behavior Therapy skills module"""
    
    def __init__(self):
        self.distress_tolerance_skills = {
            'TIPP': {
                'name': 'TIPP (Temperature, Intense exercise, Paced breathing, Paired muscle relaxation)',
                'description': 'Quick crisis survival skills',
                'techniques': [
                    'Cold water on face/hands',
                    'Intense exercise for 10 minutes',
                    'Breathing out longer than breathing in',
                    'Tense and release muscle groups'
                ]
            },
            'ACCEPTS': {
                'name': 'ACCEPTS (Activities, Contributing, Comparisons, Emotions, Push away, Thoughts, Sensations)',
                'description': 'Distraction techniques',
                'techniques': [
                    'Engaging activities',
                    'Helping others',
                    'Comparing to worse situations',
                    'Creating opposite emotions',
                    'Pushing away painful thoughts',
                    'Occupying your mind',
                    'Intense sensations'
                ]
            }
        }
    
    def mindfulness_skills(self, skill_focus: str = 'general') -> Dict[str, Any]:
        """Core DBT mindfulness skills"""
        
        mindfulness_components = {
            'wise_mind': {
                'description': 'Balance between emotion mind and reasonable mind',
                'exercise': 'Take deep breaths and ask: What does my wise mind say about this situation?',
                'practice': [
                    'Notice when you\'re in emotion mind (all feelings)',
                    'Notice when you\'re in reasonable mind (all logic)',
                    'Find the balance point between both',
                    'Ask wise mind for guidance on decisions'
                ]
            },
            'observe': {
                'description': 'Notice and watch your experience without getting caught up',
                'exercise': 'Observe your breathing for 2 minutes without changing it',
                'practice': [
                    'Watch your thoughts like clouds passing',
                    'Notice emotions without judging them',
                    'Observe sensations in your body',
                    'Watch what\'s happening around you'
                ]
            },
            'describe': {
                'description': 'Put words to your experience',
                'exercise': 'Describe what you\'re experiencing right now in detail',
                'practice': [
                    'Use factual language',
                    'Avoid interpretations',
                    'Stick to what you observe',
                    'Label emotions and thoughts'
                ]
            },
            'participate': {
                'description': 'Throw yourself into the current activity',
                'exercise': 'Choose one activity and do it with complete attention',
                'practice': [
                    'Be spontaneous',
                    'Let go of self-consciousness',
                    'Become one with your activity',
                    'Act intuitively'
                ]
            }
        }
        
        return {
            'skill_type': 'mindfulness',
            'focus': skill_focus,
            'components': mindfulness_components,
            'daily_practice': self._create_mindfulness_practice_plan(),
            'homework': 'Practice mindfulness exercises 5 minutes daily'
        }
    
    def distress_tolerance(self, crisis_level: int, situation: str = '') -> Dict[str, Any]:
        """Distress tolerance skills for crisis situations"""
        
        if crisis_level >= 8:  # High crisis
            recommended_skills = ['TIPP', 'Intense_exercise', 'Cold_water']
            timeframe = 'Immediate (0-15 minutes)'
        elif crisis_level >= 5:  # Moderate crisis
            recommended_skills = ['ACCEPTS', 'Self_soothing', 'IMPROVE']
            timeframe = 'Short-term (15-60 minutes)'
        else:  # Lower distress
            recommended_skills = ['Mindfulness', 'Radical_acceptance', 'Distraction']
            timeframe = 'As needed'
        
        distress_plan = {
            'crisis_level': crisis_level,
            'situation': situation,
            'recommended_skills': recommended_skills,
            'timeframe': timeframe,
            'skill_instructions': self._get_distress_tolerance_instructions(recommended_skills),
            'safety_plan': self._create_crisis_safety_plan(),
            'follow_up': 'Check distress level after using skills'
        }
        
        return distress_plan
    
    def emotion_regulation(self, target_emotion: str, intensity: int) -> Dict[str, Any]:
        """Emotion regulation skills and strategies"""
        
        emotion_regulation_skills = {
            'PLEASE': {
                'description': 'Reduce vulnerability to negative emotions',
                'components': [
                    'Treat PhysicaL illness',
                    'Balance Eating',
                    'Avoid mood-Altering substances',
                    'Balance Sleep',
                    'Get Exercise'
                ]
            },
            'opposite_action': {
                'description': 'Act opposite to your emotion\'s urge',
                'instructions': [
                    'Identify the emotion and its urge',
                    'Check if the emotion fits the facts',
                    'If not fitting facts, do the opposite action',
                    'Do it all the way, with willingness'
                ]
            },
            'emotion_surfing': {
                'description': 'Ride out the emotion without making it worse',
                'steps': [
                    'Notice the emotion arising',
                    'Name it without judgment',
                    'Feel it in your body',
                    'Remember: emotions are temporary',
                    'Wait for it to naturally decrease'
                ]
            }
        }
        
        # Customize based on specific emotion
        opposite_actions = {
            'anger': 'Be kind, walk away gently, validate others',
            'fear': 'Approach what you fear, do what scares you',
            'sadness': 'Be active, do mastery activities, connect with others',
            'shame': 'Make eye contact, speak up, don\'t hide',
            'guilt': 'Repair if needed, then move forward'
        }
        
        regulation_plan = {
            'target_emotion': target_emotion,
            'intensity': intensity,
            'regulation_skills': emotion_regulation_skills,
            'specific_opposite_action': opposite_actions.get(target_emotion.lower(), 'Observe and describe the emotion'),
            'practice_exercise': self._create_emotion_regulation_exercise(target_emotion),
            'homework': f'Practice emotion regulation skills when experiencing {target_emotion}'
        }
        
        return regulation_plan
    
    def interpersonal_effectiveness(self, relationship_goal: str, situation: str) -> Dict[str, Any]:
        """Interpersonal effectiveness skills"""
        
        interpersonal_skills = {
            'DEAR_MAN': {
                'description': 'Asking for what you want or saying no',
                'components': {
                    'Describe': 'Describe the situation factually',
                    'Express': 'Express your feelings and opinions',
                    'Assert': 'Assert your needs clearly',
                    'Reinforce': 'Reinforce the benefits',
                    'Mindful': 'Stay focused on your goal',
                    'Appear_confident': 'Use confident body language',
                    'Negotiate': 'Be willing to compromise'
                }
            },
            'GIVE': {
                'description': 'Maintaining relationships',
                'components': {
                    'Gentle': 'Be kind and respectful',
                    'Interested': 'Show genuine interest',
                    'Validate': 'Acknowledge their feelings',
                    'Easy': 'Use humor and be lighthearted'
                }
            },
            'FAST': {
                'description': 'Maintaining self-respect',
                'components': {
                    'Fair': 'Be fair to yourself and others',
                    'Apologies': 'Don\'t over-apologize',
                    'Stick_to_values': 'Don\'t compromise your values',
                    'Truthful': 'Be honest and authentic'
                }
            }
        }
        
        effectiveness_plan = {
            'relationship_goal': relationship_goal,
            'situation': situation,
            'skills': interpersonal_skills,
            'practice_scenario': self._create_interpersonal_practice(relationship_goal),
            'homework': 'Practice DEAR MAN in a low-stakes situation this week'
        }
        
        return effectiveness_plan
    
    def _create_mindfulness_practice_plan(self) -> Dict[str, Any]:
        """Create daily mindfulness practice plan"""
        return {
            'morning': 'Wise mind meditation (3 minutes)',
            'afternoon': 'Mindful eating or walking (5 minutes)',
            'evening': 'Observe and describe practice (2 minutes)',
            'weekly_goal': 'Complete 5 out of 7 days of practice'
        }
    
    def _get_distress_tolerance_instructions(self, skills: List[str]) -> Dict[str, str]:
        """Get specific instructions for distress tolerance skills"""
        instructions = {}
        for skill in skills:
            if skill == 'TIPP':
                instructions[skill] = 'Cold water on face, intense exercise, breathe out longer than in'
            elif skill == 'ACCEPTS':
                instructions[skill] = 'Use activities, help others, create opposite emotions'
            # Add more skill instructions as needed
        return instructions
    
    def _create_crisis_safety_plan(self) -> Dict[str, Any]:
        """Create crisis safety plan"""
        return {
            'immediate_steps': [
                'Use distress tolerance skills',
                'Contact support person',
                'Remove means of self-harm',
                'Go to safe location'
            ],
            'support_contacts': 'Emergency contact numbers',
            'professional_help': 'Crisis hotline: 988'
        }
    
    def _create_emotion_regulation_exercise(self, emotion: str) -> Dict[str, Any]:
        """Create emotion-specific regulation exercise"""
        return {
            'exercise_name': f'{emotion.title()} Regulation Practice',
            'steps': [
                f'Notice when {emotion} arises',
                'Rate intensity 0-10',
                'Use PLEASE skills preventively',
                'Apply opposite action if emotion doesn\'t fit facts',
                'Practice emotion surfing',
                'Re-rate intensity'
            ]
        }
    
    def _create_interpersonal_practice(self, goal: str) -> Dict[str, Any]:
        """Create interpersonal effectiveness practice scenario"""
        return {
            'scenario': f'Practice {goal} in upcoming situation',
            'preparation': [
                'Identify your goal clearly',
                'Plan your DEAR MAN script',
                'Practice confident body language',
                'Prepare for possible responses'
            ],
            'debrief': 'Review what worked and what to adjust'
        }


class ACTModule:
    """Acceptance and Commitment Therapy module"""
    
    def __init__(self):
        self.six_core_processes = [
            'contact_with_present_moment',
            'acceptance',
            'cognitive_defusion',
            'self_as_context',
            'values',
            'committed_action'
        ]
    
    def acceptance_strategies(self, struggling_with: str, avoidance_level: int) -> Dict[str, Any]:
        """Acceptance and willingness techniques"""
        
        acceptance_techniques = {
            'creative_hopelessness': {
                'description': 'Recognizing that avoidance strategies aren\'t working',
                'exercise': 'List all the ways you\'ve tried to control or avoid this struggle. How well have they worked long-term?'
            },
            'passengers_on_bus': {
                'description': 'Metaphor for accepting difficult thoughts/feelings',
                'exercise': 'Imagine your difficult thoughts as passengers on your life bus. You\'re the driver - where do you want to go?'
            },
            'tug_of_war': {
                'description': 'Stopping the struggle against difficult experiences',
                'exercise': 'Instead of pulling against the rope (your struggle), what if you dropped the rope?'
            },
            'waves_metaphor': {
                'description': 'Riding out difficult emotions',
                'exercise': 'Notice emotions like waves - they rise, peak, and naturally fall. Can you surf this wave?'
            }
        }
        
        acceptance_plan = {
            'struggling_with': struggling_with,
            'avoidance_level': avoidance_level,
            'techniques': acceptance_techniques,
            'willingness_exercise': self._create_willingness_exercise(struggling_with),
            'homework': 'Practice acceptance techniques when struggling arises'
        }
        
        return acceptance_plan
    
    def cognitive_defusion(self, target_thought: str, thought_stickiness: int) -> Dict[str, Any]:
        """Cognitive defusion techniques to reduce thought believability"""
        
        defusion_techniques = {
            'just_having_thought': {
                'name': 'I\'m Having the Thought That...',
                'instruction': f'Instead of "{target_thought}", say "I\'m having the thought that {target_thought}"',
                'purpose': 'Create distance from the thought'
            },
            'singing_thought': {
                'name': 'Sing the Thought',
                'instruction': 'Sing your thought to the tune of "Happy Birthday" or another familiar song',
                'purpose': 'Reduce thought\'s emotional impact'
            },
            'silly_voice': {
                'name': 'Silly Voice',
                'instruction': 'Say the thought in a cartoon character voice or very slow/fast',
                'purpose': 'Decrease thought believability'
            },
            'thank_you_mind': {
                'name': 'Thank You, Mind',
                'instruction': 'When mind offers unhelpful thoughts, say "Thank you, mind, for that thought"',
                'purpose': 'Acknowledge without buying into thoughts'
            },
            'leaves_on_stream': {
                'name': 'Leaves on a Stream',
                'instruction': 'Visualize placing thoughts on leaves floating down a stream',
                'purpose': 'Practice letting thoughts come and go'
            }
        }
        
        defusion_plan = {
            'target_thought': target_thought,
            'stickiness_level': thought_stickiness,
            'techniques': defusion_techniques,
            'practice_exercise': self._create_defusion_practice(target_thought),
            'daily_practice': 'Use defusion techniques when stuck thoughts appear'
        }
        
        return defusion_plan
    
    def values_clarification(self, life_domain: str = 'general') -> Dict[str, Any]:
        """Values exploration and clarification exercises"""
        
        life_domains = {
            'relationships': 'Family, friendships, romantic relationships',
            'work_education': 'Career, job, education, professional development',
            'leisure': 'Recreation, fun, relaxation, hobbies',
            'personal_growth': 'Self-development, spirituality, meaning',
            'health': 'Physical health, mental health, self-care',
            'community': 'Community involvement, citizenship, social causes'
        }
        
        values_exercises = {
            'funeral_exercise': {
                'description': 'Imagine what you\'d want people to say about how you lived',
                'questions': [
                    'What would you want your eulogy to say?',
                    'How would you want to be remembered?',
                    'What kind of person would you want to have been?'
                ]
            },
            'values_card_sort': {
                'description': 'Identify your most important values',
                'top_values': [
                    'Authenticity', 'Compassion', 'Courage', 'Creativity',
                    'Family', 'Friendship', 'Growth', 'Health',
                    'Honesty', 'Justice', 'Learning', 'Love',
                    'Security', 'Spirituality', 'Success', 'Adventure'
                ]
            },
            'ideal_day': {
                'description': 'Describe your ideal day if nothing held you back',
                'questions': [
                    'How would you spend your time?',
                    'Who would you be with?',
                    'What would you be doing?',
                    'What values would this represent?'
                ]
            }
        }
        
        values_plan = {
            'life_domain': life_domain,
            'domain_description': life_domains.get(life_domain, 'General life values'),
            'exercises': values_exercises,
            'reflection_questions': self._create_values_reflection_questions(life_domain),
            'homework': 'Complete values exercises and identify top 3-5 values'
        }
        
        return values_plan
    
    def committed_action(self, identified_values: List[str], current_barriers: List[str]) -> Dict[str, Any]:
        """Create committed action plans based on values"""
        
        action_planning_steps = {
            'SMART_goals': {
                'description': 'Create Specific, Measurable, Achievable, Relevant, Time-bound goals',
                'template': 'I will [specific action] by [date] as measured by [outcome]'
            },
            'values_connection': {
                'description': 'Connect each goal to your values',
                'questions': [
                    'How does this goal serve my values?',
                    'What value am I living by taking this action?',
                    'How will I feel when acting in line with my values?'
                ]
            },
            'barrier_planning': {
                'description': 'Plan for obstacles and setbacks',
                'strategy': 'If [barrier occurs], then I will [specific response]'
            },
            'start_small': {
                'description': 'Begin with small, manageable steps',
                'principle': 'Better to take consistent small steps than inconsistent large ones'
            }
        }
        
        committed_action_plan = {
            'values': identified_values,
            'barriers': current_barriers,
            'planning_steps': action_planning_steps,
            'action_goals': self._create_values_based_goals(identified_values),
            'weekly_commitment': 'Choose one small values-based action for this week',
            'tracking': 'Daily check-in: Did my actions align with my values today?'
        }
        
        return committed_action_plan
    
    def mindfulness_practices(self, practice_type: str = 'general') -> Dict[str, Any]:
        """ACT-specific mindfulness practices"""
        
        mindfulness_exercises = {
            'five_senses': {
                'name': '5-4-3-2-1 Grounding',
                'instructions': [
                    'Notice 5 things you can see',
                    'Notice 4 things you can touch',
                    'Notice 3 things you can hear',
                    'Notice 2 things you can smell',
                    'Notice 1 thing you can taste'
                ]
            },
            'breathing_space': {
                'name': 'Three-Minute Breathing Space',
                'steps': [
                    'Minute 1: Awareness - What\'s happening right now?',
                    'Minute 2: Gathering - Focus on your breath',
                    'Minute 3: Expanding - Widen awareness to whole body and surroundings'
                ]
            },
            'observer_self': {
                'name': 'Observer Self Exercise',
                'instructions': [
                    'Notice you are noticing your thoughts',
                    'Notice you are noticing your feelings',
                    'Notice the part of you that notices - this is your observer self',
                    'Rest in this observing awareness'
                ]
            }
        }
        
        mindfulness_plan = {
            'practice_type': practice_type,
            'exercises': mindfulness_exercises,
            'daily_practice': 'Choose one exercise to practice daily for a week',
            'integration': 'Use brief mindfulness moments throughout the day'
        }
        
        return mindfulness_plan
    
    def _create_willingness_exercise(self, struggle: str) -> Dict[str, Any]:
        """Create willingness exercise for specific struggle"""
        return {
            'exercise_name': f'Willingness Practice for {struggle}',
            'steps': [
                f'Acknowledge that you\'re struggling with {struggle}',
                'Notice your urge to control or avoid this experience',
                'Ask yourself: How has trying to control this worked?',
                'Experiment with opening up to this experience',
                'Say to yourself: "I\'m willing to have this experience"',
                'Notice what happens when you stop fighting'
            ],
            'daily_practice': f'Practice willingness when {struggle} arises'
        }
    
    def _create_defusion_practice(self, thought: str) -> Dict[str, Any]:
        """Create defusion practice for specific thought"""
        return {
            'target_thought': thought,
            'practice_sequence': [
                f'Think the thought: "{thought}"',
                f'Now think: "I\'m having the thought that {thought}"',
                f'Now think: "I notice I\'m having the thought that {thought}"',
                f'Sing the thought to "Happy Birthday"',
                'Notice any change in how the thought feels'
            ],
            'effectiveness_check': 'Rate how believable/sticky the thought feels after practice'
        }
    
    def _create_values_reflection_questions(self, domain: str) -> List[str]:
        """Create reflection questions for specific life domain"""
        general_questions = [
            'What matters most to you in this area of life?',
            'What kind of person do you want to be in this domain?',
            'If you were living fully according to your values here, what would you be doing?',
            'What would you regret not doing in this area?'
        ]
        
        domain_specific = {
            'relationships': [
                'What kind of partner/friend/family member do you want to be?',
                'How do you want to treat the people you care about?'
            ],
            'work_education': [
                'What do you want your work to contribute to the world?',
                'What kind of colleague/student do you want to be?'
            ]
        }
        
        questions = general_questions + domain_specific.get(domain, [])
        return questions
    
    def _create_values_based_goals(self, values: List[str]) -> List[Dict[str, Any]]:
        """Create sample goals based on identified values"""
        sample_goals = []
        for value in values[:3]:  # Top 3 values
            sample_goals.append({
                'value': value,
                'goal_example': f'Take one action this week that honors {value}',
                'measurement': 'Complete the action and reflect on how it felt',
                'timeline': '1 week'
            })
        return sample_goals


class PsychodynamicModule:
    """Psychodynamic therapy interventions focusing on insight and patterns"""
    
    def __init__(self):
        self.defense_mechanisms = {
            'denial': 'Refusing to acknowledge reality',
            'projection': 'Attributing your feelings to others',
            'rationalization': 'Creating logical explanations for emotional reactions',
            'displacement': 'Redirecting emotions to safer targets',
            'regression': 'Reverting to earlier developmental behaviors',
            'sublimation': 'Channeling impulses into socially acceptable activities'
        }
    
    def pattern_recognition(self, presenting_issue: str, relationship_history: str = '') -> Dict[str, Any]:
        """Explore recurring patterns in thoughts, feelings, and relationships"""
        
        pattern_exploration = {
            'presenting_issue': presenting_issue,
            'pattern_areas': {
                'interpersonal': {
                    'questions': [
                        'What patterns do you notice in your relationships?',
                        'How do your relationships tend to begin and end?',
                        'What roles do you often find yourself playing?',
                        'What do you expect from others?'
                    ],
                    'common_patterns': [
                        'Seeking approval from authority figures',
                        'Difficulty with boundaries',
                        'Fear of abandonment or engulfment',
                        'Repeating family dynamics'
                    ]
                },
                'emotional': {
                    'questions': [
                        'What emotions do you have difficulty experiencing?',
                        'How did your family handle emotions?',
                        'What emotions feel dangerous or forbidden?',
                        'When do you feel most/least like yourself?'
                    ],
                    'common_patterns': [
                        'Suppressing anger or sadness',
                        'Perfectionism and self-criticism',
                        'Difficulty accessing emotions',
                        'Emotional overwhelm or numbness'
                    ]
                },
                'behavioral': {
                    'questions': [
                        'What situations trigger your strongest reactions?',
                        'What do you do when you feel threatened?',
                        'How do you handle conflict or disappointment?',
                        'What behaviors do you repeat despite negative outcomes?'
                    ]
                }
            },
            'exploration_techniques': self._create_pattern_exploration_techniques(),
            'homework': 'Keep a pattern journal noting recurring themes'
        }
        
        return pattern_exploration
    
    def defense_mechanism_exploration(self, current_struggle: str) -> Dict[str, Any]:
        """Explore and understand defense mechanisms"""
        
        defense_exploration = {
            'current_struggle': current_struggle,
            'defense_mechanisms': self.defense_mechanisms,
            'exploration_process': {
                'identification': {
                    'description': 'Recognize which defenses you use',
                    'questions': [
                        'How do you protect yourself from emotional pain?',
                        'What do you do when you feel vulnerable?',
                        'How do you handle criticism or rejection?',
                        'What patterns do others point out about you?'
                    ]
                },
                'understanding': {
                    'description': 'Understand the purpose and origin of defenses',
                    'questions': [
                        'When did you first start using this defense?',
                        'How did it help you in the past?',
                        'What were you protecting yourself from?',
                        'What would happen if you didn\'t use this defense?'
                    ]
                },
                'adaptation': {
                    'description': 'Develop more adaptive responses',
                    'questions': [
                        'How is this defense limiting you now?',
                        'What would be different if you used it less?',
                        'What other ways could you protect yourself?',
                        'What small experiment could you try?'
                    ]
                }
            },
            'defense_assessment': self._create_defense_assessment(),
            'integration_work': 'Gradual awareness and choice in defensive responses'
        }
        
        return defense_exploration
    
    def transference_analysis(self, therapeutic_relationship_observations: str = '') -> Dict[str, Any]:
        """Explore transference patterns in therapeutic relationship"""
        
        transference_work = {
            'definition': 'Unconscious redirection of feelings from past relationships onto the therapist',
            'exploration_areas': {
                'authority_figures': {
                    'questions': [
                        'How do you typically respond to authority figures?',
                        'What do you expect from people in helping roles?',
                        'How do you handle power dynamics?'
                    ],
                    'patterns': [
                        'Compliance or rebellion',
                        'Seeking approval or rejecting help',
                        'Fear of judgment or criticism'
                    ]
                },
                'caretaker_dynamics': {
                    'questions': [
                        'How comfortable are you receiving help?',
                        'What do you worry about in this relationship?',
                        'How do you handle dependency on others?'
                    ]
                },
                'family_parallels': {
                    'questions': [
                        'Does the therapist remind you of anyone?',
                        'What family dynamics might be playing out here?',
                        'How did you relate to your parents/caregivers?'
                    ]
                }
            },
            'therapeutic_use': {
                'description': 'How transference provides insight into other relationships',
                'benefits': [
                    'Understanding relationship patterns',
                    'Practicing new ways of relating',
                    'Healing old emotional wounds',
                    'Developing more authentic connections'
                ]
            },
            'homework': 'Notice reactions to the therapist and explore their origins'
        }
        
        return transference_work
    
    def unconscious_pattern_work(self, symptoms: List[str], family_history: str = '') -> Dict[str, Any]:
        """Explore unconscious patterns and their origins"""
        
        unconscious_exploration = {
            'current_symptoms': symptoms,
            'family_history': family_history,
            'exploration_techniques': {
                'free_association': {
                    'description': 'Say whatever comes to mind without censoring',
                    'instruction': 'When discussing a topic, notice what thoughts, images, or memories arise spontaneously'
                },
                'dream_exploration': {
                    'description': 'Explore symbolic meaning in dreams',
                    'process': [
                        'Record dreams immediately upon waking',
                        'Notice recurring themes or symbols',
                        'Explore personal associations with dream elements',
                        'Consider metaphorical meanings'
                    ]
                },
                'early_memory_work': {
                    'description': 'Explore formative childhood experiences',
                    'questions': [
                        'What are your earliest memories?',
                        'What family stories have you been told?',
                        'What messages did you receive about yourself?',
                        'How did your family handle conflict, emotions, achievements?'
                    ]
                },
                'symptom_symbolism': {
                    'description': 'Explore what symptoms might represent',
                    'questions': [
                        'If your symptom could speak, what would it say?',
                        'What might your symptom be protecting you from?',
                        'When did this symptom first appear?',
                        'What was happening in your life at that time?'
                    ]
                }
            },
            'integration_process': self._create_integration_process(),
            'ongoing_work': 'Regular exploration of unconscious material through various techniques'
        }
        
        return unconscious_exploration
    
    def insight_development(self, current_insights: List[str] = None) -> Dict[str, Any]:
        """Facilitate development of psychological insight"""
        
        if current_insights is None:
            current_insights = []
        
        insight_work = {
            'current_insights': current_insights,
            'insight_levels': {
                'intellectual': {
                    'description': 'Understanding patterns cognitively',
                    'example': 'I can see that I repeat the same relationship pattern'
                },
                'emotional': {
                    'description': 'Feeling the emotional truth of insights',
                    'example': 'I feel how deeply I fear abandonment'
                },
                'experiential': {
                    'description': 'Living insights through new experiences',
                    'example': 'I\'m choosing to respond differently in relationships'
                }
            },
            'insight_development_techniques': {
                'connecting_past_present': {
                    'description': 'Link current patterns to historical origins',
                    'questions': [
                        'How does this current situation remind you of the past?',
                        'What childhood experiences might be influencing this?',
                        'How are you recreating familiar dynamics?'
                    ]
                },
                'affect_exploration': {
                    'description': 'Deepen emotional understanding',
                    'process': [
                        'Notice what emotions arise with insights',
                        'Stay with difficult feelings that emerge',
                        'Explore the meaning of emotional reactions',
                        'Connect emotions to underlying needs'
                    ]
                },
                'behavioral_experiments': {
                    'description': 'Test insights through new behaviors',
                    'approach': 'Try acting differently and notice what happens internally and relationally'
                }
            },
            'working_through': {
                'description': 'Repeated exploration of insights until they create lasting change',
                'process': [
                    'Recognize the pattern in multiple contexts',
                    'Understand its origins and purpose',
                    'Feel the emotional impact fully',
                    'Experiment with new responses',
                    'Integrate new ways of being'
                ]
            },
            'homework': 'Journal about insights and experiment with new responses'
        }
        
        return insight_work
    
    def _create_pattern_exploration_techniques(self) -> Dict[str, Any]:
        """Create techniques for pattern exploration"""
        return {
            'genogram_work': {
                'description': 'Map family patterns across generations',
                'focus': 'Identify recurring themes, roles, and dynamics'
            },
            'relationship_timeline': {
                'description': 'Chart relationship patterns over time',
                'elements': ['Beginning patterns', 'Conflict styles', 'Ending patterns', 'Lessons learned']
            },
            'role_analysis': {
                'description': 'Identify roles you play in different relationships',
                'common_roles': ['Caretaker', 'Rebel', 'Peacemaker', 'Scapegoat', 'Hero']
            }
        }
    
    def _create_defense_assessment(self) -> Dict[str, Any]:
        """Create defense mechanism assessment"""
        return {
            'self_assessment_questions': [
                'When criticized, I typically...',
                'When feeling vulnerable, I...',
                'When angry, I usually...',
                'When disappointed, I tend to...',
                'Others often tell me I...'
            ],
            'defensive_style_inventory': {
                'mature_defenses': ['Humor', 'Sublimation', 'Suppression'],
                'neurotic_defenses': ['Repression', 'Displacement', 'Intellectualization'],
                'immature_defenses': ['Denial', 'Projection', 'Acting out']
            }
        }
    
    def _create_integration_process(self) -> Dict[str, Any]:
        """Create process for integrating unconscious material"""
        return {
            'steps': [
                'Recognition: Becoming aware of unconscious patterns',
                'Understanding: Exploring origins and meanings',
                'Emotional processing: Feeling associated emotions',
                'Integration: Incorporating insights into conscious awareness',
                'Behavioral change: Acting from new understanding'
            ],
            'timeline': 'This is typically a gradual, ongoing process',
            'support': 'Regular therapy sessions provide container for this work'
        }


class TherapyModuleIntegrator:
    """Integrates different therapy modules and provides unified interface"""
    
    def __init__(self):
        self.cbt = CBTModule()
        self.dbt = DBTModule()
        self.act = ACTModule()
        self.psychodynamic = PsychodynamicModule()
        
        self.modality_map = {
            'CBT': self.cbt,
            'DBT': self.dbt,
            'ACT': self.act,
            'Psychodynamic': self.psychodynamic
        }
    
    def get_intervention(self, modality: str, intervention_type: str, **kwargs) -> Dict[str, Any]:
        """Get specific intervention from chosen modality"""
        
        if modality not in self.modality_map:
            raise ValueError(f"Unknown modality: {modality}")
        
        module = self.modality_map[modality]
        
        # Route to appropriate intervention based on type
        intervention_routing = {
            'CBT': {
                'cognitive_restructuring': module.cognitive_restructuring,
                'behavioral_activation': module.behavioral_activation,
                'exposure_therapy': module.exposure_therapy_protocol
            },
            'DBT': {
                'mindfulness': module.mindfulness_skills,
                'distress_tolerance': module.distress_tolerance,
                'emotion_regulation': module.emotion_regulation,
                'interpersonal_effectiveness': module.interpersonal_effectiveness
            },
            'ACT': {
                'acceptance': module.acceptance_strategies,
                'defusion': module.cognitive_defusion,
                'values': module.values_clarification,
                'committed_action': module.committed_action,
                'mindfulness': module.mindfulness_practices
            },
            'Psychodynamic': {
                'pattern_recognition': module.pattern_recognition,
                'defense_exploration': module.defense_mechanism_exploration,
                'transference': module.transference_analysis,
                'unconscious_patterns': module.unconscious_pattern_work,
                'insight_development': module.insight_development
            }
        }
        
        if intervention_type not in intervention_routing[modality]:
            raise ValueError(f"Unknown intervention type: {intervention_type} for {modality}")
        
        intervention_func = intervention_routing[modality][intervention_type]
        return intervention_func(**kwargs)
    
    def recommend_interventions(self, presenting_problems: List[str], patient_preferences: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Recommend appropriate interventions based on presenting problems"""
        
        if patient_preferences is None:
            patient_preferences = {}
        
        recommendations = []
        
        # Problem-to-intervention mapping
        intervention_recommendations = {
            'depression': [
                {'modality': 'CBT', 'intervention': 'behavioral_activation', 'priority': 'high'},
                {'modality': 'CBT', 'intervention': 'cognitive_restructuring', 'priority': 'high'},
                {'modality': 'ACT', 'intervention': 'values', 'priority': 'medium'}
            ],
            'anxiety': [
                {'modality': 'CBT', 'intervention': 'cognitive_restructuring', 'priority': 'high'},
                {'modality': 'CBT', 'intervention': 'exposure_therapy', 'priority': 'high'},
                {'modality': 'DBT', 'intervention': 'distress_tolerance', 'priority': 'medium'}
            ],
            'trauma': [
                {'modality': 'DBT', 'intervention': 'distress_tolerance', 'priority': 'high'},
                {'modality': 'DBT', 'intervention': 'emotion_regulation', 'priority': 'high'},
                {'modality': 'ACT', 'intervention': 'acceptance', 'priority': 'medium'}
            ],
            'relationship_issues': [
                {'modality': 'DBT', 'intervention': 'interpersonal_effectiveness', 'priority': 'high'},
                {'modality': 'Psychodynamic', 'intervention': 'pattern_recognition', 'priority': 'high'},
                {'modality': 'Psychodynamic', 'intervention': 'transference', 'priority': 'medium'}
            ],
            'emotional_regulation': [
                {'modality': 'DBT', 'intervention': 'emotion_regulation', 'priority': 'high'},
                {'modality': 'DBT', 'intervention': 'mindfulness', 'priority': 'high'},
                {'modality': 'ACT', 'intervention': 'acceptance', 'priority': 'medium'}
            ]
        }
        
        # Generate recommendations
        for problem in presenting_problems:
            problem_lower = problem.lower()
            for key, interventions in intervention_recommendations.items():
                if key in problem_lower or problem_lower in key:
                    recommendations.extend(interventions)
        
        # Remove duplicates and sort by priority
        unique_recommendations = []
        seen = set()
        for rec in recommendations:
            key = (rec['modality'], rec['intervention'])
            if key not in seen:
                unique_recommendations.append(rec)
                seen.add(key)
        
        # Sort by priority
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        unique_recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return unique_recommendations
    
    def create_session_plan(self, modality: str, session_goals: List[str], patient_state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured session plan using chosen modality"""
        
        session_plan = {
            'modality': modality,
            'session_goals': session_goals,
            'patient_state': patient_state,
            'session_structure': {
                'opening': {
                    'duration': 5,
                    'activities': ['Check-in', 'Mood assessment', 'Review homework', 'Set session agenda']
                },
                'main_work': {
                    'duration': 35,
                    'planned_interventions': []
                },
                'closing': {
                    'duration': 10,
                    'activities': ['Session summary', 'Homework assignment', 'Next session planning']
                }
            },
            'crisis_monitoring': True,
            'homework_options': []
        }
        
        # Customize based on modality
        if modality == 'CBT':
            session_plan['session_structure']['main_work']['planned_interventions'] = [
                'Thought record review',
                'Cognitive restructuring exercise',
                'Behavioral experiment planning'
            ]
            session_plan['homework_options'] = [
                'Thought record worksheet',
                'Activity scheduling',
                'Behavioral experiment'
            ]
        
        elif modality == 'DBT':
            session_plan['session_structure']['main_work']['planned_interventions'] = [
                'Mindfulness practice',
                'Skills training',
                'Skills practice and rehearsal'
            ]
            session_plan['homework_options'] = [
                'Mindfulness practice',
                'Skills practice diary',
                'Distress tolerance skills use'
            ]
        
        elif modality == 'ACT':
            session_plan['session_structure']['main_work']['planned_interventions'] = [
                'Values exploration',
                'Defusion exercises',
                'Committed action planning'
            ]
            session_plan['homework_options'] = [
                'Values-based goal setting',
                'Defusion practice',
                'Mindfulness exercises'
            ]
        
        elif modality == 'Psychodynamic':
            session_plan['session_structure']['main_work']['planned_interventions'] = [
                'Free association',
                'Pattern exploration',
                'Transference examination'
            ]
            session_plan['homework_options'] = [
                'Dream journal',
                'Pattern observation',
                'Relationship reflection'
            ]
        
        return session_plan
    
    def track_intervention_effectiveness(self, intervention_id: str, patient_id: int, pre_scores: Dict[str, int], post_scores: Dict[str, int]) -> Dict[str, Any]:
        """Track the effectiveness of interventions"""
        
        effectiveness_data = {
            'intervention_id': intervention_id,
            'patient_id': patient_id,
            'pre_intervention_scores': pre_scores,
            'post_intervention_scores': post_scores,
            'improvements': {},
            'overall_effectiveness': 'pending_calculation'
        }
        
        # Calculate improvements
        for measure, pre_score in pre_scores.items():
            if measure in post_scores:
                improvement = pre_score - post_scores[measure]  # Assuming lower scores are better
                effectiveness_data['improvements'][measure] = {
                    'change': improvement,
                    'percent_change': (improvement / pre_score * 100) if pre_score > 0 else 0
                }
        
        # Calculate overall effectiveness
        total_improvements = sum(imp['change'] for imp in effectiveness_data['improvements'].values())
        num_measures = len(effectiveness_data['improvements'])
        
        if num_measures > 0:
            avg_improvement = total_improvements / num_measures
            if avg_improvement >= 2:
                effectiveness_data['overall_effectiveness'] = 'highly_effective'
            elif avg_improvement >= 1:
                effectiveness_data['overall_effectiveness'] = 'moderately_effective'
            elif avg_improvement > 0:
                effectiveness_data['overall_effectiveness'] = 'minimally_effective'
            else:
                effectiveness_data['overall_effectiveness'] = 'not_effective'
        
        return effectiveness_data


# Module testing and example usage
def main():
    """Test the therapy modules"""
    print("Therapy Modules Test")
    print("=" * 50)
    
    # Initialize integrator
    integrator = TherapyModuleIntegrator()
    
    # Test CBT cognitive restructuring
    print("\n1. Testing CBT Cognitive Restructuring:")
    cbt_result = integrator.get_intervention(
        'CBT', 
        'cognitive_restructuring', 
        patient_thought="I always mess everything up",
        patient_id=1
    )
    print(f"Identified distortions: {cbt_result['identified_distortions']}")
    print(f"Original thought: {cbt_result['original_thought']}")
    
    # Test DBT mindfulness
    print("\n2. Testing DBT Mindfulness:")
    dbt_result = integrator.get_intervention(
        'DBT',
        'mindfulness',
        skill_focus='wise_mind'
    )
    print(f"Skill type: {dbt_result['skill_type']}")
    print(f"Components: {list(dbt_result['components'].keys())}")
    
    # Test ACT values clarification
    print("\n3. Testing ACT Values Clarification:")
    act_result = integrator.get_intervention(
        'ACT',
        'values',
        life_domain='relationships'
    )
    print(f"Life domain: {act_result['life_domain']}")
    print(f"Exercises: {list(act_result['exercises'].keys())}")
    
    # Test intervention recommendations
    print("\n4. Testing Intervention Recommendations:")
    recommendations = integrator.recommend_interventions(
        presenting_problems=['depression', 'anxiety']
    )
    for rec in recommendations[:3]:  # Show top 3
        print(f"- {rec['modality']}: {rec['intervention']} (Priority: {rec['priority']})")
    
    # Test session planning
    print("\n5. Testing Session Planning:")
    session_plan = integrator.create_session_plan(
        modality='CBT',
        session_goals=['Reduce negative thinking', 'Increase activity'],
        patient_state={'mood': 4, 'anxiety': 7}
    )
    print(f"Session structure: {list(session_plan['session_structure'].keys())}")
    print(f"Planned interventions: {session_plan['session_structure']['main_work']['planned_interventions']}")
    
    print("\nTherapy Modules Test Complete!")


if __name__ == "__main__":
    main()