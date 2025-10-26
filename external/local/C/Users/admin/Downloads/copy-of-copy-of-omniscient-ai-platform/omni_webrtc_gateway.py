#!/usr/bin/env python3
"""
OMNI WebRTC Gateway for Real-time Video/VR
Advanced WebRTC gateway for low-latency video streaming and VR communication
Supports STUN/TURN servers, media routing, and real-time data channels
"""

import asyncio
import json
import time
import uuid
import aiohttp
import aiortc
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
import threading
from enum import Enum

class WebRTCMediaType(Enum):
    """WebRTC media types"""
    VIDEO = "video"
    AUDIO = "audio"
    DATA = "data"
    SCREEN = "screen"

class WebRTCSessionState(Enum):
    """WebRTC session states"""
    NEW = "new"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    CLOSED = "closed"

@dataclass
class WebRTCSession:
    """WebRTC session information"""
    session_id: str
    device_id: str
    peer_connection: aiortc.RTCPeerConnection
    data_channels: Dict[str, aiortc.RTCDataChannel] = field(default_factory=dict)
    media_tracks: Dict[str, Any] = field(default_factory=dict)
    state: WebRTCSessionState = WebRTCSessionState.NEW
    created_at: datetime = field(default_factory=datetime.now)
    connected_at: Optional[datetime] = None
    bandwidth_usage: float = 0.0
    latency_ms: float = 0.0

@dataclass
class STUNServer:
    """STUN server configuration"""
    urls: List[str]
    username: str = ""
    password: str = ""

@dataclass
class TURNServer:
    """TURN server configuration"""
    urls: List[str]
    username: str
    password: str

