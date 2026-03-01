"""
Test suite for Component 4 Feature Engineer
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from comp4.data.schemas import Component4Input, EngineeredFeatures, UserHistoryContext
from comp4.src.feature_engineer import FeatureEngineer

class TestFeatureEngineer:
    """Test cases for FeatureEngineer"""
    
    @pytest.fixture
    def feature_engineer(self):
        """Create FeatureEngineer instance"""
        return FeatureEngineer()
    
    @pytest.fixture
    def mock_emotion_analysis(self):
        """Create mock emotion analysis"""
        mock_emotions = MagicMock()
        mock_emotions.joy = 0.8
        mock_emotions.sadness = 0.1
        mock_emotions.anger = 0.0
        mock_emotions.fear = 0.1
        mock_emotions.surprise = 0.0
        mock_emotions.disgust = 0.0
        mock_emotions.anticipation = 0.0
        mock_emotions.trust = 0.0
        
        mock_analysis = MagicMock()
        mock_analysis.emotions = mock_emotions
        mock_analysis.dominant_emotion = "joy"
        mock_analysis.intensity = 0.8
        mock_analysis.confidence = 0.9
        
        return mock_analysis
    
    @pytest.fixture
    def mock_semantic_analysis(self):
        """Create mock semantic analysis"""
        mock_person = MagicMock()
        mock_person.name = "John"
        mock_person.relationship_type = "friend"
        mock_person.confidence = 0.8
        mock_person.mentions = 1
        
        mock_analysis = MagicMock()
        mock_analysis.people = [mock_person]
        mock_analysis.organizations = []
        mock_analysis.locations = []
        mock_analysis.detected_topics = ["work", "meeting"]
        mock_analysis.future_events = []
        mock_analysis.novelty_score = 0.6
        mock_analysis.complexity_score = 0.4
        
        return mock_analysis
    
    @pytest.fixture
    def mock_user_history(self):
        """Create mock user history"""
        return UserHistoryContext(
            writing_frequency_baseline=0.5,
            emotional_baseline={"joy": 0.6, "sadness": 0.2, "anger": 0.1},
            topic_preferences=["work", "family"],
            behavioral_patterns={"avg_entry_length": 150},
            last_entry_timestamp=datetime.now() - timedelta(days=1),
            total_entries=10,
            preferred_writing_times=[9, 14, 20]
        )
    
    @pytest.fixture
    def component4_input(self, mock_emotion_analysis, mock_semantic_analysis, mock_user_history):
        """Create Component4Input for testing"""
        return Component4Input(
            emotion_analysis=mock_emotion_analysis,
            semantic_analysis=mock_semantic_analysis,
            user_id="test_user_001",
            entry_id="test_entry_001",
            session_id="test_session_001",
            entry_timestamp=datetime.now(),
            raw_text="Had a great meeting with John today about the new project. Really excited about the possibilities!",
            user_history=mock_user_history,
            previous_entries=[]
        )
    
    def test_feature_engineer_initialization(self, feature_engineer):
        """Test FeatureEngineer initialization"""
        assert feature_engineer.name == "FeatureEngineer"
        assert feature_engineer.version == "4.0"
        assert feature_engineer.temporal_extractor is not None
        assert feature_engineer.emotional_extractor is not None
        assert feature_engineer.semantic_extractor is not None
        assert feature_engineer.user_extractor is not None
        assert feature_engineer.quality_controller is not None
    
    def test_engineer_features_basic(self, feature_engineer, component4_input):
        """Test basic feature engineering"""
        result = feature_engineer.engineer_features(component4_input)
        
        # Check return type
        assert isinstance(result, EngineeredFeatures)
        
        # Check feature vector dimensions
        assert result.feature_vector.shape == (90,)
        assert result.temporal_features.shape == (25,)
        assert result.emotional_features.shape == (20,)
        assert result.semantic_features.shape == (30,)
        assert result.user_features.shape == (15,)
        
        # Check metadata
        assert result.metadata is not None
        assert result.user_id == "test_user_001"
        assert result.entry_id == "test_entry_001"
        
        # Check quality metrics
        assert 0.0 <= result.feature_completeness <= 1.0
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.processing_time_ms >= 0
    
    def test_feature_vector_concatenation(self, feature_engineer, component4_input):
        """Test that main feature vector is correct concatenation"""
        result = feature_engineer.engineer_features(component4_input)
        
        # Reconstruct main vector
        reconstructed = np.concatenate([
            result.temporal_features,
            result.emotional_features,
            result.semantic_features,
            result.user_features
        ])
        
        # Should match main feature vector
        np.testing.assert_array_almost_equal(result.feature_vector, reconstructed, decimal=6)
    
    def test_feature_value_ranges(self, feature_engineer, component4_input):
        """Test that feature values are in expected ranges"""
        result = feature_engineer.engineer_features(component4_input)
        
        # All features should be finite
        assert np.all(np.isfinite(result.feature_vector))
        assert np.all(np.isfinite(result.temporal_features))
        assert np.all(np.isfinite(result.emotional_features))
        assert np.all(np.isfinite(result.semantic_features))
        assert np.all(np.isfinite(result.user_features))
        
        # Most features should be in [0, 1] range (allowing some tolerance)
        assert np.all(result.feature_vector >= -0.1)
        assert np.all(result.feature_vector <= 1.1)
    
    def test_temporal_features_extraction(self, feature_engineer, component4_input):
        """Test temporal features extraction"""
        temporal_features = feature_engineer._extract_temporal_features(component4_input)
        
        assert temporal_features is not None
        assert hasattr(temporal_features, 'cyclical_hour')
        assert hasattr(temporal_features, 'cyclical_day')
        assert hasattr(temporal_features, 'days_since_last')
        
        # Check cyclical hour is in valid range
        assert 0 <= temporal_features.cyclical_hour <= 23
        assert 0 <= temporal_features.cyclical_day <= 6
    
    def test_emotional_features_extraction(self, feature_engineer, component4_input):
        """Test emotional features extraction"""
        emotional_features = feature_engineer._extract_emotional_features(component4_input)
        
        assert emotional_features is not None
        assert hasattr(emotional_features, 'emotion_vector')
        assert hasattr(emotional_features, 'dominant_emotion_idx')
        assert hasattr(emotional_features, 'emotional_intensity')
        
        # Check emotion vector
        assert emotional_features.emotion_vector.shape == (8,)
        assert np.all(emotional_features.emotion_vector >= 0)
        assert np.all(emotional_features.emotion_vector <= 1)
        
        # Check dominant emotion index
        assert 0 <= emotional_features.dominant_emotion_idx <= 7
    
    def test_semantic_features_extraction(self, feature_engineer, component4_input):
        """Test semantic features extraction"""
        semantic_features = feature_engineer._extract_semantic_features(component4_input)
        
        assert semantic_features is not None
        assert hasattr(semantic_features, 'topic_distribution')
        assert hasattr(semantic_features, 'novelty_score')
        assert hasattr(semantic_features, 'complexity_score')
        
        # Check topic distribution
        assert semantic_features.topic_distribution.shape == (10,)
        assert np.all(semantic_features.topic_distribution >= 0)
        assert np.all(semantic_features.topic_distribution <= 1)
        
        # Check scores
        assert 0 <= semantic_features.novelty_score <= 1
        assert 0 <= semantic_features.complexity_score <= 1
    
    def test_user_features_extraction(self, feature_engineer, component4_input):
        """Test user features extraction"""
        user_features = feature_engineer._extract_user_features(component4_input)
        
        assert user_features is not None
        assert hasattr(user_features, 'writing_consistency')
        assert hasattr(user_features, 'engagement_level')
        assert hasattr(user_features, 'personal_growth')
        
        # Check feature ranges
        assert 0 <= user_features.writing_consistency <= 1
        assert 0 <= user_features.engagement_level <= 1
        assert 0 <= user_features.personal_growth <= 1
    
    def test_confidence_score_calculation(self, feature_engineer, component4_input):
        """Test confidence score calculation"""
        result = feature_engineer.engineer_features(component4_input)
        
        assert 0.0 <= result.confidence_score <= 1.0
        
        # Confidence should be reasonable for good input
        assert result.confidence_score > 0.3  # Should be above minimum threshold
    
    def test_metadata_generation(self, feature_engineer, component4_input):
        """Test metadata generation"""
        result = feature_engineer.engineer_features(component4_input)
        
        metadata = result.metadata
        assert metadata is not None
        assert metadata.original_entry_id == "test_entry_001"
        assert 0 <= metadata.importance_score <= 1
        assert 0 <= metadata.emotional_significance <= 1
        assert 0 <= metadata.temporal_relevance <= 1
        
        # Check gate scores
        assert 'forget_score' in metadata.gate_scores
        assert 'input_score' in metadata.gate_scores
        assert 'output_score' in metadata.gate_scores
        assert 'confidence' in metadata.gate_scores
        
        for score in metadata.gate_scores.values():
            assert 0 <= score <= 1
    
    def test_error_handling_missing_data(self, feature_engineer):
        """Test error handling with missing data"""
        # Create input with missing components
        incomplete_input = Component4Input(
            emotion_analysis=None,
            semantic_analysis=None,
            user_id="test_user",
            entry_id="test_entry",
            session_id="test_session",
            entry_timestamp=datetime.now(),
            raw_text="Test text"
        )
        
        # Should not crash, should return default features
        result = feature_engineer.engineer_features(incomplete_input)
        
        assert isinstance(result, EngineeredFeatures)
        assert result.feature_vector.shape == (90,)
        assert result.confidence_score == 0.0  # Should be low for missing data
    
    def test_batch_processing(self, feature_engineer, component4_input):
        """Test batch processing"""
        # Create multiple inputs
        inputs = [component4_input] * 3
        
        results = feature_engineer.batch_engineer_features(inputs)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, EngineeredFeatures)
            assert result.feature_vector.shape == (90,)
    
    def test_performance_tracking(self, feature_engineer, component4_input):
        """Test performance tracking"""
        initial_count = feature_engineer.total_processed
        
        feature_engineer.engineer_features(component4_input)
        
        # Should increment counter
        assert feature_engineer.total_processed == initial_count + 1
        assert feature_engineer.total_processing_time > 0
    
    def test_config_impact(self):
        """Test that configuration affects feature engineering"""
        # Test with different normalization methods
        config1 = {'normalization_method': 'minmax'}
        config2 = {'normalization_method': 'zscore'}
        
        fe1 = FeatureEngineer(config1)
        fe2 = FeatureEngineer(config2)
        
        # Both should initialize successfully
        assert fe1.config['normalization_method'] == 'minmax'
        assert fe2.config['normalization_method'] == 'zscore'
    
    def test_quality_control_integration(self, feature_engineer, component4_input):
        """Test quality control integration"""
        result = feature_engineer.engineer_features(component4_input)
        
        # Quality controller should have validated features
        assert hasattr(result.metadata, 'feature_quality_score')
        assert 0 <= result.metadata.feature_quality_score <= 1
    
    @pytest.mark.parametrize("user_history", [None, "empty_history"])
    def test_different_user_histories(self, feature_engineer, component4_input, user_history):
        """Test with different user history scenarios"""
        if user_history == "empty_history":
            component4_input.user_history = UserHistoryContext(
                writing_frequency_baseline=0.0,
                emotional_baseline={},
                topic_preferences=[],
                behavioral_patterns={},
                total_entries=0
            )
        elif user_history is None:
            component4_input.user_history = None
        
        result = feature_engineer.engineer_features(component4_input)
        
        # Should handle different scenarios gracefully
        assert isinstance(result, EngineeredFeatures)
        assert result.feature_vector.shape == (90,)
    
    def test_feature_engineering_consistency(self, feature_engineer, component4_input):
        """Test that feature engineering produces consistent results"""
        # Process same input multiple times
        result1 = feature_engineer.engineer_features(component4_input)
        result2 = feature_engineer.engineer_features(component4_input)
        
        # Results should be very similar (allowing for small floating point differences)
        np.testing.assert_array_almost_equal(
            result1.feature_vector, 
            result2.feature_vector, 
            decimal=4
        )
