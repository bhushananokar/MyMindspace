"""
WebSocket handler for real-time TTS streaming.
"""

import json
import asyncio
import logging
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect
from ..services.audio_generator import audio_generator
from ..config.settings import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for TTS service."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_tasks: Dict[WebSocket, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "data": {
                "message": "Connected to TTS microservice",
                "status": "ready",
                "supported_voices": [settings.default_voice],
                "max_concurrent": settings.max_concurrent_connections
            }
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Handle client disconnection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Cancel any running tasks for this connection
        if websocket in self.connection_tasks:
            task = self.connection_tasks[websocket]
            if not task.done():
                task.cancel()
            del self.connection_tasks[websocket]
        
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


class TTSWebSocketHandler:
    """Handles TTS-specific WebSocket communication."""
    
    def __init__(self):
        self.manager = ConnectionManager()
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle a WebSocket connection lifecycle."""
        await self.manager.connect(websocket)
        
        try:
            while True:
                # Wait for client message with timeout
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(), 
                        timeout=settings.chunk_timeout_seconds
                    )
                    await self.process_message(data, websocket)
                except asyncio.TimeoutError:
                    # Send keepalive ping if no message received
                    await self.manager.send_personal_message({
                        "type": "keepalive",
                        "data": {"timestamp": asyncio.get_event_loop().time()}
                    }, websocket)
                    continue
                
        except WebSocketDisconnect:
            logger.info("Client disconnected normally")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await self.send_error(f"Server error: {str(e)}", websocket)
        finally:
            self.manager.disconnect(websocket)
    
    async def process_message(self, data: str, websocket: WebSocket):
        """Process incoming WebSocket message."""
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            logger.info(f"Received message type: {message_type}")
            
            if message_type == "ping":
                await self.handle_ping(message, websocket)
            
            elif message_type == "text_input":
                await self.handle_text_input(message, websocket)
            
            elif message_type == "cancel_generation":
                await self.handle_cancel_generation(websocket)
            
            elif message_type == "get_status":
                await self.handle_get_status(websocket)
            
            else:
                await self.send_error(f"Unknown message type: {message_type}", websocket)
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format", websocket)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send_error(f"Processing error: {str(e)}", websocket)
    
    async def handle_ping(self, message: Dict[str, Any], websocket: WebSocket):
        """Handle ping message."""
        await self.manager.send_personal_message({
            "type": "pong",
            "data": {
                "timestamp": message.get("data", {}).get("timestamp"),
                "server_time": asyncio.get_event_loop().time()
            }
        }, websocket)
    
    async def handle_text_input(self, message: Dict[str, Any], websocket: WebSocket):
        """Handle text input for TTS generation."""
        data = message.get("data", {})
        text = data.get("text", "").strip()
        
        if not text:
            await self.send_error("Empty text provided", websocket)
            return
        
        # Check connection limit
        if len(self.manager.active_connections) > settings.max_concurrent_connections:
            await self.send_error("Server at capacity, please try again later", websocket)
            return
        
        voice = data.get("voice", settings.default_voice)
        parameters = data.get("parameters", {})
        
        logger.info(f"Starting TTS generation for text: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        # Cancel any existing generation task for this connection
        if websocket in self.manager.connection_tasks:
            old_task = self.manager.connection_tasks[websocket]
            if not old_task.done():
                old_task.cancel()
            # Remove the completed/cancelled task from tracking
            del self.manager.connection_tasks[websocket]
        
        # Start new generation task
        task = asyncio.create_task(
            self.stream_audio_generation(text, voice, parameters, websocket)
        )
        self.manager.connection_tasks[websocket] = task
    
    async def handle_cancel_generation(self, websocket: WebSocket):
        """Handle cancellation of ongoing generation."""
        if websocket in self.manager.connection_tasks:
            task = self.manager.connection_tasks[websocket]
            if not task.done():
                task.cancel()
                await self.manager.send_personal_message({
                    "type": "generation_cancelled",
                    "data": {"message": "Generation cancelled successfully"}
                }, websocket)
            else:
                await self.manager.send_personal_message({
                    "type": "info",
                    "data": {"message": "No active generation to cancel"}
                }, websocket)
        else:
            await self.manager.send_personal_message({
                "type": "info",
                "data": {"message": "No active generation found"}
            }, websocket)
    
    async def handle_get_status(self, websocket: WebSocket):
        """Handle status request."""
        await self.manager.send_personal_message({
            "type": "status",
            "data": {
                "active_connections": len(self.manager.active_connections),
                "max_connections": settings.max_concurrent_connections,
                "model_loaded": audio_generator.is_initialized,
                "default_voice": settings.default_voice
            }
        }, websocket)
    
    async def stream_audio_generation(
        self, 
        text: str, 
        voice: str, 
        parameters: Dict[str, Any], 
        websocket: WebSocket
    ):
        """Stream audio generation results to client."""
        try:
            # Send generation started message
            await self.manager.send_personal_message({
                "type": "generation_started",
                "data": {
                    "text": text,
                    "voice": voice,
                    "parameters": parameters
                }
            }, websocket)
            
            # Stream audio chunks
            async for chunk_data in audio_generator.generate_audio_stream(text, voice, parameters):
                if websocket not in self.manager.active_connections:
                    logger.info("Client disconnected during generation")
                    break
                
                await self.manager.send_personal_message(chunk_data, websocket)
                
                # Send keepalive after each chunk to prevent timeout
                await self.manager.send_personal_message({
                    "type": "keepalive",
                    "data": {"timestamp": asyncio.get_event_loop().time()}
                }, websocket)
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)
            
        except asyncio.CancelledError:
            logger.info("Audio generation cancelled")
            await self.manager.send_personal_message({
                "type": "generation_cancelled",
                "data": {"message": "Generation was cancelled"}
            }, websocket)
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            await self.send_error(f"Generation failed: {str(e)}", websocket)
        finally:
            # Clean up task reference
            if websocket in self.manager.connection_tasks:
                del self.manager.connection_tasks[websocket]
    
    async def send_error(self, message: str, websocket: WebSocket):
        """Send error message to client."""
        await self.manager.send_personal_message({
            "type": "error",
            "data": {
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            }
        }, websocket)


# Global WebSocket handler instance
tts_websocket_handler = TTSWebSocketHandler()