#!/usr/bin/env python3
"""
OMNI VR WebXR Integration with WebRTC
Advanced VR glasses integration using WebXR API with WebRTC for real-time communication
Supports Oculus Quest, HTC Vive, and other WebXR-compatible devices
"""

import asyncio
import json
import time
import uuid
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import threading
import aiohttp
from enum import Enum

class WebXRSessionType(Enum):
    """WebXR session types"""
    IMMERSIVE_VR = "immersive-vr"
    IMMERSIVE_AR = "immersive-ar"
    INLINE = "inline"

class WebXRInputType(Enum):
    """WebXR input types"""
    GAZE = "gaze"
    SCREEN_TOUCH = "screen_touch"
    HAND_TRACKING = "hand_tracking"
    CONTROLLER_6DOF = "controller_6dof"
    CONTROLLER_3DOF = "controller_3dof"
    VOICE = "voice"

@dataclass
class VRDeviceCapabilities:
    """VR device capabilities for WebXR"""
    webxr_support: bool = True
    webxr_version: str = "1.0"
    supported_session_types: List[WebXRSessionType] = field(default_factory=list)
    input_types: List[WebXRInputType] = field(default_factory=list)
    max_resolution: Tuple[int, int] = (1920, 1080)
    refresh_rate: int = 90
    fov: Tuple[float, float, float, float] = (45.0, 45.0, 45.0, 45.0)  # left, right, top, bottom
    has_external_display: bool = False
    supports_passthrough: bool = False
    supports_hand_tracking: bool = False
    supports_eye_tracking: bool = False
    supports_face_tracking: bool = False
    supports_body_tracking: bool = False

@dataclass
class WebXRSession:
    """WebXR session information"""
    session_id: str
    device_id: str
    session_type: WebXRSessionType
    input_types: List[WebXRInputType]
    capabilities: VRDeviceCapabilities
    webrtc_session_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    frame_rate: float = 0.0
    latency_ms: float = 0.0
    user_agent: str = ""

@dataclass
class VRInputEvent:
    """VR input event"""
    event_id: str
    session_id: str
    input_type: WebXRInputType
    timestamp: datetime
    data: Dict[str, Any]
    hand: str = ""  # "left", "right", or ""

