"""
Compliance Service
HIPAA, SOC 2, ISO 27001 compliance management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ComplianceStandard(str, Enum):
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


class ControlStatus(str, Enum):
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"


class ComplianceService:
    """Service for managing compliance requirements"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.controls = {}
        self.audits = {}
        self.policies = {}
        
        # Initialize compliance controls
        self._initialize_controls()
    
    def _initialize_controls(self):
        """Initialize compliance control definitions"""
        # HIPAA Controls
        self.controls["hipaa_164_308_a_1"] = {
            "id": "hipaa_164_308_a_1",
            "standard": ComplianceStandard.HIPAA,
            "section": "164.308(a)(1)",
            "title": "Security Management Process",
            "description": "Implement policies and procedures to prevent, detect, contain, and correct security violations",
            "requirements": ["Risk analysis", "Risk management", "Sanction policy", "Information system activity review"],
            "status": ControlStatus.IMPLEMENTED
        }
        
        # SOC 2 Controls
        self.controls["soc2_cc6_1"] = {
            "id": "soc2_cc6_1",
            "standard": ComplianceStandard.SOC2,
            "section": "CC6.1",
            "title": "Logical and Physical Access Controls",
            "description": "The entity implements logical access security software, infrastructure, and architectures over protected information assets",
            "requirements": ["Multi-factor authentication", "Access reviews", "Privileged access management"],
            "status": ControlStatus.IMPLEMENTED
        }
        
        # ISO 27001 Controls
        self.controls["iso_a5_1_1"] = {
            "id": "iso_a5_1_1",
            "standard": ComplianceStandard.ISO27001,
            "section": "A.5.1.1",
            "title": "Policies for information security",
            "description": "A set of policies for information security shall be defined, approved by management, published and communicated",
            "requirements": ["Information security policy", "Review and update procedures"],
            "status": ControlStatus.IMPLEMENTED
        }
    
    async def get_compliance_status(self, tenant_id: str, standard: ComplianceStandard) -> Dict[str, Any]:
        """Get compliance status for a standard"""
        relevant_controls = [
            ctrl for ctrl_id, ctrl in self.controls.items()
            if ctrl["standard"] == standard
        ]
        
        total_controls = len(relevant_controls)
        implemented = len([c for c in relevant_controls if c["status"] == ControlStatus.IMPLEMENTED])
        partial = len([c for c in relevant_controls if c["status"] == ControlStatus.PARTIAL])
        not_implemented = len([c for c in relevant_controls if c["status"] == ControlStatus.NOT_IMPLEMENTED])
        
        compliance_percentage = (implemented / total_controls * 100) if total_controls > 0 else 0
        
        return {
            "tenant_id": tenant_id,
            "standard": standard,
            "compliance_percentage": compliance_percentage,
            "total_controls": total_controls,
            "implemented": implemented,
            "partial": partial,
            "not_implemented": not_implemented,
            "last_assessed": datetime.now().isoformat()
        }
    
    async def get_control(self, control_id: str) -> Optional[Dict[str, Any]]:
        """Get specific control details"""
        return self.controls.get(control_id)
    
    async def update_control_status(self, control_id: str, status: ControlStatus, evidence: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update control implementation status"""
        control = self.controls.get(control_id)
        if not control:
            return None
        
        control["status"] = status
        control["last_updated"] = datetime.now().isoformat()
        if evidence:
            control["evidence"] = evidence
        
        return control
    
    async def create_audit(self, tenant_id: str, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create compliance audit record"""
        audit_id = f"audit_{tenant_id}_{int(datetime.now().timestamp())}"
        
        audit = {
            "id": audit_id,
            "tenant_id": tenant_id,
            "standard": audit_data.get("standard"),
            "auditor_name": audit_data.get("auditor_name", ""),
            "audit_type": audit_data.get("audit_type", "internal"),  # internal or external
            "scope": audit_data.get("scope", []),
            "findings": audit_data.get("findings", []),
            "status": "in_progress",
            "start_date": audit_data.get("start_date", datetime.now().isoformat()),
            "end_date": audit_data.get("end_date"),
            "created_at": datetime.now().isoformat()
        }
        
        self.audits[audit_id] = audit
        return audit
    
    async def add_audit_finding(self, audit_id: str, finding: Dict[str, Any]) -> bool:
        """Add finding to audit"""
        audit = self.audits.get(audit_id)
        if not audit:
            return False
        
        finding["id"] = f"finding_{int(datetime.now().timestamp())}"
        finding["created_at"] = datetime.now().isoformat()
        
        if "findings" not in audit:
            audit["findings"] = []
        
        audit["findings"].append(finding)
        return True
    
    async def complete_audit(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Mark audit as complete"""
        audit = self.audits.get(audit_id)
        if not audit:
            return None
        
        audit["status"] = "completed"
        audit["end_date"] = datetime.now().isoformat()
        audit["completed_at"] = datetime.now().isoformat()
        
        return audit
    
    async def get_audits(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all audits for tenant"""
        return [
            audit for audit_id, audit in self.audits.items()
            if audit["tenant_id"] == tenant_id
        ]
    
    async def create_policy(self, tenant_id: str, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create compliance policy document"""
        policy_id = f"policy_{tenant_id}_{int(datetime.now().timestamp())}"
        
        policy = {
            "id": policy_id,
            "tenant_id": tenant_id,
            "title": policy_data.get("title", ""),
            "category": policy_data.get("category", ""),  # e.g., "data_protection", "access_control"
            "description": policy_data.get("description", ""),
            "content": policy_data.get("content", ""),
            "version": policy_data.get("version", "1.0"),
            "status": "draft",
            "owner": policy_data.get("owner", ""),
            "reviewers": policy_data.get("reviewers", []),
            "approval_date": None,
            "effective_date": None,
            "review_frequency": policy_data.get("review_frequency", "annual"),
            "next_review_date": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.policies[policy_id] = policy
        return policy
    
    async def approve_policy(self, policy_id: str, approver: str) -> Optional[Dict[str, Any]]:
        """Approve policy"""
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        
        policy["status"] = "approved"
        policy["approval_date"] = datetime.now().isoformat()
        policy["effective_date"] = datetime.now().isoformat()
        policy["approved_by"] = approver
        policy["updated_at"] = datetime.now().isoformat()
        
        return policy
    
    async def get_policies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all policies for tenant"""
        return [
            policy for policy_id, policy in self.policies.items()
            if policy["tenant_id"] == tenant_id
        ]
    
    async def generate_compliance_report(self, tenant_id: str, standard: ComplianceStandard) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        status = await self.get_compliance_status(tenant_id, standard)
        audits = [a for a in await self.get_audits(tenant_id) if a.get("standard") == standard]
        policies = await self.get_policies(tenant_id)
        
        # Get controls for standard
        controls = [
            ctrl for ctrl_id, ctrl in self.controls.items()
            if ctrl["standard"] == standard
        ]
        
        return {
            "tenant_id": tenant_id,
            "standard": standard,
            "generated_at": datetime.now().isoformat(),
            "compliance_status": status,
            "controls": controls,
            "audits": audits,
            "policies": policies,
            "recommendations": self._get_recommendations(controls)
        }
    
    def _get_recommendations(self, controls: List[Dict[str, Any]]) -> List[str]:
        """Get recommendations based on control status"""
        recommendations = []
        
        not_implemented = [c for c in controls if c["status"] == ControlStatus.NOT_IMPLEMENTED]
        partial = [c for c in controls if c["status"] == ControlStatus.PARTIAL]
        
        if not_implemented:
            recommendations.append(f"Implement {len(not_implemented)} missing controls")
        
        if partial:
            recommendations.append(f"Complete {len(partial)} partially implemented controls")
        
        return recommendations
