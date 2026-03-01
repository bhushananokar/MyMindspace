"""
Component 2: RL Emotion Model - Models Module
Exports all model classes and factory functions
"""

from .emotion_models import (
    EmotionIntensityHead,
    PolicyNetwork,
    DoubleQNetwork,
    SACAgent
)

def create_sac_agent(
    state_dim: int,
    action_dim: int = 9,
    device: str = 'cpu',
    learning_rate: float = 3e-4,
    gamma: float = 0.99,
    tau: float = 0.005,
    alpha: float = 0.2
):
    """
    Factory function to create SAC agent
    
    Args:
        state_dim: Dimension of state space
        action_dim: Dimension of action space
        device: Device to run on
        learning_rate: Learning rate for optimizers
        gamma: Discount factor
        tau: Soft update coefficient
        alpha: Entropy regularization coefficient
        
    Returns:
        SACAgent instance
    """
    return SACAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        device=device,
        learning_rate=learning_rate,
        gamma=gamma,
        tau=tau,
        alpha=alpha
    )

__all__ = [
    'EmotionIntensityHead',
    'PolicyNetwork', 
    'DoubleQNetwork',
    'SACAgent',
    'create_sac_agent'
]
