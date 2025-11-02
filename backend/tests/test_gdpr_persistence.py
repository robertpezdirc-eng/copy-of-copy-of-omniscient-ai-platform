"""
Unit tests for GDPR persistence layer
Tests consent lifecycle: upsert, withdraw, re-grant, access export
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from services.compliance.gdpr_repository import (
    GDPRRepository,
    InMemoryGDPRRepository,
    get_best_available_repository,
)
from services.compliance.gdpr_service import (
    GDPRService,
    ConsentType,
)


@pytest.fixture
def in_memory_repo():
    """Provide clean in-memory repository for each test"""
    return InMemoryGDPRRepository()


@pytest.fixture
def gdpr_service_with_in_memory():
    """GDPR service with in-memory repository for testing"""
    repo = InMemoryGDPRRepository()
    service = GDPRService(
        dpo_email="test-dpo@example.com",
        retention_period_days=90,
        repository=repo
    )
    return service


class TestConsentLifecycle:
    """Test consent record, withdraw, re-grant lifecycle"""

    def test_record_consent_creates_new_record(self, gdpr_service_with_in_memory):
        """Test creating a new consent record"""
        service = gdpr_service_with_in_memory
        
        record = service.record_consent(
            user_id="user123",
            consent_type=ConsentType.MARKETING,
            granted=True,
            purpose="Email marketing campaigns",
            ip_address="192.168.1.100",
            metadata={"source": "web_form"}
        )
        
        assert record["user_id"] == "user123"
        assert record["consent_type"] == ConsentType.MARKETING
        assert record["granted"] is True
        assert record["purpose"] == "Email marketing campaigns"
        assert record["ip_address"] == "192.168.1.100"
        assert record["metadata"]["source"] == "web_form"
        assert record["withdrawn_at"] is None
        assert "consent_id" in record
        assert "timestamp" in record

    def test_upsert_consent_updates_existing(self, gdpr_service_with_in_memory):
        """Test that recording consent twice updates the same record"""
        service = gdpr_service_with_in_memory
        
        # First consent
        record1 = service.record_consent(
            user_id="user456",
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            purpose="User analytics",
        )
        
        # Second consent (upsert)
        record2 = service.record_consent(
            user_id="user456",
            consent_type=ConsentType.ANALYTICS,
            granted=False,
            purpose="User analytics - updated",
        )
        
        # Should update, not create new
        assert record2["user_id"] == "user456"
        assert record2["consent_type"] == ConsentType.ANALYTICS
        assert record2["granted"] is False
        assert record2["purpose"] == "User analytics - updated"
        
        # Check only one record exists
        consents = service.repo.list_consents_for_user("user456")
        assert len(consents) == 1

    def test_withdraw_consent(self, gdpr_service_with_in_memory):
        """Test withdrawing consent"""
        service = gdpr_service_with_in_memory
        
        # Record consent first
        service.record_consent(
            user_id="user789",
            consent_type=ConsentType.PROFILING,
            granted=True,
            purpose="User profiling",
        )
        
        # Withdraw consent
        withdrawn = service.withdraw_consent(
            user_id="user789",
            consent_type=ConsentType.PROFILING
        )
        
        assert withdrawn["granted"] is False
        assert withdrawn["withdrawn_at"] is not None
        
        # Check consent is no longer active
        is_granted = service.check_consent("user789", ConsentType.PROFILING)
        assert is_granted is False

    def test_withdraw_nonexistent_consent_raises_error(self, gdpr_service_with_in_memory):
        """Test that withdrawing non-existent consent raises error"""
        service = gdpr_service_with_in_memory
        
        with pytest.raises(ValueError, match="No marketing consent for user"):
            service.withdraw_consent(
                user_id="nonexistent_user",
                consent_type=ConsentType.MARKETING
            )

    def test_re_grant_after_withdrawal(self, gdpr_service_with_in_memory):
        """Test that user can re-grant consent after withdrawal"""
        service = gdpr_service_with_in_memory
        
        # Initial consent
        service.record_consent(
            user_id="user999",
            consent_type=ConsentType.MARKETING,
            granted=True,
            purpose="Marketing",
        )
        
        # Withdraw
        service.withdraw_consent("user999", ConsentType.MARKETING)
        assert service.check_consent("user999", ConsentType.MARKETING) is False
        
        # Re-grant (new consent record)
        service.record_consent(
            user_id="user999",
            consent_type=ConsentType.MARKETING,
            granted=True,
            purpose="Marketing - re-granted",
        )
        
        # Should be active again
        assert service.check_consent("user999", ConsentType.MARKETING) is True

    def test_check_consent_returns_false_for_nonexistent(self, gdpr_service_with_in_memory):
        """Test that checking non-existent consent returns False"""
        service = gdpr_service_with_in_memory
        
        granted = service.check_consent("nonexistent", ConsentType.ANALYTICS)
        assert granted is False


class TestAccessExport:
    """Test right to access (data export)"""

    async def test_access_request_includes_consents(self, gdpr_service_with_in_memory):
        """Test that access request exports user consents"""
        service = gdpr_service_with_in_memory
        
        # Create multiple consents
        service.record_consent(
            user_id="export_user",
            consent_type=ConsentType.MARKETING,
            granted=True,
            purpose="Marketing emails",
        )
        service.record_consent(
            user_id="export_user",
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            purpose="Usage analytics",
        )
        
        # Exercise right to access
        response = await service.exercise_right_to_access(
            user_id="export_user",
            include_processing_info=True
        )
        
        assert response["user_id"] == "export_user"
        assert "consents" in response
        assert len(response["consents"]) == 2
        assert ConsentType.MARKETING in response["consents"]
        assert ConsentType.ANALYTICS in response["consents"]
        assert "dpo_contact" in response
        assert "your_rights" in response

    async def test_access_request_for_user_without_consents(self, gdpr_service_with_in_memory):
        """Test access request for user with no consent records"""
        service = gdpr_service_with_in_memory
        
        response = await service.exercise_right_to_access(
            user_id="new_user",
            include_processing_info=False
        )
        
        assert response["user_id"] == "new_user"
        assert response["consents"] == {}


class TestAuditLogging:
    """Test audit event logging"""

    def test_consent_record_creates_audit_event(self, gdpr_service_with_in_memory):
        """Test that recording consent creates an audit event"""
        service = gdpr_service_with_in_memory
        
        initial_audit_count = len(service.audit_log)
        
        service.record_consent(
            user_id="audit_user",
            consent_type=ConsentType.MARKETING,
            granted=True,
            purpose="Testing",
        )
        
        # Should have created audit event
        assert len(service.audit_log) == initial_audit_count + 1
        
        # Check audit event details
        latest_audit = service.audit_log[-1]
        assert latest_audit["action"] == "consent_recorded"
        assert latest_audit["user_id"] == "audit_user"
        assert latest_audit["details"]["consent_type"] == str(ConsentType.MARKETING)
        assert latest_audit["details"]["granted"] is True

    def test_consent_withdrawal_creates_audit_event(self, gdpr_service_with_in_memory):
        """Test that withdrawing consent creates an audit event"""
        service = gdpr_service_with_in_memory
        
        # Record first
        service.record_consent(
            user_id="audit_user2",
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            purpose="Testing",
        )
        
        initial_audit_count = len(service.audit_log)
        
        # Withdraw
        service.withdraw_consent("audit_user2", ConsentType.ANALYTICS)
        
        # Should have created audit event
        assert len(service.audit_log) == initial_audit_count + 1
        
        latest_audit = service.audit_log[-1]
        assert latest_audit["action"] == "consent_withdrawn"
        assert latest_audit["user_id"] == "audit_user2"


class TestRepositoryCounts:
    """Test repository count methods for /status endpoint"""

    def test_count_unique_consent_users(self, in_memory_repo):
        """Test counting unique users with consent records"""
        repo = in_memory_repo
        
        # Add consents for multiple users
        repo.save_consent({
            "user_id": "user1",
            "consent_type": "marketing",
            "granted": True,
            "timestamp": datetime.utcnow().isoformat(),
        })
        repo.save_consent({
            "user_id": "user2",
            "consent_type": "marketing",
            "granted": True,
            "timestamp": datetime.utcnow().isoformat(),
        })
        repo.save_consent({
            "user_id": "user1",
            "consent_type": "analytics",
            "granted": True,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        count = repo.count_unique_consent_users()
        assert count == 2  # user1 and user2

    def test_count_audit_events(self, in_memory_repo):
        """Test counting audit events"""
        repo = in_memory_repo
        
        repo.log_audit("test_action", "user1", {"detail": "test"})
        repo.log_audit("test_action", "user2", {"detail": "test"})
        repo.log_audit("test_action", "user3", {"detail": "test"})
        
        count = repo.count_audit_events()
        assert count == 3


class TestMultipleConsentTypes:
    """Test handling multiple consent types per user"""

    def test_user_can_have_multiple_consent_types(self, gdpr_service_with_in_memory):
        """Test that a user can have multiple consent types simultaneously"""
        service = gdpr_service_with_in_memory
        
        user_id = "multi_consent_user"
        
        # Grant multiple consent types
        service.record_consent(user_id, ConsentType.MARKETING, True, "Marketing")
        service.record_consent(user_id, ConsentType.ANALYTICS, True, "Analytics")
        service.record_consent(user_id, ConsentType.PROFILING, False, "Profiling")
        
        # Check each independently
        assert service.check_consent(user_id, ConsentType.MARKETING) is True
        assert service.check_consent(user_id, ConsentType.ANALYTICS) is True
        assert service.check_consent(user_id, ConsentType.PROFILING) is False
        
        # List all consents
        consents = service.repo.list_consents_for_user(user_id)
        assert len(consents) == 3

    def test_withdraw_one_consent_leaves_others_active(self, gdpr_service_with_in_memory):
        """Test that withdrawing one consent type doesn't affect others"""
        service = gdpr_service_with_in_memory
        
        user_id = "selective_withdrawal_user"
        
        # Grant multiple
        service.record_consent(user_id, ConsentType.MARKETING, True, "Marketing")
        service.record_consent(user_id, ConsentType.ANALYTICS, True, "Analytics")
        
        # Withdraw one
        service.withdraw_consent(user_id, ConsentType.MARKETING)
        
        # Check states
        assert service.check_consent(user_id, ConsentType.MARKETING) is False
        assert service.check_consent(user_id, ConsentType.ANALYTICS) is True


