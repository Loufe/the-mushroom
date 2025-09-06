#!/usr/bin/env python3
"""
Audio Module - Audio capture and processing for LED patterns
"""

from .device import AudioDevice
from .stream import AudioStream
from .utils import (
    get_volume,
    get_peak,
    get_frequency_bands,
    AudioSmoother,
    BeatDetector,
    normalize_audio
)

__all__ = [
    'AudioDevice', 
    'AudioStream',
    'get_volume',
    'get_peak',
    'get_frequency_bands',
    'AudioSmoother',
    'BeatDetector',
    'normalize_audio'
]