#!/usr/bin/env python3
"""
Omni VR Project Generator
Uses OpenAI to generate WebXR experiences from natural language prompts
"""

import os
import json
import asyncio
import aiohttp
import openai
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import base64

class OmniVRProjectGenerator:
    def __init__(self, openai_api_key: str = None, config_file: str = "vr_gateway.json"):
        """
        Initialize the VR Project Generator

        Args:
            openai_api_key: OpenAI API key (optional, can be set via environment)
            config_file: Path to VR gateway configuration file
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.config_file = config_file
        self.config = self.load_config()
        self.vr_config = self.config.get('generation', {})
        self.projects_dir = self.config.get('directories', {}).get('projects', '/vr_projects/')

        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        openai.api_key = self.api_key

        # Ensure projects directory exists
        os.makedirs(self.projects_dir, exist_ok=True)

        print("🚀 Omni VR Project Generator initialized"
    def load_config(self) -> Dict[str, Any]:
        """Load VR gateway configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Config file {self.config_file} not found. Using defaults.")
            return {
                "generation": {
                    "openai_model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "supported_types": ["game", "experience", "scene", "environment", "interactive"],
                    "default_framework": "three.js",
                    "fallback_framework": "aframe"
                },
                "directories": {
                    "projects": "/vr_projects/",
                    "published": "/vr/",
                    "templates": "/vr_templates/",
                    "assets": "/vr_assets/"
                }
            }

    async def generate_vr_project(self, prompt: str, project_type: str = "game",
                                framework: str = None, project_name: str = None) -> Dict[str, Any]:
        """
        Generate a complete VR project from a natural language prompt

        Args:
            prompt: Natural language description of the VR experience
            project_type: Type of VR project (game, experience, scene, etc.)
            framework: VR framework to use (three.js, aframe, etc.)
            project_name: Name for the project (auto-generated if not provided)

        Returns:
            Dictionary containing project details and generated files
        """
        print(f"🎨 Generating VR project: {prompt[:50]}...")

        # Auto-generate project name if not provided
        if not project_name:
            project_name = self._generate_project_name(prompt)

        # Determine framework
        if not framework:
            framework = self.vr_config.get('default_framework', 'three.js')

        # Create project structure
        project_data = {
            "name": project_name,
            "type": project_type,
            "framework": framework,
            "prompt": prompt,
            "created_at": datetime.now().isoformat(),
            "status": "generating",
            "files": {},
            "directories": []
        }

        try:
            # Generate project files based on type
            if project_type == "game":
                await self._generate_game_project(prompt, project_data, framework)
            elif project_type == "experience":
                await self._generate_experience_project(prompt, project_data, framework)
            elif project_type == "scene":
                await self._generate_scene_project(prompt, project_data, framework)
            else:
                await self._generate_generic_project(prompt, project_data, framework)

            project_data["status"] = "completed"
            print(f"✅ VR project '{project_name}' generated successfully")

        except Exception as e:
            project_data["status"] = "failed"
            project_data["error"] = str(e)
            print(f"❌ Failed to generate VR project: {e}")

        return project_data

    def _generate_project_name(self, prompt: str) -> str:
        """Generate a project name from the prompt"""
        # Extract key words from prompt
        words = re.findall(r'\b\w+\b', prompt.lower())
        key_words = [word for word in words if len(word) > 3][:3]

        if key_words:
            name = "-".join(key_words) + "-vr"
        else:
            name = f"vr-project-{int(datetime.now().timestamp())}"

        return name

    async def _generate_game_project(self, prompt: str, project_data: Dict, framework: str):
        """Generate a VR game project"""
        game_prompt = f"""
        Create a complete VR game with the following requirements:
        - Theme/Concept: {prompt}
        - Framework: {framework}
        - Interactive 3D environment
        - Game mechanics and objectives
        - VR controls (gaze, controllers)
        - Scoring system
        - Win/lose conditions

        Generate the complete HTML file with embedded JavaScript and CSS.
        Include WebXR initialization, 3D scene setup, game logic, and VR interactions.
        Make it immediately runnable in VR browsers.
        """

        html_content = await self._call_openai(game_prompt, framework)

        # Extract and clean the HTML content
        html_content = self._extract_html_content(html_content)

        project_data["files"]["index.html"] = html_content
        project_data["directories"] = ["assets", "js", "css"]

    async def _generate_experience_project(self, prompt: str, project_data: Dict, framework: str):
        """Generate a VR experience project"""
        experience_prompt = f"""
        Create an immersive VR experience with:
        - Theme: {prompt}
        - Framework: {framework}
        - Atmospheric 3D environment
        - Interactive elements
        - Ambient effects (lighting, sounds, particles)
        - Smooth VR navigation

        Generate a complete HTML file with WebXR support.
        Focus on immersion, atmosphere, and user experience.
        """

        html_content = await self._call_openai(experience_prompt, framework)
        html_content = self._extract_html_content(html_content)

        project_data["files"]["index.html"] = html_content

    async def _generate_scene_project(self, prompt: str, project_data: Dict, framework: str):
        """Generate a VR scene project"""
        scene_prompt = f"""
        Create a static VR scene/environment:
        - Description: {prompt}
        - Framework: {framework}
        - Detailed 3D models and textures
        - Proper lighting and shadows
        - Spatial audio (if applicable)
        - 360-degree exploration

        Generate complete HTML with WebXR scene setup.
        """

        html_content = await self._call_openai(scene_prompt, framework)
        html_content = self._extract_html_content(html_content)

        project_data["files"]["index.html"] = html_content

    async def _generate_generic_project(self, prompt: str, project_data: Dict, framework: str):
        """Generate a generic VR project"""
        generic_prompt = f"""
        Create a VR project based on: {prompt}
        Framework: {framework}

        Generate a complete, interactive WebXR experience.
        Include proper VR setup, 3D scene, and interactions.
        """

        html_content = await self._call_openai(generic_prompt, framework)
        html_content = self._extract_html_content(html_content)

        project_data["files"]["index.html"] = html_content

    async def _call_openai(self, prompt: str, framework: str) -> str:
        """Call OpenAI API to generate VR content"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.vr_config.get('openai_model', 'gpt-4'),
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert VR developer creating WebXR experiences using {framework}. Generate complete, runnable HTML files with embedded JavaScript and CSS. Always include proper WebXR initialization and VR support."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.vr_config.get('max_tokens', 4000),
                temperature=self.vr_config.get('temperature', 0.7)
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return self._get_fallback_content(framework)

    def _extract_html_content(self, content: str) -> str:
        """Extract and clean HTML content from OpenAI response"""
        # Remove markdown code blocks if present
        content = re.sub(r'```html?\s*', '', content)
        content = re.sub(r'```\s*$', '', content)

        # Ensure we have a complete HTML document
        if not content.strip().startswith('<!DOCTYPE html>'):
            # If it's not a complete HTML, wrap it
            content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VR Experience</title>
    <style>
        body {{ margin: 0; overflow: hidden; }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""

        return content

    def _get_fallback_content(self, framework: str) -> str:
        """Get fallback content if OpenAI fails"""
        if framework.lower() == "three.js":
            return self._get_threejs_fallback()
        else:
            return self._get_aframe_fallback()

    def _get_threejs_fallback(self) -> str:
        """Get Three.js fallback content"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VR Experience - Three.js</title>
    <style>
        body { margin: 0; overflow: hidden; font-family: Arial, sans-serif; }
        #info { position: absolute; top: 10px; left: 10px; color: white; z-index: 100; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="info">Loading VR Experience...</div>

    <script>
        let scene, camera, renderer, vrButton;

        function init() {
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.xr.enabled = true;
            document.body.appendChild(renderer.domElement);

            // Add VR button
            vrButton = document.createElement('button');
            vrButton.textContent = 'Enter VR';
            vrButton.style.cssText = 'position: absolute; top: 20px; right: 20px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; z-index: 1000;';
            vrButton.addEventListener('click', () => {
                renderer.xr.getSession().then(session => {
                    vrButton.style.display = 'none';
                }).catch(() => {
                    navigator.xr.requestSession('immersive-vr').then(session => {
                        vrButton.style.display = 'none';
                    });
                });
            });
            document.body.appendChild(vrButton);

            // Add basic scene content
            const geometry = new THREE.BoxGeometry(1, 1, 1);
            const material = new THREE.MeshPhongMaterial({ color: 0x00ff00 });
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            camera.position.z = 5;

            const light = new THREE.PointLight(0xffffff, 1);
            light.position.set(10, 10, 10);
            scene.add(light);

            animate();
        }

        function animate() {
            renderer.setAnimationLoop(render);
        }

        function render() {
            if (renderer.xr.isPresenting) {
                document.getElementById('info').style.display = 'none';
            }
            renderer.render(scene, camera);
        }

        // Check for WebXR support
        if (navigator.xr) {
            navigator.xr.isSessionSupported('immersive-vr').then(supported => {
                if (supported) {
                    init();
                } else {
                    document.getElementById('info').textContent = 'WebXR not supported';
                }
            });
        } else {
            document.getElementById('info').textContent = 'WebXR not available';
        }
    </script>
