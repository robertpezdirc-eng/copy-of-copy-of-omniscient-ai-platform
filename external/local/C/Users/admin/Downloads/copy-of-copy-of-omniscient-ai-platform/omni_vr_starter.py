#!/usr/bin/env python3
"""
OMNI VR Starter - Connect VR headsets and start learning
"""

import json
import time
import socket
import threading
from omni_vr_connector import OmniVRConnector
from omni_event_logger import EventLogger

class OmniVRStarter:
    def __init__(self, config_path="omni_autolearn_config.json"):
        self.logger = EventLogger()
        self.config = self.load_config(config_path)
        self.vr_connector = OmniVRConnector(self.config)
        self.running = False

    def load_config(self, path):
        """Load configuration file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.log(f"Config load error: {e}")
            return {}

    def create_unity_example(self):
        """Create Unity script example for VR headset data sending"""
        unity_script = """
using UnityEngine;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class OmniVRDataSender : MonoBehaviour
{
    // OMNI Platform settings
    public string omniPlatformIP = "192.168.1.100"; // Change to your platform IP
    public int port = 9090;
    private UdpClient udpClient;
    private Thread sendThread;

    void Start()
    {
        udpClient = new UdpClient();
        sendThread = new Thread(new ThreadStart(SendVRData));
        sendThread.Start();
        Debug.Log("OMNI VR Data Sender started - connecting to: " + omniPlatformIP + ":" + port);
    }

    void SendVRData()
    {
        while (true)
        {
            try
            {
                // Collect VR headset data
                var vrData = new
                {
                    event_type = "movement",
                    headset = "Meta Quest 3",
                    position = new
                    {
                        x = transform.position.x,
                        y = transform.position.y,
                        z = transform.position.z
                    },
                    rotation = new
                    {
                        x = transform.rotation.eulerAngles.x,
                        y = transform.rotation.eulerAngles.y,
                        z = transform.rotation.eulerAngles.z
                    },
                    timestamp = System.DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                    controller_left = new
                    {
                        position = new { x = 0, y = 0, z = 0 },
                        trigger = Input.GetAxis("Oculus_CrossPlatform_PrimaryIndexTrigger"),
                        grip = Input.GetAxis("Oculus_CrossPlatform_PrimaryHandTrigger")
                    },
                    controller_right = new
                    {
                        position = new { x = 0, y = 0, z = 0 },
                        trigger = Input.GetAxis("Oculus_CrossPlatform_SecondaryIndexTrigger"),
                        grip = Input.GetAxis("Oculus_CrossPlatform_SecondaryHandTrigger")
                    }
                };

                string jsonData = JsonUtility.ToJson(vrData);
                byte[] data = Encoding.UTF8.GetBytes(jsonData);

                udpClient.Send(data, data.Length, omniPlatformIP, port);

                // Send data 30 times per second
                Thread.Sleep(33);
            }
            catch (System.Exception e)
            {
                Debug.LogError("Error sending VR data: " + e.Message);
                Thread.Sleep(1000);
            }
        }
    }

    void OnApplicationQuit()
    {
        if (sendThread != null && sendThread.IsAlive)
        {
            sendThread.Abort();
        }
        udpClient.Close();
    }
}
"""
        with open("omni_vr_unity_example.cs", "w") as f:
            f.write(unity_script)

        self.logger.log("Unity example script created: omni_vr_unity_example.cs")
        return "omni_vr_unity_example.cs"

    def create_vr_test_client(self):
        """Create a test VR client to simulate headset data"""
        test_client_script = '''
import socket
import json
import time
import random

def simulate_vr_headset():
    """Simulate VR headset sending movement data"""
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Your OMNI platform IP
    OMNI_IP = "localhost"  # Change to your platform IP
    PORT = 9090

    print(f"Simulating VR headset - sending data to {OMNI_IP}:{PORT}")
    print("Press Ctrl+C to stop")

    try:
        while True:
            # Simulate natural head movement
            vr_data = {
                "event_type": "movement",
                "headset": "Meta Quest 3",
                "position": {
                    "x": random.uniform(-2.0, 2.0),
                    "y": random.uniform(1.0, 2.0),
                    "z": random.uniform(-3.0, 1.0)
                },
                "rotation": {
                    "x": random.uniform(-90, 90),
                    "y": random.uniform(-180, 180),
                    "z": random.uniform(-45, 45)
                },
                "timestamp": time.time(),
                "controllers": {
                    "left": {
                        "position": {"x": -0.5, "y": 1.0, "z": -1.0},
                        "trigger": random.uniform(0, 1),
                        "grip": random.uniform(0, 1)
                    },
                    "right": {
                        "position": {"x": 0.5, "y": 1.0, "z": -1.0},
                        "trigger": random.uniform(0, 1),
                        "grip": random.uniform(0, 1)
                    }
                }
            }

            message = json.dumps(vr_data).encode('utf-8')
            client.sendto(message, (OMNI_IP, PORT))

            print(f"Sent VR data: position={vr_data['position']}")
            time.sleep(0.1)  # 10 FPS

    except KeyboardInterrupt:
        print("\\nVR simulation stopped")
    finally:
        client.close()

if __name__ == "__main__":
    simulate_vr_headset()
'''
        with open("simulate_vr_headset.py", "w") as f:
            f.write(test_client_script)

        self.logger.log("VR test client created: simulate_vr_headset.py")
        return "simulate_vr_headset.py"

    def start_vr_listener(self):
        """Start listening for VR data"""
        self.running = True
        self.logger.log("VR listener started - waiting for headset data...")

        while self.running:
            try:
                vr_data = self.vr_connector.listen()
                if vr_data:
                    self.logger.log(f"VR Data Received: {vr_data.get('event_type', 'unknown')}")
                    self.logger.log(f"Position: {vr_data.get('position', {})}")
                    self.logger.log(f"Headset: {vr_data.get('headset', 'unknown')}")

                    # Here you could add additional processing
                    # like saving to database, triggering events, etc.

            except Exception as e:
                self.logger.log(f"VR listener error: {e}")
                time.sleep(1)

    def stop(self):
        """Stop the VR listener"""
        self.running = False
        self.logger.log("VR listener stopped")

def main():
    """Main function"""
    print("OMNI VR Starter")
    print("=" * 50)

    vr_starter = OmniVRStarter()

    # Create Unity example
    print("Creating Unity example script...")
    unity_file = vr_starter.create_unity_example()
    print(f"Created: {unity_file}")

    # Create test client
    print("Creating VR test client...")
    test_file = vr_starter.create_vr_test_client()
    print(f"Created: {test_file}")

    print("\\nVR Setup Complete!")
    print("Choose an option:")
    print("1. Start VR listener (wait for real headset)")
    print("2. Run VR simulation test")
    print("3. Exit")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        print("Starting VR listener...")
        print("Make sure your VR headset is configured to send data to this machine")
        print("Press Ctrl+C to stop")

        try:
            vr_starter.start_vr_listener()
        except KeyboardInterrupt:
            print("\\nStopping VR listener...")
        finally:
            vr_starter.stop()

    elif choice == "2":
        print("Starting VR simulation...")
        print("Run this in a separate terminal: python simulate_vr_headset.py")
        print("Then press Enter here to start listening...")

        input()

        try:
            vr_starter.start_vr_listener()
        except KeyboardInterrupt:
            print("\\nStopping VR listener...")
        finally:
            vr_starter.stop()

    else:
        print("Exiting...")

if __name__ == "__main__":
    main()