"""
recommendation.py - AI-Powered Therapy Recommendation Engine

This module analyzes therapy session conversations and generates two types of recommendations:
1. Content Recommendations: YouTube videos, articles, podcasts for therapeutic education
2. Lifestyle Recommendations: Activities, habits, exercises based on goals and homework
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dataclasses import dataclass


@dataclass
class ContentRecommendation:
    """Structure for content recommendations"""
    title: str
    description: str
    content_type: str  # 'youtube', 'article', 'podcast', 'app'
    search_query: str
    relevance_reason: str
    estimated_duration: str


@dataclass
class LifestyleRecommendation:
    """Structure for lifestyle recommendations"""
    title: str
    description: str
    activity_type: str  # 'physical', 'mental', 'social', 'self_care'
    instructions: str
    frequency: str
    duration: str
    difficulty_level: str  # 'beginner', 'intermediate', 'advanced'
    relates_to_goal: Optional[str] = None
    relates_to_homework: Optional[str] = None


class TherapyKeywordExtractor:
    """Extract therapeutic keywords and themes from conversations"""
    
    def __init__(self, gemini_model):
        self.model = gemini_model
    
    async def extract_keywords_and_themes(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Extract keywords, themes, and therapeutic insights from conversation"""
        
        # Build conversation text
        conversation_text = self._format_conversation(conversation_history)
        
        extraction_prompt = f"""
Analyze this therapy session conversation and extract key information for generating recommendations:

CONVERSATION:
{conversation_text}

Extract and provide:
1. PRIMARY SYMPTOMS: Main mental health symptoms discussed (anxiety, depression, trauma, etc.)
2. SECONDARY CONCERNS: Related issues (sleep, relationships, work, etc.)  
3. THERAPEUTIC THEMES: Key themes that emerged (cognitive patterns, behaviors, emotions)
4. COPING CHALLENGES: Specific difficulties the patient faces
5. STRENGTHS IDENTIFIED: Patient's existing strengths and resources
6. LEARNING NEEDS: Areas where patient needs education or skills
7. EMOTIONAL STATE: Current emotional patterns and mood
8. BEHAVIORAL PATTERNS: Specific behaviors or habits mentioned
9. TRIGGERS: Identified triggers or stressors
10. MOTIVATION LEVEL: Patient's readiness for change and engagement

Format your response as JSON:
{{
    "primary_symptoms": ["symptom1", "symptom2"],
    "secondary_concerns": ["concern1", "concern2"],
    "therapeutic_themes": ["theme1", "theme2"],
    "coping_challenges": ["challenge1", "challenge2"],
    "strengths": ["strength1", "strength2"],
    "learning_needs": ["need1", "need2"],
    "emotional_state": "description",
    "behavioral_patterns": ["pattern1", "pattern2"],
    "triggers": ["trigger1", "trigger2"],
    "motivation_level": "high/medium/low",
    "session_summary": "2-3 sentence summary of key session themes"
}}
"""
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(extraction_prompt)
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing if JSON isn't cleanly formatted
                return self._fallback_keyword_extraction(conversation_text)
                
        except Exception as e:
            print(f"Keyword extraction error: {e}")
            return self._fallback_keyword_extraction(conversation_text)
    
    def _format_conversation(self, conversation_history: List[Dict]) -> str:
        """Format conversation for analysis"""
        formatted = []
        for exchange in conversation_history:
            formatted.append(f"Patient: {exchange.get('user', '')}")
            formatted.append(f"Therapist: {exchange.get('ai', '')}")
        return "\n".join(formatted)
    
    def _fallback_keyword_extraction(self, conversation_text: str) -> Dict[str, Any]:
        """Fallback keyword extraction using simple pattern matching"""
        # Simple keyword detection for common therapy themes
        anxiety_indicators = ['anxious', 'worried', 'panic', 'fear', 'nervous']
        depression_indicators = ['depressed', 'sad', 'hopeless', 'empty', 'worthless']
        sleep_indicators = ['sleep', 'insomnia', 'tired', 'exhausted']
        work_indicators = ['work', 'job', 'boss', 'career', 'stress']
        
        text_lower = conversation_text.lower()
        
        primary_symptoms = []
        if any(word in text_lower for word in anxiety_indicators):
            primary_symptoms.append('anxiety')
        if any(word in text_lower for word in depression_indicators):
            primary_symptoms.append('depression')
        
        secondary_concerns = []
        if any(word in text_lower for word in sleep_indicators):
            secondary_concerns.append('sleep_issues')
        if any(word in text_lower for word in work_indicators):
            secondary_concerns.append('work_stress')
        
        return {
            "primary_symptoms": primary_symptoms,
            "secondary_concerns": secondary_concerns,
            "therapeutic_themes": ["coping_strategies", "emotional_regulation"],
            "coping_challenges": ["managing_symptoms"],
            "strengths": ["seeking_help"],
            "learning_needs": ["symptom_management"],
            "emotional_state": "seeking_support",
            "behavioral_patterns": ["avoidance"],
            "triggers": ["identified_stressors"],
            "motivation_level": "medium",
            "session_summary": "Patient discussing mental health concerns and seeking coping strategies."
        }


