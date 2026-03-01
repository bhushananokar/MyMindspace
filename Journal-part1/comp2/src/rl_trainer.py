"""
RL training coordinator for SAC emotion adjustment models
Handles training loops, experience management, and model updates
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict
import time


from comp2.data import (
    RLExperience, RLState, RLAction, TrainingBatch, 
    UserCalibration, UserFeedback, RewardComponents
)
from comp2.models import SACAgent, create_sac_agent
from .experience_buffer import UserExperienceManager
from .reward_calculator import RewardCalculator
from comp2.utils import load_config

logger = logging.getLogger(__name__)


class TrainingMetrics:
    """Container for training metrics and statistics"""
    
    def __init__(self):
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []
        self.policy_losses: List[float] = []
        self.q_losses: List[float] = []
        self.training_times: List[float] = []
        self.convergence_scores: List[float] = []
        
    def add_episode(self, reward: float, length: int):
        """Add episode metrics"""
        self.episode_rewards.append(reward)
        self.episode_lengths.append(length)
        
    def add_training_step(self, policy_loss: float, q_loss: float, training_time: float):
        """Add training step metrics"""
        self.policy_losses.append(policy_loss)
        self.q_losses.append(q_loss)
        self.training_times.append(training_time)
        
    def get_recent_performance(self, window: int = 50) -> Dict[str, float]:
        """Get recent performance statistics"""
        if not self.episode_rewards:
            return {}
            
        recent_rewards = self.episode_rewards[-window:]
        recent_lengths = self.episode_lengths[-window:]
        recent_policy_losses = self.policy_losses[-window:] if self.policy_losses else [0.0]
        recent_q_losses = self.q_losses[-window:] if self.q_losses else [0.0]
        
        return {
            'mean_reward': np.mean(recent_rewards),
            'std_reward': np.std(recent_rewards),
            'mean_episode_length': np.mean(recent_lengths),
            'mean_policy_loss': np.mean(recent_policy_losses),
            'mean_q_loss': np.mean(recent_q_losses),
            'episodes_trained': len(recent_rewards)
        }


class RLTrainer:
    """
    Main RL training coordinator for SAC emotion adjustment models
    Manages training loops, experience collection, and model updates
    """
    
    def __init__(
        self,
        config_path: str = "config.yaml",
        models_dir: str = "./models/saved_models",
        user_data_dir: str = "./data/user_data",
        device: str = None
    ):
        """
        Initialize RL trainer
        
        Args:
            config_path: Path to configuration file
            models_dir: Directory for saved models
            user_data_dir: Directory for user-specific data  
            device: 'cpu', 'cuda', or None (auto-detect)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.models_dir = Path(models_dir)
        self.user_data_dir = Path(user_data_dir)
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.experience_manager = UserExperienceManager(
            buffer_capacity=self.config.buffer_size,
            use_prioritized=self.config.prioritized_replay,
            storage_dir=str(self.user_data_dir / "experience_buffers")
        )
        
        self.reward_calculator = RewardCalculator()
        
        # User-specific agents and metrics
        self.user_agents: Dict[str, SACAgent] = {}
        self.user_metrics: Dict[str, TrainingMetrics] = defaultdict(TrainingMetrics)
        self.user_calibrations: Dict[str, UserCalibration] = {}
        
        # Training state
        self.training_active = False
        self.global_step = 0
        
        logger.info(f"RL Trainer initialized on {self.device}")
    
    def _get_user_agent(self, user_id: str) -> SACAgent:
        """Get or create SAC agent for user"""
        if user_id not in self.user_agents:
            # Calculate state dimension (from emotion analyzer)
            state_dim = 768 + 20  # Base features + context features
            
            # Create agent
            agent = create_sac_agent(
                state_dim=state_dim,
                device=self.device,
                learning_rate=self.config.learning_rate,
                gamma=self.config.gamma,
                tau=self.config.tau,
                alpha=self.config.alpha
            )
            
            # Try to load existing model
            model_path = self.models_dir / f"user_{user_id}_sac_model.pt"
            if model_path.exists():
                agent.load(str(model_path))
                logger.info(f"Loaded existing SAC model for user {user_id}")
            else:
                logger.info(f"Created new SAC model for user {user_id}")
            
            self.user_agents[user_id] = agent
        
        return self.user_agents[user_id]
    
    def add_experience(
        self,
        user_id: str,
        state: RLState,
        action: RLAction,
        reward: float,
        next_state: Optional[RLState] = None,
        done: bool = False,
        episode_id: Optional[int] = None
    ):
        """
        Add experience to user's replay buffer
        
        Args:
            user_id: User identifier
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state (optional)
            done: Whether episode ended
            episode_id: Episode identifier
        """
        try:
            experience = RLExperience(
                user_id=user_id,
                episode_id=episode_id or 0,
                step_id=self.global_step,
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                done=done,
                priority=abs(reward) + 0.1  # Initial priority based on reward magnitude
            )
            
            self.experience_manager.add_experience(user_id, experience)
            self.global_step += 1
            
            logger.debug(f"Added experience for user {user_id}: reward={reward:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to add experience for user {user_id}: {e}")
    
    def process_user_feedback(
        self,
        feedback: UserFeedback,
        state: RLState,
        action: RLAction
    ) -> bool:
        """
        Process user feedback and add training experience
        
        Args:
            feedback: User feedback data
            state: State when feedback was given
            action: Action that received feedback
            
        Returns:
            Success status
        """
        try:
            # Calculate reward from feedback
            reward_components = self.reward_calculator.calculate_reward(feedback)
            
            # Add experience to replay buffer
            self.add_experience(
                user_id=feedback.user_id,
                state=state,
                action=action,
                reward=reward_components.total_reward,
                done=True  # Feedback marks end of interaction
            )
            
            # Update user calibration
            self._update_user_calibration(feedback.user_id, reward_components)
            
            # Trigger training if enough experiences
            if self._should_trigger_training(feedback.user_id):
                self.train_user_model(feedback.user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process feedback for user {feedback.user_id}: {e}")
            return False
    
    def _should_trigger_training(self, user_id: str) -> bool:
        """Check if user has enough experiences to trigger training"""
        buffer_size = self.experience_manager.get_buffer_size(user_id)
        min_experiences = max(self.config.batch_size * 2, 100)
        
        # Also check if enough time has passed since last training
        calibration = self.user_calibrations.get(user_id)
        if calibration and calibration.last_updated:
            time_since_update = datetime.now() - calibration.last_updated
            min_time_passed = time_since_update > timedelta(hours=1)
        else:
            min_time_passed = True
        
        return buffer_size >= min_experiences and min_time_passed
    
    def train_user_model(
        self,
        user_id: str,
        num_updates: int = None,
        save_after_training: bool = True
    ) -> Dict[str, float]:
        """
        Train SAC model for specific user
        
        Args:
            user_id: User identifier
            num_updates: Number of training updates (default from config)
            save_after_training: Whether to save model after training
            
        Returns:
            Training metrics dictionary
        """
        if self.training_active:
            logger.warning(f"Training already active, skipping user {user_id}")
            return {}
        
        try:
            self.training_active = True
            start_time = time.time()
            
            # Get user's agent and check if training is possible
            agent = self._get_user_agent(user_id)
            buffer_size = self.experience_manager.get_buffer_size(user_id)
            
            if buffer_size < self.config.batch_size:
                logger.warning(f"Insufficient experiences for user {user_id}: {buffer_size}")
                return {}
            
            num_updates = num_updates or self.config.update_frequency
            metrics = self.user_metrics[user_id]
            training_losses = []
            
            logger.info(f"Starting training for user {user_id}: {num_updates} updates")
            
            # Training loop
            for update_step in range(num_updates):
                # Sample batch from experience buffer
                batch = self.experience_manager.sample_batch(user_id, self.config.batch_size)
                
                if batch is None:
                    logger.warning(f"Could not sample batch for user {user_id}")
                    break
                
                # Convert to tensors
                batch_tensors = self._prepare_batch_tensors(batch)
                
                # Train agent
                losses = agent.train_step(batch_tensors)
                training_losses.append(losses)
                
                # Update priorities for prioritized replay
                if self.config.prioritized_replay:
                    td_errors = self._calculate_td_errors(agent, batch_tensors)
                    self.experience_manager.update_priorities(user_id, batch, td_errors)
                
                # Log progress
                if (update_step + 1) % 10 == 0:
                    avg_policy_loss = np.mean([l['policy_loss'] for l in training_losses[-10:]])
                    avg_q_loss = np.mean([l['q1_loss'] + l['q2_loss'] for l in training_losses[-10:]])
                    logger.debug(f"User {user_id} - Update {update_step + 1}/{num_updates}: "
                               f"Policy Loss: {avg_policy_loss:.4f}, Q Loss: {avg_q_loss:.4f}")
            
            # Calculate training statistics
            total_time = time.time() - start_time
            
            if training_losses:
                avg_policy_loss = np.mean([l['policy_loss'] for l in training_losses])
                avg_q_loss = np.mean([l['q1_loss'] + l['q2_loss'] for l in training_losses])
                
                # Update metrics
                metrics.add_training_step(avg_policy_loss, avg_q_loss, total_time)
            
            # Update user calibration
            self._update_training_metrics(user_id, training_losses, total_time)
            
            # Save model if requested
            if save_after_training:
                self._save_user_model(user_id)
            
            logger.info(f"Training completed for user {user_id}: "
                       f"{len(training_losses)} updates in {total_time:.2f}s")
            
            return {
                'updates_completed': len(training_losses),
                'training_time': total_time,
                'avg_policy_loss': avg_policy_loss if training_losses else 0.0,
                'avg_q_loss': avg_q_loss if training_losses else 0.0,
                'buffer_size': buffer_size
            }
            
        except Exception as e:
            logger.error(f"Training failed for user {user_id}: {e}")
            return {}
        
        finally:
            self.training_active = False
    
    def _prepare_batch_tensors(self, batch: TrainingBatch) -> Dict[str, torch.Tensor]:
        """Convert training batch to PyTorch tensors"""
        batch_data = batch.to_tensors()
        
        return {
            'states': torch.FloatTensor(batch_data['states']).to(self.device),
            'actions': torch.FloatTensor(batch_data['actions']).to(self.device),
            'rewards': torch.FloatTensor(batch_data['rewards']).unsqueeze(1).to(self.device),
            'next_states': torch.FloatTensor(batch_data['next_states']).to(self.device),
            'dones': torch.FloatTensor(batch_data['dones']).unsqueeze(1).to(self.device),
            'weights': torch.FloatTensor(batch_data['weights']).to(self.device) if batch.weights else None
        }
    
    def _calculate_td_errors(self, agent: SACAgent, batch_tensors: Dict[str, torch.Tensor]) -> List[float]:
        """Calculate TD errors for prioritized replay"""
        with torch.no_grad():
            states = batch_tensors['states']
            actions = batch_tensors['actions']
            rewards = batch_tensors['rewards']
            next_states = batch_tensors['next_states']
            dones = batch_tensors['dones']
            
            # Current Q values
            q1_current, q2_current = agent.q_network(states, actions)
            q_current = torch.min(q1_current, q2_current)
            
            # Target Q values
            next_actions, next_log_probs = agent.policy.sample(next_states)
            q1_next, q2_next = agent.target_q_network(next_states, next_actions)
            q_next = torch.min(q1_next, q2_next) - agent.alpha * next_log_probs
            q_target = rewards + (1 - dones) * agent.gamma * q_next
            
            # Calculate TD errors
            td_errors = torch.abs(q_current - q_target)
            
        return td_errors.cpu().numpy().flatten().tolist()
    
    def _update_user_calibration(self, user_id: str, reward_components: RewardComponents):
        """Update user's calibration metrics"""
        if user_id not in self.user_calibrations:
            self.user_calibrations[user_id] = UserCalibration(user_id=user_id)
        
        calibration = self.user_calibrations[user_id]
        calibration.feedback_count += 1
        calibration.reward_history.append(reward_components.total_reward)
        
        # Keep only recent rewards
        if len(calibration.reward_history) > 1000:
            calibration.reward_history = calibration.reward_history[-1000:]
        
        calibration.avg_reward = np.mean(calibration.reward_history)
        calibration.last_updated = datetime.now()
        
        # Calculate accuracy improvement (simplified)
        if len(calibration.reward_history) >= 50:
            recent_avg = np.mean(calibration.reward_history[-25:])
            older_avg = np.mean(calibration.reward_history[-50:-25])
            calibration.accuracy_improvement = recent_avg - older_avg
    
    def _update_training_metrics(self, user_id: str, training_losses: List[Dict], training_time: float):
        """Update training metrics for user"""
        calibration = self.user_calibrations[user_id]
        
        if training_losses:
            # Update loss history
            avg_policy_loss = np.mean([l['policy_loss'] for l in training_losses])
            avg_q_loss = np.mean([l['q1_loss'] + l['q2_loss'] for l in training_losses])
            
            calibration.policy_loss_history.append(avg_policy_loss)
            calibration.value_loss_history.append(avg_q_loss)
            
            # Keep only recent history
            if len(calibration.policy_loss_history) > 100:
                calibration.policy_loss_history = calibration.policy_loss_history[-100:]
            if len(calibration.value_loss_history) > 100:
                calibration.value_loss_history = calibration.value_loss_history[-100:]
        
        calibration.training_episodes += 1
        calibration.total_experiences = self.experience_manager.get_buffer_size(user_id)
    
    def _save_user_model(self, user_id: str):
        """Save user's trained model"""
        try:
            if user_id in self.user_agents:
                model_path = self.models_dir / f"user_{user_id}_sac_model.pt"
                self.user_agents[user_id].save(str(model_path))
                logger.info(f"Saved model for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to save model for user {user_id}: {e}")
    
    def batch_train_users(
        self, 
        user_ids: List[str], 
        max_concurrent: int = 3
    ) -> Dict[str, Dict[str, float]]:
        """
        Train multiple users in batches
        
        Args:
            user_ids: List of users to train
            max_concurrent: Maximum concurrent training sessions
            
        Returns:
            Dictionary mapping user_id to training metrics
        """
        results = {}
        
        # Process users in batches to limit resource usage
        for i in range(0, len(user_ids), max_concurrent):
            batch_users = user_ids[i:i + max_concurrent]
            
            logger.info(f"Training batch {i//max_concurrent + 1}: {batch_users}")
            
            # Train each user in the batch
            for user_id in batch_users:
                if self._should_trigger_training(user_id):
                    metrics = self.train_user_model(user_id)
                    results[user_id] = metrics
                else:
                    logger.info(f"Skipping training for user {user_id} - insufficient data")
        
        return results
    
    def get_user_training_stats(self, user_id: str) -> Dict[str, any]:
        """Get comprehensive training statistics for user"""
        calibration = self.user_calibrations.get(user_id)
        metrics = self.user_metrics.get(user_id)
        buffer_stats = self.experience_manager.get_user_stats(user_id)
        
        if not calibration:
            return {'error': 'No calibration data found'}
        
        stats = {
            'calibration': {
                'training_episodes': calibration.training_episodes,
                'total_experiences': calibration.total_experiences,
                'avg_reward': calibration.avg_reward,
                'accuracy_improvement': calibration.accuracy_improvement,
                'feedback_count': calibration.feedback_count,
                'last_updated': calibration.last_updated.isoformat() if calibration.last_updated else None
            },
            'buffer_stats': buffer_stats
        }
        
        if metrics:
            recent_performance = metrics.get_recent_performance()
            stats['recent_performance'] = recent_performance
        
        return stats
    
    def cleanup_user_data(self, user_id: str):
        """Clean up all data for user (privacy compliance)"""
        try:
            # Remove from memory
            if user_id in self.user_agents:
                del self.user_agents[user_id]
            
            if user_id in self.user_calibrations:
                del self.user_calibrations[user_id]
            
            if user_id in self.user_metrics:
                del self.user_metrics[user_id]
            
            # Clean up experience buffer
            self.experience_manager.cleanup_user_data(user_id)
            
            # Remove saved model
            model_path = self.models_dir / f"user_{user_id}_sac_model.pt"
            if model_path.exists():
                model_path.unlink()
            
            logger.info(f"Cleaned up all training data for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup data for user {user_id}: {e}")
    
    def save_all_models(self):
        """Save all user models"""
        for user_id in self.user_agents.keys():
            self._save_user_model(user_id)
    
    def get_global_training_stats(self) -> Dict[str, any]:
        """Get overall training statistics across all users"""
        total_users = len(self.user_calibrations)
        active_users = sum(1 for cal in self.user_calibrations.values() 
                          if cal.last_updated and 
                          datetime.now() - cal.last_updated < timedelta(days=7))
        
        total_experiences = sum(cal.total_experiences for cal in self.user_calibrations.values())
        total_episodes = sum(cal.training_episodes for cal in self.user_calibrations.values())
        
        avg_reward = np.mean([cal.avg_reward for cal in self.user_calibrations.values()]) if self.user_calibrations else 0.0
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_experiences': total_experiences,
            'total_training_episodes': total_episodes,
            'avg_reward_across_users': avg_reward,
            'global_training_steps': self.global_step,
            'device': self.device
        }