class TestProcessingActivities:
    """Test processing activity recording"""

    def test_record_processing_activity(self, gdpr_service_with_in_memory):
        """Test recording a processing activity"""
        from services.compliance.gdpr_service import ProcessingLegalBasis
        
        service = gdpr_service_with_in_memory
        
        activity_id = service.record_processing_activity(
            activity_name="Email Marketing",
            purpose="Send promotional emails",
            legal_basis=ProcessingLegalBasis.CONSENT,
            data_categories=["email", "name"],
            recipients=["Marketing Team"],
            retention_period="2 years",
            security_measures=["encryption", "access control"]
        )
        
        assert activity_id is not None
        assert len(service.processing_activities) == 1
        
        activity = service.processing_activities[0]
        assert activity["name"] == "Email Marketing"
        assert activity["legal_basis"] == ProcessingLegalBasis.CONSENT


class TestRepositoryFallback:
    """Test repository selection and fallback"""

    def test_get_best_available_repository_returns_valid_repo(self):
        """Test that factory returns a valid repository"""
        repo = get_best_available_repository()
        
        assert isinstance(repo, GDPRRepository)
        assert hasattr(repo, 'save_consent')
        assert hasattr(repo, 'get_consent')
        assert hasattr(repo, 'withdraw_consent')
        assert hasattr(repo, 'count_unique_consent_users')