class ContentRecommendationGenerator:
    """Generate content recommendations based on session analysis"""
    
    def __init__(self, gemini_model):
        self.model = gemini_model
    
    async def generate_content_recommendations(
        self, 
        keywords_data: Dict[str, Any], 
        num_recommendations: int = 5
    ) -> List[ContentRecommendation]:
        """Generate content recommendations based on extracted keywords"""
        
        content_prompt = f"""
Based on this therapy session analysis, recommend {num_recommendations} educational/therapeutic content pieces:

SESSION ANALYSIS:
- Primary Symptoms: {', '.join(keywords_data.get('primary_symptoms', []))}
- Secondary Concerns: {', '.join(keywords_data.get('secondary_concerns', []))}
- Learning Needs: {', '.join(keywords_data.get('learning_needs', []))}
- Therapeutic Themes: {', '.join(keywords_data.get('therapeutic_themes', []))}
- Session Summary: {keywords_data.get('session_summary', '')}

Generate recommendations for:
1. YouTube videos (educational, guided meditations, techniques)
2. Articles or blog posts
3. Podcasts
4. Mobile apps
5. Online resources

For each recommendation, provide:
- Title: Specific, searchable title
- Description: Why this content is helpful for this patient
- Content Type: youtube/article/podcast/app
- Search Query: Exact search terms to find this content
- Relevance Reason: How it addresses patient's specific needs
- Estimated Duration: How long to engage with this content

Format as JSON array:
[
  {{
    "title": "specific title",
    "description": "why this helps the patient",
    "content_type": "youtube/article/podcast/app",
    "search_query": "exact search terms",
    "relevance_reason": "how it addresses their needs",
    "estimated_duration": "10 minutes/30 minutes/etc"
  }}
]

Focus on evidence-based, professional content. Avoid overly clinical or triggering material.
"""
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(content_prompt)
            )
            
            # Parse JSON response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                recommendations_data = json.loads(json_match.group())
                return [ContentRecommendation(**rec) for rec in recommendations_data]
            else:
                return self._fallback_content_recommendations(keywords_data)
                
        except Exception as e:
            print(f"Content recommendation error: {e}")
            return self._fallback_content_recommendations(keywords_data)
    
    def _fallback_content_recommendations(self, keywords_data: Dict[str, Any]) -> List[ContentRecommendation]:
        """Fallback content recommendations"""
        symptoms = keywords_data.get('primary_symptoms', ['general'])
        
        recommendations = []
        if 'anxiety' in symptoms:
            recommendations.append(ContentRecommendation(
                title="Guided Breathing Exercises for Anxiety",
                description="Learn breathing techniques to manage anxiety symptoms",
                content_type="youtube",
                search_query="guided breathing exercises anxiety relief",
                relevance_reason="Addresses anxiety symptoms mentioned in session",
                estimated_duration="10-15 minutes"
            ))
        
        if 'depression' in symptoms:
            recommendations.append(ContentRecommendation(
                title="Understanding Depression: Psychology Explained",
                description="Educational content about depression and recovery",
                content_type="youtube", 
                search_query="depression psychology education recovery",
                relevance_reason="Provides psychoeducation about depression",
                estimated_duration="20-30 minutes"
            ))
        
        return recommendations


