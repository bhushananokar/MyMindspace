"""
PyTorch neural network models for Component 2: RL Emotion Model
Base emotion detector + RL policy/value networks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Dict, Optional
import numpy as np


class EmotionIntensityHead(nn.Module):
    """
    Intensity prediction head for base emotion model
    Takes RoBERTa features and outputs emotion intensities
    """
    def __init__(self, input_dim: int = 768, num_emotions: int = 8):
        super().__init__()
        self.intensity_head = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(), 
            nn.Dropout(0.2),
            nn.Linear(256, num_emotions),
            nn.Sigmoid()  # Output 0-1 intensities
        )
        
    def forward(self, roberta_features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            roberta_features: [batch_size, 768] features from RoBERTa
        Returns:
            emotion_intensities: [batch_size, 8] emotion scores 0-1
        """
        return self.intensity_head(roberta_features)


class PolicyNetwork(nn.Module):
    """
    SAC policy network for RL emotion adjustments
    Takes state features and outputs emotion adjustment actions
    """
    def __init__(
        self, 
        state_dim: int,
        action_dim: int = 9,  # 8 emotions + 1 confidence
        hidden_dims: list = [128, 64],
        max_adjustment: float = 0.3
    ):
        super().__init__()
        self.max_adjustment = max_adjustment
        
        # Build network layers
        layers = []
        prev_dim = state_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_dim = hidden_dim
            
        self.backbone = nn.Sequential(*layers)
        
        # Separate heads for mean and log_std
        self.mean_head = nn.Linear(prev_dim, action_dim)
        self.log_std_head = nn.Linear(prev_dim, action_dim)
        
        # Clamp log_std to reasonable range
        self.log_std_min = -20
        self.log_std_max = 2
        
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            state: [batch_size, state_dim] state features
        Returns:
            mean: [batch_size, action_dim] action means
            log_std: [batch_size, action_dim] action log stds
        """
        features = self.backbone(state)
        
        mean = self.mean_head(features)
        log_std = self.log_std_head(features)
        
        # Clamp log_std and scale mean
        log_std = torch.clamp(log_std, self.log_std_min, self.log_std_max)
        mean = torch.tanh(mean) * self.max_adjustment  # Scale to [-0.3, 0.3]
        
        return mean, log_std
    
    def sample(self, state: torch.Tensor, deterministic: bool = False) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Sample actions from the policy
        
        Args:
            state: [batch_size, state_dim] state features  
            deterministic: If True, return mean action
        Returns:
            action: [batch_size, action_dim] sampled actions
            log_prob: [batch_size, 1] log probabilities
        """
        mean, log_std = self.forward(state)
        
        if deterministic:
            return mean, torch.zeros_like(mean[:, :1])
            
        std = log_std.exp()
        normal = torch.distributions.Normal(mean, std)
        
        # Reparameterization trick
        x_t = normal.rsample()  
        action = torch.tanh(x_t) * self.max_adjustment
        
        # Calculate log probability with tanh correction
        log_prob = normal.log_prob(x_t)
        log_prob -= torch.log(1 - action.pow(2) + 1e-6)
        log_prob = log_prob.sum(dim=1, keepdim=True)
        
        return action, log_prob


class QNetwork(nn.Module):
    """
    Q-value network for SAC critic
    Takes state-action pairs and outputs Q-values
    """
    def __init__(
        self, 
        state_dim: int, 
        action_dim: int = 9,
        hidden_dims: list = [256, 128]
    ):
        super().__init__()
        
        # Build network
        layers = []
        prev_dim = state_dim + action_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_dim = hidden_dim
            
        layers.append(nn.Linear(prev_dim, 1))  # Single Q-value output
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """
        Args:
            state: [batch_size, state_dim] state features
            action: [batch_size, action_dim] actions
        Returns:
            q_value: [batch_size, 1] Q-values
        """
        x = torch.cat([state, action], dim=1)
        return self.network(x)


