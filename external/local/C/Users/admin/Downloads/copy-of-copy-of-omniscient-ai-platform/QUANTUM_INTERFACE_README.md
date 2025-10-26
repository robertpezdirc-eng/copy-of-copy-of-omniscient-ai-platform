# 🧠 OMNI Quantum AI Interface

## Overview

The **OMNI Quantum AI Interface** provides a clean, modular interface to Google Gemini AI through the OMNI platform backend. This system enables frontend applications to easily access advanced AI capabilities organized into specialized "quantum modules" for different use cases.

## 🚀 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │───▶│  OMNI Backend    │───▶│  Google Gemini  │
│  (React/Vue)    │    │  (quantum.py)    │    │  (Vertex AI)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Quantum Cache   │
                       │  & Performance   │
                       └──────────────────┘
```

## 📦 Components

### 1. **quantum.py** - Main Interface Module
- Clean API functions for different quantum modules
- Automatic caching and performance optimization
- Error handling and fallback mechanisms
- Integration with OMNI backend

### 2. **quantum_api_endpoint.py** - Backend API
- Flask-based REST API server
- Request validation and security
- Module routing and response formatting
- Performance monitoring

### 3. **quantum_frontend_integration.jsx** - Frontend Component
- React component for quantum module selection
- Real-time result display
- Performance metrics visualization
- Responsive design

## 🎯 Quantum Modules

### 🎮 **Quantum Gaming**
```python
from quantum import quantum_gaming_idea, quantum_game_mechanics

# Generate game ideas
game_idea = quantum_gaming_idea("trampolin", "otroke", "aktivna")

# Generate game mechanics
mechanics = quantum_game_mechanics("Robot, ki se nauči čustev")
```

**Functions:**
- `quantum_gaming_idea(theme, age_group, game_type)` - Generate game concepts
- `quantum_game_mechanics(base_concept)` - Create detailed game mechanics

### 🏔️ **Quantum Tourism**
```python
from quantum import quantum_tourism_idea, quantum_cultural_experience

# Generate travel plans
travel_plan = quantum_tourism_idea("Bled", "weekend", "medium")

# Generate cultural experiences
cultural_exp = quantum_cultural_experience("Ljubljana", "history")
```

**Functions:**
- `quantum_tourism_idea(location, duration, budget)` - Create travel itineraries
- `quantum_cultural_experience(location, interest)` - Cultural experience recommendations

### 📚 **Quantum Education**
```python
from quantum import quantum_educational_content, quantum_learning_path

# Generate lesson plans
lesson = quantum_educational_content("Python programiranje", "beginner", "lesson_plan")

# Generate learning paths
learning_path = quantum_learning_path("Machine Learning", "3_months")
```

**Functions:**
- `quantum_educational_content(topic, level, format_type)` - Educational materials
- `quantum_learning_path(skill, timeframe)` - Personalized learning plans

### 💼 **Quantum Business**
```python
from quantum import quantum_business_idea, quantum_market_analysis

# Generate business ideas
business_idea = quantum_business_idea("tehnologija", "pomanjkanje inovativnih rešitev")

# Generate market analysis
market_analysis = quantum_market_analysis("AI aplikacija", "slovenia")
```

**Functions:**
- `quantum_business_idea(industry, problem)` - Business concept generation
- `quantum_market_analysis(product, market)` - Market research and analysis

### 🎨 **Quantum Creative**
```python
from quantum import quantum_storytelling, quantum_poetry

# Generate stories
story = quantum_storytelling("Robot, ki odkrije čustva", "sci-fi", "short")

# Generate poetry
poem = quantum_poetry("Ljubezen", "free_verse", "slovenian")
```

**Functions:**
- `quantum_storytelling(prompt, genre, length)` - Creative story generation
- `quantum_poetry(theme, style, language)` - Poetry and artistic content

### 🏃 **Quantum Health**
```python
from quantum import quantum_wellness_plan, quantum_nutrition_guide

# Generate wellness plans
wellness_plan = quantum_wellness_plan("izguba teže in več energije", "30_days")

# Generate nutrition guides
nutrition_guide = quantum_nutrition_guide("mediterranean", 2000, "vegetarian")
```

**Functions:**
- `quantum_wellness_plan(goals, timeframe, fitness_level)` - Health and fitness plans
- `quantum_nutrition_guide(diet_type, calories, preferences)` - Nutrition guidance

### 💻 **Quantum Technology**
```python
from quantum import quantum_code_generation, quantum_system_architecture

