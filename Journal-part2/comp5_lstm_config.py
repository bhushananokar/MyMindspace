# comp5_lstm_config.py
"""
Simplified Component 5 configuration for pipeline integration
"""
from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class LSTMConfig:
    """Complete LSTM configuration for Component 5"""
    
    @dataclass
    class AstraDBConfig:
        endpoint: str
        token: str
        keyspace: str = "default_keyspace"
        timeout: int = 30
    
    @dataclass
    class GateNetworkConfig:
        input_size: int = 90
        hidden_size: int = 128
        dropout_rate: float = 0.1
    
    @dataclass
    class MemoryConfig:
        forget_threshold: float = 0.3
        input_threshold: float = 0.4
        output_threshold: float = 0.4
        max_context_tokens: int = 2000
        max_memories_per_context: int = 20
    
    astra_db: AstraDBConfig
    gate_network: GateNetworkConfig
    memory: MemoryConfig
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            astra_db=cls.AstraDBConfig(
                endpoint=os.getenv("ASTRA_DB_API_ENDPOINT", ""),
                token=os.getenv("ASTRA_DB_TOKEN", ""),
                keyspace=os.getenv("KEYSPACE", "default_keyspace")
            ),
            gate_network=cls.GateNetworkConfig(),
            memory=cls.MemoryConfig()
        )
