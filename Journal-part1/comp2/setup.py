#!/usr/bin/env python3
"""
Quick test to verify Component 2 is working
"""

import sys
sys.path.insert(0, '.')

try:
    # Test imports
    print("Testing imports...")
    from comp2.data.schemas import EmotionAnalysis, EmotionScores
    from comp2.utils.config import ComponentConfig
    print("✅ Data schemas imported")
    
    from comp2.models.emotion_models import PolicyNetwork, SACAgent
    print("✅ Models imported")
    
    from comp2.utils.logging_utils import setup_logging, LoggingConfig
    from comp2.utils.metrics import MetricsCollector
    print("✅ Utils imported")
    
    # Test basic functionality
    print("\nTesting basic functionality...")
    
    # Test emotion scores
    emotions = EmotionScores(joy=0.8, sadness=0.2, trust=0.7)
    print(f"✅ EmotionScores created: dominant = {emotions.dominant_emotion()}")
    
    # Test configuration
    config = ComponentConfig()
    print(f"✅ Config created: device = {config.get_device()}")
    
    # Test policy network
    import torch
    policy = PolicyNetwork(state_dim=100, action_dim=9)
    test_state = torch.randn(1, 100)
    mean, log_std = policy.forward(test_state)
    print(f"✅ PolicyNetwork working: output shape = {mean.shape}")
    
    # Test metrics collector
    metrics = MetricsCollector()
    metrics.record_timing("test_operation", 150.5)
    stats = metrics.get_timing_stats("test_operation")
    print(f"✅ Metrics working: recorded timing = {stats['test_operation']['recent_avg_ms']:.1f}ms")
    
    print("\n🎉 All tests passed! Component 2 is ready to use.")
    print("\nNext steps:")
    print("1. Run: python quick_test.py")
    print("2. Create your own emotion analyzer")
    print("3. Start integrating with your journal platform!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTroubleshooting steps:")
    print("1. Make sure you're in the component2_rl_emotion directory")
    print("2. Install dependencies: pip install torch transformers numpy scipy pydantic PyYAML psutil pytest spacy python-dateutil")
    print("3. Download spaCy model: python -m spacy download en_core_web_lg")
    print("4. Set PYTHONPATH: $env:PYTHONPATH = \"$env:PYTHONPATH;$PWD\"")
    sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)