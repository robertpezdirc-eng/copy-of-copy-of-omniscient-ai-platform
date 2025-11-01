#!/usr/bin/env python3
"""
Generate individual HTML pages for all 20 OMNI platform modules
"""

MODULES = [
    {"id": "sales", "name": "Prodaja", "icon": "📊", "description": "Spremljaj prihodke, trende, AI vpoglede", "price": 9.0, "category": "Business"},
    {"id": "customers", "name": "Stranke", "icon": "👥", "description": "CRM + engagement analiza", "price": 12.0, "category": "Business"},
    {"id": "ai-chat", "name": "AI Chat Bot", "icon": "💬", "description": "Notranji asistent za podatke", "price": 0.0, "category": "AI"},
    {"id": "inventory", "name": "Zaloga", "icon": "📦", "description": "Nadzor zalog, napoved povpraševanja", "price": 8.0, "category": "Operations"},
    {"id": "finance", "name": "Finance", "icon": "💰", "description": "AI analiza stroškov, prihodkov", "price": 10.0, "category": "Finance"},
    {"id": "planning", "name": "Planiranje", "icon": "📅", "description": "Pametno planiranje dela in resursov", "price": 7.0, "category": "Operations"},
    {"id": "seo", "name": "SEO Analitika", "icon": "🔍", "description": "Sledenje ključnim besedam", "price": 6.0, "category": "Marketing"},
    {"id": "marketing", "name": "Marketing", "icon": "📢", "description": "Analiza kampanj + predlogi", "price": 11.0, "category": "Marketing"},
    {"id": "performance", "name": "Performance", "icon": "⚡", "description": "Hitrost sistema, uptime", "price": 5.0, "category": "Tech"},
    {"id": "web-analytics", "name": "Web Analytics", "icon": "🌐", "description": "Obisk, bounce rate, zemljevid", "price": 6.0, "category": "Analytics"},
    {"id": "ai-forecast", "name": "AI Forecast", "icon": "🧮", "description": "Napoved prodaje in trendov", "price": 12.0, "category": "AI"},
    {"id": "research", "name": "Omni Research", "icon": "🧠", "description": "Analize trga in konkurence", "price": 14.0, "category": "Analytics"},
    {"id": "security", "name": "Varnostni center", "icon": "🔐", "description": "Prijave, grožnje, MFA nadzor", "price": 7.0, "category": "Security"},
    {"id": "projects", "name": "Projektni modul", "icon": "🏗️", "description": "Nadzor projektov, Gantt AI", "price": 10.0, "category": "Operations"},
    {"id": "suppliers", "name": "Dobavitelji", "icon": "📦", "description": "Nadzor cen, AI predlog menjav", "price": 9.0, "category": "Business"},
    {"id": "bi-analytics", "name": "BI Analytics Pro", "icon": "📈", "description": "Napredna poslovna inteligenca", "price": 15.0, "category": "Analytics"},
    {"id": "reports", "name": "Poročila", "icon": "🧾", "description": "PDF, Excel, e-mail reporti", "price": 5.0, "category": "Operations"},
    {"id": "kpi", "name": "Cilji in KPI", "icon": "🎯", "description": "Postavljanje ciljev z AI spremljanjem", "price": 6.0, "category": "Analytics"},
    {"id": "data-science", "name": "Data Science Lab", "icon": "🧬", "description": "Analize modelov in LLM testiranja", "price": 18.0, "category": "AI"},
    {"id": "api-management", "name": "API Management", "icon": "🔗", "description": "Pregled povezav in kvot", "price": 4.0, "category": "Tech"},
]

