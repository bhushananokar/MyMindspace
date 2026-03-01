"""
Experience replay buffer for RL training with prioritized sampling
Stores and samples state-action-reward experiences for SAC training
"""

import numpy as np
import random
from typing import List, Dict, Tuple, Optional, Union
from collections import deque
import heapq
import pickle
from pathlib import Path
import logging
from datetime import datetime

from comp2.data import RLExperience, TrainingBatch, RLState, RLAction

logger = logging.getLogger(__name__)


class SumTree:
    """
    Sum tree data structure for efficient prioritized sampling
    Used internally by PrioritizedExperienceBuffer
    """
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity - 1)
        self.data = np.zeros(capacity, dtype=object)
        self.write = 0
        self.n_entries = 0
    
    def _propagate(self, idx: int, change: float):
        """Update tree with new priority values"""
        parent = (idx - 1) // 2
        self.tree[parent] += change
        
        if parent != 0:
            self._propagate(parent, change)
    
    def _retrieve(self, idx: int, s: float) -> int:
        """Retrieve sample index based on priority"""
        left = 2 * idx + 1
        right = left + 1
        
        if left >= len(self.tree):
            return idx
        
        if s <= self.tree[left]:
            return self._retrieve(left, s)
        else:
            return self._retrieve(right, s - self.tree[left])
    
    def total(self) -> float:
        """Get total priority sum"""
        return self.tree[0]
    
    def add(self, priority: float, data) -> int:
        """Add new experience with priority"""
        idx = self.write + self.capacity - 1
        
        self.data[self.write] = data
        self.update(idx, priority)
        
        self.write += 1
        if self.write >= self.capacity:
            self.write = 0
        
        if self.n_entries < self.capacity:
            self.n_entries += 1
            
        return self.write
    
    def update(self, idx: int, priority: float):
        """Update priority of existing experience"""
        change = priority - self.tree[idx]
        self.tree[idx] = priority
        self._propagate(idx, change)
    
    def get(self, s: float) -> Tuple[int, float, any]:
        """Get experience by priority sampling value"""
        idx = self._retrieve(0, s)
        data_idx = idx - self.capacity + 1
        return (idx, self.tree[idx], self.data[data_idx])


