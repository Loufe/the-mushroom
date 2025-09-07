#!/usr/bin/env python3
"""
Wisps Pattern - Magical firefly/wisp effect with gentle pulses
Creates a living field of blue-white lights that fade in and out organically
"""

import numpy as np
import random
import time
from dataclasses import dataclass
from typing import Dict, Any, Set
from .base import Pattern
from .registry import PatternRegistry
from effects.colors import hsv_to_rgb


@dataclass
class Firefly:
    """Single firefly with lifecycle parameters"""
    active: bool = False
    position: int = -1
    birth_time: float = 0.0
    fade_in_time: float = 2.0
    peak_time: float = 0.2
    fade_out_time: float = 1.5
    max_brightness: float = 0.5
    hue: float = 210.0
    saturation: float = 0.5
    
    def reset(self, position: int, current_time: float, **params):
        """Reset firefly for reuse from pool"""
        self.active = True
        self.position = position
        self.birth_time = current_time
        for key, value in params.items():
            setattr(self, key, value)


@PatternRegistry.register("wisps")
class Wisps(Pattern):
    """Magical wisp/firefly pattern with organic light pulses"""
    
    # Density control
    MAX_FIREFLIES = 50
    MIN_ACTIVE = 30
    TARGET_DENSITY = 0.15  # 15% of LEDs active at once
    SPAWN_PROBABILITY = 0.02  # Per frame chance to spawn
    
    # Lifecycle timing ranges (seconds)
    FADE_IN_MIN = 1.0
    FADE_IN_MAX = 3.0
    PEAK_MIN = 0.1
    PEAK_MAX = 0.3
    FADE_OUT_MIN = 1.0
    FADE_OUT_MAX = 2.0
    
    # Brightness ranges (0-1)
    FIREFLY_BRIGHTNESS_MIN = 0.3
    FIREFLY_BRIGHTNESS_MAX = 0.6
    
    # Color ranges (blue-white spectrum)
    HUE_MIN = 200  # Deep blue
    HUE_MAX = 220  # Light blue
    SATURATION_MIN = 0.2  # Allows white mixing
    SATURATION_MAX = 0.8  # Still colorful
    
    def __init__(self, led_count: int, fps: float = 30.0):
        super().__init__(led_count, fps)
        
        # Adjust pool size for small LED counts
        self.pool_size = min(self.MAX_FIREFLIES, led_count // 2)
        
        # Initialize firefly pool
        self.fireflies = [Firefly() for _ in range(self.pool_size)]
        
        # Track occupied LED positions
        self.occupied_positions: Set[int] = set()
        
        # Audio reactivity preparation
        self.audio_boost = 0.0  # 0-1 audio level
    
    def get_default_params(self) -> Dict[str, Any]:
        """Return default parameters for this pattern"""
        return {
            'spawn_rate': self.SPAWN_PROBABILITY,
            'min_active': self.MIN_ACTIVE,
            'target_density': self.TARGET_DENSITY
        }
    
    def should_spawn(self) -> bool:
        """Determine if a new firefly should spawn"""
        active_count = sum(1 for ff in self.fireflies if ff.active)
        
        # Always maintain minimum
        if active_count < self.MIN_ACTIVE:
            return True
        
        # Random spawn up to max, influenced by audio
        if active_count < self.pool_size:
            spawn_chance = self.params['spawn_rate'] * (1.0 + self.audio_boost)
            return random.random() < spawn_chance
        
        return False
    
    def spawn_firefly(self) -> bool:
        """Spawn a new firefly if possible"""
        # Find available positions
        available_positions = set(range(self.led_count)) - self.occupied_positions
        if not available_positions:
            return False
        
        # Find inactive firefly in pool
        for firefly in self.fireflies:
            if not firefly.active:
                # Random position
                position = random.choice(list(available_positions))
                
                # Random parameters for variety
                firefly.reset(
                    position=position,
                    current_time=self.get_time(),
                    fade_in_time=random.uniform(self.FADE_IN_MIN, self.FADE_IN_MAX),
                    peak_time=random.uniform(self.PEAK_MIN, self.PEAK_MAX),
                    fade_out_time=random.uniform(self.FADE_OUT_MIN, self.FADE_OUT_MAX),
                    max_brightness=random.uniform(self.FIREFLY_BRIGHTNESS_MIN, self.FIREFLY_BRIGHTNESS_MAX),
                    hue=random.uniform(self.HUE_MIN, self.HUE_MAX),
                    saturation=random.uniform(self.SATURATION_MIN, self.SATURATION_MAX)
                )
                
                self.occupied_positions.add(position)
                return True
        
        return False
    
    def calculate_brightness(self, firefly: Firefly, current_time: float) -> float:
        """Calculate current brightness based on lifecycle phase"""
        if not firefly.active:
            return 0.0
        
        age = current_time - firefly.birth_time
        
        # Fade in phase
        if age < firefly.fade_in_time:
            progress = age / firefly.fade_in_time
            return progress * firefly.max_brightness
        
        # Peak phase
        age -= firefly.fade_in_time
        if age < firefly.peak_time:
            return firefly.max_brightness
        
        # Fade out phase
        age -= firefly.peak_time
        if age < firefly.fade_out_time:
            progress = 1.0 - (age / firefly.fade_out_time)
            return progress * firefly.max_brightness
        
        # Lifecycle complete
        return 0.0
    
    def is_complete(self, firefly: Firefly, current_time: float) -> bool:
        """Check if firefly lifecycle is complete"""
        if not firefly.active:
            return False
        
        age = current_time - firefly.birth_time
        total_life = firefly.fade_in_time + firefly.peak_time + firefly.fade_out_time
        return age >= total_life
    
    def deactivate_firefly(self, firefly: Firefly):
        """Clean deactivation of a firefly"""
        if firefly.active and firefly.position >= 0:
            self.occupied_positions.discard(firefly.position)
            firefly.active = False
            firefly.position = -1
    
    def update(self, delta_time: float) -> np.ndarray:
        """Update pattern and return pixel colors"""
        current_time = self.get_time()
        
        # Clear pixel buffer
        self.pixels.fill(0)
        
        # Spawn new fireflies if needed
        while self.should_spawn():
            if not self.spawn_firefly():
                break
        
        # Update all active fireflies
        for firefly in self.fireflies:
            if not firefly.active:
                continue
            
            # Check if lifecycle complete
            if self.is_complete(firefly, current_time):
                self.deactivate_firefly(firefly)
                continue
            
            # Calculate brightness with hardware brightness applied
            firefly_brightness = self.calculate_brightness(firefly, current_time)
            final_brightness = firefly_brightness * self.brightness * (1.0 + self.audio_boost * 0.5)
            
            # Convert HSV to RGB
            if final_brightness > 0.001:  # Skip if too dim
                rgb = hsv_to_rgb(
                    np.array([firefly.hue]),
                    firefly.saturation,
                    final_brightness
                )
                self.pixels[firefly.position] = rgb[0]
        
        return self.pixels
    
    def set_audio_level(self, level: float):
        """Set audio reactivity level (0-1) for future use"""
        self.audio_boost = max(0.0, min(1.0, level))
    
    def get_target_density(self) -> int:
        """Get target number of active fireflies based on audio"""
        base = self.params['min_active']
        if self.audio_boost > 0:
            return int(base + (self.pool_size - base) * self.audio_boost)
        return base