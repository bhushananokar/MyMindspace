"""
SAC Policy Network for emotion adjustment actions
Implements the policy component of Soft Actor-Critic algorithm
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal
import numpy as np
from typing import Tuple, Dict, Optional, List
import logging

from data import RLState, RLAction

logger = logging.getLogger(__name__)


class PolicyNetwork(nn.Module):
    """
    SAC policy network for continuous emotion adjustments
    Outputs mean and log_std for Gaussian policy distribution
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 9,  # 8 emotions + 1 confidence
        hidden_dims: List[int] = [128, 64],
        max_adjustment: float = 0.3,
        log_std_min: float = -20,
        log_std_max: float = 2,
        activation: str = 'relu'
    ):
        """
        Initialize policy network
        
        Args:
            state_dim: Dimension of input state features
            action_dim: Dimension of action space (default 9)
            hidden_dims: List of hidden layer dimensions
            max_adjustment: Maximum emotion adjustment magnitude
            log_std_min: Minimum log standard deviation
            log_std_max: Maximum log standard deviation  
            activation: Activation function ('relu', 'tanh', 'leaky_relu')
        """
        super().__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.max_adjustment = max_adjustment
        self.log_std_min = log_std_min
        self.log_std_max = log_std_max
        
        # Choose activation function
        if activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'tanh':
            self.activation = nn.Tanh()
        elif activation == 'leaky_relu':
            self.activation = nn.LeakyReLU(0.2)
        else:
            raise ValueError(f"Unknown activation: {activation}")
        
        # Build backbone network
        layers = []
        prev_dim = state_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                self.activation,
                nn.BatchNorm1d(hidden_dim),  # Batch norm for stable training
                nn.Dropout(0.1)  # Light dropout to prevent overfitting
            ])
            prev_dim = hidden_dim
        
        self.backbone = nn.Sequential(*layers)
        
        # Separate heads for mean and log_std
        self.mean_head = nn.Linear(prev_dim, action_dim)
        self.log_std_head = nn.Linear(prev_dim, action_dim)
        
        # Initialize weights
        self._init_weights()
        
    def _init_weights(self):
        """Initialize network weights"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                # Xavier initialization for linear layers
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0.0)
        
        # Small initialization for mean head (start near zero adjustments)
        nn.init.uniform_(self.mean_head.weight, -0.1, 0.1)
        nn.init.constant_(self.mean_head.bias, 0.0)
        
        # Initialize log_std head to reasonable values
        nn.init.uniform_(self.log_std_head.weight, -0.1, 0.1)
        nn.init.constant_(self.log_std_head.bias, -1.0)  # Start with low variance
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through policy network
        
        Args:
            state: State tensor [batch_size, state_dim]
            
        Returns:
            mean: Action means [batch_size, action_dim]
            log_std: Action log standard deviations [batch_size, action_dim]
        """
        # Extract features
        features = self.backbone(state)
        
        # Get mean and log_std
        mean = self.mean_head(features)
        log_std = self.log_std_head(features)
        
        # Clamp log_std to prevent numerical issues
        log_std = torch.clamp(log_std, self.log_std_min, self.log_std_max)
        
        # Scale mean to adjustment range using tanh
        mean = torch.tanh(mean) * self.max_adjustment
        
        return mean, log_std
    
    def sample(
        self, 
        state: torch.Tensor, 
        deterministic: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Sample actions from policy distribution
        
        Args:
            state: State tensor [batch_size, state_dim]
            deterministic: If True, return mean action (no noise)
            
        Returns:
            action: Sampled actions [batch_size, action_dim]
            log_prob: Log probabilities [batch_size, 1]
        """
        mean, log_std = self.forward(state)
        
        if deterministic:
            # Return mean action with zero log probability
            return mean, torch.zeros(mean.shape[0], 1, device=mean.device)
        
        # Sample from Gaussian distribution
        std = log_std.exp()
        normal = Normal(mean, std)
        
        # Use reparameterization trick for differentiable sampling
        x_t = normal.rsample()
        
        # Apply tanh squashing to keep actions bounded
        action = torch.tanh(x_t) * self.max_adjustment
        
        # Calculate log probability with change of variables correction
        log_prob = normal.log_prob(x_t)
        
        # Tanh correction: log_prob -= log(1 - tanh^2(x))
        log_prob -= torch.log(1 - (action / self.max_adjustment).pow(2) + 1e-6)
        log_prob = log_prob.sum(dim=1, keepdim=True)
        
        return action, log_prob
    
    def log_prob(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """
        Calculate log probability of given actions
        
        Args:
            state: State tensor [batch_size, state_dim]
            action: Action tensor [batch_size, action_dim]
            
        Returns:
            log_prob: Log probabilities [batch_size, 1]
        """
        mean, log_std = self.forward(state)
        std = log_std.exp()
        
        # Inverse tanh to get pre-squashing values
        action_scaled = action / self.max_adjustment
        # Clamp to prevent numerical issues with arctanh
        action_scaled = torch.clamp(action_scaled, -0.999, 0.999)
        x_t = torch.atanh(action_scaled)
        
        # Calculate log probability
        normal = Normal(mean, std)
        log_prob = normal.log_prob(x_t)
        
        # Apply tanh correction
        log_prob -= torch.log(1 - action_scaled.pow(2) + 1e-6)
        log_prob = log_prob.sum(dim=1, keepdim=True)
        
        return log_prob
    
    def get_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        """
        Get action from numpy state (convenience method)
        
        Args:
            state: State as numpy array
            deterministic: Whether to use deterministic policy
            
        Returns:
            action: Action as numpy array
        """
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            if next(self.parameters()).is_cuda:
                state_tensor = state_tensor.cuda()
            
            action, _ = self.sample(state_tensor, deterministic=deterministic)
            return action.cpu().numpy()[0]
    
    def get_rl_action(self, rl_state: RLState, deterministic: bool = False) -> RLAction:
        """
        Get RLAction from RLState (high-level interface)
        
        Args:
            rl_state: Input state object
            deterministic: Whether to use deterministic policy
            
        Returns:
            action: RLAction object with emotion adjustments
        """
        state_vector = np.array(rl_state.to_vector(), dtype=np.float32)
        action_vector = self.get_action(state_vector, deterministic=deterministic)
        
        return RLAction(
            emotion_adjustments=action_vector[:8].tolist(),
            confidence_modifier=float(action_vector[8])
        )
    
    def entropy(self, state: torch.Tensor) -> torch.Tensor:
        """
        Calculate policy entropy for given states
        
        Args:
            state: State tensor [batch_size, state_dim]
            
        Returns:
            entropy: Policy entropy [batch_size, 1]
        """
        _, log_std = self.forward(state)
        std = log_std.exp()
        
        # Entropy of multivariate Gaussian
        entropy = 0.5 * (torch.log(2 * np.pi * std.pow(2)) + 1).sum(dim=1, keepdim=True)
        
        return entropy
    
    def get_parameters_info(self) -> Dict[str, int]:
        """Get information about network parameters"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'max_adjustment': self.max_adjustment
        }
    
    def save_checkpoint(self, filepath: str, optimizer_state: Optional[Dict] = None):
        """
        Save model checkpoint
        
        Args:
            filepath: Path to save checkpoint
            optimizer_state: Optional optimizer state dict
        """
        checkpoint = {
            'model_state_dict': self.state_dict(),
            'model_config': {
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'max_adjustment': self.max_adjustment,
                'log_std_min': self.log_std_min,
                'log_std_max': self.log_std_max
            }
        }
        
        if optimizer_state is not None:
            checkpoint['optimizer_state_dict'] = optimizer_state
        
        torch.save(checkpoint, filepath)
        logger.info(f"Saved policy checkpoint to {filepath}")
    
    def load_checkpoint(self, filepath: str) -> Optional[Dict]:
        """
        Load model checkpoint
        
        Args:
            filepath: Path to checkpoint file
            
        Returns:
            optimizer_state_dict if present in checkpoint
        """
        checkpoint = torch.load(filepath, map_location=next(self.parameters()).device)
        
        # Load model state
        self.load_state_dict(checkpoint['model_state_dict'])
        
        logger.info(f"Loaded policy checkpoint from {filepath}")
        
        # Return optimizer state if present
        return checkpoint.get('optimizer_state_dict', None)


