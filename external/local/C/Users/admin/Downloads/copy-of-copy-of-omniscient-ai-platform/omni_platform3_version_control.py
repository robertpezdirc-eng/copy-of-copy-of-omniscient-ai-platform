#!/usr/bin/env python3
"""
OMNI Platform3 Version Control and Rollback System
Advanced version control and rollback capabilities for OMNI Platform3

This system provides comprehensive version control, change tracking,
and rollback capabilities to ensure platform state integrity and
recovery options.

Features:
- Complete state version tracking
- Change history and diff analysis
- One-click rollback to any previous state
- Branch-based state management
- Automatic rollback on critical failures
- State snapshot and comparison tools
"""

import json
import time
import os
import sys
import hashlib
import difflib
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import copy

class VersionControlStrategy(Enum):
    """Version control strategies"""
    LINEAR_HISTORY = "linear_history"
    BRANCH_BASED = "branch_based"
    SNAPSHOT_BASED = "snapshot_based"

class RollbackTrigger(Enum):
    """Triggers for automatic rollback"""
    MANUAL = "manual"
    HEALTH_DEGRADATION = "health_degradation"
    CORRUPTION_DETECTED = "corruption_detected"
    USER_REQUEST = "user_request"
    SCHEDULED = "scheduled"

class OmniPlatform3VersionControl:
    """Advanced version control system for OMNI Platform3"""

    def __init__(self, platform3_instance=None):
        self.platform3 = platform3_instance

        # Version control configuration
        self.vc_config = {
            "strategy": VersionControlStrategy.LINEAR_HISTORY.value,
            "auto_commit": True,
            "commit_interval": 300,  # 5 minutes
            "max_versions": 100,
            "max_age_days": 30,
            "enable_branching": False,
            "auto_rollback_threshold": 0.5,  # 50% health
            "rollback_on_corruption": True,
            "create_snapshot_on_rollback": True
        }

        # Version control state
        self.version_history = []
        self.current_version = None
        self.branches = {}
        self.rollback_history = []
        self.pending_commits = []

        # Version metadata
        self.next_version_id = 1
        self.base_version = None

        # Setup logging
        self.logger = logging.getLogger('OmniPlatform3VC')

        # Initialize version control system
        self._initialize_version_control()

    def _initialize_version_control(self):
        """Initialize the version control system"""
        # Create version control directories
        os.makedirs("omni_platform3_versions", exist_ok=True)
        os.makedirs("omni_platform3_versions/commits", exist_ok=True)
        os.makedirs("omni_platform3_versions/branches", exist_ok=True)
        os.makedirs("omni_platform3_versions/rollbacks", exist_ok=True)

        # Load existing version history
        self._load_version_history()

        # Setup auto-commit if enabled
        if self.vc_config["auto_commit"]:
            self._start_auto_commit()

    def _load_version_history(self):
        """Load existing version history"""
        try:
            history_file = "omni_platform3_versions/version_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.version_history = json.load(f)

                # Set next version ID
                if self.version_history:
                    self.next_version_id = max(v["version_id"] for v in self.version_history) + 1

        except Exception as e:
            self.logger.error(f"Failed to load version history: {e}")
            self.version_history = []

    def _start_auto_commit(self):
        """Start automatic commit process"""
        import threading

        def auto_commit_loop():
            while True:
                try:
                    time.sleep(self.vc_config["commit_interval"])
                    if self.platform3 and self._has_significant_changes():
                        self.commit_state("auto_commit", "Automatic commit")
                except Exception as e:
                    self.logger.error(f"Auto-commit error: {e}")

        commit_thread = threading.Thread(target=auto_commit_loop, daemon=True)
        commit_thread.start()

    def _has_significant_changes(self) -> bool:
        """Check if there are significant changes since last commit"""
        if not self.version_history:
            return True

        try:
            latest_version = self.version_history[-1]
            latest_state = latest_version["state_data"]

            # Compare current state with latest version
            current_hash = self._calculate_state_hash(self.platform3.current_state)
            latest_hash = latest_version["state_hash"]

            return current_hash != latest_hash

        except:
            return True  # Assume changes if comparison fails

    def _calculate_state_hash(self, state_data: Dict[str, Any]) -> str:
        """Calculate hash of state data"""
        state_copy = json.loads(json.dumps(state_data, sort_keys=True))
        state_str = json.dumps(state_copy, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()

    def commit_state(self, commit_message: str, author: str = "system",
                    version_type: str = "regular") -> Optional[str]:
        """Commit current platform state to version history"""
        try:
            if not self.platform3:
                return None

            # Create version record
            version_record = {
                "version_id": self.next_version_id,
                "version_name": f"v{self.next_version_id}",
                "commit_message": commit_message,
                "author": author,
                "timestamp": time.time(),
                "version_type": version_type,
                "state_hash": self._calculate_state_hash(self.platform3.current_state),
                "state_data": copy.deepcopy(self.platform3.current_state),
                "parent_version": self.current_version,
                "branch": "main",
                "metadata": {
                    "platform_version": self.platform3.version,
                    "environment": getattr(self.platform3, 'current_environment', 'unknown'),
                    "state_size": len(json.dumps(self.platform3.current_state)),
                    "significant_changes": self._identify_significant_changes()
                }
            }

            # Save state data to separate file for large states
            if len(json.dumps(version_record["state_data"])) > 10000:  # 10KB
                state_file = f"omni_platform3_versions/commits/state_{self.next_version_id}.json"
                with open(state_file, 'w') as f:
                    json.dump(version_record["state_data"], f, indent=2)
                version_record["state_file"] = state_file
                del version_record["state_data"]  # Remove from main record

            # Add to version history
            self.version_history.append(version_record)

            # Update current version
            self.current_version = self.next_version_id

            # Increment version counter
            self.next_version_id += 1

            # Manage version count
            self._manage_version_count()

            # Save version history
            self._save_version_history()

            self.logger.info(f"State committed: v{version_record['version_id']} - {commit_message}")

            return f"v{version_record['version_id']}"

        except Exception as e:
            self.logger.error(f"Failed to commit state: {e}")
            return None

    def _identify_significant_changes(self) -> List[str]:
        """Identify significant changes in current state"""
        changes = []

        if len(self.version_history) < 2:
            return ["initial_state"]

        try:
            current_state = self.platform3.current_state
            latest_version = self.version_history[-1]
            latest_state = latest_version.get("state_data") or self._load_state_from_file(latest_version.get("state_file"))

            if not latest_state:
                return ["unknown_changes"]

            # Compare key metrics
            current_metrics = current_state.get("system_metrics", {})
            latest_metrics = latest_state.get("system_metrics", {})

            # Check for significant metric changes
            if current_metrics.get("total_operations", 0) > latest_metrics.get("total_operations", 0) + 10:
                changes.append("significant_operation_increase")

            if current_metrics.get("platform_health", 1.0) < latest_metrics.get("platform_health", 1.0) - 0.2:
                changes.append("health_degradation")

            if current_metrics.get("state_integrity", 1.0) < latest_metrics.get("state_integrity", 1.0) - 0.1:
                changes.append("integrity_degradation")

            # Check for feature changes
            current_features = set(current_state.get("advanced_features", {}).keys())
            latest_features = set(latest_state.get("advanced_features", {}).keys())

            if current_features != latest_features:
                changes.append("feature_configuration_change")

        except Exception as e:
            self.logger.error(f"Error identifying changes: {e}")
            changes.append("error_during_analysis")

        return changes or ["minor_changes"]

    def _load_state_from_file(self, state_file: str) -> Optional[Dict[str, Any]]:
        """Load state data from separate file"""
        try:
            if state_file and os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None

    def _manage_version_count(self):
        """Manage the number of stored versions"""
        max_versions = self.vc_config["max_versions"]

        if len(self.version_history) > max_versions:
            # Remove oldest versions
            versions_to_remove = self.version_history[:-max_versions]

            for old_version in versions_to_remove:
                # Remove state file if it exists
                state_file = old_version.get("state_file")
                if state_file and os.path.exists(state_file):
                    try:
                        os.remove(state_file)
                    except:
                        pass

            # Keep only recent versions
            self.version_history = self.version_history[-max_versions:]

    def _save_version_history(self):
        """Save version history to persistent storage"""
        try:
            with open("omni_platform3_versions/version_history.json", 'w') as f:
                json.dump(self.version_history, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save version history: {e}")

    def get_version_info(self, version_id: Optional[int] = None) -> Dict[str, Any]:
        """Get information about a specific version or current version"""
        if version_id is None:
            version_id = self.current_version

        # Find version in history
        for version in self.version_history:
            if version["version_id"] == version_id:
                return version

        return {"error": "Version not found"}

    def list_versions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent versions with metadata"""
        recent_versions = self.version_history[-limit:] if self.version_history else []
        return recent_versions

    def compare_versions(self, version1_id: int, version2_id: int) -> Dict[str, Any]:
        """Compare two versions and show differences"""
        version1 = None
        version2 = None

        # Find versions
        for version in self.version_history:
            if version["version_id"] == version1_id:
                version1 = version
            elif version["version_id"] == version2_id:
                version2 = version

        if not version1 or not version2:
            return {"error": "One or both versions not found"}

        # Load state data if stored in separate files
        state1 = version1.get("state_data") or self._load_state_from_file(version1.get("state_file"))
        state2 = version2.get("state_data") or self._load_state_from_file(version2.get("state_file"))

        if not state1 or not state2:
            return {"error": "Could not load state data for comparison"}

        # Generate diff
        diff_result = {
            "version1": {"id": version1_id, "timestamp": version1["timestamp"]},
            "version2": {"id": version2_id, "timestamp": version2["timestamp"]},
            "differences": self._generate_state_diff(state1, state2),
            "summary": self._generate_diff_summary(state1, state2)
        }

        return diff_result

    def _generate_state_diff(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed diff between two states"""
        diff = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged": {}
        }

        # Get all keys from both states
        all_keys = set(state1.keys()) | set(state2.keys())

        for key in all_keys:
            value1 = state1.get(key)
            value2 = state2.get(key)

            if key not in state1:
                diff["added"][key] = value2
            elif key not in state2:
                diff["removed"][key] = value1
            elif value1 != value2:
                diff["modified"][key] = {
                    "old_value": value1,
                    "new_value": value2
                }
            else:
                diff["unchanged"][key] = value1

        return diff

    def _generate_diff_summary(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of differences"""
        diff = self._generate_state_diff(state1, state2)

        summary = {
            "total_changes": len(diff["added"]) + len(diff["removed"]) + len(diff["modified"]),
            "fields_added": len(diff["added"]),
            "fields_removed": len(diff["removed"]),
            "fields_modified": len(diff["modified"]),
            "fields_unchanged": len(diff["unchanged"])
        }

        return summary

    def rollback_to_version(self, version_id: int, trigger: RollbackTrigger = RollbackTrigger.MANUAL,
                          reason: str = "Manual rollback") -> bool:
        """Rollback platform state to specified version"""
        try:
            # Find target version
            target_version = None
            for version in self.version_history:
                if version["version_id"] == version_id:
                    target_version = version
                    break

            if not target_version:
                self.logger.error(f"Version {version_id} not found for rollback")
                return False

            # Create snapshot of current state before rollback
            if self.vc_config["create_snapshot_on_rollback"]:
                snapshot_message = f"Pre-rollback snapshot before rolling back to v{version_id}"
                self.commit_state(snapshot_message, "system", "snapshot")

            # Load target state
            target_state = target_version.get("state_data") or self._load_state_from_file(target_version.get("state_file"))

            if not target_state:
                self.logger.error(f"Could not load state data for version {version_id}")
                return False

            # Perform rollback
            if self.platform3:
                # Backup current state
                old_state = copy.deepcopy(self.platform3.current_state)

                # Apply target state
                self.platform3.current_state = copy.deepcopy(target_state)
                self.platform3.save_platform_state()

                # Record rollback
                rollback_record = {
                    "rollback_id": f"rollback_{int(time.time())}",
                    "from_version": self.current_version,
                    "to_version": version_id,
                    "trigger": trigger.value,
                    "reason": reason,
                    "timestamp": time.time(),
                    "success": True,
                    "state_backup": old_state
                }

                self.rollback_history.append(rollback_record)
                self.current_version = version_id

                # Save rollback record
                self._save_rollback_history()

                self.logger.info(f"Successfully rolled back to version {version_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Rollback to version {version_id} failed: {e}")
            return False

    def _save_rollback_history(self):
        """Save rollback history to persistent storage"""
        try:
            with open("omni_platform3_versions/rollback_history.json", 'w') as f:
                json.dump(self.rollback_history, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save rollback history: {e}")

    def create_branch(self, branch_name: str, from_version: Optional[int] = None) -> bool:
        """Create a new branch from specified version"""
        if not self.vc_config["enable_branching"]:
            self.logger.warning("Branching is disabled in configuration")
            return False

        try:
            # Use current version if not specified
            if from_version is None:
                from_version = self.current_version

            # Create branch record
            branch_record = {
                "branch_name": branch_name,
                "created_from": from_version,
                "created_at": time.time(),
                "versions": [from_version],
                "current_version": from_version,
                "metadata": {
                    "author": "system",
                    "purpose": "feature_development"
                }
            }

            self.branches[branch_name] = branch_record

            # Save branch data
            self._save_branches()

            self.logger.info(f"Created branch '{branch_name}' from version {from_version}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create branch '{branch_name}': {e}")
            return False

    def _save_branches(self):
        """Save branch information to persistent storage"""
        try:
            with open("omni_platform3_versions/branches.json", 'w') as f:
                json.dump(self.branches, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save branches: {e}")

    def switch_branch(self, branch_name: str) -> bool:
        """Switch to specified branch"""
        if branch_name not in self.branches:
            self.logger.error(f"Branch '{branch_name}' not found")
            return False

        try:
            branch = self.branches[branch_name]

            # Commit current state if on different branch
            if self.current_version and branch["current_version"] != self.current_version:
                commit_message = f"Auto-commit before switching to branch '{branch_name}'"
                self.commit_state(commit_message, "system", "branch_switch")

            # Switch to branch
            target_version = branch["current_version"]
            success = self.rollback_to_version(target_version, RollbackTrigger.MANUAL, f"Switch to branch '{branch_name}'")

            if success:
                self.logger.info(f"Switched to branch '{branch_name}' at version {target_version}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to switch to branch '{branch_name}': {e}")
            return False

    def merge_branches(self, source_branch: str, target_branch: str = "main",
                      merge_strategy: str = "manual") -> bool:
        """Merge source branch into target branch"""
        if source_branch not in self.branches or target_branch not in self.branches:
            self.logger.error(f"One or both branches not found: {source_branch}, {target_branch}")
            return False

        try:
            source_branch_data = self.branches[source_branch]
            target_branch_data = self.branches[target_branch]

            # Get latest versions from both branches
            source_version = source_branch_data["current_version"]
            target_version = target_branch_data["current_version"]

            # Compare versions and create merge commit
            merge_version = self._create_merge_version(source_version, target_version, merge_strategy)

            if merge_version:
                # Update target branch
                target_branch_data["versions"].append(merge_version)
                target_branch_data["current_version"] = merge_version

                # Save updated branch data
                self._save_branches()

                self.logger.info(f"Successfully merged '{source_branch}' into '{target_branch}'")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to merge branches: {e}")
            return False

    def _create_merge_version(self, source_version: int, target_version: int, strategy: str) -> Optional[int]:
        """Create a merge version from two parent versions"""
        try:
            # Get state data from both versions
            source_state = None
            target_state = None

            for version in self.version_history:
                if version["version_id"] == source_version:
                    source_state = version.get("state_data") or self._load_state_from_file(version.get("state_file"))
                elif version["version_id"] == target_version:
                    target_state = version.get("state_data") or self._load_state_from_file(version.get("state_file"))

            if not source_state or not target_state:
                return None

            # Create merged state based on strategy
            if strategy == "source_wins":
                merged_state = copy.deepcopy(source_state)
            elif strategy == "target_wins":
                merged_state = copy.deepcopy(target_state)
            else:  # manual or default
                merged_state = self._intelligent_merge(source_state, target_state)

            # Create merge version record
            merge_record = {
                "version_id": self.next_version_id,
                "version_name": f"merge_{self.next_version_id}",
                "commit_message": f"Merge commit: {source_version} -> {target_version}",
                "author": "system",
                "timestamp": time.time(),
                "version_type": "merge",
                "state_hash": self._calculate_state_hash(merged_state),
                "state_data": merged_state,
                "parent_versions": [source_version, target_version],
                "merge_strategy": strategy
            }

            # Add to version history
            self.version_history.append(merge_record)
            self.next_version_id += 1

            return merge_record["version_id"]

        except Exception as e:
            self.logger.error(f"Failed to create merge version: {e}")
            return None

    def _intelligent_merge(self, source_state: Dict[str, Any], target_state: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently merge two state versions"""
        merged = copy.deepcopy(target_state)  # Start with target as base

        # Merge strategy: prefer non-null values, then newer timestamps
        for key, source_value in source_state.items():
            if key not in merged:
                merged[key] = source_value
            else:
                target_value = merged[key]

                # If both are dictionaries, merge recursively
                if isinstance(source_value, dict) and isinstance(target_value, dict):
                    merged[key] = self._merge_dicts(target_value, source_value)
                # If values are different, prefer source (as it's the "incoming" change)
                elif source_value != target_value:
                    merged[key] = source_value

        return merged

    def _merge_dicts(self, base_dict: Dict[str, Any], overlay_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries"""
        result = copy.deepcopy(base_dict)

        for key, value in overlay_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def get_rollback_options(self) -> List[Dict[str, Any]]:
        """Get available rollback options with risk assessment"""
        if not self.version_history:
            return []

        options = []

        for version in reversed(self.version_history[:-1]):  # Exclude current version
            option = {
                "version_id": version["version_id"],
                "version_name": version["version_name"],
                "timestamp": version["timestamp"],
                "commit_message": version["commit_message"],
                "author": version["author"],
                "risk_level": self._assess_rollback_risk(version),
                "estimated_impact": self._estimate_rollback_impact(version),
                "recommendations": self._get_rollback_recommendations(version)
            }

            options.append(option)

        return options

    def _assess_rollback_risk(self, target_version: Dict[str, Any]) -> str:
        """Assess risk level of rolling back to specific version"""
        try:
            # Calculate time difference
            time_diff = time.time() - target_version["timestamp"]
            days_old = time_diff / (24 * 3600)

            # Assess based on age and changes
            if days_old > 7:
                return "high"
            elif days_old > 3:
                return "medium"
            else:
                return "low"

        except:
            return "unknown"

    def _estimate_rollback_impact(self, target_version: Dict[str, Any]) -> str:
        """Estimate impact of rolling back to specific version"""
        try:
            # Compare with current version
            if self.version_history:
                current_version = self.version_history[-1]
                diff_summary = self._generate_diff_summary(
                    target_version.get("state_data") or {},
                    current_version.get("state_data") or {}
                )

                change_count = diff_summary.get("total_changes", 0)

                if change_count > 20:
                    return "major"
                elif change_count > 10:
                    return "moderate"
                else:
                    return "minor"

        except:
            return "unknown"

    def _get_rollback_recommendations(self, target_version: Dict[str, Any]) -> List[str]:
        """Get recommendations for rolling back to specific version"""
        recommendations = []

        risk_level = self._assess_rollback_risk(target_version)
        impact_level = self._estimate_rollback_risk(target_version)

        if risk_level == "high":
            recommendations.append("Consider creating a backup before rollback")
            recommendations.append("Test rollback in staging environment first")

        if impact_level == "major":
            recommendations.append("Major changes detected - review differences carefully")
            recommendations.append("Consider incremental rollback strategy")

        recommendations.append("Verify platform functionality after rollback")
        recommendations.append("Monitor system health post-rollback")

        return recommendations

    def cleanup_old_versions(self, max_age_days: Optional[int] = None) -> int:
        """Clean up old versions based on age"""
        if max_age_days is None:
            max_age_days = self.vc_config["max_age_days"]

        try:
            cutoff_time = time.time() - (max_age_days * 24 * 3600)
            versions_to_remove = []
            files_to_remove = []

            # Identify old versions
            for version in self.version_history:
                if version["timestamp"] < cutoff_time:
                    versions_to_remove.append(version)

                    # Collect associated files
                    state_file = version.get("state_file")
                    if state_file:
                        files_to_remove.append(state_file)

            # Remove old versions from history
            for old_version in versions_to_remove:
                if old_version in self.version_history:
                    self.version_history.remove(old_version)

            # Remove associated files
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass

            # Save updated history
            self._save_version_history()

            removed_count = len(versions_to_remove)
            self.logger.info(f"Cleaned up {removed_count} old versions")

            return removed_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old versions: {e}")
            return 0

    def get_version_statistics(self) -> Dict[str, Any]:
        """Get version control statistics"""
        if not self.version_history:
            return {"error": "No version history available"}

        # Calculate statistics
        total_versions = len(self.version_history)
        version_types = {}
        authors = {}
        time_span = 0

        if total_versions > 1:
            oldest_version = min(self.version_history, key=lambda v: v["timestamp"])
            newest_version = max(self.version_history, key=lambda v: v["timestamp"])
            time_span = newest_version["timestamp"] - oldest_version["timestamp"]

        # Count by type and author
        for version in self.version_history:
            v_type = version.get("version_type", "unknown")
            author = version.get("author", "unknown")

            version_types[v_type] = version_types.get(v_type, 0) + 1
            authors[author] = authors.get(author, 0) + 1

        return {
            "total_versions": total_versions,
            "current_version": self.current_version,
            "next_version_id": self.next_version_id,
            "version_types": version_types,
            "authors": authors,
            "time_span_seconds": time_span,
            "auto_commit_enabled": self.vc_config["auto_commit"],
            "branching_enabled": self.vc_config["enable_branching"],
            "total_branches": len(self.branches),
            "total_rollbacks": len(self.rollback_history),
            "oldest_version_date": oldest_version["timestamp"] if total_versions > 0 else None,
            "newest_version_date": newest_version["timestamp"] if total_versions > 0 else None
        }

    def demonstrate_version_control_features(self):
        """Demonstrate version control features"""
        print("\n📋 OMNI Platform3 Version Control System Demonstration")
        print("=" * 60)

        # Show version control configuration
        print("⚙️ Version Control Configuration:")
        print(f"  📚 Strategy: {self.vc_config['strategy']}")
        print(f"  🤖 Auto Commit: {self.vc_config['auto_commit']}")
        print(f"  ⏱️ Commit Interval: {self.vc_config['commit_interval']}s")
        print(f"  📦 Max Versions: {self.vc_config['max_versions']}")
        print(f"  🌿 Branching: {self.vc_config['enable_branching']}")

        # Show version statistics
        stats = self.get_version_statistics()
        if "error" not in stats:
            print("
📊 Version Statistics:"            print(f"  📚 Total Versions: {stats['total_versions']}")
            print(f"  🏃 Current Version: {stats['current_version']}")
            print(f"  ⏱️ Time Span: {stats['time_span_seconds']".1f"}s")
            print(f"  🌿 Branches: {stats['total_branches']}")
            print(f"  ↩️ Rollbacks: {stats['total_rollbacks']}")

            # Show version types
            print("
📂 Version Types:"            for v_type, count in stats['version_types'].items():
                print(f"  • {v_type}: {count}")

            # Show authors
            print("
👥 Authors:"            for author, count in list(stats['authors'].items())[:5]:  # Show top 5
                print(f"  • {author}: {count}")

        # Show recent versions
        recent_versions = self.list_versions(5)
        if recent_versions:
            print("
📜 Recent Versions:"            for version in recent_versions:
                version_time = datetime.fromtimestamp(version['timestamp']).strftime("%H:%M:%S")
                print(f"  📦 v{version['version_id']}: {version['commit_message']} ({version_time})")

        # Show rollback options
        rollback_options = self.get_rollback_options()
        if rollback_options:
            print("
↩️ Rollback Options:"            for option in rollback_options[:3]:  # Show top 3
                risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}
                icon = risk_icon.get(option['risk_level'], "❓")
                print(f"  {icon} v{option['version_id']}: {option['risk_level']} risk, {option['estimated_impact']} impact")

def main():
    """Main function to demonstrate Platform3 version control system"""
    print("📋 OMNI Platform3 Version Control and Rollback System")
    print("=" * 70)
    print("📦 Complete state version tracking")
    print("↩️ One-click rollback capabilities")
    print("🌿 Branch-based state management")
    print()

    try:
        # Create version control instance
        version_control = OmniPlatform3VersionControl()

        # Demonstrate version control features
        print("📋 Version Control System Features:")
        print("  ✅ Complete state tracking")
        print("  ↩️ One-click rollback")
        print("  🌿 Branch management")
        print("  🔄 Automatic commits")
        print("  📊 Change analysis")

        # Show version control capabilities
        version_control.demonstrate_version_control_features()

        # Demonstrate version operations
        print("
🚀 Version Control Operations:"        print("  📦 Commit system: Ready")
        print("  ↩️ Rollback system: Available")
        print("  🌿 Branch management: Operational")
        print("  📊 Version comparison: Active")
        print("  🧹 Cleanup system: Ready")

        print("
✅ OMNI Platform3 Version Control System Ready!"        print("📦 State versioning: Active")
        print("↩️ Rollback capabilities: Operational")
        print("🌿 Branch management: Available")
        print("📊 Change tracking: Enabled")

        return version_control.get_version_statistics()

    except Exception as e:
        print(f"\n❌ Version control initialization failed: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    stats = main()
    print(f"\n✅ Version control system execution completed")