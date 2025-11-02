# GDPR Persistence System Documentation

## Pregled / Overview

GDPR persistence layer omogoča trajno shranjevanje privolitev, revizijskih zapisov in aktivnosti procesiranja v skladu z EU GDPR.

**The GDPR persistence layer provides durable storage for consents, audit logs, and processing activities in compliance with EU GDPR.**

## Arhitektura / Architecture

### Repository Pattern

Sistem uporablja repository pattern s tremi implementacijami:

1. **PostgresGDPRRepository** (Primary)
   - Trajna shramba v PostgreSQL
   - Transakcijska integriteta
   - ACID garancije
   - Priporočeno za produkcijo

2. **MongoGDPRRepository** (Fallback)
   - Trajna shramba v MongoDB
   - Dokumentni model
   - Uporablja se če PostgreSQL ni dosegljiv

3. **InMemoryGDPRRepository** (Emergency Fallback)
   - ⚠️ **OPOZORILO**: Podatki se ne ohranijo ob ponovnem zagonu!
   - Uporablja se samo če nobena baza ni dosegljiva
   - Sistem samodejno logira kritično opozorilo

### Komponente / Components

```
backend/
├── models/
│   └── gdpr.py                      # SQLAlchemy modeli
├── services/compliance/
│   ├── gdpr_service.py              # Poslovna logika
│   ├── gdpr_repository.py           # Persistence layer
│   └── gdpr_health.py               # Health monitoring
├── routes/
│   └── gdpr_routes.py               # FastAPI endpoints
├── alembic/
│   ├── versions/
│   │   └── 001_gdpr_initial.py     # Začetna migracija
│   ├── env.py                       # Alembic config
│   └── README.md                    # Migration docs
└── tests/
    └── test_gdpr_persistence.py     # Unit testi
```

## Namestitev / Installation

### 1. Database Setup

**PostgreSQL (priporočeno):**
```bash
# Create database
createdb omni

# Set environment variable
export DATABASE_URL="postgresql://user:pass@localhost:5432/omni"
```

**MongoDB (fallback):**
```bash
# Set environment variable
export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DB="omni"
```

### 2. Run Migrations

```bash
cd backend
alembic upgrade head
```

Ta ukaz ustvari:
- `gdpr_consent_records` tabelo
- `gdpr_audit_events` tabelo
- `gdpr_processing_activities` tabelo

### 3. Verify Installation

```bash
# Check migration status
alembic current

# Test health endpoint
curl http://localhost:8080/api/v1/gdpr/health
```

## API Endpoints

### Health Check

```http
GET /api/v1/gdpr/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "gdpr",
  "repository_type": "PostgresGDPRRepository",
  "metrics": {
    "consent_saves": {
      "successes": 150,
      "failures": 2,
      "total": 152
    },
    "audit_logs": {
      "successes": 300,
      "failures": 0,
      "total": 300
    },
    "health_status": "healthy"
  },
  "recommendations": []
}
```

**Status Values:**
- `healthy` - Vse deluje normalno
- `degraded` - Uporablja fallback repository (MongoDB ali InMemory)
- `unhealthy` - Visoka stopnja napak (>10%)

### Status Endpoint

```http
GET /api/v1/gdpr/status
```

**Response:**
```json
{
  "dpo_email": "dpo@omni-platform.eu",
  "consent_users": 1247,
  "processing_activities": 12,
  "audit_events": 5832,
  "retention_days": 90,
  "repository_type": "PostgresGDPRRepository",
  "status": "operational"
}
```

### Record Consent

```http
POST /api/v1/gdpr/consent
```

**Request:**
```json
{
  "user_id": "user123",
  "consent_type": "marketing",
  "granted": true,
  "purpose": "Email marketing campaigns",
  "metadata": {
    "source": "web_form",
    "campaign": "summer_2025"
  }
}
```

**Response:**
```json
{
  "success": true,
  "record": {
    "consent_id": "abc123def456",
    "user_id": "user123",
    "consent_type": "marketing",
    "granted": true,
    "purpose": "Email marketing campaigns",
    "timestamp": "2025-11-02T10:30:00Z",
    "ip_address": "192.168.1.100",
    "metadata": { ... },
    "withdrawn_at": null
  }
}
```

### Withdraw Consent

```http
POST /api/v1/gdpr/consent/withdraw
```

**Request:**
```json
{
  "user_id": "user123",
  "consent_type": "marketing"
}
```

### Check Consent

```http
GET /api/v1/gdpr/consent/check?user_id=user123&consent_type=marketing
```

**Response:**
```json
{
  "user_id": "user123",
  "consent_type": "marketing",
  "granted": true
}
```

### Right to Access (Art. 15)

```http
POST /api/v1/gdpr/rights/access
```

**Request:**
```json
{
  "user_id": "user123",
  "include_processing_info": true
}
```