class PolicyEvaluator:
    """
    Utility class for evaluating policy performance
    """
    
    def __init__(self, policy: PolicyNetwork):
        """
        Initialize policy evaluator
        
        Args:
            policy: Policy network to evaluate
        """
        self.policy = policy
        
    def evaluate_on_states(
        self, 
        states: List[RLState], 
        deterministic: bool = True
    ) -> Dict[str, float]:
        """
        Evaluate policy on a set of states
        
        Args:
            states: List of states to evaluate
            deterministic: Whether to use deterministic policy
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not states:
            return {}
        
        actions = []
        entropies = []
        
        with torch.no_grad():
            for state in states:
                # Get action
                action = self.policy.get_rl_action(state, deterministic=deterministic)
                actions.append(action)
                
                # Calculate entropy
                state_tensor = torch.FloatTensor(state.to_vector()).unsqueeze(0)
                if next(self.policy.parameters()).is_cuda:
                    state_tensor = state_tensor.cuda()
                
                entropy = self.policy.entropy(state_tensor)
                entropies.append(entropy.item())
        
        # Calculate statistics
        emotion_adjustments = [action.emotion_adjustments for action in actions]
        confidence_adjustments = [action.confidence_modifier for action in actions]
        
        return {
            'mean_emotion_adjustment': np.mean([np.mean(np.abs(adj)) for adj in emotion_adjustments]),
            'max_emotion_adjustment': np.max([np.max(np.abs(adj)) for adj in emotion_adjustments]),
            'mean_confidence_adjustment': np.mean(np.abs(confidence_adjustments)),
            'mean_entropy': np.mean(entropies),
            'adjustment_std': np.std([np.mean(adj) for adj in emotion_adjustments]),
            'num_states_evaluated': len(states)
        }
    
    def get_action_distribution(
        self, 
        state: RLState, 
        num_samples: int = 1000
    ) -> Dict[str, np.ndarray]:
        """
        Sample from policy to analyze action distribution
        
        Args:
            state: State to analyze
            num_samples: Number of action samples to draw
            
        Returns:
            Dictionary with action statistics
        """
        state_tensor = torch.FloatTensor(state.to_vector()).unsqueeze(0)
        if next(self.policy.parameters()).is_cuda:
            state_tensor = state_tensor.cuda()
        
        # Repeat state for batch sampling
        state_batch = state_tensor.repeat(num_samples, 1)
        
        with torch.no_grad():
            actions, log_probs = self.policy.sample(state_batch, deterministic=False)
            actions = actions.cpu().numpy()
            log_probs = log_probs.cpu().numpy()
        
        return {
            'emotion_adjustments_mean': np.mean(actions[:, :8], axis=0),
            'emotion_adjustments_std': np.std(actions[:, :8], axis=0),
            'confidence_adjustment_mean': np.mean(actions[:, 8]),
            'confidence_adjustment_std': np.std(actions[:, 8]),
            'mean_log_prob': np.mean(log_probs),
            'action_samples': actions
        }