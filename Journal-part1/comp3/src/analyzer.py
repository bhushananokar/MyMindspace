import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from comp3.src.entity_extractor import EntityExtractor
from comp3.src.event_extractor import EventExtractor
from comp3.src.embedding_generator import EmbeddingGenerator
from comp3.src.temporal_analyzer import TemporalAnalyzer
from comp3.data.schemas import SemanticAnalysis

class Component3Analyzer:
    """Main orchestrator for Component 3: NER, Temporal & Event Analysis"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_default_config()
        
        print("Initializing Component 3: NER, Temporal & Event Analysis...")
        start_time = time.time()
        
        # Initialize all sub-components
        self.entity_extractor = EntityExtractor(
            model_name=self.config['models']['spacy_model']
        )
        
        self.event_extractor = EventExtractor()
        
        self.embedding_generator = EmbeddingGenerator(
            primary_model=self.config['models']['primary_embedding_model'],
            lightweight_model=self.config['models']['lightweight_embedding_model'],
            cache_size=self.config['performance']['embedding_cache_size']
        )
        
        self.temporal_analyzer = TemporalAnalyzer()
        
        print(f"Component 3 initialized in {time.time() - start_time:.2f}s")
    
    def analyze(self, 
               processed_text: str,
               user_id: str,
               entry_timestamp: datetime = None,
               last_entry_timestamp: datetime = None) -> SemanticAnalysis:
        """
        Main analysis function - processes text through all components
        
        Args:
            processed_text: Clean text from Component 1
            user_id: User identifier for personalized analysis
            entry_timestamp: When this entry was created
            last_entry_timestamp: When user's last entry was created
        
        Returns:
            SemanticAnalysis object with all extracted features
        """
        start_time = time.time()
        
        if entry_timestamp is None:
            entry_timestamp = datetime.now()
        
        try:
            # 1. Entity Extraction (NER)
            people, locations, organizations, relationships = self.entity_extractor.extract_entities(
                processed_text
            )
            
            # 2. Event Extraction (Component 8 integration)
            future_events = self.event_extractor.extract_events(
                processed_text, entry_timestamp
            )
            
            followup_questions = self.event_extractor.generate_followup_questions(
                future_events, entry_timestamp
            )
            
            # 3. Generate Embeddings
            embeddings = self.embedding_generator.generate_embeddings(
                processed_text, 
                max_length=self.config['embedding_settings']['max_text_length']
            )
            
            # 4. Temporal Analysis
            temporal_features = self.temporal_analyzer.analyze_temporal_features(
                current_time=entry_timestamp,
                user_id=user_id,
                last_entry_time=last_entry_timestamp
            )
            
            # 5. Additional Analysis
            detected_topics = self._extract_topics(processed_text, embeddings)
            novelty_score = self._calculate_novelty(user_id, embeddings)
            complexity_score = self.embedding_generator.analyze_content_complexity(
                processed_text, embeddings
            )
            
            # 6. Build final analysis object
            analysis = SemanticAnalysis(
                # Entity extraction results
                people=people,
                locations=locations,
                organizations=organizations,
                entity_relationships=relationships,
                
                # Event extraction results (Component 8)
                future_events=future_events,
                followup_questions=followup_questions,
                
                # Embedding results
                embeddings=embeddings,
                
                # Temporal analysis
                temporal_features=temporal_features,
                
                # Additional features
                detected_topics=detected_topics,
                novelty_score=novelty_score,
                complexity_score=complexity_score,
                
                # Metadata
                processing_time_ms=(time.time() - start_time) * 1000,
                component_version="3.0"
            )
            
            # Store analysis for future novelty calculations
            self._store_analysis_for_user(user_id, analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error in Component 3 analysis: {e}")
            # Return minimal analysis object on error
            return self._create_error_analysis(processed_text, entry_timestamp, str(e))
    
    def batch_analyze(self, 
                     entries: list,
                     user_id: str) -> list:
        """Analyze multiple entries efficiently"""
        results = []
        
        # Extract texts for batch embedding generation
        texts = [entry['text'] for entry in entries]
        batch_embeddings = self.embedding_generator.batch_generate_embeddings(
            texts, batch_size=self.config['performance']['batch_size']
        )
        
        # Process each entry with pre-computed embeddings
        for i, entry in enumerate(entries):
            try:
                # Use pre-computed embeddings
                embeddings = batch_embeddings[i]
                
                # Process other components normally
                people, locations, organizations, relationships = self.entity_extractor.extract_entities(
                    entry['text']
                )
                
                future_events = self.event_extractor.extract_events(
                    entry['text'], entry.get('timestamp', datetime.now())
                )
                
                followup_questions = self.event_extractor.generate_followup_questions(
                    future_events, entry.get('timestamp', datetime.now())
                )
                
                temporal_features = self.temporal_analyzer.analyze_temporal_features(
                    current_time=entry.get('timestamp', datetime.now()),
                    user_id=user_id,
                    last_entry_time=entry.get('last_entry_timestamp')
                )
                
                # Create analysis object
                analysis = SemanticAnalysis(
                    people=people,
                    locations=locations,
                    organizations=organizations,
                    entity_relationships=relationships,
                    future_events=future_events,
                    followup_questions=followup_questions,
                    embeddings=embeddings,
                    temporal_features=temporal_features,
                    detected_topics=self._extract_topics(entry['text'], embeddings),
                    novelty_score=self._calculate_novelty(user_id, embeddings),
                    complexity_score=self.embedding_generator.analyze_content_complexity(
                        entry['text'], embeddings
                    ),
                    processing_time_ms=0,  # Will be calculated for batch
                    component_version="3.0"
                )
                
                results.append(analysis)
                
            except Exception as e:
                print(f"Error processing entry {i}: {e}")
                error_analysis = self._create_error_analysis(
                    entry['text'], 
                    entry.get('timestamp', datetime.now()), 
                    str(e)
                )
                results.append(error_analysis)
        
        return results
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights about user patterns and behavior"""
        return {
            'writing_patterns': self.temporal_analyzer.get_user_writing_insights(user_id),
            'writing_streaks': self.temporal_analyzer.detect_writing_streaks(user_id),
            'next_predicted_entry': self.temporal_analyzer.predict_next_entry_time(
                user_id, datetime.now()
            )
        }
    
    def _extract_topics(self, text: str, embeddings) -> list:
        """Extract main topics from text"""
        # Simple keyword extraction for now
        # In production, could use more sophisticated topic modeling
        words = text.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        important_words = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Get most frequent words as topics
        from collections import Counter
        word_counts = Counter(important_words)
        topics = [word for word, count in word_counts.most_common(5)]
        
        return topics
    
    def _calculate_novelty(self, user_id: str, current_embedding) -> float:
        """Calculate novelty score compared to user's history"""
        # This would typically compare against stored user embeddings
        # For now, return a placeholder
        return 0.5
    
    def _store_analysis_for_user(self, user_id: str, analysis: SemanticAnalysis):
        """Store analysis results for future reference"""
        # In production, this would store to database
        # For now, this is a placeholder
        pass
    
    def _create_error_analysis(self, text: str, timestamp: datetime, error_msg: str) -> SemanticAnalysis:
        """Create minimal analysis object when errors occur"""
        return SemanticAnalysis(
            people=[],
            locations=[],
            organizations=[],
            entity_relationships={},
            future_events=[],
            followup_questions=[],
            embeddings=None,
            temporal_features=None,
            detected_topics=[],
            novelty_score=0.0,
            complexity_score=0.0,
            processing_time_ms=0.0,
            component_version="3.0-error"
        )
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'models': {
                'spacy_model': 'en_core_web_lg',
                'primary_embedding_model': 'all-mpnet-base-v2',
                'lightweight_embedding_model': 'all-MiniLM-L6-v2'
            },
            'performance': {
                'max_processing_time_ms': 300,
                'embedding_cache_size': 10000,
                'batch_size': 32
            },
            'entity_extraction': {
                'person_confidence_threshold': 0.7,
                'location_confidence_threshold': 0.6,
                'organization_confidence_threshold': 0.6
            },
            'event_extraction': {
                'confidence_threshold': 0.5,
                'max_future_days': 365
            },
            'embedding_settings': {
                'cache_enabled': True,
                'similarity_threshold': 0.8,
                'max_text_length': 5000
            }
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_size = 0
        if hasattr(self.embedding_generator, '_cached_encode') and hasattr(self.embedding_generator._cached_encode, 'cache_info'):
            cache_size = self.embedding_generator._cached_encode.cache_info().currsize
        
        return {
            'cache_size': cache_size,
            'models_loaded': {
                'spacy': self.entity_extractor.nlp is not None,
                'primary_embedding': self.embedding_generator.primary_model is not None,
                'lightweight_embedding': self.embedding_generator.lightweight_model is not None
            }
        }