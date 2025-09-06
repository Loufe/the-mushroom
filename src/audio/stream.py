#!/usr/bin/env python3
"""
Audio Stream - Simple wrapper around sounddevice for audio capture
"""

import sounddevice as sd
import numpy as np
import logging
import time
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AudioStatus:
    """Current audio stream status"""
    is_active: bool
    sample_rate: int
    buffer_size: int
    device_name: str
    current_level: float  # 0-1 RMS level
    peak_level: float     # 0-1 peak
    frames_read: int      # Total frames read
    uptime: float        # Seconds since started


class AudioStream:
    """Simple audio capture using sounddevice's internal buffering"""
    
    def __init__(self, config: dict):
        """
        Initialize audio stream
        
        Args:
            config: Dictionary with audio settings
        """
        # Configuration
        self.sample_rate = config.get('sample_rate', 44100)
        self.buffer_size = config.get('buffer_size', 512)
        self.device_id = config.get('device_id', None)
        self.gain = config.get('gain', 1.0)  # Software gain multiplier
        
        # Signal monitoring
        self.current_level = 0.0
        self.peak_level = 0.0
        self.peak_decay = 0.95
        
        # Statistics
        self.frames_read = 0
        self.start_time = None
        
        # Cache for last valid audio
        self.last_audio = np.zeros(self.buffer_size, dtype=np.float32)
        
        # Stream handle
        self.stream = None
        self.device_info = {}
        
        logger.info(f"Audio stream configured: {self.sample_rate}Hz, {self.buffer_size} samples")
    
    def start(self) -> bool:
        """
        Start audio stream
        
        Returns:
            True if successful
        """
        try:
            # Get device info
            if self.device_id is not None:
                self.device_info = sd.query_devices(self.device_id, 'input')
            else:
                self.device_info = sd.query_devices(kind='input')
            
            # Create stream WITHOUT callback (uses internal buffering)
            self.stream = sd.InputStream(
                device=self.device_id,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                dtype=np.float32
            )
            
            self.stream.start()
            self.start_time = time.time()
            
            logger.info(f"Audio stream started on '{self.device_info['name']}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            return False
    
    def read_latest(self) -> Optional[np.ndarray]:
        """
        Non-blocking read of latest audio data
        
        Returns:
            Audio data or None if no new data
        """
        if not self.stream or not self.stream.active:
            return self.last_audio
        
        try:
            # Non-blocking read - get available data
            available = self.stream.read_available
            if available > 0:
                # Read available frames (may be more or less than buffer_size)
                audio_data, overflowed = self.stream.read(available)
                
                if overflowed:
                    logger.debug("Audio buffer overflow detected")
                
                # Flatten to mono if needed
                if audio_data.ndim > 1:
                    audio_data = audio_data[:, 0]
                
                # Apply gain if needed
                if self.gain != 1.0:
                    audio_data = np.clip(audio_data * self.gain, -1.0, 1.0)
                
                # Update statistics
                self.frames_read += len(audio_data)
                
                # Calculate signal levels (after gain)
                self.current_level = float(np.sqrt(np.mean(audio_data**2)))
                peak = float(np.max(np.abs(audio_data)))
                self.peak_level = max(peak, self.peak_level * self.peak_decay)
                
                # Cache the audio
                if len(audio_data) >= self.buffer_size:
                    # Take last buffer_size samples if we got more
                    self.last_audio = audio_data[-self.buffer_size:].copy()
                else:
                    # Pad with zeros if we got less
                    self.last_audio[:len(audio_data)] = audio_data
                    self.last_audio[len(audio_data):] = 0
                
                return self.last_audio
            else:
                # No new data available, return cached
                return self.last_audio
                
        except Exception as e:
            logger.error(f"Error reading audio stream: {e}")
            return self.last_audio
    
    def stop(self):
        """Stop audio stream"""
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                logger.info("Audio stream stopped")
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self.stream = None
    
    def get_status(self) -> AudioStatus:
        """Get current stream status"""
        device_name = self.device_info.get('name', 'None')
        
        return AudioStatus(
            is_active=self.stream is not None and self.stream.active,
            sample_rate=self.sample_rate,
            buffer_size=self.buffer_size,
            device_name=device_name,
            current_level=self.current_level,
            peak_level=self.peak_level,
            frames_read=self.frames_read,
            uptime=time.time() - self.start_time if self.start_time else 0
        )
    
    def reset_peak(self):
        """Reset peak level meter"""
        self.peak_level = 0.0
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop()