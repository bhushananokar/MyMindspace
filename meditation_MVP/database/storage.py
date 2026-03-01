import io
import uuid
from pathlib import Path
from typing import Optional, Union, BinaryIO
from datetime import datetime, timedelta
import mimetypes

from firebase_admin import storage
from fastapi import UploadFile, HTTPException
from database.firebase_client import get_storage_bucket

class FirebaseStorage:
    """Firebase Cloud Storage operations for meditation app"""
    
    def __init__(self):
        self.bucket = get_storage_bucket()
        
        # Supported file types
        self.audio_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg', 
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg'
        }
        
        self.image_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        
        self.document_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json'
        }
        
        # File size limits (in bytes)
        self.max_audio_size = 100 * 1024 * 1024  # 100MB
        self.max_image_size = 10 * 1024 * 1024   # 10MB
        self.max_document_size = 5 * 1024 * 1024  # 5MB

    async def upload_audio_file(self, 
                               file: Union[UploadFile, BinaryIO, bytes], 
                               destination_path: str,
                               metadata: Optional[dict] = None) -> str:
        """
        Upload audio file to Firebase Storage
        
        Args:
            file: Audio file to upload
            destination_path: Storage path (e.g., 'sessions/session_123/audio')
            metadata: Optional metadata to store with file
            
        Returns:
            Public download URL
        """
        
        # Handle different file input types
        if isinstance(file, UploadFile):
            filename = file.filename or f"audio_{uuid.uuid4().hex}.wav"
            content = await file.read()
            content_type = file.content_type
        elif isinstance(file, (BinaryIO, io.BytesIO)):
            filename = f"audio_{uuid.uuid4().hex}.wav"
            content = file.read()
            content_type = 'audio/wav'
        elif isinstance(file, bytes):
            filename = f"audio_{uuid.uuid4().hex}.wav"
            content = file
            content_type = 'audio/wav'
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Validate file
        self._validate_audio_file(filename, content, content_type)
        
        # Generate storage path
        file_extension = Path(filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        full_path = f"{destination_path.rstrip('/')}/{unique_filename}"
        
        # Upload file
        return await self._upload_file(
            content=content,
            storage_path=full_path,
            content_type=content_type,
            metadata=metadata
        )

    async def upload_image_file(self,
                               file: Union[UploadFile, BinaryIO, bytes],
                               destination_path: str,
                               metadata: Optional[dict] = None) -> str:
        """
        Upload image file to Firebase Storage
        
        Args:
            file: Image file to upload
            destination_path: Storage path (e.g., 'users/user_123/profile')
            metadata: Optional metadata to store with file
            
        Returns:
            Public download URL
        """
        
        # Handle different file input types
        if isinstance(file, UploadFile):
            filename = file.filename or f"image_{uuid.uuid4().hex}.png"
            content = await file.read()
            content_type = file.content_type
        elif isinstance(file, (BinaryIO, io.BytesIO)):
            filename = f"image_{uuid.uuid4().hex}.png"
            content = file.read()
            content_type = 'image/png'
        elif isinstance(file, bytes):
            filename = f"image_{uuid.uuid4().hex}.png"
            content = file
            content_type = 'image/png'
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Validate file
        self._validate_image_file(filename, content, content_type)
        
        # Generate storage path
        file_extension = Path(filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        full_path = f"{destination_path.rstrip('/')}/{unique_filename}"
        
        # Upload file
        return await self._upload_file(
            content=content,
            storage_path=full_path,
            content_type=content_type,
            metadata=metadata
        )

    async def upload_document_file(self,
                                  file: Union[UploadFile, BinaryIO, bytes],
                                  destination_path: str,
                                  metadata: Optional[dict] = None) -> str:
        """
        Upload document file to Firebase Storage
        
        Args:
            file: Document file to upload
            destination_path: Storage path (e.g., 'documents/reports')
            metadata: Optional metadata to store with file
            
        Returns:
            Public download URL
        """
        
        # Handle different file input types
        if isinstance(file, UploadFile):
            filename = file.filename or f"document_{uuid.uuid4().hex}.pdf"
            content = await file.read()
            content_type = file.content_type
        elif isinstance(file, (BinaryIO, io.BytesIO)):
            filename = f"document_{uuid.uuid4().hex}.pdf"
            content = file.read()
            content_type = 'application/pdf'
        elif isinstance(file, bytes):
            filename = f"document_{uuid.uuid4().hex}.pdf"
            content = file
            content_type = 'application/pdf'
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Validate file
        self._validate_document_file(filename, content, content_type)
        
        # Generate storage path
        file_extension = Path(filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        full_path = f"{destination_path.rstrip('/')}/{unique_filename}"
        
        # Upload file
        return await self._upload_file(
            content=content,
            storage_path=full_path,
            content_type=content_type,
            metadata=metadata
        )

    async def _upload_file(self,
                          content: bytes,
                          storage_path: str,
                          content_type: str,
                          metadata: Optional[dict] = None) -> str:
        """
        Internal method to upload file to Firebase Storage
        
        Args:
            content: File content as bytes
            storage_path: Full storage path
            content_type: MIME type
            metadata: File metadata
            
        Returns:
            Public download URL
        """
        
        try:
            # Create blob reference
            blob = self.bucket.blob(storage_path)
            
            # Set metadata
            if metadata:
                blob.metadata = metadata
            
            # Upload file
            blob.upload_from_string(
                data=content,
                content_type=content_type
            )
            
            # Make file publicly accessible
            blob.make_public()
            
            # Return public URL
            return blob.public_url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def download_file(self, storage_path: str) -> bytes:
        """
        Download file from Firebase Storage
        
        Args:
            storage_path: Full storage path
            
        Returns:
            File content as bytes
        """
        
        try:
            blob = self.bucket.blob(storage_path)
            
            if not blob.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            return blob.download_as_bytes()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from Firebase Storage
        
        Args:
            storage_path: Full storage path
            
        Returns:
            True if successful
        """
        
        try:
            blob = self.bucket.blob(storage_path)
            
            if blob.exists():
                blob.delete()
            
            return True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

    async def generate_signed_url(self,
                                 storage_path: str,
                                 expiration_minutes: int = 60) -> str:
        """
        Generate signed URL for private file access
        
        Args:
            storage_path: Full storage path
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Signed URL
        """
        
        try:
            blob = self.bucket.blob(storage_path)
            
            if not blob.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            # Generate signed URL
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            signed_url = blob.generate_signed_url(expiration=expiration)
            
            return signed_url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Signed URL generation failed: {str(e)}")

    async def list_files(self,
                        prefix: str = "",
                        max_results: int = 100) -> list:
        """
        List files in storage with optional prefix filter
        
        Args:
            prefix: Path prefix to filter by
            max_results: Maximum number of results
            
        Returns:
            List of file information
        """
        
        try:
            blobs = self.bucket.list_blobs(prefix=prefix, max_results=max_results)
            
            file_list = []
            for blob in blobs:
                file_info = {
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'content_type': blob.content_type,
                    'public_url': blob.public_url,
                    'metadata': blob.metadata or {}
                }
                file_list.append(file_info)
            
            return file_list
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"List files failed: {str(e)}")

    async def get_file_info(self, storage_path: str) -> dict:
        """
        Get file information and metadata
        
        Args:
            storage_path: Full storage path
            
        Returns:
            File information dictionary
        """
        
        try:
            blob = self.bucket.blob(storage_path)
            
            if not blob.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            # Reload to get latest metadata
            blob.reload()
            
            return {
                'name': blob.name,
                'size': blob.size,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'content_type': blob.content_type,
                'public_url': blob.public_url,
                'metadata': blob.metadata or {},
                'md5_hash': blob.md5_hash,
                'etag': blob.etag
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Get file info failed: {str(e)}")

    def _validate_audio_file(self, filename: str, content: bytes, content_type: str):
        """Validate audio file"""
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.audio_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported: {', '.join(self.audio_types.keys())}"
            )
        
        # Check content type
        expected_type = self.audio_types[file_ext]
        if content_type and content_type not in [expected_type, 'audio/*']:
            # Allow some flexibility in content type detection
            if not content_type.startswith('audio/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid content type. Expected audio file, got {content_type}"
                )
        
        # Check file size
        if len(content) > self.max_audio_size:
            size_mb = self.max_audio_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Maximum size: {size_mb:.1f}MB"
            )
        
        # Check minimum file size (avoid empty files)
        if len(content) < 1024:  # 1KB minimum
            raise HTTPException(status_code=400, detail="Audio file appears to be empty or corrupted")

    def _validate_image_file(self, filename: str, content: bytes, content_type: str):
        """Validate image file"""
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format. Supported: {', '.join(self.image_types.keys())}"
            )
        
        # Check content type
        expected_type = self.image_types[file_ext]
        if content_type and content_type not in [expected_type, 'image/*']:
            if not content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid content type. Expected image file, got {content_type}"
                )
        
        # Check file size
        if len(content) > self.max_image_size:
            size_mb = self.max_image_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"Image file too large. Maximum size: {size_mb:.1f}MB"
            )
        
        # Check minimum file size
        if len(content) < 100:  # 100 bytes minimum
            raise HTTPException(status_code=400, detail="Image file appears to be empty or corrupted")

    def _validate_document_file(self, filename: str, content: bytes, content_type: str):
        """Validate document file"""
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.document_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported document format. Supported: {', '.join(self.document_types.keys())}"
            )
        
        # Check content type
        expected_type = self.document_types[file_ext]
        if content_type and content_type != expected_type:
            # Allow some flexibility for common cases
            if file_ext == '.txt' and content_type.startswith('text/'):
                pass  # Accept any text type
            elif file_ext == '.json' and 'json' in content_type:
                pass  # Accept variants of JSON type
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid content type. Expected {expected_type}, got {content_type}"
                )
        
        # Check file size
        if len(content) > self.max_document_size:
            size_mb = self.max_document_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"Document file too large. Maximum size: {size_mb:.1f}MB"
            )
        
        # Check minimum file size
        if len(content) < 10:  # 10 bytes minimum
            raise HTTPException(status_code=400, detail="Document file appears to be empty")

# Global storage instance
firebase_storage = FirebaseStorage()

# Convenience functions that match the expected interface
async def upload_audio_file(file: Union[UploadFile, BinaryIO, bytes], 
                           destination_path: str,
                           metadata: Optional[dict] = None) -> str:
    """Upload audio file to Firebase Storage"""
    return await firebase_storage.upload_audio_file(file, destination_path, metadata)

async def upload_image_file(file: Union[UploadFile, BinaryIO, bytes],
                           destination_path: str,
                           metadata: Optional[dict] = None) -> str:
    """Upload image file to Firebase Storage"""
    return await firebase_storage.upload_image_file(file, destination_path, metadata)

async def download_file(storage_path: str) -> bytes:
    """Download file from Firebase Storage"""
    return await firebase_storage.download_file(storage_path)

async def delete_file(storage_path: str) -> bool:
    """Delete file from Firebase Storage"""
    return await firebase_storage.delete_file(storage_path)

async def get_file_info(storage_path: str) -> dict:
    """Get file information"""
    return await firebase_storage.get_file_info(storage_path)