# Generate code
code = quantum_code_generation("Python", "kalkulator za BMI z validacijo")

# Generate system architecture
architecture = quantum_system_architecture("E-commerce platform", ["scalability", "security"])
```

**Functions:**
- `quantum_code_generation(language, specification, complexity)` - Code generation
- `quantum_system_architecture(description, requirements)` - System design

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements-google-quantum.txt
```

### 2. **Start the Quantum API Server**
```bash
python quantum_api_endpoint.py
```

The server will start on `http://127.0.0.1:8002`

### 3. **Use Quantum Interface in Python**
```python
from quantum import quantum_gaming_idea, quantum_tourism_idea

# Generate a game idea
game_idea = quantum_gaming_idea("space exploration", "teenagers", "adventure")
print(game_idea)

# Generate a travel plan
travel_plan = quantum_tourism_idea("Tokyo", "week", "high")
print(travel_plan)
```

### 4. **Integrate with Frontend**
```jsx
import { QuantumPlayground } from './quantum_frontend_integration.jsx';

// Use in your React app
function App() {
    return (
        <div>
            <QuantumPlayground />
        </div>
    );
}
```

## 🔧 Configuration

### Environment Variables

```bash
# OMNI Backend API endpoint
export OMNI_API_BASE="http://127.0.0.1:8002"

# API Key for authentication (optional)
export QUANTUM_API_KEY="your-api-key-here"

# Enable API key requirement
export REQUIRE_API_KEY="true"

# Allowed origins for CORS
export ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

### API Configuration

```python
from quantum import configure_quantum_api, set_quantum_model

# Configure API endpoint
configure_quantum_api("http://your-omni-backend:8002", timeout=60)

# Set default model
set_quantum_model("gemini-1.5-pro")
```

## 📡 API Endpoints

### GET `/api/quantum/status`
Get quantum AI interface status and available modules.

**Response:**
```json
{
    "ok": true,
    "status": {
        "api_base": "http://127.0.0.1:8002",
        "default_model": "gemini-1.5-flash-8b",
        "cache_enabled": true,
        "cache_size": 150,
        "available_modules": ["quantum_gaming", "quantum_tourism", ...]
    }
}
```

### POST `/api/quantum/query`
Submit quantum AI query.

**Request:**
```json
{
    "module": "quantum_gaming",
    "prompt": "Ustvari idejo za igro na trampolinu",
    "model": "gemini-1.5-pro",
    "options": {
        "age_group": "otroke",
        "game_type": "aktivna"
    }
}
```

**Response:**
```json
{
    "ok": true,
    "module": "quantum_gaming",
    "model": "gemini-1.5-pro",
    "reply": "Generated game idea content...",
    "execution_time": 2.34,
    "timestamp": "2025-01-19T17:20:00.000Z"
}
```

### GET `/api/quantum/modules`
List all available quantum modules.

**Response:**
```json
{
    "ok": true,
    "modules": {
        "quantum_gaming": {
            "name": "Quantum Gaming",
            "description": "Generate innovative game ideas and mechanics",
            "functions": ["quantum_gaming_idea", "quantum_game_mechanics"],
            "models": ["gemini-1.5-pro", "gemini-1.5-flash-8b"],
            "category": "entertainment"
        }
    }
}
```

## 🎨 Frontend Integration

### React Component Usage

```jsx
import React, { useState } from 'react';