class OmniVRWebXRIntegration:
    """WebXR Integration for VR glasses"""

    def __init__(self, webrtc_gateway=None):
        self.webrtc_gateway = webrtc_gateway
        self.sessions: Dict[str, WebXRSession] = {}
        self.input_events: List[VRInputEvent] = []
        self.device_capabilities: Dict[str, VRDeviceCapabilities] = {}

        # WebXR configuration
        self.config = {
            "required_features": ["local-floor"],
            "optional_features": ["hand-tracking", "eye-tracking", "layers"],
            "reference_space_type": "local-floor",
            "enable_webrtc": True,
            "enable_spatial_audio": True,
            "enable_haptic_feedback": True,
            "max_session_duration": 3600,  # seconds
            "frame_rate_target": 90
        }

        # Background tasks
        self._running = False
        self._input_processor_task = None
        self._session_monitor_task = None

        print("🥽 OMNI VR WebXR Integration initialized")

    async def start(self) -> bool:
        """Start WebXR integration"""
        try:
            self._running = True

            # Start input processor
            self._input_processor_task = asyncio.create_task(self._process_input_events())

            # Start session monitor
            self._session_monitor_task = asyncio.create_task(self._monitor_sessions())

            print("✅ OMNI VR WebXR Integration started")
            return True

        except Exception as e:
            print(f"❌ Failed to start WebXR integration: {e}")
            return False

    async def stop(self):
        """Stop WebXR integration"""
        try:
            self._running = False

            # End all sessions
            for session in self.sessions.values():
                await self.end_session(session.session_id)

            # Cancel background tasks
            if self._input_processor_task:
                self._input_processor_task.cancel()
            if self._session_monitor_task:
                self._session_monitor_task.cancel()

            print("🛑 OMNI VR WebXR Integration stopped")

        except Exception as e:
            print(f"⚠️ Error stopping WebXR integration: {e}")

    async def create_session(self, device_id: str, user_agent: str = "", webrtc_enabled: bool = True) -> str:
        """Create new WebXR session"""
        try:
            session_id = str(uuid.uuid4())

            # Detect device capabilities from user agent
            capabilities = self._detect_device_capabilities(user_agent)

            # Determine session type based on capabilities
            session_type = WebXRSessionType.IMMERSIVE_VR
            if capabilities.supports_passthrough:
                session_type = WebXRSessionType.IMMERSIVE_AR

            # Create WebXR session
            session = WebXRSession(
                session_id=session_id,
                device_id=device_id,
                session_type=session_type,
                input_types=capabilities.input_types,
                capabilities=capabilities,
                user_agent=user_agent
            )

            self.sessions[session_id] = session

            # Create WebRTC session if enabled
            if webrtc_enabled and self.webrtc_gateway:
                webrtc_session_id = await self.webrtc_gateway.create_session(
                    device_id,
                    ["video", "audio", "data"]
                )

                if webrtc_session_id:
                    session.webrtc_session_id = webrtc_session_id
                    print(f"🎥 WebRTC session created for WebXR: {webrtc_session_id}")

            print(f"🥽 WebXR session created: {session_id} for device {device_id}")
            return session_id

        except Exception as e:
            print(f"❌ Failed to create WebXR session: {e}")
            return None

    async def end_session(self, session_id: str) -> bool:
        """End WebXR session"""
        try:
            if session_id not in self.sessions:
                return False

            session = self.sessions[session_id]

            # Close WebRTC session if exists
            if session.webrtc_session_id and self.webrtc_gateway:
                await self.webrtc_gateway.close_session(session.webrtc_session_id)

            # Remove session
            del self.sessions[session_id]

            print(f"🥽 WebXR session ended: {session_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to end WebXR session: {e}")
            return False

    def _detect_device_capabilities(self, user_agent: str) -> VRDeviceCapabilities:
        """Detect VR device capabilities from user agent"""
        capabilities = VRDeviceCapabilities()

        user_agent_lower = user_agent.lower()

        # Detect Oculus Quest
        if "oculus" in user_agent_lower or "quest" in user_agent_lower:
            capabilities = VRDeviceCapabilities(
                webxr_support=True,
                webxr_version="1.0",
                supported_session_types=[WebXRSessionType.IMMERSIVE_VR, WebXRSessionType.IMMERSIVE_AR],
                input_types=[WebXRInputType.CONTROLLER_6DOF, WebXRInputType.HAND_TRACKING],
                max_resolution=(1920, 1080),
                refresh_rate=90,
                fov=(45.0, 45.0, 45.0, 45.0),
                has_external_display=False,
                supports_passthrough=True,
                supports_hand_tracking=True,
                supports_eye_tracking=False,
                supports_face_tracking=False,
                supports_body_tracking=False
            )

        # Detect HTC Vive
        elif "vive" in user_agent_lower or "htc" in user_agent_lower:
            capabilities = VRDeviceCapabilities(
                webxr_support=True,
                webxr_version="1.0",
                supported_session_types=[WebXRSessionType.IMMERSIVE_VR],
                input_types=[WebXRInputType.CONTROLLER_6DOF],
                max_resolution=(2160, 1200),
                refresh_rate=90,
                fov=(50.0, 50.0, 50.0, 50.0),
                has_external_display=True,
                supports_passthrough=False,
                supports_hand_tracking=False,
                supports_eye_tracking=False,
                supports_face_tracking=False,
                supports_body_tracking=False
            )

        # Detect mobile VR
        elif "mobile" in user_agent_lower or "android" in user_agent_lower:
            capabilities = VRDeviceCapabilities(
                webxr_support=True,
                webxr_version="1.0",
                supported_session_types=[WebXRSessionType.IMMERSIVE_VR],
                input_types=[WebXRInputType.GAZE, WebXRInputType.SCREEN_TOUCH],
                max_resolution=(1920, 1080),
                refresh_rate=60,
                fov=(40.0, 40.0, 40.0, 40.0),
                has_external_display=False,
                supports_passthrough=False,
                supports_hand_tracking=False,
                supports_eye_tracking=False,
                supports_face_tracking=False,
                supports_body_tracking=False
            )

        # Default desktop VR
        else:
            capabilities = VRDeviceCapabilities(
                webxr_support=True,
                webxr_version="1.0",
                supported_session_types=[WebXRSessionType.IMMERSIVE_VR],
                input_types=[WebXRInputType.CONTROLLER_3DOF],
                max_resolution=(1920, 1080),
                refresh_rate=90,
                fov=(45.0, 45.0, 45.0, 45.0),
                has_external_display=True,
                supports_passthrough=False,
                supports_hand_tracking=False,
                supports_eye_tracking=False,
                supports_face_tracking=False,
                supports_body_tracking=False
            )

        return capabilities

    async def handle_input_event(self, session_id: str, input_type: str, event_data: Dict[str, Any], hand: str = "") -> bool:
        """Handle VR input event"""
        try:
            if session_id not in self.sessions:
                return False

            # Create input event
            input_event = VRInputEvent(
                event_id=str(uuid.uuid4()),
                session_id=session_id,
                input_type=WebXRInputType(input_type),
                timestamp=datetime.now(),
                data=event_data,
                hand=hand
            )

            # Add to input events queue for processing
            self.input_events.append(input_event)

            # Process immediately for real-time response
            await self._process_vr_input(input_event)

            return True

        except Exception as e:
            print(f"❌ Failed to handle VR input event: {e}")
            return False

    async def _process_vr_input(self, input_event: VRInputEvent):
        """Process VR input event"""
        try:
            session = self.sessions.get(input_event.session_id)
            if not session:
                return

            # Handle different input types
            if input_event.input_type == WebXRInputType.HAND_TRACKING:
                await self._handle_hand_tracking(session, input_event)
            elif input_event.input_type == WebXRInputType.CONTROLLER_6DOF:
                await self._handle_controller_input(session, input_event)
            elif input_event.input_type == WebXRInputType.GAZE:
                await self._handle_gaze_input(session, input_event)
            elif input_event.input_type == WebXRInputType.VOICE:
                await self._handle_voice_input(session, input_event)

        except Exception as e:
            print(f"⚠️ VR input processing error: {e}")

    async def _handle_hand_tracking(self, session: WebXRSession, input_event: VRInputEvent):
        """Handle hand tracking input"""
        try:
            hand_data = input_event.data

            # Send hand tracking data via WebRTC data channel
            if session.webrtc_session_id and self.webrtc_gateway:
                await self.webrtc_gateway.send_data_channel_message(
                    session.webrtc_session_id,
                    "omni_control",
                    {
                        "type": "hand_tracking",
                        "hand": input_event.hand,
                        "position": hand_data.get("position", {}),
                        "rotation": hand_data.get("rotation", {}),
                        "gesture": hand_data.get("gesture", ""),
                        "timestamp": input_event.timestamp.isoformat()
                    }
                )

        except Exception as e:
            print(f"⚠️ Hand tracking error: {e}")

    async def _handle_controller_input(self, session: WebXRSession, input_event: VRInputEvent):
        """Handle controller input"""
        try:
            controller_data = input_event.data

            # Send controller data via WebRTC
            if session.webrtc_session_id and self.webrtc_gateway:
                await self.webrtc_gateway.send_data_channel_message(
                    session.webrtc_session_id,
                    "omni_control",
                    {
                        "type": "controller_input",
                        "hand": input_event.hand,
                        "buttons": controller_data.get("buttons", {}),
                        "axes": controller_data.get("axes", {}),
                        "position": controller_data.get("position", {}),
                        "rotation": controller_data.get("rotation", {}),
                        "timestamp": input_event.timestamp.isoformat()
                    }
                )

        except Exception as e:
            print(f"⚠️ Controller input error: {e}")

    async def _handle_gaze_input(self, session: WebXRSession, input_event: VRInputEvent):
        """Handle gaze input"""
        try:
            gaze_data = input_event.data

            # Send gaze data for attention tracking
            if session.webrtc_session_id and self.webrtc_gateway:
                await self.webrtc_gateway.send_data_channel_message(
                    session.webrtc_session_id,
                    "omni_control",
                    {
                        "type": "gaze_input",
                        "direction": gaze_data.get("direction", {}),
                        "target": gaze_data.get("target", ""),
                        "timestamp": input_event.timestamp.isoformat()
                    }
                )

        except Exception as e:
            print(f"⚠️ Gaze input error: {e}")

    async def _handle_voice_input(self, session: WebXRSession, input_event: VRInputEvent):
        """Handle voice input"""
        try:
            voice_data = input_event.data

            # Send voice data for processing
            if session.webrtc_session_id and self.webrtc_gateway:
                await self.webrtc_gateway.send_data_channel_message(
                    session.webrtc_session_id,
                    "omni_control",
                    {
                        "type": "voice_input",
                        "audio_data": voice_data.get("audio_data", ""),
                        "confidence": voice_data.get("confidence", 0.0),
                        "transcript": voice_data.get("transcript", ""),
                        "timestamp": input_event.timestamp.isoformat()
                    }
                )

        except Exception as e:
            print(f"⚠️ Voice input error: {e}")

    async def _process_input_events(self):
        """Process input events queue"""
        while self._running:
            try:
                if self.input_events:
                    # Process oldest events first
                    input_event = self.input_events.pop(0)
                    await self._process_vr_input(input_event)

                await asyncio.sleep(0.01)  # 10ms for real-time processing

            except Exception as e:
                print(f"⚠️ Input processing error: {e}")
                await asyncio.sleep(0.01)

    async def _monitor_sessions(self):
        """Monitor WebXR sessions"""
        while self._running:
            try:
                current_time = datetime.now()
                expired_sessions = []

                for session_id, session in self.sessions.items():
                    # Check for expired sessions
                    if (current_time - session.started_at).seconds > self.config["max_session_duration"]:
                        expired_sessions.append(session_id)

                # End expired sessions
                for session_id in expired_sessions:
                    await self.end_session(session_id)
                    print(f"⏰ Ended expired WebXR session: {session_id}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                print(f"⚠️ Session monitoring error: {e}")
                await asyncio.sleep(60)

    def generate_webxr_html(self, session_id: str, vr_project_url: str = "") -> str:
        """Generate WebXR HTML for VR glasses"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return "<html><body>Error: Session not found</body></html>"

            # Generate WebXR HTML based on device capabilities
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMNI VR - WebXR Experience</title>
    <style>
        body {{
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #000;
            color: #fff;
            overflow: hidden;
        }}

        #vr-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}

        #vr-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}

        #status {{
            position: fixed;
            top: 20px;
            left: 20px;
            color: white;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
        }}

        #info-panel {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 10px;
            display: none;
        }}
    </style>
</head>
<body>
    <div id="status">Initializing OMNI VR WebXR...</div>
    <button id="vr-button">Enter VR</button>

    <div id="info-panel">
        <h3>🎮 OMNI VR Controls</h3>
        <p>Use your controllers to interact with the virtual environment.</p>
        <p>Session ID: {session_id}</p>
        <p>Device: {session.capabilities.max_resolution[0]}x{session.capabilities.max_resolution[1]} @ {session.capabilities.refresh_rate}Hz</p>
    </div>

    <!-- WebXR Scene Container -->
    <div id="webxr-scene"></div>

    <script>
        // OMNI VR WebXR Integration
        class OmniVRWebXR {{
            constructor() {{
                this.sessionId = '{session_id}';
                this.deviceId = '{session.device_id}';
                this.vrButton = document.getElementById('vr-button');
                this.status = document.getElementById('status');
                this.infoPanel = document.getElementById('info-panel');
                this.sceneContainer = document.getElementById('webxr-scene');

                this.isVRActive = false;
                this.xrSession = null;
                this.gl = null;
                this.animationFrame = null;

                this.init();
            }}

            async init() {{
                this.updateStatus('Checking WebXR support...');

                if (!navigator.xr) {{
                    this.updateStatus('WebXR not supported in this browser');
                    this.vrButton.disabled = true;
                    return;
                }}

                // Check for immersive VR support
                try {{
                    const supported = await navigator.xr.isSessionSupported('immersive-vr');
                    if (supported) {{
                        this.updateStatus('WebXR supported - Ready for VR');
                        this.vrButton.addEventListener('click', () => this.enterVR());
                    }} else {{
                        this.updateStatus('Immersive VR not supported');
                        this.vrButton.disabled = true;
                    }}
                }} catch (error) {{
                    this.updateStatus('Error checking WebXR support: ' + error.message);
                    this.vrButton.disabled = true;
                }}
            }}

            async enterVR() {{
                try {{
                    this.updateStatus('Entering VR mode...');

                    const sessionInit = {{
                        requiredFeatures: {json.dumps(self.config['required_features'])},
                        optionalFeatures: {json.dumps(self.config['optional_features'])}
                    }};

                    this.xrSession = await navigator.xr.requestSession('immersive-vr', sessionInit);

                    // Set up session event listeners
                    this.xrSession.addEventListener('end', () => this.exitVR());
                    this.xrSession.addEventListener('inputsourceschange', (event) => this.handleInputSourcesChange(event));

                    // Create WebGL context
                    this.gl = this.createWebGLContext();

                    // Set up reference space
                    const referenceSpace = await this.xrSession.requestReferenceSpace('{self.config['reference_space_type']}');

                    // Start render loop
                    this.animationFrame = this.xrSession.requestAnimationFrame((time, frame) => this.renderFrame(time, frame, referenceSpace));

                    this.isVRActive = true;
                    this.vrButton.textContent = 'Exit VR';
                    this.updateStatus('In VR Mode - Enjoy your experience!');
                    this.infoPanel.style.display = 'block';

                    // Send session start event to OMNI platform
                    await this.sendToOMNI({{
                        type: 'session_started',
                        session_id: this.sessionId,
                        timestamp: new Date().toISOString()
                    }});

                }} catch (error) {{
                    this.updateStatus('Failed to enter VR: ' + error.message);
                    console.error('VR entry error:', error);
                }}
            }}

            exitVR() {{
                if (this.xrSession) {{
                    this.xrSession.end();
                }}

                this.isVRActive = false;
                this.vrButton.textContent = 'Enter VR';
                this.updateStatus('VR session ended');
                this.infoPanel.style.display = 'none';

                // Cancel animation frame
                if (this.animationFrame) {{
                    this.xrSession.cancelAnimationFrame(this.animationFrame);
                }}

                // Send session end event to OMNI platform
                this.sendToOMNI({{
                    type: 'session_ended',
                    session_id: this.sessionId,
                    timestamp: new Date().toISOString()
                }});
            }}

            createWebGLContext() {{
                const canvas = document.createElement('canvas');
                canvas.width = {session.capabilities.max_resolution[0]};
                canvas.height = {session.capabilities.max_resolution[1]};
                canvas.style.display = 'none';
                document.body.appendChild(canvas);

                const gl = canvas.getContext('webgl', {{
                    xrCompatible: true
                }});

                if (!gl) {{
                    throw new Error('WebGL not supported');
                }}

                return gl;
            }}

            renderFrame(time, frame, referenceSpace) {{
                if (!this.isVRActive) return;

                const pose = frame.getViewerPose(referenceSpace);
                if (!pose) {{
                    this.xrSession.requestAnimationFrame((time, frame) => this.renderFrame(time, frame, referenceSpace));
                    return;
                }}

                // Clear canvas
                this.gl.clearColor(0.1, 0.1, 0.1, 1.0);
                this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT);

                // Render VR frame (simplified)
                this.renderVRScene(pose);

                // Handle input events
                this.processInputEvents(frame);

                // Continue render loop
                this.animationFrame = this.xrSession.requestAnimationFrame((time, frame) => this.renderFrame(time, frame, referenceSpace));
            }}

            renderVRScene(pose) {{
                // Simplified VR scene rendering
                // In a real implementation, this would use Three.js or A-Frame

                pose.views.forEach((view) => {{
                    const viewport = this.gl.getParameter(this.gl.VIEWPORT);
                    this.gl.viewport(viewport[0], viewport[1], viewport[2], viewport[3]);

                    // Set up view matrix and projection matrix
                    // Render 3D content here
                }});
            }}

            processInputEvents(frame) {{
                // Process input sources (controllers, hands, etc.)
                const inputSources = frame.getInputSources();

                inputSources.forEach(async (inputSource, index) => {{
                    const inputPose = frame.getPose(inputSource.gripSpace);

                    if (inputPose) {{
                        const hand = index === 0 ? 'left' : 'right';

                        // Send input data to OMNI platform
                        await this.sendInputEvent('controller_6dof', {{
                            hand: hand,
                            position: inputPose.transform.position,
                            rotation: inputPose.transform.orientation,
                            buttons: this.getButtonStates(inputSource),
                            axes: this.getAxesValues(inputSource)
                        }}, hand);
                    }}

                    // Handle hand tracking if available
                    if (inputSource.hand) {{
                        await this.processHandTracking(inputSource, frame, index === 0 ? 'left' : 'right');
                    }}
                }});
            }}

            async processHandTracking(inputSource, frame, hand) {{
                const handPose = frame.getPose(inputSource.gripSpace);

                if (handPose) {{
                    // Send hand tracking data
                    await this.sendInputEvent('hand_tracking', {{
                        hand: hand,
                        wrist: handPose.transform,
                        joints: this.getHandJoints(inputSource.hand)
                    }}, hand);
                }}
            }}

            getHandJoints(hand) {{
                // Get hand joint positions and rotations
                const joints = [];

                if (hand && hand.length > 0) {{
                    for (let i = 0; i < hand.length; i++) {{
                        joints.push({{
                            position: hand[i].position || {{x: 0, y: 0, z: 0}},
                            rotation: hand[i].orientation || {{x: 0, y: 0, z: 0, w: 1}}
                        }});
                    }}
                }}

                return joints;
            }}

            getButtonStates(inputSource) {{
                const buttons = {{}};

                if (inputSource.gamepad) {{
                    inputSource.gamepad.buttons.forEach((button, index) => {{
                        buttons['button_' + index] = {{
                            pressed: button.pressed,
                            touched: button.touched,
                            value: button.value
                        }};
                    }});
                }}

                return buttons;
            }}

            getAxesValues(inputSource) {{
                const axes = {{}};

                if (inputSource.gamepad) {{
                    inputSource.gamepad.axes.forEach((value, index) => {{
                        axes['axis_' + index] = value;
                    }});
                }}

                return axes;
            }}

            handleInputSourcesChange(event) {{
                this.updateStatus('Input sources changed: ' + event.added.length + ' added, ' + event.removed.length + ' removed');
            }}

            async sendInputEvent(inputType, data, hand = '') {{
                try {{
                    await this.sendToOMNI({{
                        type: 'input_event',
                        input_type: inputType,
                        data: data,
                        hand: hand,
                        timestamp: new Date().toISOString()
                    }});
                }} catch (error) {{
                    console.error('Error sending input event:', error);
                }}
            }}

            async sendToOMNI(data) {{
                try {{
                    // Send via WebSocket if available
                    if (window.omniWebSocket && window.omniWebSocket.readyState === WebSocket.OPEN) {{
                        window.omniWebSocket.send(JSON.stringify(data));
                    }} else {{
                        // Fallback to fetch API
                        await fetch('/vr/input', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                session_id: this.sessionId,
                                ...data
                            }})
                        }});
                    }}
                }} catch (error) {{
                    console.error('Error sending to OMNI:', error);
                }}
            }}

            updateStatus(message) {{
                if (this.status) {{
                    this.status.textContent = message;
                }}
                console.log('VR Status:', message);
            }}
        }}

        // Initialize OMNI VR WebXR
        const omniVR = new OmniVRWebXR();

        // Connect to OMNI WebSocket for real-time communication
        window.omniWebSocket = new WebSocket('ws://localhost:3090/vr/websocket');

        window.omniWebSocket.onopen = function(event) {{
            console.log('Connected to OMNI VR WebSocket');
        }};

        window.omniWebSocket.onerror = function(error) {{
            console.error('OMNI VR WebSocket error:', error);
        }};

        window.omniWebSocket.onclose = function(event) {{
            console.log('OMNI VR WebSocket closed');
        }};

        // Handle window visibility change (for VR focus)
        document.addEventListener('visibilitychange', function() {{
            if (document.hidden) {{
                console.log('VR app hidden');
            }} else {{
                console.log('VR app visible');
            }}
        }});
    </script>
</body>
</html>
            """

            return html_content

        except Exception as e:
            return f"<html><body>Error generating WebXR HTML: {e}</body></html>"

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get WebXR session information"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}

        session = self.sessions[session_id]

        return {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "session_type": session.session_type.value,
            "input_types": [it.value for it in session.input_types],
            "capabilities": {
                "max_resolution": session.capabilities.max_resolution,
                "refresh_rate": session.capabilities.refresh_rate,
                "supports_hand_tracking": session.capabilities.supports_hand_tracking,
                "supports_eye_tracking": session.capabilities.supports_eye_tracking,
                "supports_passthrough": session.capabilities.supports_passthrough
            },
            "webrtc_session_id": session.webrtc_session_id,
            "started_at": session.started_at.isoformat(),
            "status": session.status,
            "frame_rate": session.frame_rate,
            "latency_ms": session.latency_ms
        }

    def get_integration_stats(self) -> Dict[str, Any]:
        """Get WebXR integration statistics"""
        total_sessions = len(self.sessions)
        active_sessions = len([s for s in self.sessions.values() if s.status == "active"])

        # Calculate average frame rate
        avg_frame_rate = 0.0
        if active_sessions > 0:
            frame_rate_sum = sum(s.frame_rate for s in self.sessions.values() if s.status == "active")
            avg_frame_rate = frame_rate_sum / active_sessions

        # Calculate average latency
        avg_latency = 0.0
        if active_sessions > 0:
            latency_sum = sum(s.latency_ms for s in self.sessions.values() if s.status == "active")
            avg_latency = latency_sum / active_sessions

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "average_frame_rate": round(avg_frame_rate, 2),
            "average_latency_ms": round(avg_latency, 2),
            "input_events_processed": len(self.input_events),
            "webrtc_integration": self.webrtc_gateway is not None,
            "running": self._running,
            "last_updated": datetime.now().isoformat()
        }

