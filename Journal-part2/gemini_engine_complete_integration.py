# gemini_engine_complete_integration.py (REPLACE EXISTING)
#!/usr/bin/env python3
"""
Gemini Engine Complete Integration - Components 5, 6 & 7
========================================================

Complete integration of all three Gemini Engine components with real Component 5 LSTM:
- Component 5: LSTM-Inspired Memory Gates + RL Training (REAL IMPLEMENTATION)
- Component 6: Gemini Brain Integration  
- Component 7: Gemini Response Analysis

Architecture Flow:
Memory Gates (Comp 5) → Context Assembly (Comp 6) → Gemini API → Response Analysis (Comp 7)
     ↑                                                                        ↓
     ←←←←←←←←←←← Feedback Loop for Optimization ←←←←←←←←←←←←←←←←←←←←←←←←←
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import traceback

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeminiEngineIntegration:
    """Complete integration of all Gemini Engine components with real Component 5"""
    
    def __init__(self):
        """Initialize the complete Gemini Engine system"""
        self.logger = logging.getLogger("gemini_engine_integration")
        self.components_status = {}
        self.orchestrator = None
        
        # Performance metrics
        self.conversation_history = []
        self.performance_metrics = {
            "total_conversations": 0,
            "avg_response_time_ms": 0.0,
            "success_rate": 0.0,
            "quality_scores": [],
            "satisfaction_scores": [],
            "component5_lstm_health": False,
            "integration_errors": 0
        }
    
    async def initialize_components(self):
        """Initialize all Gemini Engine components with real Component 5"""
        self.logger.info("🚀 Initializing Gemini Engine with Real Component 5...")
        
        # Initialize the main orchestrator (includes Component 5, 6, 7)
        await self._initialize_orchestrator()
        
        # Verify system health
        await self._verify_system_health()
        
        self.logger.info("✅ Gemini Engine initialization complete!")
    
    async def _initialize_orchestrator(self):
        """Initialize main orchestrator with real Component 5"""
        try:
            from gemini_engine_orchestrator import GeminiEngineOrchestrator
            
            # Initialize orchestrator with real Component 5 bridge
            self.orchestrator = GeminiEngineOrchestrator()
            
            # Initialize the orchestrator (this will initialize Component 5 bridge)
            orchestrator_success = await self.orchestrator.initialize()
            
            if not orchestrator_success:
                raise RuntimeError("Orchestrator initialization failed")
            
            # Verify health
            health_status = await self.orchestrator.health_check()
            
            self.components_status = {
                "component5": {
                    "status": "initialized" if health_status["component_health"]["component5"]["initialized"] else "failed",
                    "type": "real_lstm_gates",
                    "memory_manager": health_status["component_health"]["component5"]["memory_manager_healthy"],
                    "gate_network": health_status["component_health"]["component5"]["gate_network_healthy"],
                    "database": health_status["component_health"]["component5"]["database_connection"]
                },
                "component6": {
                    "status": "initialized" if health_status["component_health"]["component6"]["conversation_manager"] else "failed",
                    "modules": health_status["component_health"]["component6"]
                },
                "component7": {
                    "status": "initialized" if health_status["component_health"]["component7"]["orchestrator"] else "failed",
                    "response_analysis": health_status["component_health"]["component7"]["response_analysis"]
                },
                "orchestrator": {
                    "status": "initialized",
                    "overall_healthy": health_status["overall_healthy"]
                }
            }
            
            self.performance_metrics["component5_lstm_health"] = health_status["component_health"]["component5"]["initialized"]
            
            self.logger.info("✅ Orchestrator with real Component 5 initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Orchestrator initialization failed: {e}")
            self.performance_metrics["integration_errors"] += 1
            self.components_status["orchestrator"] = {"status": "failed", "error": str(e)}
    
    async def _verify_system_health(self):
        """Verify overall system health"""
        try:
            if self.orchestrator:
                health_check = await self.orchestrator.health_check()
                self.components_status["system_health"] = health_check
                self.logger.info("✅ System health verification complete")
                
                # Log detailed health status
                for component, status in health_check["component_health"].items():
                    self.logger.info(f"Component {component}: {'✅ Healthy' if status else '❌ Unhealthy'}")
                    
            else:
                self.logger.warning("⚠️ Cannot verify system health - orchestrator not initialized")
                
        except Exception as e:
            self.logger.error(f"❌ System health verification failed: {e}")
            self.performance_metrics["integration_errors"] += 1
    
    async def process_conversation(
        self,
        user_id: str,
        user_message: str,
        conversation_id: Optional[str] = None,
        emotional_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a complete conversation through all components with real Component 5"""
        
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized. Call initialize_components() first.")
        
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Processing conversation with real Component 5 LSTM")
            self.logger.info(f"User: {user_message}")
            
            # Process through orchestrator (Component 5 → 6 → 7)
            enhanced_response = await self.orchestrator.process_conversation(
                user_id=user_id,
                user_message=user_message,
                conversation_id=conversation_id,
                emotional_state=emotional_state
            )
            
            # Extract results
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            conversation_result = {
                "conversation_id": conversation_id or enhanced_response.conversation_id,
                "response": enhanced_response.enhanced_response,
                "processing_time_ms": processing_time,
                "quality_analysis": enhanced_response.response_analysis.__dict__ if enhanced_response.response_analysis else {},
                "memory_context_used": enhanced_response.memory_context_metadata,
                "component5_stats": self.orchestrator.component5_bridge.get_statistics(),
                "success": True
            }
            
            # Update performance metrics
            self.performance_metrics["total_conversations"] += 1
            self.performance_metrics["quality_scores"].append(
                enhanced_response.response_analysis.overall_quality if enhanced_response.response_analysis else 0.5
            )
            
            # Update conversation history
            self.conversation_history.append({
                "timestamp": datetime.utcnow(),
                "user_id": user_id,
                "user_message": user_message,
                "ai_response": enhanced_response.enhanced_response,
                "processing_time_ms": processing_time,
                "memories_used": len(enhanced_response.memory_context_metadata.get("selected_memories", []))
            })
            
            self.logger.info(f"✅ Conversation processed successfully")
            self.logger.info(f"Response: {enhanced_response.enhanced_response}")
            
            return conversation_result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.performance_metrics["integration_errors"] += 1
            
            error_result = {
                "error": str(e),
                "processing_time_ms": processing_time,
                "component5_stats": self.orchestrator.component5_bridge.get_statistics() if self.orchestrator else {},
                "success": False
            }
            
            self.logger.error(f"❌ Conversation processing failed: {e}")
            return error_result
    
    async def demonstrate_proactive_engagement(self, user_id: str) -> Dict[str, Any]:
        """Demonstrate proactive engagement using real Component 5"""
        try:
            self.logger.info(f"Demonstrating proactive engagement for user {user_id}")
            
            proactive_result = await self.orchestrator.process_proactive_engagement(
                user_id=user_id,
                context={"trigger": "demonstration"}
            )
            
            return proactive_result or {"message": "No proactive message generated"}
            
        except Exception as e:
            self.logger.error(f"Proactive engagement demo failed: {e}")
            return {"error": str(e)}
    
    def print_status_report(self):
        """Print detailed status report"""
        print("\n" + "="*80)
        print("🏗️  GEMINI ENGINE INTEGRATION STATUS REPORT")
        print("="*80)
        
        # Component status
        for comp_name, comp_status in self.components_status.items():
            status_icon = "✅" if comp_status.get("status") == "initialized" else "❌"
            print(f"{status_icon} {comp_name.upper()}: {comp_status.get('status', 'unknown')}")
            
            if comp_name == "component5" and comp_status.get("status") == "initialized":
                print(f"   🧠 Memory Manager: {'✅' if comp_status.get('memory_manager') else '❌'}")
                print(f"   🔗 Gate Network: {'✅' if comp_status.get('gate_network') else '❌'}")
                print(f"   💾 Database: {'✅' if comp_status.get('database') else '❌'}")
        
        # Performance metrics
        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"   Total Conversations: {self.performance_metrics['total_conversations']}")
        print(f"   Avg Response Time: {self.performance_metrics['avg_response_time_ms']:.2f}ms")
        print(f"   Success Rate: {self.performance_metrics['success_rate']*100:.1f}%")
        print(f"   Component 5 LSTM: {'✅ Healthy' if self.performance_metrics['component5_lstm_health'] else '❌ Unhealthy'}")
        print(f"   Integration Errors: {self.performance_metrics['integration_errors']}")
        
        if self.performance_metrics['quality_scores']:
            avg_quality = sum(self.performance_metrics['quality_scores']) / len(self.performance_metrics['quality_scores'])
            print(f"   Avg Quality Score: {avg_quality:.3f}")
        
        # Recent conversations
        print(f"\n💬 RECENT CONVERSATIONS: {len(self.conversation_history)}")
        for conv in self.conversation_history[-3:]:  # Last 3 conversations
            print(f"   [{conv['timestamp'].strftime('%H:%M:%S')}] User: {conv['user_message'][:50]}...")
            print(f"   {'    ' * 6} AI: {conv['ai_response'][:50]}...")
            print(f"   {'    ' * 6} Memories Used: {conv['memories_used']}, Time: {conv['processing_time_ms']:.1f}ms")
        
        print("="*80)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {
            "integration_status": self.components_status,
            "performance_metrics": self.performance_metrics,
            "system_health": {},
            "component_details": {}
        }
        
        # Add orchestrator performance data
        if self.orchestrator:
            summary["system_health"] = self.orchestrator.get_performance_summary()
            summary["component_details"] = {
                "component5": self.orchestrator.component5_bridge.get_statistics(),
                "component6": self.orchestrator.conversation_manager.get_performance_metrics(),
                "component7": {"status": "integrated"}  # Would need Component 7 interface
            }
        
        return summary
    
    async def run_integration_test(self):
        """Run comprehensive integration test with real Component 5"""
        print(f"\n🧪 RUNNING INTEGRATION TEST WITH REAL COMPONENT 5")
        print("="*80)
        
        test_conversations = [
            {
                "user_id": "test_user_001",
                "message": "I'm feeling excited about my new project at work!",
                "emotional_state": {"primary_emotion": "excited", "intensity": 0.8}
            },
            {
                "user_id": "test_user_001", 
                "message": "Can you remind me what we discussed about my presentation?",
                "emotional_state": {"primary_emotion": "neutral", "intensity": 0.5}
            },
            {
                "user_id": "test_user_001",
                "message": "I'm having trouble with time management lately.",
                "emotional_state": {"primary_emotion": "frustrated", "intensity": 0.6}
            }
        ]
        
        for i, test_conv in enumerate(test_conversations, 1):
            print(f"\n🎯 Test Conversation {i}:")
            print(f"User: {test_conv['message']}")
            
            try:
                result = await self.process_conversation(
                    user_id=test_conv["user_id"],
                    user_message=test_conv["message"],
                    emotional_state=test_conv["emotional_state"]
                )
                
                if result.get("success", False):
                    print(f"✅ AI Response: {result['response']}")
                    print(f"📊 Quality: {result.get('quality_analysis', {}).get('overall_quality', 0):.3f}")
                    print(f"⏱️  Time: {result['processing_time_ms']:.2f}ms")
                    
                    # Show Component 5 stats
                    comp5_stats = result.get('component5_stats', {})
                    bridge_stats = comp5_stats.get('bridge_stats', {})
                    print(f"🧠 Memories Retrieved: {bridge_stats.get('memories_retrieved', 0)}")
                    print(f"🔄 Context Assemblies: {bridge_stats.get('context_assemblies', 0)}")
                else:
                    print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ Test conversation {i} failed: {e}")
        
        print(f"\n✅ Integration test completed!")


