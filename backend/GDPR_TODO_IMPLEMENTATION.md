# GDPR Service - Implementation TODO Documentation

This document tracks the TODO items in the GDPR compliance service and provides guidance for implementation.

## Overview

The GDPR service (`services/compliance/gdpr_service.py`) provides comprehensive GDPR compliance functionality. Several features are marked as TODO and require database integration for production use.

## TODO Items

### 1. Automatic Breach Notification Workflow (Line 448)

**Context:**
```python
# TODO: Trigger automatic notification workflow
```

**Description:**
When a high or critical data breach is reported, automatic notifications must be sent to:
- Data Protection Authority (within 72 hours per Art. 33)
- Affected data subjects (without undue delay per Art. 34)
- Data Protection Officer (DPO)

**Implementation Requirements:**

1. **Email Service Integration:**
   ```python
   from services.email_service import EmailService
   
   async def _notify_breach(self, breach: Dict[str, Any]):
       email_service = EmailService()
       
       # Notify DPA (Data Protection Authority)
       await email_service.send_breach_notification_to_dpa(
           breach_id=breach["breach_id"],
           severity=breach["severity"],
           affected_count=breach["affected_users_count"],
           description=breach["description"],
           mitigation_steps=breach["mitigation_steps"]
       )
       
       # Notify affected users
       for user_id in breach["affected_users"]:
           await email_service.send_breach_notification_to_user(
               user_id=user_id,
               breach_id=breach["breach_id"],
               description=breach["description_for_users"],
               recommended_actions=breach["user_actions"]
           )
       
       # Notify DPO
       await email_service.send_breach_notification_to_dpo(
           dpo_email=self.dpo_email,
           breach=breach
       )
   ```

2. **Scheduled Task for Deadline Monitoring:**
   ```python
   # Check breach notification deadlines
   # Run every hour via Celery/background task
   async def check_breach_notification_deadlines(self):
       breaches = self.repo.get_unnotified_breaches()
       for breach in breaches:
           time_since_discovery = datetime.utcnow() - breach["discovery_date"]
           if time_since_discovery > timedelta(hours=68):  # 4 hours before deadline
               logger.critical(f"URGENT: Breach {breach['breach_id']} notification deadline approaching!")
   ```

3. **Database Schema:**
   ```sql
   CREATE TABLE gdpr_breach_notifications (
       notification_id UUID PRIMARY KEY,
       breach_id VARCHAR(50) REFERENCES gdpr_data_breaches(breach_id),
       recipient_type VARCHAR(50), -- 'dpa', 'user', 'dpo'
       recipient_id VARCHAR(255),
       sent_at TIMESTAMP,
       notification_method VARCHAR(50), -- 'email', 'sms', 'letter'
       status VARCHAR(50) -- 'sent', 'failed', 'acknowledged'
   );
   ```

### 2. Query All Databases and Services (Line 475)

**Context:**
```python
async def _collect_user_data(self, user_id: str) -> Dict[str, Any]:
    # TODO: Query all databases and services
```

**Description:**
For Right to Access requests (Art. 15), collect all user data from:
- PostgreSQL (user profiles, transactions)
- MongoDB (logs, analytics)
- Redis (session data)
- Firestore (real-time data)
- External services (CRM, email service, etc.)

**Implementation Requirements:**

