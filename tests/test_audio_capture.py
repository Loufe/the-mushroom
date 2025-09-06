#!/usr/bin/env python3
"""
Audio Capture Test Script
Tests USB audio detection and signal monitoring
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

try:
    import sounddevice as sd
    from src.audio.device import AudioDevice
    from src.audio.stream import AudioStream
    AUDIO_AVAILABLE = True
except (ImportError, OSError) as e:
    AUDIO_AVAILABLE = False
    print(f"Error: Audio support not available - {e}")
    print("\nTo fix this, install PortAudio:")
    print("  sudo apt-get update")
    print("  sudo apt-get install libportaudio2")
    print("\nThen reinstall Python package:")
    print("  mushroom-env/bin/pip install sounddevice")
    sys.exit(1)


def print_level_meter(level: float, peak: float, width: int = 40):
    """Print visual audio level meter"""
    level_bars = int(level * width)
    peak_pos = int(peak * width)
    
    meter = []
    for i in range(width):
        if i < level_bars:
            meter.append('█')
        elif i == peak_pos:
            meter.append('|')
        else:
            meter.append('░')
    
    # Color coding
    if peak >= 0.99:
        color = '\033[91m'  # Red for clipping
    elif peak >= 0.8:
        color = '\033[93m'  # Yellow for hot
    else:
        color = '\033[92m'  # Green for good
    
    return f"{color}{''.join(meter)}\033[0m RMS: {level:.3f} Peak: {peak:.3f}"


def list_audio_devices():
    """List all available audio devices"""
    print("\n" + "="*60)
    print("Available Audio Devices")
    print("="*60)
    
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append((i, device))
            marker = "[USB]" if 'usb' in device['name'].lower() else ""
            print(f"  [{i:2d}] {device['name']:<40} {marker}")
            print(f"       Channels: {device['max_input_channels']}, "
                  f"Sample Rate: {device['default_samplerate']:.0f}Hz")
    
    if not input_devices:
        print("  No input devices found!")
        return None
    
    print("\n" + "-"*60)
    return input_devices


def test_usb_detection():
    """Test USB device detection"""
    print("\n" + "="*60)
    print("USB Device Detection Test")
    print("="*60)
    
    # Try auto-detection
    print("\n1. Auto-detecting USB device...")
    device_id = AudioDevice.find_usb_device('USB')
    
    if device_id is not None:
        info = AudioDevice.get_device_info(device_id)
        print(f"   ✓ Found: {info['name']} (ID: {device_id})")
        print(f"   Channels: {info['channels']}, Sample Rate: {info['sample_rate']:.0f}Hz")
        
        # Validate device
        print("\n2. Validating device capabilities...")
        if AudioDevice.validate_device(device_id, 44100):
            print("   ✓ Device supports 44100Hz mono input")
        else:
            print("   ✗ Device validation failed")
            device_id = None
    else:
        print("   ✗ No USB device found, will use default input")
    
    print("\n" + "-"*60)
    return device_id


def test_audio_capture(device_id: int = None):
    """Test audio capture with real-time monitoring"""
    print("\n" + "="*60)
    print("Audio Capture Test")
    print("="*60)
    
    # Configure audio stream
    config = {
        'sample_rate': 44100,
        'buffer_size': 512,
        'device_id': device_id
    }
    
    # Create and start stream
    stream = AudioStream(config)
    
    print("\nStarting audio stream...")
    if not stream.start():
        print("✗ Failed to start audio stream")
        return False
    
    status = stream.get_status()
    print(f"✓ Stream active on: {status.device_name}")
    print(f"  Sample rate: {status.sample_rate}Hz")
    print(f"  Buffer size: {status.buffer_size} samples")
    
    print("\n" + "-"*60)
    print("Monitoring audio levels (speak or play music)")
    print("Press Ctrl+C to stop")
    print("-"*60 + "\n")
    
    try:
        frame_count = 0
        last_stats_time = time.time()
        
        while True:
            # Read audio (non-blocking)
            audio_data = stream.read_latest()
            
            if audio_data is not None:
                frame_count += 1
                
                # Get current status
                status = stream.get_status()
                
                # Print level meter
                meter = print_level_meter(status.current_level, status.peak_level)
                
                # Add statistics every second
                current_time = time.time()
                if current_time - last_stats_time >= 1.0:
                    fps = frame_count / (current_time - last_stats_time)
                    print(f"\r{meter} | FPS: {fps:.1f} | Frames: {status.frames_read}", end='')
                    frame_count = 0
                    last_stats_time = current_time
                else:
                    print(f"\r{meter}", end='')
                
                # Warning for clipping
                if status.peak_level >= 0.99:
                    print(" [CLIP!]", end='')
                
            # Small sleep to control update rate
            time.sleep(0.02)  # ~50 FPS display update
            
    except KeyboardInterrupt:
        print("\n\n" + "-"*60)
        print("Stopping audio stream...")
    
    finally:
        stream.stop()
        
        # Print final statistics
        final_status = stream.get_status()
        print(f"\nCapture Statistics:")
        print(f"  Device: {final_status.device_name}")
        print(f"  Total frames: {final_status.frames_read}")
        print(f"  Uptime: {final_status.uptime:.1f} seconds")
        print(f"  Average sample rate: {final_status.frames_read/final_status.uptime:.0f} Hz")
    
    return True


def main():
    """Main test routine"""
    print("\n" + "="*60)
    print("Mushroom LED Audio System Test")
    print("="*60)
    
    # List all devices
    devices = list_audio_devices()
    if not devices:
        print("\nNo audio input devices available!")
        return 1
    
    # Test USB detection
    device_id = test_usb_detection()
    
    # Ask user if they want to proceed with capture test
    print("\nReady to test audio capture.")
    response = input("Continue? (y/n): ")
    
    if response.lower() == 'y':
        success = test_audio_capture(device_id)
        
        if success:
            print("\n" + "="*60)
            print("✓ Audio system test completed successfully!")
            print("="*60)
            return 0
        else:
            print("\n✗ Audio test failed")
            return 1
    else:
        print("Test cancelled")
        return 0


if __name__ == "__main__":
    sys.exit(main())