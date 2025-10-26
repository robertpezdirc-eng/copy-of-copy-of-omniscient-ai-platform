import socket
import json
from omni_event_logger import EventLogger

class OmniVRConnector:
    def __init__(self, config):
        self.config = config
        self.logger = EventLogger()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(("", 9090))  # Sprejem podatkov z očal
        self.logger.log("VR Connector initialized on port 9090")

    def listen(self):
        data, addr = self.server_socket.recvfrom(4096)
        try:
            vr_data = json.loads(data.decode())
            self.logger.log(f"VR data received: {vr_data.get('event_type', 'unknown')}")
            return vr_data
        except Exception as e:
            self.logger.log(f"VR data parse error: {e}")
            return None