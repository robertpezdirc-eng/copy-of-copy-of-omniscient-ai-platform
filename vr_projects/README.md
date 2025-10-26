# Omni VR Projects Directory

This directory contains all generated VR experiences and projects for the Omni platform.

## Directory Structure

```
vr_projects/
├── README.md                    # This file
├── templates/                   # VR project templates
│   ├── threejs_basic.html       # Basic Three.js VR template
│   ├── aframe_basic.html        # Basic A-Frame VR template
│   └── game_template.html       # VR game template
├── assets/                      # Shared assets and resources
│   ├── textures/               # Texture files
│   ├── models/                 # 3D model files
│   ├── sounds/                 # Audio files
│   └── shaders/                # Custom shader files
├── published/                  # Auto-published VR experiences
└── [project_name]/             # Individual project directories
    ├── project.json            # Project metadata
    ├── index.html              # Main VR experience file
    ├── assets/                 # Project-specific assets
    ├── js/                     # JavaScript files
    └── css/                    # Stylesheet files
```

## Project Structure

Each VR project directory contains:

### project.json
Metadata file containing:
- Project name and description
- Creation date and author
- VR framework used (Three.js, A-Frame, etc.)
- Project type (game, experience, scene, etc.)
- Generation parameters
- File manifest

### Main Files
- `index.html` - Main VR experience file with WebXR support
- Supporting assets in subdirectories

## Usage

### Creating New Projects

Use the VR Project Generator:
```bash
python vr_project_generator.py "A 3D trampoline VR game with physics" game
```

Or from Python:
```python
from vr_project_generator import OmniVRProjectGenerator

generator = OmniVRProjectGenerator("your-openai-key")
project = await generator.generate_vr_project(
    "Interactive VR art gallery",
    project_type="experience"
)
project_dir = generator.save_project(project)
```

### Accessing Projects

Projects are accessible via:
- Local development: `http://localhost:8080/vr/[project_name]/`
- Railway deployment: `https://your-app.railway.app/vr/[project_name]/`
- LocalTunnel: `https://your-subdomain.loca.lt/vr/[project_name]/`

### VR Glasses Compatibility

For VR glasses (Oculus Quest, HTC Vive, etc.):
1. Ensure HTTPS is enabled (required for WebXR)
2. Use supported browsers (Oculus Browser, Chrome, Edge)
3. Navigate to the project URL
4. Click "Enter VR" button
5. Grant necessary permissions

## Supported VR Frameworks

### Three.js
- Advanced 3D graphics and animations
- Custom shaders and materials
- Physics integration
- Complex interactions

### A-Frame
- HTML-based VR scenes
- Entity-component system
- Easy to learn and modify
- Good for simple experiences

## Project Types

### Games
- Interactive gameplay mechanics
- Scoring systems
- Win/lose conditions
- Physics-based interactions

### Experiences
- Immersive environments
- Atmospheric effects
- Guided tours
- Interactive storytelling

### Scenes
- Static 3D environments
- Architectural visualizations
- Product showcases
- Art installations

## Development Tips

1. **HTTPS Requirement**: WebXR requires HTTPS for security
2. **Browser Compatibility**: Test in VR-capable browsers
3. **Performance**: Optimize 3D models and textures for VR
4. **User Interface**: Keep UI elements simple and readable
5. **Motion Sickness**: Avoid rapid movements and camera shake

## Integration with Omni Platform

VR projects integrate with:
- **OpenAI Generation**: Natural language to VR experiences
- **Dashboard**: Project management and links
- **Cloud Deployment**: Automatic publishing to Railway
- **Version Control**: Project history and updates

## Troubleshooting

### Common Issues

1. **WebXR Not Supported**
   - Use Oculus Browser on Quest
   - Enable WebXR in browser flags
   - Update browser to latest version

2. **HTTPS Issues**
   - Ensure valid SSL certificate
   - Check CORS configuration
   - Verify domain configuration

3. **Performance Problems**
   - Reduce polygon count in 3D models
   - Optimize texture sizes
   - Limit concurrent animations

### Debug Mode

Enable debug logging:
```javascript
localStorage.setItem('vr-debug', 'true');
```

Check browser console for WebXR errors and warnings.