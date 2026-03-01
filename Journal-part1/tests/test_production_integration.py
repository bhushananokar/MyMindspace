#!/usr/bin/env python3
"""
Production Integration Tests for Components 2+3+4
Tests the complete pipeline without fallbacks
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import production components
try:
    from production_integration import ProductionIntegrator
    from comp4.src.production_processor import ProductionComponent4Processor
    from production_comp234_integration import ProductionPipeline
    PRODUCTION_AVAILABLE = True
except ImportError as e:
    PRODUCTION_AVAILABLE = False
    pytest.skip(f"Production components not available: {e}", allow_module_level=True)

class TestProductionIntegration:
    """Test suite for production integration"""
    
    @pytest.fixture(scope="class")
    def production_pipeline(self):
        """Create production pipeline for testing"""
        if not PRODUCTION_AVAILABLE:
            pytest.skip("Production components not available")
        return ProductionPipeline()
    
    def test_pipeline_initialization(self, production_pipeline):
        """Test that production pipeline initializes correctly"""
        assert production_pipeline is not None
        assert hasattr(production_pipeline, 'c23_integrator')
        assert hasattr(production_pipeline, 'c4_processor')
        assert production_pipeline.c23_integrator.version == "production_v1.0"
        assert production_pipeline.c4_processor.version == "4.0-PRODUCTION"
    
    def test_single_entry_processing(self, production_pipeline):
        """Test processing a single journal entry"""
        test_text = "Had a great day at work today. My presentation went well and the team was very supportive. Feeling proud and excited about the upcoming project."
        user_id = "test_user_001"
        
        result = production_pipeline.process_journal_entry(
            text=test_text,
            user_id=user_id
        )
        
        # Validate structure
        assert 'c23_output' in result
        assert 'c4_output' in result
        assert 'vector_db_export' in result
        assert 'pipeline_metadata' in result
        
        # Validate C2+3 output
        c23_output = result['c23_output']
        assert 'emotion_analysis' in c23_output
        assert 'semantic_analysis' in c23_output
        assert c23_output['user_id'] == user_id
        
        # Validate C4 output
        c4_output = result['c4_output']
        assert len(c4_output['feature_vector']) == 90
        assert len(c4_output['temporal_features']) == 25
        assert len(c4_output['emotional_features']) == 20
        assert len(c4_output['semantic_features']) == 30
        assert len(c4_output['user_features']) == 15
        
        # Validate vector DB export
        vector_export = result['vector_db_export']
        assert 'embedding' in vector_export
        assert 'metadata' in vector_export
        assert len(vector_export['embedding']) == 90
        
        # Validate metadata
        metadata = vector_export['metadata']
        assert 'memory_type' in metadata
        assert 'importance_score' in metadata
        assert 'gate_scores' in metadata
        assert 'retrieval_triggers' in metadata
        assert metadata['production_mode'] is True
        assert metadata['no_fallbacks'] is True
    
    def test_feature_vector_properties(self, production_pipeline):
        """Test that feature vectors have correct properties"""
        test_text = "Struggling with anxiety about the deadline. Need to talk to my manager about extending the timeline."
        
        result = production_pipeline.process_journal_entry(
            text=test_text,
            user_id="test_user_002"
        )
        
        feature_vector = np.array(result['c4_output']['feature_vector'])
        
        # Test dimensions
        assert feature_vector.shape == (90,)
        
        # Test value ranges (should be normalized to [0,1] or finite)
        assert np.all(np.isfinite(feature_vector))
        assert np.all(feature_vector >= 0.0)
        assert np.all(feature_vector <= 1.0)
        
        # Test that vectors are not all zeros or all ones
        assert not np.all(feature_vector == 0.0)
        assert not np.all(feature_vector == 1.0)
    
    def test_gate_scores_validity(self, production_pipeline):
        """Test that LSTM gate scores are valid"""
        test_text = "Excited about the new AI project we're starting. Sarah will be my co-lead which gives me confidence."
        
        result = production_pipeline.process_journal_entry(
            text=test_text,
            user_id="test_user_003"
        )
        
        gate_scores = result['vector_db_export']['metadata']['gate_scores']
        
        # Test all gate scores are present
        required_gates = ['forget_score', 'input_score', 'output_score', 'confidence']
        for gate in required_gates:
            assert gate in gate_scores
            score = gate_scores[gate]
            assert isinstance(score, (int, float))
            assert 0.0 <= score <= 1.0
    
    def test_different_emotional_content(self, production_pipeline):
        """Test processing entries with different emotional content"""
        test_cases = [
            {
                'text': "Amazing breakthrough at work! So proud of our team's accomplishment.",
                'expected_emotion_type': 'joy',
                'user_id': 'test_joy_001'
            },
            {
                'text': "Feeling overwhelmed by all the deadlines and pressure from management.",
                'expected_emotion_type': 'stress',
                'user_id': 'test_stress_001'
            },
            {
                'text': "Had dinner with family tonight. My brother surprised us by visiting from Seattle.",
                'expected_emotion_type': 'neutral',
                'user_id': 'test_family_001'
            }
        ]
        
        for case in test_cases:
            result = production_pipeline.process_journal_entry(
                text=case['text'],
                user_id=case['user_id']
            )
            
            # Validate processing succeeded
            assert result is not None
            assert 'c4_output' in result
            
            # Validate different emotional signatures
            emotional_features = result['c4_output']['emotional_features']
            assert len(emotional_features) == 20
            assert not np.all(np.array(emotional_features) == 0.5)  # Should have emotional variation
    
    def test_semantic_content_extraction(self, production_pipeline):
        """Test semantic content extraction and feature generation"""
        test_text = "Meeting with John from Microsoft about the AI partnership. We discussed the timeline for the Seattle office project."
        
        result = production_pipeline.process_journal_entry(
            text=test_text,
            user_id="test_semantic_001"
        )
        
        # Check semantic analysis
        semantic_analysis = result['c23_output']['semantic_analysis']
        assert 'people' in semantic_analysis
        assert 'organizations' in semantic_analysis
        assert 'detected_topics' in semantic_analysis
        
        # Check that entities were detected
        people = semantic_analysis['people']
        orgs = semantic_analysis['organizations']
        
        # Should detect John and Microsoft
        assert len(people) > 0 or len(orgs) > 0  # At least some entities
        
        # Check semantic features in C4 output
        semantic_features = result['c4_output']['semantic_features']
        assert len(semantic_features) == 30
    
    def test_error_handling_strict_mode(self, production_pipeline):
        """Test that strict mode handles errors properly"""
        # Test empty text
        with pytest.raises(ValueError, match="Journal entry text cannot be empty"):
            production_pipeline.process_journal_entry(
                text="",
                user_id="test_error_001"
            )
        
        # Test missing user ID
        with pytest.raises(ValueError, match="User ID is required"):
            production_pipeline.process_journal_entry(
                text="Valid text here",
                user_id=""
            )
    
    def test_performance_benchmarks(self, production_pipeline):
        """Test that processing meets performance requirements"""
        test_text = "Regular journal entry for performance testing. Contains some emotional content about work and relationships."
        
        start_time = datetime.now()
        
        result = production_pipeline.process_journal_entry(
            text=test_text,
            user_id="test_performance_001"
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000  # Convert to ms
        
        # Should process in under 1000ms (generous for integration test)
        assert processing_time < 1000, f"Processing took {processing_time}ms, expected <1000ms"
        
        # Check reported processing time
        reported_time = result['pipeline_metadata']['total_processing_time_ms']
        assert reported_time > 0
        assert reported_time < 1000
    
    def test_batch_processing(self, production_pipeline):
        """Test batch processing functionality"""
        test_entries = [
            {'text': 'First entry about work success', 'user_id': 'batch_user_001'},
            {'text': 'Second entry about family time', 'user_id': 'batch_user_001'},
            {'text': 'Third entry about personal growth', 'user_id': 'batch_user_001'}
        ]
        
        results = production_pipeline.batch_process(test_entries)
        
        assert len(results) == 3
        
        for i, result in enumerate(results):
            assert 'c4_output' in result
            assert len(result['c4_output']['feature_vector']) == 90
            assert result['c23_output']['user_id'] == 'batch_user_001'
    
    def test_vector_database_compatibility(self, production_pipeline):
        """Test vector database export format compatibility"""
        test_text = "Test entry for vector database compatibility validation."
        
        result = production_pipeline.process_journal_entry(
            text=test_text,
            user_id="test_vectordb_001"
        )
        
        vector_export = result['vector_db_export']
        
        # Validate vector DB format
        assert 'embedding' in vector_export
        assert 'metadata' in vector_export
        
        # Validate embedding
        embedding = vector_export['embedding']
        assert isinstance(embedding, list)
        assert len(embedding) == 90
        assert all(isinstance(x, (int, float)) for x in embedding)
        
        # Validate metadata structure
        metadata = vector_export['metadata']
        required_fields = [
            'memory_type', 'importance_score', 'emotional_significance',
            'temporal_relevance', 'gate_scores', 'retrieval_triggers',
            'user_id', 'entry_timestamp', 'feature_breakdown'
        ]
        
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"
        
        # Validate feature breakdown
        feature_breakdown = metadata['feature_breakdown']
        assert len(feature_breakdown['temporal']) == 25
        assert len(feature_breakdown['emotional']) == 20
        assert len(feature_breakdown['semantic']) == 30
        assert len(feature_breakdown['user']) == 15

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
