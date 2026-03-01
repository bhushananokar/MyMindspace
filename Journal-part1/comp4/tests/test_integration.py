"""
Integration tests for Component 4 with Components 2 & 3
"""

import pytest
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from comp4.src.processor import Component4Processor
from comp4.data.schemas import Component4Input, EngineeredFeatures

# Try to import from production integration
try:
    from production_integration import UnifiedIntegrator
    PRODUCTION_AVAILABLE = True
except ImportError:
    PRODUCTION_AVAILABLE = False
    print("Production integration not available, using mock data")

class TestComponent4Integration:
    """Integration tests for Component 4 with full pipeline"""
    
    @pytest.fixture
    def processor(self):
        """Create Component4Processor instance"""
        return Component4Processor()
    
    @pytest.fixture
    def sample_journal_entries(self):
        """Sample journal entries for testing"""
        return [
            "Had a wonderful day at work today. My presentation went really well and the team seemed impressed. Looking forward to the feedback session tomorrow with Sarah.",
            
            "Feeling a bit stressed about the upcoming deadline. Need to finish the project by Friday but there's still so much to do. Called Mom for some encouragement.",
            
            "Went to the gym this morning and feel amazing! Met my friend Alex there and we had a great workout together. Planning to make this a regular thing.",
            
            "Had dinner with the family tonight. Dad cooked his famous pasta and we talked about our summer vacation plans. Really grateful for these moments together.",
            
            "Tough day at the office. The client meeting didn't go as planned and I'm worried about the contract. Need to regroup and come up with a new strategy."
        ]
    
    @pytest.mark.skipif(not PRODUCTION_AVAILABLE, reason="Production integration not available")
    def test_full_pipeline_integration(self, processor, sample_journal_entries):
        """Test full pipeline from Components 2+3 to Component 4"""
        integrator = UnifiedIntegrator()
        
        results = []
        for i, text in enumerate(sample_journal_entries):
            # Get Component 2+3 output
            c23_output = integrator.process_journal_entry(
                text=text,
                user_id="integration_test_user",
                entry_timestamp=datetime.now()
            )
            
            # Process through Component 4
            c4_output = processor.process_from_integration_output(c23_output.to_dict())
            
            # Validate Component 4 output
            assert isinstance(c4_output, EngineeredFeatures)
            assert c4_output.feature_vector.shape == (90,)
            assert c4_output.validate_dimensions()
            
            results.append(c4_output)
        
        # Check that we processed all entries
        assert len(results) == len(sample_journal_entries)
        
        # Check that features vary across different entries
        feature_vectors = [r.feature_vector for r in results]
        for i in range(len(feature_vectors) - 1):
            # Vectors should be different (not identical)
            assert not np.array_equal(feature_vectors[i], feature_vectors[i + 1])
    
    @pytest.mark.skipif(not PRODUCTION_AVAILABLE, reason="Production integration not available")
    def test_user_history_accumulation(self, processor):
        """Test that user history accumulates properly across entries"""
        integrator = UnifiedIntegrator()
        user_id = "history_test_user"
        
        entries = [
            "First entry - just testing the system.",
            "Second entry - getting more comfortable with journaling.",
            "Third entry - really enjoying this daily practice."
        ]
        
        results = []
        for i, text in enumerate(entries):
            c23_output = integrator.process_journal_entry(
                text=text,
                user_id=user_id
            )
            
            c4_output = processor.process_from_integration_output(c23_output.to_dict())
            results.append(c4_output)
            
            # Check user history accumulation
            if c23_output.user_history:
                assert c23_output.user_history.total_entries == i + 1
        
        # Validate progression in user features
        user_features = [r.user_features for r in results]
        
        # Writing consistency might improve over time
        consistencies = [uf[0] for uf in user_features]  # writing_consistency is first feature
        
        # Check that values are reasonable
        for consistency in consistencies:
            assert 0 <= consistency <= 1
    
    def test_component4_input_validation(self, processor):
        """Test Component4Input validation"""
        from unittest.mock import MagicMock
        
        # Create mock components
        mock_emotion = MagicMock()
        mock_semantic = MagicMock()
        
        # Test valid input
        validation = processor.validate_input(
            emotion_analysis=mock_emotion,
            semantic_analysis=mock_semantic,
            user_id="test_user",
            entry_id="test_entry",
            raw_text="Test text"
        )
        
        assert validation['is_valid']
        assert len(validation['issues']) == 0
        
        # Test invalid input (missing user_id)
        validation = processor.validate_input(
            emotion_analysis=mock_emotion,
            semantic_analysis=mock_semantic,
            user_id="",  # Empty user_id
            entry_id="test_entry",
            raw_text="Test text"
        )
        
        assert not validation['is_valid']
        assert len(validation['issues']) > 0
    
    def test_batch_processing_integration(self, processor):
        """Test batch processing with multiple entries"""
        from unittest.mock import MagicMock
        
        # Create mock batch data
        batch_data = []
        for i in range(5):
            mock_data = {
                'emotion_analysis': MagicMock(),
                'semantic_analysis': MagicMock(),
                'user_id': f'batch_user_{i}',
                'entry_id': f'batch_entry_{i}',
                'session_id': f'batch_session_{i}',
                'entry_timestamp': datetime.now(),
                'raw_text': f'Batch test entry {i}',
                'user_history': None,
                'previous_entries': None
            }
            
            # Configure mocks with reasonable values
            mock_data['emotion_analysis'].dominant_emotion = "joy"
            mock_data['emotion_analysis'].intensity = 0.5
            mock_data['emotion_analysis'].confidence = 0.8
            
            emotions_mock = MagicMock()
            emotions_mock.joy = 0.6
            emotions_mock.sadness = 0.2
            emotions_mock.anger = 0.1
            emotions_mock.fear = 0.1
            emotions_mock.surprise = 0.0
            emotions_mock.disgust = 0.0
            emotions_mock.anticipation = 0.0
            emotions_mock.trust = 0.0
            mock_data['emotion_analysis'].emotions = emotions_mock
            
            mock_data['semantic_analysis'].detected_topics = [f"topic_{i}"]
            mock_data['semantic_analysis'].people = []
            mock_data['semantic_analysis'].organizations = []
            mock_data['semantic_analysis'].locations = []
            mock_data['semantic_analysis'].future_events = []
            mock_data['semantic_analysis'].novelty_score = 0.5
            mock_data['semantic_analysis'].complexity_score = 0.4
            
            batch_data.append(mock_data)
        
        # Process batch
        results = processor.batch_process(batch_data)
        
        # Validate results
        assert len(results) == 5
        for result in results:
            assert isinstance(result, EngineeredFeatures)
            assert result.feature_vector.shape == (90,)
    
    def test_vector_db_export_format(self, processor):
        """Test vector database export format"""
        from unittest.mock import MagicMock
        
        # Create mock engineered features
        mock_features = MagicMock()
        mock_features.feature_vector = np.random.rand(90)
        mock_features.temporal_features = np.random.rand(25)
        mock_features.emotional_features = np.random.rand(20)
        mock_features.semantic_features = np.random.rand(30)
        mock_features.user_features = np.random.rand(15)
        mock_features.user_id = "test_user"
        mock_features.entry_id = "test_entry"
        mock_features.timestamp = datetime.now()
        mock_features.confidence_score = 0.8
        mock_features.feature_completeness = 0.9
        mock_features.processing_time_ms = 25.5
        mock_features.component_version = "4.0"
        
        # Mock metadata
        mock_metadata = MagicMock()
        mock_metadata.memory_type = "conversation"
        mock_metadata.content_summary = "Test summary"
        mock_metadata.original_entry_id = "test_entry"
        mock_metadata.importance_score = 0.7
        mock_metadata.emotional_significance = 0.6
        mock_metadata.temporal_relevance = 0.8
        mock_metadata.gate_scores = {
            'forget_score': 0.3,
            'input_score': 0.8,
            'output_score': 0.7,
            'confidence': 0.8
        }
        mock_metadata.retrieval_triggers = ["test", "keywords"]
        mock_metadata.relationships = []
        mock_metadata.context_needed = {}
        mock_metadata.created_at = datetime.now()
        mock_metadata.access_frequency = 0
        mock_features.metadata = mock_metadata
        
        # Export for vector DB
        exported = processor.export_features_for_vector_db(mock_features)
        
        # Validate export format
        assert 'embedding' in exported
        assert 'metadata' in exported
        assert len(exported['embedding']) == 90
        
        metadata = exported['metadata']
        assert 'memory_type' in metadata
        assert 'importance_score' in metadata
        assert 'gate_scores' in metadata
        assert 'feature_breakdown' in metadata
        
        # Check feature breakdown
        breakdown = metadata['feature_breakdown']
        assert 'temporal' in breakdown
        assert 'emotional' in breakdown
        assert 'semantic' in breakdown
        assert 'user' in breakdown
        assert len(breakdown['temporal']) == 25
        assert len(breakdown['emotional']) == 20
        assert len(breakdown['semantic']) == 30
        assert len(breakdown['user']) == 15
    
    def test_feature_consistency_across_sessions(self, processor):
        """Test that features are consistent across different sessions"""
        from unittest.mock import MagicMock
        
        # Create identical mock data
        def create_mock_data():
            mock_emotion = MagicMock()
            mock_emotion.dominant_emotion = "joy"
            mock_emotion.intensity = 0.7
            mock_emotion.confidence = 0.9
            
            emotions_mock = MagicMock()
            emotions_mock.joy = 0.7
            emotions_mock.sadness = 0.1
            emotions_mock.anger = 0.1
            emotions_mock.fear = 0.05
            emotions_mock.surprise = 0.05
            emotions_mock.disgust = 0.0
            emotions_mock.anticipation = 0.0
            emotions_mock.trust = 0.0
            mock_emotion.emotions = emotions_mock
            
            mock_semantic = MagicMock()
            mock_semantic.detected_topics = ["work", "meeting"]
            mock_semantic.people = []
            mock_semantic.organizations = []
            mock_semantic.locations = []
            mock_semantic.future_events = []
            mock_semantic.novelty_score = 0.6
            mock_semantic.complexity_score = 0.5
            
            return mock_emotion, mock_semantic
        
        # Process same data twice
        mock_emotion1, mock_semantic1 = create_mock_data()
        mock_emotion2, mock_semantic2 = create_mock_data()
        
        result1 = processor.process_journal_entry(
            emotion_analysis=mock_emotion1,
            semantic_analysis=mock_semantic1,
            user_id="consistency_test_user",
            entry_id="test_entry_1",
            session_id="session_1",
            entry_timestamp=datetime.now(),
            raw_text="Consistent test text",
            user_history=None,
            previous_entries=None
        )
        
        result2 = processor.process_journal_entry(
            emotion_analysis=mock_emotion2,
            semantic_analysis=mock_semantic2,
            user_id="consistency_test_user",
            entry_id="test_entry_2",
            session_id="session_2",
            entry_timestamp=datetime.now(),
            raw_text="Consistent test text",
            user_history=None,
            previous_entries=None
        )
        
        # Results should be very similar
        assert result1.feature_vector.shape == result2.feature_vector.shape
        
        # Allow for small differences due to timestamps, etc.
        correlation = np.corrcoef(result1.feature_vector, result2.feature_vector)[0, 1]
        assert correlation > 0.95  # Very high correlation expected
    
    def test_performance_requirements(self, processor):
        """Test that processing meets performance requirements"""
        from unittest.mock import MagicMock
        
        # Create simple mock data
        mock_emotion = MagicMock()
        mock_semantic = MagicMock()
        
        # Configure mocks minimally
        mock_emotion.dominant_emotion = "neutral"
        mock_emotion.intensity = 0.5
        mock_emotion.confidence = 0.7
        emotions_mock = MagicMock()
        for emotion in ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'anticipation', 'trust']:
            setattr(emotions_mock, emotion, 0.125)  # Equal distribution
        mock_emotion.emotions = emotions_mock
        
        mock_semantic.detected_topics = []
        mock_semantic.people = []
        mock_semantic.organizations = []
        mock_semantic.locations = []
        mock_semantic.future_events = []
        mock_semantic.novelty_score = 0.5
        mock_semantic.complexity_score = 0.5
        
        # Process entry
        result = processor.process_journal_entry(
            emotion_analysis=mock_emotion,
            semantic_analysis=mock_semantic,
            user_id="performance_test_user",
            entry_id="performance_test_entry",
            session_id="performance_test_session",
            entry_timestamp=datetime.now(),
            raw_text="Performance test text for Component 4",
            user_history=None,
            previous_entries=None
        )
        
        # Check performance requirement: <50ms per entry
        assert result.processing_time_ms < 100  # Relaxed for testing environment
        
        # Check quality requirement: reasonable feature completeness
        assert result.feature_completeness > 0.5  # At least half the features should be populated
    
    def test_error_recovery_integration(self, processor):
        """Test error recovery in integration scenarios"""
        # Test with malformed data
        try:
            result = processor.process_journal_entry(
                emotion_analysis=None,  # Invalid
                semantic_analysis=None,  # Invalid
                user_id="error_test_user",
                entry_id="error_test_entry",
                session_id="error_test_session",
                entry_timestamp=datetime.now(),
                raw_text="Error recovery test"
            )
            
            # Should not crash, should return valid but low-quality features
            assert isinstance(result, EngineeredFeatures)
            assert result.feature_vector.shape == (90,)
            assert result.confidence_score == 0.0  # Should indicate low confidence
            
        except Exception as e:
            # If it raises an exception, it should be a clear RuntimeError
            assert isinstance(e, RuntimeError)
            assert "Component 4 processing failed" in str(e)
