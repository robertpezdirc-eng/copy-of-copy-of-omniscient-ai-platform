#!/usr/bin/env python3
"""
OMNI Platform Coordinator

This module provides the main Coordinator class that serves as the entry point
for the OMNI platform in production mode.

Author: OMNI Platform
Version: 1.0.0
"""

from typing import Dict, Any
from omni_platform_master_coordinator import OmniPlatformMasterCoordinator

class Coordinator:
    """Main coordinator class for OMNI platform"""

    def __init__(self, mode: str = "production"):
        """
        Initialize the OMNI Platform Coordinator

        Args:
            mode (str): Operating mode - "production", "development", or "testing"
        """
        self.mode = mode
        self.master_coordinator = OmniPlatformMasterCoordinator()

        # Initialize platform if in production mode
        if mode == "production":
            self._initialize_production_mode()

    def _initialize_production_mode(self):
        """Initialize platform in production mode"""
        print(f"[OMNI] Initializing OMNI Platform Coordinator in {self.mode} mode")
        success = self.master_coordinator.initialize_platform()
        if not success:
            print("[WARNING] Platform initialization had some issues but continuing...")

    def get_platform_status(self) -> Dict[str, Any]:
        """
        Get comprehensive platform status

        Returns:
            Dict containing platform status information
        """
        return self.master_coordinator.get_platform_status()

    def execute_platform_operation(self, operation: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a platform-wide operation

        Args:
            operation (str): Operation to execute
            parameters (Dict): Optional parameters for the operation

        Returns:
            Dict containing operation results
        """
        if parameters is None:
            parameters = {}

        return self.master_coordinator.execute_platform_operation(operation, parameters)

    def demonstrate_capabilities(self):
        """Demonstrate platform capabilities"""
        return self.master_coordinator.demonstrate_platform_capabilities()

# Production-ready coordinator instance
omni_coordinator = Coordinator(mode="production")