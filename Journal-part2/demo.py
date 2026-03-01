# enhanced_integration_demo.py
import asyncio
from datetime import datetime
from component6.enhanced_conversation_manager import EnhancedConversationManager
from component7.quality_analyzer import QualityAnalyzer
from component7.feedback_engine import FeedbackEngine
from component7.metrics_collector import MetricsCollector

class Complete5to6to7Integration:
    """Complete integration: Component 5 → Component 6 → Component 7"""
    
    def __init__(self):
        # Core components
        self.conversation_manager = EnhancedConversationManager()
        
        # Component 7 modules
        self.quality_analyzer = QualityAnalyzer()
        self.feedback_engine = FeedbackEngine()
        self.metrics_collector = MetricsCollector()
        
        # Integration metrics
        self.pipeline_stats = {
            'total_queries_processed': 0,
            'successful_completions': 0,
            'average_quality_score': 0.0,
            'processing_times': []
        }
    
    async def initialize(self):
        """Initialize all components"""
        print("🚀 Initializing Complete 5→6→7 Integration Pipeline...")
        
        # Initialize conversation manager (includes Component 5 LSTM)
        await self.conversation_manager.initialize()
        
        print("✅ Complete integration pipeline initialized")
    
    async def process_complete_workflow(self, 
                                       user_id: str,
                                       user_query: str) -> Dict[str, Any]:
        """
        Complete workflow: Query → LSTM → Gemini → Analysis → Response
        """
        start_time = datetime.utcnow()
        
        print(f"\n🎯 Complete Integration Workflow")
        print("=" * 80)
        print(f"User: {user_id}")
        print(f"Query: {user_query}")
        
        try:
            self.pipeline_stats['total_queries_processed'] += 1
            
            # Phase 1: Component 5 + 6 Integration (LSTM → Gemini)
            print(f"\n📍 Phase 1: LSTM Memory Retrieval + Gemini Response")
            conversation_result = await self.conversation_manager.process_user_query(
                user_id=user_id,
                user_query=user_query
            )
            
            if 'error' in conversation_result:
                raise Exception(f"Conversation processing failed: {conversation_result['error']}")
            
            # Phase 2: Component 7 Analysis
            print(f"\n📍 Phase 2: Response Quality Analysis")
            
            # Analyze response quality
            quality_analysis = await self.quality_analyzer.analyze_response(
                user_message=user_query,
                ai_response=conversation_result['response'],
                conversation_context={
                    'memories_used': conversation_result['memories_used'],
                    'processing_time': conversation_result['processing_time_ms'],
                    'lstm_stats': conversation_result['lstm_stats']
                }
            )
            
            # Collect metrics
            await self.metrics_collector.record_interaction(
                user_id=user_id,
                conversation_id=conversation_result['conversation_id'],
                quality_metrics=quality_analysis,
                response_time=conversation_result['processing_time_ms']
            )
            
            # Generate feedback
            feedback = await self.feedback_engine.generate_improvement_feedback(
                quality_analysis,
                conversation_result['memory_context']
            )
            
            # Update pipeline statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.pipeline_stats['processing_times'].append(processing_time)
            self.pipeline_stats['successful_completions'] += 1
            
            quality_score = quality_analysis.get('overall_quality', 0.0)
            current_avg = self.pipeline_stats['average_quality_score']
            total_completions = self.pipeline_stats['successful_completions']
            self.pipeline_stats['average_quality_score'] = (
                (current_avg * (total_completions - 1) + quality_score) / total_completions
            )
            
            # Compile complete result
            complete_result = {
                **conversation_result,
                'quality_analysis': quality_analysis,
                'component7_feedback': feedback,
                'pipeline_performance': {
                    'total_processing_time_ms': processing_time * 1000,
                    'phase1_time_ms': conversation_result['processing_time_ms'],
                    'phase2_time_ms': (processing_time * 1000) - conversation_result['processing_time_ms'],
                    'quality_score': quality_score,
                    'pipeline_efficiency': self._calculate_efficiency_score(conversation_result, quality_analysis)
                },
                'integration_summary': {
                    'workflow': 'User Query → LSTM Memory Gates → Gemini Engine → Quality Analysis → Enhanced Response',
                    'components_active': ['Component5_LSTM', 'Component6_Gemini', 'Component7_Analysis'],
                    'pipeline_version': '1.0.0',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            print(f"\n✅ Complete Integration Pipeline Successful!")
            print(f"   📚 LSTM Memories Used: {conversation_result['memories_used']}")
            print(f"   🤖 Gemini Response: {len(conversation_result['response'])} chars")
            print(f"   📊 Quality Score: {quality_score:.3f}")
            print(f"   ⏱️ Total Time: {processing_time:.2f}s")
            
            return complete_result
            
        except Exception as e:
            print(f"❌ Complete integration pipeline failed: {e}")
            return {
                'error': str(e),
                'user_id': user_id,
                'user_query': user_query,
                'pipeline_stage': 'integration_failure',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _calculate_efficiency_score(self, conv_result: Dict, quality_analysis: Dict) -> float:
        """Calculate pipeline efficiency score"""
        # Factors: processing time, memory utilization, response quality
        time_efficiency = max(0, 1.0 - (conv_result['processing_time_ms'] / 10000))  # Penalty after 10s
        memory_efficiency = min(1.0, conv_result['memories_used'] / 5)  # Optimal around 5 memories
        quality_efficiency = quality_analysis.get('overall_quality', 0.0)
        
        return (time_efficiency * 0.3 + memory_efficiency * 0.2 + quality_efficiency * 0.5)

async def main():
    """Demo of complete integration"""
    print("🌟 Component 5 → 6 → 7 Complete Integration Demo")
    print("=" * 80)
    
    # Initialize integration
    integration = Complete5to6to7Integration()
    await integration.initialize()
    
    # Demo queries
    demo_queries = [
        {
            'user_id': '123',
            'query': 'How did my English exam go and what should I focus on next?'
        },
        {
            'user_id': '123',
            'query': 'I\'m feeling nervous about my upcoming date with Ninad. Any advice?'
        },
        {
            'user_id': '123',
            'query': 'Can you help me understand what I learned recently?'
        }
    ]
    
    # Process each query through complete pipeline
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n🔄 Processing Demo Query {i}/{len(demo_queries)}")
        
        result = await integration.process_complete_workflow(
            user_id=demo['user_id'],
            user_query=demo['query']
        )
        
        if 'error' not in result:
            print(f"\n💬 Final Response:")
            print(f"   {result['response'][:200]}...")
        
        print(f"\n" + "="*40)
    
    # Show pipeline statistics
    print(f"\n📈 Pipeline Statistics:")
    print(f"   Total Queries: {integration.pipeline_stats['total_queries_processed']}")
    print(f"   Successful: {integration.pipeline_stats['successful_completions']}")
    print(f"   Average Quality: {integration.pipeline_stats['average_quality_score']:.3f}")
    print(f"   Success Rate: {integration.pipeline_stats['successful_completions']/integration.pipeline_stats['total_queries_processed']:.1%}")

if __name__ == "__main__":
    asyncio.run(main())
