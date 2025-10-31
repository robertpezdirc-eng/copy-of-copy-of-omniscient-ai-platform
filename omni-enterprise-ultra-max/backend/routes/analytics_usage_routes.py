""""""

Usage Analytics & Data Export RoutesAnalytics Routes

"""Provides usage analytics and insights per tenant

"""

from fastapi import APIRouter, Query

from datetime import datetime, timezone, timedeltafrom datetime import datetime, timezone, timedelta

import randomfrom typing import Optional, List

from fastapi import APIRouter, Depends, Header, HTTPException, Query

router = APIRouter()from jose import jwt, JWTError

import os

from utils.gcp import get_firestore

@router.get("/usage/api-calls")try:

async def get_api_usage(    from google.cloud import firestore  # type: ignore

    tenant_id: str,except Exception:

    period: str = Query("30d", description="Period: 7d, 30d, 90d")    firestore = None  # Fallback when package hints aren't available locally

):

    """Get API usage statistics"""router = APIRouter()

    

    return {JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")

        "tenant_id": tenant_id,

        "period": period,

        "total_calls": random.randint(10000, 100000),def get_current_user(authorization: Optional[str] = Header(None)):

        "successful_calls": random.randint(9000, 95000),    if not authorization or not authorization.lower().startswith("bearer "):

        "failed_calls": random.randint(100, 5000),        raise HTTPException(status_code=401, detail="Missing token")

        "average_response_time": round(random.uniform(50, 200), 2)    token = authorization.split(" ", 1)[1]

    }    try:

        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        return payload

@router.get("/usage/export")    except JWTError:

async def export_usage_data(        raise HTTPException(status_code=401, detail="Invalid token")

    tenant_id: str,

    format: str = Query("json", description="Format: json, csv, xlsx")

):@router.get("/usage/summary")

    """Export usage data"""async def get_usage_summary(

        days: int = Query(7, ge=1, le=90),

    return {    user=Depends(get_current_user)

        "tenant_id": tenant_id,):

        "format": format,    """Get usage summary for the last N days"""

        "download_url": f"https://cdn.omni-ultra.com/exports/{tenant_id}/usage.{format}",    tenant_id = user.get('tenant_id', 'anonymous')

        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()    db = get_firestore()

    }    

    summary = {

        'tenant_id': tenant_id,

@router.get("/usage/billing")        'period_days': days,

async def get_usage_billing(tenant_id: str):        'total_api_calls': 0,

    """Get usage-based billing information"""        'avg_response_time_ms': 0,

            'total_devices': 0,

    return {        'total_telemetry_points': 0,

        "tenant_id": tenant_id,        'daily_breakdown': []

        "current_period": {    }

            "api_calls": random.randint(10000, 50000),    

            "storage_gb": round(random.uniform(1, 100), 2),    # Get daily usage metrics

            "bandwidth_gb": round(random.uniform(10, 500), 2),    today = datetime.now(timezone.utc)

            "estimated_cost": round(random.uniform(50, 500), 2)    for i in range(days):

        }        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')

    }        doc_ref = db.collection('usage_metrics').document(f"{tenant_id}_{date}")

        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            api_calls = data.get('api_calls', 0)
            total_duration = data.get('total_duration_ms', 0)
            
            summary['total_api_calls'] += api_calls
            summary['daily_breakdown'].append({
                'date': date,
                'api_calls': api_calls,
                'avg_duration_ms': total_duration / api_calls if api_calls > 0 else 0
            })
    
    # Calculate average response time
    if summary['total_api_calls'] > 0:
        total_duration = sum(
            day['api_calls'] * day['avg_duration_ms'] 
            for day in summary['daily_breakdown']
        )
        summary['avg_response_time_ms'] = total_duration / summary['total_api_calls']
    
    # Count devices
    devices_ref = db.collection('devices').where('tenant_id', '==', tenant_id)
    summary['total_devices'] = len(list(devices_ref.limit(1000).stream()))
    
    # Count telemetry points (approximate)
    # In production, maintain a counter in usage_metrics
    summary['total_telemetry_points'] = summary['total_api_calls'] // 2  # Rough estimate
    
    summary['daily_breakdown'].reverse()  # Oldest to newest
    
    return summary


