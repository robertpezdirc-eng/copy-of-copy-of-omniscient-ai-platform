/**
 * Background Tasks Registration
 */

import BackgroundFetch from 'react-native-background-fetch';
import { syncPendingActions } from './OfflineService';

BackgroundFetch.configure(
  {
    minimumFetchInterval: 15,
    stopOnTerminate: false,
    startOnBoot: true,
    enableHeadless: true,
  },
  async (taskId) => {
    console.log('[BackgroundFetch] Task started:', taskId);
    
    try {
      await syncPendingActions();
      console.log('[BackgroundFetch] Sync completed');
    } catch (error) {
      console.error('[BackgroundFetch] Error:', error);
    }
    
    BackgroundFetch.finish(taskId);
  },
  (taskId) => {
    console.log('[BackgroundFetch] Task timeout:', taskId);
    BackgroundFetch.finish(taskId);
  }
);

export default BackgroundFetch;