```python
async def _collect_user_data(self, user_id: str) -> Dict[str, Any]:
    """Collect all user data from system"""
    from database import get_db, get_mongodb, get_redis, get_firestore
    from models.user import User
    from models.analytics import UserAnalytics
    
    data = {
        "user_id": user_id,
        "collection_date": datetime.utcnow().isoformat(),
        "sources": {}
    }
    
    # 1. PostgreSQL - User profile and transactions
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            data["sources"]["postgresql"] = {
                "profile": {
                    "email": user.email,
                    "name": user.name,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "preferences": user.preferences or {},
                "subscription": user.subscription_data or {}
            }
    except Exception as e:
        logger.error(f"Failed to collect PostgreSQL data: {e}")
        data["sources"]["postgresql"] = {"error": str(e)}
    
    # 2. MongoDB - Analytics and logs
    try:
        mongo_db = await get_mongodb()
        if mongo_db:
            # User activity logs
            logs = await mongo_db.activity_logs.find(
                {"user_id": user_id}
            ).limit(1000).to_list(1000)
            
            # Analytics events
            analytics = await mongo_db.analytics.find(
                {"user_id": user_id}
            ).limit(1000).to_list(1000)
            
            data["sources"]["mongodb"] = {
                "activity_logs": logs,
                "analytics_events": analytics
            }
    except Exception as e:
        logger.error(f"Failed to collect MongoDB data: {e}")
        data["sources"]["mongodb"] = {"error": str(e)}
    
    # 3. Redis - Session data
    try:
        redis = await get_redis()
        if redis:
            session_keys = await redis.keys(f"session:{user_id}:*")
            sessions = {}
            for key in session_keys:
                sessions[key] = await redis.get(key)
            data["sources"]["redis"] = {
                "sessions": sessions
            }
    except Exception as e:
        logger.error(f"Failed to collect Redis data: {e}")
        data["sources"]["redis"] = {"error": str(e)}
    
    # 4. Firestore - Real-time data
    try:
        firestore_db = get_firestore()
        if firestore_db:
            user_doc = firestore_db.collection('users').document(user_id).get()
            if user_doc.exists:
                data["sources"]["firestore"] = user_doc.to_dict()
    except Exception as e:
        logger.error(f"Failed to collect Firestore data: {e}")
        data["sources"]["firestore"] = {"error": str(e)}
    
    # 5. External services
    data["sources"]["external_services"] = {}
    
    # Email service
    try:
        from services.email_service import EmailService
        email_service = EmailService()
        email_history = await email_service.get_user_email_history(user_id)
        data["sources"]["external_services"]["email_history"] = email_history
    except Exception as e:
        logger.warning(f"Failed to collect email history: {e}")
    
    # CRM integration (Salesforce, HubSpot)
    try:
        from services.hubspot_service import HubSpotService
        hubspot = HubSpotService()
        crm_data = await hubspot.get_contact_data(user_id)
        data["sources"]["external_services"]["crm"] = crm_data
    except Exception as e:
        logger.warning(f"Failed to collect CRM data: {e}")
    
    return data
```

### 3. Delete from All Databases (Line 485)

**Context:**
```python
async def _delete_user_data(self, user_id: str) -> Dict[str, int]:
    # TODO: Delete from all databases
```

**Description:**
For Right to Erasure requests (Art. 17), delete user data from all systems.

**Implementation Requirements:**

```python
async def _delete_user_data(self, user_id: str) -> Dict[str, int]:
    """Delete user data from all systems"""
    from database import get_db, get_mongodb, get_redis, get_firestore
    from models.user import User
    from sqlalchemy import delete
    
    deletion_count = {
        "postgresql_records": 0,
        "mongodb_documents": 0,
        "redis_keys": 0,
        "firestore_documents": 0
    }
    
    # 1. PostgreSQL - Cascade deletes
    try:
        db = next(get_db())
        # Delete user and cascade to related records
        result = db.query(User).filter(User.id == user_id).delete()
        db.commit()
        deletion_count["postgresql_records"] = result
        logger.info(f"Deleted {result} PostgreSQL records for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to delete PostgreSQL data: {e}")
        db.rollback()
    
    # 2. MongoDB - Delete all collections
    try:
        mongo_db = await get_mongodb()
        if mongo_db:
            # Activity logs
            result1 = await mongo_db.activity_logs.delete_many({"user_id": user_id})
            # Analytics
            result2 = await mongo_db.analytics.delete_many({"user_id": user_id})
            # User documents
            result3 = await mongo_db.users.delete_one({"_id": user_id})
            
            deletion_count["mongodb_documents"] = (
                result1.deleted_count + result2.deleted_count + result3.deleted_count
            )
            logger.info(f"Deleted {deletion_count['mongodb_documents']} MongoDB documents")
    except Exception as e:
        logger.error(f"Failed to delete MongoDB data: {e}")
    
    # 3. Redis - Delete all user keys
    try:
        redis = await get_redis()
        if redis:
            user_keys = await redis.keys(f"*{user_id}*")
            if user_keys:
                deletion_count["redis_keys"] = await redis.delete(*user_keys)
                logger.info(f"Deleted {deletion_count['redis_keys']} Redis keys")
    except Exception as e:
        logger.error(f"Failed to delete Redis data: {e}")
    
    # 4. Firestore - Delete user document
    try:
        firestore_db = get_firestore()
        if firestore_db:
            firestore_db.collection('users').document(user_id).delete()
            deletion_count["firestore_documents"] = 1
            logger.info(f"Deleted Firestore document for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to delete Firestore data: {e}")
    
    # 5. External services cleanup
    try:
        # Remove from email service
        from services.email_service import EmailService
        email_service = EmailService()
        await email_service.remove_contact(user_id)
        
        # Remove from CRM
        from services.hubspot_service import HubSpotService
        hubspot = HubSpotService()
        await hubspot.delete_contact(user_id)
    except Exception as e:
        logger.warning(f"Failed to cleanup external services: {e}")
    
    return deletion_count
```