async def main():
    """Main demo function"""
    print("🚀 Gemini Engine Complete Integration Demo")
    print("=" * 80)
    print("This demo shows the complete integration of Components 5, 6 & 7")
    print("Component 5: Real LSTM Memory Gates (no more mocks!)")
    print("Component 6: Gemini Brain Integration")
    print("Component 7: Response Analysis")
    print("=" * 80)
    
    engine = GeminiEngineIntegration()
    
    try:
        # Initialize all components
        print("\n1️⃣ Initializing All Components...")
        await engine.initialize_components()
        
        # Run integration test
        print("\n2️⃣ Running Integration Test...")
        await engine.run_integration_test()
        
        # Demo proactive engagement
        print("\n3️⃣ Demonstrating Proactive Engagement...")
        try:
            proactive_result = await engine.demonstrate_proactive_engagement("test_user_001")
            print(f"Generated proactive message: {proactive_result.get('message', 'None')}")
        except Exception as e:
            print(f"❌ Proactive engagement demo failed: {e}")
        
        # Final status report
        print("\n4️⃣ Final Status Report:")
        engine.print_status_report()
        
        # Performance summary
        print("\n5️⃣ Detailed Performance Summary:")
        performance = engine.get_performance_summary()
        print(json.dumps(performance, indent=2, default=str))
        
        print("\n✅ Gemini Engine Integration Demo Complete!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
    
    finally:
        # Cleanup
        if engine.orchestrator:
            try:
                await engine.orchestrator.cleanup()
                print("🧹 Cleanup completed")
            except:
                pass


if __name__ == "__main__":
    # Run the complete integration demo with real Component 5
    asyncio.run(main())