**Response:** Exports all user data, consents, and processing activities.

### Right to Erasure (Art. 17)

```http
POST /api/v1/gdpr/rights/erasure
```

**Request:**
```json
{
  "user_id": "user123",
  "reason": "User requested account deletion"
}
```

### Right to Rectification (Art. 16)

```http
POST /api/v1/gdpr/rights/rectification
```

**Request:**
```json
{
  "user_id": "user123",
  "corrections": {
    "email": "newemail@example.com",
    "name": "Corrected Name"
  }
}
```

### Right to Data Portability (Art. 20)

```http
POST /api/v1/gdpr/rights/portability
```

**Request:**
```json
{
  "user_id": "user123",
  "format": "json"
}
```

**Formats:** `json`, `csv`, `xml`

## Testing

### Run Unit Tests

```bash
cd backend
pytest tests/test_gdpr_persistence.py -v
```

**Test Coverage:**
- Consent lifecycle (create, withdraw, re-grant)
- Multiple consent types per user
- Access request data export
- Audit logging
- Repository interface compliance
- Upsert behavior
- Error handling

### Manual Testing

```bash
# Test consent record
curl -X POST http://localhost:8080/api/v1/gdpr/consent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "consent_type": "marketing",
    "granted": true,
    "purpose": "Testing"
  }'

# Check consent
curl "http://localhost:8080/api/v1/gdpr/consent/check?user_id=test_user&consent_type=marketing"

# Withdraw consent
curl -X POST http://localhost:8080/api/v1/gdpr/consent/withdraw \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "consent_type": "marketing"
  }'
```

## Monitoring

### Health Monitoring

Sistem kontinuirano spremlja zdravje persistence layer:

- **Automatic fallback detection** - Zazna ko sistem uporablja fallback repository
- **Failure rate tracking** - Spremlja uspešnost shranjenih operacij
- **Critical alerts** - Logira kritična opozorila ko podatki niso trajno shranjeni

### Prometheus Metrics

Exporta metriko na `/metrics`:

```prometheus
# Consent saves
gdpr_consent_saves_total{status="success"} 150
gdpr_consent_saves_total{status="failure"} 2

# Audit logs
gdpr_audit_logs_total{status="success"} 300
gdpr_audit_logs_total{status="failure"} 0

# Repository type (2=Postgres, 1=Mongo, 0=InMemory)
gdpr_repository_type 2

# Health status (2=Healthy, 1=Degraded, 0=Unhealthy)
gdpr_health_status 2

# Fallback events
gdpr_repository_fallback_total 0
```

### Log Monitoring

**Critical Alerts:**
```
⚠️  GDPR DATA LOSS RISK: Using in-memory storage.
User consents and audit logs will NOT persist across restarts.
Check database configuration immediately!
```

**Warnings:**
```
GDPRRepository Postgres unavailable: connection refused
GDPRRepository: falling back to MongoDB
```

### Alerting Rules

**Grafana/Prometheus Alert:**
```yaml
- alert: GDPRPersistenceDegraded
  expr: gdpr_health_status < 2
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "GDPR persistence degraded - data loss risk"
    description: "Repository type: {{ $labels.repository_type }}"
```

## Database Schema

### gdpr_consent_records

| Column        | Type           | Description                        |
|---------------|----------------|------------------------------------|
| id            | VARCHAR(36)    | Primary key (UUID)                 |
| user_id       | VARCHAR(255)   | User identifier (indexed)          |
| consent_type  | VARCHAR(64)    | Type of consent (indexed)          |
| granted       | BOOLEAN        | Consent granted or denied          |
| purpose       | VARCHAR(512)   | Purpose of processing              |
| ip_address    | VARCHAR(64)    | IP address when consent recorded   |
| metadata      | JSON           | Additional metadata                |
| timestamp     | DATETIME       | When consent was recorded          |
| withdrawn_at  | DATETIME       | When consent was withdrawn (null)  |

**Indexes:**
- PRIMARY KEY (id)
- INDEX (user_id)
- INDEX (consent_type)
- UNIQUE (user_id, consent_type)
- INDEX (user_id, consent_type) - composite

### gdpr_audit_events

| Column     | Type          | Description                    |
|------------|---------------|--------------------------------|
| id         | INTEGER       | Primary key (auto-increment)   |
| timestamp  | DATETIME      | Event timestamp (indexed)      |
| action     | VARCHAR(128)  | Action performed (indexed)     |
| user_id    | VARCHAR(255)  | User affected (indexed)        |
| details    | JSON          | Event details                  |

### gdpr_processing_activities