</body>
</html>"""

    def _get_aframe_fallback(self) -> str:
        """Get A-Frame fallback content"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VR Experience - A-Frame</title>
    <script src="https://aframe.io/releases/1.4.0/aframe.min.js"></script>
</head>
<body>
    <a-scene>
        <a-box position="-1 0.5 -3" rotation="0 45 0" color="#4CC3D9"></a-box>
        <a-sphere position="0 1.25 -5" radius="1.25" color="#EF2D5E"></a-sphere>
        <a-cylinder position="1 0.75 -3" radius="0.5" height="1.5" color="#FFC65D"></a-cylinder>
        <a-plane position="0 0 -4" rotation="-90 0 0" width="4" height="4" color="#7BC8A4"></a-plane>
        <a-sky color="#ECECEC"></a-sky>

        <!-- VR Controls -->
        <a-entity camera look-controls wasd-controls position="0 1.6 0">
            <a-cursor></a-cursor>
        </a-entity>
    </a-scene>

    <div style="position: absolute; top: 20px; right: 20px; z-index: 1000;">
        <button onclick="document.querySelector('a-scene').enterVR()">Enter VR</button>
    </div>
</body>
</html>"""

    def save_project(self, project_data: Dict[str, Any]) -> str:
        """Save the generated VR project to disk"""
        project_name = project_data["name"]
        project_dir = os.path.join(self.projects_dir, project_name)

        # Create project directory
        os.makedirs(project_dir, exist_ok=True)

        # Save project metadata
        metadata_file = os.path.join(project_dir, "project.json")
        with open(metadata_file, 'w') as f:
            json.dump(project_data, f, indent=2)

        # Save all files
        for filename, content in project_data.get("files", {}).items():
            file_path = os.path.join(project_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)

        # Create additional directories if specified
        for dir_name in project_data.get("directories", []):
            os.makedirs(os.path.join(project_dir, dir_name), exist_ok=True)

        print(f"💾 Project saved to: {project_dir}")
        return project_dir

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all generated VR projects"""
        projects = []

        if not os.path.exists(self.projects_dir):
            return projects

        for project_name in os.listdir(self.projects_dir):
            project_dir = os.path.join(self.projects_dir, project_name)

            if os.path.isdir(project_dir):
                metadata_file = os.path.join(project_dir, "project.json")

                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        project_data = json.load(f)
                        projects.append(project_data)

        return sorted(projects, key=lambda x: x.get("created_at", ""), reverse=True)

# Example usage and CLI interface
async def main():
    """Main function for CLI usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python vr_project_generator.py 'Your VR project description'")
        sys.exit(1)

    prompt = sys.argv[1]
    project_type = sys.argv[2] if len(sys.argv) > 2 else "game"

    # Get API key from environment or file
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Try to read from file
        key_file = "openai key.txt"
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                api_key = f.read().strip()

    if not api_key:
        print("❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable or create 'openai key.txt'")
        sys.exit(1)

    generator = OmniVRProjectGenerator(api_key)

    print(f"🎨 Generating VR project from prompt: {prompt}")
    project_data = await generator.generate_vr_project(prompt, project_type)

    if project_data["status"] == "completed":
        project_dir = generator.save_project(project_data)
        print(f"✅ Project generated successfully!")
        print(f"📁 Location: {project_dir}")
        print(f"🌐 Access at: /vr/{project_data['name']}/")
    else:
        print(f"❌ Project generation failed: {project_data.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())