@router.get("/usage/api-logs")
async def get_api_logs(
    limit: int = Query(100, ge=1, le=1000),
    user=Depends(get_current_user)
):
    """Get recent API request logs"""
    tenant_id = user.get('tenant_id', 'anonymous')
    db = get_firestore()
    
    # Prefer server-side ordering; if it fails (index/direction), fall back to client-side sort
    logs: list = []
    try:
        if firestore is not None:
            logs_ref = (
                db.collection('api_logs')
                .where('tenant_id', '==', tenant_id)
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            for doc in logs_ref.stream():
                logs.append(doc.to_dict())
        else:
            # Fallback if firestore symbol isn't available
            logs_ref = (
                db.collection('api_logs')
                .where('tenant_id', '==', tenant_id)
                .limit(limit)
            )
            for doc in logs_ref.stream():
                logs.append(doc.to_dict())
            logs.sort(key=lambda d: d.get('timestamp') or '', reverse=True)
    except Exception:
        # Likely missing composite index for (tenant_id, timestamp desc). Do client-side ordering as fallback.
        logs_ref = (
            db.collection('api_logs')
            .where('tenant_id', '==', tenant_id)
            .limit(1000)
        )
        for doc in logs_ref.stream():
            logs.append(doc.to_dict())
        logs.sort(key=lambda d: d.get('timestamp') or '', reverse=True)
        logs = logs[:limit]

    return {'logs': logs, 'count': len(logs)}


@router.get("/usage/devices-telemetry")
async def get_devices_telemetry_stats(user=Depends(get_current_user)):
    """Get device and telemetry statistics"""
    tenant_id = user.get('tenant_id', 'anonymous')
    db = get_firestore()
    
    # Get all devices for tenant
    devices_ref = db.collection('devices').where('tenant_id', '==', tenant_id)
    devices = list(devices_ref.stream())
    
    stats = {
        'total_devices': len(devices),
        'devices': []
    }
    
    # Get telemetry count per device
    for device_doc in devices:
        device_data = device_doc.to_dict()
        device_id = device_data.get('device_id')
        
        # Count telemetry points for this device
        telemetry_ref = device_doc.reference.collection('telemetry')
        telemetry_count = len(list(telemetry_ref.limit(10000).stream()))
        
        # Get latest telemetry
        latest = list(telemetry_ref.order_by('ts', direction='DESCENDING').limit(1).stream())
        latest_data = latest[0].to_dict() if latest else None
        
        stats['devices'].append({
            'device_id': device_id,
            'name': device_data.get('name'),
            'model': device_data.get('model'),
            'created_at': device_data.get('created_at'),
            'telemetry_count': telemetry_count,
            'latest_telemetry': latest_data.get('metrics') if latest_data else None,
            'latest_timestamp': latest_data.get('ts') if latest_data else None
        })
    
    return stats


@router.get("/usage/export")
async def export_usage_data(
    format: str = Query('json', regex='^(json|csv)$'),
    days: int = Query(30, ge=1, le=365),
    user=Depends(get_current_user)
):
    """Export usage data in JSON or CSV format"""
    tenant_id = user.get('tenant_id', 'anonymous')
    db = get_firestore()
    
    # Collect data
    today = datetime.now(timezone.utc)
    export_data = []
    
    for i in range(days):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        doc_ref = db.collection('usage_metrics').document(f"{tenant_id}_{date}")
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            export_data.append({
                'date': date,
                'tenant_id': tenant_id,
                'api_calls': data.get('api_calls', 0),
                'total_duration_ms': data.get('total_duration_ms', 0),
                'avg_duration_ms': (
                    data.get('total_duration_ms', 0) / data.get('api_calls', 1)
                    if data.get('api_calls', 0) > 0 else 0
                )
            })
    
    if format == 'csv':
        # Generate CSV
        import io
        output = io.StringIO()
        if export_data:
            headers = ','.join(export_data[0].keys())
            output.write(headers + '\n')
            for row in export_data:
                values = ','.join(str(v) for v in row.values())
                output.write(values + '\n')
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=usage_export_{tenant_id}_{today.strftime("%Y%m%d")}.csv'
            }
        )
    
    return {'data': export_data, 'count': len(export_data), 'format': 'json'}
