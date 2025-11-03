# Omni Enterprise Ultra Max - Mobile Application

## 🚀 Features

### ✅ iOS + Android Support (React Native)
- Cross-platform mobile application built with React Native
- Native performance on both iOS and Android
- TypeScript for type safety and better developer experience

### 📱 Push Notifications
- Firebase Cloud Messaging (FCM) for Android
- Apple Push Notification Service (APNs) for iOS
- Background and foreground notification handling
- Rich notifications with data payloads
- Notification topics for targeted messaging

### 🔌 Offline Mode
- AsyncStorage for local data persistence
- Offline request queue with automatic retry
- Network state monitoring
- Automatic sync when connection is restored
- Visual indicators for offline status

### 🔐 Biometric Authentication
- Fingerprint authentication support
- Face ID support (iOS)
- Secure credential storage with Keychain (iOS) / Keystore (Android)
- Fallback to PIN/password authentication
- Biometric prompt customization

### ⚡ Native Performance
- Hermes JavaScript engine for Android
- Optimized bundle size
- Lazy loading and code splitting
- ProGuard/R8 for Android
- Native module integration for performance-critical operations

## 📋 Prerequisites

### General
- Node.js >= 18
- npm or yarn
- Git

### Android
- Android Studio
- Android SDK
- Java Development Kit (JDK) 11 or higher
- Android emulator or physical device

### iOS (macOS only)
- Xcode 14 or higher
- CocoaPods
- iOS Simulator or physical device
- Apple Developer account (for device deployment)

## 🛠️ Installation

### 1. Clone the repository

```bash
cd mobile
```

### 2. Install dependencies

```bash
npm install
# or
yarn install
```

### 3. iOS Setup (macOS only)

```bash
cd ios
pod install
cd ..
```

### 4. Android Setup

No additional setup required. The project is ready to build.

## 🚀 Running the App

### Start Metro Bundler

```bash
npm start
# or
yarn start
```

### Run on Android

```bash
npm run android
# or
yarn android
```

### Run on iOS (macOS only)

```bash
npm run ios
# or
yarn ios
```

## 🔧 Configuration

### API Configuration

Edit `src/config/app.config.ts`:

```typescript
export const API_CONFIG = {
  GATEWAY_URL: 'https://your-gateway-url.com',
  BACKEND_URL: 'https://your-backend-url.com',
  API_KEY: 'your-api-key',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
};
```

### Firebase Configuration

#### Android
1. Download `google-services.json` from Firebase Console
2. Place it in `android/app/google-services.json`

#### iOS
1. Download `GoogleService-Info.plist` from Firebase Console
2. Place it in `ios/OmniMobile/GoogleService-Info.plist`

## 📱 Features Implementation

### Push Notifications

The app uses Firebase Cloud Messaging for push notifications:

```typescript
import pushNotificationService from './services/pushNotification.service';

// Initialize push notifications
await pushNotificationService.initialize();

// Send local notification
await pushNotificationService.sendLocalNotification(
  'Hello',
  'This is a test notification'
);
```

### Offline Mode

Automatic offline queue management:

```typescript
import apiService from './services/api.service';

// API calls are automatically queued when offline
const response = await apiService.get('/api/endpoint');

// Requests are automatically retried when connection is restored
```

### Biometric Authentication

```typescript
import biometricService from './services/biometric.service';

// Check if biometric is available
const {available, biometryType} = await biometricService.isBiometricAvailable();

// Authenticate user
const result = await biometricService.authenticate('Login to Omni Enterprise');
if (result.success) {
  // Authentication successful
}
```

## 🏗️ Project Structure

```
mobile/
├── android/                 # Android native code
├── ios/                     # iOS native code
├── src/
│   ├── components/         # Reusable UI components
│   ├── config/            # App configuration
│   ├── navigation/        # Navigation setup
│   ├── screens/           # App screens
│   ├── services/          # API and utility services
│   ├── store/             # State management (Zustand)
│   ├── types/             # TypeScript types
│   └── App.tsx            # Main app component
├── .eslintrc.js           # ESLint configuration
├── .prettierrc.js         # Prettier configuration
├── babel.config.js        # Babel configuration
├── jest.config.js         # Jest configuration
├── metro.config.js        # Metro bundler configuration
├── package.json           # Dependencies and scripts
└── tsconfig.json          # TypeScript configuration
```

## 🔨 Build for Production

### Android

```bash
cd android
./gradlew assembleRelease
```

The APK will be in `android/app/build/outputs/apk/release/`

### iOS

```bash
cd ios
xcodebuild -workspace OmniMobile.xcworkspace -scheme OmniMobile -configuration Release
```

## 🧪 Testing

```bash
npm test
# or
yarn test
```

## 📦 Key Dependencies

- **react-native**: Core framework
- **@react-navigation**: Navigation library
- **@react-native-firebase**: Firebase integration
- **@notifee/react-native**: Local notifications
- **react-native-biometrics**: Biometric authentication
- **@react-native-async-storage**: Local storage
- **@react-native-community/netinfo**: Network monitoring
- **react-native-keychain**: Secure credential storage
- **zustand**: State management
- **axios**: HTTP client

## 🎨 UI Components

The app uses:
- React Native core components
- Custom styled components
- Material Community Icons

## 🔐 Security Features

- Biometric authentication
- Secure credential storage
- API key authentication
- SSL/TLS for API communication
- Sensitive data encryption

## 🌐 Backend Integration

The mobile app connects to the Omni Enterprise Ultra Max backend:

- **Gateway URL**: API Gateway with rate limiting
- **Backend URL**: ML backend with 50+ endpoints
- **Authentication**: API key + JWT tokens
- **Real-time**: WebSocket support for live updates

## 📊 Performance Optimizations

- Hermes engine for faster startup
- Code splitting and lazy loading
- Image optimization
- Virtualized lists for large datasets
- Memory management
- ProGuard/R8 for Android bundle size reduction

## 🐛 Troubleshooting

### Android

**Issue**: Build failed
```bash
cd android
./gradlew clean
cd ..
npm run android
```

**Issue**: Metro bundler cache
```bash
npm start -- --reset-cache
```

### iOS

**Issue**: Pod install failed
```bash
cd ios
pod deintegrate
pod install
cd ..
```

**Issue**: Build failed
```bash
cd ios
xcodebuild clean
cd ..
npm run ios
```

## 📝 Environment Variables

Create a `.env` file in the mobile directory:

```env
API_GATEWAY_URL=https://your-gateway-url.com
API_BACKEND_URL=https://your-backend-url.com
API_KEY=your-api-key
```

## 🚢 CI/CD

GitHub Actions workflow for mobile builds (see `.github/workflows/mobile-build.yml`)

## 📄 License

Copyright © 2025 Omni Enterprise Ultra Max. All rights reserved.

## 🤝 Support

For issues and questions:
- Create a GitHub issue
- Contact: support@omni-enterprise.com

---

**Built with ❤️ for iOS and Android**
