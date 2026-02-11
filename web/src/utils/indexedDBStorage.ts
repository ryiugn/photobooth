/**
 * IndexedDB wrapper for storing custom frames
 * Provides a simple async API with built-in error handling and localStorage fallback
 */

import { CustomFrame } from '../types';

const DB_NAME = 'PhotoboothFramesDB';
const STORE_NAME = 'customFrames';
const DB_VERSION = 1;

/**
 * Result type for database operations
 */
export interface DBResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Storage usage information
 */
export interface StorageUsage {
  used: number;      // Bytes used
  total: number;     // Total quota (estimated)
  percentage: number; // Percentage used
}

/**
 * IndexedDB Storage class
 * Handles all IndexedDB operations with fallback to localStorage
 */
class IndexedDBStorage {
  private db: IDBDatabase | null = null;
  private isInitialized = false;
  private useFallback = false;
  private fallbackKey = 'photobooth_custom_frames_fallback';

  /**
   * Initialize the IndexedDB database
   */
  async init(): Promise<DBResult<void>> {
    // Check if already initialized
    if (this.isInitialized) {
      return { success: true };
    }

    // Check if IndexedDB is supported
    if (typeof window === 'undefined' || !window.indexedDB) {
      console.warn('IndexedDB not supported, using localStorage fallback');
      this.useFallback = true;
      this.isInitialized = true;
      return { success: true };
    }

    return new Promise((resolve) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('Failed to open IndexedDB, using localStorage fallback');
        this.useFallback = true;
        this.isInitialized = true;
        resolve({ success: true });
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.isInitialized = true;
        resolve({ success: true });
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        }
      };
    });
  }

  /**
   * Get all frames from storage
   */
  async getAllFrames(): Promise<DBResult<CustomFrame[]>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.getFallback();
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        resolve({ success: true, data: request.result as CustomFrame[] });
      };

      request.onerror = () => {
        console.error('Failed to get frames from IndexedDB, trying fallback');
        resolve(this.getFallback());
      };
    });
  }

  /**
   * Add a single frame to storage (uses put() for duplicate handling)
   */
  async addFrame(frame: CustomFrame): Promise<DBResult<void>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.addFallback(frame);
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');

      // Add transaction error handler
      transaction.onerror = () => {
        console.error('Transaction failed, trying fallback');
        resolve(this.addFallback(frame));
      };

      transaction.oncomplete = () => {
        // Transaction succeeded
      };

      const store = transaction.objectStore(STORE_NAME);
      // Use put() instead of add() to handle duplicates gracefully (replaces if exists)
      const request = store.put(frame);

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        console.error('Failed to add frame to IndexedDB, trying fallback');
        resolve(this.addFallback(frame));
      };
    });
  }

  /**
   * Delete a frame by ID
   */
  async deleteFrame(frameId: string): Promise<DBResult<void>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.deleteFallback(frameId);
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');

      transaction.onerror = () => {
        console.error('Delete transaction failed, trying fallback');
        resolve(this.deleteFallback(frameId));
      };

      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(frameId);

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        console.error('Failed to delete frame from IndexedDB, trying fallback');
        resolve(this.deleteFallback(frameId));
      };
    });
  }

  /**
   * Get storage usage information
   * For IndexedDB, this is an estimate based on frame data sizes
   */
  async getStorageUsage(): Promise<StorageUsage> {
    const result = await this.getAllFrames();
    const frames = result.data || [];

    let used = 0;
    for (const frame of frames) {
      // Estimate size based on dataUrl length
      used += frame.dataUrl.length * 2; // UTF-16
    }

    // IndexedDB has much larger limits - estimate 100MB per origin
    const total = 100 * 1024 * 1024;
    const percentage = (used / total) * 100;

    return { used, total, percentage };
  }

  /**
   * Clear all frames from storage
   */
  async clearAllFrames(): Promise<DBResult<void>> {
    await this.init();

    if (this.useFallback || !this.db) {
      return this.clearFallback();
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');

      transaction.onerror = () => {
        console.error('Failed to clear IndexedDB, trying fallback');
        resolve(this.clearFallback());
      };

      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        resolve(this.clearFallback());
      };
    });
  }

  /**
   * Reset/clear all storage (for debugging or recovery)
   */
  async resetStorage(): Promise<DBResult<void>> {
    await this.init();

    // Clear migration flag
    localStorage.removeItem('photobooth_frames_migrated');

    if (this.useFallback || !this.db) {
      return this.clearFallback();
    }

    return new Promise((resolve) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');

      transaction.onerror = () => {
        console.error('Failed to reset IndexedDB');
        resolve({ success: false, error: 'Reset failed' });
      };

      const store = transaction.objectStore(STORE_NAME);
      const request = store.clear();

      request.onsuccess = () => {
        resolve({ success: true });
      };

      request.onerror = () => {
        resolve({ success: false, error: 'Reset failed' });
      };
    });
  }

  // Fallback methods using localStorage

  private getFallback(): DBResult<CustomFrame[]> {
    try {
      // Check both old and new fallback keys for migration compatibility
      let stored = localStorage.getItem(this.fallbackKey);
      if (!stored) {
        // Try old key for migration
        stored = localStorage.getItem('photobooth_custom_frames');
      }
      if (stored) {
        return { success: true, data: JSON.parse(stored) };
      }
      return { success: true, data: [] };
    } catch (error) {
      console.error('Fallback localStorage read failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  private addFallback(frame: CustomFrame): DBResult<void> {
    try {
      const result = this.getFallback();
      const frames = result.data || [];
      frames.push(frame);
      localStorage.setItem(this.fallbackKey, JSON.stringify(frames));
      return { success: true };
    } catch (error) {
      console.error('Fallback localStorage write failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  private deleteFallback(frameId: string): DBResult<void> {
    try {
      const result = this.getFallback();
      const frames = (result.data || []).filter((f) => f.id !== frameId);
      localStorage.setItem(this.fallbackKey, JSON.stringify(frames));
      return { success: true };
    } catch (error) {
      console.error('Fallback localStorage delete failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  private clearFallback(): DBResult<void> {
    try {
      localStorage.removeItem(this.fallbackKey);
      localStorage.removeItem('photobooth_custom_frames'); // Also clear old key
      return { success: true };
    } catch (error) {
      console.error('Fallback localStorage clear failed:', error);
      return { success: false, error: 'Fallback storage unavailable' };
    }
  }

  /**
   * Check if using fallback storage
   */
  isUsingFallback(): boolean {
    return this.useFallback;
  }

  /**
   * Migrate frames from localStorage to IndexedDB
   * This should be called once on app initialization
   */
  async migrateFromLocalStorage(): Promise<DBResult<{ migrated: number; skipped: number }>> {
    await this.init();

    // Skip if using fallback or already migrated
    if (this.useFallback || !this.db) {
      return { success: true, data: { migrated: 0, skipped: 0 } };
    }

    // Check if already migrated (use both flag and presence of IndexedDB data)
    const migrationFlag = localStorage.getItem('photobooth_frames_migrated');
    const existingFrames = await this.getAllFrames();

    // Consider migrated if flag is set OR we already have frames in IndexedDB
    if (migrationFlag === 'true' || (existingFrames.data && existingFrames.data.length > 0)) {
      // Update flag if not set but we have data
      if (migrationFlag !== 'true') {
        localStorage.setItem('photobooth_frames_migrated', 'true');
      }
      return { success: true, data: { migrated: 0, skipped: 0 } };
    }

    try {
      // Read from old localStorage key
      const oldData = localStorage.getItem('photobooth_custom_frames');
      if (!oldData) {
        // Mark as migrated even if no data
        localStorage.setItem('photobooth_frames_migrated', 'true');
        return { success: true, data: { migrated: 0, skipped: 0 } };
      }

      const oldFrames: CustomFrame[] = JSON.parse(oldData);
      let migrated = 0;
      let skipped = 0;

      // Get existing frames to avoid duplicates
      const existingIds = new Set((existingFrames.data || []).map((f) => f.id));

      // Add each frame to IndexedDB
      for (const frame of oldFrames) {
        if (existingIds.has(frame.id)) {
          skipped++;
          continue;
        }

        const addResult = await this.addFrame(frame);
        if (addResult.success) {
          migrated++;
        } else {
          skipped++;
        }
      }

      // ONLY clear localStorage after ALL frames are successfully migrated
      if (migrated === oldFrames.length) {
        // All frames migrated successfully, safe to clear
        try {
          localStorage.removeItem('photobooth_custom_frames');
          console.log('[Migration] Cleared old localStorage data after successful migration');
        } catch (e) {
          console.warn('[Migration] Could not clear old localStorage data:', e);
        }
      } else if (migrated > 0) {
        // Partial migration - log warning but don't clear
        console.warn(`[Migration] Partial migration: ${migrated}/${oldFrames.length} frames. Old data preserved.`);
      }

      // Mark migration as complete
      localStorage.setItem('photobooth_frames_migrated', 'true');

      return { success: true, data: { migrated, skipped } };
    } catch (error) {
      console.error('[Migration] Failed:', error);
      // Don't set migration flag on error - allow retry
      return { success: false, error: 'Migration failed' };
    }
  }
}

// Singleton instance
const storage = new IndexedDBStorage();

// Export API functions
export const indexedDBStorage = {
  init: () => storage.init(),
  getAllFrames: () => storage.getAllFrames(),
  addFrame: (frame: CustomFrame) => storage.addFrame(frame),
  deleteFrame: (frameId: string) => storage.deleteFrame(frameId),
  getStorageUsage: () => storage.getStorageUsage(),
  clearAllFrames: () => storage.clearAllFrames(),
  isUsingFallback: () => storage.isUsingFallback(),
  migrateFromLocalStorage: () => storage.migrateFromLocalStorage(),
  resetStorage: () => storage.resetStorage(),
};
