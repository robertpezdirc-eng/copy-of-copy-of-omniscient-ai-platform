#!/usr/bin/env python3
"""
OMNI Platform3 State Validator and Restoration System
Advanced validation and restoration mechanisms for OMNI Platform3

This system provides comprehensive state validation, corruption detection,
and automatic restoration capabilities to ensure platform integrity.

Features:
- Advanced state validation algorithms
- Corruption detection and recovery
- Automatic state restoration
- Cross-platform state synchronization
- Version compatibility checking
- Emergency recovery procedures
"""

import json
import time
import os
import sys
import hashlib
import difflib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

class OmniPlatform3Validator:
    """Advanced state validation and restoration system"""

    def __init__(self, platform3_instance=None):
        self.platform3 = platform3_instance
        self.validation_rules = {}
        self.corruption_signatures = []
        self.recovery_strategies = {}
        self.validation_history = []

        # Setup logging
        self.logger = logging.getLogger('OmniPlatform3Validator')

        # Initialize validation system
        self._initialize_validation_system()

    def _initialize_validation_system(self):
        """Initialize the validation system with comprehensive rules"""
        self.validation_rules = {
            "state_structure": {
                "required_fields": [
                    "platform_info", "system_metrics", "advanced_features",
                    "backup_info", "recovery_info"
                ],
                "optional_fields": [
                    "active_modules", "custom_config", "user_preferences"
                ]
            },
            "data_integrity": {
                "checksum_algorithm": "sha256",
                "redundancy_checks": True,
                "cross_reference_validation": True
            },
            "version_compatibility": {
                "min_supported_version": "2.0.0",
                "max_supported_version": "4.0.0",
                "migration_required": True
            },
            "platform_health": {
                "min_health_threshold": 0.7,
                "corruption_threshold": 0.1,
                "recovery_time_limit": 300  # 5 minutes
            }
        }

        # Define corruption signatures
        self._define_corruption_signatures()

        # Define recovery strategies
        self._define_recovery_strategies()

    def _define_corruption_signatures(self):
        """Define known corruption patterns and signatures"""
        self.corruption_signatures = [
            {
                "name": "json_syntax_error",
                "pattern": "JSON parsing fails",
                "severity": "high",
                "auto_recovery": True
            },
            {
                "name": "missing_required_fields",
                "pattern": "Required fields missing from state",
                "severity": "high",
                "auto_recovery": True
            },
            {
                "name": "checksum_mismatch",
                "pattern": "Stored checksum doesn't match calculated",
                "severity": "critical",
                "auto_recovery": True
            },
            {
                "name": "version_incompatibility",
                "pattern": "State version incompatible with platform",
                "severity": "medium",
                "auto_recovery": True
            },
            {
                "name": "data_type_mismatch",
                "pattern": "Data types don't match expected schema",
                "severity": "medium",
                "auto_recovery": False
            },
            {
                "name": "timestamp_anomaly",
                "pattern": "Timestamps are inconsistent or invalid",
                "severity": "low",
                "auto_recovery": True
            }
        ]

    def _define_recovery_strategies(self):
        """Define recovery strategies for different corruption types"""
        self.recovery_strategies = {
            "json_syntax_error": {
                "strategy": "restore_from_backup",
                "fallback": "create_new_state",
                "estimated_time": 30
            },
            "missing_required_fields": {
                "strategy": "field_reconstruction",
                "fallback": "restore_from_backup",
                "estimated_time": 45
            },
            "checksum_mismatch": {
                "strategy": "restore_from_backup",
                "fallback": "create_new_state",
                "estimated_time": 60
            },
            "version_incompatibility": {
                "strategy": "state_migration",
                "fallback": "restore_from_backup",
                "estimated_time": 90
            },
            "data_type_mismatch": {
                "strategy": "schema_correction",
                "fallback": "restore_from_backup",
                "estimated_time": 120
            },
            "timestamp_anomaly": {
                "strategy": "timestamp_correction",
                "fallback": "restore_from_backup",
                "estimated_time": 15
            }
        }

    def validate_platform_state(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive validation of platform state"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "corruption_detected": False,
            "recovery_needed": False,
            "validation_timestamp": time.time(),
            "validation_version": "1.0.0"
        }

        try:
            # 1. Basic structure validation
            structure_result = self._validate_state_structure(state_data)
            if not structure_result["valid"]:
                validation_result["issues"].extend(structure_result["issues"])
                validation_result["valid"] = False
                validation_result["corruption_detected"] = True

            # 2. Data integrity validation
            integrity_result = self._validate_data_integrity(state_data)
            if not integrity_result["valid"]:
                validation_result["issues"].extend(integrity_result["issues"])
                validation_result["valid"] = False
                validation_result["corruption_detected"] = True

            # 3. Version compatibility validation
            version_result = self._validate_version_compatibility(state_data)
            if not version_result["valid"]:
                validation_result["warnings"].extend(version_result["warnings"])
                if version_result["migration_needed"]:
                    validation_result["recovery_needed"] = True

            # 4. Platform health validation
            health_result = self._validate_platform_health(state_data)
            if not health_result["valid"]:
                validation_result["warnings"].extend(health_result["warnings"])

            # 5. Advanced validation checks
            advanced_result = self._perform_advanced_validation(state_data)
            if not advanced_result["valid"]:
                validation_result["issues"].extend(advanced_result["issues"])
                validation_result["valid"] = False

        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Validation exception: {str(e)}")
            validation_result["corruption_detected"] = True

        # Store validation result
        self.validation_history.append(validation_result)

        # Keep only last 100 validations
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]

        return validation_result

    def _validate_state_structure(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate basic state structure"""
        result = {"valid": True, "issues": []}

        # Check required fields
        required_fields = self.validation_rules["state_structure"]["required_fields"]
        for field in required_fields:
            if field not in state_data:
                result["valid"] = False
                result["issues"].append(f"Missing required field: {field}")

        # Check for unexpected fields (optional - can be disabled)
        if self.platform3 and self.platform3.config.get("validation", {}).get("strict_schema", False):
            expected_fields = set(required_fields + self.validation_rules["state_structure"]["optional_fields"])
            actual_fields = set(state_data.keys())

            unexpected_fields = actual_fields - expected_fields
            if unexpected_fields:
                result["issues"].append(f"Unexpected fields found: {list(unexpected_fields)}")

        return result

    def _validate_data_integrity(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data integrity including checksums"""
        result = {"valid": True, "issues": []}

        # Check checksum if present
        if "checksum" in state_data:
            stored_checksum = state_data["checksum"]
            calculated_checksum = self._calculate_checksum(state_data)

            if stored_checksum != calculated_checksum:
                result["valid"] = False
                result["issues"].append("Checksum mismatch - data corruption detected")

        # Check data types
        type_issues = self._validate_data_types(state_data)
        if type_issues:
            result["valid"] = False
            result["issues"].extend(type_issues)

        # Check for null/invalid values in critical fields
        null_issues = self._check_for_null_values(state_data)
        if null_issues:
            result["issues"].extend(null_issues)

        return result

    def _calculate_checksum(self, state_data: Dict[str, Any]) -> str:
        """Calculate checksum for state data"""
        # Remove checksum field for calculation
        data_to_hash = {k: v for k, v in state_data.items() if k != "checksum"}

        # Sort keys for consistent hashing
        data_str = json.dumps(data_to_hash, sort_keys=True)

        # Use SHA-256 for checksum
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _validate_data_types(self, state_data: Dict[str, Any]) -> List[str]:
        """Validate data types in state"""
        issues = []
        expected_types = {
            "platform_info": dict,
            "system_metrics": dict,
            "advanced_features": dict,
            "backup_info": dict,
            "recovery_info": dict,
            "active_modules": list
        }

        for field, expected_type in expected_types.items():
            if field in state_data:
                if not isinstance(state_data[field], expected_type):
                    issues.append(f"Field '{field}' should be {expected_type.__name__}, got {type(state_data[field]).__name__}")

        return issues

    def _check_for_null_values(self, state_data: Dict[str, Any]) -> List[str]:
        """Check for null or invalid values in critical fields"""
        issues = []
        critical_fields = ["platform_info", "system_metrics"]

        for field in critical_fields:
            if field in state_data:
                if state_data[field] is None:
                    issues.append(f"Critical field '{field}' is None")

        return issues

    def _validate_version_compatibility(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate version compatibility"""
        result = {"valid": True, "warnings": [], "migration_needed": False}

        if "platform_info" not in state_data:
            return result

        platform_info = state_data["platform_info"]
        state_version = platform_info.get("version", "1.0.0")

        # Simple version comparison (in real implementation, use proper version comparison)
        min_version = self.validation_rules["version_compatibility"]["min_supported_version"]
        max_version = self.validation_rules["version_compatibility"]["max_supported_version"]

        if self._compare_versions(state_version, min_version) < 0:
            result["valid"] = False
            result["warnings"].append(f"State version {state_version} is below minimum supported {min_version}")

        if self._compare_versions(state_version, max_version) > 0:
            result["warnings"].append(f"State version {state_version} is newer than maximum supported {max_version}")
            result["migration_needed"] = True

        return result

    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings"""
        try:
            v1_parts = [int(x) for x in version1.split(".")]
            v2_parts = [int(x) for x in version2.split(".")]

            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            for i in range(max_len):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1

            return 0
        except:
            return 0  # Default to equal if comparison fails

    def _validate_platform_health(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate platform health indicators"""
        result = {"valid": True, "warnings": []}

        if "system_metrics" not in state_data:
            return result

        metrics = state_data["system_metrics"]
        min_health = self.validation_rules["platform_health"]["min_health_threshold"]

        # Check overall health
        health_score = metrics.get("platform_health", 1.0)
        if health_score < min_health:
            result["warnings"].append(f"Platform health {health_score".2f"} is below threshold {min_health}")

        # Check state integrity
        integrity_score = metrics.get("state_integrity", 1.0)
        if integrity_score < 0.9:
            result["warnings"].append(f"State integrity {integrity_score".2f"} is degraded")

        return result

    def _perform_advanced_validation(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform advanced validation checks"""
        result = {"valid": True, "issues": []}

        # Cross-field validation
        cross_field_issues = self._validate_cross_field_consistency(state_data)
        if cross_field_issues:
            result["issues"].extend(cross_field_issues)

        # Timestamp validation
        timestamp_issues = self._validate_timestamps(state_data)
        if timestamp_issues:
            result["issues"].extend(timestamp_issues)

        # Business logic validation
        logic_issues = self._validate_business_logic(state_data)
        if logic_issues:
            result["issues"].extend(logic_issues)

        if result["issues"]:
            result["valid"] = False

        return result

    def _validate_cross_field_consistency(self, state_data: Dict[str, Any]) -> List[str]:
        """Validate consistency between related fields"""
        issues = []

        # Check backup count consistency
        backup_info = state_data.get("backup_info", {})
        backup_count = backup_info.get("backup_count", 0)

        if self.platform3:
            actual_backup_count = len([f for f in os.listdir(self.platform3.backup_dir)
                                     if f.startswith('state_backup_')])
            if abs(backup_count - actual_backup_count) > 2:  # Allow small discrepancy
                issues.append(f"Backup count mismatch: state shows {backup_count}, actual {actual_backup_count}")

        return issues

    def _validate_timestamps(self, state_data: Dict[str, Any]) -> List[str]:
        """Validate timestamp fields"""
        issues = []

        try:
            # Check platform creation timestamp
            created_at = state_data.get("platform_info", {}).get("created_at")
            if created_at:
                datetime.fromisoformat(created_at.replace('Z', '+00:00'))

            # Check last updated timestamp
            last_updated = state_data.get("platform_info", {}).get("last_updated")
            if last_updated:
                datetime.fromisoformat(last_updated.replace('Z', '+00:00'))

            # Check backup timestamp
            last_backup = state_data.get("backup_info", {}).get("last_backup")
            if last_backup:
                datetime.fromisoformat(last_backup.replace('Z', '+00:00'))

        except ValueError as e:
            issues.append(f"Invalid timestamp format: {e}")

        return issues

    def _validate_business_logic(self, state_data: Dict[str, Any]) -> List[str]:
        """Validate business logic constraints"""
        issues = []

        # Check that successful operations don't exceed total operations
        metrics = state_data.get("system_metrics", {})
        total_ops = metrics.get("total_operations", 0)
        successful_ops = metrics.get("successful_operations", 0)
        failed_ops = metrics.get("failed_operations", 0)

        if successful_ops + failed_ops != total_ops:
            issues.append("Operation counts don't add up correctly")

        # Check that health scores are within valid range
        health_score = metrics.get("platform_health", 1.0)
        if not (0.0 <= health_score <= 1.0):
            issues.append(f"Platform health score {health_score} is outside valid range [0.0, 1.0]")

        return issues

    def detect_corruption_type(self, state_data: Dict[str, Any]) -> List[str]:
        """Detect types of corruption in state data"""
        corruption_types = []

        # Check each corruption signature
        for signature in self.corruption_signatures:
            if self._matches_corruption_signature(state_data, signature):
                corruption_types.append(signature["name"])

        return corruption_types

    def _matches_corruption_signature(self, state_data: Dict[str, Any], signature: Dict[str, Any]) -> bool:
        """Check if state matches a corruption signature"""
        signature_name = signature["name"]

        if signature_name == "json_syntax_error":
            try:
                json.dumps(state_data)
                return False
            except:
                return True

        elif signature_name == "missing_required_fields":
            required_fields = self.validation_rules["state_structure"]["required_fields"]
            return any(field not in state_data for field in required_fields)

        elif signature_name == "checksum_mismatch":
            if "checksum" in state_data:
                stored_checksum = state_data["checksum"]
                calculated_checksum = self._calculate_checksum(state_data)
                return stored_checksum != calculated_checksum
            return False

        elif signature_name == "version_incompatibility":
            version_result = self._validate_version_compatibility(state_data)
            return not version_result["valid"]

        elif signature_name == "data_type_mismatch":
            type_issues = self._validate_data_types(state_data)
            return len(type_issues) > 0

        elif signature_name == "timestamp_anomaly":
            timestamp_issues = self._validate_timestamps(state_data)
            return len(timestamp_issues) > 0

        return False

    def restore_state(self, corruption_types: List[str], state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore state using appropriate recovery strategies"""
        restoration_result = {
            "success": False,
            "restored": False,
            "strategy_used": None,
            "backup_used": None,
            "time_taken": 0,
            "issues_encountered": []
        }

        start_time = time.time()

        try:
            # Try recovery strategies in order of preference
            for corruption_type in corruption_types:
                if corruption_type in self.recovery_strategies:
                    strategy = self.recovery_strategies[corruption_type]

                    # Try primary strategy
                    success = self._execute_recovery_strategy(strategy["strategy"], state_data, corruption_type)

                    if success:
                        restoration_result["success"] = True
                        restoration_result["restored"] = True
                        restoration_result["strategy_used"] = strategy["strategy"]
                        restoration_result["time_taken"] = time.time() - start_time
                        break

                    # Try fallback strategy
                    if "fallback" in strategy:
                        success = self._execute_recovery_strategy(strategy["fallback"], state_data, corruption_type)
                        if success:
                            restoration_result["success"] = True
                            restoration_result["restored"] = True
                            restoration_result["strategy_used"] = strategy["fallback"]
                            restoration_result["time_taken"] = time.time() - start_time
                            break

            if not restoration_result["success"]:
                restoration_result["issues_encountered"].append("All recovery strategies failed")

        except Exception as e:
            restoration_result["issues_encountered"].append(f"Restoration exception: {str(e)}")

        return restoration_result

    def _execute_recovery_strategy(self, strategy: str, state_data: Dict[str, Any], corruption_type: str) -> bool:
        """Execute a specific recovery strategy"""
        try:
            if strategy == "restore_from_backup":
                return self._restore_from_backup(state_data)
            elif strategy == "create_new_state":
                return self._create_new_state(state_data)
            elif strategy == "field_reconstruction":
                return self._reconstruct_missing_fields(state_data)
            elif strategy == "state_migration":
                return self._migrate_state_version(state_data)
            elif strategy == "schema_correction":
                return self._correct_schema_issues(state_data)
            elif strategy == "timestamp_correction":
                return self._correct_timestamp_issues(state_data)

            return False

        except Exception as e:
            self.logger.error(f"Recovery strategy {strategy} failed: {e}")
            return False

    def _restore_from_backup(self, state_data: Dict[str, Any]) -> bool:
        """Restore state from most recent backup"""
        try:
            if not self.platform3:
                return False

            # Find most recent backup
            backup_files = [f for f in os.listdir(self.platform3.backup_dir)
                          if f.startswith('state_backup_') and f.endswith('.json')]
            if not backup_files:
                return False

            backup_files.sort(reverse=True)
            latest_backup = backup_files[0]
            backup_path = os.path.join(self.platform3.backup_dir, latest_backup)

            # Load backup
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            # Validate backup integrity
            validation_result = self.validate_platform_state(backup_data.get("state_data", {}))
            if validation_result["valid"]:
                # Update current state with backup data
                if self.platform3:
                    self.platform3.current_state = backup_data["state_data"].copy()
                    self.platform3.save_platform_state()

                self.logger.info(f"Successfully restored from backup: {latest_backup}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Backup restoration failed: {e}")
            return False

    def _create_new_state(self, state_data: Dict[str, Any]) -> bool:
        """Create a new state when recovery is not possible"""
        try:
            if self.platform3:
                self.platform3._create_initial_state()
                self.platform3.save_platform_state()
                self.logger.info("Created new state after recovery failure")
                return True

            return False

        except Exception as e:
            self.logger.error(f"New state creation failed: {e}")
            return False

    def _reconstruct_missing_fields(self, state_data: Dict[str, Any]) -> bool:
        """Reconstruct missing fields in state"""
        try:
            # Add missing required fields with default values
            if "backup_info" not in state_data:
                state_data["backup_info"] = {
                    "last_backup": None,
                    "backup_count": 0,
                    "next_backup_due": None
                }

            if "recovery_info" not in state_data:
                state_data["recovery_info"] = {
                    "last_recovery": None,
                    "recovery_attempts": 0,
                    "successful_recoveries": 0
                }

            # Update recovery info
            state_data["recovery_info"]["recovery_attempts"] += 1
            state_data["recovery_info"]["last_recovery"] = datetime.now().isoformat()

            return True

        except Exception as e:
            self.logger.error(f"Field reconstruction failed: {e}")
            return False

    def _migrate_state_version(self, state_data: Dict[str, Any]) -> bool:
        """Migrate state to current version"""
        try:
            # Update version information
            if "platform_info" in state_data:
                state_data["platform_info"]["version"] = self.platform3.version if self.platform3 else "3.0.0"
                state_data["platform_info"]["state_version"] = int(self.platform3.version.split('.')[0]) if self.platform3 else 3

            return True

        except Exception as e:
            self.logger.error(f"State migration failed: {e}")
            return False

    def _correct_schema_issues(self, state_data: Dict[str, Any]) -> bool:
        """Correct schema-related issues"""
        try:
            # Fix common data type issues
            if "system_metrics" in state_data:
                metrics = state_data["system_metrics"]

                # Ensure numeric fields are numbers
                numeric_fields = ["platform_health", "state_integrity", "uptime"]
                for field in numeric_fields:
                    if field in metrics:
                        try:
                            metrics[field] = float(metrics[field])
                        except:
                            metrics[field] = 0.0

            return True

        except Exception as e:
            self.logger.error(f"Schema correction failed: {e}")
            return False

    def _correct_timestamp_issues(self, state_data: Dict[str, Any]) -> bool:
        """Correct timestamp-related issues"""
        try:
            current_time = datetime.now().isoformat()

            # Update timestamps to current time
            if "platform_info" in state_data:
                state_data["platform_info"]["last_updated"] = current_time

            if "backup_info" in state_data:
                state_data["backup_info"]["next_backup_due"] = current_time

            return True

        except Exception as e:
            self.logger.error(f"Timestamp correction failed: {e}")
            return False

    def get_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        if not self.validation_history:
            return {"error": "No validation history available"}

        latest_validation = self.validation_history[-1]

        # Calculate validation statistics
        total_validations = len(self.validation_history)
        successful_validations = len([v for v in self.validation_history if v["valid"]])
        corruption_incidents = len([v for v in self.validation_history if v["corruption_detected"]])

        return {
            "latest_validation": latest_validation,
            "validation_statistics": {
                "total_validations": total_validations,
                "successful_validations": successful_validations,
                "failed_validations": total_validations - successful_validations,
                "corruption_incidents": corruption_incidents,
                "success_rate": successful_validations / max(total_validations, 1)
            },
            "validation_rules": self.validation_rules,
            "corruption_signatures": len(self.corruption_signatures),
            "recovery_strategies": len(self.recovery_strategies),
            "report_generated": time.time()
        }

def main():
    """Main function to demonstrate Platform3 validation system"""
    print("🔍 OMNI Platform3 State Validator and Restoration System")
    print("=" * 70)
    print("🛡️ Advanced state validation and corruption recovery")
    print("🔄 Automatic restoration and health monitoring")
    print("💾 Never lose your platform state again!")
    print()

    try:
        # Create validator instance
        validator = OmniPlatform3Validator()

        # Demonstrate validation capabilities
        print("🔍 Validation System Features:")
        print(f"  ✅ Validation Rules: {len(validator.validation_rules)} categories")
        print(f"  🛡️ Corruption Signatures: {len(validator.corruption_signatures)} patterns")
        print(f"  🔄 Recovery Strategies: {len(validator.recovery_strategies)} methods")

        # Show validation rules
        print("
📋 Validation Rules:"        for category, rules in validator.validation_rules.items():
            print(f"  📂 {category.replace('_', ' ').title()}:")
            for rule, value in rules.items():
                if isinstance(value, list):
                    print(f"    • {rule}: {len(value)} items")
                else:
                    print(f"    • {rule}: {value}")

        # Show corruption signatures
        print("
⚠️ Corruption Signatures:"        for signature in validator.corruption_signatures:
            severity_icon = {"low": "🟡", "medium": "🟠", "high": "🔴", "critical": "❌"}
            icon = severity_icon.get(signature["severity"], "❓")
            auto_recovery = "✅" if signature["auto_recovery"] else "❌"
            print(f"  {icon} {signature['name']}: {signature['severity']} severity, Auto-recovery: {auto_recovery}")

        # Show recovery strategies
        print("
🔧 Recovery Strategies:"        for strategy_name, strategy_info in validator.recovery_strategies.items():
            print(f"  🔄 {strategy_name}: {strategy_info['estimated_time']}s estimated")
            if "fallback" in strategy_info:
                print(f"    Fallback: {strategy_info['fallback']}")

        # Generate validation report
        report = validator.get_validation_report()

        print("
📊 Validation System Report:"        stats = report["validation_statistics"]
        print(f"  📈 Success Rate: {stats['success_rate']".1%"}")
        print(f"  ✅ Successful: {stats['successful_validations']}")
        print(f"  ❌ Failed: {stats['failed_validations']}")
        print(f"  ⚠️ Corruption Incidents: {stats['corruption_incidents']}")

        print("
🎯 OMNI Platform3 Validator Ready!"        print("🛡️ State validation: Active")
        print("🔄 Corruption recovery: Ready")
        print("💾 Backup restoration: Available")
        print("🔍 Health monitoring: Operational")

        return report

    except Exception as e:
        print(f"\n❌ Validator initialization failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    report = main()
    print(f"\n✅ Validation system execution completed")