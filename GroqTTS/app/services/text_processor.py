"""
Text processing service for chunking and preprocessing text for TTS.
"""

import re
import logging
from typing import List, Tuple
from ..config.settings import settings

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text preprocessing and chunking for optimal TTS generation."""
    
    def __init__(self):
        # Sentence boundary patterns
        self.sentence_patterns = [
            r'[.!?]+\s+',  # Period, exclamation, question mark followed by space
            r'[.!?]+$',    # End of text
        ]
        
        # Maximum tokens per chunk (approximate) - optimized for real-time streaming
        self.max_chunk_tokens = 75  # Further reduced for faster generation
        
        # Minimum chunk length
        self.min_chunk_length = 3  # Further reduced for more responsive streaming
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for TTS processing."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle common abbreviations that might confuse sentence splitting
        text = re.sub(r'\bDr\.', 'Doctor', text)
        text = re.sub(r'\bMr\.', 'Mister', text)
        text = re.sub(r'\bMrs\.', 'Missus', text)
        text = re.sub(r'\bMs\.', 'Miss', text)
        text = re.sub(r'\betc\.', 'etcetera', text)
        text = re.sub(r'\be\.g\.', 'for example', text)
        text = re.sub(r'\bi\.e\.', 'that is', text)
        
        # Handle URLs and email addresses
        text = re.sub(r'http[s]?://\S+', '[URL]', text)
        text = re.sub(r'\S+@\S+\.\S+', '[EMAIL]', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using multiple patterns."""
        sentences = []
        current_text = text
        
        for pattern in self.sentence_patterns:
            parts = re.split(pattern, current_text)
            if len(parts) > 1:
                sentences.extend([part.strip() for part in parts if part.strip()])
                break
        else:
            # If no patterns matched, treat as single sentence
            sentences = [current_text.strip()] if current_text.strip() else []
        
        return [s for s in sentences if len(s) >= self.min_chunk_length]
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count (approximation)."""
        # Simple approximation: ~4 characters per token on average
        return len(text) // 4
    
    def chunk_text(self, text: str, target_chunk_size: int = None) -> List[str]:
        """
        Split text into chunks suitable for TTS processing.
        
        Args:
            text: Input text to chunk
            target_chunk_size: Target number of tokens per chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        target_size = target_chunk_size or self.max_chunk_tokens
        
        # Clean the text first
        clean_text = self.clean_text(text)
        
        # If text is small enough, return as single chunk
        if self.estimate_tokens(clean_text) <= target_size:
            return [clean_text]
        
        # Split into sentences
        sentences = self.split_into_sentences(clean_text)
        
        if not sentences:
            return [clean_text]
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)
            
            # If adding this sentence would exceed the target, finalize current chunk
            if current_tokens + sentence_tokens > target_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Handle very long sentences that exceed target size
        final_chunks = []
        for chunk in chunks:
            if self.estimate_tokens(chunk) > target_size * 1.5:
                # Split long chunk by words
                words = chunk.split()
                word_chunks = []
                current_words = []
                current_tokens = 0
                
                for word in words:
                    word_tokens = self.estimate_tokens(word)
                    if current_tokens + word_tokens > target_size and current_words:
                        word_chunks.append(' '.join(current_words))
                        current_words = [word]
                        current_tokens = word_tokens
                    else:
                        current_words.append(word)
                        current_tokens += word_tokens
                
                if current_words:
                    word_chunks.append(' '.join(current_words))
                
                final_chunks.extend(word_chunks)
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def prepare_for_tts(self, text: str, voice: str = None) -> Tuple[str, List[str]]:
        """
        Prepare text for TTS processing.
        
        Args:
            text: Input text
            voice: Voice to use
            
        Returns:
            Tuple of (cleaned_full_text, chunks)
        """
        voice = voice or settings.default_voice
        
        # Clean the text
        cleaned_text = self.clean_text(text)
        
        if not cleaned_text:
            return "", []
        
        # Create chunks
        chunks = self.chunk_text(cleaned_text)
        
        logger.info(f"Processed text into {len(chunks)} chunks for voice '{voice}'")
        for i, chunk in enumerate(chunks):
            logger.debug(f"Chunk {i+1}: {chunk[:50]}{'...' if len(chunk) > 50 else ''}")
        
        return cleaned_text, chunks
    
    def create_micro_chunks(self, text: str, words_per_chunk: int = 15) -> List[str]:
        """
        Create micro-chunks for faster Groq API responses.
        
        Args:
            text: Input text
            words_per_chunk: Number of words per chunk (default: 15 for faster responses)
            
        Returns:
            List of micro-chunks
        """
        if not text:
            return []
        
        # Clean the text first
        cleaned_text = self.clean_text(text)
        
        # Split into words
        words = cleaned_text.split()
        
        if len(words) <= words_per_chunk:
            return [cleaned_text]
        
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            
            # Check if we should end this chunk
            should_end_chunk = (
                len(current_chunk) >= words_per_chunk or
                word.endswith('.') or
                word.endswith('!') or
                word.endswith('?') or
                word.endswith(':')
            )
            
            if should_end_chunk and len(current_chunk) >= 3:  # Minimum chunk size
                chunk_text = ' '.join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                current_chunk = []
        
        # Add any remaining words
        if current_chunk:
            chunk_text = ' '.join(current_chunk).strip()
            if chunk_text:
                # If it's too short, combine with last chunk
                if len(chunks) > 0 and len(current_chunk) < 3:
                    chunks[-1] += ' ' + chunk_text
                else:
                    chunks.append(chunk_text)
        
        logger.info(f"Created {len(chunks)} micro-chunks from text")
        return chunks


# Global text processor instance
text_processor = TextProcessor()