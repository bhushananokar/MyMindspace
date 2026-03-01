"""
Pytest configuration and shared fixtures for Components 2, 3, and 4 tests
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_journal_entries():
    """Sample journal entries for testing"""
    return [
        {
            'text': "Had an incredible breakthrough at work today! My presentation to the board went exceptionally well, and they approved our new AI initiative. I'm feeling so proud and excited about leading this project.",
            'user_id': 'test_user_001',
            'expected_emotion': 'joy',
            'expected_entities': ['board', 'AI'],
            'entry_id': 'breakthrough_001'
        },
        {
            'text': "Struggling with anxiety about the upcoming project deadline. The client expectations are really high and I'm worried we won't deliver on time. Need to have a difficult conversation with my manager tomorrow.",
            'user_id': 'test_user_002', 
            'expected_emotion': 'anxiety',
            'expected_entities': ['client', 'manager'],
            'entry_id': 'anxiety_001'
        },
        {
            'text': "Wonderful family dinner tonight to celebrate Dad's birthday. We went to his favorite Italian restaurant and shared so many laughs and memories. My brother surprised us all by flying in from Seattle.",
            'user_id': 'test_user_003',
            'expected_emotion': 'joy',
            'expected_entities': ['Dad', 'brother', 'Seattle'],
            'entry_id': 'family_001'
        },
        {
            'text': "Reflecting on my personal growth this year. I've learned to be more patient with myself and others. The meditation practice has really helped me find inner peace and clarity.",
            'user_id': 'test_user_004',
            'expected_emotion': 'neutral',
            'expected_entities': [],
            'entry_id': 'growth_001'
        }
    ]

@pytest.fixture
def mock_user_history():
    """Mock user history for testing"""
    return {
        'total_entries': 10,
        'avg_emotions': {
            'joy': 0.6,
            'sadness': 0.2,
            'anger': 0.1,
            'fear': 0.1
        },
        'writing_patterns': {
            'avg_length': 150,
            'complexity_score': 0.6
        },
        'common_topics': ['work', 'family', 'personal'],
        'relationship_network': {
            'family': ['Dad', 'brother'],
            'work': ['manager', 'client', 'board']
        }
    }

@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing"""
    return {
        'component_2_max_ms': 100,
        'component_3_max_ms': 200, 
        'component_4_max_ms': 50,
        'full_pipeline_max_ms': 500,
        'memory_usage_max_mb': 200
    }

@pytest.fixture
def quality_thresholds():
    """Quality thresholds for testing"""
    return {
        'min_confidence_score': 0.7,
        'min_feature_completeness': 0.8,
        'min_quality_score': 0.8,
        'max_error_rate': 0.05
    }

@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset any global state before each test"""
    # Clear any cached models or state
    yield
    # Cleanup after test if needed