class LifestyleRecommendationGenerator:
    """Generate lifestyle recommendations based on goals and homework"""
    
    def __init__(self, gemini_model):
        self.model = gemini_model
    
    async def generate_lifestyle_recommendations(
        self,
        keywords_data: Dict[str, Any],
        goals: List[Dict[str, Any]],
        homework: List[Dict[str, Any]],
        num_recommendations: int = 6
    ) -> List[LifestyleRecommendation]:
        """Generate lifestyle recommendations based on session analysis and treatment plan"""
        
        goals_text = self._format_goals(goals)
        homework_text = self._format_homework(homework)
        
        lifestyle_prompt = f"""
Based on this therapy session analysis and treatment plan, recommend {num_recommendations} lifestyle activities:

SESSION ANALYSIS:
- Primary Symptoms: {', '.join(keywords_data.get('primary_symptoms', []))}
- Behavioral Patterns: {', '.join(keywords_data.get('behavioral_patterns', []))}
- Triggers: {', '.join(keywords_data.get('triggers', []))}
- Motivation Level: {keywords_data.get('motivation_level', 'medium')}

TREATMENT GOALS:
{goals_text}

HOMEWORK ASSIGNMENTS:
{homework_text}

Generate {num_recommendations} lifestyle recommendations that:
1. Support the patient's treatment goals
2. Complement their homework assignments
3. Address their specific symptoms and triggers
4. Match their motivation level
5. Are practical and achievable

Include a mix of:
- Physical activities (exercise, movement, outdoor activities)
- Mental activities (mindfulness, creativity, learning)
- Social activities (connection, communication)
- Self-care activities (relaxation, routines, hobbies)

For each recommendation provide:
- Title: Clear, actionable title
- Description: What the activity involves
- Activity Type: physical/mental/social/self_care
- Instructions: Step-by-step how to do it
- Frequency: How often to do it
- Duration: How long each session
- Difficulty Level: beginner/intermediate/advanced
- Relates to Goal: Which goal it supports (if applicable)
- Relates to Homework: Which homework it complements (if applicable)

Format as JSON array:
[
  {{
    "title": "specific activity title",
    "description": "what this activity involves",
    "activity_type": "physical/mental/social/self_care",
    "instructions": "step-by-step instructions",
    "frequency": "daily/3x week/weekly/etc",
    "duration": "10 minutes/30 minutes/etc",
    "difficulty_level": "beginner/intermediate/advanced",
    "relates_to_goal": "goal description if applicable",
    "relates_to_homework": "homework type if applicable"
  }}
]

Focus on evidence-based wellness activities. Consider the patient's current capacity and symptoms.
"""
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(lifestyle_prompt)
            )
            
            # Parse JSON response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                recommendations_data = json.loads(json_match.group())
                return [LifestyleRecommendation(**rec) for rec in recommendations_data]
            else:
                return self._fallback_lifestyle_recommendations(keywords_data, goals, homework)
                
        except Exception as e:
            print(f"Lifestyle recommendation error: {e}")
            return self._fallback_lifestyle_recommendations(keywords_data, goals, homework)
    
    def _format_goals(self, goals: List[Dict[str, Any]]) -> str:
        """Format goals for prompt"""
        if not goals:
            return "No specific goals set yet."
        
        formatted = []
        for goal in goals:
            formatted.append(f"- {goal.get('goal_type', '')}: {goal.get('goal_description', '')}")
        return "\n".join(formatted)
    
    def _format_homework(self, homework: List[Dict[str, Any]]) -> str:
        """Format homework for prompt"""
        if not homework:
            return "No homework assignments yet."
        
        formatted = []
        for hw in homework:
            formatted.append(f"- {hw.get('assignment_type', '')}: {hw.get('description', '')}")
        return "\n".join(formatted)
    
    def _fallback_lifestyle_recommendations(
        self, 
        keywords_data: Dict[str, Any], 
        goals: List[Dict[str, Any]], 
        homework: List[Dict[str, Any]]
    ) -> List[LifestyleRecommendation]:
        """Fallback lifestyle recommendations"""
        
        recommendations = []
        symptoms = keywords_data.get('primary_symptoms', [])
        
        # Physical activity for all
        recommendations.append(LifestyleRecommendation(
            title="Daily Morning Walk",
            description="Start your day with gentle physical activity and fresh air",
            activity_type="physical",
            instructions="Take a 15-20 minute walk outside, preferably in nature or a pleasant neighborhood. Focus on your surroundings and breathe deeply.",
            frequency="daily",
            duration="15-20 minutes",
            difficulty_level="beginner",
            relates_to_goal="General wellness and mood improvement"
        ))
        
        # Mental activity based on symptoms
        if 'anxiety' in symptoms:
            recommendations.append(LifestyleRecommendation(
                title="Progressive Muscle Relaxation",
                description="Learn to release physical tension associated with anxiety",
                activity_type="mental",
                instructions="Find a quiet space. Tense and then relax each muscle group starting from your toes and working up to your head.",
                frequency="daily",
                duration="10-15 minutes", 
                difficulty_level="beginner",
                relates_to_homework="Anxiety management practice"
            ))
        
        return recommendations