class OmniWebRTCGateway:
    """WebRTC Gateway for real-time communications"""

    def __init__(self, stun_servers: List[STUNServer] = None, turn_servers: List[TURNServer] = None):
        self.stun_servers = stun_servers or [
            STUNServer(urls=["stun:stun.l.google.com:19302"]),
            STUNServer(urls=["stun:stun1.l.google.com:19302"])
        ]

        self.turn_servers = turn_servers or []

        # Session management
        self.sessions: Dict[str, WebRTCSession] = {}
        self.session_handlers = {}

        # ICE configuration
        self.ice_configuration = self._build_ice_configuration()

        # Media codecs
        self.video_codecs = [
            aiortc.RTCRtpCodecParameters(
                mimeType="video/VP8",
                clockRate=90000,
                rtcpFeedback=[
                    aiortc.RTCRtcpFeedback(type="ccm", parameter="fir"),
                    aiortc.RTCRtcpFeedback(type="nack"),
                    aiortc.RTCRtcpFeedback(type="nack", parameter="pli"),
                ]
            ),
            aiortc.RTCRtpCodecParameters(
                mimeType="video/H264",
                clockRate=90000,
                fmtp="level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42001f"
            )
        ]

        self.audio_codecs = [
            aiortc.RTCRtpCodecParameters(
                mimeType="audio/opus",
                clockRate=48000,
                channels=2
            ),
            aiortc.RTCRtpCodecParameters(
                mimeType="audio/PCMU",
                clockRate=8000,
                channels=1
            )
        ]

        # Background tasks
        self._running = False
        self._cleanup_task = None

        print("📹 OMNI WebRTC Gateway initialized")

    def _build_ice_configuration(self) -> Dict[str, Any]:
        """Build ICE server configuration"""
        ice_servers = []

        # Add STUN servers
        for stun in self.stun_servers:
            for url in stun.urls:
                ice_servers.append({"urls": url})

        # Add TURN servers
        for turn in self.turn_servers:
            for url in turn.urls:
                ice_servers.append({
                    "urls": url,
                    "username": turn.username,
                    "credential": turn.password
                })

        return {"iceServers": ice_servers}

    async def start(self) -> bool:
        """Start WebRTC gateway"""
        try:
            self._running = True

            # Start session cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_sessions())

            print("✅ OMNI WebRTC Gateway started")
            return True

        except Exception as e:
            print(f"❌ Failed to start WebRTC gateway: {e}")
            return False

    async def stop(self):
        """Stop WebRTC gateway"""
        try:
            self._running = False

            # Close all sessions
            for session in self.sessions.values():
                await self.close_session(session.session_id)

            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()

            print("🛑 OMNI WebRTC Gateway stopped")

        except Exception as e:
            print(f"⚠️ Error stopping WebRTC gateway: {e}")

    async def create_session(self, device_id: str, media_types: List[WebRTCMediaType] = None) -> str:
        """Create new WebRTC session"""
        try:
            session_id = str(uuid.uuid4())

            # Create peer connection
            pc = aiortc.RTCPeerConnection(configuration=self.ice_configuration)

            # Set up event handlers
            pc.on("connectionstatechange", lambda: self._on_connection_state_change(session_id))
            pc.on("iceconnectionstatechange", lambda: self._on_ice_connection_state_change(session_id))
            pc.on("icegatheringstatechange", lambda: self._on_ice_gathering_state_change(session_id))

            # Create data channel for control messages
            data_channel = pc.createDataChannel("omni_control")
            data_channel.on("message", lambda message: self._on_data_channel_message(session_id, message))

            # Create session
            session = WebRTCSession(
                session_id=session_id,
                device_id=device_id,
                peer_connection=pc,
                data_channels={"omni_control": data_channel}
            )

            self.sessions[session_id] = session

            print(f"🎥 WebRTC session created: {session_id} for device {device_id}")
            return session_id

        except Exception as e:
            print(f"❌ Failed to create WebRTC session: {e}")
            return None

    async def close_session(self, session_id: str) -> bool:
        """Close WebRTC session"""
        try:
            if session_id not in self.sessions:
                return False

            session = self.sessions[session_id]

            # Close peer connection
            await session.peer_connection.close()

            # Remove session
            del self.sessions[session_id]

            print(f"🎥 WebRTC session closed: {session_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to close WebRTC session: {e}")
            return False

    async def handle_offer(self, session_id: str, offer: aiortc.RTCSessionDescription) -> Dict[str, Any]:
        """Handle WebRTC offer from device"""
        try:
            if session_id not in self.sessions:
                return {"error": "Session not found"}

            session = self.sessions[session_id]

            # Set remote description
            await session.peer_connection.setRemoteDescription(offer)

            # Create answer
            answer = await session.peer_connection.createAnswer()
            await session.peer_connection.setLocalDescription(answer)

            # Update session state
            session.state = WebRTCSessionState.CONNECTED
            session.connected_at = datetime.now()

            return {
                "type": "answer",
                "sdp": answer.sdp,
                "type": answer.type
            }

        except Exception as e:
            print(f"❌ Failed to handle WebRTC offer: {e}")
            session.state = WebRTCSessionState.FAILED
            return {"error": str(e)}

    async def add_media_track(self, session_id: str, media_type: WebRTCMediaType, track: Any) -> bool:
        """Add media track to session"""
        try:
            if session_id not in self.sessions:
                return False

            session = self.sessions[session_id]

            # Add track to peer connection
            if media_type == WebRTCMediaType.VIDEO:
                await session.peer_connection.addTrack(track, None)
            elif media_type == WebRTCMediaType.AUDIO:
                await session.peer_connection.addTrack(track, None)

            session.media_tracks[media_type.value] = track

            print(f"📹 Added {media_type.value} track to session {session_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to add media track: {e}")
            return False

    async def send_data_channel_message(self, session_id: str, channel_name: str, message: Dict[str, Any]) -> bool:
        """Send message via data channel"""
        try:
            if session_id not in self.sessions:
                return False

            session = self.sessions[session_id]

            if channel_name not in session.data_channels:
                return False

            data_channel = session.data_channels[channel_name]

            # Send message
            message_json = json.dumps(message)
            data_channel.send(message_json)

            return True

        except Exception as e:
            print(f"❌ Failed to send data channel message: {e}")
            return False

    def _on_connection_state_change(self, session_id: str):
        """Handle connection state change"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                pc = session.peer_connection

                print(f"🔗 WebRTC connection state: {pc.connectionState}")

                if pc.connectionState == "connected":
                    session.state = WebRTCSessionState.CONNECTED
                    session.connected_at = datetime.now()
                elif pc.connectionState == "failed":
                    session.state = WebRTCSessionState.FAILED
                elif pc.connectionState == "closed":
                    session.state = WebRTCSessionState.CLOSED

        except Exception as e:
            print(f"⚠️ Connection state change error: {e}")

    def _on_ice_connection_state_change(self, session_id: str):
        """Handle ICE connection state change"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                pc = session.peer_connection

                print(f"🧊 ICE connection state: {pc.iceConnectionState}")

        except Exception as e:
            print(f"⚠️ ICE connection state change error: {e}")

    def _on_ice_gathering_state_change(self, session_id: str):
        """Handle ICE gathering state change"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                pc = session.peer_connection

                print(f"🧊 ICE gathering state: {pc.iceGatheringState}")

        except Exception as e:
            print(f"⚠️ ICE gathering state change error: {e}")

    def _on_data_channel_message(self, session_id: str, message):
        """Handle data channel message"""
        try:
            data = json.loads(message)

            # Route message to appropriate handler
            message_type = data.get("type", "unknown")

            if message_type in self.session_handlers:
                asyncio.create_task(self.session_handlers[message_type](session_id, data))
            else:
                print(f"⚠️ Unknown data channel message type: {message_type}")

        except Exception as e:
            print(f"⚠️ Data channel message error: {e}")

    async def _cleanup_sessions(self):
        """Clean up expired sessions"""
        while self._running:
            try:
                current_time = datetime.now()
                expired_sessions = []

                for session_id, session in self.sessions.items():
                    # Check for expired sessions (no activity for 5 minutes)
                    if session.state == WebRTCSessionState.CONNECTED:
                        if session.connected_at and (current_time - session.connected_at).seconds > 300:
                            expired_sessions.append(session_id)
                    elif session.state in [WebRTCSessionState.FAILED, WebRTCSessionState.CLOSED]:
                        expired_sessions.append(session_id)

                # Close expired sessions
                for session_id in expired_sessions:
                    await self.close_session(session_id)
                    print(f"⏰ Closed expired WebRTC session: {session_id}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                print(f"⚠️ Session cleanup error: {e}")
                await asyncio.sleep(60)

    def register_session_handler(self, message_type: str, handler: Callable[[str, Dict[str, Any]], None]):
        """Register session message handler"""
        self.session_handlers[message_type] = handler

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get WebRTC session information"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}

        session = self.sessions[session_id]

        return {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "state": session.state.value,
            "created_at": session.created_at.isoformat(),
            "connected_at": session.connected_at.isoformat() if session.connected_at else None,
            "bandwidth_usage": session.bandwidth_usage,
            "latency_ms": session.latency_ms,
            "media_tracks": list(session.media_tracks.keys()),
            "data_channels": list(session.data_channels.keys())
        }

    def get_gateway_stats(self) -> Dict[str, Any]:
        """Get WebRTC gateway statistics"""
        total_sessions = len(self.sessions)
        connected_sessions = len([s for s in self.sessions.values() if s.state == WebRTCSessionState.CONNECTED])
        failed_sessions = len([s for s in self.sessions.values() if s.state == WebRTCSessionState.FAILED])

        # Calculate average latency
        avg_latency = 0.0
        if connected_sessions > 0:
            latency_sum = sum(s.latency_ms for s in self.sessions.values() if s.state == WebRTCSessionState.CONNECTED)
            avg_latency = latency_sum / connected_sessions

        return {
            "total_sessions": total_sessions,
            "connected_sessions": connected_sessions,
            "failed_sessions": failed_sessions,
            "average_latency_ms": round(avg_latency, 2),
            "stun_servers": len(self.stun_servers),
            "turn_servers": len(self.turn_servers),
            "running": self._running,
            "last_updated": datetime.now().isoformat()
        }

# Global WebRTC gateway instance
omni_webrtc_gateway = None

def initialize_webrtc_gateway(stun_servers: List[STUNServer] = None, turn_servers: List[TURNServer] = None) -> OmniWebRTCGateway:
    """Initialize WebRTC gateway"""
    global omni_webrtc_gateway
    omni_webrtc_gateway = OmniWebRTCGateway(stun_servers, turn_servers)
    return omni_webrtc_gateway

def get_webrtc_gateway() -> OmniWebRTCGateway:
    """Get global WebRTC gateway instance"""
    return omni_webrtc_gateway

# WebRTC API functions
async def create_webrtc_session(device_id: str, media_types: List[str] = None) -> str:
    """Create WebRTC session"""
    if omni_webrtc_gateway:
        webrtc_media_types = [WebRTCMediaType(mt) for mt in (media_types or ["video", "audio"])]
        return await omni_webrtc_gateway.create_session(device_id, webrtc_media_types)
    return None

async def handle_webrtc_offer(session_id: str, offer_sdp: str) -> Dict[str, Any]:
    """Handle WebRTC offer"""
    if omni_webrtc_gateway:
        offer = aiortc.RTCSessionDescription(sdp=offer_sdp, type="offer")
        return await omni_webrtc_gateway.handle_offer(session_id, offer)
    return {"error": "WebRTC gateway not initialized"}

def get_webrtc_session_info(session_id: str) -> Dict[str, Any]:
    """Get WebRTC session info"""
    if omni_webrtc_gateway:
        return omni_webrtc_gateway.get_session_info(session_id)
    return {"error": "WebRTC gateway not initialized"}

def get_webrtc_stats() -> Dict[str, Any]:
    """Get WebRTC gateway stats"""
    if omni_webrtc_gateway:
        return omni_webrtc_gateway.get_gateway_stats()
    return {"error": "WebRTC gateway not initialized"}

async def main():
    """Main function for testing WebRTC gateway"""
    print("🧪 Testing OMNI WebRTC Gateway...")

    # Initialize WebRTC gateway
    gateway = initialize_webrtc_gateway()

    try:
        # Start gateway
        await gateway.start()

        # Create test session
        session_id = await create_webrtc_session("test_device_001", ["video", "audio"])

        if session_id:
            print(f"✅ WebRTC session created: {session_id}")

            # Get session info
            session_info = get_webrtc_session_info(session_id)
            print(f"📊 Session info: {session_info}")

            # Monitor for a while
            for i in range(5):
                await asyncio.sleep(1)
                stats = get_webrtc_stats()
                print(f"📊 Gateway stats: {stats['connected_sessions']} connected sessions")

        else:
            print("❌ Failed to create WebRTC session")

    finally:
        await gateway.stop()

    print("✅ OMNI WebRTC Gateway test completed!")

if __name__ == "__main__":
    asyncio.run(main())