#!/usr/bin/env python3
"""
IoT Data Generator and Publisher
Generates sample IIoT sensor data and publishes it to Google Cloud Pub/Sub
"""
import json
import time
import random
import argparse
from datetime import datetime
from google.cloud import pubsub_v1

# Status distribution weights for mixed mode
STATUS_DISTRIBUTION_NORMAL = 0.6   # 60% of messages are normal
STATUS_DISTRIBUTION_WARNING = 0.25  # 25% of messages are warnings
STATUS_DISTRIBUTION_CRITICAL = 0.15 # 15% of messages are critical

# Device configurations
DEVICES = {
    "vibration_sensor_001": {
        "type": "vibration",
        "normal_range": {"vibration": (50, 70), "temperature": (60, 75)},
        "warning_range": {"vibration": (70, 85), "temperature": (75, 85)},
        "critical_range": {"vibration": (85, 100), "temperature": (85, 95)}
    },
    "pressure_sensor_002": {
        "type": "pressure",
        "normal_range": {"pressure": (98, 102), "temperature": (65, 75)},
        "warning_range": {"pressure": (95, 98), "temperature": (75, 82)},
        "critical_range": {"pressure": (90, 95), "temperature": (82, 90)}
    },
    "temperature_sensor_003": {
        "type": "temperature",
        "normal_range": {"temperature": (65, 75), "humidity": (40, 60)},
        "warning_range": {"temperature": (75, 85), "humidity": (60, 75)},
        "critical_range": {"temperature": (85, 95), "humidity": (75, 90)}
    }
}


def generate_sensor_data(device_id, status="normal"):
    """Generate realistic sensor data based on device type and status"""
    device_config = DEVICES[device_id]
    device_type = device_config["type"]
    
    # Select appropriate range based on status
    if status == "normal":
        ranges = device_config["normal_range"]
    elif status == "warning":
        ranges = device_config["warning_range"]
    else:  # critical
        ranges = device_config["critical_range"]
    
    # Generate measurements
    measurements = {}
    for metric, (min_val, max_val) in ranges.items():
        measurements[metric] = round(random.uniform(min_val, max_val), 2)
    
    # Create message
    message = {
        "device_id": device_id,
        "sensor_type": device_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "measurements": measurements,
        "status": status
    }
    
    return message


def publish_message(publisher, topic_path, message):
    """Publish a message to Pub/Sub"""
    message_json = json.dumps(message)
    message_bytes = message_json.encode('utf-8')
    
    future = publisher.publish(topic_path, message_bytes)
    message_id = future.result()
    
    return message_id


def main():
    parser = argparse.ArgumentParser(description='IoT Data Generator and Publisher')
    parser.add_argument('--project', required=True, help='Google Cloud Project ID')
    parser.add_argument('--topic', default='iot-data-topic', help='Pub/Sub topic name')
    parser.add_argument('--count', type=int, default=10, help='Number of messages to send')
    parser.add_argument('--interval', type=float, default=2.0, help='Interval between messages (seconds)')
    parser.add_argument('--status', choices=['normal', 'warning', 'critical', 'mixed'], 
                        default='mixed', help='Device status type')
    
    args = parser.parse_args()
    
    # Initialize Pub/Sub publisher
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(args.project, args.topic)
    
    print(f"IoT Data Generator")
    print(f"==================")
    print(f"Project: {args.project}")
    print(f"Topic: {args.topic}")
    print(f"Messages: {args.count}")
    print(f"Interval: {args.interval}s")
    print(f"Status: {args.status}")
    print("")
    
    try:
        for i in range(args.count):
            # Select random device
            device_id = random.choice(list(DEVICES.keys()))
            
            # Determine status
            if args.status == 'mixed':
                # 60% normal, 25% warning, 15% critical
                status = random.choices(
                    ['normal', 'warning', 'critical'],
                    weights=[
                        STATUS_DISTRIBUTION_NORMAL,
                        STATUS_DISTRIBUTION_WARNING,
                        STATUS_DISTRIBUTION_CRITICAL
                    ]
                )[0]
            else:
                status = args.status
            
            # Generate and publish data
            message = generate_sensor_data(device_id, status)
            message_id = publish_message(publisher, topic_path, message)
            
            # Display
            status_icon = {
                'normal': '✓',
                'warning': '⚠',
                'critical': '❌'
            }[status]
            
            print(f"{status_icon} [{i+1}/{args.count}] {device_id} ({status})")
            print(f"  Message ID: {message_id}")
            print(f"  Data: {json.dumps(message['measurements'], indent=4)}")
            print("")
            
            if i < args.count - 1:
                time.sleep(args.interval)
        
        print("✓ All messages published successfully")
        
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
