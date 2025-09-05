#!/usr/bin/env python3
"""
Audio Device - USB audio device detection
"""

import sounddevice as sd
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AudioDevice:
    """Finds and validates USB audio device at startup"""
    
    @staticmethod
    def find_usb_device(prefer_device: Optional[str] = None) -> Optional[int]:
        """
        Find USB audio input device
        
        Args:
            prefer_device: Preferred device name or 'USB' for auto-detect
            
        Returns:
            Device ID or None if not found
        """
        try:
            devices = sd.query_devices()
            
            # If specific device name provided, look for exact match first
            if prefer_device and prefer_device != 'USB':
                for i, device in enumerate(devices):
                    if device['max_input_channels'] > 0:
                        if prefer_device.lower() in device['name'].lower():
                            logger.info(f"Found preferred device: {device['name']} (ID: {i})")
                            return i
            
            # Look for USB device
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    device_name = device['name'].lower()
                    # Common USB audio adapter identifiers
                    if any(usb_hint in device_name for usb_hint in ['usb', 'audio adapter', 'au-mmsa']):
                        logger.info(f"Found USB audio device: {device['name']} (ID: {i})")
                        return i
            
            # Fallback to first available input device
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    logger.warning(f"No USB device found, using: {device['name']} (ID: {i})")
                    return i
                    
            logger.error("No audio input devices found")
            return None
            
        except Exception as e:
            logger.error(f"Error querying audio devices: {e}")
            return None
    
    @staticmethod
    def validate_device(device_id: int, sample_rate: int = 44100) -> bool:
        """
        Validate that device supports required format
        
        Args:
            device_id: Device ID to validate
            sample_rate: Required sample rate
            
        Returns:
            True if device is valid
        """
        try:
            device_info = sd.query_devices(device_id, 'input')
            
            # Check if device has input channels
            if device_info['max_input_channels'] < 1:
                logger.error(f"Device {device_id} has no input channels")
                return False
            
            # Check sample rate support
            try:
                sd.check_input_settings(
                    device=device_id,
                    channels=1,
                    samplerate=sample_rate
                )
                logger.info(f"Device {device_id} validated at {sample_rate}Hz")
                return True
            except Exception as e:
                logger.error(f"Device {device_id} doesn't support {sample_rate}Hz: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating device {device_id}: {e}")
            return False
    
    @staticmethod
    def get_device_info(device_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get device information
        
        Args:
            device_id: Device ID or None for default
            
        Returns:
            Device info dictionary
        """
        try:
            if device_id is None:
                device_id = sd.default.device[0]  # Input device
            
            info = sd.query_devices(device_id, 'input')
            return {
                'id': device_id,
                'name': info['name'],
                'channels': info['max_input_channels'],
                'sample_rate': info['default_samplerate'],
                'host_api': sd.query_hostapis(info['hostapi'])['name']
            }
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}