class ExperienceBuffer:
    """
    Basic experience replay buffer
    FIFO storage with uniform random sampling
    """
    
    def __init__(self, capacity: int = 10000):
        """
        Initialize experience buffer
        
        Args:
            capacity: Maximum number of experiences to store
        """
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.position = 0
    
    def add(self, experience: RLExperience):
        """Add new experience to buffer"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
            self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int) -> Optional[TrainingBatch]:
        """
        Sample batch of experiences
        
        Args:
            batch_size: Number of experiences to sample
            
        Returns:
            Training batch or None if insufficient data
        """
        if len(self.buffer) < batch_size:
            return None
        
        experiences = random.sample(list(self.buffer), batch_size)
        return TrainingBatch(experiences=experiences, batch_size=batch_size)
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
    
    def clear(self):
        """Clear all experiences"""
        self.buffer.clear()
        self.position = 0


class PrioritizedExperienceBuffer:
    """
    Prioritized experience replay buffer
    Samples experiences based on TD error priorities
    """
    
    def __init__(
        self,
        capacity: int = 10000,
        alpha: float = 0.6,
        beta: float = 0.4,
        beta_increment: float = 0.001,
        epsilon: float = 1e-6
    ):
        """
        Initialize prioritized experience buffer
        
        Args:
            capacity: Maximum number of experiences
            alpha: Prioritization exponent (0=uniform, 1=full priority)
            beta: Importance sampling exponent  
            beta_increment: Beta increase per sample
            epsilon: Small constant to avoid zero priorities
        """
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment
        self.epsilon = epsilon
        
        self.tree = SumTree(capacity)
        self.max_priority = 1.0
    
    def add(self, experience: RLExperience):
        """
        Add experience with maximum priority
        
        Args:
            experience: RL experience to store
        """
        priority = self.max_priority ** self.alpha
        self.tree.add(priority, experience)
    
    def sample(self, batch_size: int) -> Optional[TrainingBatch]:
        """
        Sample batch with prioritized sampling
        
        Args:
            batch_size: Number of experiences to sample
            
        Returns:
            Training batch with importance weights
        """
        if self.tree.n_entries < batch_size:
            return None
        
        experiences = []
        weights = []
        indices = []
        
        # Calculate segment size for stratified sampling
        segment = self.tree.total() / batch_size
        
        # Update beta
        self.beta = np.min([1.0, self.beta + self.beta_increment])
        
        # Sample experiences
        for i in range(batch_size):
            a = segment * i
            b = segment * (i + 1)
            s = random.uniform(a, b)
            
            idx, priority, experience = self.tree.get(s)
            
            # Calculate importance sampling weight
            prob = priority / self.tree.total()
            weight = (self.tree.n_entries * prob) ** (-self.beta)
            
            experiences.append(experience)
            weights.append(weight)
            indices.append(idx)
        
        # Normalize weights
        max_weight = max(weights)
        weights = [w / max_weight for w in weights]
        
        batch = TrainingBatch(
            experiences=experiences,
            batch_size=batch_size,
            weights=weights
        )
        
        # Store indices for priority updates
        batch._indices = indices  # Private attribute for priority updates
        
        return batch
    
    def update_priorities(self, batch: TrainingBatch, td_errors: List[float]):
        """
        Update priorities based on TD errors
        
        Args:
            batch: Training batch from sample()
            td_errors: List of TD errors for priority calculation
        """
        if not hasattr(batch, '_indices'):
            logger.warning("Batch missing indices for priority update")
            return
        
        for idx, td_error in zip(batch._indices, td_errors):
            priority = (abs(td_error) + self.epsilon) ** self.alpha
            self.max_priority = max(self.max_priority, priority)
            self.tree.update(idx, priority)
    
    def size(self) -> int:
        """Get current buffer size"""
        return self.tree.n_entries
    
    def clear(self):
        """Clear all experiences"""
        self.tree = SumTree(self.capacity)
        self.max_priority = 1.0


class UserExperienceManager:
    """
    Manages experience buffers for multiple users
    Handles persistence and user-specific replay buffers
    """
    
    def __init__(
        self,
        buffer_capacity: int = 10000,
        use_prioritized: bool = True,
        storage_dir: str = "./data/user_data/experience_buffers",
        auto_save_interval: int = 100  # Save every 100 experiences
    ):
        """
        Initialize user experience manager
        
        Args:
            buffer_capacity: Size of each user's buffer
            use_prioritized: Whether to use prioritized replay
            storage_dir: Directory to save experience buffers
            auto_save_interval: Experiences between auto-saves
        """
        self.buffer_capacity = buffer_capacity
        self.use_prioritized = use_prioritized
        self.storage_dir = Path(storage_dir)
        self.auto_save_interval = auto_save_interval
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # User buffers
        self.user_buffers: Dict[str, Union[ExperienceBuffer, PrioritizedExperienceBuffer]] = {}
        self.experience_counts: Dict[str, int] = {}
        
    def _create_buffer(self) -> Union[ExperienceBuffer, PrioritizedExperienceBuffer]:
        """Create new experience buffer"""
        if self.use_prioritized:
            return PrioritizedExperienceBuffer(capacity=self.buffer_capacity)
        else:
            return ExperienceBuffer(capacity=self.buffer_capacity)
    
    def _get_user_buffer(self, user_id: str) -> Union[ExperienceBuffer, PrioritizedExperienceBuffer]:
        """Get or create buffer for user"""
        if user_id not in self.user_buffers:
            self.user_buffers[user_id] = self._create_buffer()
            self.experience_counts[user_id] = 0
            
            # Try to load existing buffer
            self._load_user_buffer(user_id)
        
        return self.user_buffers[user_id]
    
    def add_experience(self, user_id: str, experience: RLExperience):
        """
        Add experience for user
        
        Args:
            user_id: User identifier
            experience: Experience to add
        """
        buffer = self._get_user_buffer(user_id)
        buffer.add(experience)
        
        self.experience_counts[user_id] += 1
        
        # Auto-save periodically
        if self.experience_counts[user_id] % self.auto_save_interval == 0:
            self._save_user_buffer(user_id)
    
    def sample_batch(self, user_id: str, batch_size: int) -> Optional[TrainingBatch]:
        """
        Sample training batch for user
        
        Args:
            user_id: User identifier  
            batch_size: Size of batch to sample
            
        Returns:
            Training batch or None if insufficient data
        """
        buffer = self._get_user_buffer(user_id)
        return buffer.sample(batch_size)
    
    def update_priorities(
        self, 
        user_id: str, 
        batch: TrainingBatch, 
        td_errors: List[float]
    ):
        """
        Update experience priorities (for prioritized buffers only)
        
        Args:
            user_id: User identifier
            batch: Training batch
            td_errors: TD errors for priority calculation
        """
        buffer = self._get_user_buffer(user_id)
        if isinstance(buffer, PrioritizedExperienceBuffer):
            buffer.update_priorities(batch, td_errors)
    
    def get_buffer_size(self, user_id: str) -> int:
        """Get size of user's experience buffer"""
        buffer = self._get_user_buffer(user_id)
        return buffer.size()
    
    def clear_user_buffer(self, user_id: str):
        """Clear user's experience buffer"""
        if user_id in self.user_buffers:
            self.user_buffers[user_id].clear()
            self.experience_counts[user_id] = 0
    
    def _save_user_buffer(self, user_id: str):
        """Save user's experience buffer to disk"""
        try:
            if user_id not in self.user_buffers:
                return
            
            buffer_file = self.storage_dir / f"user_{user_id}_buffer.pkl"
            
            # Convert experiences to serializable format
            buffer = self.user_buffers[user_id]
            if isinstance(buffer, PrioritizedExperienceBuffer):
                # Extract experiences from sum tree
                experiences = []
                for i in range(buffer.tree.n_entries):
                    if buffer.tree.data[i] is not None:
                        experiences.append(buffer.tree.data[i])
            else:
                experiences = list(buffer.buffer)
            
            # Save to file
            with open(buffer_file, 'wb') as f:
                pickle.dump({
                    'experiences': experiences,
                    'use_prioritized': self.use_prioritized,
                    'capacity': self.buffer_capacity,
                    'timestamp': datetime.now().isoformat()
                }, f)
                
            logger.debug(f"Saved buffer for user {user_id}: {len(experiences)} experiences")
            
        except Exception as e:
            logger.error(f"Failed to save buffer for user {user_id}: {e}")
    
    def _load_user_buffer(self, user_id: str):
        """Load user's experience buffer from disk"""
        try:
            buffer_file = self.storage_dir / f"user_{user_id}_buffer.pkl"
            
            if not buffer_file.exists():
                return
            
            with open(buffer_file, 'rb') as f:
                data = pickle.load(f)
            
            experiences = data.get('experiences', [])
            
            # Add experiences to buffer
            buffer = self.user_buffers[user_id]
            for exp in experiences:
                buffer.add(exp)
            
            logger.debug(f"Loaded buffer for user {user_id}: {len(experiences)} experiences")
            
        except Exception as e:
            logger.error(f"Failed to load buffer for user {user_id}: {e}")
    
    def save_all_buffers(self):
        """Save all user buffers"""
        for user_id in self.user_buffers.keys():
            self._save_user_buffer(user_id)
    
    def cleanup_user_data(self, user_id: str):
        """Remove user's experience data"""
        try:
            # Remove from memory
            if user_id in self.user_buffers:
                del self.user_buffers[user_id]
            
            if user_id in self.experience_counts:
                del self.experience_counts[user_id]
            
            # Remove file
            buffer_file = self.storage_dir / f"user_{user_id}_buffer.pkl"
            if buffer_file.exists():
                buffer_file.unlink()
                
            logger.info(f"Cleaned up experience data for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup experience data for user {user_id}: {e}")
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get statistics for user's experience buffer"""
        buffer = self._get_user_buffer(user_id)
        
        return {
            'buffer_size': buffer.size(),
            'buffer_capacity': self.buffer_capacity,
            'total_experiences': self.experience_counts.get(user_id, 0),
            'buffer_type': 'prioritized' if self.use_prioritized else 'uniform',
            'utilization': buffer.size() / self.buffer_capacity
        }