| Column              | Type          | Description                      |
|---------------------|---------------|----------------------------------|
| id                  | VARCHAR(36)   | Primary key (UUID)               |
| name                | VARCHAR(255)  | Activity name                    |
| purpose             | VARCHAR(512)  | Purpose of processing            |
| legal_basis         | VARCHAR(64)   | Legal basis (consent, contract)  |
| data_categories     | JSON          | Categories of data processed     |
| recipients          | JSON          | Data recipients                  |
| retention_period    | VARCHAR(128)  | How long data is kept            |
| security_measures   | JSON          | Security measures applied        |
| created_at          | DATETIME      | When activity recorded (indexed) |

## Migrations

### Create New Migration

```bash
# Auto-generate from model changes
cd backend
alembic revision --autogenerate -m "add new gdpr fields"

# Review generated migration
# Edit if needed: alembic/versions/XXXXXX_add_new_gdpr_fields.py

# Apply migration
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

### View Migration Status

```bash
# Current version
alembic current

# Migration history
alembic history

# Show SQL without executing
alembic upgrade head --sql
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Database backup completed
- [ ] Migrations tested in staging
- [ ] Health endpoints verified
- [ ] Monitoring alerts configured
- [ ] DATABASE_URL configured
- [ ] GDPR_DPO_EMAIL configured
- [ ] Rollback plan documented

### Deployment Steps

1. **Backup database:**
   ```bash
   pg_dump -h $DB_HOST -U $DB_USER -d omni > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Verify health:**
   ```bash
   curl https://api.example.com/api/v1/gdpr/health
   ```

4. **Monitor logs:**
   ```bash
   # Check for critical alerts
   tail -f /var/log/backend.log | grep "GDPR\|CRITICAL"
   ```

### Rollback Procedure

```bash
# 1. Stop application
systemctl stop backend

# 2. Rollback migration
cd backend
alembic downgrade -1

# 3. Restore database if needed
psql -h $DB_HOST -U $DB_USER -d omni < backup_20251102_103000.sql

# 4. Restart with previous version
git checkout <previous_version>
systemctl start backend
```

## Configuration

### Environment Variables

```bash
# Database (required)
DATABASE_URL="postgresql://user:pass@localhost:5432/omni"

# MongoDB (optional fallback)
MONGODB_URL="mongodb://localhost:27017"
MONGODB_DB="omni"

# GDPR Configuration
GDPR_DPO_EMAIL="dpo@omni-platform.eu"
GDPR_RETENTION_DAYS="90"

# Monitoring
SENTRY_DSN="https://..."
```

### Configuration File

Create `backend/.env`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/omni
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=omni
GDPR_DPO_EMAIL=dpo@omni-platform.eu
GDPR_RETENTION_DAYS=90
```

## Troubleshooting

### "Using in-memory storage" Warning

**Problem:** GDPR data will not persist across restarts.

**Solution:**
1. Check DATABASE_URL is set correctly
2. Verify PostgreSQL is running: `pg_isready -h localhost`
3. Test connection: `psql $DATABASE_URL`
4. Check MongoDB if Postgres is unavailable
5. Review logs for connection errors

### High Failure Rate

**Problem:** Health status shows "unhealthy".

**Solution:**
1. Check database connectivity
2. Review error logs: `grep "Consent save failed" /var/log/backend.log`
3. Verify database disk space
4. Check connection pool settings
5. Monitor query performance

### Migration Conflicts

**Problem:** "Can't locate revision" or "Multiple heads"

**Solution:**
```bash
# Check current state
alembic current
alembic history

# Merge multiple heads
alembic merge heads -m "merge conflict resolution"

# Stamp database to specific version (careful!)
alembic stamp head
```

### Repository Fallback Loop

**Problem:** System constantly falls back between repositories.

**Solution:**
1. Fix primary database connectivity first
2. Restart application after database recovery
3. Monitor health endpoint for stability
4. Review connection pool exhaustion

## Compliance Notes

### GDPR Articles Implemented

- **Art. 6-7**: Consent management (record, withdraw, check)
- **Art. 15**: Right to access (data export)
- **Art. 16**: Right to rectification (data correction)
- **Art. 17**: Right to erasure (right to be forgotten)
- **Art. 20**: Right to data portability (JSON/CSV/XML export)
- **Art. 30**: Processing activities records
- **Art. 33-34**: Data breach recording (foundation)

### Audit Trail

Vse operacije so logirane v `gdpr_audit_events`:
- Consent recorded
- Consent withdrawn
- Access request
- Erasure request
- Rectification request
- Portability request

### Data Protection Officer (DPO)

DPO contact je vključen v vse odgovore:
```json
{
  "dpo_contact": "dpo@omni-platform.eu"
}
```

### Retention Policy

Default retention period: **90 dni** (configurable via `GDPR_RETENTION_DAYS`)

## Support

Za pomoč ali vprašanja:
- GitHub Issues: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform
- Email: dpo@omni-platform.eu
- Dokumentacija: `/backend/alembic/README.md`
