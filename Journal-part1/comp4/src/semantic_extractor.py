"""
Semantic Feature Extractor for Component 4
Extracts topic modeling, novelty detection, content complexity, and entity features
"""

import numpy as np
import re
from typing import Dict, List, Optional, Any, Set
from collections import Counter
import logging

from comp4.data.schemas import SemanticFeatures

logger = logging.getLogger(__name__)

class SemanticFeatureExtractor:
    """
    Extracts semantic features from Component 3's semantic analysis
    Focuses on content analysis, novelty, complexity, and linguistic patterns
    """
    
    def __init__(self):
        """Initialize semantic feature extractor"""
        self.name = "SemanticFeatureExtractor"
        self.version = "4.0"
        
        # Emotional language indicators
        self.emotional_words = {
            'positive': {'happy', 'joy', 'excited', 'love', 'wonderful', 'amazing', 'great', 'fantastic', 'beautiful', 'perfect'},
            'negative': {'sad', 'angry', 'frustrated', 'terrible', 'awful', 'hate', 'horrible', 'disappointing', 'stressed', 'worried'},
            'intensity': {'very', 'extremely', 'incredibly', 'absolutely', 'completely', 'totally', 'really', 'so', 'quite', 'pretty'}
        }
        
        # Social language indicators
        self.social_words = {
            'people': {'friend', 'family', 'colleague', 'partner', 'mom', 'dad', 'brother', 'sister', 'we', 'us', 'they', 'together'},
            'interaction': {'talk', 'discuss', 'meet', 'call', 'text', 'share', 'tell', 'listen', 'conversation', 'chat'},
            'relationships': {'relationship', 'connection', 'bond', 'close', 'distant', 'support', 'help', 'care', 'love', 'trust'}
        }
        
        # Complexity indicators
        self.complexity_patterns = {
            'conjunctions': r'\b(however|therefore|moreover|furthermore|nevertheless|consequently|although|whereas)\b',
            'subordination': r'\b(because|since|while|if|unless|though|when|where|that|which)\b',
            'abstract_concepts': r'\b(concept|idea|theory|philosophy|perspective|approach|strategy|principle)\b'
        }
    
    def extract(
        self,
        semantic_analysis,  # From Component 3
        raw_text: str = "",
        user_topic_history: Optional[List[str]] = None
    ) -> SemanticFeatures:
        """
        Extract semantic features from semantic analysis and raw text
        
        Args:
            semantic_analysis: SemanticAnalysis from Component 3
            raw_text: Original text for linguistic analysis
            user_topic_history: User's historical topics for novelty detection
            
        Returns:
            SemanticFeatures object with 30-dimensional feature vector
        """
        try:
            # Extract topic distribution
            topic_distribution = self._extract_topic_distribution(semantic_analysis)
            
            # Calculate novelty score
            novelty_score = self._calculate_novelty_score(semantic_analysis, user_topic_history)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(raw_text, semantic_analysis)
            
            # Calculate coherence score
            coherence_score = self._calculate_coherence_score(raw_text, semantic_analysis)
            
            # Calculate entity density
            entity_density = self._calculate_entity_density(semantic_analysis, raw_text)
            
            # Calculate event density
            event_density = self._calculate_event_density(semantic_analysis, raw_text)
            
            # Calculate vocabulary richness
            vocabulary_richness = self._calculate_vocabulary_richness(raw_text)
            
            # Calculate sentence complexity
            sentence_complexity = self._calculate_sentence_complexity(raw_text)
            
            # Calculate emotional language density
            emotional_language = self._calculate_emotional_language(raw_text)
            
            # Calculate social language density
            social_language = self._calculate_social_language(raw_text)
            
            return SemanticFeatures(
                topic_distribution=topic_distribution,
                novelty_score=novelty_score,
                complexity_score=complexity_score,
                coherence_score=coherence_score,
                entity_density=entity_density,
                event_density=event_density,
                vocabulary_richness=vocabulary_richness,
                sentence_complexity=sentence_complexity,
                emotional_language=emotional_language,
                social_language=social_language
            )
            
        except Exception as e:
            logger.error(f"Error extracting semantic features: {e}")
            return
    
    def _extract_topic_distribution(self, semantic_analysis) -> np.ndarray:
        """Extract topic distribution from semantic analysis"""
        try:
            # Initialize 10-dimensional topic vector
            topic_vector = np.zeros(10, dtype=np.float32)
            
            if hasattr(semantic_analysis, 'detected_topics') and semantic_analysis.detected_topics:
                topics = semantic_analysis.detected_topics
                
                # Map topics to predefined categories
                topic_categories = {
                    0: ['work', 'job', 'career', 'business', 'office', 'professional'],
                    1: ['family', 'mom', 'dad', 'parent', 'child', 'home', 'house'],
                    2: ['friend', 'social', 'party', 'meet', 'together', 'relationship'],
                    3: ['health', 'doctor', 'exercise', 'fitness', 'medical', 'body'],
                    4: ['travel', 'trip', 'vacation', 'journey', 'visit', 'place'],
                    5: ['education', 'school', 'study', 'learn', 'class', 'university'],
                    6: ['emotion', 'feel', 'mood', 'happy', 'sad', 'stress', 'anxiety'],
                    7: ['goal', 'plan', 'future', 'dream', 'hope', 'ambition'],
                    8: ['hobby', 'interest', 'fun', 'enjoy', 'activity', 'leisure'],
                    9: ['daily', 'routine', 'everyday', 'normal', 'regular', 'usual']
                }
                
                # Count matches for each category
                for topic in topics:
                    topic_lower = topic.lower()
                    for category_idx, keywords in topic_categories.items():
                        if any(keyword in topic_lower for keyword in keywords):
                            topic_vector[category_idx] += 1.0
                
                # Normalize to probabilities
                total = np.sum(topic_vector)
                if total > 0:
                    topic_vector = topic_vector / total
                else:
                    topic_vector[9] = 1.0  # Default to 'daily' category
                    
            else:
                # Default distribution for missing topics
                topic_vector[9] = 1.0  # 'daily' category
            
            return topic_vector
            
        except Exception as e:
            logger.error(f"Error extracting topic distribution: {e}")
            default_vector = np.zeros(10, dtype=np.float32)
            default_vector[9] = 1.0
            return default_vector
    
    def _calculate_novelty_score(
        self, 
        semantic_analysis, 
        user_topic_history: Optional[List[str]]
    ) -> float:
        """Calculate content novelty based on user's topic history"""
        try:
            if not user_topic_history:
                return 0.5  # Neutral for new users
            
            current_topics = set()
            if hasattr(semantic_analysis, 'detected_topics') and semantic_analysis.detected_topics:
                current_topics = set(topic.lower() for topic in semantic_analysis.detected_topics)
            
            if not current_topics:
                return 0.3  # Low novelty for entries without clear topics
            
            # Calculate overlap with historical topics
            historical_topics = set(topic.lower() for topic in user_topic_history)
            
            if not historical_topics:
                return 0.8  # High novelty for first entries
            
            # Calculate Jaccard distance (1 - Jaccard similarity)
            intersection = len(current_topics.intersection(historical_topics))
            union = len(current_topics.union(historical_topics))
            
            if union == 0:
                return 0.5
            
            jaccard_similarity = intersection / union
            novelty = 1.0 - jaccard_similarity
            
            return min(max(novelty, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating novelty score: {e}")
            return 0.5
    
    def _calculate_complexity_score(self, raw_text: str, semantic_analysis) -> float:
        """Calculate content complexity based on text analysis"""
        try:
            if not raw_text:
                return 0.0
            
            complexity_score = 0.0
            text_lower = raw_text.lower()
            
            # Sentence structure complexity
            sentences = re.split(r'[.!?]+', raw_text)
            if sentences:
                avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()])
                # Normalize sentence length (10-30 words is typical range)
                complexity_score += min(max(avg_sentence_length - 10, 0) / 20, 0.3)
            
            # Lexical complexity
            words = raw_text.split()
            if words:
                unique_words = len(set(word.lower() for word in words))
                lexical_diversity = unique_words / len(words)
                complexity_score += min(lexical_diversity, 0.3)
            
            # Syntactic complexity patterns
            for pattern_name, pattern in self.complexity_patterns.items():
                matches = len(re.findall(pattern, text_lower))
                complexity_score += min(matches * 0.05, 0.15)
            
            # Entity and concept density
            if hasattr(semantic_analysis, 'people') and semantic_analysis.people:
                complexity_score += min(len(semantic_analysis.people) * 0.02, 0.1)
            
            if hasattr(semantic_analysis, 'organizations') and semantic_analysis.organizations:
                complexity_score += min(len(semantic_analysis.organizations) * 0.02, 0.1)
            
            return min(complexity_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 0.3
    
    def _calculate_coherence_score(self, raw_text: str, semantic_analysis) -> float:
        """Calculate logical coherence of the text"""
        try:
            if not raw_text:
                return 0.0
            
            coherence_score = 0.5  # Base score
            
            # Topic consistency
            if hasattr(semantic_analysis, 'detected_topics') and semantic_analysis.detected_topics:
                topics = semantic_analysis.detected_topics
                if len(topics) > 0:
                    # Higher coherence if fewer, more focused topics
                    topic_focus = max(0, 1.0 - (len(topics) - 1) * 0.1)
                    coherence_score += topic_focus * 0.3
            
            # Temporal consistency (events in logical order)
            if hasattr(semantic_analysis, 'future_events') and semantic_analysis.future_events:
                # Check if future events have reasonable time progression
                events_with_dates = [
                    event for event in semantic_analysis.future_events 
                    if hasattr(event, 'parsed_date') and event.parsed_date
                ]
                if len(events_with_dates) > 1:
                    dates = [event.parsed_date for event in events_with_dates]
                    is_chronological = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
                    if is_chronological:
                        coherence_score += 0.2
            
            # Pronoun and reference consistency
            pronouns = len(re.findall(r'\b(he|she|it|they|this|that)\b', raw_text.lower()))
            total_words = len(raw_text.split())
            if total_words > 0:
                pronoun_ratio = pronouns / total_words
                # Moderate pronoun use indicates good coherence
                if 0.02 <= pronoun_ratio <= 0.1:
                    coherence_score += 0.1
            
            return min(max(coherence_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating coherence score: {e}")
            return 0.5
    
    def _calculate_entity_density(self, semantic_analysis, raw_text: str) -> float:
        """Calculate density of named entities (people, places, organizations)"""
        try:
            if not raw_text:
                return 0.0
            
            entity_count = 0
            
            if hasattr(semantic_analysis, 'people') and semantic_analysis.people:
                entity_count += len(semantic_analysis.people)
            
            if hasattr(semantic_analysis, 'locations') and semantic_analysis.locations:
                entity_count += len(semantic_analysis.locations)
            
            if hasattr(semantic_analysis, 'organizations') and semantic_analysis.organizations:
                entity_count += len(semantic_analysis.organizations)
            
            # Normalize by text length (entities per 100 words)
            word_count = len(raw_text.split())
            if word_count > 0:
                density = (entity_count / word_count) * 100
                return min(density / 10.0, 1.0)  # Normalize to 0-1 range
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating entity density: {e}")
            return 0.0
    
    def _calculate_event_density(self, semantic_analysis, raw_text: str) -> float:
        """Calculate density of future events and temporal references"""
        try:
            if not raw_text:
                return 0.0
            
            event_count = 0
            
            if hasattr(semantic_analysis, 'future_events') and semantic_analysis.future_events:
                event_count = len(semantic_analysis.future_events)
            
            # Also count temporal keywords in text
            temporal_keywords = [
                'tomorrow', 'next', 'later', 'soon', 'eventually', 'upcoming',
                'plan', 'schedule', 'meeting', 'appointment', 'deadline'
            ]
            
            text_lower = raw_text.lower()
            keyword_count = sum(1 for keyword in temporal_keywords if keyword in text_lower)
            
            total_events = event_count + keyword_count * 0.5  # Weight keywords less
            
            # Normalize by text length
            word_count = len(raw_text.split())
            if word_count > 0:
                density = (total_events / word_count) * 100
                return min(density / 5.0, 1.0)  # Normalize to 0-1 range
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating event density: {e}")
            return 0.0
    
    def _calculate_vocabulary_richness(self, raw_text: str) -> float:
        """Calculate vocabulary richness (type-token ratio)"""
        try:
            if not raw_text:
                return 0.0
            
            # Clean and tokenize text
            words = re.findall(r'\b\w+\b', raw_text.lower())
            
            if len(words) < 5:  # Too short to calculate meaningful richness
                return 0.5
            
            # Calculate type-token ratio
            unique_words = len(set(words))
            total_words = len(words)
            
            # Raw type-token ratio
            ttr = unique_words / total_words
            
            # Adjust for text length (longer texts naturally have lower TTR)
            if total_words > 50:
                # Moving-average TTR for longer texts
                window_size = min(50, total_words // 2)
                ttr_values = []
                for i in range(0, total_words - window_size + 1, window_size // 2):
                    window_words = words[i:i + window_size]
                    window_unique = len(set(window_words))
                    window_ttr = window_unique / len(window_words)
                    ttr_values.append(window_ttr)
                ttr = np.mean(ttr_values)
            
            return min(max(ttr, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating vocabulary richness: {e}")
            return 0.5
    
    def _calculate_sentence_complexity(self, raw_text: str) -> float:
        """Calculate average sentence complexity"""
        try:
            if not raw_text:
                return 0.0
            
            sentences = re.split(r'[.!?]+', raw_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return 0.0
            
            complexity_scores = []
            
            for sentence in sentences:
                score = 0.0
                words = sentence.split()
                
                # Length component
                if len(words) > 15:
                    score += 0.3
                elif len(words) > 10:
                    score += 0.2
                elif len(words) > 5:
                    score += 0.1
                
                # Punctuation complexity
                commas = sentence.count(',')
                semicolons = sentence.count(';')
                colons = sentence.count(':')
                score += min((commas + semicolons * 2 + colons * 1.5) * 0.1, 0.3)
                
                # Subordinate clauses
                subordinators = ['that', 'which', 'who', 'where', 'when', 'because', 'although', 'while']
                sub_count = sum(1 for sub in subordinators if sub in sentence.lower())
                score += min(sub_count * 0.15, 0.4)
                
                complexity_scores.append(min(score, 1.0))
            
            return np.mean(complexity_scores)
            
        except Exception as e:
            logger.error(f"Error calculating sentence complexity: {e}")
            return 0.3
    
    def _calculate_emotional_language(self, raw_text: str) -> float:
        """Calculate density of emotional language"""
        try:
            if not raw_text:
                return 0.0
            
            text_lower = raw_text.lower()
            words = set(re.findall(r'\b\w+\b', text_lower))
            
            emotional_word_count = 0
            for category, word_set in self.emotional_words.items():
                emotional_word_count += len(words.intersection(word_set))
            
            # Normalize by total unique words
            if len(words) > 0:
                density = emotional_word_count / len(words)
                return min(density * 2, 1.0)  # Scale up since emotional words are subset
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating emotional language: {e}")
            return 0.0
    
    def _calculate_social_language(self, raw_text: str) -> float:
        """Calculate density of social/interpersonal language"""
        try:
            if not raw_text:
                return 0.0
            
            text_lower = raw_text.lower()
            words = set(re.findall(r'\b\w+\b', text_lower))
            
            social_word_count = 0
            for category, word_set in self.social_words.items():
                social_word_count += len(words.intersection(word_set))
            
            # Normalize by total unique words
            if len(words) > 0:
                density = social_word_count / len(words)
                return min(density * 2, 1.0)  # Scale up since social words are subset
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating social language: {e}")
            return 0.0
    
    # def _get_default_features(self) -> SemanticFeatures:
    #     """Return default semantic features for error cases"""
    #     default_topic_dist = np.zeros(10, dtype=np.float32)
    #     default_topic_dist[9] = 1.0  # Default to 'daily' category
        
    #     return SemanticFeatures(
    #         topic_distribution=default_topic_dist,
    #         novelty_score=0.5,
    #         complexity_score=0.3,
    #         coherence_score=0.5,
    #         entity_density=0.0,
    #         event_density=0.0,
    #         vocabulary_richness=0.5,
    #         sentence_complexity=0.3,
    #         emotional_language=0.0,
    #         social_language=0.0
    #     )
    
    def get_feature_names(self) -> List[str]:
        """Get names of all semantic features for debugging"""
        return [
            'topic_work', 'topic_family', 'topic_social', 'topic_health', 'topic_travel',
            'topic_education', 'topic_emotion', 'topic_goals', 'topic_hobbies', 'topic_daily',
            'novelty_score', 'complexity_score', 'coherence_score', 'entity_density', 'event_density',
            'vocabulary_richness', 'sentence_complexity', 'emotional_language', 'social_language', 'combined_complexity',
            'high_social_content', 'future_focused', 'rich_vocabulary', 'emotional_content', 'social_content',
            'novel_complexity', 'coherent_complexity', 'total_mention_density', 'expressive_language', 'overall_quality'
        ]
