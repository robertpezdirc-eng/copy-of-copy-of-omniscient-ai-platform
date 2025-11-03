"""
Mobile Push Notification Routes
Handles device registration and push notification delivery
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/mobile/notifications",
    tags=["Mobile Notifications"]
)


class DeviceRegistration(BaseModel):
    """Device registration model"""
    token: str
    platform: str  # 'ios' or 'android'
    device_id: Optional[str] = None
    user_id: Optional[str] = None
    topics: Optional[List[str]] = []


class PushNotification(BaseModel):
    """Push notification model"""
    title: str
    body: str
    data: Optional[Dict[str, Any]] = {}
    tokens: Optional[List[str]] = None
    topic: Optional[str] = None
    priority: Optional[str] = "high"
    badge: Optional[int] = None
    sound: Optional[str] = "default"


class NotificationResponse(BaseModel):
    """Notification response model"""
    success: bool
    message: str
    sent_count: Optional[int] = 0
    failed_count: Optional[int] = 0


# In-memory storage (replace with database in production)
registered_devices: Dict[str, DeviceRegistration] = {}


@router.post("/register", response_model=NotificationResponse)
async def register_device(device: DeviceRegistration):
    """
    Register a device for push notifications
    
    **Parameters:**
    - **token**: FCM/APNs device token
    - **platform**: 'ios' or 'android'
    - **device_id**: Unique device identifier
    - **user_id**: User ID associated with the device
    - **topics**: List of topics to subscribe to
    
    **Returns:**
    - Success status and message
    """
    try:
        if not device.token:
            raise HTTPException(status_code=400, detail="Device token is required")
        
        if device.platform not in ['ios', 'android']:
            raise HTTPException(status_code=400, detail="Platform must be 'ios' or 'android'")
        
        # Store device registration
        registered_devices[device.token] = device
        
        logger.info(f"Device registered: {device.platform} - Token: {device.token[:20]}...")
        
        return NotificationResponse(
            success=True,
            message=f"Device registered successfully for {device.platform}",
            sent_count=1
        )
    
    except Exception as e:
        logger.error(f"Error registering device: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unregister/{token}")
async def unregister_device(token: str):
    """
    Unregister a device from push notifications
    
    **Parameters:**
    - **token**: FCM/APNs device token
    
    **Returns:**
    - Success status and message
    """
    try:
        if token in registered_devices:
            del registered_devices[token]
            logger.info(f"Device unregistered: {token[:20]}...")
            return NotificationResponse(
                success=True,
                message="Device unregistered successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Device not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering device: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification: PushNotification,
    background_tasks: BackgroundTasks
):
    """
    Send push notification to devices
    
    **Parameters:**
    - **title**: Notification title
    - **body**: Notification body
    - **data**: Additional data payload (optional)
    - **tokens**: List of device tokens to send to (optional)
    - **topic**: Topic to send to all subscribed devices (optional)
    - **priority**: Notification priority ('high' or 'normal')
    - **badge**: Badge count for iOS (optional)
    - **sound**: Notification sound (optional)
    
    **Returns:**
    - Success status and counts
    
    **Note:** In production, this should integrate with Firebase Cloud Messaging
    and Apple Push Notification Service. This is a mock implementation.
    """
    try:
        sent_count = 0
        failed_count = 0
        
        # Mock implementation - in production, use FCM/APNs
        if notification.tokens:
            for token in notification.tokens:
                if token in registered_devices:
                    sent_count += 1
                    logger.info(f"Notification sent to {token[:20]}...")
                else:
                    failed_count += 1
                    logger.warning(f"Device not found: {token[:20]}...")
        
        elif notification.topic:
            # Send to all devices subscribed to topic
            for token, device in registered_devices.items():
                if notification.topic in device.topics:
                    sent_count += 1
                    logger.info(f"Notification sent to topic {notification.topic}: {token[:20]}...")
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Either tokens or topic must be provided"
            )
        
        logger.info(
            f"Notification '{notification.title}' sent to {sent_count} devices, "
            f"{failed_count} failed"
        )
        
        return NotificationResponse(
            success=True,
            message="Notification sent successfully",
            sent_count=sent_count,
            failed_count=failed_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices")
async def get_registered_devices():
    """
    Get list of registered devices
    
    **Returns:**
    - List of registered devices (tokens masked for security)
    """
    try:
        devices = []
        for token, device in registered_devices.items():
            devices.append({
                "token": token[:20] + "...",
                "platform": device.platform,
                "device_id": device.device_id,
                "user_id": device.user_id,
                "topics": device.topics
            })
        
        return {
            "success": True,
            "count": len(devices),
            "devices": devices
        }
    
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast", response_model=NotificationResponse)
async def broadcast_notification(notification: PushNotification):
    """
    Broadcast notification to all registered devices
    
    **Parameters:**
    - **title**: Notification title
    - **body**: Notification body
    - **data**: Additional data payload (optional)
    - **priority**: Notification priority ('high' or 'normal')
    
    **Returns:**
    - Success status and sent count
    """
    try:
        sent_count = len(registered_devices)
        
        for token in registered_devices.keys():
            logger.info(f"Broadcast notification sent to {token[:20]}...")
        
        logger.info(f"Broadcast notification '{notification.title}' sent to {sent_count} devices")
        
        return NotificationResponse(
            success=True,
            message="Broadcast notification sent successfully",
            sent_count=sent_count,
            failed_count=0
        )
    
    except Exception as e:
        logger.error(f"Error broadcasting notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
