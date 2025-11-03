# Alembic Database Migrations

This directory contains database migration scripts managed by Alembic.

## Quick Start

### 1. Initialize database (first time only)
```bash
cd backend
alembic upgrade head
```

### 2. Create a new migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Or create empty migration
alembic revision -m "description of changes"
```

### 3. Apply migrations
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>
```

### 4. View migration history
```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Configuration

Database URL is configured in `alembic.ini` and can be overridden by setting the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/omni"
alembic upgrade head
```

## Migration Files

- `env.py` - Alembic environment configuration
- `script.py.mako` - Template for new migration files
- `versions/` - Migration scripts directory
  - `001_gdpr_initial.py` - Initial GDPR tables (consent, audit, processing activities)

## Best Practices

1. **Always review auto-generated migrations** before applying
   - Alembic may not detect all changes correctly
   - Verify indexes, constraints, and defaults

2. **Test migrations in development first**
   ```bash
   # Test upgrade
   alembic upgrade head
   
   # Test downgrade
   alembic downgrade -1
   
   # Test re-upgrade
   alembic upgrade head
   ```

3. **Keep migrations reversible**
   - Always implement both `upgrade()` and `downgrade()`
   - Test downgrade paths

4. **Use transactions**
   - Alembic wraps migrations in transactions by default
   - For PostgreSQL, most DDL is transactional

5. **Handle data migrations carefully**
   - Separate schema changes from data changes
   - Use batch operations for large datasets
   - Consider downtime requirements

## Common Commands

```bash
# Create new revision
alembic revision -m "add user_preferences table"

# Auto-generate from model changes
alembic revision --autogenerate -m "add new columns to users"

# Apply all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Show current database version
alembic current

# Show all revisions
alembic history

# Show SQL without executing
alembic upgrade head --sql

# Stamp database without running migrations (dangerous!)
alembic stamp head
```

## Troubleshooting

### "Can't locate revision identified by 'xxxxx'"
- Ensure all migration files are present in `versions/`
- Check that `alembic_version` table exists in database

### "Target database is not up to date"
```bash
# Check current version
alembic current

# Check what migrations need to run
alembic history

# Apply missing migrations
alembic upgrade head
```

### "Multiple head revisions are present"
- Resolve with merge migration:
```bash
alembic merge heads -m "merge multiple heads"
```

### Database schema out of sync
```bash
# Generate migration to match current state
alembic revision --autogenerate -m "sync schema"

# Review and edit the generated migration
# Then apply
alembic upgrade head
```

## Production Deployment

1. **Backup database before migrating**
   ```bash
   pg_dump -h localhost -U user -d omni > backup_$(date +%Y%m%d).sql
   ```

2. **Run migrations during deployment**
   ```bash
   # In CI/CD pipeline or deployment script
   cd backend
   alembic upgrade head
   ```

3. **Monitor migration logs**
   - Check for errors
   - Verify indexes were created
   - Confirm constraints are in place

4. **Rollback plan**
   ```bash
   # If migration fails, rollback
   alembic downgrade -1
   
   # Restore from backup if needed
   psql -h localhost -U user -d omni < backup_20251102.sql
   ```

## CI/CD Integration

### GitHub Actions example
```yaml
- name: Run database migrations
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    cd backend
    alembic upgrade head
```

### Docker Compose
```yaml
services:
  backend:
    command: >
      sh -c "alembic upgrade head && 
             uvicorn main:app --host 0.0.0.0 --port 8080"
```

## Documentation

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
