"""
Service Layer - Business Logic

Note:
- Avoid eager imports in this package to prevent optional/heavy dependencies
    from being required during test collection or when importing unrelated submodules.
- Import concrete services explicitly, e.g.:
        from services.auth import AuthService
        from services.advanced_ai.ab_testing import ABTestingService
"""

# Intentionally empty to keep package lightweight. Explicit submodule imports are recommended.

__all__: list[str] = []
