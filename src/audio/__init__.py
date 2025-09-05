#!/usr/bin/env python3
"""
Audio Module - Audio capture and processing for LED patterns
"""

from .device import AudioDevice
from .stream import AudioStream

__all__ = ['AudioDevice', 'AudioStream']