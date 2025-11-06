"""
Dashboard Builder Service - Uses Ollama to generate dashboards
Automatically builds 20+ dashboards based on instructions and GitHub code
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from .ollama_service import get_ollama_service

logger = logging.getLogger(__name__)


class DashboardBuilderService:
    """Service for building dashboards using Ollama AI."""

    def __init__(self):
        self.ollama = get_ollama_service()
        self.github_repo = "robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform"
        self.cloud_run_base = "https://omni-ultra-backend-661612368188.europe-west1.run.app"
        
        # Dashboard types to build
        self.dashboard_types = [
            {
                "name": "Revenue Analytics",
                "description": "Real-time revenue tracking with charts and KPIs",
                "endpoints": ["/api/v1/billing/revenue", "/api/v1/analytics/revenue"],
                "priority": 1
            },
            {
                "name": "User Analytics",
                "description": "User engagement metrics and cohort analysis",
                "endpoints": ["/api/v1/users/stats", "/api/v1/analytics/users"],
                "priority": 1
            },
            {
                "name": "AI Performance",
                "description": "ML model performance and inference metrics",
                "endpoints": ["/api/v1/ai/stats", "/api/v1/analytics/ai"],
                "priority": 1
            },
            {
                "name": "Affiliate Tracking",
                "description": "Multi-tier affiliate program analytics",
                "endpoints": ["/api/v1/affiliate/stats", "/api/v1/affiliate/performance"],
                "priority": 2
            },
            {
                "name": "Marketplace Overview",
                "description": "API marketplace sales and usage",
                "endpoints": ["/api/v1/marketplace/stats", "/api/v1/marketplace/apis"],
                "priority": 2
            },
            {
                "name": "Churn Prediction",
                "description": "ML-powered churn risk dashboard",
                "endpoints": ["/api/v1/churn/predict", "/api/v1/analytics/churn"],
                "priority": 2
            },
            {
                "name": "Forecast Dashboard",
                "description": "Revenue and user growth forecasting",
                "endpoints": ["/api/v1/forecast/revenue", "/api/v1/forecast/users"],
                "priority": 2
            },
            {
                "name": "Sentiment Analysis",
                "description": "Customer sentiment from support tickets",
                "endpoints": ["/api/v1/sentiment/analyze", "/api/v1/analytics/sentiment"],
                "priority": 2
            },
            {
                "name": "Anomaly Detection",
                "description": "Real-time anomaly alerts and trends",
                "endpoints": ["/api/v1/anomaly/detect", "/api/v1/analytics/anomalies"],
                "priority": 2
            },
            {
                "name": "Payment Gateway",
                "description": "Stripe, PayPal, Crypto transaction monitoring",
                "endpoints": ["/api/v1/stripe/stats", "/api/v1/paypal/stats", "/api/v1/crypto/stats"],
                "priority": 2
            },
            {
                "name": "Subscription Metrics",
                "description": "Subscription lifecycle and MRR tracking",
                "endpoints": ["/api/v1/subscriptions/stats", "/api/v1/billing/mrr"],
                "priority": 1
            },
            {
                "name": "API Usage Dashboard",
                "description": "Rate limiting, quotas, and endpoint usage",
                "endpoints": ["/api/v1/usage/stats", "/api/v1/analytics/api-calls"],
                "priority": 2
            },
            {
                "name": "Growth Engine",
                "description": "Viral coefficients and referral tracking",
                "endpoints": ["/api/v1/growth/stats", "/api/v1/growth/viral-metrics"],
                "priority": 2
            },
            {
                "name": "Gamification Dashboard",
                "description": "User points, badges, and leaderboards",
                "endpoints": ["/api/v1/gamification/stats", "/api/v1/gamification/leaderboard"],
                "priority": 3
            },
            {
                "name": "Recommendation Engine",
                "description": "Product recommendation performance",
                "endpoints": ["/api/v1/recommendations/stats", "/api/v1/recommendations/performance"],
                "priority": 3
            },
            {
                "name": "Neo4j Graph Insights",
                "description": "Knowledge graph and relationship analytics",
                "endpoints": ["/api/v1/neo4j/stats", "/api/v1/analytics/graph"],
                "priority": 3
            },
            {
                "name": "Swarm Intelligence",
                "description": "Multi-agent coordination and task distribution",
                "endpoints": ["/api/v1/swarm/stats", "/api/v1/agents/coordination"],
                "priority": 3
            },
            {
                "name": "AGI Dashboard",
                "description": "Advanced AI reasoning and planning metrics",
                "endpoints": ["/api/v1/agi/stats", "/api/v1/agi/planning"],
                "priority": 3
            },
            {
                "name": "System Health",
                "description": "Infrastructure monitoring and alerts",
                "endpoints": ["/api/health", "/api/v1/system/metrics"],
                "priority": 1
            },
            {
                "name": "Security & Auth",
                "description": "Authentication, authorization, and security events",
                "endpoints": ["/api/v1/auth/stats", "/api/v1/security/events"],
                "priority": 1
            }
        ]

    async def build_dashboard(self, dashboard_type: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a single dashboard using Ollama.
        
        Args:
            dashboard_type: Dashboard configuration
            
        Returns:
            Dashboard code and metadata
        """
        if not self.ollama.enabled:
            logger.warning("Ollama not enabled, returning template")
            return self._get_template_dashboard(dashboard_type)

        # Create prompt for Ollama
        prompt = self._create_dashboard_prompt(dashboard_type)
        
        try:
            # Generate dashboard using Ollama
            result = await self.ollama.generate(
                prompt=prompt,
                model=self.ollama.default_model,
                temperature=0.3,  # Lower temperature for more consistent code
                max_tokens=4000
            )
            
            # Extract code from response
            dashboard_code = self._extract_code(result["reply"])
            
            return {
                "name": dashboard_type["name"],
                "description": dashboard_type["description"],
                "code": dashboard_code,
                "endpoints": dashboard_type["endpoints"],
                "generated_at": datetime.utcnow().isoformat(),
                "model": result["model"],
                "priority": dashboard_type.get("priority", 3)
            }
            
        except Exception as e:
            logger.error(f"Error building dashboard {dashboard_type['name']}: {e}")
            return self._get_template_dashboard(dashboard_type)

    def _create_dashboard_prompt(self, dashboard_type: Dict[str, Any]) -> str:
        """Create a prompt for Ollama to generate dashboard code."""
        return f"""Generate a React TypeScript dashboard component for: {dashboard_type['name']}

Description: {dashboard_type['description']}

Requirements:
1. Use React hooks (useState, useEffect)
2. Fetch data from these endpoints: {', '.join(dashboard_type['endpoints'])}
3. Use Recharts for visualizations (LineChart, BarChart, PieChart)
4. Include real-time updates with WebSocket if applicable
5. Show loading states and error handling
6. Use Tailwind CSS for styling
7. Include key metrics cards at the top
8. Make it responsive for mobile and desktop
9. Add export to PDF/CSV functionality
10. Include date range filters

Base URL: {self.cloud_run_base}

Generate ONLY the React component code, properly formatted with TypeScript types.
Start with: import React, {{ useState, useEffect }} from 'react';"""

    def _extract_code(self, ollama_reply: str) -> str:
        """Extract code block from Ollama's response."""
        # Try to find code between ```typescript or ```tsx markers
        import re
        
        patterns = [
            r'```(?:typescript|tsx|javascript|jsx)\n(.*?)\n```',
            r'```\n(.*?)\n```',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, ollama_reply, re.DOTALL)
            if matches:
                return matches[0].strip()
        
        # If no code blocks found, return the whole response
        return ollama_reply.strip()

    def _get_template_dashboard(self, dashboard_type: Dict[str, Any]) -> Dict[str, Any]:
        """Return a template dashboard when Ollama is not available."""
        template_code = f"""import React, {{ useState, useEffect }} from 'react';
import {{ LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer }} from 'recharts';

interface {dashboard_type['name'].replace(' ', '')}Props {{
  refreshInterval?: number;
}}

export const {dashboard_type['name'].replace(' ', '')}Dashboard: React.FC<{dashboard_type['name'].replace(' ', '')}Props> = ({{ refreshInterval = 30000 }}) => {{
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {{
    const fetchData = async () => {{
      try {{
        setLoading(true);
        const response = await fetch('{self.cloud_run_base}{dashboard_type['endpoints'][0]}');
        if (!response.ok) throw new Error('Failed to fetch data');
        const result = await response.json();
        setData(result);
        setError(null);
      }} catch (err) {{
        setError(err instanceof Error ? err.message : 'Unknown error');
      }} finally {{
        setLoading(false);
      }}
    }};

    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }}, [refreshInterval]);

  if (loading) return <div className="flex items-center justify-center h-64">Loading...</div>;
  if (error) return <div className="text-red-500 p-4">Error: {{error}}</div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">{dashboard_type['name']}</h1>
      <p className="text-gray-600">{dashboard_type['description']}</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500">Metric 1</h3>
          <p className="text-2xl font-bold">{{data?.metric1 || 'N/A'}}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500">Metric 2</h3>
          <p className="text-2xl font-bold">{{data?.metric2 || 'N/A'}}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500">Metric 3</h3>
          <p className="text-2xl font-bold">{{data?.metric3 || 'N/A'}}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={{data?.chartData || []}}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#8884d8" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}};"""

        return {
            "name": dashboard_type["name"],
            "description": dashboard_type["description"],
            "code": template_code,
            "endpoints": dashboard_type["endpoints"],
            "generated_at": datetime.utcnow().isoformat(),
            "model": "template",
            "priority": dashboard_type.get("priority", 3)
        }

    async def build_all_dashboards(self, priority_filter: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Build all dashboards or filtered by priority.
        
        Args:
            priority_filter: If set, only build dashboards with this priority (1=high, 2=medium, 3=low)
            
        Returns:
            List of generated dashboards
        """
        dashboards_to_build = self.dashboard_types
        
        if priority_filter:
            dashboards_to_build = [d for d in self.dashboard_types if d.get("priority") == priority_filter]
        
        logger.info(f"Building {len(dashboards_to_build)} dashboards...")
        
        results = []
        for dashboard_type in dashboards_to_build:
            logger.info(f"Building: {dashboard_type['name']}")
            try:
                dashboard = await self.build_dashboard(dashboard_type)
                results.append(dashboard)
                logger.info(f"✅ Built: {dashboard_type['name']}")
            except Exception as e:
                logger.error(f"❌ Failed: {dashboard_type['name']} - {e}")
        
        return results

    async def save_dashboards(self, dashboards: List[Dict[str, Any]], output_dir: str = "dashboards/generated"):
        """Save generated dashboards to files."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save individual dashboard files
        for dashboard in dashboards:
            filename = dashboard["name"].lower().replace(" ", "_") + ".tsx"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(dashboard["code"])
            
            logger.info(f"Saved: {filepath}")
        
        # Save manifest
        manifest = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_dashboards": len(dashboards),
            "dashboards": [
                {
                    "name": d["name"],
                    "file": d["name"].lower().replace(" ", "_") + ".tsx",
                    "priority": d["priority"],
                    "endpoints": d["endpoints"]
                }
                for d in dashboards
            ]
        }
        
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Saved manifest: {manifest_path}")


# Singleton instance
_dashboard_builder: Optional[DashboardBuilderService] = None


def get_dashboard_builder() -> DashboardBuilderService:
    """Get or create dashboard builder singleton."""
    global _dashboard_builder
    if _dashboard_builder is None:
        _dashboard_builder = DashboardBuilderService()
    return _dashboard_builder
