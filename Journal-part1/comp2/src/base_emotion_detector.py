"""
Base emotion detection using CardiffNLP's RoBERTa model
Provides foundation emotion scores before RL personalization
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List, Tuple, Optional
import numpy as np
import logging
from pathlib import Path

from comp2.data import EmotionScores, EmotionAnalysis
from comp2.models import EmotionIntensityHead

logger = logging.getLogger(__name__)


class BaseEmotionDetector:
    """
    Cardiff NLP RoBERTa-based emotion detection
    Maps to 8 emotions: joy, sadness, anger, fear, surprise, disgust, anticipation, trust
    """
    
    EMOTION_MAPPING = {
        # Cardiff model outputs -> our 8 emotions
        'joy': 'joy',
        'optimism': 'joy', 
        'sadness': 'sadness',
        'anger': 'anger',
        'fear': 'fear',
        'surprise': 'surprise',
        'disgust': 'disgust',
        'anticipation': 'anticipation',
        'trust': 'trust',
        'love': 'joy',  # Map love to joy
        'pessimism': 'sadness',  # Map pessimism to sadness
    }
    
    def __init__(
        self,
        model_name: str = "cardiffnlp/twitter-roberta-base-emotion",
        device: str = None,
        cache_dir: str = "./models/saved_models",
        max_length: int = 512
    ):
        """
        Initialize base emotion detector
        
        Args:
            model_name: HuggingFace model identifier
            device: 'cpu', 'cuda', or None (auto-detect)
            cache_dir: Directory to cache downloaded models
            max_length: Maximum sequence length for tokenization
        """
        self.model_name = model_name
        self.max_length = max_length
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.tokenizer = None
        self.model = None
        self.intensity_head = None
        self._label_mapping = None
        
        # Load model
        self._load_model()
        
    def _load_model(self):
        """Load tokenizer and model from HuggingFace"""
        try:
            logger.info(f"Loading base emotion model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()
            
            # Create intensity head for fine-grained scores
            hidden_size = self.model.config.hidden_size
            self.intensity_head = EmotionIntensityHead(hidden_size, num_emotions=8)
            self.intensity_head.to(self.device)
            
            # Get label mapping
            self._create_label_mapping()
            
            logger.info(f"Base emotion model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load emotion model: {e}")
            raise
    
    def _create_label_mapping(self):
        """Create mapping from model labels to our 8 emotion categories"""
        model_labels = self.model.config.id2label
        
        # Initialize our 8 emotions to 0
        self._label_mapping = {
            'joy': [],
            'sadness': [],
            'anger': [],
            'fear': [],
            'surprise': [],
            'disgust': [],
            'anticipation': [],
            'trust': []
        }
        
        # Map model labels to our categories
        for label_id, label_name in model_labels.items():
            label_clean = label_name.lower().strip()
            if label_clean in self.EMOTION_MAPPING:
                target_emotion = self.EMOTION_MAPPING[label_clean]
                self._label_mapping[target_emotion].append(label_id)
        
        logger.info(f"Created label mapping: {self._label_mapping}")
    
    def _preprocess_text(self, text: str) -> Dict[str, torch.Tensor]:
        """
        Tokenize and prepare text for model input
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with input tensors
        """
        # Clean text
        text = text.strip()
        if not text:
            text = "[EMPTY]"
            
        # Tokenize
        inputs = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding=True,
            return_tensors="pt"
        )
        
        # Move to device
        return {k: v.to(self.device) for k, v in inputs.items()}
    
    def _extract_features(self, inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Extract features from RoBERTa model
        
        Args:
            inputs: Tokenized inputs
            
        Returns:
            Hidden state features [batch_size, hidden_size]
        """
        with torch.no_grad():
            outputs = self.model.roberta(**inputs)
            # Use [CLS] token representation
            features = outputs.last_hidden_state[:, 0, :]  # [batch_size, hidden_size]
            return features
    
    def _get_base_predictions(self, inputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Get raw predictions from Cardiff model
        
        Args:
            inputs: Tokenized inputs
            
        Returns:
            Logits tensor [batch_size, num_classes]
        """
        with torch.no_grad():
            outputs = self.model(**inputs)
            return torch.softmax(outputs.logits, dim=-1)
    
    def _map_to_8_emotions(self, predictions: torch.Tensor) -> EmotionScores:
        """
        Map model predictions to our 8 emotion categories
        
        Args:
            predictions: Model predictions [num_classes]
            
        Returns:
            EmotionScores with our 8 emotions
        """
        emotion_scores = {
            'joy': 0.0,
            'sadness': 0.0,
            'anger': 0.0,
            'fear': 0.0,
            'surprise': 0.0,
            'disgust': 0.0,
            'anticipation': 0.0,
            'trust': 0.0
        }
        
        # Sum scores for each emotion category
        for emotion, label_ids in self._label_mapping.items():
            if label_ids:
                # Take max score if multiple labels map to same emotion
                scores = [predictions[label_id].item() for label_id in label_ids]
                emotion_scores[emotion] = max(scores)
        
        return EmotionScores(**emotion_scores)
    
    def _calculate_confidence(
        self, 
        predictions: torch.Tensor, 
        features: torch.Tensor
    ) -> float:
        """
        Calculate confidence score for predictions
        
        Args:
            predictions: Model predictions
            features: Hidden features
            
        Returns:
            Confidence score 0-1
        """
        # Use entropy-based confidence
        entropy = -torch.sum(predictions * torch.log(predictions + 1e-8))
        max_entropy = np.log(len(predictions))
        confidence = 1.0 - (entropy / max_entropy).item()
        
        # Also consider prediction strength
        max_prob = torch.max(predictions).item()
        strength_confidence = max_prob
        
        # Combine both measures
        final_confidence = 0.7 * confidence + 0.3 * strength_confidence
        return float(np.clip(final_confidence, 0.0, 1.0))
    
    def detect_emotions(self, text: str) -> EmotionAnalysis:
        """
        Main emotion detection method
        
        Args:
            text: Input text to analyze
            
        Returns:
            Complete emotion analysis
        """
        if not text or not text.strip():
            # Return neutral emotions for empty text
            return EmotionAnalysis(
                emotions=EmotionScores(),
                dominant_emotion='trust',
                intensity=0.1,
                confidence=0.5,
                calibration_applied=False,
                model_version="cardiff_base_v1.0",
                processing_time_ms=0
            )
        
        try:
            start_time = torch.cuda.Event(enable_timing=True) if self.device == 'cuda' else None
            end_time = torch.cuda.Event(enable_timing=True) if self.device == 'cuda' else None
            
            if start_time:
                start_time.record()
            
            # Preprocess text
            inputs = self._preprocess_text(text)
            
            # Get predictions and features
            predictions = self._get_base_predictions(inputs)
            features = self._extract_features(inputs)
            
            # Map to our 8 emotions
            emotion_scores = self._map_to_8_emotions(predictions[0])
            
            # Use intensity head for refined scores
            if self.intensity_head:
                with torch.no_grad():
                    refined_scores = self.intensity_head(features)[0]
                    
                # Blend original and refined scores
                original = torch.tensor(emotion_scores.to_list())
                blended = 0.6 * refined_scores.cpu() + 0.4 * original
                
                # Update emotion scores
                emotion_names = ['joy', 'sadness', 'anger', 'fear', 
                               'surprise', 'disgust', 'anticipation', 'trust']
                emotion_dict = {name: float(score) for name, score in zip(emotion_names, blended)}
                emotion_scores = EmotionScores(**emotion_dict)
            
            # Calculate overall intensity and confidence
            intensity = float(torch.mean(torch.tensor(emotion_scores.to_list())).item())
            confidence = self._calculate_confidence(predictions[0], features[0])
            
            # Get dominant emotion
            dominant_emotion = emotion_scores.dominant_emotion()
            
            if end_time:
                end_time.record()
                torch.cuda.synchronize()
                processing_time = int(start_time.elapsed_time(end_time))
            else:
                processing_time = 0
            
            return EmotionAnalysis(
                emotions=emotion_scores,
                dominant_emotion=dominant_emotion,
                intensity=intensity,
                confidence=confidence,
                calibration_applied=False,
                model_version="cardiff_base_v1.0",
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in emotion detection: {e}")
            # Return neutral emotions on error
            return EmotionAnalysis(
                emotions=EmotionScores(),
                dominant_emotion='trust',
                intensity=0.1,
                confidence=0.0,
                calibration_applied=False,
                model_version="cardiff_base_v1.0",
                processing_time_ms=0
            )
    
    def batch_detect_emotions(self, texts: List[str]) -> List[EmotionAnalysis]:
        """
        Batch emotion detection for efficiency
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of emotion analyses
        """
        if not texts:
            return []
        
        try:
            # Process all texts
            results = []
            for text in texts:
                result = self.detect_emotions(text)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch emotion detection: {e}")
            # Return neutral emotions for all texts
            return [
                EmotionAnalysis(
                    emotions=EmotionScores(),
                    dominant_emotion='trust',
                    intensity=0.1,
                    confidence=0.0,
                    calibration_applied=False,
                    model_version="cardiff_base_v1.0"
                )
                for _ in texts
            ]
    
    def get_features(self, text: str) -> np.ndarray:
        """
        Extract features for downstream RL processing
        
        Args:
            text: Input text
            
        Returns:
            Feature vector as numpy array
        """
        try:
            inputs = self._preprocess_text(text)
            features = self._extract_features(inputs)
            return features[0].cpu().numpy()
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.zeros(768)  # Return zero vector on error