def generate_module_html(module):
    """Generate HTML page for a single module"""
    price_text = "Brezplačno" if module["price"] == 0 else f"€{module['price']}/mesec"
    
    html = f'''<!DOCTYPE html>
<html lang="sl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module["name"]} - OMNI Intelligence Platform</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="../env.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .module-title {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .module-icon {{
            font-size: 48px;
        }}
        .module-info h1 {{
            font-size: 32px;
            color: #333;
            margin-bottom: 5px;
        }}
        .module-category {{
            color: #667eea;
            font-size: 14px;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .module-price {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 24px;
            font-weight: bold;
        }}
        .module-description {{
            font-size: 18px;
            color: #666;
            margin-bottom: 20px;
        }}
        .actions {{
            display: flex;
            gap: 15px;
        }}
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        .btn-secondary {{
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
        }}
        .btn-secondary:hover {{
            background: #667eea;
            color: white;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            font-size: 14px;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .stat-change {{
            font-size: 14px;
            color: #52c41a;
        }}
        .stat-change.negative {{
            color: #f5222d;
        }}
        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .chart-container h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: white;
            text-decoration: none;
            font-size: 16px;
            margin-bottom: 20px;
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 8px;
            transition: all 0.3s;
        }}
        .back-link:hover {{
            background: rgba(255,255,255,0.3);
        }}
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .feature-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        .feature-card h4 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        .feature-card p {{
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="../omni-dashboard.html" class="back-link">
            ← Nazaj na Dashboard
        </a>
        
        <div class="header">
            <div class="header-top">
                <div class="module-title">
                    <div class="module-icon">{module["icon"]}</div>
                    <div class="module-info">
                        <h1>{module["name"]}</h1>
                        <div class="module-category">{module["category"]}</div>
                    </div>
                </div>
                <div class="module-price">{price_text}</div>
            </div>
            <div class="module-description">
                {module["description"]}
            </div>
            <div class="actions">
                <button class="btn btn-primary" onclick="activateModule()">Aktiviraj modul</button>
                <button class="btn btn-secondary" onclick="showDemo()">Oglej si demo</button>
                <button class="btn btn-secondary" onclick="exportData()">Izvozi podatke</button>
            </div>
        </div>

        <div class="dashboard-grid" id="statsGrid">
            <!-- Stats will be populated by JavaScript -->
        </div>

        <div class="chart-container">
            <h2>📈 Trend analiza</h2>
            <canvas id="trendChart" height="80"></canvas>
        </div>

        <div class="chart-container">
            <h2>✨ Ključne funkcije</h2>
            <div class="features-grid" id="featuresGrid">
                <!-- Features will be populated by JavaScript -->
            </div>
        </div>
    </div>

    <script>
        const MODULE_ID = '{module["id"]}';
        const API_BASE_URL = window.ENV?.API_BASE_URL || 'http://localhost:8080';

        // Load module data
        async function loadModuleData() {{
            try {{
                const response = await fetch(`${{API_BASE_URL}}/api/modules/${{MODULE_ID}}/data`);
                const data = await response.json();
                displayStats(data);
                displayChart(data);
            }} catch (error) {{
                console.error('Error loading module data:', error);
                displayDemoData();
            }}
        }}

        function displayStats(data) {{
            const statsGrid = document.getElementById('statsGrid');
            const stats = generateStatsForModule(data);
            
            statsGrid.innerHTML = stats.map(stat => `
                <div class="stat-card">
                    <h3>${{stat.label}}</h3>
                    <div class="stat-value">${{stat.value}}</div>
                    <div class="stat-change ${{stat.change < 0 ? 'negative' : ''}}">
                        ${{stat.change > 0 ? '↑' : '↓'}} ${{Math.abs(stat.change)}}% vs prošli mesec
                    </div>
                </div>
            `).join('');
        }}

        function generateStatsForModule(data) {{
            // Generate appropriate stats based on module type
            return [
                {{ label: 'Skupna vrednost', value: data.revenue || Math.round(Math.random() * 50000), change: Math.round((Math.random() - 0.5) * 30) }},
                {{ label: 'Rast', value: `${{data.growth || Math.round(Math.random() * 25)}}%`, change: Math.round((Math.random() - 0.5) * 20) }},
                {{ label: 'Transakcije', value: data.transactions || Math.round(Math.random() * 1000), change: Math.round((Math.random() - 0.5) * 15) }},
                {{ label: 'AI Score', value: Math.round(Math.random() * 100), change: Math.round((Math.random() - 0.5) * 10) }}
            ];
        }}

        function displayChart(data) {{
            const ctx = document.getElementById('trendChart').getContext('2d');
            const chartData = data.forecast || Array.from({{length: 7}}, () => Math.round(Math.random() * 40000));
            
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: ['Pon', 'Tor', 'Sre', 'Čet', 'Pet', 'Sob', 'Ned'],
                    datasets: [{{
                        label: 'Napoved',
                        data: chartData,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: true }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }}
            }});
        }}

        function displayDemoData() {{
            displayStats({{}});
            displayChart({{}});
        }}

        function activateModule() {{
            if (confirm('Aktivirati modul {module["name"]}?')) {{
                alert('Modul uspešno aktiviran! 🎉');
            }}
        }}

        function showDemo() {{
            alert('Demo način - prikazani so vzorčni podatki');
        }}

        function exportData() {{
            alert('Podatki izvoženi! 📊');
        }}

        // Load features
        const featuresGrid = document.getElementById('featuresGrid');
        featuresGrid.innerHTML = `
            <div class="feature-card">
                <h4>🤖 AI Analiza</h4>
                <p>Inteligentna analiza podatkov z AI priporočili</p>
            </div>
            <div class="feature-card">
                <h4>📊 Vizualizacije</h4>
                <p>Interaktivni grafi in dashboardi</p>
            </div>
            <div class="feature-card">
                <h4>🔔 Opozorila</h4>
                <p>Avtomatska obvestila o pomembnih dogodkih</p>
            </div>
            <div class="feature-card">
                <h4>📈 Napovedi</h4>
                <p>AI napovedi trendov in priložnosti</p>
            </div>
        `;

        // Initialize
        loadModuleData();
    </script>
</body>
</html>'''
    return html

def main():
    import os
    
    # Create modules directory if it doesn't exist
    output_dir = '../frontend/modules'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate HTML for each module
    for module in MODULES:
        filename = f"{module['id']}.html"
        filepath = os.path.join(output_dir, filename)
        
        html_content = generate_module_html(module)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Created: {filename}")
    
    print(f"\n🎉 Successfully generated {len(MODULES)} module pages!")
    print(f"📁 Location: {output_dir}")

if __name__ == "__main__":
    main()
