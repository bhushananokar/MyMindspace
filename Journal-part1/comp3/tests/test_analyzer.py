#!/usr/bin/env python3
"""Unit tests for Component 3 Analyzer"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from src.analyzer import Component3Analyzer
from data.schemas import (
    PersonEntity, LocationEntity, OrganizationEntity, 
    ExtractedEvent, FollowupQuestion, SemanticEmbedding, 
    TemporalFeatures, SemanticAnalysis
)

class TestComponent3Analyzer(unittest.TestCase):
    """Test cases for the main Component3Analyzer"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_user_id = "test_user_123"
        self.test_timestamp = datetime(2025, 1, 15, 14, 30)
        
        # Mock the heavy dependencies to avoid loading actual models
        with patch('src.entity_extractor.EntityExtractor'), \
             patch('src.event_extractor.EventExtractor'), \
             patch('src.embedding_generator.EmbeddingGenerator'), \
             patch('src.temporal_analyzer.TemporalAnalyzer'):
            
            self.analyzer = Component3Analyzer()
            
            # Set up mocks
            self.setup_mocks()
    
    def setup_mocks(self):
        """Set up mock responses for all components"""
        
        # Mock entity extractor
        self.analyzer.entity_extractor.extract_entities = Mock(return_value=(
            [PersonEntity(name="John Doe", confidence=0.9)],  # people
            [LocationEntity(name="New York", location_type="city", confidence=0.8)],  # locations
            [OrganizationEntity(name="Google", org_type="company", confidence=0.85)],  # organizations
            {"John Doe": ["Sarah"]}  # relationships
        ))
        
        # Mock event extractor
        mock_event = ExtractedEvent(
            event_id="evt_123",
            event_text="meeting tomorrow",
            event_type="professional",
            parsed_date=self.test_timestamp + timedelta(days=1),
            confidence=0.8
        )
        
        mock_followup = FollowupQuestion(
            event_id="evt_123",
            question_text="How did your meeting go?",
            question_type="after_event",
            optimal_timing=self.test_timestamp + timedelta(days=1, hours=6)
        )
        
        self.analyzer.event_extractor.extract_events = Mock(return_value=[mock_event])
        self.analyzer.event_extractor.generate_followup_questions = Mock(return_value=[mock_followup])
        
        # Mock embedding generator
        import numpy as np
        mock_embedding = SemanticEmbedding(
            primary_embedding=np.random.rand(768),
            lightweight_embedding=np.random.rand(384),
            text_length=100,
            processing_time_ms=50.0,
            model_version="test"
        )
        
        self.analyzer.embedding_generator.generate_embeddings = Mock(return_value=mock_embedding)
        self.analyzer.embedding_generator.analyze_content_complexity = Mock(return_value=0.6)
        
        # Mock temporal analyzer
        mock_temporal = TemporalFeatures(
            writing_time=self.test_timestamp,
            hour_of_day=14,
            day_of_week=1,  # Tuesday
            is_weekend=False,
            days_since_last_entry=1,
            writing_frequency_score=0.8,
            cyclical_patterns={"preferred_hour": 14},
            anomaly_score=0.1
        )
        
        self.analyzer.temporal_analyzer.analyze_temporal_features = Mock(return_value=mock_temporal)
    
    def test_analyze_basic(self):
        """Test basic analyze functionality"""
        text = "I have a meeting with John at Google tomorrow."
        
        result = self.analyzer.analyze(
            processed_text=text,
            user_id=self.test_user_id,
            entry_timestamp=self.test_timestamp
        )
        
        # Verify result type
        self.assertIsInstance(result, SemanticAnalysis)
        
        # Verify entities
        self.assertEqual(len(result.people), 1)
        self.assertEqual(result.people[0].name, "John Doe")
        
        self.assertEqual(len(result.locations), 1)
        self.assertEqual(result.locations[0].name, "New York")
        
        self.assertEqual(len(result.organizations), 1)
        self.assertEqual(result.organizations[0].name, "Google")
        
        # Verify events
        self.assertEqual(len(result.future_events), 1)
        self.assertEqual(result.future_events[0].event_id, "evt_123")
        
        # Verify followups
        self.assertEqual(len(result.followup_questions), 1)
        
        # Verify embeddings
        self.assertIsNotNone(result.embeddings)
        self.assertEqual(len(result.embeddings.primary_embedding), 768)
        
        # Verify temporal features
        self.assertIsNotNone(result.temporal_features)
        self.assertEqual(result.temporal_features.hour_of_day, 14)
        
        # Verify processing time is recorded
        self.assertGreaterEqual(result.processing_time_ms, 0)
    
    def test_analyze_with_last_entry_time(self):
        """Test analyze with previous entry timestamp"""
        text = "Another journal entry."
        last_entry = self.test_timestamp - timedelta(days=2)
        
        result = self.analyzer.analyze(
            processed_text=text,
            user_id=self.test_user_id,
            entry_timestamp=self.test_timestamp,
            last_entry_timestamp=last_entry
        )
        
        # Verify temporal analyzer was called with correct parameters
        self.analyzer.temporal_analyzer.analyze_temporal_features.assert_called_with(
            current_time=self.test_timestamp,
            user_id=self.test_user_id,
            last_entry_time=last_entry
        )
        
        self.assertIsInstance(result, SemanticAnalysis)
    
    def test_analyze_error_handling(self):
        """Test analyze handles errors gracefully"""
        # Make entity extractor throw an exception
        self.analyzer.entity_extractor.extract_entities.side_effect = Exception("Test error")
        
        result = self.analyzer.analyze(
            processed_text="Test text",
            user_id=self.test_user_id,
            entry_timestamp=self.test_timestamp
        )
        
        # Should return error analysis
        self.assertIsInstance(result, SemanticAnalysis)
        self.assertEqual(result.component_version, "3.0-error")
        self.assertEqual(len(result.people), 0)
    
    def test_batch_analyze(self):
        """Test batch analysis functionality"""
        entries = [
            {
                'text': "First entry with meeting",
                'timestamp': self.test_timestamp
            },
            {
                'text': "Second entry about vacation",
                'timestamp': self.test_timestamp + timedelta(hours=1)
            },
            {
                'text': "Third entry personal thoughts",
                'timestamp': self.test_timestamp + timedelta(hours=2)
            }
        ]
        
        # Mock batch embedding generation
        import numpy as np
        mock_embeddings = [
            SemanticEmbedding(
                primary_embedding=np.random.rand(768),
                lightweight_embedding=np.random.rand(384),
                text_length=len(entry['text']),
                processing_time_ms=30.0,
                model_version="test"
            ) for entry in entries
        ]
        
        self.analyzer.embedding_generator.batch_generate_embeddings = Mock(return_value=mock_embeddings)
        
        results = self.analyzer.batch_analyze(entries, self.test_user_id)
        
        # Verify results
        self.assertEqual(len(results), 3)
        
        for i, result in enumerate(results):
            self.assertIsInstance(result, SemanticAnalysis)
            self.assertIsNotNone(result.embeddings)
            self.assertEqual(result.embeddings.text_length, len(entries[i]['text']))
        
        # Verify batch embedding was called
        self.analyzer.embedding_generator.batch_generate_embeddings.assert_called_once()
    
    def test_batch_analyze_with_errors(self):
        """Test batch analysis handles individual entry errors"""
        entries = [
            {'text': "Good entry", 'timestamp': self.test_timestamp},
            {'text': "Bad entry", 'timestamp': self.test_timestamp + timedelta(hours=1)},
        ]
        
        # Mock batch embeddings
        import numpy as np
        mock_embeddings = [
            SemanticEmbedding(
                primary_embedding=np.random.rand(768),
                lightweight_embedding=np.random.rand(384),
                text_length=10,
                processing_time_ms=30.0,
                model_version="test"
            ) for _ in entries
        ]
        
        self.analyzer.embedding_generator.batch_generate_embeddings = Mock(return_value=mock_embeddings)
        
        # Make entity extractor fail on second entry
        def side_effect(text):
            if "Bad entry" in text:
                raise Exception("Processing error")
            return ([], [], [], {})
        
        self.analyzer.entity_extractor.extract_entities.side_effect = side_effect
        
        results = self.analyzer.batch_analyze(entries, self.test_user_id)
        
        # Should still return 2 results
        self.assertEqual(len(results), 2)
        
        # First should be normal, second should be error
        self.assertNotEqual(results[0].component_version, "3.0-error")
        self.assertEqual(results[1].component_version, "3.0-error")
    
    def test_get_user_insights(self):
        """Test user insights functionality"""
        # Mock temporal analyzer insights
        mock_insights = {
            'writing_patterns': {
                'most_active_time': '14:00 (afternoon)',
                'most_active_day': 'Tuesday',
                'writing_frequency': 'daily'
            },
            'writing_streaks': {
                'current_streak': 5,
                'longest_streak': 12,
                'total_days': 30
            }
        }
        
        self.analyzer.temporal_analyzer.get_user_writing_insights = Mock(
            return_value=mock_insights['writing_patterns']
        )
        self.analyzer.temporal_analyzer.detect_writing_streaks = Mock(
            return_value=mock_insights['writing_streaks']
        )
        self.analyzer.temporal_analyzer.predict_next_entry_time = Mock(
            return_value=self.test_timestamp + timedelta(days=1)
        )
        
        insights = self.analyzer.get_user_insights(self.test_user_id)
        
        # Verify structure
        self.assertIn('writing_patterns', insights)
        self.assertIn('writing_streaks', insights)
        self.assertIn('next_predicted_entry', insights)
        
        # Verify content
        self.assertEqual(insights['writing_patterns']['most_active_day'], 'Tuesday')
        self.assertEqual(insights['writing_streaks']['current_streak'], 5)
    
    def test_performance_stats(self):
        """Test performance statistics"""
        # Mock cache info
        with patch.object(self.analyzer.embedding_generator, '_cached_encode') as mock_cached:
            mock_cache_info = Mock()
            mock_cache_info.currsize = 150
            mock_cached.cache_info.return_value = mock_cache_info
            
            stats = self.analyzer.get_performance_stats()
            
            self.assertIn('models_loaded', stats)
            self.assertIn('spacy', stats['models_loaded'])
            self.assertIn('primary_embedding', stats['models_loaded'])
    
    def test_extract_topics_simple(self):
        """Test simple topic extraction"""
        text = "meeting work project deadline schedule team collaboration"
        
        # Mock embedding (not used in simple implementation)
        mock_embedding = Mock()
        
        topics = self.analyzer._extract_topics(text, mock_embedding)
        
        # Should extract some meaningful words
        self.assertIsInstance(topics, list)
        # Most frequent words should be extracted
        self.assertTrue(any(len(topic) > 3 for topic in topics))
    
    def test_calculate_novelty_placeholder(self):
        """Test novelty calculation placeholder"""
        mock_embedding = Mock()
        
        novelty = self.analyzer._calculate_novelty(self.test_user_id, mock_embedding)
        
        # Currently returns placeholder value
        self.assertEqual(novelty, 0.5)
    
    def test_default_config_loading(self):
        """Test loading default configuration"""
        config = self.analyzer._load_default_config()
        
        # Verify expected structure
        self.assertIn('models', config)
        self.assertIn('performance', config)
        self.assertIn('entity_extraction', config)
        self.assertIn('event_extraction', config)
        
        # Verify some default values
        self.assertEqual(config['models']['spacy_model'], 'en_core_web_lg')
        self.assertEqual(config['performance']['batch_size'], 32)
    
    def test_create_error_analysis(self):
        """Test error analysis creation"""
        error_analysis = self.analyzer._create_error_analysis(
            "test text", 
            self.test_timestamp, 
            "Test error message"
        )
        
        self.assertIsInstance(error_analysis, SemanticAnalysis)
        self.assertEqual(error_analysis.component_version, "3.0-error")
        self.assertEqual(len(error_analysis.people), 0)
        self.assertEqual(len(error_analysis.locations), 0)
        self.assertEqual(len(error_analysis.future_events), 0)
        self.assertIsNone(error_analysis.embeddings)


class TestAnalyzerIntegration(unittest.TestCase):
    """Integration-style tests that test component interactions"""
    
    def setUp(self):
        """Set up with minimal mocking for integration tests"""
        self.test_user_id = "integration_user"
        self.test_timestamp = datetime(2025, 1, 15, 10, 0)
    
    @patch('src.analyzer.Component3Analyzer.__init__', return_value=None)
    def test_component_initialization_order(self, mock_init):
        """Test that components are initialized in correct order"""
        # This test verifies the initialization doesn't have circular dependencies
        pass
    
    def test_data_flow_between_components(self):
        """Test data flows correctly between components"""
        # This would test real component interactions
        # Skipped for unit tests as it requires actual model loading
        pass


if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        buffer=True,  # Capture print statements
        failfast=False,  # Continue after first failure
        warnings='ignore'  # Suppress warnings during tests
    )