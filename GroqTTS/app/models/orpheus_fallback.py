"""
Orpheus TTS Model wrapper with singleton pattern for efficient memory management.
"""

import asyncio
import torch
import numpy as np
import soundfile as sf
from typing import List, Optional, Union
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login, snapshot_download
from snac import SNAC
import logging
import base64
import io

from ..config.settings import settings

logger = logging.getLogger(__name__)


class OrpheusModel:
    """Singleton TTS model wrapper for Orpheus 3B."""
    
    _instance: Optional['OrpheusModel'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.model = None
            self.tokenizer = None
            self.snac_model = None
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Initializing OrpheusModel on device: {self._device}")
    
    async def initialize(self):
        """Initialize the model, tokenizer, and SNAC codec."""
        if self._initialized:
            logger.info("Model already initialized")
            return
        
        try:
            logger.info("Starting model initialization...")
            
            # Login to Hugging Face if token provided
            if settings.hf_token:
                login(token=settings.hf_token)
                logger.info("Logged in to Hugging Face")
            
            # Load SNAC model (keep on CPU to save GPU memory)
            logger.info("Loading SNAC model...")
            self.snac_model = SNAC.from_pretrained(settings.snac_model_name)
            self.snac_model = self.snac_model.to("cpu")
            logger.info("SNAC model loaded successfully")
            
            # Download Orpheus model files
            logger.info(f"Downloading model files for {settings.model_name}...")
            model_path = snapshot_download(
                repo_id=settings.model_name,
                allow_patterns=[
                    "config.json",
                    "*.safetensors",
                    "model.safetensors.index.json",
                ],
                ignore_patterns=[
                    "optimizer.pt",
                    "pytorch_model.bin",
                    "training_args.bin",
                    "scheduler.pt",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "special_tokens_map.json",
                    "vocab.json",
                    "merges.txt",
                    "tokenizer.*"
                ]
            )
            
            # Load main model
            logger.info("Loading Orpheus model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.model_name, 
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )
            logger.info("Orpheus model loaded successfully")
            
            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(settings.model_name)
            logger.info("Tokenizer loaded successfully")
            
            self._initialized = True
            logger.info("Model initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    def _prepare_input(self, text: str, voice: str = None) -> torch.Tensor:
        """Prepare input text for the model."""
        voice = voice or settings.default_voice
        prompt = f"{voice}: {text}"
        
        # Tokenize
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
        
        # Add special tokens
        start_token = torch.tensor([[128259]], dtype=torch.int64)  # Start of human
        end_tokens = torch.tensor([[128009, 128260]], dtype=torch.int64)  # End of text, End of human
        
        # Combine tokens
        modified_input_ids = torch.cat([start_token, input_ids, end_tokens], dim=1)
        
        # Add padding token
        padding_token = 128263
        padded_input_ids = torch.cat([
            torch.full((1, 1), padding_token, dtype=torch.int64), 
            modified_input_ids
        ], dim=1)
        
        # Create attention mask
        attention_mask = torch.cat([
            torch.zeros((1, 1), dtype=torch.int64),
            torch.ones((1, modified_input_ids.shape[1]), dtype=torch.int64)
        ], dim=1)
        
        return padded_input_ids.to(self._device), attention_mask.to(self._device)
    
    def _redistribute_codes(self, code_list: List[int]) -> torch.Tensor:
        """Convert audio codes back to audio using SNAC."""
        layer_1 = []
        layer_2 = []
        layer_3 = []
        
        for i in range((len(code_list) + 1) // 7):
            if 7 * i >= len(code_list):
                break
            
            layer_1.append(code_list[7 * i])
            
            if 7 * i + 1 < len(code_list):
                layer_2.append(code_list[7 * i + 1] - 4096)
            if 7 * i + 2 < len(code_list):
                layer_3.append(code_list[7 * i + 2] - (2 * 4096))
            if 7 * i + 3 < len(code_list):
                layer_3.append(code_list[7 * i + 3] - (3 * 4096))
            if 7 * i + 4 < len(code_list):
                layer_2.append(code_list[7 * i + 4] - (4 * 4096))
            if 7 * i + 5 < len(code_list):
                layer_3.append(code_list[7 * i + 5] - (5 * 4096))
            if 7 * i + 6 < len(code_list):
                layer_3.append(code_list[7 * i + 6] - (6 * 4096))
        
        # Create code tensors for SNAC (on CPU)
        codes = [
            torch.tensor(layer_1).unsqueeze(0).to("cpu"),
            torch.tensor(layer_2).unsqueeze(0).to("cpu"),
            torch.tensor(layer_3).unsqueeze(0).to("cpu")
        ]
        
        # Generate audio
        audio_hat = self.snac_model.decode(codes)
        return audio_hat
    
    def _generate_tokens_sync(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        max_tokens: int,
        temperature: float,
        top_p: float,
        repetition_penalty: float
    ) -> torch.Tensor:
        """Synchronous token generation for running in background thread."""
        with torch.no_grad():
            return self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                num_return_sequences=1,
                eos_token_id=128258,
            )

    async def generate_audio(
        self,
        text: str,
        voice: str = None,
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        repetition_penalty: float = None
    ) -> np.ndarray:
        """Generate audio from text."""
        if not self._initialized:
            await self.initialize()

        # Use provided parameters or defaults
        max_tokens = max_tokens or settings.max_new_tokens
        temperature = temperature or settings.temperature
        top_p = top_p or settings.top_p
        repetition_penalty = repetition_penalty or settings.repetition_penalty

        try:
            # Prepare input
            input_ids, attention_mask = self._prepare_input(text, voice)

            # Generate tokens in background thread to prevent blocking
            generated_ids = await asyncio.to_thread(
                self._generate_tokens_sync,
                input_ids,
                attention_mask,
                max_tokens,
                temperature,
                top_p,
                repetition_penalty
            )            # Parse audio tokens
            token_to_find = 128257
            token_to_remove = 128258
            
            # Find speech tokens
            token_indices = (generated_ids == token_to_find).nonzero(as_tuple=True)
            
            if len(token_indices[1]) > 0:
                last_occurrence_idx = token_indices[1][-1].item()
                cropped_tensor = generated_ids[:, last_occurrence_idx + 1:]
            else:
                cropped_tensor = generated_ids
            
            # Remove end tokens
            processed_rows = []
            for row in cropped_tensor:
                masked_row = row[row != token_to_remove]
                processed_rows.append(masked_row)
            
            # Convert to code lists
            code_lists = []
            for row in processed_rows:
                row_length = row.size(0)
                new_length = (row_length // 7) * 7
                trimmed_row = row[:new_length]
                trimmed_row = [t.item() - 128266 for t in trimmed_row]
                code_lists.append(trimmed_row)
            
            # Generate audio from codes
            if code_lists and len(code_lists[0]) > 0:
                audio_samples = self._redistribute_codes(code_lists[0])
                audio_data = audio_samples.detach().squeeze().to("cpu").numpy()
                
                # Clear GPU memory
                torch.cuda.empty_cache()
                
                return audio_data
            else:
                logger.warning("No valid audio codes generated")
                return np.array([])
                
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            torch.cuda.empty_cache()  # Clean up even on error
            raise
    
    def audio_to_base64(self, audio_data: np.ndarray) -> str:
        """Convert audio numpy array to base64 encoded string."""
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, settings.sample_rate, format='WAV')
        buffer.seek(0)
        audio_bytes = buffer.read()
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def cleanup(self):
        """Clean up GPU memory."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("GPU memory cleaned up")


# Global model instance
tts_model = OrpheusModel()