### 4. Anonymize Instead of Delete (Line 494)

**Context:**
```python
async def _anonymize_user_data(self, user_id: str) -> Dict[str, int]:
    # TODO: Anonymize instead of delete
```

**Description:**
For data that must be retained for legal/regulatory reasons, anonymize instead of deleting.

**Implementation Requirements:**

```python
async def _anonymize_user_data(self, user_id: str) -> Dict[str, int]:
    """Anonymize user data (for legal retention)"""
    from database import get_db, get_mongodb
    from models.user import User
    import hashlib
    
    anonymization_count = {
        "postgresql_records": 0,
        "mongodb_documents": 0
    }
    
    # Generate anonymous identifier
    anon_id = hashlib.sha256(f"anon_{user_id}_{datetime.utcnow()}".encode()).hexdigest()[:16]
    
    # 1. PostgreSQL - Anonymize PII
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Replace PII with anonymized values
            user.email = f"anonymized_{anon_id}@deleted.local"
            user.name = f"Deleted User {anon_id}"
            user.phone = None
            user.address = None
            user.ip_address = "0.0.0.0"
            # Keep aggregated data for statistics
            user.anonymized_at = datetime.utcnow()
            db.commit()
            anonymization_count["postgresql_records"] = 1
    except Exception as e:
        logger.error(f"Failed to anonymize PostgreSQL data: {e}")
        db.rollback()
    
    # 2. MongoDB - Anonymize logs
    try:
        mongo_db = await get_mongodb()
        if mongo_db:
            # Anonymize activity logs (keep aggregate data)
            result = await mongo_db.activity_logs.update_many(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": anon_id,
                        "email": f"anonymized_{anon_id}@deleted.local",
                        "ip_address": "0.0.0.0",
                        "anonymized": True,
                        "anonymized_at": datetime.utcnow()
                    },
                    "$unset": {
                        "name": "",
                        "phone": "",
                        "address": ""
                    }
                }
            )
            anonymization_count["mongodb_documents"] = result.modified_count
    except Exception as e:
        logger.error(f"Failed to anonymize MongoDB data: {e}")
    
    logger.info(f"Anonymized user {user_id} to {anon_id}")
    return anonymization_count
```

### 5. Update All Databases (Line 505)

**Context:**
```python
async def _update_user_data(self, user_id: str, corrections: Dict[str, Any]) -> List[str]:
    # TODO: Update all databases
```

**Description:**
For Right to Rectification requests (Art. 16), update user data across all systems.

**Implementation Requirements:**

```python
async def _update_user_data(
    self,
    user_id: str,
    corrections: Dict[str, Any]
) -> List[str]:
    """Update user data across systems"""
    from database import get_db, get_mongodb, get_firestore
    from models.user import User
    
    updated_fields = []
    
    # 1. PostgreSQL - Update user profile
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for field, value in corrections.items():
                if hasattr(user, field):
                    setattr(user, field, value)
                    updated_fields.append(f"postgresql.{field}")
            user.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Updated {len(updated_fields)} PostgreSQL fields")
    except Exception as e:
        logger.error(f"Failed to update PostgreSQL data: {e}")
        db.rollback()
    
    # 2. MongoDB - Update user documents
    try:
        mongo_db = await get_mongodb()
        if mongo_db:
            result = await mongo_db.users.update_one(
                {"_id": user_id},
                {"$set": corrections}
            )
            if result.modified_count > 0:
                for field in corrections.keys():
                    updated_fields.append(f"mongodb.{field}")
    except Exception as e:
        logger.error(f"Failed to update MongoDB data: {e}")
    
    # 3. Firestore - Update real-time data
    try:
        firestore_db = get_firestore()
        if firestore_db:
            firestore_db.collection('users').document(user_id).update(corrections)
            for field in corrections.keys():
                updated_fields.append(f"firestore.{field}")
    except Exception as e:
        logger.error(f"Failed to update Firestore data: {e}")
    
    # 4. Sync to external services
    try:
        from services.hubspot_service import HubSpotService
        hubspot = HubSpotService()
        await hubspot.update_contact(user_id, corrections)
    except Exception as e:
        logger.warning(f"Failed to sync to CRM: {e}")
    
    return updated_fields
```

