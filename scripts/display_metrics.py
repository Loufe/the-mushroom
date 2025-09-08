#!/usr/bin/env python3
"""
Display performance metrics from mushroom LED controller
"""

import json
import time
import sys
import os

def main():
    metrics_file = '/tmp/mushroom-metrics.json'
    
    # Check if metrics file exists
    if not os.path.exists(metrics_file):
        print("No metrics available")
        print("Start the controller first with:")
        print("  ./run.sh start")
        sys.exit(1)
    
    try:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading metrics: {e}")
        sys.exit(1)
    
    # Validate required fields exist
    if 'timestamp' not in data:
        print("Metrics not ready yet - waiting for first update")
        sys.exit(0)
    
    # Calculate age of data
    age = int(time.time() - data['timestamp'])
    
    print('=== Performance Metrics ===')
    print(f'Data age: {age} seconds ago\n')
    
    # Display patterns if available
    if 'patterns' in data:
        for strip in ['cap', 'stem']:
            pattern = data['patterns'].get(strip, 'Not set')
            led_count = 450 if strip == 'cap' else 250
            print(f'{strip.upper()} ({led_count} LEDs, {pattern} pattern)')
        print()
    
    # Display FPS if available  
    if 'fps' in data and 'frames_sent' in data:
        print(f'FPS: {data["fps"]:.1f}')
        print(f'Frames sent: {data["frames_sent"]}')
    else:
        print('Performance data not yet available')
    
    # Display timing breakdown if available
    if 'timing_ms' in data:
        print()
        print('Timing breakdown (last frame):')
        timing = data['timing_ms']
        if 'pattern_wait' in timing:
            print(f'  Pattern wait: {timing["pattern_wait"]:.1f}ms')
        if 'buffer_prep' in timing:
            print(f'  Buffer prep:  {timing["buffer_prep"]:.1f}ms')
        if 'spi_transmit' in timing:
            print(f'  SPI transmit: {timing["spi_transmit"]:.1f}ms')
        
        if 'buffer_prep' in timing and 'spi_transmit' in timing:
            total_ms = timing['buffer_prep'] + timing['spi_transmit']
            print(f'  Total frame:  {total_ms:.1f}ms')

if __name__ == '__main__':
    main()