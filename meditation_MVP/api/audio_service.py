import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from fastapi import UploadFile, HTTPException
from database.api_collections import save_session, update_session
from Encoders.audio_encoder import AudioEncoder
from api.constants import sanitize_audio_analysis_results
# from preprocessing_unit.audio_preprocessor import AudioPreprocessor  # Skip for now

class AudioService:
    """Audio processing service for MVP - no external storage dependency"""
    
    def __init__(self):
        self.audio_encoder = AudioEncoder(target_mfcc_dim=20)
        # self.audio_preprocessor = AudioPreprocessor()  # Skip for now
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.flac']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    async def process_audio(self, file: UploadFile, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process uploaded audio file and return analysis results
        
        Args:
            file: Uploaded audio file
            user_id: User ID
            session_id: Optional session ID, creates new if not provided
            
        Returns:
            Dict with session_id and analysis results (no storage URLs)
        """
        
        # Create session if not provided
        if not session_id:
            local_id = str(uuid.uuid4())
            api_session_id = await save_session({
                'id': local_id,
                'user_id': user_id,
                'status': 'processing',
                'input_type': 'audio',
            })
            session_id = api_session_id or local_id
        
        try:
            # Validate file
            self._validate_audio_file(file)
            
            # Process audio immediately in memory
            results = await self._process_audio_in_memory(file, session_id)
            
            return {
                'session_id': session_id,
                'audio_url': f"session://{session_id}/audio",  # Virtual URL for session reference
                'status': 'completed',
                'message': 'Audio processed successfully'
            }
            
        except Exception as e:
            # Update session status on error
            await update_session(session_id, {
                'status': 'failed',
                'error': str(e)
            })
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    
    async def _process_audio_in_memory(self, file: UploadFile, session_id: str) -> Dict[str, Any]:
        """Process audio file entirely in memory without external storage"""
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Save to temporary file for processing
            temp_dir = Path(tempfile.mkdtemp())
            file_extension = Path(file.filename or 'audio.wav').suffix
            temp_audio_path = temp_dir / f"audio_{uuid.uuid4().hex}{file_extension}"
            
            # Write content to temp file
            with open(temp_audio_path, 'wb') as temp_file:
                temp_file.write(file_content)
            
            # Preprocess audio to extract MFCC features
            try:
                mfcc_path = await self._preprocess_audio(temp_audio_path, temp_dir)
            except Exception as e:
                print(f"Error in preprocessing: {e}")
                raise HTTPException(status_code=500, detail=f"Audio preprocessing failed: {str(e)}")
            
            # Encode audio features
            try:
                audio_results = self.audio_encoder.process_mfcc_file(mfcc_path)
                # Sanitize results to remove API-incompatible fields
                audio_results = sanitize_audio_analysis_results(audio_results)
            except Exception as e:
                print(f"Error in encoding: {e}")
                raise HTTPException(status_code=500, detail=f"Audio encoding failed: {str(e)}")
            
            # Update session with results
            await update_session(session_id, {
                'status': 'completed',
                'results': {
                    'audio_analysis': audio_results,
                    'method': 'audio_processing',
                }
            })
            
            # Cleanup temp files
            self._cleanup_temp_files(temp_dir)
            
            return {
                'audio_analysis': audio_results,
                'file_info': {
                    'filename': file.filename,
                    'size_bytes': len(file_content),
                    'content_type': file.content_type
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            # Cleanup on error
            if 'temp_dir' in locals():
                self._cleanup_temp_files(temp_dir)
            
            await update_session(session_id, {
                'status': 'failed',
                'error': str(e)
            })
            print(f"Unexpected error in audio processing: {e}")
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    
    async def _preprocess_audio(self, audio_path: Path, temp_dir: Path) -> Path:
        """
        Preprocess audio file to extract MFCC features
        
        Args:
            audio_path: Path to audio file
            temp_dir: Temporary directory for outputs
            
        Returns:
            Path to generated MFCC .npy file
        """
        
        # Create output directory for MFCC
        mfcc_output_dir = temp_dir / "mfcc_output"
        mfcc_output_dir.mkdir(exist_ok=True)
        
        # Use existing audio preprocessor
        try:
            # Import the process_file function directly
            import sys
            sys.path.append('preprocessing_unit')
            from preprocessing_unit.audio_preprocessor import process_file
            
            # Call process_file directly with our parameters
            process_file(
                input_path=audio_path,
                output_dir=mfcc_output_dir,
                target_sr=22050,
                n_mfcc=20,
                n_mels=80,
                reduce_noise=True,
                save_spectrogram=False
            )
            
            # Find the generated MFCC file
            mfcc_filename = f"{audio_path.stem}_mfcc.npy"
            mfcc_path = mfcc_output_dir / mfcc_filename
            
            if mfcc_path.exists():
                return mfcc_path
            else:
                raise FileNotFoundError(f"MFCC file not generated: {mfcc_path}")
            
        except (ImportError, AttributeError, Exception) as e:
            # Fallback to basic MFCC extraction using librosa directly
            import librosa
            import numpy as np
            
            # Load audio
            y, sr = librosa.load(str(audio_path), sr=22050)
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
            
            # Save MFCC
            mfcc_filename = f"{audio_path.stem}_mfcc.npy"
            mfcc_path = mfcc_output_dir / mfcc_filename
            np.save(mfcc_path, mfcc.T)  # Transpose to [frames, n_mfcc]
            
            return mfcc_path


        mfcc_files = list(mfcc_output_dir.glob("*_mfcc.npy"))
        if not mfcc_files:
            raise ValueError("MFCC extraction failed - no output files generated")
        
        return mfcc_files[0]
    
    def _validate_audio_file(self, file: UploadFile):
        """Validate uploaded audio file"""
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported format. Supported: {', '.join(self.supported_formats)}"
            )
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {self.max_file_size // (1024*1024)}MB"
            )
    
    def _cleanup_temp_files(self, temp_dir: Path):
        """Clean up temporary files and directory"""
        try:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            # Log warning but don't fail the request
            print(f"Warning: Could not clean up temp files: {e}")
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get processing status for a session"""
        from database.api_collections import get_session
        
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            'session_id': session_id,
            'status': session['status'],
            'created_at': session.get('created_at'),
            'has_results': 'results' in session
        }
    
    async def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get results for a completed session"""
        from database.api_collections import get_session
        
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session['status'] == 'processing':
            raise HTTPException(status_code=202, detail="Processing not complete")
        
        if session['status'] == 'failed':
            raise HTTPException(status_code=500, detail=session.get('error', 'Processing failed'))
        
        return {
            'session_id': session_id,
            'status': session['status'],
            'results': session.get('results', {}),
            'file_info': session.get('input_data', {})
        }
    
    async def process_audio_with_diary(self, file: UploadFile, diary_text: str, user_id: str) -> Dict[str, Any]:
        """
        Process audio and combine with diary text for enhanced recommendations
        
        Args:
            file: Audio file
            diary_text: User's diary entry
            user_id: User ID
            
        Returns:
            Combined analysis results
        """
        
        # Process audio
        audio_result = await self.process_audio(file, user_id)
        
        if audio_result['status'] != 'completed':
            return audio_result
        
        # Get enhanced recommendations using both text and audio
        from api.meditation_service import meditation_service
        
        enhanced_recommendations = await meditation_service.get_enhanced_recommendations(
            diary_text=diary_text,
            audio_analysis=audio_result['results']['audio_analysis'],
            user_id=user_id
        )
        
        return {
            'session_id': audio_result['session_id'],
            'status': 'completed',
            'audio_analysis': audio_result['results'],
            'recommendations': enhanced_recommendations['recommendations'],
            'audio_insights': enhanced_recommendations.get('audio_insights', {}),
            'method': 'audio_text_combined'
        }

# Global service instance
audio_service = AudioService()