function QuantumGameGenerator() {
    const [gameIdea, setGameIdea] = useState('');
    const [loading, setLoading] = useState(false);

    const generateGame = async (theme) => {
        setLoading(true);
        try {
            const response = await fetch('/api/quantum/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    module: 'quantum_gaming',
                    prompt: theme,
                    model: 'gemini-1.5-pro'
                })
            });

            const data = await response.json();
            if (data.ok) {
                setGameIdea(data.reply);
            }
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button onClick={() => generateGame('space adventure')}>
                Generate Space Game
            </button>
            {loading && <p>Generating...</p>}
            {gameIdea && <div>{gameIdea}</div>}
        </div>
    );
}
```

### Vue.js Integration

```vue
<template>
    <div class="quantum-interface">
        <select v-model="selectedModule">
            <option value="quantum_gaming">Gaming</option>
            <option value="quantum_tourism">Tourism</option>
        </select>

        <textarea v-model="prompt" placeholder="Enter your prompt..."></textarea>

        <button @click="generateContent" :disabled="loading">
            {{ loading ? 'Generating...' : 'Generate' }}
        </button>

        <div v-if="result" class="result">
            {{ result }}
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            selectedModule: 'quantum_gaming',
            prompt: '',
            result: '',
            loading: false
        };
    },
    methods: {
        async generateContent() {
            this.loading = true;
            try {
                const response = await fetch('/api/quantum/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        module: this.selectedModule,
                        prompt: this.prompt,
                        model: 'gemini-1.5-pro'
                    })
                });

                const data = await response.json();
                if (data.ok) {
                    this.result = data.reply;
                }
            } catch (error) {
                console.error('Error:', error);
            } finally {
                this.loading = false;
            }
        }
    }
};
</script>
```

## 🔧 Advanced Usage

### Custom Module Creation

```python
# Create custom quantum module
def quantum_custom_module(prompt: str, custom_param: str = None) -> str:
    """Custom quantum module example"""
    if custom_param:
        enhanced_prompt = f"{prompt} (custom parameter: {custom_param})"
    else:
        enhanced_prompt = prompt

    response = quantum_ai._make_api_call(enhanced_prompt, "gemini-1.5-pro", "custom_module")

    if response.success:
        return response.content
    else:
        return f"Custom Module Error: {response.error_message}"

# Add to quantum modules registry in quantum_api_endpoint.py
QUANTUM_MODULES["quantum_custom"] = {
    "name": "Custom Quantum Module",
    "description": "Custom functionality example",
    "functions": ["quantum_custom_module"],
    "models": ["gemini-1.5-pro"],
    "category": "custom"
}
```

### Performance Optimization

```python
from quantum import configure_quantum_api, clear_quantum_cache

# Configure for high performance
configure_quantum_api("http://localhost:8002", timeout=30)

# Clear cache for fresh results
clear_quantum_cache()

# Use specific models for different tasks
from quantum import set_quantum_model

set_quantum_model("gemini-1.5-pro")  # For complex tasks
# ... run complex tasks ...
set_quantum_model("gemini-1.5-flash-8b")  # For simple tasks
```

### Error Handling

```python
from quantum import call_gemini

try:
    result = call_gemini("Generate a story about AI")
    print(f"Success: {result[:100]}...")
except Exception as e:
    print(f"Error: {e}")

# Check quantum status for troubleshooting
from quantum import get_quantum_status
status = get_quantum_status()
print(f"Quantum API available: {status.get('connected', False)}")
```

## 📊 Performance & Monitoring

### Cache Management

```python
from quantum import get_quantum_status, clear_quantum_cache

# Check cache performance
status = get_quantum_status()
print(f"Cache size: {status['cache_size']}")
print(f"Cache enabled: {status['cache_enabled']}")

# Clear cache when needed
clear_quantum_cache()
```

### Rate Limiting

The API includes built-in rate limiting (60 requests/minute by default). Monitor usage:

```python
# Check current rate limit status
response = requests.get('/api/quantum/status')
rate_info = response.json()
print(f"Requests remaining: {rate_info.get('rate_limit_remaining', 'unknown')}")
```

## 🔒 Security

### API Key Authentication

```python
# Set API key for authentication
export QUANTUM_API_KEY="your-secure-api-key"

# Enable API key requirement
export REQUIRE_API_KEY="true"
```

### Frontend API Calls

```javascript
// Include API key in requests
const response = await fetch('/api/quantum/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'  // Include API key
    },
    body: JSON.stringify({
        module: 'quantum_gaming',
        prompt: 'Generate game idea'
    })
});
```

## 🚨 Troubleshooting

### Common Issues

#### 1. **Connection Errors**
```python
# Check if OMNI backend is running
from quantum import get_quantum_status
status = get_quantum_status()
print(f"Connected: {status.get('connected', False)}")

# Test basic connectivity
from quantum import call_gemini
result = call_gemini("Hello")
print(f"Basic test: {result}")
```

#### 2. **Module Not Found**
```python
# Check available modules
from quantum import get_quantum_status
status = get_quantum_status()
print(f"Available modules: {status['quantum_modules_available']}")
```

#### 3. **Performance Issues**
```python
# Check cache status
status = get_quantum_status()
print(f"Cache size: {status['cache_size']}")

