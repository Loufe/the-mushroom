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
    
    # Calculate age of data
    age = int(time.time() - data.get('timestamp', 0))
    
    print('=== Performance Metrics ===')
    print(f'Data age: {age} seconds ago\n')
    
    # Define metrics with descriptions
    metrics_info = [
        ('color_calc', 'Color Calc', 'Calculating pixel colors'),
        ('pattern_wait', 'Pattern Wait', 'Pattern thread waiting for buffer'),
        ('buffer_prep', 'Buffer Prep', 'Filling Pi5Neo buffer pixel-by-pixel'),
        ('spi_transmit', 'SPI Transmit', 'Hardware transmission to LEDs'),
        ('spi_wait', 'SPI Wait', 'SPI thread waiting for new frame')
    ]
    
    for strip in ['cap', 'stem']:
        strip_data = data.get(strip, {})
        pattern = data.get('patterns', {}).get(strip) or 'None'
        led_count = 450 if strip == 'cap' else 250
        
        print(f'{strip.upper()} ({led_count} LEDs, {pattern} pattern)')
        
        # Show each metric with description
        for metric_name, display_name, description in metrics_info:
            if metric_name in strip_data:
                m = strip_data[metric_name]
                
                # Show metric with safe defaults
                avg = m.get('avg', 0.0)
                min_val = m.get('min', 0.0)
                max_val = m.get('max', 0.0)
                last = m.get('last', 0.0)
                samples = m.get('samples', 0)
                
                print(f'  {display_name:12}: {avg:6.2f}ms avg ({min_val:.1f}-{max_val:.1f} range) '
                      f'last: {last:.1f}ms')
                print(f'                 {description} [{samples} samples]')
        
        # Calculate and show totals for context
        if 'color_calc' in strip_data and 'buffer_prep' in strip_data and 'spi_transmit' in strip_data:
            pattern_time = strip_data['color_calc']['avg']
            spi_time = strip_data['buffer_prep']['avg'] + strip_data['spi_transmit']['avg']
            print(f'\n  Pattern thread: {pattern_time:.1f}ms | SPI thread: {spi_time:.1f}ms')
        
        print()
    
    print('Note: Buffer Prep is typically the bottleneck due to Pi5Neo\'s per-pixel API.')
    print('      Low wait times (<1ms) indicate good parallelism between threads.')

if __name__ == '__main__':
    main()