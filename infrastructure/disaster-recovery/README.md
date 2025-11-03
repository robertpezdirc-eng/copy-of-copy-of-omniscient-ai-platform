# Disaster Recovery Plan

## Overview

This document outlines the disaster recovery (DR) procedures for the Omni Enterprise Ultra Max platform.

## Recovery Objectives

- **RTO (Recovery Time Objective):** 4 hours
- **RPO (Recovery Point Objective):** 1 hour
- **Data Loss Tolerance:** < 1 hour of transactions

## Backup Strategy

### Database Backups
- **Frequency:** Every hour (automated)
- **Retention:** 30 days
- **Location:** Multi-region Cloud Storage
- **Type:** Full + incremental

### Application Backups
- **Configuration:** Daily
- **Code:** Git repository (continuous)
- **Secrets:** Encrypted in Secret Manager

### File Storage Backups
- **User uploads:** Real-time replication
- **Logs:** 90-day retention

## Backup Commands

### Manual Database Backup
```bash
#!/bin/bash
# backup-database.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="omni-db-backup-${TIMESTAMP}.sql"

# Backup PostgreSQL
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d omni > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Upload to Cloud Storage
gsutil cp ${BACKUP_FILE}.gz gs://omni-backups/database/

# Cleanup local file
rm ${BACKUP_FILE}.gz

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Manual Redis Backup
```bash
#!/bin/bash
# backup-redis.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="omni-redis-backup-${TIMESTAMP}.rdb"

# Save Redis snapshot
redis-cli BGSAVE

# Wait for save to complete
while [ $(redis-cli LASTSAVE) -eq $LASTSAVE ]; do
  sleep 1
done

# Copy RDB file
cp /var/lib/redis/dump.rdb $BACKUP_FILE

# Upload to Cloud Storage
gsutil cp $BACKUP_FILE gs://omni-backups/redis/

# Cleanup
rm $BACKUP_FILE

echo "Redis backup completed: $BACKUP_FILE"
```

## Restore Procedures

### Database Restore
```bash
#!/bin/bash
# restore-database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore-database.sh <backup-file>"
  exit 1
fi

# Download from Cloud Storage
gsutil cp gs://omni-backups/database/$BACKUP_FILE .

# Decompress
gunzip $BACKUP_FILE

# Restore
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d omni < ${BACKUP_FILE%.gz}

echo "Database restored from: $BACKUP_FILE"
```

### Redis Restore
```bash
#!/bin/bash
# restore-redis.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore-redis.sh <backup-file>"
  exit 1
fi

# Stop Redis
systemctl stop redis

# Download from Cloud Storage
gsutil cp gs://omni-backups/redis/$BACKUP_FILE /var/lib/redis/dump.rdb

# Set permissions
chown redis:redis /var/lib/redis/dump.rdb

# Start Redis
systemctl start redis

echo "Redis restored from: $BACKUP_FILE"
```

## Disaster Scenarios

### Scenario 1: Complete Region Failure

**Symptoms:**
- Primary region (us-central1) is completely unavailable
- All services in region are down

**Recovery Steps:**
1. Verify global load balancer has failedover to EU region (5 minutes)
2. Promote EU database replica to primary (15 minutes)
3. Update DNS if needed (propagation: 5-60 minutes)
4. Verify all services operational (15 minutes)
5. Monitor for 1 hour
6. Post-incident review

**Total RTO:** ~2 hours

### Scenario 2: Database Corruption

**Symptoms:**
- Database queries returning errors
- Data inconsistencies detected

**Recovery Steps:**
1. Stop application writes immediately
2. Identify last good backup
3. Restore database from backup (30 minutes)
4. Replay transaction logs if available (30 minutes)
5. Verify data integrity (30 minutes)
6. Resume application (10 minutes)
7. Verify full functionality (30 minutes)

**Total RTO:** ~2.5 hours

### Scenario 3: Security Breach

**Symptoms:**
- Unauthorized access detected
- Data exfiltration suspected

**Recovery Steps:**
1. Isolate affected systems (immediate)
2. Revoke all API keys and tokens (10 minutes)
3. Reset all credentials (20 minutes)
4. Restore from last clean backup (1 hour)
5. Apply security patches (30 minutes)
6. Security audit (2 hours)
7. Resume operations (30 minutes)

**Total RTO:** ~4 hours

### Scenario 4: Data Center Failure

**Symptoms:**
- Connectivity loss to entire data center
- Hardware failure

**Recovery Steps:**
1. Automatic failover to secondary region (5 minutes)
2. Verify application functionality (15 minutes)
3. Check data consistency (30 minutes)
4. Monitor performance (1 hour)
5. Plan migration back when primary recovers

**Total RTO:** ~1 hour

## Testing Schedule

### Backup Verification
- **Daily:** Automated backup tests
- **Weekly:** Sample restore tests
- **Monthly:** Full restore dry run

### DR Drills
- **Quarterly:** Simulated region failure
- **Bi-annually:** Full DR exercise
- **Annually:** Complete disaster simulation

## Monitoring & Alerts

### Backup Monitoring
- Backup completion status
- Backup size tracking
- Failed backup alerts
- Storage capacity alerts

### System Health
- Database replication lag
- Service availability
- Cross-region latency
- Error rate thresholds

## Contact Information

### Emergency Contacts
- **On-Call Engineer:** +1-XXX-XXX-XXXX
- **DevOps Lead:** devops-lead@omniscient.ai
- **CTO:** cto@omniscient.ai

### Escalation Path
1. On-Call Engineer (0-30 min)
2. DevOps Lead (30-60 min)
3. CTO (60+ min)

## Post-Incident Procedures

### Documentation
1. Timeline of events
2. Actions taken
3. Root cause analysis
4. Lessons learned
5. Action items

### Review Meeting
- Within 24 hours of incident resolution
- All stakeholders present
- Document improvements needed

## Continuous Improvement

### Metrics to Track
- Actual RTO vs target
- Actual RPO vs target
- Backup success rate
- Restore success rate
- Mean time to recovery (MTTR)

### Regular Reviews
- Monthly backup strategy review
- Quarterly DR plan update
- Annual comprehensive audit

## Compliance

### Regulatory Requirements
- GDPR: 72-hour breach notification
- HIPAA: Contingency plan required
- SOC 2: Documented DR procedures
- ISO 27001: Business continuity management

### Audit Trail
All DR activities are logged:
- Backup operations
- Restore operations
- Failover events
- Access to backup systems