# Clear cache if too large
from quantum import clear_quantum_cache
clear_quantum_cache()
```

#### 4. **API Key Issues**
```python
# Test API key
import requests
response = requests.post('/api/quantum/query',
    headers={'X-API-Key': 'your-key'},
    json={'module': 'quantum_gaming', 'prompt': 'test'}
)
print(f"Status: {response.status_code}")
```

## 🎯 Best Practices

### 1. **Efficient Prompting**
```python
# Good: Specific and clear
prompt = "Ustvari igro za otroke stare 8-12 let na temo vesolja"

# Better: Include context and requirements
prompt = "Ustvari aktivno igro za otroke (8-12 let) na temo vesolja. Vključi: fizične aktivnosti, izobraževalne elemente in več igralcev."
```

### 2. **Error Handling**
```python
from quantum import call_gemini

def safe_quantum_call(prompt, fallback="Default response"):
    try:
        result = call_gemini(prompt)
        return result if result else fallback
    except Exception as e:
        print(f"Quantum call failed: {e}")
        return fallback
```

### 3. **Caching Strategy**
```python
# Use cache for repeated requests
from quantum import get_quantum_status

status = get_quantum_status()
if status['cache_size'] > 1000:
    from quantum import clear_quantum_cache
    clear_quantum_cache()
```

## 📈 Scaling & Production

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-google-quantum.txt .
RUN pip install -r requirements-google-quantum.txt

COPY quantum.py quantum_api_endpoint.py ./
COPY gcp-credentials.json ./

EXPOSE 8002

CMD ["python", "quantum_api_endpoint.py"]
```

### Load Balancing

```nginx
upstream quantum_backend {
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

server {
    listen 80;

    location /api/quantum/ {
        proxy_pass http://quantum_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 Contributing

### Adding New Quantum Modules

1. **Add function to quantum.py:**
```python
def quantum_new_module(prompt: str, param1: str = None) -> str:
    """New quantum module description"""
    # Implementation
    pass
```

2. **Update API endpoint:**
```python
# Add to QUANTUM_MODULES in quantum_api_endpoint.py
"quantum_new": {
    "name": "New Quantum Module",
    "description": "Description of new module",
    "functions": ["quantum_new_module"],
    "models": ["gemini-1.5-pro"],
    "category": "custom"
}
```

3. **Add routing logic:**
```python
elif module == "quantum_new":
    return quantum_new_module(prompt, options.get('param1'))
```

## 📚 Examples

### Complete Integration Example

```python
#!/usr/bin/env python3
"""
Complete OMNI Quantum AI integration example
"""

from quantum import (
    quantum_gaming_idea,
    quantum_tourism_idea,
    quantum_educational_content,
    get_quantum_status
)

def main():
    print("🧠 OMNI Quantum AI Integration Example")
    print("=" * 50)

    # Check status
    status = get_quantum_status()
    print(f"Quantum AI Connected: {status['connected']}")
    print(f"Available Modules: {len(status['quantum_modules_available'])}")

    # Generate game idea
    print("\n🎮 Generating game idea...")
    game_idea = quantum_gaming_idea("space exploration", "teenagers", "adventure")
    print(f"Game Idea: {game_idea[:200]}...")

    # Generate travel plan
    print("\n🏔️ Generating travel plan...")
    travel_plan = quantum_tourism_idea("Istanbul", "week", "medium")
    print(f"Travel Plan: {travel_plan[:200]}...")

    # Generate educational content
    print("\n📚 Generating educational content...")
    lesson_plan = quantum_educational_content("Umetna inteligenca", "intermediate", "lesson_plan")
    print(f"Lesson Plan: {lesson_plan[:200]}...")

    print("\n✅ Integration example completed!")

if __name__ == "__main__":
    main()
```

## 🔗 Integration with Existing OMNI Platform

The Quantum AI Interface seamlessly integrates with your existing OMNI platform:

1. **Backend Integration**: Uses existing OMNI API endpoints
2. **Authentication**: Leverages current OMNI security model
3. **Caching**: Integrates with OMNI's caching system
4. **Monitoring**: Uses OMNI's monitoring and logging
5. **Frontend**: Compatible with existing OMNI UI components

## 🎉 Ready for Production!

Your OMNI Quantum AI Interface is now ready for:

- ✅ **Frontend integration** with React/Vue.js applications
- ✅ **Modular AI capabilities** for different use cases
- ✅ **Performance optimization** with caching and monitoring
- ✅ **Security and authentication** with API keys
- ✅ **Scalable deployment** with Docker and load balancing
- ✅ **Easy maintenance** with clear module structure

**🚀 Start building amazing AI-powered applications with the OMNI Quantum AI Interface!**