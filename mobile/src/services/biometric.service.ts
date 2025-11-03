import ReactNativeBiometrics, {BiometryTypes} from 'react-native-biometrics';
import * as Keychain from 'react-native-keychain';
import {BIOMETRIC_CONFIG} from '../config/app.config';
import {BiometricAuthResult} from '../types';

class BiometricService {
  private rnBiometrics: ReactNativeBiometrics;

  constructor() {
    this.rnBiometrics = new ReactNativeBiometrics({
      allowDeviceCredentials: BIOMETRIC_CONFIG.FALLBACK_ENABLED,
    });
  }

  async isBiometricAvailable(): Promise<{
    available: boolean;
    biometryType: BiometryTypes | null;
  }> {
    try {
      const {available, biometryType} = await this.rnBiometrics.isSensorAvailable();
      return {available, biometryType};
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      return {available: false, biometryType: null};
    }
  }

  async authenticate(promptMessage?: string): Promise<BiometricAuthResult> {
    try {
      const {available} = await this.isBiometricAvailable();

      if (!available) {
        return {
          success: false,
          error: 'Biometric authentication is not available on this device',
        };
      }

      const {success} = await this.rnBiometrics.simplePrompt({
        promptMessage: promptMessage || BIOMETRIC_CONFIG.PROMPT_MESSAGE,
        cancelButtonText: BIOMETRIC_CONFIG.CANCEL_BUTTON,
      });

      return {success};
    } catch (error: any) {
      console.error('Biometric authentication error:', error);
      return {
        success: false,
        error: error.message || 'Authentication failed',
      };
    }
  }

  async saveCredentials(username: string, password: string): Promise<boolean> {
    try {
      await Keychain.setGenericPassword(username, password, {
        accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_ANY,
        accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED,
      });
      return true;
    } catch (error) {
      console.error('Error saving credentials:', error);
      return false;
    }
  }

  async getCredentials(): Promise<{username: string; password: string} | null> {
    try {
      const credentials = await Keychain.getGenericPassword();
      if (credentials) {
        return {
          username: credentials.username,
          password: credentials.password,
        };
      }
      return null;
    } catch (error) {
      console.error('Error getting credentials:', error);
      return null;
    }
  }

  async deleteCredentials(): Promise<boolean> {
    try {
      await Keychain.resetGenericPassword();
      return true;
    } catch (error) {
      console.error('Error deleting credentials:', error);
      return false;
    }
  }

  async createKeys(): Promise<{publicKey: string} | null> {
    try {
      const {publicKey} = await this.rnBiometrics.createKeys();
      return {publicKey};
    } catch (error) {
      console.error('Error creating biometric keys:', error);
      return null;
    }
  }

  async deleteKeys(): Promise<boolean> {
    try {
      const {keysDeleted} = await this.rnBiometrics.deleteKeys();
      return keysDeleted;
    } catch (error) {
      console.error('Error deleting biometric keys:', error);
      return false;
    }
  }
}

export default new BiometricService();
