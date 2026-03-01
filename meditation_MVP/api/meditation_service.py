import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

from fastapi import HTTPException
from database.api_collections import save_session, update_session, get_user, create_user
from database.sync_collections import sync_create_user, sync_save_session, sync_update_session
from Core_engine.meditation_selector import MeditationSelectorModule
from api.constants import validate_meditation_recommendations, map_meditation_type_to_api
import google.generativeai as genai
import os
class MeditationService:
    """Core meditation recommendation and script generation service"""
    
    def __init__(self):
        self.meditation_selector = MeditationSelectorModule(use_ml=True)
        self.meditation_data = self._load_meditation_data()
        
        # Configure Gemini API for script generation
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-flash-latest')
            self.has_gemini = True
            logger.info("Gemini model initialised: gemini-flash-latest")
        except Exception as e:
            self.has_gemini = False
            logger.warning(f"Gemini unavailable — script generation will use fallback template. Reason: {e}")
    
    def _load_meditation_data(self) -> pd.DataFrame:
        """Load meditation types from CSV"""
        try:
            return pd.read_csv('Core_engine/meditation.csv')
        except FileNotFoundError:
            # Fallback meditation types if CSV not found
            return pd.DataFrame({
                'Name': [
                    'Mindfulness Meditation',
                    'Body Scan Meditation', 
                    'Breathing Meditation',
                    'Loving-Kindness Meditation',
                    'Progressive Muscle Relaxation'
                ],
                'Instructions': [
                    'Focus on present moment awareness',
                    'Systematically scan your body for tension',
                    'Focus on your natural breathing rhythm',
                    'Cultivate feelings of love and compassion',
                    'Tense and release muscle groups'
                ]
            })
    
    async def get_text_recommendations(self, diary_text: str, user_id: str) -> Dict[str, Any]:
        """
        Get meditation recommendations based on text input
        
        Args:
            diary_text: User's diary entry or current state
            user_id: User ID for personalization
            
        Returns:
            Dict with recommendations and session info
        """
        
        # Create session using sync version to avoid aiohttp issues
        local_id = str(uuid.uuid4())
        session_id = local_id
        try:
            api_session_id = sync_save_session({
                'id': local_id,
                'user_id': user_id,
                'status': 'processing',
                'input_type': 'text',
                'input_data': {'diary_text': diary_text}
            })
            session_id = api_session_id or local_id
        except Exception as e:
            print(f"Warning: Could not save session to API: {e}")
            # Continue without saving - the recommendation is the priority
        
        try:
            # Create temp files for meditation selector
            recommendations = await self._process_text_recommendations(diary_text, user_id)
            
            # Validate and fix recommendations for API compatibility
            validated_recommendations = validate_meditation_recommendations(recommendations)
            
            # Update session with results
            try:
                sync_update_session(session_id, {
                    'status': 'completed',
                    'results': {
                        'recommendations': validated_recommendations,
                        'method': 'text_processing'
                    }
                })
            except Exception as e:
                print(f"Warning: Could not update session: {e}")
            
            return {
                'session_id': session_id,
                'recommendations': validated_recommendations,
                'status': 'completed',
                'method': 'text_analysis'
            }
            
        except Exception as e:
            try:
                sync_update_session(session_id, {
                    'status': 'failed',
                    'error': str(e)
                })
            except:
                pass  # Don't fail on session update failure
            raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")
    
    async def _process_text_recommendations(self, diary_text: str, user_id: str) -> List[Dict[str, Any]]:
        """Process text and get recommendations using existing meditation selector"""
        
        # Create temporary files for meditation selector
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create feedback file
            feedback_file = temp_path / "user_feedback.json"
            feedback_data = [{
                "user_prompt": diary_text,
                "feedbackText": diary_text
            }]
            with open(feedback_file, 'w') as f:
                json.dump(feedback_data, f)
            
            # Create simple diagnosis file
            diagnosis_file = temp_path / "diagnosis.json"
            diagnosis_data = {"diagnosis": "general_wellness", "text_analysis": diary_text}
            with open(diagnosis_file, 'w') as f:
                json.dump(diagnosis_data, f)
            
            # Get recommendations from meditation selector
            try:
                result = self.meditation_selector.select_meditation(
                    str(feedback_file), 
                    str(diagnosis_file)
                )
                
                # Convert to API format
                recommendations = []
                if 'recommendations' in result:
                    for rec in result['recommendations'][:5]:  # Top 5
                        # Ensure all required fields are present
                        recommendation = {
                            'meditation_type': rec.get('meditation_type', 'Mindfulness Meditation'),
                            'confidence': float(rec.get('confidence', 0.5)),
                            'rationale': rec.get('rationale', 'Recommended based on your input'),
                            'source': rec.get('source', 'meditation_selector')
                        }
                        recommendations.append(recommendation)
                
                # If no recommendations, use fallback
                if not recommendations:
                    recommendations = self._get_fallback_recommendations(diary_text)
                
                return recommendations
                
            except Exception as e:
                # Fallback to simple keyword matching
                return self._get_fallback_recommendations(diary_text)
    
    def _get_fallback_recommendations(self, text: str) -> List[Dict[str, Any]]:
        """Simple fallback recommendations based on keywords"""
        
        text_lower = text.lower()
        recommendations = []
        
        # Simple keyword matching
        if any(word in text_lower for word in ['anxious', 'anxiety', 'worry', 'nervous']):
            recommendations.append({
                'meditation_type': 'breathing',
                'confidence': 0.85,
                'rationale': 'Breathing meditation helps calm anxiety',
                'source': 'keyword_fallback'
            })
        
        if any(word in text_lower for word in ['stress', 'tension', 'overwhelmed']):
            recommendations.append({
                'meditation_type': 'body_scan',
                'confidence': 0.80,
                'rationale': 'Body scan helps release physical tension',
                'source': 'keyword_fallback'
            })
        
        if any(word in text_lower for word in ['sleep', 'tired', 'insomnia', 'rest']):
            recommendations.append({
                'meditation_type': 'movement',
                'confidence': 0.75,
                'rationale': 'Progressive relaxation aids sleep',
                'source': 'keyword_fallback'
            })
        
        # Default recommendation
        if not recommendations:
            recommendations.append({
                'meditation_type': 'mindfulness',
                'confidence': 0.70,
                'rationale': 'General mindfulness practice',
                'source': 'default'
            })
        
        return recommendations
    
    async def generate_meditation_script(self, meditation_type: str, user_id: str, duration_minutes: int = 5) -> Dict[str, Any]:
        """
        Generate TTS-ready meditation script
        
        Args:
            meditation_type: Type of meditation to generate script for
            user_id: User ID for personalization
            duration_minutes: Desired script duration
            
        Returns:
            Dict with generated script and metadata
        """
        
        # Find meditation instructions
        meditation_row = self.meditation_data[self.meditation_data['Name'] == meditation_type]
        if meditation_row.empty:
            instructions = f"Practice {meditation_type}"
        else:
            instructions = meditation_row.iloc[0]['Instructions']
        
        # Require Gemini — no fallback
        if not self.has_gemini:
            raise HTTPException(status_code=503, detail="Script generation unavailable: Gemini API is not configured")

        script = await self._generate_script_with_gemini(meditation_type, instructions, duration_minutes)

        return {
            'meditation_type': meditation_type,
            'instructions': instructions,
            'script': script,
            'duration_minutes': f"{duration_minutes-1}-{duration_minutes+1}",
            'format': 'TTS-ready'
        }

    async def _generate_script_with_gemini(self, meditation_type: str, instructions: str, duration: int) -> str:
        """Generate script using Gemini API"""

        prompt = f"""Generate a {duration}-minute guided meditation script.
Meditation Type: {meditation_type}
Instructions: {instructions}

Requirements:
- Calm, soothing tone suitable for text-to-speech
- Natural pauses marked with [pause] for TTS timing
- Clear guidance for breathing and body awareness
- Gentle return to awareness at the end
- Approximately {duration} minutes when spoken

Format as spoken text for TTS system."""

        response = self.gemini_model.generate_content(prompt)
        return response.text
    
    async def get_enhanced_recommendations(self, diary_text: str, audio_analysis: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Get enhanced recommendations using both text and audio analysis
        
        Args:
            diary_text: User's text input
            audio_analysis: Results from audio processing
            user_id: User ID
            
        Returns:
            Enhanced recommendations combining text and audio insights
        """
        
        # Get text-based recommendations
        text_recs_result = await self.get_text_recommendations(diary_text, user_id)
        text_recs = text_recs_result['recommendations']
        
        # Analyze audio features for emotional state
        audio_insights = self._analyze_audio_features(audio_analysis)
        
        # Combine and enhance recommendations
        enhanced_recs = self._combine_recommendations(text_recs, audio_insights)
        
        return {
            'session_id': text_recs_result['session_id'],
            'recommendations': enhanced_recs,
            'status': 'completed',
            'audio_insights': audio_insights,
            'method': 'text_audio_combined'
        }
    
    def _analyze_audio_features(self, audio_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from audio analysis results"""
        
        insights = {
            'emotional_state': 'neutral',
            'stress_indicators': [],
            'voice_energy': 'moderate'
        }
        
        try:
            if 'features' in audio_analysis:
                features = audio_analysis['features']
                
                # Analyze emotion if available
                if 'emotion' in features:
                    emotion_probs = features['emotion'].get('probs', [0.33, 0.33, 0.34])
                    if len(emotion_probs) >= 3:
                        if emotion_probs[2] > 0.6:  # stressed
                            insights['emotional_state'] = 'stressed'
                            insights['stress_indicators'].append('high_stress_voice_patterns')
                        elif emotion_probs[0] > 0.6:  # calm
                            insights['emotional_state'] = 'calm'
                
                # Analyze voice activity
                if 'vad' in features:
                    speech_ratio = features['vad'].get('speech_ratio', 0.5)
                    if speech_ratio > 0.8:
                        insights['voice_energy'] = 'high'
                    elif speech_ratio < 0.3:
                        insights['voice_energy'] = 'low'
        
        except Exception:
            pass  # Use defaults on any error
        
        return insights
    
    def _combine_recommendations(self, text_recs: List[Dict], audio_insights: Dict) -> List[Dict]:
        """Combine text and audio insights for enhanced recommendations"""
        
        enhanced_recs = text_recs.copy()
        
        # Boost confidence for stress-related meditations if audio shows stress
        if audio_insights['emotional_state'] == 'stressed':
            for rec in enhanced_recs:
                if any(word in rec['meditation_type'].lower() for word in ['breathing', 'body scan', 'relaxation']):
                    rec['confidence'] = min(0.95, rec['confidence'] * 1.2)
                    rec['rationale'] += ' (Audio analysis confirms stress patterns)'
        
        # Adjust for low energy voice
        if audio_insights['voice_energy'] == 'low':
            for rec in enhanced_recs:
                if 'energizing' in rec['meditation_type'].lower():
                    rec['confidence'] *= 0.8
                elif any(word in rec['meditation_type'].lower() for word in ['gentle', 'body scan', 'progressive']):
                    rec['confidence'] = min(0.95, rec['confidence'] * 1.1)
        
        # Sort by updated confidence
        enhanced_recs.sort(key=lambda x: x['confidence'], reverse=True)
        
        return enhanced_recs

# Global service instance
meditation_service = MeditationService()