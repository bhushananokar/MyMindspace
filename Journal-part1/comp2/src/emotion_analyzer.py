"""
Main emotion analyzer orchestrator for Component 2
Combines base emotion detection with RL personalization
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Union
import logging
from pathlib import Path
import json
from datetime import datetime

from comp2.data.schemas import (
    EmotionAnalysis, EmotionScores, RLState, RLAction,
    UserCalibration, UserFeedback, ModelConfig
)
from comp2.models.emotion_models import SACAgent
from comp2.models import create_sac_agent
from .base_emotion_detector import BaseEmotionDetector
from .reward_calculator import RewardCalculator
from comp2.utils.config import ComponentConfig, load_config

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """
    Main emotion analyzer combining base detection + RL personalization
    Provides the primary interface for Component 2
    """
    
    def __init__(
        self,
        config_path: str = "config.yaml",
        models_dir: str = "./models/saved_models",
        user_data_dir: str = "./data/user_data",
        device: str = None
    ):
        """
        Initialize the complete emotion analysis system
        
        Args:
            config_path: Path to configuration file
            models_dir: Directory for saved models
            user_data_dir: Directory for user-specific data
            device: 'cpu', 'cuda', or None (auto-detect)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.models_dir = Path(models_dir)
        self.user_data_dir = Path(user_data_dir)
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.base_detector = None
        self.reward_calculator = None
        self.user_agents: Dict[str, SACAgent] = {}  # User-specific RL agents
        self.user_calibrations: Dict[str, UserCalibration] = {}
        
        # Initialize system
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing emotion analyzer components...")
            
            # Initialize base emotion detector - FIX: Use correct config structure
            self.base_detector = BaseEmotionDetector(
                model_name=self.config.base_emotion.model_name,
                device=self.device,
                cache_dir=str(self.models_dir),
                max_length=self.config.base_emotion.max_sequence_length
            )
            
            # Initialize reward calculator
            self.reward_calculator = RewardCalculator()
            
            # Load existing user calibrations
            self._load_user_calibrations()
            
            logger.info("Emotion analyzer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize emotion analyzer: {e}")
            raise
    
    def _load_user_calibrations(self):
        """Load existing user calibration data"""
        try:
            calibrations_file = self.user_data_dir / "user_calibrations.json"
            if calibrations_file.exists():
                with open(calibrations_file, 'r') as f:
                    data = json.load(f)
                    
                for user_id, cal_data in data.items():
                    self.user_calibrations[user_id] = UserCalibration(**cal_data)
                    
                logger.info(f"Loaded calibrations for {len(self.user_calibrations)} users")
        except Exception as e:
            logger.warning(f"Could not load user calibrations: {e}")
    
    def _save_user_calibrations(self):
        """Save user calibration data"""
        try:
            calibrations_file = self.user_data_dir / "user_calibrations.json"
            data = {}
            
            for user_id, calibration in self.user_calibrations.items():
                data[user_id] = calibration.dict()
                
            with open(calibrations_file, 'w') as f:
                json.dump(data, f, default=str, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save user calibrations: {e}")
    
    def _get_user_agent(self, user_id: str) -> Optional[SACAgent]:
        """Get or create RL agent for user"""
        if user_id not in self.user_agents:
            try:
                # Calculate state dimension
                # Features from base detector (768) + context features
                state_dim = 768 + 20  # Base features + context
                
                # Create new agent - FIX: Use correct config structure
                agent = create_sac_agent(
                    state_dim=state_dim,
                    device=self.device,
                    learning_rate=self.config.rl.learning_rate,
                    gamma=self.config.rl.gamma,
                    tau=self.config.rl.tau,
                    alpha=self.config.rl.alpha
                )
                
                # Try to load existing model
                model_path = self.models_dir / f"user_{user_id}_sac_model.pt"
                if model_path.exists():
                    agent.load(str(model_path))
                    logger.info(f"Loaded existing model for user {user_id}")
                else:
                    logger.info(f"Created new model for user {user_id}")
                
                self.user_agents[user_id] = agent
                
            except Exception as e:
                logger.error(f"Failed to create agent for user {user_id}: {e}")
                return None
        
        return self.user_agents[user_id]
    
    def _create_rl_state(
        self, 
        text: str, 
        base_analysis: EmotionAnalysis,
        user_id: str
    ) -> RLState:
        """
        Create RL state representation
        
        Args:
            text: Original text
            base_analysis: Base emotion analysis
            user_id: User identifier
            
        Returns:
            RL state for policy network
        """
        # Get text features from base detector
        text_features = self.base_detector.get_features(text).tolist()
        
        # User history (recent emotion patterns)
        calibration = self.user_calibrations.get(user_id)
        if calibration and calibration.reward_history:
            user_history = calibration.reward_history[-10:]  # Last 10 rewards
        else:
            user_history = [0.0] * 10
        
        # Context features (time, intensity, confidence)
        hour = datetime.now().hour / 24.0  # Normalize to 0-1
        context_features = [
            hour,
            base_analysis.intensity,
            base_analysis.confidence,
            len(text) / 1000.0,  # Text length normalized
            sum(base_analysis.emotions.to_list()),  # Total emotional activity
            max(base_analysis.emotions.to_list()),  # Peak emotion
            np.std(base_analysis.emotions.to_list()),  # Emotional variance
            1.0 if base_analysis.dominant_emotion in ['joy', 'trust'] else 0.0,  # Positive dominant
            1.0 if base_analysis.dominant_emotion in ['sadness', 'anger', 'fear'] else 0.0,  # Negative dominant
            float(calibration.feedback_count if calibration else 0) / 100.0  # Feedback history
        ]
        
        return RLState(
            text_features=text_features,
            base_emotions=base_analysis.emotions,
            user_history=user_history,
            context_features=context_features
        )
    
    def _apply_rl_adjustments(
        self, 
        base_analysis: EmotionAnalysis, 
        action: RLAction
    ) -> EmotionAnalysis:
        """
        Apply RL adjustments to base emotion analysis
        
        Args:
            base_analysis: Original analysis
            action: RL action with adjustments
            
        Returns:
            Calibrated emotion analysis
        """
        # Get base emotions as array
        base_emotions = np.array(base_analysis.emotions.to_list())
        
        # Apply adjustments
        adjusted_emotions = base_emotions + np.array(action.emotion_adjustments)
        
        # Clamp to valid range [0, 1]
        adjusted_emotions = np.clip(adjusted_emotions, 0.0, 1.0)
        
        # Create new emotion scores
        emotion_names = ['joy', 'sadness', 'anger', 'fear', 
                        'surprise', 'disgust', 'anticipation', 'trust']
        emotion_dict = {name: float(score) for name, score in zip(emotion_names, adjusted_emotions)}
        new_emotions = EmotionScores(**emotion_dict)
        
        # Apply confidence adjustment
        new_confidence = np.clip(
            base_analysis.confidence + action.confidence_modifier, 
            0.0, 1.0
        )
        
        # Calculate new intensity
        new_intensity = float(np.mean(adjusted_emotions))
        
        # Create calibrated analysis
        return EmotionAnalysis(
            emotions=new_emotions,
            dominant_emotion=new_emotions.dominant_emotion(),
            intensity=new_intensity,
            confidence=new_confidence,
            calibration_applied=True,
            model_version=f"{base_analysis.model_version}_rl_calibrated",
            processing_time_ms=base_analysis.processing_time_ms + 50,  # Add RL processing time
            timestamp=datetime.now()
        )
    
    def analyze_emotion(self, text: str, user_id: str) -> EmotionAnalysis:
        """
        Main emotion analysis method
        
        Args:
            text: Text to analyze
            user_id: User identifier for personalization
            
        Returns:
            Personalized emotion analysis
        """
        if not text or not text.strip():
            # Return neutral for empty text
            return EmotionAnalysis(
                emotions=EmotionScores(),
                dominant_emotion='trust',
                intensity=0.1,
                confidence=0.5,
                calibration_applied=False,
                model_version="empty_text_v1.0"
            )
        
        try:
            # Get base emotion analysis
            base_analysis = self.base_detector.detect_emotions(text)
            
            # Get user's RL agent
            agent = self._get_user_agent(user_id)
            
            if agent is None:
                # Return base analysis if no RL agent available
                return base_analysis
            
            # Create RL state
            state = self._create_rl_state(text, base_analysis, user_id)
            
            # Get RL action (emotion adjustments)
            state_vector = np.array(state.to_vector(), dtype=np.float32)
            action_vector = agent.get_action(state_vector, deterministic=False)
            
            # Create action object
            action = RLAction(
                emotion_adjustments=action_vector[:8].tolist(),
                confidence_modifier=float(action_vector[8])
            )
            
            # Apply RL adjustments
            calibrated_analysis = self._apply_rl_adjustments(base_analysis, action)
            
            return calibrated_analysis
            
        except Exception as e:
            logger.error(f"Error in emotion analysis for user {user_id}: {e}")
            # Return base analysis on error
            return self.base_detector.detect_emotions(text)
    
    def process_user_feedback(
        self, 
        feedback: UserFeedback, 
        original_analysis: EmotionAnalysis
    ) -> bool:
        """
        Process user feedback to improve RL model
        
        Args:
            feedback: User feedback data
            original_analysis: Original emotion analysis that received feedback
            
        Returns:
            Success status
        """
        try:
            user_id = feedback.user_id
            
            # Calculate reward
            reward = self.reward_calculator.calculate_reward(feedback)
            
            # Get or create user calibration
            if user_id not in self.user_calibrations:
                self.user_calibrations[user_id] = UserCalibration(user_id=user_id)
            
            calibration = self.user_calibrations[user_id]
            
            # Update calibration metrics
            calibration.feedback_count += 1
            calibration.reward_history.append(reward.total_reward)
            
            # Keep only recent rewards
            if len(calibration.reward_history) > 1000:
                calibration.reward_history = calibration.reward_history[-1000:]
            
            calibration.avg_reward = np.mean(calibration.reward_history)
            calibration.last_updated = datetime.now()
            
            # Save calibration
            self._save_user_calibrations()
            
            logger.info(f"Processed feedback for user {user_id}: reward={reward.total_reward:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process user feedback: {e}")
            return False
    
    def batch_analyze_emotions(
        self, 
        texts: List[str], 
        user_id: str
    ) -> List[EmotionAnalysis]:
        """
        Batch emotion analysis for efficiency
        
        Args:
            texts: List of texts to analyze
            user_id: User identifier
            
        Returns:
            List of emotion analyses
        """
        return [self.analyze_emotion(text, user_id) for text in texts]
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """
        Get user's personalization statistics
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user stats or None
        """
        calibration = self.user_calibrations.get(user_id)
        if not calibration:
            return None
        
        return {
            'feedback_count': calibration.feedback_count,
            'avg_reward': calibration.avg_reward,
            'recent_performance': calibration.get_recent_performance(),
            'accuracy_improvement': calibration.accuracy_improvement,
            'last_updated': calibration.last_updated.isoformat()
        }
    
    def save_user_model(self, user_id: str) -> bool:
        """
        Save user's RL model to disk
        
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            if user_id in self.user_agents:
                model_path = self.models_dir / f"user_{user_id}_sac_model.pt"
                self.user_agents[user_id].save(str(model_path))
                logger.info(f"Saved model for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to save model for user {user_id}: {e}")
        return False
    
    def cleanup_user_data(self, user_id: str) -> bool:
        """
        Remove user's data (for privacy compliance)
        
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            # Remove from memory
            if user_id in self.user_agents:
                del self.user_agents[user_id]
            
            if user_id in self.user_calibrations:
                del self.user_calibrations[user_id]
            
            # Remove model file
            model_path = self.models_dir / f"user_{user_id}_sac_model.pt"
            if model_path.exists():
                model_path.unlink()
            
            # Save updated calibrations
            self._save_user_calibrations()
            
            logger.info(f"Cleaned up data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup user {user_id}: {e}")
            return False