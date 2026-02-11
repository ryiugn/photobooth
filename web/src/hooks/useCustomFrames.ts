/**
 * React hook for managing custom frame uploads and storage
 * Handles frame validation, processing, IndexedDB persistence, and storage quota management
 */

import { useState, useEffect, useCallback } from 'react';
import { CustomFrame } from '../types';
import {
  validateImageFile,
  processImageFile
  // REMOVED: isStorageQuotaExceeded, getStorageUsage as getImageStorageUsage
} from '../utils/imageProcessor';
import { indexedDBStorage } from '../utils/indexedDBStorage';

/**
 * Result object from getStorageUsage with formatted strings
 */
export interface StorageUsageInfo {
  used: string;      // Formatted as "X.XX MB"
  total: string;     // Formatted as "X.XX MB"
  percentage: string; // Formatted as "X.XX %"
}

/**
 * Format bytes to megabytes with 2 decimal places
 */
function formatMB(bytes: number): string {
  return (bytes / (1024 * 1024)).toFixed(2);
}

/**
 * Hook return value interface
 */
export interface UseCustomFramesReturn {
  /** Array of custom frames sorted by creation date (newest first) */
  customFrames: CustomFrame[];
  /** Whether frames are being loaded from storage */
  isLoading: boolean;
  /** Upload progress percentage (0-100), 0 when not uploading */
  uploadProgress: number;
  /** Add a new custom frame from a file */
  addCustomFrame: (file: File, name: string) => Promise<CustomFrame>;
  /** Delete a custom frame by ID */
  deleteCustomFrame: (id: string) => void;
  /** Get current storage usage information (async) */
  getStorageUsage: () => Promise<StorageUsageInfo>;
}

/**
 * React hook for managing custom frame state
 *
 * Provides functionality to:
 * - Load frames from IndexedDB on mount and run migration
 * - Add new custom frames with validation and processing
 * - Delete existing frames
 * - Track upload progress
 * - Monitor storage usage
 *
 * @returns UseCustomFramesReturn object with state and functions
 *
 * @example
 * ```tsx
 * const {
 *   customFrames,
 *   isLoading,
 *   uploadProgress,
 *   addCustomFrame,
 *   deleteCustomFrame,
 *   getStorageUsage
 * } = useCustomFrames();
 *
 * // Add a frame
 * await addCustomFrame(file, "My Custom Frame");
 *
 * // Delete a frame
 * deleteCustomFrame(frameId);
 *
 * // Check storage (now async)
 * const { used, total, percentage } = await getStorageUsage();
 * ```
 */
export function useCustomFrames(): UseCustomFramesReturn {
  const [customFrames, setCustomFrames] = useState<CustomFrame[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);

  /**
   * Format bytes to megabytes with 2 decimal places
   */
  const formatMB = useCallback((bytes: number): string => {
    return (bytes / (1024 * 1024)).toFixed(2);
  }, []);

  /**
   * Load frames from IndexedDB on mount and run migration
   */
  useEffect(() => {
    const loadFrames = async () => {
      try {
        // Initialize IndexedDB and run migration
        await indexedDBStorage.init();

        // Run migration from localStorage
        const migrationResult = await indexedDBStorage.migrateFromLocalStorage();
        if (migrationResult.data && migrationResult.data.migrated > 0) {
          console.log(`Migrated ${migrationResult.data.migrated} frames from localStorage`);
        }

        // Load all frames
        const result = await indexedDBStorage.getAllFrames();
        if (result.success && result.data) {
          // Sort by creation date (newest first)
          const sorted = result.data.sort(
            (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          );
          setCustomFrames(sorted);
        }
      } catch (error) {
        console.error('Failed to load custom frames:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadFrames();
  }, []);

  /**
   * Add a new custom frame
   *
   * @param file - The image file to upload
   * @param name - Display name for the frame
   * @returns Promise resolving to the created CustomFrame object
   * @throws Error if validation fails or storage quota exceeded
   */
  const addCustomFrame = async (file: File, name: string): Promise<CustomFrame> => {
    // Start upload progress
    setUploadProgress(10);

    // Validate the file
    const validation = validateImageFile(file);
    if (!validation.valid) {
      setUploadProgress(0);
      throw new Error(validation.error || 'Invalid file');
    }

    // Check storage quota
    const usage = await indexedDBStorage.getStorageUsage();
    if (usage.percentage >= 90) {
      setUploadProgress(0);
      throw new Error('Storage quota exceeded. Please delete some frames to make space.');
    }

    setUploadProgress(50);

    // Process the image file
    const processed = await processImageFile(file);

    setUploadProgress(90);

    // Create custom frame object with unique ID
    const newFrame: CustomFrame = {
      id: `custom_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      dataUrl: processed.dataUrl,
      type: file.type,
      createdAt: new Date().toISOString(),
      source: 'user-upload'
    };

    // Save to IndexedDB
    const result = await indexedDBStorage.addFrame(newFrame);
    if (!result.success) {
      setUploadProgress(0);
      throw new Error(result.error || 'Failed to save frame');
    }

    // Update state
    setCustomFrames((prev) => {
      const updated = [...prev, newFrame];
      return updated.sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
    });

    setUploadProgress(100);

    // Reset progress after a short delay
    setTimeout(() => {
      setUploadProgress(0);
    }, 500);

    return newFrame;
  };

  /**
   * Delete a custom frame by ID
   *
   * @param id - The ID of the frame to delete
   */
  const deleteCustomFrame = async (id: string): Promise<void> => {
    const result = await indexedDBStorage.deleteFrame(id);
    if (result.success) {
      setCustomFrames((prev) => prev.filter((frame) => frame.id !== id));
    } else {
      console.error('Failed to delete frame:', result.error);
    }
  };

  /**
   * Get current storage usage information
   *
   * Calculates the current IndexedDB usage and returns formatted strings
   *
   * @returns StorageUsageInfo with used, total, and percentage as formatted strings
   *
   * @example
   * ```tsx
   * const { used, total, percentage } = await getStorageUsage();
   * console.log(`Used: ${used} of ${total} (${percentage})`);
   * // Output: "Used: 2.45 MB of 100.00 MB (2.45 %)"
   * ```
   */
  const getStorageUsage = useCallback(async (): Promise<StorageUsageInfo> => {
    const usage = await indexedDBStorage.getStorageUsage();
    return {
      used: `${formatMB(usage.used)} MB`,
      total: `${formatMB(usage.total)} MB`,
      percentage: `${usage.percentage.toFixed(2)} %`
    };
  }, [formatMB]);

  return {
    customFrames,
    isLoading,
    uploadProgress,
    addCustomFrame,
    deleteCustomFrame,
    getStorageUsage
  };
}