class DoubleQNetwork(nn.Module):
    """
    Twin Q-networks for SAC (reduces overestimation bias)
    """
    def __init__(self, state_dim: int, action_dim: int = 9, hidden_dims: list = [256, 128]):
        super().__init__()
        self.q1 = QNetwork(state_dim, action_dim, hidden_dims)
        self.q2 = QNetwork(state_dim, action_dim, hidden_dims)
        
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns Q-values from both networks
        """
        return self.q1(state, action), self.q2(state, action)
    
    def q1_forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """Forward pass through Q1 only (for policy updates)"""
        return self.q1(state, action)


class SACAgent(nn.Module):
    """
    Complete SAC agent combining policy and value networks
    Handles the full RL emotion adjustment process
    """
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 9,
        policy_hidden_dims: list = [128, 64],
        value_hidden_dims: list = [256, 128],
        learning_rate: float = 3e-4,
        tau: float = 0.005,
        gamma: float = 0.99,
        alpha: float = 0.2,
        device: str = 'cpu'
    ):
        super().__init__()
        self.device = device
        self.gamma = gamma
        self.tau = tau
        self.alpha = alpha
        
        # Networks
        self.policy = PolicyNetwork(state_dim, action_dim, policy_hidden_dims)
        self.q_network = DoubleQNetwork(state_dim, action_dim, value_hidden_dims)
        self.target_q_network = DoubleQNetwork(state_dim, action_dim, value_hidden_dims)
        
        # Copy parameters to target networks
        self.update_target_networks(tau=1.0)
        
        # Optimizers
        self.policy_optimizer = torch.optim.Adam(self.policy.parameters(), lr=learning_rate)
        self.q_optimizer = torch.optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Move to device
        self.to(device)
        
    def get_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        """
        Get action from current policy
        
        Args:
            state: State features as numpy array
            deterministic: Whether to use deterministic policy
        Returns:
            action: Action as numpy array
        """
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action, _ = self.policy.sample(state_tensor, deterministic)
            return action.cpu().numpy()[0]
    
    def update_target_networks(self, tau: Optional[float] = None):
        """Soft update target networks"""
        tau = tau or self.tau
        
        for target_param, param in zip(self.target_q_network.parameters(), self.q_network.parameters()):
            target_param.data.copy_(tau * param.data + (1.0 - tau) * target_param.data)
    
    def train_step(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """
        Single training step
        
        Args:
            batch: Dictionary with 'states', 'actions', 'rewards', 'next_states', 'dones'
        Returns:
            losses: Dictionary of loss values
        """
        states = batch['states'].to(self.device)
        actions = batch['actions'].to(self.device)  
        rewards = batch['rewards'].to(self.device)
        next_states = batch['next_states'].to(self.device)
        dones = batch['dones'].to(self.device)
        
        # Update Q-networks
        with torch.no_grad():
            next_actions, next_log_probs = self.policy.sample(next_states)
            q1_next, q2_next = self.target_q_network(next_states, next_actions)
            q_next = torch.min(q1_next, q2_next) - self.alpha * next_log_probs
            q_target = rewards + (1 - dones) * self.gamma * q_next
            
        q1_current, q2_current = self.q_network(states, actions)
        q1_loss = F.mse_loss(q1_current, q_target)
        q2_loss = F.mse_loss(q2_current, q_target)
        q_loss = q1_loss + q2_loss
        
        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()
        
        # Update policy
        new_actions, log_probs = self.policy.sample(states)
        q1_new = self.q_network.q1_forward(states, new_actions)
        policy_loss = (self.alpha * log_probs - q1_new).mean()
        
        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        self.policy_optimizer.step()
        
        # Update target networks
        self.update_target_networks()
        
        return {
            'q1_loss': q1_loss.item(),
            'q2_loss': q2_loss.item(),
            'policy_loss': policy_loss.item(),
            'mean_q_value': q1_current.mean().item()
        }
    
    def save(self, filepath: str):
        """Save model state"""
        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'q_network_state_dict': self.q_network.state_dict(),
            'target_q_network_state_dict': self.target_q_network.state_dict(),
            'policy_optimizer_state_dict': self.policy_optimizer.state_dict(),
            'q_optimizer_state_dict': self.q_optimizer.state_dict(),
        }, filepath)
    
    def load(self, filepath: str):
        """Load model state"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_q_network.load_state_dict(checkpoint['target_q_network_state_dict'])
        self.policy_optimizer.load_state_dict(checkpoint['policy_optimizer_state_dict'])
        self.q_optimizer.load_state_dict(checkpoint['q_optimizer_state_dict'])