# Global WebXR integration instance
omni_vr_webxr = None

def initialize_vr_webxr_integration(webrtc_gateway=None) -> OmniVRWebXRIntegration:
    """Initialize VR WebXR integration"""
    global omni_vr_webxr
    omni_vr_webxr = OmniVRWebXRIntegration(webrtc_gateway)
    return omni_vr_webxr

def get_vr_webxr_integration() -> OmniVRWebXRIntegration:
    """Get global VR WebXR integration instance"""
    return omni_vr_webxr

# WebXR API functions
async def create_webxr_session(device_id: str, user_agent: str = "", webrtc_enabled: bool = True) -> str:
    """Create WebXR session"""
    if omni_vr_webxr:
        return await omni_vr_webxr.create_session(device_id, user_agent, webrtc_enabled)
    return None

async def handle_vr_input_event(session_id: str, input_type: str, event_data: Dict[str, Any], hand: str = "") -> bool:
    """Handle VR input event"""
    if omni_vr_webxr:
        return await omni_vr_webxr.handle_input_event(session_id, input_type, event_data, hand)
    return False

def generate_webxr_page(session_id: str, vr_project_url: str = "") -> str:
    """Generate WebXR HTML page"""
    if omni_vr_webxr:
        return omni_vr_webxr.generate_webxr_html(session_id, vr_project_url)
    return "<html><body>Error: WebXR integration not initialized</body></html>"