class RecommendationEngine:
    """Main recommendation engine that coordinates all components"""
    
    def __init__(self, gemini_model):
        self.keyword_extractor = TherapyKeywordExtractor(gemini_model)
        self.content_generator = ContentRecommendationGenerator(gemini_model)
        self.lifestyle_generator = LifestyleRecommendationGenerator(gemini_model)
    
    async def generate_recommendations(
        self,
        conversation_history: List[Dict[str, Any]],
        goals: List[Dict[str, Any]] = None,
        homework: List[Dict[str, Any]] = None,
        content_count: int = 5,
        lifestyle_count: int = 6
    ) -> Dict[str, Any]:
        """
        Generate complete recommendations for a therapy session
        
        Args:
            conversation_history: List of conversation exchanges
            goals: Patient's treatment goals
            homework: Patient's homework assignments
            content_count: Number of content recommendations
            lifestyle_count: Number of lifestyle recommendations
            
        Returns:
            Dictionary containing all recommendations and analysis
        """
        
        # Extract keywords and themes
        keywords_data = await self.keyword_extractor.extract_keywords_and_themes(conversation_history)
        
        # Generate content recommendations
        content_recommendations = await self.content_generator.generate_content_recommendations(
            keywords_data, content_count
        )
        
        # Generate lifestyle recommendations
        lifestyle_recommendations = await self.lifestyle_generator.generate_lifestyle_recommendations(
            keywords_data, goals or [], homework or [], lifestyle_count
        )
        
        return {
            "session_analysis": keywords_data,
            "content_recommendations": [
                {
                    "title": rec.title,
                    "description": rec.description,
                    "content_type": rec.content_type,
                    "search_query": rec.search_query,
                    "relevance_reason": rec.relevance_reason,
                    "estimated_duration": rec.estimated_duration
                } for rec in content_recommendations
            ],
            "lifestyle_recommendations": [
                {
                    "title": rec.title,
                    "description": rec.description,
                    "activity_type": rec.activity_type,
                    "instructions": rec.instructions,
                    "frequency": rec.frequency,
                    "duration": rec.duration,
                    "difficulty_level": rec.difficulty_level,
                    "relates_to_goal": rec.relates_to_goal,
                    "relates_to_homework": rec.relates_to_homework
                } for rec in lifestyle_recommendations
            ],
            "recommendation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "session_themes": keywords_data.get('therapeutic_themes', []),
                "primary_focus": keywords_data.get('primary_symptoms', []),
                "motivation_level": keywords_data.get('motivation_level', 'medium')
            }
        }


# Usage example and testing function
async def test_recommendation_engine():
    """Test the recommendation engine with sample data"""
    
    # Initialize Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Create recommendation engine
    engine = RecommendationEngine(model)
    
    # Sample conversation history
    sample_conversation = [
        {
            "user": "I've been feeling really anxious about work lately",
            "ai": "I hear that work has been causing you anxiety. Can you tell me more about what's happening at work?",
            "phase": "intake"
        },
        {
            "user": "My boss keeps giving me impossible deadlines and I can't sleep",
            "ai": "That sounds very stressful. Sleep problems often go hand in hand with work anxiety. How long has this been going on?",
            "phase": "assessment"
        }
    ]
    
    # Sample goals and homework
    sample_goals = [
        {
            "goal_type": "symptom",
            "goal_description": "Reduce work-related anxiety within 6 weeks"
        }
    ]
    
    sample_homework = [
        {
            "assignment_type": "thought_record",
            "description": "Track anxious thoughts about work daily"
        }
    ]
    
    # Generate recommendations
    recommendations = await engine.generate_recommendations(
        sample_conversation, sample_goals, sample_homework
    )
    
    return recommendations


if __name__ == "__main__":
    # Test the recommendation engine
    async def main():
        genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
        recommendations = await test_recommendation_engine()
        print(json.dumps(recommendations, indent=2))
    
    asyncio.run(main())