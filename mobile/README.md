# iOS & Android Mobile App - README

## 🚀 Quick Start

### Installation
```bash
cd mobile
npm install

# iOS only
cd ios && pod install && cd ..
```

### Run
```bash
# iOS
npm run ios

# Android
npm run android
```

## ✅ Features

- ✅ Push Notifications (iOS + Android)
- ✅ Offline Mode with Realm DB
- ✅ Biometric Auth (Touch ID, Face ID, Fingerprint)
- ✅ Native Performance (60 FPS)
- ✅ Background Sync
- ✅ Secure Credential Storage

## 📱 Screens

1. **Login**: Email/password + biometric auth
2. **Dashboard**: Real-time metrics and system status
3. **Metrics**: Analytics and charts
4. **Settings**: App configuration and logout

## 🔧 Configuration

Set API URL in AsyncStorage or .env:
```
API_URL=https://omni-ultra-backend-prod-661612368188.europe-west1.run.app
```

## 📖 Documentation

See `MOBILE_APP_IMPLEMENTATION.md` for complete documentation.
