#!/usr/bin/env python3
"""
Strip Controller - Manages a single LED strip with parallel pattern generation and SPI transmission
"""

import threading
import time
import numpy as np
import logging
from typing import Optional
from pi5neo import Pi5Neo

logger = logging.getLogger(__name__)


class StripController:
    """Controls a single LED strip with dedicated pattern and SPI threads"""
    
    def __init__(self, name: str, strip_config: dict, hardware_config: dict):
        """
        Initialize strip controller
        
        Args:
            name: Strip identifier (e.g., 'cap', 'stem')
            strip_config: Strip configuration from YAML
            hardware_config: Hardware settings from YAML
        """
        self.name = name
        self.strip_id = strip_config['id']
        self.spi_device = strip_config['spi_device']
        self.led_count = strip_config['led_count']
        self.led_start = strip_config['led_start']
        self.led_end = strip_config['led_end']
        
        # Hardware settings
        self.spi_speed = hardware_config.get('spi_speed_khz', 800)
        self.brightness = hardware_config.get('brightness', 128)
        self._brightness_factor = self.brightness / 255.0
        
        # Pattern (will be set later)
        self.pattern = None
        
        # Buffer for double-buffering
        self.buffer = None
        self.buffer_lock = threading.Lock()
        
        # Thread coordination events
        self.can_generate = threading.Event()
        self.can_transmit = threading.Event()
        self.can_generate.set()  # Start with empty buffer
        
        # Thread control
        self.running = False
        self.pattern_thread = None
        self.spi_thread = None
        
        # Error handling
        self.pattern_error_count = 0
        self.spi_error_count = 0
        self.MAX_ERRORS = 3
        
        # Health monitoring
        self.last_pattern_heartbeat = time.time()
        self.last_spi_heartbeat = time.time()
        self.frames_generated = 0
        self.frames_transmitted = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        # Setup logger for this strip
        self.logger = logging.getLogger(f"Strip.{name}")
        
        # Initialize SPI device
        try:
            self.spi = Pi5Neo(
                spi_device=self.spi_device,
                num_leds=self.led_count,
                spi_speed_khz=self.spi_speed
            )
            self.logger.info(f"Initialized {name} strip on {self.spi_device} with {self.led_count} LEDs")
        except Exception as e:
            self.logger.error(f"Failed to initialize SPI for {name}: {e}")
            raise
    
    def set_pattern(self, pattern):
        """Set the pattern for this strip"""
        if self.running:
            raise RuntimeError("Cannot change pattern while running")
        self.pattern = pattern
        self.logger.info(f"Set pattern {pattern.__class__.__name__} for {self.name}")
    
    def start(self):
        """Start pattern generation and SPI transmission threads"""
        if not self.pattern:
            raise RuntimeError("No pattern set")
        
        if self.running:
            self.logger.warning(f"{self.name} already running")
            return
        
        self.running = True
        
        # Create and start threads
        self.pattern_thread = threading.Thread(
            target=self._pattern_thread_loop,
            name=f"Pattern-{self.name}",
            daemon=True
        )
        self.spi_thread = threading.Thread(
            target=self._spi_thread_loop,
            name=f"SPI-{self.name}",
            daemon=True
        )
        
        self.pattern_thread.start()
        self.spi_thread.start()
        
        self.logger.info(f"Started {self.name} controller threads")
    
    def stop(self):
        """Stop all threads and clear LEDs"""
        if not self.running:
            return
        
        self.logger.info(f"Stopping {self.name} controller")
        self.running = False
        
        # Wake threads so they can exit
        self.can_generate.set()
        self.can_transmit.set()
        
        # Wait for threads to finish
        if self.pattern_thread and self.pattern_thread.is_alive():
            self.pattern_thread.join(timeout=1.0)
        if self.spi_thread and self.spi_thread.is_alive():
            self.spi_thread.join(timeout=1.0)
        
        # Clear LEDs
        self._clear_leds()
        
        self.logger.info(f"Stopped {self.name} controller")
    
    def _pattern_thread_loop(self):
        """Pattern generation thread main loop"""
        threading.current_thread().name = f"Pattern-{self.name}"
        self.logger.debug(f"Pattern thread started for {self.name}")
        
        while self.running:
            try:
                # Wait for permission to generate
                self.can_generate.wait(timeout=0.1)
                if not self.running:
                    break
                
                # Update heartbeat
                self.last_pattern_heartbeat = time.time()
                
                # Generate new frame
                start_time = time.perf_counter()
                pixels = self.pattern.render()
                
                # Validate pixel array
                if pixels is None:
                    raise ValueError("Pattern returned None")
                if len(pixels) != self.led_count:
                    raise ValueError(f"Pattern returned {len(pixels)} pixels, expected {self.led_count}")
                
                # Apply brightness
                if self.brightness != 255:
                    pixels = (pixels * self._brightness_factor).clip(0, 255).astype(np.uint8)
                
                # Store in buffer
                with self.buffer_lock:
                    self.buffer = pixels
                
                # Update stats
                self.frames_generated += 1
                gen_time = (time.perf_counter() - start_time) * 1000
                self.logger.debug(f"Generated frame in {gen_time:.1f}ms")
                
                # Reset error count on success
                self.pattern_error_count = 0
                
                # Signal SPI thread
                self.can_generate.clear()
                self.can_transmit.set()
                
            except Exception as e:
                self.pattern_error_count += 1
                self.logger.error(f"Pattern error in {self.name} ({self.pattern_error_count}/{self.MAX_ERRORS}): {e}")
                
                # Use black frame on error
                with self.buffer_lock:
                    self.buffer = np.zeros((self.led_count, 3), dtype=np.uint8)
                
                # Signal SPI thread even on error
                self.can_generate.clear()
                self.can_transmit.set()
                
                # Exit if too many errors
                if self.pattern_error_count >= self.MAX_ERRORS:
                    self.logger.critical(f"Pattern thread {self.name} exiting after {self.MAX_ERRORS} errors")
                    self.running = False
                    break
        
        self.logger.debug(f"Pattern thread exited for {self.name}")
    
    def _spi_thread_loop(self):
        """SPI transmission thread main loop"""
        threading.current_thread().name = f"SPI-{self.name}"
        self.logger.debug(f"SPI thread started for {self.name}")
        
        while self.running:
            try:
                # Wait for frame to transmit
                self.can_transmit.wait(timeout=0.1)
                if not self.running:
                    break
                
                # Update heartbeat
                self.last_spi_heartbeat = time.time()
                
                # Get buffer
                with self.buffer_lock:
                    if self.buffer is None:
                        continue
                    pixels = self.buffer.copy()
                
                # Clear buffer and signal pattern thread
                self.can_transmit.clear()
                self.can_generate.set()
                
                # Transmit to SPI
                start_time = time.perf_counter()
                for i in range(len(pixels)):
                    r, g, b = pixels[i]
                    self.spi.set_led_color(i, int(r), int(g), int(b))
                self.spi.update_strip(sleep_duration=None)
                
                # Update stats
                self.frames_transmitted += 1
                tx_time = (time.perf_counter() - start_time) * 1000
                self.logger.debug(f"Transmitted frame in {tx_time:.1f}ms")
                
                # Update FPS
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.current_fps = self.frames_transmitted / (current_time - self.last_fps_time)
                    self.frames_transmitted = 0
                    self.last_fps_time = current_time
                
                # Reset error count on success
                self.spi_error_count = 0
                
            except Exception as e:
                self.spi_error_count += 1
                self.logger.error(f"SPI error in {self.name} ({self.spi_error_count}/{self.MAX_ERRORS}): {e}")
                
                # Exit if too many errors
                if self.spi_error_count >= self.MAX_ERRORS:
                    self.logger.critical(f"SPI thread {self.name} exiting after {self.MAX_ERRORS} errors")
                    self.running = False
                    break
        
        self.logger.debug(f"SPI thread exited for {self.name}")
    
    def _clear_leds(self):
        """Clear all LEDs on this strip"""
        try:
            self.spi.clear_strip()
            self.spi.update_strip(sleep_duration=None)
        except Exception as e:
            self.logger.error(f"Failed to clear {self.name} LEDs: {e}")
    
    def set_brightness(self, brightness: int):
        """Set brightness (0-255)"""
        self.brightness = max(0, min(255, brightness))
        self._brightness_factor = self.brightness / 255.0
        self.logger.info(f"Set {self.name} brightness to {self.brightness}")
    
    def get_health(self) -> dict:
        """Get health status of this strip"""
        now = time.time()
        return {
            'name': self.name,
            'running': self.running,
            'fps': self.current_fps,
            'frames_generated': self.frames_generated,
            'pattern_alive': (now - self.last_pattern_heartbeat) < 1.0,
            'spi_alive': (now - self.last_spi_heartbeat) < 1.0,
            'pattern_errors': self.pattern_error_count,
            'spi_errors': self.spi_error_count,
            'pattern_heartbeat_age': now - self.last_pattern_heartbeat,
            'spi_heartbeat_age': now - self.last_spi_heartbeat
        }
    
    def cleanup(self):
        """Clean shutdown"""
        self.stop()
        # Close SPI device
        if hasattr(self.spi, 'spi') and self.spi.spi:
            try:
                self.spi.spi.close()
                self.logger.info(f"Closed SPI device for {self.name}")
            except Exception as e:
                self.logger.error(f"Error closing SPI for {self.name}: {e}")