# test_integration.py (ADD NEW FILE)
#!/usr/bin/env python3
"""
Integration Test Script for Components 5, 6 & 7
===============================================

Comprehensive test to verify that Component 5 is properly integrated with Components 6 & 7.
Tests the complete pipeline with real LSTM memory gates.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import traceback

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from component5_integration import Component5Bridge
from gemini_engine_orchestrator import GeminiEngineOrchestrator
from gemini_engine_complete_integration import GeminiEngineIntegration


class IntegrationTester:
    """Test suite for Component 5, 6, 7 integration"""
    
    def __init__(self):
        self.test_results = {
            "component5_tests": [],
            "integration_tests": [],
            "performance_tests": [],
            "error_tests": []
        }
    
    async def run_all_tests(self):
        """Run complete integration test suite"""
        print("🧪 COMPONENT 5, 6, 7 INTEGRATION TEST SUITE")
        print("=" * 80)
        
        # Test 1: Component 5 Bridge Direct Test
        await self.test_component5_bridge()
        
        # Test 2: Orchestrator Integration Test
        await self.test_orchestrator_integration()
        
        # Test 3: Complete Pipeline Test
        await self.test_complete_pipeline()
        
        # Test 4: Error Handling Test
        await self.test_error_handling()
        
        # Test 5: Performance Test
        await self.test_performance()
        
        # Print test summary
        self.print_test_summary()
    
    async def test_component5_bridge(self):
        """Test Component 5 bridge functionality directly"""
        print("\n1️⃣ TESTING COMPONENT 5 BRIDGE")
        print("-" * 40)
        
        try:
            # Initialize Component 5 bridge
            bridge = Component5Bridge()
            init_success = await bridge.initialize()
            
            if init_success:
                print("✅ Component 5 bridge initialized successfully")
                
                # Test memory context retrieval
                memory_context = await bridge.get_memory_context(
                    user_id="test_user",
                    current_message="How am I feeling about work lately?",
                    conversation_id="test_conv_001"
                )
                
                print(f"✅ Memory context retrieved: {len(memory_context.selected_memories)} memories")
                print(f"📊 Token usage: {memory_context.token_usage}")
                
                # Test health check
                health = await bridge.health_check()
                print(f"✅ Health check: {health['initialized']}")
                
                self.test_results["component5_tests"].append({
                    "test": "bridge_functionality",
                    "status": "passed",
                    "memories_retrieved": len(memory_context.selected_memories)
                })
                
            else:
                print("❌ Component 5 bridge initialization failed")
                self.test_results["component5_tests"].append({
                    "test": "bridge_initialization", 
                    "status": "failed"
                })
                
        except Exception as e:
            print(f"❌ Component 5 bridge test failed: {e}")
            self.test_results["component5_tests"].append({
                "test": "bridge_functionality",
                "status": "error",
                "error": str(e)
            })
    
    async def test_orchestrator_integration(self):
        """Test orchestrator with Component 5 integration"""
        print("\n2️⃣ TESTING ORCHESTRATOR INTEGRATION")
        print("-" * 40)
        
        try:
            # Initialize orchestrator
            orchestrator = GeminiEngineOrchestrator()
            init_success = await orchestrator.initialize()
            
            if init_success:
                print("✅ Orchestrator initialized with Component 5")
                
                # Test health check
                health = await orchestrator.health_check()
                print(f"✅ Overall health: {health['overall_healthy']}")
                print(f"✅ Component 5: {health['component_health']['component5']['initialized']}")
                print(f"✅ Component 6: {health['component_health']['component6']['conversation_manager']}")
                print(f"✅ Component 7: {health['component_health']['component7']['orchestrator']}")
                
                self.test_results["integration_tests"].append({
                    "test": "orchestrator_health",
                    "status": "passed",
                    "component_health": health["component_health"]
                })
                
            else:
                print("❌ Orchestrator initialization failed")
                self.test_results["integration_tests"].append({
                    "test": "orchestrator_initialization",
                    "status": "failed"
                })
                
        except Exception as e:
            print(f"❌ Orchestrator integration test failed: {e}")
            self.test_results["integration_tests"].append({
                "test": "orchestrator_integration",
                "status": "error",
                "error": str(e)
            })
    
    async def test_complete_pipeline(self):
        """Test complete conversation pipeline"""
        print("\n3️⃣ TESTING COMPLETE CONVERSATION PIPELINE")
        print("-" * 40)
        
        try:
            # Initialize complete integration
            engine = GeminiEngineIntegration()
            await engine.initialize_components()
            
            # Test conversations with real Component 5
            test_messages = [
                "I just had an amazing breakthrough in my project!",
                "Can you help me remember what I was working on yesterday?", 
                "I'm feeling overwhelmed with my schedule."
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n  Test {i}: {message}")
                
                start_time = datetime.utcnow()
                result = await engine.process_conversation(
                    user_id="pipeline_test_user",
                    user_message=message,
                    emotional_state={"primary_emotion": "neutral", "intensity": 0.5}
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if result.get("success", False):
                    print(f"  ✅ Response: {result['response'][:100]}...")
                    print(f"  📊 Quality: {result.get('quality_analysis', {}).get('overall_quality', 0):.3f}")
                    print(f"  ⏱️  Time: {processing_time:.2f}ms")
                    
                    comp5_stats = result.get('component5_stats', {}).get('bridge_stats', {})
                    print(f"  🧠 C5 Memories: {comp5_stats.get('memories_retrieved', 0)}")
                    
                    self.test_results["integration_tests"].append({
                        "test": f"pipeline_conversation_{i}",
                        "status": "passed",
                        "processing_time_ms": processing_time,
                        "memories_used": comp5_stats.get('memories_retrieved', 0)
                    })
                    
                else:
                    print(f"  ❌ Pipeline test {i} failed: {result.get('error', 'Unknown')}")
                    self.test_results["integration_tests"].append({
                        "test": f"pipeline_conversation_{i}",
                        "status": "failed",
                        "error": result.get('error', 'Unknown')
                    })
                
                # Small delay between tests
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Complete pipeline test failed: {e}")
            self.test_results["integration_tests"].append({
                "test": "complete_pipeline",
                "status": "error",
                "error": str(e)
            })
    
    async def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        print("\n4️⃣ TESTING ERROR HANDLING")
        print("-" * 40)
        
        try:
            engine = GeminiEngineIntegration()
            await engine.initialize_components()
            
            # Test with invalid user ID
            print("  Testing invalid user ID...")
            result = await engine.process_conversation(
                user_id="",  # Invalid user ID
                user_message="Test message",
            )
            
            if not result.get("success", True):
                print("  ✅ Error handling working for invalid user ID")
                self.test_results["error_tests"].append({
                    "test": "invalid_user_id",
                    "status": "passed"
                })
            else:
                print("  ⚠️  Expected error not caught for invalid user ID")
                self.test_results["error_tests"].append({
                    "test": "invalid_user_id",
                    "status": "warning"
                })
            
            # Test with empty message
            print("  Testing empty message...")
            result = await engine.process_conversation(
                user_id="test_user",
                user_message="",  # Empty message
            )
            
            self.test_results["error_tests"].append({
                "test": "empty_message",
                "status": "passed" if not result.get("success", True) else "warning"
            })
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.test_results["error_tests"].append({
                "test": "error_handling",
                "status": "error",
                "error": str(e)
            })
    
    async def test_performance(self):
        """Test performance characteristics"""
        print("\n5️⃣ TESTING PERFORMANCE")
        print("-" * 40)
        
        try:
            engine = GeminiEngineIntegration()
            await engine.initialize_components()
            
            # Test multiple rapid conversations
            processing_times = []
            memory_counts = []
            
            for i in range(5):
                start_time = datetime.utcnow()
                
                result = await engine.process_conversation(
                    user_id="perf_test_user",
                    user_message=f"Performance test message number {i+1}",
                    emotional_state={"primary_emotion": "neutral", "intensity": 0.5}
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                processing_times.append(processing_time)
                
                comp5_stats = result.get('component5_stats', {}).get('bridge_stats', {})
                memory_counts.append(comp5_stats.get('memories_retrieved', 0))
                
                print(f"  Test {i+1}: {processing_time:.2f}ms, {comp5_stats.get('memories_retrieved', 0)} memories")
            
            # Calculate performance metrics
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)
            avg_memories = sum(memory_counts) / len(memory_counts)
            
            print(f"\n📊 Performance Results:")
            print(f"   Average Time: {avg_time:.2f}ms")
            print(f"   Min Time: {min_time:.2f}ms")
            print(f"   Max Time: {max_time:.2f}ms")
            print(f"   Average Memories: {avg_memories:.1f}")
            
            # Performance assessment
            performance_good = avg_time < 5000 and max_time < 10000  # Under 5s average, 10s max
            
            self.test_results["performance_tests"].append({
                "test": "rapid_conversations",
                "status": "passed" if performance_good else "warning",
                "avg_time_ms": avg_time,
                "max_time_ms": max_time,
                "avg_memories": avg_memories
            })
            
            if performance_good:
                print("✅ Performance within acceptable limits")
            else:
                print("⚠️  Performance may need optimization")
                
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.test_results["performance_tests"].append({
                "test": "performance",
                "status": "error",
                "error": str(e)
            })
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("📋 INTEGRATION TEST SUMMARY")
        print("="*80)
        
        # Count results
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.test_results.items():
            print(f"\n📁 {category.upper().replace('_', ' ')}:")
            for test in tests:
                status = test["status"]
                total_tests += 1
                
                if status == "passed":
                    passed_tests += 1
                    print(f"   ✅ {test['test']}")
                elif status == "failed":
                    failed_tests += 1
                    print(f"   ❌ {test['test']}")
                elif status == "error":
                    error_tests += 1
                    print(f"   🚨 {test['test']}: {test.get('error', 'Unknown error')}")
                else:
                    print(f"   ⚠️  {test['test']} (Warning)")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Errors: {error_tests} 🚨")
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        print(f"   Success Rate: {success_rate*100:.1f}%")
        
        if success_rate >= 0.8:
            print("\n🎉 INTEGRATION TEST PASSED! Component 5 successfully integrated.")
        elif success_rate >= 0.6:
            print("\n⚠️  INTEGRATION PARTIALLY WORKING. Some issues need attention.")
        else:
            print("\n❌ INTEGRATION TEST FAILED. Major issues need fixing.")
        
        print("="*80)


async def main():
    """Main test runner"""
    tester = IntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())