### 6. Filter Processing Activities by User (Line 521)

**Context:**
```python
def _get_user_processing_activities(self, user_id: str) -> List[Dict[str, Any]]:
    # TODO: Filter processing activities by user
```

**Implementation Requirements:**

```python
def _get_user_processing_activities(self, user_id: str) -> List[Dict[str, Any]]:
    """Get processing activities affecting user"""
    
    # Query repository for user-specific activities
    activities = self.repo.get_processing_activities_for_user(user_id)
    
    # If not user-specific, return all activities with user data categories
    if not activities:
        # Filter global activities that affect this user
        all_activities = self.processing_activities
        relevant_activities = []
        
        for activity in all_activities:
            # Check if activity involves user data
            data_categories = activity.get("data_categories", [])
            if any(cat in ["profile_data", "usage_data", "analytics_data"] for cat in data_categories):
                relevant_activities.append(activity)
        
        return relevant_activities
    
    return activities
```

### 7. CSV Conversion (Line 526)

**Context:**
```python
def _convert_to_csv(self, data: Dict[str, Any]) -> str:
    # TODO: Implement CSV conversion
```

**Implementation Requirements:**

```python
def _convert_to_csv(self, data: Dict[str, Any]) -> str:
    """Convert data to CSV format"""
    import csv
    import io
    
    output = io.StringIO()
    
    # Flatten nested dictionary
    def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to comma-separated strings
                items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    flat_data = flatten_dict(data)
    
    # Write CSV
    writer = csv.writer(output)
    writer.writerow(['Field', 'Value'])  # Header
    for key, value in flat_data.items():
        writer.writerow([key, value])
    
    return output.getvalue()
```

### 8. XML Conversion (Line 531)

**Context:**
```python
def _convert_to_xml(self, data: Dict[str, Any]) -> str:
    # TODO: Implement XML conversion
```

**Implementation Requirements:**

```python
def _convert_to_xml(self, data: Dict[str, Any]) -> str:
    """Convert data to XML format"""
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom
    
    def dict_to_xml(parent: Element, data: Dict[str, Any]) -> None:
        """Recursively convert dict to XML"""
        for key, value in data.items():
            # Sanitize key for XML
            key = key.replace(' ', '_').replace('.', '_')
            
            if isinstance(value, dict):
                child = SubElement(parent, key)
                dict_to_xml(child, value)
            elif isinstance(value, list):
                for item in value:
                    child = SubElement(parent, key)
                    if isinstance(item, dict):
                        dict_to_xml(child, item)
                    else:
                        child.text = str(item)
            else:
                child = SubElement(parent, key)
                child.text = str(value) if value is not None else ''
    
    # Create root element
    root = Element('gdpr_data_export')
    root.set('user_id', data.get('user_id', 'unknown'))
    root.set('export_date', datetime.utcnow().isoformat())
    
    # Convert data to XML
    dict_to_xml(root, data)
    
    # Pretty print
    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
    return xml_str
```

## Priority and Timeline

### High Priority (Implement before production deployment)
1. **Delete from All Databases** - Required for GDPR compliance
2. **Query All Databases and Services** - Required for access requests
3. **Update All Databases** - Required for rectification requests

### Medium Priority (Implement within 1 month of production)
4. **Anonymize Instead of Delete** - Important for legal data retention
5. **Automatic Breach Notification Workflow** - Critical for breach response

### Low Priority (Can be deferred)
6. **Filter Processing Activities by User** - Enhancement for transparency
7. **CSV Conversion** - Convenience feature
8. **XML Conversion** - Convenience feature

## Testing Requirements

For each TODO implementation, ensure:

1. **Unit Tests**: Test each function independently
2. **Integration Tests**: Test database interactions
3. **Edge Cases**: Test error handling, empty data, large datasets
4. **Performance**: Test with realistic data volumes
5. **GDPR Compliance**: Verify all requirements are met

## Documentation Updates

After implementing each TODO:

1. Update this document with "✅ Implemented"
2. Add implementation details to ARCHITECTURE.md
3. Update API documentation in route handlers
4. Add examples to README.md

## Related Files

- `services/compliance/gdpr_service.py` - Main GDPR service
- `services/compliance/gdpr_repository.py` - Data persistence
- `routes/gdpr_routes.py` - API endpoints
- `models/gdpr.py` - Database models
- `tests/test_gdpr_persistence.py` - Test suite
