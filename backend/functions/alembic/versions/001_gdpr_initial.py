"""Initial GDPR tables

Revision ID: 001_gdpr_initial
Revises: 
Create Date: 2025-11-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_gdpr_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create GDPR compliance tables"""
    
    # Create gdpr_consent_records table
    op.create_table(
        'gdpr_consent_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('consent_type', sa.String(64), nullable=False, index=True),
        sa.Column('granted', sa.Boolean(), nullable=False, default=True),
        sa.Column('purpose', sa.String(512), nullable=True),
        sa.Column('ip_address', sa.String(64), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('withdrawn_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'consent_type', name='uq_user_consent_type'),
    )
    
    # Create composite index for user_id + consent_type queries
    op.create_index(
        'ix_consent_user_type',
        'gdpr_consent_records',
        ['user_id', 'consent_type']
    )
    
    # Create gdpr_audit_events table
    op.create_table(
        'gdpr_audit_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
        sa.Column('action', sa.String(128), nullable=False, index=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    
    # Create gdpr_processing_activities table
    op.create_table(
        'gdpr_processing_activities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('purpose', sa.String(512), nullable=False),
        sa.Column('legal_basis', sa.String(64), nullable=False),
        sa.Column('data_categories', postgresql.JSON(astext_type=sa.Text()), nullable=False, default=list),
        sa.Column('recipients', postgresql.JSON(astext_type=sa.Text()), nullable=False, default=list),
        sa.Column('retention_period', sa.String(128), nullable=False),
        sa.Column('security_measures', postgresql.JSON(astext_type=sa.Text()), nullable=False, default=list),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
    )


def downgrade() -> None:
    """Drop GDPR compliance tables"""
    op.drop_table('gdpr_processing_activities')
    op.drop_table('gdpr_audit_events')
    op.drop_index('ix_consent_user_type', table_name='gdpr_consent_records')
    op.drop_table('gdpr_consent_records')
