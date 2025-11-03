"""
WebSocket Service for Real-time Communication
Provides real-time updates, live chat, and presence tracking
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
from dataclasses import dataclass, asdict


@dataclass
class WebSocketConnection:
    """WebSocket connection details"""
    connection_id: str
    tenant_id: str
    user_id: str
    connected_at: datetime
    last_activity: datetime
    rooms: List[str]
    metadata: Dict[str, Any]


@dataclass
class ChatMessage:
    """Chat message structure"""
    message_id: str
    room_id: str
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime
    message_type: str  # text, image, file, system
    metadata: Dict[str, Any]


@dataclass
class PresenceStatus:
    """User presence status"""
    user_id: str
    status: str  # online, away, busy, offline
    last_seen: datetime
    current_room: Optional[str]


class WebSocketService:
    """Service for managing WebSocket connections and real-time communication"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.rooms: Dict[str, List[str]] = {}  # room_id -> [connection_ids]
        self.user_connections: Dict[str, List[str]] = {}  # user_id -> [connection_ids]
        self.presence: Dict[str, PresenceStatus] = {}
        
    async def connect(
        self,
        connection_id: str,
        tenant_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WebSocketConnection:
        """Register new WebSocket connection"""
        connection = WebSocketConnection(
            connection_id=connection_id,
            tenant_id=tenant_id,
            user_id=user_id,
            connected_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            rooms=[],
            metadata=metadata or {}
        )
        
        self.connections[connection_id] = connection
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        # Update presence
        self.presence[user_id] = PresenceStatus(
            user_id=user_id,
            status="online",
            last_seen=datetime.utcnow(),
            current_room=None
        )
        
        # Broadcast presence update
        await self._broadcast_presence_update(user_id, "online")
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        # Leave all rooms
        for room_id in connection.rooms:
            await self.leave_room(connection_id, room_id)
        
        # Remove connection
        del self.connections[connection_id]
        
        # Update user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                # Update presence to offline
                self.presence[user_id] = PresenceStatus(
                    user_id=user_id,
                    status="offline",
                    last_seen=datetime.utcnow(),
                    current_room=None
                )
                await self._broadcast_presence_update(user_id, "offline")
    
    async def join_room(self, connection_id: str, room_id: str):
        """Join a chat room"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        if room_id not in connection.rooms:
            connection.rooms.append(room_id)
        
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        
        if connection_id not in self.rooms[room_id]:
            self.rooms[room_id].append(connection_id)
        
        # Update presence
        if connection.user_id in self.presence:
            self.presence[connection.user_id].current_room = room_id
        
        # Broadcast join event
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "user_id": connection.user_id,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_connection=connection_id)
    
    async def leave_room(self, connection_id: str, room_id: str):
        """Leave a chat room"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        if room_id in connection.rooms:
            connection.rooms.remove(room_id)
        
        if room_id in self.rooms and connection_id in self.rooms[room_id]:
            self.rooms[room_id].remove(connection_id)
            
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        # Update presence
        if connection.user_id in self.presence:
            self.presence[connection.user_id].current_room = None
        
        # Broadcast leave event
        await self.broadcast_to_room(room_id, {
            "type": "user_left",
            "user_id": connection.user_id,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_message(
        self,
        connection_id: str,
        room_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Send chat message to room"""
        if connection_id not in self.connections:
            raise ValueError("Connection not found")
        
        connection = self.connections[connection_id]
        
        if room_id not in connection.rooms:
            raise ValueError("Not in room")
        
        message = ChatMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}_{connection_id}",
            room_id=room_id,
            sender_id=connection.user_id,
            sender_name=connection.metadata.get("name", "Unknown"),
            content=content,
            timestamp=datetime.utcnow(),
            message_type=message_type,
            metadata=metadata or {}
        )
        
        # Broadcast to room
        await self.broadcast_to_room(room_id, {
            "type": "chat_message",
            "message": asdict(message)
        })
        
        return message
    
    async def broadcast_to_room(
        self,
        room_id: str,
        data: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ):
        """Broadcast message to all connections in room"""
        if room_id not in self.rooms:
            return
        
        tasks = []
        for connection_id in self.rooms[room_id]:
            if connection_id != exclude_connection:
                tasks.append(self._send_to_connection(connection_id, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_user(self, user_id: str, data: Dict[str, Any]):
        """Broadcast message to all user's connections"""
        if user_id not in self.user_connections:
            return
        
        tasks = []
        for connection_id in self.user_connections[user_id]:
            tasks.append(self._send_to_connection(connection_id, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_tenant(self, tenant_id: str, data: Dict[str, Any]):
        """Broadcast message to all tenant connections"""
        tasks = []
        for connection in self.connections.values():
            if connection.tenant_id == tenant_id:
                tasks.append(self._send_to_connection(connection.connection_id, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_connection(self, connection_id: str, data: Dict[str, Any]):
        """Send data to specific connection (to be implemented by transport layer)"""
        # This would integrate with actual WebSocket/Socket.IO implementation
        print(f"Sending to {connection_id}: {json.dumps(data)}")
    
    async def _broadcast_presence_update(self, user_id: str, status: str):
        """Broadcast presence update to relevant connections"""
        if user_id not in self.presence:
            return
        
        presence_data = {
            "type": "presence_update",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all rooms where user was present
        for room_id, connections in self.rooms.items():
            await self.broadcast_to_room(room_id, presence_data)
    
    def get_room_users(self, room_id: str) -> List[Dict[str, Any]]:
        """Get list of users in room"""
        if room_id not in self.rooms:
            return []
        
        users = []
        seen_users = set()
        
        for connection_id in self.rooms[room_id]:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.user_id not in seen_users:
                    seen_users.add(connection.user_id)
                    users.append({
                        "user_id": connection.user_id,
                        "name": connection.metadata.get("name", "Unknown"),
                        "status": self.presence.get(connection.user_id, PresenceStatus(
                            user_id=connection.user_id,
                            status="online",
                            last_seen=datetime.utcnow(),
                            current_room=room_id
                        )).status
                    })
        
        return users
    
    def get_online_users(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get list of online users for tenant"""
        online_users = []
        seen_users = set()
        
        for connection in self.connections.values():
            if connection.tenant_id == tenant_id and connection.user_id not in seen_users:
                seen_users.add(connection.user_id)
                online_users.append({
                    "user_id": connection.user_id,
                    "name": connection.metadata.get("name", "Unknown"),
                    "status": self.presence.get(connection.user_id, PresenceStatus(
                        user_id=connection.user_id,
                        status="online",
                        last_seen=datetime.utcnow(),
                        current_room=None
                    )).status,
                    "connected_at": connection.connected_at.isoformat()
                })
        
        return online_users
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.connections),
            "total_rooms": len(self.rooms),
            "online_users": len(self.user_connections),
            "rooms_by_size": {
                room_id: len(connections)
                for room_id, connections in self.rooms.items()
            }
        }


# Global service instance
websocket_service = WebSocketService()