def get_webxr_session_info(session_id: str) -> Dict[str, Any]:
    """Get WebXR session info"""
    if omni_vr_webxr:
        return omni_vr_webxr.get_session_info(session_id)
    return {"error": "WebXR integration not initialized"}

def get_webxr_stats() -> Dict[str, Any]:
    """Get WebXR integration stats"""
    if omni_vr_webxr:
        return omni_vr_webxr.get_integration_stats()
    return {"error": "WebXR integration not initialized"}

async def main():
    """Main function for testing WebXR integration"""
    print("🧪 Testing OMNI VR WebXR Integration...")

    # Initialize WebXR integration
    webxr = initialize_vr_webxr_integration()

    try:
        # Start integration
        await webxr.start()

        # Create test session
        session_id = await create_webxr_session("test_oculus_quest", "Oculus Quest 2")

        if session_id:
            print(f"✅ WebXR session created: {session_id}")

            # Get session info
            session_info = get_webxr_session_info(session_id)
            print(f"📊 Session info: {session_info}")

            # Generate WebXR HTML
            html_content = generate_webxr_page(session_id)
            print(f"📄 Generated WebXR HTML: {len(html_content)} characters")

            # Simulate input events
            await handle_vr_input_event(session_id, "controller_6dof", {
                "position": {"x": 0.1, "y": 0.2, "z": -0.5},
                "rotation": {"x": 0, "y": 0.1, "z": 0, "w": 1},
                "buttons": {"trigger": 0.8, "grip": 0.9}
            }, "right")

            # Monitor for a while
            for i in range(5):
                await asyncio.sleep(1)
                stats = get_webxr_stats()
                print(f"📊 WebXR stats: {stats['active_sessions']} active sessions")

        else:
            print("❌ Failed to create WebXR session")

    finally:
        await webxr.stop()

    print("✅ OMNI VR WebXR Integration test completed!")

if __name__ == "__main__":
    asyncio.run(main())