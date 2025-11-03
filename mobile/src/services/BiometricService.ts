/**
 * Biometric Authentication Service
 * Touch ID, Face ID (iOS) and Fingerprint (Android)
 */

import ReactNativeBiometrics from 'react-native-biometrics';
import * as Keychain from 'react-native-keychain';

const rnBiometrics = new ReactNativeBiometrics();

class BiometricService {
  constructor() {
    this.biometryType = null;
    this.isAvailable = false;
  }

  async initialize() {
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      
      this.isAvailable = available;
      this.biometryType = biometryType;

      if (available) {
        console.log(`Biometrics available: ${biometryType}`);
      }

      return { available, biometryType };
    } catch (error) {
      console.error('Error initializing biometrics:', error);
      return { available: false, biometryType: null };
    }
  }

  getBiometryName() {
    switch (this.biometryType) {
      case ReactNativeBiometrics.TouchID:
        return 'Touch ID';
      case ReactNativeBiometrics.FaceID:
        return 'Face ID';
      case ReactNativeBiometrics.Biometrics:
        return 'Fingerprint';
      default:
        return 'Biometric Authentication';
    }
  }

  async authenticate(reason = 'Authenticate to continue') {
    try {
      const { success, error } = await rnBiometrics.simplePrompt({
        promptMessage: reason,
        cancelButtonText: 'Cancel',
      });

      if (success) {
        return { success: true };
      } else {
        return { success: false, error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async saveCredentials(username, password) {
    try {
      await Keychain.setGenericPassword(username, password, {
        accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
        accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_ANY,
        authenticationType: Keychain.AUTHENTICATION_TYPE.BIOMETRICS,
      });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getCredentials(reason = 'Authenticate to access credentials') {
    try {
      const credentials = await Keychain.getGenericPassword({
        authenticationPrompt: {
          title: reason,
          cancel: 'Cancel',
        },
      });

      if (credentials) {
        return {
          success: true,
          username: credentials.username,
          password: credentials.password,
        };
      } else {
        return { success: false, error: 'No credentials stored' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async authenticateForLogin() {
    if (!this.isAvailable) {
      return { success: false, error: 'Biometric authentication not available' };
    }

    const authResult = await this.authenticate('Login with biometrics');
    
    if (!authResult.success) {
      return authResult;
    }

    const credentials = await this.getCredentials('Access your credentials');
    return credentials;
  }
}

const biometricService = new BiometricService();

export const initializeBiometrics = () => biometricService.initialize();
export const authenticateWithBiometrics = (reason) => biometricService.authenticate(reason);
export const saveBiometricCredentials = (username, password) => biometricService.saveCredentials(username, password);

export default biometricService;
