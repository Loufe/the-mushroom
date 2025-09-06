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
    
    # Class constants
    WAIT_TIMEOUT_MS = 100  # Thread wait timeout in milliseconds
    WS2811_LATCH_DELAY = 0.0002  # 200µs reset period required by WS2811 protocol
    
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
        
        # Performance metrics (running statistics with 5-minute window)
        self.metrics = {
            'color_calc': {'count': 0, 'sum': 0.0, 'min': float('inf'), 'max': 0.0, 'last': 0.0},
            'pattern_wait': {'count': 0, 'sum': 0.0, 'min': float('inf'), 'max': 0.0, 'last': 0.0},
            'buffer_prep': {'count': 0, 'sum': 0.0, 'min': float('inf'), 'max': 0.0, 'last': 0.0},
            'spi_transmit': {'count': 0, 'sum': 0.0, 'min': float('inf'), 'max': 0.0, 'last': 0.0},
            'spi_wait': {'count': 0, 'sum': 0.0, 'min': float('inf'), 'max': 0.0, 'last': 0.0}
        }
        self.metrics_start_time = time.time()
        self.METRICS_WINDOW_SECONDS = 300  # 5-minute rolling window
        
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
        # Pass hardware brightness to pattern
        pattern.set_brightness(self._brightness_factor)
        # Reset metrics for new pattern
        for metric in self.metrics.values():
            metric['count'] = 0
            metric['sum'] = 0.0
            metric['min'] = float('inf')
            metric['max'] = 0.0
            metric['last'] = 0.0
        self.metrics_start_time = time.time()
        self.logger.info(f"Set pattern {pattern.__class__.__name__} for {self.name}, reset metrics")
    
    def _record_metric(self, name: str, value_ms: float):
        """Record a performance metric with running statistics"""
        # Check if metrics window has expired (5 minutes)
        current_time = time.time()
        if current_time - self.metrics_start_time > self.METRICS_WINDOW_SECONDS:
            # Reset all metrics for new window
            for metric in self.metrics.values():
                metric['count'] = 0
                metric['sum'] = 0.0
                metric['min'] = float('inf')
                metric['max'] = 0.0
                metric['last'] = 0.0
            self.metrics_start_time = current_time
            self.logger.debug(f"Reset metrics for {self.name} after 5-minute window")
        
        # Record the metric
        metric = self.metrics[name]
        metric['count'] += 1
        metric['sum'] += value_ms
        metric['min'] = min(metric['min'], value_ms)
        metric['max'] = max(metric['max'], value_ms)
        metric['last'] = value_ms
    
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
                wait_start = time.perf_counter()
                self.can_generate.wait(timeout=0.1)
                wait_time_ms = (time.perf_counter() - wait_start) * 1000
                if wait_time_ms < self.WAIT_TIMEOUT_MS:  # Only record if not timeout
                    self._record_metric('pattern_wait', wait_time_ms)
                
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
                
                # Store in buffer (pattern already applied brightness)
                with self.buffer_lock:
                    self.buffer = pixels
                
                # Update stats
                self.frames_generated += 1
                gen_time = (time.perf_counter() - start_time) * 1000
                self._record_metric('color_calc', gen_time)
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
                wait_start = time.perf_counter()
                self.can_transmit.wait(timeout=0.1)
                wait_time_ms = (time.perf_counter() - wait_start) * 1000
                if wait_time_ms < self.WAIT_TIMEOUT_MS:  # Only record if not timeout
                    self._record_metric('spi_wait', wait_time_ms)
                
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
                
                # Transmit to SPI - measure buffer preparation and SPI transmission separately
                pixel_start = time.perf_counter()
                for i in range(len(pixels)):
                    r, g, b = pixels[i]
                    self.spi.set_led_color(i, int(r), int(g), int(b))
                pixel_time_ms = (time.perf_counter() - pixel_start) * 1000
                self._record_metric('buffer_prep', pixel_time_ms)
                
                spi_start = time.perf_counter()
                self.spi.update_strip(sleep_duration=self.WS2811_LATCH_DELAY)
                spi_time_ms = (time.perf_counter() - spi_start) * 1000
                self._record_metric('spi_transmit', spi_time_ms)
                
                # Update stats
                self.frames_transmitted += 1
                total_tx_time = pixel_time_ms + spi_time_ms
                self.logger.debug(f"Transmitted frame in {total_tx_time:.1f}ms (pixel:{pixel_time_ms:.1f}ms spi:{spi_time_ms:.1f}ms)")
                
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
            self.spi.update_strip(sleep_duration=self.WS2811_LATCH_DELAY)
        except Exception as e:
            self.logger.error(f"Failed to clear {self.name} LEDs: {e}")
    
    def set_brightness(self, brightness: int):
        """Set brightness (0-255)"""
        self.brightness = max(0, min(255, brightness))
        self._brightness_factor = self.brightness / 255.0
        # Update pattern's brightness if one is set
        if self.pattern:
            self.pattern.set_brightness(self._brightness_factor)
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
    
    def get_performance_details(self) -> dict:
        """Get detailed performance metrics"""
        details = {}
        
        # Add defensive programming
        try:
            for name, metric in self.metrics.items():
                if metric.get('count', 0) > 0:
                    count = metric['count']
                    sum_val = metric.get('sum', 0.0)
                    details[name] = {
                        'avg': sum_val / count if count > 0 else 0.0,
                        'min': metric.get('min', 0.0),
                        'max': metric.get('max', 0.0),
                        'last': metric.get('last', 0.0),
                        'samples': count
                    }
                else:
                    details[name] = {
                        'avg': 0.0,
                        'min': 0.0,
                        'max': 0.0,
                        'last': 0.0,
                        'samples': 0
                    }
        except (KeyError, TypeError, ZeroDivisionError) as e:
            self.logger.debug(f"Error calculating metrics: {e}")
            # Return safe defaults
            for name in ['color_calc', 'pattern_wait', 'buffer_prep', 'spi_transmit', 'spi_wait']:
                details[name] = {
                    'avg': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'last': 0.0,
                    'samples': 0
                }
        
        return details
    
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