#!/usr/bin/env python3
"""
Audio Utilities - Helper functions for audio-reactive patterns
Simple tools that patterns can optionally use for audio processing
"""

import numpy as np
from typing import Optional, Tuple


def get_volume(audio_data: np.ndarray, gain: float = 1.0) -> float:
    """
    Get normalized volume level from audio data
    
    Args:
        audio_data: Raw audio samples
        gain: Software gain multiplier (default 1.0)
        
    Returns:
        Volume level 0.0-1.0 (clipped)
    """
    if audio_data is None or len(audio_data) == 0:
        return 0.0
    
    # Calculate RMS (Root Mean Square) for perceived loudness
    rms = np.sqrt(np.mean(audio_data**2))
    
    # Apply gain and clip to 0-1 range
    volume = rms * gain
    return np.clip(volume, 0.0, 1.0)


def get_peak(audio_data: np.ndarray, gain: float = 1.0) -> float:
    """
    Get peak level from audio data
    
    Args:
        audio_data: Raw audio samples
        gain: Software gain multiplier
        
    Returns:
        Peak level 0.0-1.0
    """
    if audio_data is None or len(audio_data) == 0:
        return 0.0
    
    peak = np.max(np.abs(audio_data)) * gain
    return np.clip(peak, 0.0, 1.0)


def get_frequency_bands(audio_data: np.ndarray, sample_rate: int = 44100, 
                        gain: float = 1.0) -> Tuple[float, float, float]:
    """
    Get basic frequency band levels (bass, mid, treble)
    
    Args:
        audio_data: Raw audio samples
        sample_rate: Sample rate in Hz
        gain: Software gain multiplier
        
    Returns:
        Tuple of (bass, mid, treble) levels, each 0.0-1.0
    """
    if audio_data is None or len(audio_data) == 0:
        return (0.0, 0.0, 0.0)
    
    # Simple FFT to get frequency content
    fft = np.fft.rfft(audio_data)
    freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
    magnitudes = np.abs(fft)
    
    # Define frequency ranges (Hz)
    bass_range = (20, 250)
    mid_range = (250, 2000)
    treble_range = (2000, 8000)
    
    # Calculate average magnitude in each range
    bass_mask = (freqs >= bass_range[0]) & (freqs < bass_range[1])
    mid_mask = (freqs >= mid_range[0]) & (freqs < mid_range[1])
    treble_mask = (freqs >= treble_range[0]) & (freqs < treble_range[1])
    
    bass = np.mean(magnitudes[bass_mask]) if np.any(bass_mask) else 0.0
    mid = np.mean(magnitudes[mid_mask]) if np.any(mid_mask) else 0.0
    treble = np.mean(magnitudes[treble_mask]) if np.any(treble_mask) else 0.0
    
    # Normalize and apply gain
    # Note: These scaling factors may need tuning based on actual audio
    bass = np.clip(bass * gain * 0.01, 0.0, 1.0)
    mid = np.clip(mid * gain * 0.01, 0.0, 1.0)
    treble = np.clip(treble * gain * 0.01, 0.0, 1.0)
    
    return (bass, mid, treble)


class AudioSmoother:
    """Simple exponential smoothing for audio values"""
    
    def __init__(self, smoothing: float = 0.8):
        """
        Initialize smoother
        
        Args:
            smoothing: 0.0 = no smoothing, 0.99 = heavy smoothing
        """
        self.smoothing = np.clip(smoothing, 0.0, 0.99)
        self.value = 0.0
    
    def update(self, new_value: float) -> float:
        """
        Update with new value and return smoothed result
        
        Args:
            new_value: New value to incorporate
            
        Returns:
            Smoothed value
        """
        self.value = self.smoothing * self.value + (1 - self.smoothing) * new_value
        return self.value
    
    def reset(self):
        """Reset smoother to zero"""
        self.value = 0.0


class BeatDetector:
    """Simple beat detector using volume threshold"""
    
    def __init__(self, threshold: float = 1.3, cooldown: int = 5):
        """
        Initialize beat detector
        
        Args:
            threshold: Multiplier above average to trigger beat
            cooldown: Frames to wait before next beat
        """
        self.threshold = threshold
        self.cooldown = cooldown
        self.cooldown_counter = 0
        self.history = []
        self.history_size = 30  # Frames of history to keep
    
    def detect(self, volume: float) -> bool:
        """
        Detect if current frame is a beat
        
        Args:
            volume: Current volume level (0-1)
            
        Returns:
            True if beat detected
        """
        # Add to history
        self.history.append(volume)
        if len(self.history) > self.history_size:
            self.history.pop(0)
        
        # Need enough history
        if len(self.history) < 10:
            return False
        
        # Check cooldown
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            return False
        
        # Compare to recent average
        avg = np.mean(self.history[:-1])  # Exclude current
        
        # Beat if current is significantly above average
        if volume > avg * self.threshold and volume > 0.1:
            self.cooldown_counter = self.cooldown
            return True
        
        return False
    
    def reset(self):
        """Reset detector state"""
        self.history.clear()
        self.cooldown_counter = 0


def normalize_audio(audio_data: np.ndarray, target_level: float = 0.5) -> np.ndarray:
    """
    Normalize audio data to target level
    
    Args:
        audio_data: Raw audio samples
        target_level: Target RMS level (0-1)
        
    Returns:
        Normalized audio data
    """
    if audio_data is None or len(audio_data) == 0:
        return audio_data
    
    current_rms = np.sqrt(np.mean(audio_data**2))
    
    if current_rms > 0:
        scale = target_level / current_rms
        return np.clip(audio_data * scale, -1.0, 1.0)
    
    return audio_data