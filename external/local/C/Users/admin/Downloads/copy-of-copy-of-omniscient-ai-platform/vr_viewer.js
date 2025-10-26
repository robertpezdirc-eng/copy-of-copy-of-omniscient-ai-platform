'/**
 * Omni VR Viewer Module
 * Handles WebXR initialization and VR experience management
 */

class OmniVRViewer {
    constructor(config = {}) {
        this.config = {
            containerId: config.containerId || 'vr-container',
            autoInit: config.autoInit || false,
            showButton: config.showButton !== false,
            buttonText: config.buttonText || 'Enter VR',
            buttonClass: config.buttonClass || 'vr-enter-button',
            ...config
        };

        this.isVRSupported = false;
        this.isVRActive = false;
        this.currentSession = null;
        this.container = null;
        this.button = null;

        this.init();
    }

    async init() {
        console.log('🚀 Initializing Omni VR Viewer...');

        // Check for WebXR support
        this.isVRSupported = await this.checkVRSupport();

        if (!this.isVRSupported) {
            console.warn('⚠️ WebXR not supported in this browser');
            this.showFallbackMessage();
            return;
        }

        this.createContainer();
        this.createVRButton();

        if (this.config.autoInit) {
            this.enterVR();
        }

        console.log('✅ VR Viewer initialized successfully');
    }

    async checkVRSupport() {
        if (!navigator.xr) {
            return false;
        }

        try {
            return await navigator.xr.isSessionSupported('immersive-vr');
        } catch (error) {
            console.error('Error checking VR support:', error);
            return false;
        }
    }

    createContainer() {
        this.container = document.getElementById(this.config.containerId);
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = this.config.containerId;
            this.container.className = 'vr-viewer-container';
            document.body.appendChild(this.container);
        }

        // Add CSS styles
        this.addVRStyles();
    }

    createVRButton() {
        if (!this.config.showButton) return;

        this.button = document.createElement('button');
        this.button.id = 'vr-enter-button';
        this.button.className = this.config.buttonClass;
        this.button.textContent = this.config.buttonText;
        this.button.addEventListener('click', () => this.enterVR());

        // Add to container or body if no container
        if (this.container) {
            this.container.appendChild(this.button);
        } else {
            document.body.appendChild(this.button);
        }
    }

    addVRStyles() {
        const styleId = 'omni-vr-styles';
        if (document.getElementById(styleId)) return;

        const styles = document.createElement('style');
        styles.id = styleId;
        styles.textContent = `
            .vr-viewer-container {
                position: relative;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }

            .vr-enter-button {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }

            .vr-enter-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }

            .vr-enter-button:active {
                transform: translateY(0);
            }

            .vr-fallback-message {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                padding: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                border-radius: 8px;
                max-width: 400px;
            }

            .vr-active {
                cursor: grab;
            }

            .vr-active:active {
                cursor: grabbing;
            }

            @media (max-width: 768px) {
                .vr-enter-button {
                    top: 10px;
                    right: 10px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    async enterVR() {
        if (!this.isVRSupported) {
            this.showFallbackMessage();
            return;
        }

        try {
            const sessionInit = {
                optionalFeatures: ['local-floor', 'bounded-floor', 'hand-tracking']
            };

            this.currentSession = await navigator.xr.requestSession('immersive-vr', sessionInit);
            this.isVRActive = true;

            this.button.style.display = 'none';
            this.container.classList.add('vr-active');

            // Set up session event listeners
            this.currentSession.addEventListener('end', () => this.exitVR());

            console.log('🎉 Entered VR mode successfully');
            this.onVREntered();

        } catch (error) {
            console.error('❌ Failed to enter VR:', error);
            this.showError('Failed to enter VR mode. Please try again.');
        }
    }

    exitVR() {
        if (this.currentSession) {
            this.currentSession.end();
            this.currentSession = null;
        }

        this.isVRActive = false;
        this.button.style.display = 'block';
        this.container.classList.remove('vr-active');

        console.log('👋 Exited VR mode');
        this.onVRExited();
    }

    showFallbackMessage() {
        const message = document.createElement('div');
        message.className = 'vr-fallback-message';
        message.innerHTML = `
            <h3>VR Not Supported</h3>
            <p>Your browser doesn't support WebXR. Try using:</p>
            <ul style="text-align: left;">
                <li>Oculus Browser on Quest</li>
                <li>Chrome on VR-capable devices</li>
                <li>Edge on Windows Mixed Reality</li>
            </ul>
        `;

        document.body.appendChild(message);
    }

    showError(message) {
        // Create temporary error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'vr-fallback-message';
        errorDiv.innerHTML = `<h3>Error</h3><p>${message}</p>`;
        errorDiv.style.background = 'rgba(220, 38, 38, 0.9)';

        document.body.appendChild(errorDiv);

        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    // Event callbacks
    onVREntered() {
        if (this.config.onVREntered) {
            this.config.onVREntered(this.currentSession);
        }

        // Dispatch custom event
        const event = new CustomEvent('vr:entered', {
            detail: { session: this.currentSession }
        });
        document.dispatchEvent(event);
    }

    onVRExited() {
        if (this.config.onVRExited) {
            this.config.onVRExited();
        }

        // Dispatch custom event
        const event = new CustomEvent('vr:exited');
        document.dispatchEvent(event);
    }

    // Public API methods
    getIsVRActive() {
        return this.isVRActive;
    }

    getSession() {
        return this.currentSession;
    }

    destroy() {
        if (this.currentSession) {
            this.currentSession.end();
        }

        if (this.button && this.button.parentNode) {
            this.button.parentNode.removeChild(this.button);
        }

        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }

        console.log('🗑️ VR Viewer destroyed');
    }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OmniVRViewer;
}

if (typeof window !== 'undefined') {
    window.OmniVRViewer = OmniVRViewer;
}
