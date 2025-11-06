"""
White-label Platform Service
Custom branding per tenant - logos, colors, domains, themes
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class WhitelabelService:
    """Service for managing white-label branding per tenant"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.branding_configs = {}
        self.custom_domains = {}
        self.themes = {}
        
    async def create_branding(self, tenant_id: str, branding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create custom branding configuration for tenant"""
        branding_id = f"brand_{tenant_id}_{int(datetime.now().timestamp())}"
        
        branding = {
            "id": branding_id,
            "tenant_id": tenant_id,
            "company_name": branding_data.get("company_name", ""),
            "logo_url": branding_data.get("logo_url", ""),
            "logo_dark_url": branding_data.get("logo_dark_url", ""),
            "favicon_url": branding_data.get("favicon_url", ""),
            "primary_color": branding_data.get("primary_color", "#1976d2"),
            "secondary_color": branding_data.get("secondary_color", "#dc004e"),
            "accent_color": branding_data.get("accent_color", "#f50057"),
            "font_family": branding_data.get("font_family", "Roboto"),
            "custom_css": branding_data.get("custom_css", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.branding_configs[branding_id] = branding
        return branding
    
    async def get_branding(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get branding configuration for tenant"""
        for branding_id, branding in self.branding_configs.items():
            if branding["tenant_id"] == tenant_id:
                return branding
        return None
    
    async def update_branding(self, tenant_id: str, branding_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update branding configuration"""
        branding = await self.get_branding(tenant_id)
        if not branding:
            return None
        
        # Update fields
        for key, value in branding_data.items():
            if key in branding and key not in ["id", "tenant_id", "created_at"]:
                branding[key] = value
        
        branding["updated_at"] = datetime.now().isoformat()
        return branding
    
    async def create_theme(self, tenant_id: str, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create custom theme for tenant"""
        theme_id = f"theme_{tenant_id}_{int(datetime.now().timestamp())}"
        
        theme = {
            "id": theme_id,
            "tenant_id": tenant_id,
            "name": theme_data.get("name", "Default Theme"),
            "mode": theme_data.get("mode", "light"),  # light or dark
            "colors": {
                "background": theme_data.get("background", "#ffffff"),
                "surface": theme_data.get("surface", "#f5f5f5"),
                "text_primary": theme_data.get("text_primary", "#000000"),
                "text_secondary": theme_data.get("text_secondary", "#666666"),
                "border": theme_data.get("border", "#e0e0e0"),
                "success": theme_data.get("success", "#4caf50"),
                "warning": theme_data.get("warning", "#ff9800"),
                "error": theme_data.get("error", "#f44336"),
                "info": theme_data.get("info", "#2196f3")
            },
            "typography": {
                "font_family": theme_data.get("font_family", "Roboto"),
                "heading_font": theme_data.get("heading_font", "Roboto"),
                "body_font": theme_data.get("body_font", "Roboto")
            },
            "created_at": datetime.now().isoformat()
        }
        
        self.themes[theme_id] = theme
        return theme
    
    async def get_theme(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get theme for tenant"""
        for theme_id, theme in self.themes.items():
            if theme["tenant_id"] == tenant_id:
                return theme
        return None
    
    async def add_custom_domain(self, tenant_id: str, domain: str, ssl_cert: Optional[str] = None) -> Dict[str, Any]:
        """Add custom domain for tenant"""
        domain_id = f"domain_{tenant_id}_{int(datetime.now().timestamp())}"
        
        domain_config = {
            "id": domain_id,
            "tenant_id": tenant_id,
            "domain": domain,
            "ssl_cert": ssl_cert,
            "verified": False,
            "dns_record": f"CNAME {domain} -> app.omniscient.ai",
            "created_at": datetime.now().isoformat(),
            "verified_at": None
        }
        
        self.custom_domains[domain_id] = domain_config
        return domain_config
    
    async def verify_domain(self, domain_id: str) -> bool:
        """Verify custom domain DNS configuration"""
        if domain_id in self.custom_domains:
            # In production, check DNS records
            self.custom_domains[domain_id]["verified"] = True
            self.custom_domains[domain_id]["verified_at"] = datetime.now().isoformat()
            return True
        return False
    
    async def get_domains(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all custom domains for tenant"""
        return [
            domain for domain_id, domain in self.custom_domains.items()
            if domain["tenant_id"] == tenant_id
        ]
    
    async def preview_branding(self, tenant_id: str) -> Dict[str, Any]:
        """Get preview of tenant branding"""
        branding = await self.get_branding(tenant_id)
        theme = await self.get_theme(tenant_id)
        domains = await self.get_domains(tenant_id)
        
        return {
            "branding": branding,
            "theme": theme,
            "domains": domains,
            "preview_url": f"https://preview.omniscient.ai/{tenant_id}"
        }
    
    async def get_assets(self, tenant_id: str) -> Dict[str, Any]:
        """Get all branding assets for tenant"""
        branding = await self.get_branding(tenant_id)
        if not branding:
            return {}
        
        return {
            "logo": branding.get("logo_url"),
            "logo_dark": branding.get("logo_dark_url"),
            "favicon": branding.get("favicon_url"),
            "colors": {
                "primary": branding.get("primary_color"),
                "secondary": branding.get("secondary_color"),
                "accent": branding.get("accent_color")
            }
        }
