/**
 * React hook for managing custom frame uploads and storage
 * Handles frame validation, processing, localStorage persistence, and storage quota management
 */

import { useState, useEffect } from 'react';
import { CustomFrame } from '../types';
import {
  validateImageFile,
  processImageFile,
  isStorageQuotaExceeded,
  getStorageUsage as getImageStorageUsage
} from '../utils/imageProcessor';

/**
 * Storage key for custom frames in localStorage
 */
const STORAGE_KEY = 'photobooth_custom_frames';

/**
 * Format bytes to megabytes with 2 decimal places
 */
function formatMB(bytes: number): string {
  return (bytes / (1024 * 1024)).toFixed(2);
}

/**
 * Result object from getStorageUsage with formatted strings
 */
export interface StorageUsageInfo {
  used: string;      // Formatted as "X.XX MB"
  total: string;     // Formatted as "X.XX MB"
  percentage: string; // Formatted as "X.XX %"
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
  /** Get current storage usage information */
  getStorageUsage: () => StorageUsageInfo;
}

/**
 * React hook for managing custom frame state
 *
 * Provides functionality to:
 * - Load frames from localStorage on mount
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
 * // Check storage
 * const { used, total, percentage } = getStorageUsage();
 * ```
 */
export function useCustomFrames(): UseCustomFramesReturn {
  const [customFrames, setCustomFrames] = useState<CustomFrame[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);

  /**
   * Load frames from localStorage on mount
   */
  useEffect(() => {
    try {
      const storedData = localStorage.getItem(STORAGE_KEY);
      if (storedData) {
        const parsed: CustomFrame[] = JSON.parse(storedData);
        // Sort by creation date (newest first)
        const sorted = parsed.sort(
          (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
        setCustomFrames(sorted);
      }
    } catch (error) {
      console.error('Failed to load custom frames from localStorage:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Save frames to localStorage whenever they change
   */
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(customFrames));
      } catch (error) {
        console.error('Failed to save custom frames to localStorage:', error);
      }
    }
  }, [customFrames, isLoading]);

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
    if (isStorageQuotaExceeded()) {
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

    // Add to state (will be auto-sorted by creation date)
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
  const deleteCustomFrame = (id: string): void => {
    setCustomFrames((prev) => prev.filter((frame) => frame.id !== id));
  };

  /**
   * Get current storage usage information
   *
   * Calculates the current localStorage usage and returns formatted strings
   *
   * @returns StorageUsageInfo with used, total, and percentage as formatted strings
   *
   * @example
   * ```tsx
   * const { used, total, percentage } = getStorageUsage();
   * console.log(`Used: ${used} of ${total} (${percentage})`);
   * // Output: "Used: 2.45 MB of 5.00 MB (49.00 %)"
   * ```
   */
  const getStorageUsage = (): StorageUsageInfo => {
    const usage = getImageStorageUsage();
    return {
      used: `${formatMB(usage.used)} MB`,
      total: `${formatMB(usage.total)} MB`,
      percentage: `${usage.percentage} %`
    };
  };

  return {
    customFrames,
    isLoading,
    uploadProgress,
    addCustomFrame,
    deleteCustomFrame,
    getStorageUsage
  };
}