# Parametrized tests for all repository types (when available)
@pytest.mark.parametrize("repo_factory", [
    lambda: InMemoryGDPRRepository(),
    # Add PostgresGDPRRepository and MongoGDPRRepository when DB is available in test env
])
class TestRepositoryInterface:
    """Test that all repository implementations follow the same interface"""

    def test_save_and_get_consent(self, repo_factory):
        """Test basic save and retrieve"""
        repo = repo_factory()
        
        record = {
            "user_id": "test_user",
            "consent_type": "marketing",
            "granted": True,
            "purpose": "Testing",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {},
        }
        
        repo.save_consent(record)
        retrieved = repo.get_consent("test_user", "marketing")
        
        assert retrieved is not None
        assert retrieved["user_id"] == "test_user"
        assert retrieved["granted"] is True

    def test_withdraw_consent_interface(self, repo_factory):
        """Test withdraw consent interface"""
        repo = repo_factory()
        
        # Create first
        record = {
            "user_id": "withdraw_test",
            "consent_type": "analytics",
            "granted": True,
            "purpose": "Testing",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {},
        }
        repo.save_consent(record)
        
        # Withdraw
        withdrawn = repo.withdraw_consent("withdraw_test", "analytics")
        
        assert withdrawn["granted"] is False
        assert withdrawn["withdrawn_at"] is not None
