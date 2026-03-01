import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data.schemas import SemanticEmbedding

class EmbeddingGenerator:
    """Generate high-quality sentence embeddings for semantic analysis"""
    
    def __init__(self, 
                 primary_model: str = "all-mpnet-base-v2",
                 lightweight_model: str = "all-MiniLM-L6-v2",
                 cache_size: int = 10000):
        
        print("Loading embedding models...")
        start_time = time.time()
        
        # Load primary model (768 dimensions, high quality)
        self.primary_model = SentenceTransformer(primary_model)
        self.primary_dim = 768
        
        # Load lightweight model (384 dimensions, fast)
        self.lightweight_model = SentenceTransformer(lightweight_model)
        self.lightweight_dim = 384
        
        self.cache_size = cache_size
        self.model_versions = {
            'primary': primary_model,
            'lightweight': lightweight_model
        }
        
        print(f"Models loaded in {time.time() - start_time:.2f}s")
    
    @lru_cache(maxsize=10000)
    def _cached_encode(self, text: str, model_type: str) -> np.ndarray:
        """Cached encoding to avoid recomputing embeddings"""
        if model_type == 'primary':
            return self.primary_model.encode(text, convert_to_numpy=True)
        else:
            return self.lightweight_model.encode(text, convert_to_numpy=True)
    
    def generate_embeddings(self, text: str, max_length: int = 5000) -> SemanticEmbedding:
        """Generate both primary and lightweight embeddings"""
        start_time = time.time()
        
        # Truncate text if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Generate embeddings
        primary_embedding = self._cached_encode(text, 'primary')
        lightweight_embedding = self._cached_encode(text, 'lightweight')
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return SemanticEmbedding(
            primary_embedding=primary_embedding,
            lightweight_embedding=lightweight_embedding,
            text_length=len(text),
            processing_time_ms=processing_time,
            model_version=f"{self.model_versions['primary']}, {self.model_versions['lightweight']}"
        )
    
    def batch_generate_embeddings(self, texts: List[str], 
                                batch_size: int = 32) -> List[SemanticEmbedding]:
        """Generate embeddings for multiple texts efficiently"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            start_time = time.time()
            
            # Batch encode for efficiency
            primary_batch = self.primary_model.encode(batch_texts, convert_to_numpy=True)
            lightweight_batch = self.lightweight_model.encode(batch_texts, convert_to_numpy=True)
            
            processing_time = (time.time() - start_time) * 1000 / len(batch_texts)
            
            for j, text in enumerate(batch_texts):
                embedding = SemanticEmbedding(
                    primary_embedding=primary_batch[j],
                    lightweight_embedding=lightweight_batch[j],
                    text_length=len(text),
                    processing_time_ms=processing_time,
                    model_version=f"{self.model_versions['primary']}, {self.model_versions['lightweight']}"
                )
                embeddings.append(embedding)
        
        return embeddings
    
    def calculate_similarity(self, 
                           embedding1: SemanticEmbedding, 
                           embedding2: SemanticEmbedding,
                           use_primary: bool = True) -> float:
        """Calculate cosine similarity between embeddings"""
        if use_primary:
            emb1 = embedding1.primary_embedding.reshape(1, -1)
            emb2 = embedding2.primary_embedding.reshape(1, -1)
        else:
            emb1 = embedding1.lightweight_embedding.reshape(1, -1)
            emb2 = embedding2.lightweight_embedding.reshape(1, -1)
        
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return float(similarity)
    
    def find_similar_embeddings(self, 
                              query_embedding: SemanticEmbedding,
                              candidate_embeddings: List[SemanticEmbedding],
                              threshold: float = 0.8,
                              top_k: int = 10,
                              use_primary: bool = True) -> List[Tuple[int, float]]:
        """Find most similar embeddings to query"""
        similarities = []
        
        query_vec = (query_embedding.primary_embedding if use_primary 
                    else query_embedding.lightweight_embedding)
        
        # Prepare candidate vectors
        candidate_vecs = []
        for emb in candidate_embeddings:
            vec = (emb.primary_embedding if use_primary 
                  else emb.lightweight_embedding)
            candidate_vecs.append(vec)
        
        if not candidate_vecs:
            return []
        
        candidate_matrix = np.vstack(candidate_vecs)
        query_vec = query_vec.reshape(1, -1)
        
        # Calculate all similarities at once
        similarities_array = cosine_similarity(query_vec, candidate_matrix)[0]
        
        # Filter by threshold and get top-k
        valid_indices = np.where(similarities_array >= threshold)[0]
        valid_similarities = similarities_array[valid_indices]
        
        # Sort by similarity (descending) and take top-k
        sorted_indices = np.argsort(valid_similarities)[::-1][:top_k]
        
        results = [(int(valid_indices[i]), float(valid_similarities[i])) 
                  for i in sorted_indices]
        
        return results
    
    def calculate_novelty_score(self, 
                              new_embedding: SemanticEmbedding,
                              historical_embeddings: List[SemanticEmbedding],
                              use_primary: bool = True) -> float:
        """Calculate how novel/different this text is compared to historical data"""
        if not historical_embeddings:
            return 1.0  # Completely novel if no history
        
        # Find maximum similarity with historical embeddings
        max_similarity = 0.0
        
        for hist_embedding in historical_embeddings[-50:]:  # Check last 50 for efficiency
            similarity = self.calculate_similarity(new_embedding, hist_embedding, use_primary)
            max_similarity = max(max_similarity, similarity)
        
        # Novelty is inverse of similarity
        novelty_score = 1.0 - max_similarity
        return max(0.0, min(1.0, novelty_score))
    
    def analyze_content_complexity(self, text: str, embedding: SemanticEmbedding) -> float:
        """Analyze semantic complexity of the text"""
        # Simple heuristics for complexity
        sentences = text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Vocabulary richness
        words = text.lower().split()
        unique_words = len(set(words))
        vocab_richness = unique_words / max(len(words), 1)
        
        # Embedding magnitude (higher magnitude often indicates more complex semantics)
        embedding_magnitude = np.linalg.norm(embedding.primary_embedding)
        normalized_magnitude = min(embedding_magnitude / 10.0, 1.0)
        
        # Combine factors
        complexity_score = (
            (avg_sentence_length / 20.0) * 0.3 +  # Sentence complexity
            vocab_richness * 0.4 +                 # Vocabulary diversity  
            normalized_magnitude * 0.3             # Semantic density
        )
        
        return min(max(complexity_score, 0.0), 1.0)
    
    def extract_topics(self, 
                      embeddings: List[SemanticEmbedding],
                      texts: List[str],
                      num_topics: int = 5) -> List[str]:
        """Extract main topics from a collection of embeddings"""
        if not embeddings or len(embeddings) < 2:
            return []
        
        # Simple topic extraction using clustering of embeddings
        from sklearn.cluster import KMeans
        
        # Use lightweight embeddings for efficiency
        embedding_matrix = np.vstack([emb.lightweight_embedding for emb in embeddings])
        
        # Cluster embeddings
        n_clusters = min(num_topics, len(embeddings))
        if n_clusters < 2:
            return []
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embedding_matrix)
        
        # Extract representative topics from clusters
        topics = []
        for i in range(n_clusters):
            cluster_indices = np.where(cluster_labels == i)[0]
            if len(cluster_indices) > 0:
                # Find the text closest to cluster center
                cluster_embeddings = embedding_matrix[cluster_indices]
                center = kmeans.cluster_centers_[i]
                
                distances = np.linalg.norm(cluster_embeddings - center, axis=1)
                closest_idx = cluster_indices[np.argmin(distances)]
                
                # Extract keywords from the most representative text
                topic_text = texts[closest_idx]
                topic_words = self._extract_key_words(topic_text)
                if topic_words:
                    topics.append(', '.join(topic_words[:3]))
        
        return topics
    
    def _extract_key_words(self, text: str) -> List[str]:
        """Extract key words from text (simple implementation)"""
        # Remove common stop words and get important words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'can', 'this', 'that',
                     'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                     'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
                     'its', 'our', 'their', 'a', 'an'}
        
        words = text.lower().split()
        key_words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Get most frequent words
        from collections import Counter
        word_counts = Counter(key_words)
        return [word for word, count in word_counts.most_common(10)]