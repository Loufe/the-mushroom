#!/usr/bin/env python3
"""
LED Controller - Single SPI with parallel pattern generation
Uses 2 pattern threads but single SPI transmission on 700 LEDs
"""

import yaml
import logging
import time
import threading
import numpy as np
from typing import Optional, Dict, Any
from pi5neo import Pi5Neo

logger = logging.getLogger(__name__)


class LEDController:
    """Manages LED strips with parallel pattern generation on single SPI"""
    
    def __init__(self, config_path: str = "config/led_config.yaml"):
        """Initialize LED controller with single SPI channel"""
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise
        
        # Get hardware config - fail fast if missing
        if 'hardware' not in self.config:
            raise ValueError(f"Config missing 'hardware' section in {config_path}")
        hardware_config = self.config['hardware']
        
        if 'spi_device' not in hardware_config:
            raise ValueError("Config missing 'hardware.spi_device'")
        if 'spi_speed_khz' not in hardware_config:
            raise ValueError("Config missing 'hardware.spi_speed_khz'")
        if 'brightness' not in hardware_config:
            raise ValueError("Config missing 'hardware.brightness'")
            
        self.spi_device = hardware_config['spi_device']
        self.spi_speed = hardware_config['spi_speed_khz']
        self.brightness = hardware_config['brightness']
        self._brightness_factor = self.brightness / 255.0
        
        # Get LED counts from config
        if 'strips' not in self.config:
            raise ValueError(f"Config missing 'strips' section in {config_path}")
            
        cap_config = None
        stem_config = None
        for strip in self.config['strips']:
            if strip['id'] == 'cap_exterior':
                cap_config = strip
            elif strip['id'] == 'stem_interior':
                stem_config = strip
        
        if not cap_config or not stem_config:
            raise ValueError("Config must define 'cap_exterior' and 'stem_interior' strips")
        
        self.cap_led_count = cap_config['led_count']
        self.stem_led_count = stem_config['led_count']
        self.total_leds = self.cap_led_count + self.stem_led_count
        
        # Create single SPI instance for all LEDs
        logger.info(f"Initializing single SPI for {self.total_leds} LEDs on {self.spi_device}")
        self.spi = Pi5Neo(
            spi_device=self.spi_device,
            num_leds=self.total_leds,
            spi_speed_khz=self.spi_speed
        )
        
        # Patterns
        self.cap_pattern = None
        self.stem_pattern = None
        
        # Buffers for pattern outputs
        self.cap_buffer = np.zeros((self.cap_led_count, 3), dtype=np.uint8)
        self.stem_buffer = np.zeros((self.stem_led_count, 3), dtype=np.uint8)
        self.cap_buffer_lock = threading.Lock()
        self.stem_buffer_lock = threading.Lock()
        
        # Thread control
        self.running = False
        self.cap_thread = None
        self.stem_thread = None
        self.spi_thread = None
        
        # Frame synchronization
        self.cap_ready = threading.Event()
        self.stem_ready = threading.Event()
        
        # Performance tracking
        self.frames_sent = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        logger.info(f"LED Controller initialized: {self.cap_led_count} cap + {self.stem_led_count} stem = {self.total_leds} total")
    
    def set_cap_pattern(self, pattern):
        """Set pattern for cap LEDs"""
        if self.running:
            raise RuntimeError("Cannot change patterns while running")
        
        if pattern.led_count != self.cap_led_count:
            logger.warning(f"Cap pattern expects {pattern.led_count} LEDs but cap has {self.cap_led_count}")
        
        pattern.set_brightness(self._brightness_factor)
        self.cap_pattern = pattern
    
    def set_stem_pattern(self, pattern):
        """Set pattern for stem LEDs"""
        if self.running:
            raise RuntimeError("Cannot change patterns while running")
        
        if pattern.led_count != self.stem_led_count:
            logger.warning(f"Stem pattern expects {pattern.led_count} LEDs but stem has {self.stem_led_count}")
        
        pattern.set_brightness(self._brightness_factor)
        self.stem_pattern = pattern
    
    def start(self):
        """Start pattern generation and SPI transmission threads"""
        if self.running:
            logger.warning("Controller already running")
            return
        
        if not self.cap_pattern or not self.stem_pattern:
            raise RuntimeError("Both patterns must be set before starting")
        
        logger.info("Starting LED controller")
        self.running = True
        
        # Start pattern generation threads
        self.cap_thread = threading.Thread(target=self._cap_pattern_thread, daemon=True)
        self.stem_thread = threading.Thread(target=self._stem_pattern_thread, daemon=True)
        self.spi_thread = threading.Thread(target=self._spi_thread, daemon=True)
        
        self.cap_thread.start()
        self.stem_thread.start()
        self.spi_thread.start()
        
        logger.info("LED controller started with 3 threads")
    
    def stop(self):
        """Stop all threads and clear LEDs"""
        if not self.running:
            return
        
        logger.info("Stopping LED controller")
        self.running = False
        
        # Signal threads to wake up
        self.cap_ready.set()
        self.stem_ready.set()
        
        # Wait for threads to finish
        if self.cap_thread and self.cap_thread.is_alive():
            self.cap_thread.join(timeout=1.0)
        if self.stem_thread and self.stem_thread.is_alive():
            self.stem_thread.join(timeout=1.0)
        if self.spi_thread and self.spi_thread.is_alive():
            self.spi_thread.join(timeout=1.0)
        
        # Clear LEDs
        self.spi.clear_strip()
        self.spi.update_strip()
        
        logger.info("LED controller stopped")
    
    def set_brightness(self, brightness: int):
        """Set global brightness for all strips"""
        if not 0 <= brightness <= 255:
            logger.warning(f"Brightness {brightness} out of range, clamping to 0-255")
            brightness = max(0, min(255, brightness))
        
        self.brightness = brightness
        self._brightness_factor = brightness / 255.0
        
        if self.cap_pattern:
            self.cap_pattern.set_brightness(self._brightness_factor)
        if self.stem_pattern:
            self.stem_pattern.set_brightness(self._brightness_factor)
        
        logger.info(f"Set global brightness to {brightness}")
    
    def set_cap_brightness(self, brightness: int):
        """Set brightness for cap only"""
        if self.cap_pattern:
            self.cap_pattern.set_brightness(brightness / 255.0)
    
    def set_stem_brightness(self, brightness: int):
        """Set brightness for stem only"""
        if self.stem_pattern:
            self.stem_pattern.set_brightness(brightness / 255.0)
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status of all components"""
        return {
            'running': self.running,
            'cap': {
                'pattern_alive': self.cap_thread.is_alive() if self.cap_thread else False,
                'spi_alive': self.spi_thread.is_alive() if self.spi_thread else False,
                'fps': self.current_fps,
                'frames_generated': 0,
                'pattern_errors': 0,
                'spi_errors': 0
            },
            'stem': {
                'pattern_alive': self.stem_thread.is_alive() if self.stem_thread else False,
                'spi_alive': self.spi_thread.is_alive() if self.spi_thread else False,
                'fps': self.current_fps,
                'frames_generated': 0,
                'pattern_errors': 0,
                'spi_errors': 0
            },
            'total_leds': self.total_leds
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'cap_fps': self.current_fps,
            'stem_fps': self.current_fps,
            'cap_frames': self.frames_sent,
            'stem_frames': self.frames_sent,
            'cap_errors': 0,
            'stem_errors': 0
        }
    
    def cleanup(self):
        """Clean shutdown of all resources"""
        logger.info("Cleaning up LED controller")
        
        # Stop if running
        self.stop()
        
        # Close SPI device
        if hasattr(self.spi, 'spi') and self.spi.spi:
            self.spi.spi.close()
        
        logger.info("LED controller cleanup complete")
    
    def _cap_pattern_thread(self):
        """Thread function for cap pattern generation"""
        logger.debug("Cap pattern thread started")
        
        while self.running:
            try:
                # Generate pattern
                pixels = self.cap_pattern.render()
                
                # Store in buffer
                with self.cap_buffer_lock:
                    self.cap_buffer[:] = pixels
                
                # Signal ready
                self.cap_ready.set()
                
                # Wait a bit before generating next frame
                time.sleep(0.01)  # ~100 FPS generation rate
                
            except Exception as e:
                logger.error(f"Cap pattern error: {e}")
                time.sleep(0.1)
        
        logger.debug("Cap pattern thread exited")
    
    def _stem_pattern_thread(self):
        """Thread function for stem pattern generation"""
        logger.debug("Stem pattern thread started")
        
        while self.running:
            try:
                # Generate pattern
                pixels = self.stem_pattern.render()
                
                # Store in buffer
                with self.stem_buffer_lock:
                    self.stem_buffer[:] = pixels
                
                # Signal ready
                self.stem_ready.set()
                
                # Wait a bit before generating next frame
                time.sleep(0.01)  # ~100 FPS generation rate
                
            except Exception as e:
                logger.error(f"Stem pattern error: {e}")
                time.sleep(0.1)
        
        logger.debug("Stem pattern thread exited")
    
    def _spi_thread(self):
        """Thread function for SPI transmission"""
        logger.debug("SPI thread started")
        
        while self.running:
            try:
                # Wait for both patterns to be ready
                self.cap_ready.wait(timeout=0.1)
                self.stem_ready.wait(timeout=0.1)
                
                if not self.running:
                    break
                
                # Clear ready flags
                self.cap_ready.clear()
                self.stem_ready.clear()
                
                # Get buffers
                with self.cap_buffer_lock:
                    cap_pixels = self.cap_buffer.copy()
                with self.stem_buffer_lock:
                    stem_pixels = self.stem_buffer.copy()
                
                # Load into Pi5Neo
                for i in range(self.cap_led_count):
                    r, g, b = cap_pixels[i]
                    self.spi.set_led_color(i, int(r), int(g), int(b))
                
                for i in range(self.stem_led_count):
                    r, g, b = stem_pixels[i]
                    self.spi.set_led_color(self.cap_led_count + i, int(r), int(g), int(b))
                
                # Transmit
                self.spi.update_strip()
                
                # Update FPS
                self.frames_sent += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.current_fps = self.frames_sent / (current_time - self.last_fps_time)
                    self.frames_sent = 0
                    self.last_fps_time = current_time
                
            except Exception as e:
                logger.error(f"SPI thread error: {e}")
                time.sleep(0.1)
        
        logger.debug("SPI thread exited")